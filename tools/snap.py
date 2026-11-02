"""Render console text (a log file or stdin) into a terminal-style PNG "screenshot" with a timestamp.

Usage:
  python tools/snap.py <logfile|-> <out.png> --title "what ran" [--tail 60]
  some_command 2>&1 | python tools/snap.py - DELIVERABLES/11_screenshots/02_tests/x.png --title "pytest"
"""
import argparse, datetime, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG, FG, DIM, OK, BAD = "#1a1a19", "#f0efec", "#8a8984", "#3fbf6f", "#e66767"


def render(text, out, title="", tail=70, width=110):
    lines = [l.rstrip("\n") for l in text.splitlines()]
    lines = [l for l in lines if "Warning" not in l and "warn(" not in l][-tail:]
    lines = [l if len(l) <= width else l[: width - 1] + "…" for l in lines]
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z").strip()
    h = 0.6 + 0.165 * (len(lines) + 3)
    fig = plt.figure(figsize=(11.5, h), dpi=130)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_facecolor(BG)
    y = 1 - 0.35 / h
    ax.text(0.012, y, f"$ {title}", color=FG, fontsize=9.5, family="monospace", weight="bold", va="top", transform=ax.transAxes)
    ax.text(0.988, y, stamp + "  ·  Salt-Battery-Lab", color=DIM, fontsize=8, family="monospace", ha="right", va="top", transform=ax.transAxes)
    y -= 0.33 / h
    for l in lines:
        low = l.lower()
        col = BAD if any(w in low for w in ("fail", "error", "traceback")) and "0 failed" not in low else (OK if any(w in low for w in ("pass", " ok", "done", "converged")) else FG)
        ax.text(0.012, y, l.replace("$", r"\$"), color=col, fontsize=8, family="monospace", va="top", transform=ax.transAxes)
        y -= 0.165 / h
    out = pathlib.Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=BG)
    plt.close(fig)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("--title", default=""); ap.add_argument("--tail", type=int, default=70)
    a = ap.parse_args()
    txt = sys.stdin.read() if a.src == "-" else pathlib.Path(a.src).read_text(errors="ignore")
    print(render(txt, a.out, a.title or a.src, a.tail))
