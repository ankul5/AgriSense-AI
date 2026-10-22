"""
AgriSense AI — FastAPI Backend Server
======================================
This server does ONE thing: run the pump automation decision engine
(Manual / Moisture / Timer modes) and expose the endpoints needed to
configure it and manage timers.

It does NOT sit in the telemetry or manual-pump-control path — those go
directly ESP32 <-> Supabase and Website <-> Supabase (see documents/context.md).
Manual pump control and device pairing work with this server stopped;
only Moisture Auto and Timer Schedule modes require it running.

Endpoints:
  - POST   /api/command                    — manual pump ON/OFF (also used by Force Stop). Auth required.
  - POST   /api/automation/mode             — set NONE / MOISTURE / TIMER for a device. Auth required.
  - GET    /api/automation/state/{id}       — read current automation config. Auth required.
  - GET    /api/devices                     — list devices for logged-in user (unused by website; kept for API completeness)
  - DELETE /api/devices/{id}                — unbind (unused by website; kept for API completeness)
  - POST   /api/timers, GET/{id}, DELETE/{id}, PATCH/{id} — timer schedule CRUD
  - POST   /api/plant/predict               — plant photo diagnosis. Auth required. Uses the
                                               trained serving API (serving/app.py) if
                                               PLANT_API_URL/PLANT_API_KEY are set, otherwise
                                               falls back to Gemini vision. Whichever key is
                                               used stays server-side.
  - POST   /api/advisor/ask                 — proxy to Gemini, grounded in the device's
                                               live telemetry. Holds GEMINI_API_KEY server-side.
                                               Auth required.
  - POST   /api/camera/{id}/frame           — ESP32-CAM uploads one JPEG. Auth: X-Cam-Key.
  - GET    /api/camera/{id}/wanted          — ESP32-CAM polls whether anyone is watching.
  - POST   /api/camera/{id}/token           — mint a short-lived viewer token. Auth required.
  - GET    /api/camera/stream               — MJPEG stream for a token from the above.
"""

from fastapi import FastAPI, HTTPException, Header, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
import os
import asyncio
import base64
import json
import secrets
import time
import httpx

# ── Load Environment Variables ──────────────────────────────────────────────
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # service_role key — bypasses RLS

# Plant-disease serving API (serving/app.py, deployed per serving/DEPLOY.md).
# PLANT_API_KEY must only ever live here, server-side — see
# plant-disease-implementation-plan.md Phase J: the mobile app and website
# call THIS backend's /api/plant/predict instead, which holds the real key.
PLANT_API_URL = os.getenv("PLANT_API_URL")        # e.g. https://agrisense-pd-api-xxxxx.run.app
PLANT_API_KEY = os.getenv("PLANT_API_KEY")

# Gemini (farm advisor chat). Same rule — key stays server-side, app calls
# THIS backend's /api/advisor/ask, which forwards to Gemini and never
# returns the key to the client.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
# Tried in order when GEMINI_MODEL is overloaded ("high demand" 503) or rate-limited.
GEMINI_FALLBACK_MODELS = [
    m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash,gemini-2.5-flash-lite").split(",")
    if m.strip()
]

# ESP32-CAM live view. The camera authenticates with this shared secret (it
# has no user login, same idea as PLANT_API_KEY); browsers/app authenticate
# with a short-lived token minted below instead, since an <img src> can't
# send an Authorization header. Frames are held in memory only — never
# written to Supabase or disk.
CAM_UPLOAD_KEY = os.getenv("CAM_UPLOAD_KEY")
_camera_frames: dict[str, tuple[bytes, float]] = {}    # device_id -> (jpeg, ts)
_camera_watchers: dict[str, float] = {}                # device_id -> last viewer tick
_camera_tokens: dict[str, tuple[str, float]] = {}       # token -> (device_id, expires_at)
CAMERA_TOKEN_TTL_S = 600
CAMERA_WANTED_WINDOW_S = 15

# Anon client: only used to validate a user's JWT (auth.get_user). Never used
# for table reads/writes — this server has no logged-in session, so RLS
# policies scoped to auth.uid() would silently return zero rows.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Admin client: for ALL table reads/writes. Bypasses RLS entirely, so every
# endpoint below that touches a table manually re-checks ownership after
# validating the caller's JWT with the anon client above.
supabase_admin: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_ANON_KEY
)


