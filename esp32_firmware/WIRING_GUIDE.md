# AgriSense AI — ESP32 DevKit V1 Wiring Guide

---

## ❓ QUESTION 1: How does the website connect to the ESP32?

**Short answer: Through Wi-Fi — but NOT directly. The website never talks to the ESP32 directly.**

### What "Initialize Node Pairing" actually does:
Clicking that button does **NOT** send anything to the ESP32. It just **registers the device ID in the Supabase cloud database** so the backend knows the device belongs to your account.

### The real connection flow:

```
                        YOUR HOME Wi-Fi NETWORK
                                │
               ┌────────────────┴────────────────┐
               │                                 │
         ESP32 board                        Your PC
               │                                 │
               │   Every 10s:                    │  Python backend running
               │   POST /api/telemetry ─────────►│  (python -m uvicorn ...)
               │                                 │
               │   Every 5s:                     │
               │   GET /api/device/command ◄─────│
               │                                 │
                                            ↕  WebSocket
                                       Your Browser
                                    (website / dashboard)
```

- **ESP32 ↔ Backend**: HTTP over your Wi-Fi (same network required)
- **Website ↔ Backend**: HTTP/WebSocket over network
- **No Bluetooth used anywhere**
- **No direct ESP32 ↔ Website connection** — they never talk to each other directly

### Summary table:

| What you do | What actually happens |
|-------------|----------------------|
| Power on ESP32 | ESP32 joins Wi-Fi → starts sending data to backend every 10s |
| Click "Initialize Node Pairing" | Your browser tells the backend: "add AGS-0001 to my account" → backend saves in Supabase cloud database |
| Open website on phone (different city) | Browser fetches your device list from Supabase → opens WebSocket to backend → sees live data |
| Click Pump ON | Browser → `POST /api/command` → backend → `device_commands` table → ESP32 polls every 5s → relay fires |

---

## ❓ QUESTION 2: D-pins vs GPIO pins — ESP32 DevKit V1

**Short answer: The number after "D" IS the GPIO number. D4 = GPIO4. They are the same thing.**

The physical label printed on your board (e.g. **D4**, **D33**, **D34**, **D16**) directly maps to the GPIO number used in code. There is no conversion needed — just use the number.

### Physical Board Layout — ESP32 DevKit V1 (30-pin / Type-C)

```
                    ┌─────────────────┐
                    │   [ USB-C ]     │
               3.3V │ ○             ○ │ GND
                EN  │ ○             ○ │ D23
               VP   │ ○  (GPIO36)  ○ │ D22
               VN   │ ○  (GPIO39)  ○ │ TX0  (GPIO1)
             ► D34  │ ○  [SOIL]   ○  │ RX0  (GPIO3)
             D35    │ ○             ○ │ D21
             D32    │ ○             ○ │ D19
           ► D33    │ ○  [RAIN]   ○  │ D18
             D25    │ ○             ○ │ D5
             D26    │ ○             ○ │ TX2  (GPIO17)
             D27    │ ○             ○ │ RX2  ← This is GPIO16 ★ [RELAY]
             D14    │ ○             ○ │ D4   ← [DHT11] ★
             D12    │ ○             ○ │ D2
             D13    │ ○             ○ │ D15
               GND  │ ○             ○ │ GND
               VIN  │ ○             ○ │ 3.3V
                    └─────────────────┘
                         ★ = pins used in this project
```

> **Note:** On some ESP32 DevKit V1 boards, GPIO16 is labeled **RX2** instead of **D16** — they are the exact same pin. Look for "RX2" or "IO16" on the right side of the board.

### Pin mapping for this project:

| What to connect | Board Label | Silkscreen says | GPIO in code | Side of board |
|----------------|-------------|-----------------|-------------|--------------|
| DHT11 DATA wire | **D4** | `D4` | GPIO 4 | Right side |
| Soil Moisture AOUT | **D34** | `D34` | GPIO 34 | Left side |
| Rain Sensor DO | **D33** | `D33` | GPIO 33 | Left side |
| Relay Module IN | **RX2 / D16** | `RX2` or `IO16` | GPIO 16 | Right side |
| All sensors VCC | **3.3V** | `3V3` | — | Either side |
| Relay VCC | **VIN** | `VIN` | 5V | Either side |
| All GND wires | **GND** | `GND` | — | Either side |

---

## SENSOR CONNECTIONS (step by step)

### 1. DHT11 — Air Temperature & Humidity

```
DHT11 module:              ESP32 board:
  VCC  ─────────────────►  3.3V  (3V3 pin)
  DATA ─────────────────►  D4    (right side, labeled D4)
  GND  ─────────────────►  GND

⚠️  Add a 10kΩ resistor between DATA and VCC (pull-up).
    Without it, readings will be wrong or NaN.
```

### 2. Capacitive Soil Moisture Sensor (Analog)

```
Soil Sensor:               ESP32 board:
  VCC  ─────────────────►  3.3V  (3V3 pin)
  AOUT ─────────────────►  D34   (left side, labeled D34)
  GND  ─────────────────►  GND

ℹ️  GPIO34 is INPUT ONLY — no pull-up inside chip. That's fine, AOUT is an analog output.
ℹ️  Calibrate in .ino: dry air reading → SOIL_DRY_VALUE, submerged → SOIL_WET_VALUE
```

