#!/usr/bin/env python3
"""Render every salt-design shot with renders/blender_salt.py, add a caption strip, encode the module turntable.

  python renders/run_salt_renders.py [--shots a,b,...] [--samples-scale 1.0] [--frames 96]
Outputs renders/out_salt/<shot>.png, <shot>_captioned.png, sm48t_turntable.mp4, render_times.json
Captions state what the image is: a Cycles render of the build123d CAD (concept), not a photograph of hardware.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent; LAB = HERE.parent; OUT = HERE / "out_salt"; OUT.mkdir(exist_ok=True)
BLENDER = os.environ.get("BLENDER", "blender")
SHOTS = {  # shot: (samples, caption)
    "r0_hero": (128, "S-cell R0 planar salt-iron TEST CELL (30 mm beta''-alumina disc) - assembled"),
    "r0_exploded": (128, "S-cell R0 test cell - exploded (items as drawing SB-SC-001)"),
    "p1_exploded": (128, "P1 planar product cell 150 mm - anode can | beta''-alumina plate + alpha frame | cathode can (concept)"),
    "module_hero": (128, "SM-48T 48 V / 2.27 kWh salt-iron module, 7U 19-inch (concept)"),
    "module_cutaway": (160, "SM-48T cutaway - 84 P1 cells in 4 columns, heaters, 40 mm evacuated insulation, cold BMS bay"),
    "module_exploded": (128, "SM-48T exploded - outer case, insulation shell, inner hot can lifted; front panel pulled"),
    "cabinet_closed": (128, "SC-UPS-1 cabinet: 3 x SM-48T = 6.8 kWh, 600 x 800 x 1400 mm (concept)"),
    "cabinet_open": (128, "SC-UPS-1 with door open - modules on slide rails, controller, DC breakers"),
}
FONT = next((f for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf") if os.path.exists(f)), None)


def caption(png: Path, text: str):
    im = Image.open(png).convert("RGB"); W, H = im.size; bar = int(H * 0.075)
    out = Image.new("RGB", (W, H + bar), (250, 250, 248)); out.paste(im, (0, 0)); d = ImageDraw.Draw(out)
    f1 = ImageFont.truetype(FONT, int(bar * 0.36)) if FONT else None; f2 = ImageFont.truetype(FONT, int(bar * 0.24)) if FONT else None
    d.text((int(bar * 0.4), H + int(bar * 0.12)), text, fill=(20, 20, 20), font=f1)
    d.text((int(bar * 0.4), H + int(bar * 0.56)), "Render of build123d CAD (Blender Cycles) - CONCEPT, not a photograph; nothing has been built.", fill=(90, 90, 90), font=f2)
    p = png.with_name(png.stem + "_captioned.png"); out.save(p); return p


def main(argv):
    shots = argv[argv.index("--shots") + 1].split(",") if "--shots" in argv else list(SHOTS) + ["module_turntable"]
    k = float(argv[argv.index("--samples-scale") + 1]) if "--samples-scale" in argv else 1.0
    frames = int(argv[argv.index("--frames") + 1]) if "--frames" in argv else 96
    tf = OUT / "render_times.json"; times = json.load(open(tf)) if tf.exists() else {}
    for s in shots:
        t0 = time.time(); log = OUT / f"{s}.log"
        if s == "module_turntable":
            args = [BLENDER, "-b", "--factory-startup", "-P", str(HERE / "blender_salt.py"), "--", s, "--samples", str(int(32 * k)), "--res", "1280x720",
                    "--frames", str(frames), "--out", str(OUT / "sm48t_turntable.png")]
        else:
            args = [BLENDER, "-b", "--factory-startup", "-P", str(HERE / "blender_salt.py"), "--", s, "--samples", str(int(SHOTS[s][0] * k)), "--out", str(OUT / f"{s}.png")]
        with open(log, "w") as fh:
            rc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT).returncode
        dt = time.time() - t0; times[s] = dict(seconds=round(dt, 1), rc=rc)
        if s == "module_turntable" and rc == 0:
            fr = OUT / "sm48t_turntable_frames"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", str(fr / "f_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-crf", "20", str(OUT / "sm48t_turntable.mp4")])
        elif rc == 0 and (OUT / f"{s}.png").exists():
            caption(OUT / f"{s}.png", SHOTS[s][1])
        print(s, rc, f"{dt:.0f}s", flush=True)
        json.dump(times, open(tf, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