def _parse_ts(value: str) -> datetime:
    """Parse a Supabase timestamptz string (may end in 'Z') into an aware datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_user(token: str):
    """Validate a JWT, returning the user or None. supabase-py *raises* on a
    malformed/expired token instead of returning a falsy response, so a bare
    `if not user_resp.user` check 500s on bad input instead of 401ing —
    every auth call site needs this instead."""
    try:
        user_resp = supabase.auth.get_user(token)
    except Exception:
        return None
    return user_resp.user if user_resp else None


# ═══════════════════════════════════════════════════════════════════════════════
# PUMP DECISION ENGINE (Background Task)
# ═══════════════════════════════════════════════════════════════════════════════
# Reads live state from Supabase every tick — device_config for the mode and
# thresholds, device_status for the heartbeat, telemetry_data for the latest
# reading. Nothing is held in memory between ticks, so a backend restart
# never loses automation settings (they live in device_config, not in a dict).

async def pump_decision_engine():
    while True:
        try:
            await asyncio.sleep(10)
            await evaluate_all_devices()
        except Exception as e:
            print(f"[Decision Engine] Error: {e}")


async def evaluate_all_devices():
    configs_resp = supabase_admin.table("device_config") \
        .select("*").neq("automation_mode", "NONE").execute()
    configs = configs_resp.data or []

    for cfg in configs:
        device_id = cfg["device_id"]
        try:
            await evaluate_device(device_id, cfg)
        except Exception as e:
            print(f"[Decision Engine] {device_id}: error — {e}")


def automation_blocked_reason(
    mode: str, offline: bool, stale_data: bool, sensor_flags: dict
) -> Optional[str]:
    """Why automation must not run this tick, or None to proceed.

    Gated per MODE on the sensors that mode actually reads — NOT on the
    global sensors_ok, which is (dht && soil). Neither mode reads temperature
    or humidity, so a dead DHT11 must not disable irrigation:

      MOISTURE — needs a trustworthy soil reading. A failed probe reports 0,
                 which would satisfy `0 < start_threshold` forever and run
                 the pump continuously, re-triggering after every
                 max-runtime cutoff. This is the original safety gate.
      TIMER    — needs no sensor at all. Rain is a bonus safety check inside
                 evaluate_timer_mode, which already treats missing telemetry
                 as "not raining".

    A missing sensor_flags entry means older firmware that didn't report it;
    treat as OK so upgrading the backend never silently stops automation.
    Pure function so it is testable without Supabase — see test_automation.py.
    """
    if offline:
        return "device offline"

    if mode == "MOISTURE":
        if stale_data:
            return "telemetry stale"
        if sensor_flags.get("soil") is False:
            return "soil probe not reporting"

    return None


async def evaluate_device(device_id: str, cfg: dict):
    """Safety gate, then mode evaluation."""
    now = datetime.now(timezone.utc)

    status_resp = supabase_admin.table("device_status") \
        .select("*").eq("device_id", device_id).limit(1).execute()
    status = status_resp.data[0] if status_resp.data else None

    telem_resp = supabase_admin.table("telemetry_data") \
        .select("*").eq("device_id", device_id).order("created_at", desc=True).limit(1).execute()
    telemetry = telem_resp.data[0] if telem_resp.data else None

    offline = True
    if status and status.get("last_seen_at"):
        offline = (now - _parse_ts(status["last_seen_at"])).total_seconds() > 30

    stale_data = True
    if telemetry and telemetry.get("created_at"):
        stale_data = (now - _parse_ts(telemetry["created_at"])).total_seconds() > 60

    sensor_flags = (status.get("sensor_flags") or {}) if status else {}
    mode = cfg.get("automation_mode", "NONE")

    blocked = automation_blocked_reason(mode, offline, stale_data, sensor_flags)
    if blocked:
        if cfg.get("pump_on"):
            await queue_pump_command(device_id, "PUMP_OFF", f"Safety: {blocked}")
            _update_device_config(device_id, pump_on=False, pump_on_since=None)
        return

    if mode == "MOISTURE":
        await evaluate_moisture_mode(device_id, cfg, telemetry)
    elif mode == "TIMER":
        await evaluate_timer_mode(device_id, cfg, telemetry)


async def evaluate_moisture_mode(device_id: str, cfg: dict, telemetry: dict):
    """Auto-pump based on soil moisture thresholds."""
    soil = telemetry.get("soil_moisture", 0) or 0
    rain = bool(telemetry.get("rain_detected", False))
    pump_on = cfg.get("pump_on", False)
    start = cfg.get("start_threshold", 70)
    stop = cfg.get("stop_threshold", 85)
    max_runtime = cfg.get("max_runtime_mins", 20)

    # Safety: max runtime check
    if pump_on and cfg.get("pump_on_since"):
        elapsed = (datetime.now(timezone.utc) - _parse_ts(cfg["pump_on_since"])).total_seconds() / 60
        if elapsed >= max_runtime:
            await queue_pump_command(device_id, "PUMP_OFF", "Max Runtime Safety Cutoff")
            _update_device_config(device_id, pump_on=False, pump_on_since=None)
            return

    # If soil is dry AND no rain → turn pump ON
    if soil < start and not rain and not pump_on:
        await queue_pump_command(device_id, "PUMP_ON", "Smart Moisture Auto")
        _update_device_config(device_id, pump_on=True, pump_on_since=_now_iso())

    # If soil has reached the stop threshold → turn pump OFF
    elif soil >= stop and pump_on:
        await queue_pump_command(device_id, "PUMP_OFF", "Smart Moisture Auto")
        _update_device_config(device_id, pump_on=False, pump_on_since=None)


async def evaluate_timer_mode(device_id: str, cfg: dict, telemetry: dict):
    """Auto-pump based on scheduled timers from the timers table."""
    pump_on = cfg.get("pump_on", False)
    rain = bool(telemetry.get("rain_detected", False)) if telemetry else False

    # Safety: if currently raining and pump is ON → turn it off immediately
    if rain and pump_on:
        await queue_pump_command(device_id, "PUMP_OFF", "Rain Detected — Timer Paused")
        _update_device_config(device_id, pump_on=False, pump_on_since=None)
        return

    # If raining, don't start a new timer cycle
    if rain:
        return

    try:
        timers_resp = supabase_admin.table("timers") \
            .select("*") \
            .eq("device_id", device_id) \
            .eq("is_active", True) \
            .execute()
        timers = timers_resp.data if timers_resp.data else []
    except Exception:
        return

    now = datetime.now()
    # Unique 2-letter abbreviations: Mo Tu We Th Fr Sa Su
    day_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    current_day = day_names[now.weekday()]
    inside_window = False

    for timer in timers:
        active_days = timer.get("active_days", [])
        if current_day not in active_days:
            continue

        try:
            start_str = timer.get("start_time", "06:00")
            if "AM" in start_str.upper() or "PM" in start_str.upper():
                start_time = datetime.strptime(start_str.upper().strip(), "%I:%M %p").time()
            else:
                start_time = datetime.strptime(start_str.strip(), "%H:%M").time()

            duration_mins = timer.get("duration_mins", 15)
            start_dt = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
            end_dt = start_dt + timedelta(minutes=duration_mins)

            if start_dt <= now <= end_dt:
                inside_window = True
                break
        except Exception:
            continue

    if inside_window and not pump_on:
        await queue_pump_command(device_id, "PUMP_ON", "Timer Schedule")
        _update_device_config(device_id, pump_on=True, pump_on_since=_now_iso())
    elif not inside_window and pump_on:
        await queue_pump_command(device_id, "PUMP_OFF", "Timer Schedule")
        _update_device_config(device_id, pump_on=False, pump_on_since=None)


def _update_device_config(device_id: str, **fields):
    """Persist automation state back to device_config (replaces the old in-memory dict)."""
    try:
        supabase_admin.table("device_config").update(fields).eq("device_id", device_id).execute()
    except Exception as e:
        print(f"[Decision Engine] Failed to persist config for {device_id}: {e}")


async def queue_pump_command(device_id: str, command: str, trigger: str):
    """Insert a command into the device_commands table for the ESP32 to pick up.
    The website learns about this via its own Supabase Realtime subscription
    on device_commands/telemetry_data — no WebSocket broadcast needed here."""
    print(f"[Decision Engine] {device_id}: {command} (trigger: {trigger})")
    try:
        supabase_admin.table("device_commands").insert({
            "device_id": device_id,
            "command": command,
            "executed": False
        }).execute()
    except Exception as e:
        print(f"[Decision Engine] Error queuing command: {e}")


# ── App Lifespan (start background tasks) ───────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(pump_decision_engine())
    print("[Startup] Pump Decision Engine started.")
    yield
    task.cancel()
    print("[Shutdown] Pump Decision Engine stopped.")


# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(title="AgriSense AI Backend", version="4.0.0", lifespan=lifespan)

# Allow Website and App to connect (CORS)
# allow_credentials=True cannot be combined with allow_origins=["*"] — browsers reject it.
# Using explicit list instead; wildcard handles the file:// null-origin case too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve the Web Dashboard as Static Files ───────────────────────────────────
# This means opening http://10.87.216.17:8000 opens the website directly.
# No more file:// origin issues. No CORS needed between website and backend.
_DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "..", "web_dashboard")
_DASHBOARD_DIR = os.path.normpath(_DASHBOARD_DIR)

@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Redirect root to index.html"""
    return FileResponse(os.path.join(_DASHBOARD_DIR, "index.html"))

