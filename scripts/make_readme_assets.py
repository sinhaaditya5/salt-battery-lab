#!/usr/bin/env python3
"""Build the README imagery in docs/assets/ from the lab's pipeline outputs.

Reads the full-resolution outputs written by the generators (renders/, sim/*/out, diagrams/out,
drawings/out, pcb/) and writes web-sized copies:

  docs/assets/banner.jpg                 hero render with title overlay
  docs/assets/renders/*.jpg              R1, SM-48T, SC-UPS-1, P1, S-cell stills and the SCM-1 board
  docs/assets/sm48t_turntable.gif        SM-48T module turntable loop (needs ffmpeg)
  docs/assets/charts/*.png               simulation charts
  docs/assets/diagrams/*.png             system and business diagrams
  docs/assets/drawing/*.png              general-arrangement drawings

Usage:
  python scripts/make_readme_assets.py [--out PATH]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MAX_W = 1600

# output name -> source (relative to the repository root)
RENDERS = {
    "r1_hero": "renders/out/hero.png",
    "r1_exploded_annotated": "renders/out/exploded_annotated.png",
    "r1_ups_room": "renders/out/room.png",
    "sm48t_module": "renders/out_salt/module_hero.png",
    "sm48t_cutaway": "renders/out_salt/module_cutaway_captioned.png",
    "sc_ups1_cabinet_open": "renders/out_salt/cabinet_open.png",
    "p1_cell_exploded": "renders/out_salt/p1_exploded_captioned.png",
    "s_cell_r0": "renders/out_salt/r0_hero.png",
    "scm1_pcb_top": "pcb/scell_monitor/fab/scell_monitor-top.png",
}
CHARTS = [
    "sim/s12_chemistry_matrix/out/s12_pareto.png",
    "sim/s12_chemistry_matrix/out/s12_energy_ladder.png",
    "sim/s11_dft_chlorides/out/s11_voltage_vs_U.png",
    "sim/s11_dft_chlorides/out/s11_pdos.png",
    "sim/s13_founder_targets/out/s13a_fast_charge_benchmark.png",
    "sim/s13_founder_targets/out/s13b_three_dollar.png",
    "sim/s14_scell_model/out/s14_scell_curves.png",
    "sim/s15_factory/out/s15_factory_and_tornado.png",
    "sim/s05_atomistic/out/s05_voltage_parity.png",
    "sim/s03_r1_cell/out/s03_retention_vs_loading.png",
    "sim/s09_tea/out/s09_cost_waterfall.png",
    "sim/s09_tea/out/s09_ups_tco.png",
    "sim/s02_pybamm_validation/out/s02_validation_discharge.png",
    "sim/s04_gas/out/s04_water_window.png",
    "sim/s08_thermal/out/s08_monobloc_ups_temperature.png",
    "sim/s16_module_thermal/out/s16_thermal.png",
    "sim/s07_buildup/out/s07_energy_density_comparison.png",
    "sim/s10_market/out/s10_tam_sam_som.png",
]
DIAGRAMS = [
    "d1_system_architecture", "ds1_cell_electrochemistry", "ds2_module_electrical", "d5_safety_comparison",
    "d4_validation_ladder", "ds5_gate_ladder", "d7_unit_economics_waterfall", "d8_roadmap_gantt",
]
DRAWINGS = ["SB-GA-001", "SB-SM-001"]
TURNTABLE = "renders/out_salt/sm48t_turntable.mp4"

FONT_CANDIDATES = {
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "regular": ["/System/Library/Fonts/Supplemental/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}


def font(kind: str, size: int) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES[kind]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def fit_width(im: Image.Image, width: int = MAX_W) -> Image.Image:
    if im.width <= width:
        return im
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def flatten(im: Image.Image) -> Image.Image:
    """RGB copy with any transparency composited onto white (KiCad renders have alpha)."""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.getchannel("A"))
        return bg
    return im.convert("RGB")


def save_jpg(src: Path, dst: Path, quality: int = 86) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    fit_width(flatten(Image.open(src))).save(dst, quality=quality, optimize=True, progressive=True)


def save_png(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    fit_width(flatten(Image.open(src))).save(dst, optimize=True)


def banner(hero: Path, dst: Path) -> None:
    """1600x520 banner: title on the render's own studio backdrop (left), hero render (right)."""
    W, H = 1600, 520
    render_w, offset_x = 960, 640
    shot = Image.open(hero).convert("RGB")
    shot = shot.resize((render_w, round(shot.height * render_w / shot.width)), Image.LANCZOS)
    top = max(0, (shot.height - H) // 2)
    shot = shot.crop((0, top, render_w, top + H))

    # Background: vertical gradient sampled from the render's left edge, so the studio backdrop continues.
    edge = shot.crop((0, 0, 8, H)).resize((1, H), Image.LANCZOS)
    bg = edge.resize((W, H), Image.NEAREST)

    # Horizontal alpha ramp so the render dissolves into the background.
    ramp = Image.new("L", (render_w, H))
    px = ramp.load()
    fade = 260
    for x in range(render_w):
        a = 255 if x >= fade else int(255 * (x / fade) ** 1.6)
        for y in range(H):
            px[x, y] = a
    im = bg.copy()
    im.paste(shot, (offset_x, 0), ramp.filter(ImageFilter.GaussianBlur(4)))

    d = ImageDraw.Draw(im)
    x0 = 64
    d.text((x0, 140), "Salt Battery Lab", font=font("bold", 74), fill=(18, 24, 38))
    d.text((x0, 238), "aqueous sodium-ion and salt-iron battery study", font=font("regular", 31), fill=(52, 62, 82))
    d.text((x0, 281), "+ R1 UPS block, SM-48T module and S-cell concepts", font=font("regular", 31), fill=(52, 62, 82))
    d.rectangle((x0, 348, x0 + 120, 353), fill=(36, 86, 199))
    d.text((x0, 372), "DFT · cell models · CAD · PCB · techno-economics · go/no-go",
           font=font("regular", 22), fill=(84, 96, 118))
    d.text((x0, 404), "pre-prototype · every number evidence-tagged",
           font=font("regular", 22), fill=(84, 96, 118))
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=88, optimize=True, progressive=True)


