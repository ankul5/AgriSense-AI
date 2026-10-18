"""Regenerate Fig. training-curves.pdf from the real per-epoch training log.

Source of truth: ml/artifacts/results_and_accuracy/results.csv (5 epochs,
the one completed training run -- yolo11n-cls on PlantVillage). No numbers
in this script are invented; it only reshapes the committed CSV.
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ml" / "artifacts" / "results_and_accuracy" / "results.csv"
OUT = Path(__file__).resolve().parent / "training_curves.pdf"

rows = list(csv.DictReader(SRC.open()))
epoch = [int(r["epoch"]) for r in rows]
train_loss = [float(r["train/loss"]) for r in rows]
val_loss = [float(r["val/loss"]) for r in rows]
top1 = [float(r["metrics/accuracy_top1"]) * 100 for r in rows]
top5 = [float(r["metrics/accuracy_top5"]) * 100 for r in rows]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 2.8))

ax1.plot(epoch, train_loss, marker="o", label="train loss")
ax1.plot(epoch, val_loss, marker="s", label="val loss")
ax1.set_xlabel("Epoch")
ax1.set_ylabel("Cross-entropy loss")
ax1.set_xticks(epoch)
ax1.legend(fontsize=8)
ax1.grid(alpha=0.3)

ax2.plot(epoch, top1, marker="o", label="val top-1")
ax2.plot(epoch, top5, marker="s", label="val top-5")
ax2.set_xlabel("Epoch")
ax2.set_ylabel("Accuracy (%)")
ax2.set_xticks(epoch)
ax2.set_ylim(90, 101)
ax2.legend(fontsize=8, loc="lower right")
ax2.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(OUT)
print(f"wrote {OUT}")