# Mount static assets (JS, CSS, images) — must come AFTER all API routes are defined
# We mount it later at the bottom of the file to avoid route conflicts.


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class CommandPayload(BaseModel):
    """What the website/app sends to control the pump"""
    device_id: str
    command: str   # "PUMP_ON", "PUMP_OFF"

class TimerPayload(BaseModel):
    device_id: str
    start_time: str
    duration_mins: int
    active_days: List[str]
    user_token: str

class TimerPatchPayload(BaseModel):
    is_active: bool

class AutomationModePayload(BaseModel):
    """Set the pump automation mode for a device"""
    device_id: str
    mode: str              # "NONE", "MOISTURE", "TIMER"
    start_threshold: Optional[int] = 70
    stop_threshold: Optional[int] = 85
    max_runtime_mins: Optional[int] = 20

class AdvisorPayload(BaseModel):
    """A question for the farm advisor chat, optionally about a specific device."""
    device_id: Optional[str] = None
    question: str
    history: Optional[List[dict]] = None   # [{"role": "user"|"model", "text": "..."}]


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health", include_in_schema=False)
def root():
    return {"status": "AgriSense Automation Backend is running", "version": "4.0.0"}


# ── Website/App: Send a manual pump command ──────────────────────────────────
@app.post("/api/command")
async def send_command(payload: CommandPayload, authorization: str = Header(...)):
    """
    Website sends: 'Turn pump ON/OFF for device AGS-7F3K21' (manual toggle or
    Force Stop). This is a MANUAL override — it queues the command for the
    ESP32 and switches automation_mode to NONE so the Decision Engine doesn't
    fight the manual action.
    """
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _assert_owns_device(user.id, payload.device_id)

    if payload.command not in ("PUMP_ON", "PUMP_OFF"):
        raise HTTPException(status_code=400, detail="command must be PUMP_ON or PUMP_OFF")

    supabase_admin.table("device_commands").insert({
        "device_id": payload.device_id,
        "command": payload.command,
        "executed": False
    }).execute()

    pump_on = payload.command == "PUMP_ON"
    supabase_admin.table("device_config").upsert({
        "device_id": payload.device_id,
        "automation_mode": "NONE",
        "pump_on": pump_on,
        "pump_on_since": _now_iso() if pump_on else None,
    }, on_conflict="device_id").execute()

    return {"status": "command queued", "command": payload.command, "automation_mode": "NONE"}


