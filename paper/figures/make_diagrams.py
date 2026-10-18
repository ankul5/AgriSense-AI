"""Schematic figures. These depict structure and control logic, not measured
data. Every constant annotated here (sampling periods, thresholds, timeouts,
GPIO assignments, frame sizes) is transcribed from the deployed firmware
constants documented in paper/audit.md Section 4.
"""
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style  # noqa: E402

style.apply()
S = style
OUT = os.path.dirname(os.path.abspath(__file__))
COL, DBL = 3.45, 7.16


def save(fig, name):
    fig.savefig(os.path.join(OUT, name))
    plt.close(fig)
    print("wrote", name)


def box(ax, x, y, w, h, text, fc, ec=None, tc="white", fs=6.6, r=0.05):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=fc, edgecolor=ec or fc, lw=0.9,
                                zorder=2))
    ax.annotate(text, (x + w / 2, y + h / 2), ha="center", va="center",
                fontsize=fs, color=tc, zorder=3, linespacing=1.35)


def arrow(ax, p1, p2, text=None, color=None, style_="-|>", rad=0.0, fs=5.8,
          toff=(0, 0), ls="-"):
    c = color or S.SLATE
    ax.annotate("", p2, xytext=p1,
                arrowprops=dict(arrowstyle=style_, lw=0.85, color=c,
                                linestyle=ls,
                                connectionstyle=f"arc3,rad={rad}"))
    if text:
        mx, my = (p1[0] + p2[0]) / 2 + toff[0], (p1[1] + p2[1]) / 2 + toff[1]
        ax.annotate(text, (mx, my), ha="center", va="center", fontsize=fs,
                    color=c, zorder=4,
                    bbox=dict(fc="white", ec="none", pad=0.6))


