"""Render every concept shot (Cycles, Metal GPU), annotate it, render + encode the turntable, log the times.

  python renders/run_renders.py [--shots hero,cutaway,...] [--no-turntable] [--frames 300] [--samples-scale 1.0]

Outputs: renders/out/<shot>.png, <shot>_annotated.png, render_times.json,
         renders/out/r1_monobloc_turntable.mp4 (1280x720, 24 fps; 2 revolutions of the rendered frames)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
from params.mech_params import SCENE  # noqa: E402

OUT = HERE / "out"
LOGS = OUT / "logs"
BLENDER = os.environ.get("BLENDER", "/Volumes/Aditya ssd/Applications/Blender.app/Contents/MacOS/Blender")
SHOTS = {"hero": 128, "exploded": 96, "cutaway": 128, "module": 96, "row": 96, "room": 128, "r0": 96}   # samples
FONT_R = "/System/Library/Fonts/Supplemental/Arial.ttf"


def blender(args, log):
    t0 = time.time()
    with open(log, "w") as fh:
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", str(HERE / "blender_scene.py"), "--", *args],
                           stdout=fh, stderr=subprocess.STDOUT)
    return r.returncode, time.time() - t0


def encode_turntable(frames_dir: Path, out_mp4: Path, fps: int, loops: int):
    """Caption every frame, then encode with ffmpeg (system ffmpeg, else imageio-ffmpeg)."""
    ff = shutil.which("ffmpeg")
    if ff is None:
        try:
            import imageio_ffmpeg
            ff = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            raise SystemExit("no ffmpeg: install imageio-ffmpeg into the venv")
    cap = frames_dir.parent / "turntable_captioned"
    cap.mkdir(exist_ok=True)
    for old in cap.glob("c_*.png"):
        old.unlink()
    frames = sorted(frames_dir.glob("f_*.png"))
    f = ImageFont.truetype(FONT_R, 22)
    for k, fr in enumerate(frames):
        img = Image.open(fr).convert("RGB")
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, img.height - 40, img.width, img.height], fill=(10, 14, 24, 170))
        d.text((20, img.height - 32), "R1 12 V aqueous sodium-ion monobloc  |  CONCEPT RENDER - not a photograph of hardware",
               font=f, fill=(225, 230, 240))
        img.save(cap / f"c_{k:04d}.png")
    cmd = [ff, "-y", "-loglevel", "error", "-stream_loop", str(loops - 1), "-framerate", str(fps), "-i", str(cap / "c_%04d.png"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps),
           "-movflags", "+faststart", str(out_mp4)]
    subprocess.run(cmd, check=True)
    return len(frames) * loops / fps


def main(argv):
    shots = argv[argv.index("--shots") + 1].split(",") if "--shots" in argv else list(SHOTS)
    scale = float(argv[argv.index("--samples-scale") + 1]) if "--samples-scale" in argv else 1.0
    frames = int(argv[argv.index("--frames") + 1]) if "--frames" in argv else int(SCENE["turntable_seconds"] * SCENE["turntable_fps"] / 2)
    LOGS.mkdir(parents=True, exist_ok=True)
    tpath = OUT / "render_times.json"
    times = json.loads(tpath.read_text()) if tpath.exists() else {}
    for sh in shots:
        n = max(16, int(SHOTS[sh] * scale))
        rc, dt = blender([sh, "--samples", str(n), "--res", "1920x1080"], LOGS / f"render_{sh}.log")
        times[sh] = dict(seconds=round(dt, 1), samples=n, res="1920x1080", ok=rc == 0)
        print(f"{sh:10s} {n:4d} spp  {dt:6.1f} s  exit {rc}", flush=True)
    subprocess.run([sys.executable, str(HERE / "annotate.py"), *[s for s in shots if (OUT / f"{s}.png").exists()]], check=True)
    if "--no-turntable" not in argv:
        rc, dt = blender(["turntable", "--samples", "32", "--res", "1280x720", "--frames", str(frames)], LOGS / "render_turntable.log")
        dur = encode_turntable(OUT / "turntable", OUT / "r1_monobloc_turntable.mp4", SCENE["turntable_fps"], loops=2)
        times["turntable"] = dict(seconds=round(dt, 1), samples=32, res="1280x720", frames=frames, video_s=dur, ok=rc == 0)
        print(f"turntable  {frames} frames  {dt:6.1f} s  exit {rc}  -> {dur:.1f} s video", flush=True)
    times["_total_seconds"] = round(sum(v["seconds"] for k, v in times.items() if not k.startswith("_")), 1)
    tpath.write_text(json.dumps(times, indent=1))
    print("total render time", times["_total_seconds"], "s")


if __name__ == "__main__":
    main(sys.argv[1:])