# ── Website/App: Set automation mode ─────────────────────────────────────────
@app.post("/api/automation/mode")
async def set_automation_mode(payload: AutomationModePayload, authorization: str = Header(...)):
    """
    Set the pump automation mode for a device.
    Modes: "NONE" (manual only), "MOISTURE", "TIMER"
    """
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _assert_owns_device(user.id, payload.device_id)

    if payload.mode not in ("NONE", "MOISTURE", "TIMER"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use NONE, MOISTURE, or TIMER.")

    fields = {
        "device_id": payload.device_id,
        "automation_mode": payload.mode,
        "start_threshold": payload.start_threshold or 70,
        "stop_threshold": payload.stop_threshold or 85,
        "max_runtime_mins": payload.max_runtime_mins or 20,
    }
    supabase_admin.table("device_config").upsert(fields, on_conflict="device_id").execute()

    print(f"[Automation] {payload.device_id}: mode set to {payload.mode}")

    return {
        "status": "mode updated",
        "device_id": payload.device_id,
        "automation_mode": payload.mode,
    }


# ── Website/App: Get current automation state for a device ───────────────────
@app.get("/api/automation/state/{device_id}")
def get_automation_state(device_id: str, authorization: str = Header(...)):
    """Return the current automation mode and pump state from device_config."""
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _assert_owns_device(user.id, device_id)

    resp = supabase_admin.table("device_config").select("*").eq("device_id", device_id).limit(1).execute()
    if not resp.data:
        return {
            "device_id": device_id,
            "automation_mode": "NONE",
            "pump_on": False,
            "start_threshold": 70,
            "stop_threshold": 85,
            "max_runtime_mins": 20,
        }
    cfg = resp.data[0]
    return {
        "device_id": device_id,
        "automation_mode": cfg["automation_mode"],
        "pump_on": cfg["pump_on"],
        "start_threshold": cfg["start_threshold"],
        "stop_threshold": cfg["stop_threshold"],
        "max_runtime_mins": cfg["max_runtime_mins"],
    }


# ── Website/App: Get devices for logged-in user ───────────────────────────────
# Not currently called by the website (it queries Supabase directly instead —
# see web_dashboard/app.js fetchUserDevices). Kept for API completeness.
@app.get("/api/devices")
def get_devices(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user.id
    devices = supabase_admin.table("devices").select("*").eq("user_id", user_id).execute()
    return {"devices": devices.data}


# ── Website/App: Unbind a device ──────────────────────────────────────────────
# Not currently called by the website (it deletes from Supabase directly).
# Kept for API completeness.
@app.delete("/api/devices/{device_id}")
def unbind_device(device_id: str, authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    supabase_admin.table("devices") \
        .delete() \
        .eq("device_id", device_id) \
        .eq("user_id", user.id) \
        .execute()

    return {"status": "device unbound"}


# ── Website/App: Timer management ─────────────────────────────────────────────
# All timer endpoints validate the caller's JWT with the anon client, then use
# supabase_admin (service key, bypasses RLS) for the actual table operation —
# manually re-checking device ownership first, since RLS is not enforcing it here.

def _assert_owns_device(user_id: str, device_id: str):
    owned = supabase_admin.table("devices").select("device_id") \
        .eq("device_id", device_id).eq("user_id", user_id).execute()
    if not owned.data:
        raise HTTPException(status_code=403, detail="You don't own this device.")

def _device_id_for_timer(timer_id: int) -> str:
    resp = supabase_admin.table("timers").select("device_id").eq("id", timer_id).limit(1).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Timer not found")
    return resp.data[0]["device_id"]


@app.post("/api/timers")
def add_timer(payload: TimerPayload):
    user = _get_user(payload.user_token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    _assert_owns_device(user.id, payload.device_id)

    supabase_admin.table("timers").insert({
        "device_id": payload.device_id,
        "start_time": payload.start_time,
        "duration_mins": payload.duration_mins,
        "active_days": payload.active_days,
        "is_active": True
    }).execute()

    return {"status": "timer added"}


@app.get("/api/timers/{device_id}")
def get_timers(device_id: str, authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    _assert_owns_device(user.id, device_id)

    timers = supabase_admin.table("timers").select("*").eq("device_id", device_id).execute()
    return {"timers": timers.data}


@app.patch("/api/timers/{timer_id}")
def patch_timer(timer_id: int, payload: TimerPatchPayload, authorization: str = Header(...)):
    """Toggle a timer's enabled state — persists what toggleTimerActive() in
    the website used to only change locally."""
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    device_id = _device_id_for_timer(timer_id)
    _assert_owns_device(user.id, device_id)

    supabase_admin.table("timers").update({"is_active": payload.is_active}).eq("id", timer_id).execute()
    return {"status": "timer updated", "is_active": payload.is_active}


@app.delete("/api/timers/{timer_id}")
def delete_timer(timer_id: int, authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    device_id = _device_id_for_timer(timer_id)
    _assert_owns_device(user.id, device_id)

    supabase_admin.table("timers").delete().eq("id", timer_id).execute()
    return {"status": "timer deleted"}


# ── Website/App: Plant disease diagnosis ──────────────────────────────────────
# The ONNX model in ml/ isn't trained/exported yet, so this defaults to a
# Gemini vision call instead of the (unconfigured) Cloud Run serving API.
# Set PLANT_API_URL/PLANT_API_KEY later to switch back to the real model —
# no other code needs to change.
PLANT_DIAGNOSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_plant": {"type": "BOOLEAN"},
        "species": {"type": "STRING"},
        "species_confidence": {"type": "NUMBER"},
        "condition": {"type": "STRING"},
        "condition_confidence": {"type": "NUMBER"},
        "healthy": {"type": "BOOLEAN"},
        "severity": {"type": "STRING", "enum": ["none", "mild", "moderate", "severe"]},
        "affected_area_pct": {"type": "INTEGER"},
        "symptoms": {"type": "ARRAY", "items": {"type": "STRING"}},
        "cause": {"type": "STRING"},
        "treatment": {"type": "ARRAY", "items": {"type": "STRING"}},
        "prevention": {"type": "ARRAY", "items": {"type": "STRING"}},
        "notes": {"type": "STRING"},
    },
    "required": [
        "is_plant", "species", "species_confidence", "condition", "condition_confidence",
        "healthy", "severity", "affected_area_pct", "symptoms", "cause",
        "treatment", "prevention", "notes",
    ],
}

PLANT_DIAGNOSIS_PROMPT = """You are an agronomist helping a smallholder farmer in India diagnose a \
plant photo. Look closely at the leaf/plant in the image and respond ONLY with JSON matching the \
given schema, no other text.

Rules:
- If the photo does not show a plant/leaf at all, set is_plant to false and put your best guess of \
what it actually shows in notes; still fill every other field with reasonable placeholders \
(species "unknown", condition "unknown", healthy false, severity "none", affected_area_pct 0, \
empty arrays for symptoms/treatment/prevention, cause "unknown").
- Prefer common PlantVillage-style names, e.g. species "tomato", condition "early_blight" or "healthy".
- severity: "none" if healthy, otherwise "mild"/"moderate"/"severe" based on how much of the \
plant/leaf is visibly affected.
- affected_area_pct: your estimate of the percent of the visible leaf/plant area showing symptoms.
- symptoms: short phrases describing what you actually see (e.g. "yellow halo around brown spots").
- cause: one of fungal, bacterial, viral, pest, nutrient_deficiency, abiotic_stress, or unknown.
- treatment/prevention: concrete, actionable steps a smallholder farmer could do this week.
- species_confidence/condition_confidence: your honest 0-1 confidence, be conservative on blurry \
or ambiguous photos.
- notes: one short sentence with any caveat (e.g. blurry photo, multiple leaves, early stage)."""


async def _gemini_generate(body: dict) -> tuple[httpx.Response, str]:
    """Call Gemini, moving to the next model when one is overloaded (503),
    rate-limited (429) or erroring (500/504). Returns (response, model used)."""
    last_resp, last_model = None, GEMINI_MODEL
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in [GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]:
            try:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    params={"key": GEMINI_API_KEY},
                    json=body,
                )
            except httpx.RequestError as e:
                last_resp, last_model = None, model
                last_err = e
                continue
            last_resp, last_model = resp, model
            if resp.status_code not in (429, 500, 503, 504):
                return resp, model
    if last_resp is None:
        raise HTTPException(status_code=502, detail=f"Could not reach Gemini: {last_err}")
    return last_resp, last_model


@app.post("/api/plant/predict")
async def plant_predict(file: UploadFile = File(...), authorization: str = Header(...)):
    """
    Diagnose an uploaded plant photo. This is the ONLY thing the app/website
    call for "upload photo -> get diagnosis" — whichever backend key
    (PLANT_API_KEY or GEMINI_API_KEY) it uses never leaves this server.
    """
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    contents = await file.read()

    # Real trained model, once PLANT_API_URL/PLANT_API_KEY are configured.
    if PLANT_API_URL and PLANT_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{PLANT_API_URL}/predict",
                    headers={"X-API-Key": PLANT_API_KEY},
                    files={"file": (file.filename, contents, file.content_type)},
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Could not reach plant diagnosis API: {e}")

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

    # Fallback: Gemini vision.
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Plant diagnosis is not configured on this server (GEMINI_API_KEY missing).",
        )

    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=415, detail="Only JPEG, PNG or WEBP photos are supported.")

    if len(contents) > 6_000_000:
        raise HTTPException(status_code=413, detail="Photo is too large (max ~6MB).")

    body = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": PLANT_DIAGNOSIS_PROMPT},
                {"inlineData": {"mimeType": file.content_type, "data": base64.b64encode(contents).decode()}},
            ],
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": PLANT_DIAGNOSIS_SCHEMA,
            "temperature": 0.2,
            "maxOutputTokens": 2048,
        },
    }

    start = time.perf_counter()
    resp, model_used = await _gemini_generate(body)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()
    candidates = data.get("candidates") or []
    parts = candidates[0].get("content", {}).get("parts") if candidates else None
    if not parts:
        raise HTTPException(status_code=502, detail="Gemini returned no diagnosis for this photo.")

    try:
        diagnosis = json.loads(parts[0]["text"])
    except (KeyError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=502, detail=f"Gemini returned malformed diagnosis: {e}")

    inference_ms = int((time.perf_counter() - start) * 1000)
    return finalize_plant_diagnosis(diagnosis, model_used, inference_ms)


