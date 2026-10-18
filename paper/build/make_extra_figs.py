"""Extra figures for the DOCX papers: a controller simulation (labelled as
simulation in the paper), a screenshot montage, and the survey taxonomy.
The pump rule is a line-for-line port of pumpShouldRun() in
esp32_firmware/AgriSense_ESP32/AgriSense_ESP32.ino, checked against the
firmware's own 11 boot self-test cases before it is simulated.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PNG = os.path.join(os.path.dirname(HERE), "png")
ROOT = os.path.dirname(os.path.dirname(HERE))
DRY, WET = 30, 70
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"],
                     "font.size": 8, "axes.linewidth": 0.6})


def pump_should_run(pct, ok, rain, on, manual):
    if not ok: return False
    if rain: return False
    if pct >= WET: return False
    if manual < 0: return False
    if manual > 0: return True
    if pct < DRY: return True
    return on


CASES = [(10, 1, 0, 0, 0, 1), (10, 1, 1, 0, 0, 0), (10, 0, 0, 1, 0, 0), (45, 1, 0, 1, 0, 1),
         (45, 1, 0, 0, 0, 0), (80, 1, 0, 1, 0, 0), (10, 1, 0, 0, 1, 1), (10, 1, 1, 1, 1, 0),
         (90, 1, 0, 1, 1, 0), (10, 1, 0, 1, -1, 0), (10, 0, 0, 1, 1, 0)]
assert all(pump_should_run(p, o, r, n, m) == bool(w) for p, o, r, n, m, w in CASES)


def simulate(rule, hours=48, dt=10, seed=7, noise=2.0, dry_rate=2.0, wet_rate=0.12,
             max_run=15 * 60, cool=30 * 60):
    """Bucket soil model: moisture falls dry_rate %/h (ET), rises wet_rate %/tick
    while pumping. Sensor reading adds Gaussian noise. 15 min run cap and
    30 min cooldown as in firmware. Returns trace and switch count."""
    rng = np.random.default_rng(seed)
    m, on, run_t, cool_until, t = 40.0, False, 0, -1, 0
    xs, ms, ps, switches, pump_s = [], [], [], 0, 0
    for k in range(int(hours * 3600 / dt)):
        t = k * dt
        rain = 20 * 3600 <= t < 21 * 3600   # one hour of rain at t=20 h
        read = m + rng.normal(0, noise)
        want = rule(read, True, rain, on, 0)
        if on and run_t >= max_run:
            want, cool_until = False, t + cool
        if not on and want and t < cool_until:
            want = False
        if want != on:
            switches += 1
            run_t = 0
        on = want
        run_t += dt if on else 0
        pump_s += dt if on else 0
        m += (wet_rate if on else 0) + (0.02 if rain else 0) - dry_rate * dt / 3600
        m = float(np.clip(m, 0, 100))
        xs.append(t / 3600); ms.append(m); ps.append(on)
    return np.array(xs), np.array(ms), np.array(ps), switches, pump_s / 60


def single_threshold(pct, ok, rain, on, manual):
    if not ok or rain: return False
    return pct < DRY


def fig_sim():
    res = {}
    fig, axes = plt.subplots(2, 1, figsize=(3.45, 3.1), sharex=True, constrained_layout=True)
    for ax, (name, rule) in zip(axes, [("Single threshold (30 %)", single_threshold),
                                       ("AgriSense hysteresis (30/70 %)", pump_should_run)]):
        x, m, p, sw, mins = simulate(rule)
        res[name] = {"switches": sw, "pump_minutes": round(mins, 1),
                     "min_moisture": round(float(m.min()), 1),
                     "mean_moisture": round(float(m.mean()), 1),
                     "std_moisture": round(float(m.std()), 1)}
        ax.plot(x, m, color="#1B3A6B", lw=0.7)
        ax.fill_between(x, 0, 100, where=p, color="#2C7F8F", alpha=0.18, lw=0)
        ax.axhline(DRY, color="#8C2F39", lw=0.5, ls="--")
        if rule is pump_should_run:
            ax.axhline(WET, color="#2F6B45", lw=0.5, ls="--")
        ax.axvspan(20, 21, color="#9A6912", alpha=0.25, lw=0)
        ax.set_ylim(0, 100); ax.set_ylabel("Soil moisture (%)")
        ax.set_title(f"{name}: {sw} pump switches, {mins:.0f} pump-min", fontsize=7.5)
    axes[1].set_xlabel("Simulated time (h); shaded = pump ON, amber = rain")
    fig.savefig(os.path.join(PNG, "sim_hysteresis.png"), dpi=300)
    plt.close(fig)
    json.dump(res, open(os.path.join(HERE, "sim_results.json"), "w"), indent=2)
    print(json.dumps(res, indent=2))


def montage():
    imgs = [Image.open(os.path.join(ROOT, "documents", "images", f)).convert("RGB")
            for f in ("app-controls.jpg", "app-plant-scan.jpg", "app-advisor.jpg")]
    h = 900
    imgs = [im.resize((int(im.width * h / im.height), h)) for im in imgs]
    gap = 24
    out = Image.new("RGB", (sum(i.width for i in imgs) + gap * 2, h), "white")
    x = 0
    for im in imgs:
        out.paste(im, (x, 0)); x += im.width + gap
    out.save(os.path.join(PNG, "app_montage.png"))


def taxonomy():
    fig, ax = plt.subplots(figsize=(7.16, 3.3))
    ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 5)
    root = (5, 4.55)
    ax.text(*root, "AI + IoT for Smart Agriculture", ha="center", va="center", fontsize=9,
            color="white", weight="bold",
            bbox=dict(boxstyle="round,pad=0.4", fc="#1B3A6B", ec="none"))
    cols = [
        ("Sensing &\nConnectivity (§IV)", "#2C7F8F",
         ["Soil moisture (resistive,\ncapacitive, TDR)", "Air T/RH, rain, light", "Wi-Fi, LoRaWAN,\nNB-IoT, ZigBee",
          "MQTT / HTTPS /\nmanaged BaaS"]),
        ("Irrigation\nControl (§V)", "#2F6B45",
         ["Open-loop timers", "Threshold &\nhysteresis", "ET / water-balance\n(FAO-56)", "ML & DSS scheduling"]),
        ("Disease\nDiagnosis (§VI–VII)", "#B5552B",
         ["Lab datasets\n(PlantVillage)", "Field datasets\n(PlantDoc, Cassava)", "CNN / ViT / YOLO",
          "Domain shift &\nleakage control"]),
        ("Edge AI /\nTinyML (§VIII)", "#9A6912",
         ["MCU (ESP32, Cortex-M)", "Quantization (INT8)", "TFLM / ESP-DL / ONNX", "Memory-aware NAS\n(MCUNet)"]),
        ("LLM Advisory &\nSecurity (§IX–X)", "#5B6577",
         ["Grounded LLM advice", "RAG vs fine-tuning", "Schema-constrained\noutput", "Multi-tenancy, RLS,\ndevice auth"]),
    ]
    for i, (name, c, leaves) in enumerate(cols):
        x = 1.0 + i * 2.0
        ax.annotate("", (x, 3.65), xytext=(root[0], 4.3),
                    arrowprops=dict(arrowstyle="-", color="#999", lw=0.6))
        ax.text(x, 3.4, name, ha="center", va="center", fontsize=7.4, color="white", weight="bold",
                bbox=dict(boxstyle="round,pad=0.35", fc=c, ec="none"))
        for j, leaf in enumerate(leaves):
            y = 2.55 - j * 0.68
            ax.plot([x, x], [y + 0.28, 3.1 if j == 0 else y + 0.4], color=c, lw=0.6)
            ax.text(x, y, leaf, ha="center", va="center", fontsize=6.2, color="#222",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=c, lw=0.7))
    fig.savefig(os.path.join(PNG, "survey_taxonomy.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_sim(); montage(); taxonomy()