def turntable_gif(video: Path, dst: Path, width: int = 600, fps: int = 12) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not video.exists():
        print(f"skip turntable GIF (ffmpeg={bool(ffmpeg)}, video={video.exists()})")
        return False
    with tempfile.TemporaryDirectory() as tmp:
        palette = Path(tmp) / "palette.png"
        vf = f"fps={fps},scale={width}:-1:flags=lanczos"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(video),
                        "-vf", f"{vf},palettegen=stats_mode=diff", str(palette)], check=True)
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(video), "-i", str(palette),
                        "-lavfi", f"{vf}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4",
                        "-loop", "0", str(dst)], check=True)
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "assets")
    args = ap.parse_args()
    O = args.out

    banner(ROOT / RENDERS["r1_hero"], O / "banner.jpg")
    for name, src in RENDERS.items():
        save_jpg(ROOT / src, O / "renders" / f"{name}.jpg")
    turntable_gif(ROOT / TURNTABLE, O / "sm48t_turntable.gif")
    for src in CHARTS:
        save_png(ROOT / src, O / "charts" / Path(src).name)
    for name in DIAGRAMS:
        save_png(ROOT / "diagrams" / "out" / f"{name}.png", O / "diagrams" / f"{name}.png")
    for name in DRAWINGS:
        save_png(ROOT / "drawings" / "out" / f"{name}.png", O / "drawing" / f"{name}.png")

    files = [f for f in O.rglob("*") if f.is_file()]
    print(f"wrote {len(files)} files, {sum(f.stat().st_size for f in files) / 1e6:.1f} MB -> {O}")


if __name__ == "__main__":
    main()