def finalize_plant_diagnosis(diagnosis: dict, model_version: str, inference_ms: int) -> dict:
    """Fill in the fields Gemini doesn't (and shouldn't) self-report. Pure
    function so it's testable without booting FastAPI/Supabase — see
    backend/test_plant_predict.py."""
    species_confidence = diagnosis.get("species_confidence", 0) or 0
    condition_confidence = diagnosis.get("condition_confidence", 0) or 0
    joint_confidence = species_confidence * condition_confidence

    diagnosis["joint_confidence"] = joint_confidence
    diagnosis["low_confidence"] = (not diagnosis.get("is_plant", True)) or joint_confidence < 0.45
    diagnosis["model_version"] = f"gemini:{model_version}"
    diagnosis["inference_ms"] = inference_ms
    return diagnosis


# ── Website/App: Farm advisor chat (proxy to Gemini) ──────────────────────────
@app.post("/api/advisor/ask")
async def advisor_ask(payload: AdvisorPayload, authorization: str = Header(...)):
    """
    Answer a farm question, grounded in the device's live telemetry when
    device_id is given. The Gemini key never leaves this server — same
    reasoning as /api/plant/predict above.
    """
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if len(payload.question) > 2000:
        raise HTTPException(status_code=400, detail="question is too long (max 2000 chars)")

    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Advisor is not configured on this server (GEMINI_API_KEY missing).",
        )

    context_lines = ["You are the AgriSense farm advisor. Answer briefly and practically."]
    if payload.device_id:
        _assert_owns_device(user.id, payload.device_id)

        status_resp = supabase_admin.table("device_status") \
            .select("*").eq("device_id", payload.device_id).limit(1).execute()
        status = status_resp.data[0] if status_resp.data else None

        telem_resp = supabase_admin.table("telemetry_data") \
            .select("*").eq("device_id", payload.device_id).order("created_at", desc=True).limit(1).execute()
        telemetry = telem_resp.data[0] if telem_resp.data else None

        if status and status.get("last_seen_at"):
            offline = (datetime.now(timezone.utc) - _parse_ts(status["last_seen_at"])).total_seconds() > 30
        else:
            offline = True

        if offline or not telemetry:
            context_lines.append("This device's sensors are currently OFFLINE — no live data available.")
        else:
            stale = (datetime.now(timezone.utc) - _parse_ts(telemetry["created_at"])).total_seconds() > 60
            context_lines.append(
                f"Live telemetry ({'STALE, ' if stale else ''}device {payload.device_id}): "
                f"soil_moisture={telemetry.get('soil_moisture')}, "
                f"rain_detected={telemetry.get('rain_detected')}."
            )

    contents = [
        {"role": h["role"], "parts": [{"text": h["text"]}]}
        for h in (payload.history or [])
    ]
    contents.append({"role": "user", "parts": [{"text": payload.question}]})

    body = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": "\n".join(context_lines)}]},
        # gemini-3.6-flash spends part of the budget on internal "thinking"
        # tokens before the visible answer, so this needs headroom above a
        # plain output cap or a real question can get truncated to nothing.
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7},
    }

    resp, _ = await _gemini_generate(body)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates or not candidates[0].get("content", {}).get("parts"):
        return {"answer": "The advisor couldn't produce a response to that question — try rephrasing."}

    answer = candidates[0]["content"]["parts"][0]["text"]
    return {"answer": answer}