# --------------------------------------------------------------------------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(DBL, 2.9), constrained_layout=True)
    ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 4.3)

    ax.add_patch(plt.Rectangle((0.05, 0.15), 2.55, 3.95, facecolor=S.PAPER,
                               edgecolor=S.MIST, lw=0.8, zorder=0))
    ax.annotate("FIELD TIER", (1.32, 3.92), ha="center", fontsize=6.4,
                color=S.SLATE, weight="bold")
    ax.add_patch(plt.Rectangle((3.05, 0.15), 3.6, 3.95, facecolor="#eef3f6",
                               edgecolor=S.MIST, lw=0.8, zorder=0))
    ax.annotate("CLOUD TIER", (4.85, 3.92), ha="center", fontsize=6.4,
                color=S.SLATE, weight="bold")
    ax.add_patch(plt.Rectangle((7.1, 0.15), 2.85, 3.95, facecolor=S.PAPER,
                               edgecolor=S.MIST, lw=0.8, zorder=0))
    ax.annotate("CLIENT TIER", (8.52, 3.92), ha="center", fontsize=6.4,
                color=S.SLATE, weight="bold")

    box(ax, 0.25, 2.45, 2.15, 1.05,
        "Sensor / actuator node\nESP32 DevKit V1\nDHT11 $\\cdot$ soil ADC $\\cdot$ rain $\\cdot$ relay",
        S.NAVY)
    box(ax, 0.25, 0.95, 2.15, 0.95,
        "Imaging node\nESP32-CAM (OV2640)\ndemand-driven capture", S.TEAL)
    box(ax, 0.25, 0.32, 2.15, 0.5, "Pump (relay, NO contact)", S.SLATE, fs=6.2)
    # route along the tier's left margin so it never crosses the imaging node
    ax.plot([0.25, 0.15, 0.15], [2.75, 2.75, 0.57], color=S.CRIMSON, lw=0.85, zorder=1)
    arrow(ax, (0.15, 0.57), (0.25, 0.57), color=S.CRIMSON)
    ax.annotate("actuate", (0.11, 1.9), rotation=90, ha="center", va="center",
                fontsize=5.6, color=S.CRIMSON)

    box(ax, 3.25, 2.45, 1.5, 1.05, "Managed\nPostgres\ntelemetry +\ncommands", S.GREEN)
    box(ax, 4.95, 2.45, 1.5, 1.05, "Application\nbackend\nREST +\nsupervisory\nloop", S.OLIVE)
    box(ax, 3.25, 0.95, 3.2, 0.95,
        "Vision path: on-device classifier (design target)\nwith hosted vision-language fallback",
        S.RUST)

    box(ax, 7.3, 2.45, 2.45, 1.05, "Web dashboard\nMobile application", S.SLATE)
    box(ax, 7.3, 0.95, 2.45, 0.95, "Grower: irrigation\noverride, diagnosis,\nadvisory query",
        "white", S.NAVY, tc=S.NAVY)

    arrow(ax, (2.45, 3.15), (3.2, 3.15), "telemetry, 10 s", S.NAVY, toff=(0, 0.3))
    arrow(ax, (3.2, 2.72), (2.45, 2.72), "commands, 5 s poll", S.NAVY, toff=(0, -0.3))
    arrow(ax, (2.45, 1.42), (3.2, 1.42), "frames, $\\leq$4 fps", S.TEAL, toff=(0, 0.28))
    arrow(ax, (3.2, 1.15), (2.45, 1.15), "idle poll, 3 s", S.TEAL, toff=(0, -0.26))
    arrow(ax, (4.78, 2.98), (4.92, 2.98), color=S.OLIVE)
    arrow(ax, (4.92, 2.62), (4.78, 2.62), color=S.OLIVE)
    arrow(ax, (6.5, 2.98), (7.25, 2.98), "HTTPS", S.OLIVE, toff=(0, 0.26))
    arrow(ax, (6.5, 1.42), (7.25, 1.42), "diagnosis", S.RUST, toff=(0, 0.26))
    arrow(ax, (7.25, 1.9), (6.5, 2.45), "request", S.NAVY, rad=-0.2, toff=(0, 0))

    ax.annotate("closed-loop irrigation decision executes on-node and remains\n"
                "authoritative when the cloud tier is unreachable",
                (1.32, 0.05), ha="center", fontsize=6.0, color=S.CRIMSON,
                style="italic")
    save(fig, "fig_architecture.pdf")


# --------------------------------------------------------------------------
def fig_hardware():
    fig, ax = plt.subplots(figsize=(COL, 2.75), constrained_layout=True)
    ax.set_axis_off(); ax.set_xlim(0, 6); ax.set_ylim(0, 5.2)

    box(ax, 2.05, 1.5, 1.9, 2.3, "ESP32\nDevKit V1\n\n240 MHz\n520 KB SRAM\nWi-Fi 802.11n",
        S.NAVY, fs=6.4)

    sensors = [
        (4.25, "DHT11", "air $T$, RH\nGPIO 4, 1-wire", S.TEAL),
        (3.35, "Capacitive probe", "soil moisture\nGPIO 34, 12-bit ADC", S.GREEN),
        (2.45, "Rain module", "digital, active-LOW\nGPIO 33", S.OLIVE),
    ]
    for y, name, sub, c in sensors:
        box(ax, 0.05, y - 0.38, 1.7, 0.76, f"{name}\n{sub}", c, fs=5.9)
        arrow(ax, (1.78, y), (2.02, min(max(y, 1.9), 3.6)), color=c)

    box(ax, 4.25, 3.0, 1.7, 0.8, "Relay module\nGPIO 16, active-LOW", S.RUST, fs=5.9)
    box(ax, 4.25, 1.85, 1.7, 0.75, "Water pump\nNO contact", S.CRIMSON, fs=5.9)
    arrow(ax, (3.98, 3.4), (4.22, 3.4), color=S.RUST)
    arrow(ax, (5.1, 2.97), (5.1, 2.63), color=S.CRIMSON)

    box(ax, 2.05, 0.35, 1.9, 0.8, "ESP32-CAM\nOV2640, VGA/QVGA\nseparate board", S.TEAL,
        fs=5.9)
    ax.annotate("camera bus reuses GPIO 4/16/34 —\nhence a second board, not one node",
                (3.0, 0.02), ha="center", fontsize=5.6, color=S.SLATE,
                style="italic")
    ax.annotate("derived value:\n$T_{soil}=T_{air}-2.5^{\\circ}$C",
                (0.9, 1.55), ha="center", fontsize=5.7, color=S.CRIMSON)
    save(fig, "fig_hardware.pdf")