#### Disconnect calibration (required for the "online, no sensor data" feature)

The firmware also needs to tell a genuinely dry probe apart from **no probe plugged in at
all** — an unplugged GPIO34 floats, and what it reads when floating depends on your specific
wiring/board, so you must measure it once:

1. Flash the firmware and open the Serial Monitor at 115200 baud.
2. **Unplug the soil sensor.** Watch the `raw ADC` value printed each tick in the dashboard
   (`Soil Moisture: ... (raw ADC ####)`). Note it — this is the "disconnected" reading.
3. **Plug the probe back in**, leave it in dry air (not in soil). Note the raw ADC value again —
   this is the lowest reading you'll ever see with a real probe attached.
4. Open the `.ino` and set `SOIL_DISCONNECT_ADC` to a value between the two, closer to the
   disconnected reading, e.g. if unplugged reads ~20 and dry-air reads ~3600, `50` is a safe cutoff.
5. Re-flash. Unplug the probe again to confirm the dashboard now prints `[ DISCONNECTED ]` and the
   website shows `00` in green (online, no sensor) instead of a fake moisture percentage.

The current default is `SOIL_DISCONNECT_ADC 10` — measured on the project's own board, where an
unplugged probe floats to ~0 and a submerged probe reads ~30. That is a narrow margin; re-measure
on your own board rather than trusting the default.

**`SOIL_WET_VALUE` must be measured in saturated soil, not a glass of water.** Soil holds air
pockets a water bath doesn't, so calibrating "wet" in water makes the sensor read real wet soil as
only ~55-60%, which never reaches `SOIL_WET_PCT` (70) — the pump then never gets the signal to stop
and looks like it's stuck on. Push the probe into soil you've just watered thoroughly, not into a
cup of water, when you measure this value.

**DHT11 reads are retried up to `DHT_READ_ATTEMPTS` (3) times per tick**, 2.2 s apart, before giving
up — a single failed read (common with Wi-Fi active) no longer shows as "0°C / 0% humidity" on the
dashboard or in Supabase. If every attempt in a tick fails, the firmware sends the last known-good
reading instead of zeros; only a sensor that has *never* read successfully since boot sends 0.

### 3. Rain Sensor Module (Digital Output)

```
Rain Sensor module:        ESP32 board:
  VCC  ─────────────────►  3.3V  (3V3 pin)
  DO   ─────────────────►  D33   (left side, labeled D33)
  GND  ─────────────────►  GND

ℹ️  DO = Digital Output. LOW = Rain detected. HIGH = Dry.
ℹ️  The AO (analog out) pin is unused — ignore it.
⚠️  This sensor CANNOT be health-checked. A disconnected/floating DO pin reads
    the same as "no rain" — there is no way to tell the two apart in software.
    It is intentionally left out of the sensors_ok / "online, no data" check.
```

### 4. Relay Module — Water Pump Control

> ⚠️ **If the pump runs non-stop and ignores force-stop, read this section first.**
> It is almost always wiring, not code. The firmware self-tests its own logic at
> boot (`[SELFTEST] Pump logic: all 11 cases pass`).

#### Powering the relay — the #1 cause of "pump never turns off"

An opto-isolated relay module's input LED sits between `VCC` and `IN`. It
conducts whenever `VCC − IN` is more than ~1.2 V. Power the module at **5 V**
and drive `IN` from an ESP32 GPIO (**3.3 V max**) and a logic HIGH still leaves
**1.7 V** across that LED — the relay stays energised forever. The code writes
HIGH, the Serial log prints "Pump OFF", and the motor keeps running.

**Look at your module's power header:**

- **Three pins with a jumper cap (`JD-VCC` / `VCC` / `GND`)** — this is the fix:
  ```
  Remove the jumper cap, then:
    JD-VCC ────► VIN  (5V — powers the relay coil)
    VCC    ────► 3V3  (3.3V — powers the opto input side)
    GND    ────► GND
  ```
  The opto now references 3.3 V, so a 3.3 V HIGH really is "off".

- **No jumper, two pins only** — power `VCC` from **3V3** instead of VIN and
  test. If the relay never clicks at all, the 5 V coil can't pull in at 3.3 V:
  use a 3.3 V-logic relay module, or drive `IN` through an NPN transistor.

#### Signal and load wiring
 ```
Relay Module:              ESP32 board:
  IN   ─────────────────►  RX2   (right side, labeled RX2 or IO16 = GPIO16)
  GND  ─────────────────►  GND
  VCC / JD-VCC ─────────►  see "Powering the relay" above

Relay screw terminals:
  COM  ─────────────────►  Live wire (+) from pump power supply
  NO   ─────────────────►  Wire going to pump positive terminal
```

⚠️  **Use NO, never NC.** `NC` (Normally Closed) is connected when the relay is
    *idle* — wire the pump there and it runs whenever the board is off, booting,
    or commanding OFF. This is the second most common cause of a non-stop pump.