# ── ESP32-CAM: live farm view ──────────────────────────────────────────────
# The camera reuses the sensor node's device_id (e.g. "AGS-0001") instead of
# being its own paired device — it's "the camera on that field node", not a
# separate thing to pair/own/count against the 4-device limit.
MAX_CAMERA_DEVICES = 32
MAX_FRAME_BYTES = 200_000


@app.post("/api/camera/{device_id}/frame")
async def camera_upload_frame(device_id: str, request: Request, x_cam_key: str = Header(...)):
    """ESP32-CAM pushes one JPEG. Returns whether anyone is currently
    watching, so the camera can decide to keep streaming or go idle —
    piggybacking that on the upload response avoids a separate control
    channel back to the device."""
    if not CAM_UPLOAD_KEY:
        raise HTTPException(status_code=503, detail="Camera relay is not configured on this server (CAM_UPLOAD_KEY missing).")
    if x_cam_key != CAM_UPLOAD_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if device_id not in _camera_frames and len(_camera_frames) >= MAX_CAMERA_DEVICES:
        raise HTTPException(status_code=503, detail="Too many camera devices already active.")

    body = await request.body()
    if len(body) > MAX_FRAME_BYTES:
        raise HTTPException(status_code=413, detail="Frame too large.")

    _camera_frames[device_id] = (body, time.time())
    wanted = (time.time() - _camera_watchers.get(device_id, 0)) < CAMERA_WANTED_WINDOW_S
    return {"wanted": wanted}


