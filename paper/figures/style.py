"""Shared plot styling. Greyscale-safe palette: hues also differ in luminance."""
import matplotlib as mpl

# Luminance-ordered so the figures survive greyscale printing.
NAVY = "#1b3a6b"
TEAL = "#2c7f8f"
GREEN = "#3f8f5a"
OLIVE = "#8a8f3a"
AMBER = "#d19024"
RUST = "#b5532a"
CRIMSON = "#8c2f39"
SLATE = "#5a6472"
MIST = "#c9d3dd"
PAPER = "#f4f1ea"

SEQ = [NAVY, TEAL, GREEN, AMBER, RUST, CRIMSON, SLATE]


def apply():
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "axes.edgecolor": "#444444",
        "axes.linewidth": 0.7,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
    })