# --------------------------------------------------------------------------
def fig_model():
    fig, ax = plt.subplots(figsize=(DBL, 1.95), constrained_layout=True)
    ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 2.5)

    stages = [
        (0.05, 1.45, "Leaf image\n$224\\times224\\times3$", S.SLATE),
        (1.65, 1.45, "Augmentation\nRandAugment, HSV,\nmosaic, erasing", S.OLIVE),
        (3.25, 2.0, "YOLO11n-cls backbone\nImageNet/COCO-pretrained,\nfine-tuned end to end", S.NAVY),
        (5.5, 1.45, "Global pooling\n+ linear head", S.TEAL),
        (7.1, 1.45, "Softmax\n38 classes", S.GREEN),
        (8.7, 1.25, "$\\hat{y}$, confidence", "white"),
    ]
    for x, w, t, c in stages:
        tc = S.NAVY if c == "white" else "white"
        ec = S.NAVY if c == "white" else c
        box(ax, x, 1.15, w, 0.95, t, c, ec, tc=tc, fs=6.2)
        if x > 0.1:
            arrow(ax, (x - 0.12, 1.62), (x - 0.01, 1.62))

    box(ax, 1.65, 0.12, 2.0, 0.72, "Training: 43,444 images\n5 epochs, batch 64, T4 GPU",
        S.MIST, S.SLATE, tc=S.SLATE, fs=6.0)
    box(ax, 4.0, 0.12, 2.0, 0.72, "Validation: 10,861 images\n99.32% top-1 (unaudited)",
        S.MIST, S.SLATE, tc=S.SLATE, fs=6.0)
    box(ax, 6.35, 0.12, 3.3, 0.72,
        "Export: ONNX opset 12, 6.40 MB FP32 $\\rightarrow$ 12.6$\\times$ over base-ESP32 SRAM",
        "#f3dcd8", S.CRIMSON, tc=S.CRIMSON, fs=6.0)
    save(fig, "fig_model.pdf")