@app.get("/api/camera/{device_id}/wanted")
async def camera_wanted(device_id: str, x_cam_key: str = Header(...)):
    """Same signal as above, for an idle camera with no frame to upload."""
    if not CAM_UPLOAD_KEY:
        raise HTTPException(status_code=503, detail="Camera relay is not configured on this server (CAM_UPLOAD_KEY missing).")
    if x_cam_key != CAM_UPLOAD_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    wanted = (time.time() - _camera_watchers.get(device_id, 0)) < CAMERA_WANTED_WINDOW_S
    return {"wanted": wanted}


@app.post("/api/camera/{device_id}/token")
async def camera_token(device_id: str, authorization: str = Header(...)):
    """Mint a short-lived viewer token. A plain <img src="..."> can't send an
    Authorization header, so the stream carries its credential in the query
    string instead — this is the one route that still checks the real JWT
    and device ownership, same as every other route in this file."""
    token = authorization.replace("Bearer ", "")
    user = _get_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _assert_owns_device(user.id, device_id)

    cam_token = secrets.token_urlsafe(24)
    _camera_tokens[cam_token] = (device_id, time.time() + CAMERA_TOKEN_TTL_S)
    return {"token": cam_token}


@app.get("/api/camera/stream")
async def camera_stream(t: str):
    entry = _camera_tokens.get(t)
    if not entry or entry[1] < time.time():
        raise HTTPException(status_code=401, detail="Invalid or expired camera token.")
    device_id = entry[0]

    async def mjpeg():
        last_ts = 0.0
        idle_ticks = 0
        while idle_ticks < 130:            # ~20s of no fresh frame at 150ms/tick
            _camera_watchers[device_id] = time.time()
            frame = _camera_frames.get(device_id)
            if frame and frame[1] != last_ts:
                last_ts = frame[1]
                idle_ticks = 0
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(frame[0])).encode() + b"\r\n\r\n"
                    + frame[0] + b"\r\n"
                )
            else:
                idle_ticks += 1
            await asyncio.sleep(0.15)

    return StreamingResponse(mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame")


# ── Mount Static Files (MUST be last — after all API routes) ─────────────────
# Serves the web dashboard at http://10.87.216.17:8000/
# JS, CSS and other assets will be served from /web_dashboard/
app.mount("/", StaticFiles(directory=_DASHBOARD_DIR, html=True), name="dashboard")