⚠️  Active-LOW relay: GPIO16 LOW → relay ON → pump runs
                      GPIO16 HIGH → relay OFF → pump stops
    If your module is active-HIGH (or has a LOW/HIGH trigger jumper set to
    HIGH), set `RELAY_ACTIVE_LOW` to `0` in the `.ino` and re-flash.

⚠️  NEVER connect mains (230V AC) yourself without proper knowledge.
    Use a DC pump with a 12V adapter for safety during testing.

#### Three-step diagnosis (no code changes, ~2 minutes)

Do these in order — each one rules out a whole class of fault.

| # | Do this | Pump still runs? | Pump stops? |
|---|---------|------------------|-------------|
| 1 | **Unplug the `IN` wire from GPIO16 entirely** | Load wiring or a welded relay → you are on `NC` instead of `NO`, or the contacts are fused. Nothing on the ESP32 side can help. | Signal problem → go to step 2. |
| 2 | Jumper `IN` directly to **3V3** (this is what the code does for OFF) | Relay can't see 3.3 V as "off" → **the power fix above**, or the module is active-HIGH. | Module is fine; the fault is on the ESP32 pin → go to step 3. |
| 3 | Jumper `IN` directly to **GND** (this is what the code does for ON) | Correct — relay should click ON here. If it clicked ON in step 2 as well, it is stuck. | Module is inverted → set `RELAY_ACTIVE_LOW 0`. |

If the pump is off in step 2 and on in step 3, the relay is behaving correctly
and the fault is elsewhere — check that GPIO16 is really the pin you wired
(`RX2` on a DevKit V1), and watch the `[Relay] GPIO 16 → ...` lines in Serial
Monitor to confirm the firmware is actually toggling.

> **ESP32-WROVER boards only:** GPIO16 is wired to the PSRAM chip and cannot be
> used as a normal output. Move the relay to GPIO 17, 18, or 19 and update
> `RELAY_PUMP_PIN`. DevKit V1 / WROOM boards are unaffected.

---

## QUICK SCHEMATIC (text diagram)

```
ESP32 DevKit V1
├── 3.3V ────┬──── DHT11 VCC
│            ├──── Soil Sensor VCC
│            └──── Rain Sensor VCC
│
├── D4  ─────────── DHT11 DATA  (+ 10kΩ to 3.3V)
├── D34 ─────────── Soil Sensor AOUT
├── D33 ─────────── Rain Sensor DO
├── RX2 ─────────── Relay Module IN   (= GPIO 16)
│
├── VIN ─────────── Relay Module JD-VCC (5V coil — see Relay section)
├── 3.3V ────────── Relay Module VCC    (3.3V logic, jumper removed)
│
└── GND ────┬──── DHT11 GND
            ├──── Soil Sensor GND
            ├──── Rain Sensor GND
            └──── Relay Module GND
```

---

## REQUIRED ARDUINO LIBRARIES

Install via **Arduino IDE → Sketch → Include Library → Manage Libraries**:

| Library | Author | Install name |
|---------|--------|-------------|
| DHT sensor library | Adafruit | `DHT sensor library` |
| Adafruit Unified Sensor | Adafruit | `Adafruit Unified Sensor` |
| ArduinoJson | Benoit Blanchon | `ArduinoJson` (install v6.x) |

> **WiFi** and **HTTPClient** come built-in with the ESP32 Arduino core — no extra install needed.

---

## ARDUINO IDE BOARD SETTINGS

Go to **Tools** menu:

| Setting | Value |
|---------|-------|
| Board | `ESP32 Dev Module` |
| Upload Speed | `921600` |
| CPU Frequency | `240MHz` |
| Port | COM port your ESP32 is on |

---

## SETUP CHECKLIST

- [ ] Wire all sensors as shown above
- [ ] Open `AgriSense_ESP32.ino` in Arduino IDE
- [ ] Edit **CONFIGURATION section** at the top of the `.ino`:
  - [ ] `WIFI_SSID` → your Wi-Fi network name
  - [ ] `WIFI_PASSWORD` → your Wi-Fi password
  - [ ] `SUPABASE_URL` / `SUPABASE_ANON_KEY` → from your Supabase project's API settings
  - [ ] `DEVICE_ID` → unique ID like `AGS-0001`
  - [ ] `PAIRING_SECRET` → must match the secret seeded for this `DEVICE_ID` in `device_registry`
        (see `documents/supabase_presence_and_pairing.sql`)
- [ ] Install 3 libraries listed above
- [ ] Select Board: **ESP32 Dev Module**
- [ ] Click Upload
- [ ] Open Serial Monitor at **115200 baud** — you should see the boot self-test, Wi-Fi connecting,
      then sensor readings
- [ ] Open website → Log in → Go to Connect page → Enter device ID → Click **Initialize Node Pairing**
- [ ] Dashboard should start showing live telemetry within 10 seconds

---

> Flashing the ESP32-CAM (separate board, no USB port, manual boot mode) is
> covered in [ESP32CAM_UPLOAD_GUIDE.md](ESP32CAM_UPLOAD_GUIDE.md).
