"""One chart style for every Salt Battery figure (print + screen, static PNG 300 dpi + SVG).

Palette = the dataviz skill's validated reference instance (light mode, since figures are embedded
in docx/pptx on white). Categorical slots are assigned in FIXED order, never cycled; >3 series on a
scatter -> facet or fold. Text never wears series colour. Hairline solid grid, 2 px lines, >=8 px markers.
Every saved figure carries a caption with its claim tags (written next to the image as .caption.txt).
"""
from __future__ import annotations
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e6e5e1"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGING = ("#2a78d6", "#f0efec", "#e34948")
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}
DEEMPH = "#b9b8b2"

# Entity -> fixed colour (colour follows the entity in every chart, never its rank)
ENTITY = {
    "LFP": SERIES[0], "Li-ion": SERIES[0], "Salt R1": SERIES[1], "R1": SERIES[1], "Ours": SERIES[1],
    "CATL Na-ion": SERIES[2], "Na-ion": SERIES[2], "Aquion": SERIES[3], "Lead-acid": SERIES[4], "VRLA": SERIES[4],
    "MACE-MP-0b3": SERIES[0], "MACE-MP-0": SERIES[2], "CHGNet": SERIES[1], "DFT+U": SERIES[6], "Literature": TEXT,
}


def apply():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans", "font.size": 9.5, "axes.titlesize": 11, "axes.titleweight": "bold",
        "axes.labelsize": 9.5, "axes.labelcolor": TEXT2, "axes.edgecolor": GRID, "axes.linewidth": 0.8,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": TEXT2, "ytick.color": TEXT2, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "xtick.major.size": 0, "ytick.major.size": 0, "legend.frameon": False, "legend.fontsize": 8.5,
        "lines.linewidth": 2.0, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
        "lines.markersize": 7, "axes.prop_cycle": matplotlib.cycler(color=SERIES),
        "text.color": TEXT, "svg.fonttype": "none", "figure.dpi": 110,
    })


def save(fig, out_base, caption: str, tags: str):
    """Save PNG (300 dpi) + SVG and write the caption (with claim tags) beside them."""
    out = pathlib.Path(out_base)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    out.with_suffix(".caption.txt").write_text(f"{caption} {tags}".strip() + "\n")
    plt.close(fig)


def note(ax, text, loc="lower right"):
    """Small muted source/tag note inside the axes."""
    x, ha = (0.99, "right") if "right" in loc else (0.01, "left")
    y, va = (0.02, "bottom") if "lower" in loc else (0.98, "top")
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, fontsize=7.2, color=MUTED)


apply()