# --------------------------------------------------------------------------
def fig_irrigation():
    fig, ax = plt.subplots(figsize=(COL, 3.7), constrained_layout=True)
    ax.set_axis_off(); ax.set_xlim(0, 6); ax.set_ylim(0, 8.4)

    def dec(y, text, fs=5.9):
        box(ax, 1.05, y, 3.9, 0.62, text, "white", S.NAVY, tc=S.NAVY, fs=fs)

    box(ax, 1.05, 7.65, 3.9, 0.6, "Telemetry tick (every 10 s)", S.NAVY, fs=6.2)
    dec(6.85, "probe healthy?  (raw ADC $\\geq$ 10)")
    dec(6.05, "rain detected?")
    dec(5.25, "$m_t \\geq \\theta_{wet} = 70\\%$?")
    dec(4.45, "manual force-stop?")
    dec(3.65, "manual run command?")
    dec(2.85, "$m_t < \\theta_{dry} = 30\\%$?")
    box(ax, 1.05, 2.05, 3.9, 0.62, "hold previous state (anti-chatter band)",
        S.SLATE, fs=5.9)

    for y in (7.65, 6.85, 6.05, 5.25, 4.45, 3.65, 2.85):
        arrow(ax, (3.0, y), (3.0, y - 0.18))

    box(ax, 0.05, 0.95, 1.55, 0.62, "PUMP OFF", S.SLATE, fs=6.4)
    box(ax, 4.4, 0.95, 1.55, 0.62, "PUMP ON", S.GREEN, fs=6.4)

    for y, lab in ((6.85, "no"), (6.05, "yes"), (5.25, "yes"), (4.45, "yes")):
        arrow(ax, (1.02, y + 0.31), (0.82, y + 0.31), color=S.CRIMSON)
        ax.annotate(lab, (0.92, y + 0.46), fontsize=5.4, color=S.CRIMSON,
                    ha="center")
    ax.plot([0.82, 0.82], [1.57, 7.16], color=S.CRIMSON, lw=0.85, zorder=1)
    arrow(ax, (0.82, 1.62), (0.82, 1.59), color=S.CRIMSON)

    for y in (3.65, 2.85):
        arrow(ax, (4.98, y + 0.31), (5.18, y + 0.31), color=S.GREEN)
        ax.annotate("yes", (5.08, y + 0.46), fontsize=5.4, color=S.GREEN,
                    ha="center")
    ax.plot([5.18, 5.18], [1.57, 3.96], color=S.GREEN, lw=0.85, zorder=1)
    arrow(ax, (5.18, 1.62), (5.18, 1.59), color=S.GREEN)

    ax.annotate("Safety interlocks are evaluated before operator intent:\n"
                "a manual run cannot water through rain, wet soil,\n"
                "or a failed probe. Runs cap at 15 min, then 30 min cooldown.",
                (3.0, 0.30), ha="center", fontsize=5.7, color=S.CRIMSON,
                style="italic", linespacing=1.4)
    save(fig, "fig_irrigation.pdf")


# --------------------------------------------------------------------------
def fig_hysteresis():
    fig, ax = plt.subplots(figsize=(COL, 1.9), constrained_layout=True)
    ax.set_xlim(0, 100); ax.set_ylim(-0.35, 1.5)
    ax.set_xlabel("Soil moisture $m_t$ (%)")
    ax.set_yticks([0, 1]); ax.set_yticklabels(["pump off", "pump on"])

    ax.axvspan(0, 30, color=S.CRIMSON, alpha=0.10, lw=0)
    ax.axvspan(30, 70, color=S.AMBER, alpha=0.13, lw=0)
    ax.axvspan(70, 100, color=S.GREEN, alpha=0.11, lw=0)

    ax.plot([0, 30], [1, 1], color=S.GREEN, lw=2.0)
    ax.plot([70, 100], [0, 0], color=S.SLATE, lw=2.0)
    ax.plot([30, 70], [1, 1], color=S.GREEN, lw=1.6, ls=(0, (4, 2)))
    ax.plot([30, 70], [0, 0], color=S.SLATE, lw=1.6, ls=(0, (4, 2)))
    ax.annotate("", (70, 0.93), xytext=(70, 0.07),
                arrowprops=dict(arrowstyle="-|>", color=S.SLATE, lw=1.0))
    ax.annotate("", (30, 0.07), xytext=(30, 0.93),
                arrowprops=dict(arrowstyle="<|-", color=S.GREEN, lw=1.0))

    ax.axvline(30, color=S.CRIMSON, ls=":", lw=0.9)
    ax.axvline(70, color=S.GREEN, ls=":", lw=0.9)
    ax.annotate("$\\theta_{dry}$", (30, 1.33), ha="center", fontsize=7,
                color=S.CRIMSON)
    ax.annotate("$\\theta_{wet}$", (70, 1.33), ha="center", fontsize=7,
                color=S.GREEN)
    ax.annotate("hold band: state persists,\npump does not chatter", (50, 0.5),
                ha="center", fontsize=6.0, color=S.SLATE)
    save(fig, "fig_hysteresis.pdf")


if __name__ == "__main__":
    fig_architecture()
    fig_hardware()
    fig_model()
    fig_irrigation()
    fig_hysteresis()
