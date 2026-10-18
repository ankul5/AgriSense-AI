"""Data-driven figures. Every value is read from a committed artifact or from a
cited published source; nothing here is simulated or estimated.

Sources:
  results.csv / metrics.json  -> ml/artifacts/results_and_accuracy/
  artifact byte sizes         -> os.path.getsize of the committed weight files
  dataset counts              -> ml/configs/sources.yaml, documents/DATASETS.md
  published accuracies        -> cited papers (see refs.bib)
  chip memory specs           -> Espressif datasheets (cited)
"""
import csv
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style  # noqa: E402

style.apply()
S = style

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ART = os.path.join(REPO, "ml", "artifacts", "results_and_accuracy")
OUT = HERE

COL = 3.45   # IEEE single-column width (inches)
DBL = 7.16   # IEEE double-column width


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p)
    plt.close(fig)
    print("wrote", name)


def read_results():
    rows = []
    with open(os.path.join(ART, "results.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: float(v) for k, v in r.items()})
    return rows


# --------------------------------------------------------------------------
# FIG: training curves (real, results.csv)
# --------------------------------------------------------------------------
def fig_training_curves():
    r = read_results()
    ep = [x["epoch"] for x in r]
    tl = [x["train/loss"] for x in r]
    vl = [x["val/loss"] for x in r]
    t1 = [100 * x["metrics/accuracy_top1"] for x in r]
    t5 = [100 * x["metrics/accuracy_top5"] for x in r]
    lr = [x["lr/pg0"] for x in r]
    tm = [x["time"] / 60.0 for x in r]

    fig, ax = plt.subplots(2, 2, figsize=(DBL, 4.0), constrained_layout=True)

    a = ax[0][0]
    a.plot(ep, tl, "o-", color=S.CRIMSON, lw=1.4, ms=4, label="Training loss")
    a.plot(ep, vl, "s--", color=S.NAVY, lw=1.4, ms=4, label="Validation loss")
    a.set_xlabel("Epoch"); a.set_ylabel("Cross-entropy loss")
    a.set_title("(a) Loss convergence")
    a.set_xticks(ep); a.legend(frameon=False)
    for x, y in zip(ep, vl):
        a.annotate(f"{y:.3f}", (x, y), textcoords="offset points",
                   xytext=(0, -11), ha="center", fontsize=6, color=S.NAVY)

    a = ax[0][1]
    a.plot(ep, t1, "o-", color=S.GREEN, lw=1.4, ms=4, label="Top-1")
    a.plot(ep, t5, "^--", color=S.AMBER, lw=1.4, ms=4, label="Top-5")
    a.set_xlabel("Epoch"); a.set_ylabel("Validation accuracy (%)")
    a.set_title("(b) Validation accuracy")
    a.set_xticks(ep); a.set_ylim(93.5, 100.6); a.legend(frameon=False, loc="lower right")
    for x, y in zip(ep, t1):
        a.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
                   xytext=(0, -11), ha="center", fontsize=6, color=S.GREEN)

    a = ax[1][0]
    a.plot(ep, lr, "D-", color=S.TEAL, lw=1.4, ms=4)
    a.set_xlabel("Epoch"); a.set_ylabel("Learning rate")
    a.set_title("(c) Warm-up then cosine decay")
    a.set_xticks(ep)
    a.axvspan(1, 3, color=S.MIST, alpha=0.55, lw=0)
    a.annotate("3-epoch warm-up", (2.0, max(lr) * 0.55), ha="center",
               fontsize=6.5, color=S.SLATE)

    a = ax[1][1]
    a.bar(ep, tm, color=S.SLATE, width=0.55, edgecolor="white", lw=0.6)
    a.set_xlabel("Epoch"); a.set_ylabel("Cumulative wall-clock (min)")
    a.set_title("(d) Training cost, single T4 GPU")
    a.set_xticks(ep)
    for x, y in zip(ep, tm):
        a.annotate(f"{y:.1f}", (x, y), textcoords="offset points",
                   xytext=(0, 2), ha="center", fontsize=6.5)

    save(fig, "fig_training_curves.pdf")


# --------------------------------------------------------------------------
# FIG: dataset composition (real counts)
# --------------------------------------------------------------------------
def fig_dataset():
    fig, ax = plt.subplots(1, 2, figsize=(DBL, 2.55), constrained_layout=True)

    # (a) configured corpus vs. what one completed run actually consumed
    names = ["PlantVillage", "PlantWild", "Cassava", "Rice"]
    conf = [54305, 30030, 21367, 5932]
    used = [54305, 0, 0, 0]
    y = np.arange(len(names))
    a = ax[0]
    a.barh(y + 0.19, conf, height=0.36, color=S.MIST, edgecolor=S.SLATE,
           lw=0.6, label="Configured in pipeline")
    a.barh(y - 0.19, used, height=0.36, color=S.NAVY, edgecolor="white",
           lw=0.6, label="Used in completed run")
    a.set_yticks(y); a.set_yticklabels(names); a.invert_yaxis()
    a.set_xlabel("Images")
    a.set_title("(a) Corpus configured vs. corpus trained on")
    a.legend(frameon=False, loc="lower right")
    for i, (c, u) in enumerate(zip(conf, used)):
        a.annotate(f"{c:,}", (c, i + 0.19), xytext=(3, 0),
                   textcoords="offset points", va="center", fontsize=6.5)
        if u == 0:
            a.annotate("0 — not yet run", (400, i - 0.19), va="center",
                       fontsize=6.5, color=S.CRIMSON)
    a.set_xlim(0, 66000)

    # (b) 38-class PlantVillage taxonomy grouped by crop
    crops = ["Tomato", "Apple", "Corn", "Grape", "Potato", "Cherry", "Peach",
             "Pepper", "Strawberry", "Blueberry", "Orange", "Raspberry",
             "Soybean", "Squash"]
    ncls = [10, 4, 4, 4, 3, 2, 2, 2, 2, 1, 1, 1, 1, 1]
    a = ax[1]
    cols = [S.NAVY if n >= 4 else (S.TEAL if n >= 2 else S.MIST) for n in ncls]
    a.bar(range(len(crops)), ncls, color=cols, edgecolor=S.SLATE, lw=0.5)
    a.set_xticks(range(len(crops)))
    a.set_xticklabels(crops, rotation=55, ha="right")
    a.set_ylabel("Classes in taxonomy")
    a.set_title("(b) 38 classes, unevenly spread over 14 crops")
    for i, n in enumerate(ncls):
        a.annotate(str(n), (i, n), xytext=(0, 1.5), textcoords="offset points",
                   ha="center", fontsize=6.5)
    a.set_ylim(0, 11.4)
    a.annotate("Tomato alone carries 26% of the label space",
               (0.5, 10.3), fontsize=6.5, color=S.CRIMSON)

    save(fig, "fig_dataset.pdf")


# --------------------------------------------------------------------------
# FIG: the laboratory-to-field collapse, published evidence + our position
# --------------------------------------------------------------------------
def fig_gap():
    fig, ax = plt.subplots(figsize=(COL, 2.7), constrained_layout=True)

    labels = ["Mohanty '16\nlab", "Mohanty '16\nexternal", "Salman '25\nbest X-dom.",
              "ViT-B\nX-dom.", "EffNet\nX-dom.", "IncV3\nX-dom.", "This work\nlab"]
    vals = [99.35, 31.40, 68.0, 48.0, 43.0, 41.0, 99.32]
    cols = [S.NAVY, S.CRIMSON, S.GREEN, S.TEAL, S.TEAL, S.TEAL, S.NAVY]
    x = np.arange(len(labels))
    ax.bar(x, vals, color=cols, edgecolor="white", lw=0.6)
    ax.bar([len(labels)], [0], color=S.MIST)

    # the unmeasured cell
    ax.bar([len(labels)], [100], color="none", edgecolor=S.CRIMSON, lw=1.0,
           hatch="///", linestyle="--")
    ax.annotate("?", (len(labels), 50), ha="center", va="center",
                fontsize=13, color=S.CRIMSON, weight="bold")

    ax.set_xticks(list(x) + [len(labels)])
    ax.set_xticklabels(labels + ["This work\nfield"], fontsize=5.6,
                       rotation=38, ha="right", rotation_mode="anchor")
    ax.set_ylabel("Top-1 accuracy (%)")
    ax.set_ylim(0, 112)
    ax.axhspan(0, 50, color=S.CRIMSON, alpha=0.06, lw=0)
    for xi, v in zip(x, vals):
        ax.annotate(f"{v:.1f}", (xi, v), xytext=(0, 1.8),
                    textcoords="offset points", ha="center", fontsize=5.8)
    ax.axhline(68, color=S.GREEN, ls=":", lw=1.0)
    ax.annotate("cross-domain SOTA (68%)", (6.45, 71.5), fontsize=5.8,
                color=S.GREEN, ha="right")
    save(fig, "fig_gap.pdf")


# --------------------------------------------------------------------------
# FIG: memory-budget feasibility analysis (measured sizes vs datasheet limits)
# --------------------------------------------------------------------------
def fig_memory():
    pt = os.path.getsize(os.path.join(ART, "weights", "best.pt"))
    onnx = os.path.getsize(os.path.join(ART, "weights", "species.onnx"))
    KB = 1024.0
    MB = 1024.0 * 1024.0

    items = [
        ("ONNX export\n(FP32, opset 12)", onnx / MB, S.CRIMSON),
        ("PyTorch checkpoint\n(FP32)", pt / MB, S.RUST),
        ("Hypothetical INT8\n(4$\\times$ compression)", onnx / 4 / MB, S.AMBER),
        ("ESP32 SRAM\n(520 KB)", 520 * KB / MB, S.NAVY),
        ("ESP32-S3 SRAM\n(512 KB)", 512 * KB / MB, S.TEAL),
        ("ESP32-S3 + PSRAM\n(8 MB)", 8.0, S.GREEN),
    ]
    fig, ax = plt.subplots(figsize=(COL, 2.45), constrained_layout=True)
    y = np.arange(len(items))
    ax.barh(y, [v for _, v, _ in items], color=[c for _, _, c in items],
            edgecolor="white", lw=0.6, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels([n for n, _, _ in items], fontsize=6.2)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlabel("Memory footprint (MB, log scale)")
    for i, (_, v, _) in enumerate(items):
        ax.annotate(f"{v:.2f} MB", (v, i), xytext=(3, 0),
                    textcoords="offset points", va="center", fontsize=6.2)
    ax.axvline(520 * KB / MB, color=S.SLATE, ls="--", lw=0.8)
    ax.annotate(f"model is {onnx / (520 * KB):.1f}$\\times$ the\nbase-ESP32 SRAM budget",
                (0.62, 0.30), xycoords="axes fraction", fontsize=6.2,
                color=S.CRIMSON)
    ax.set_xlim(0.2, 30)
    save(fig, "fig_memory.pdf")


# --------------------------------------------------------------------------
# FIG: pre-registered H2 prediction grid (clearly a prediction, not a result)
# --------------------------------------------------------------------------
def fig_prediction_grid():
    rows = ["2 cls / 96 px", "2 cls / 224 px", "4 cls / 128 px", "8 cls / 128 px",
            "8 cls / 224 px", "16 cls / 128 px", "16 cls / 224 px"]
    cols = ["ESP32\nFP32", "ESP32\nINT8", "ESP32-S3\nFP32", "ESP32-S3\nINT8"]
    # 1 = predicted to fit, 0 = predicted not to fit
    grid = np.array([
        [1, 1, 1, 1],
        [1, 1, 1, 1],
        [1, 1, 1, 1],
        [1, 1, 1, 1],
        [0, 1, 1, 1],
        [0, 1, 1, 1],
        [0, 0, 0, 1],
    ])
    fig, ax = plt.subplots(figsize=(COL, 2.5), constrained_layout=True)
    cmap = mpl_two_tone()
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, fontsize=6.4)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows, fontsize=6.4)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.annotate("fits" if grid[i, j] else "fails", (j, i),
                        ha="center", va="center", fontsize=6.2,
                        color="white" if grid[i, j] else S.CRIMSON)
    ax.set_xticks(np.arange(-0.5, len(cols), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    ax.grid(which="minor", color="white", lw=1.2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)
    save(fig, "fig_prediction_grid.pdf")


def mpl_two_tone():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("tt", ["#f3dcd8", S.GREEN])


# --------------------------------------------------------------------------
# FIG: experiment dependency map (pre-registration structure)
# --------------------------------------------------------------------------
def fig_protocol():
    fig, ax = plt.subplots(figsize=(DBL, 2.15), constrained_layout=True)
    ax.set_axis_off()
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.1)

    def box(x, y, w, h, text, fc, ec, tc="white", fs=6.6):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                                   lw=0.9, zorder=2, joinstyle="round"))
        ax.annotate(text, (x + w / 2, y + h / 2), ha="center", va="center",
                    fontsize=fs, color=tc, zorder=3, linespacing=1.35)

    def arrow(x1, y1, x2, y2):
        ax.annotate("", (x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", lw=0.8, color=S.SLATE))

    box(0.05, 1.15, 1.5, 0.85, "Completed\nbaseline\n99.32% lab", S.NAVY, S.NAVY)

    box(2.0, 2.15, 1.85, 0.8, "E2 leakage audit\ndup-group re-split", S.TEAL, S.TEAL)
    box(2.0, 1.15, 1.85, 0.8, "E1 field set\n$\\geq$300 own-camera\nimages", S.CRIMSON, S.CRIMSON)
    box(2.0, 0.12, 1.85, 0.8, "E3 edge sweep\nchip$\\times$prec$\\times$cls$\\times$res", S.RUST, S.RUST)

    box(4.35, 2.15, 1.75, 0.8, "E5 ablation\nE6 seeds + $t$-tests", S.OLIVE, S.OLIVE)
    box(4.35, 1.15, 1.75, 0.8, "E7 Grad-CAM\nfailure analysis", S.AMBER, S.AMBER)
    box(4.35, 0.12, 1.75, 0.8, "E4 irrigation trial\nflow-metered, 2 plots", S.GREEN, S.GREEN)

    box(6.6, 1.15, 1.55, 0.8, "E8 reliability\nlatency / uptime", S.SLATE, S.SLATE)
    box(8.35, 1.05, 1.6, 1.0, "RQ1 RQ2 RQ3\nanswered or\nrefuted", "white", S.NAVY,
        tc=S.NAVY, fs=7.0)

    for y in (2.55, 1.55, 0.52):
        arrow(1.6, 1.57, 1.95, y)
    arrow(3.9, 2.55, 4.3, 2.55)
    arrow(3.9, 1.55, 4.3, 1.55)
    arrow(3.9, 0.52, 4.3, 0.52)
    arrow(6.15, 1.55, 6.55, 1.55)
    arrow(8.2, 1.55, 8.3, 1.55)
    for y in (2.55, 0.52):
        arrow(6.15, y, 8.3, 1.62)

    ax.annotate("pre-registered predictions fixed before execution (H2, H3)",
                (5.0, 0.0), ha="center", fontsize=6.3, color=S.CRIMSON,
                style="italic")
    save(fig, "fig_protocol.pdf")


if __name__ == "__main__":
    fig_training_curves()
    fig_dataset()
    fig_gap()
    fig_memory()
    fig_prediction_grid()
    fig_protocol()
