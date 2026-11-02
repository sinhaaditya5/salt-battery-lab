"""2-3 minute narrated explainer: deck slides (rendered by LibreOffice) + macOS `say` narration + SRT captions.
Narration numbers come from the claims ledger (values only; the on-screen slides carry the tags)."""
import json, pathlib, subprocess, sys, shutil
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "docs"))
from claims import build
import pypdfium2 as pdfium

C = build(); v = lambda cid: C.v(cid)
OUT = LAB / "video" / "out"; OUT.mkdir(parents=True, exist_ok=True)
TMP = LAB / "video" / "tmp"; shutil.rmtree(TMP, ignore_errors=True); TMP.mkdir(parents=True)
PDF = LAB / "DELIVERABLES/1_investor_docs/SaltBattery_Investor_Deck.pdf"

SCRIPT = [
    (1, "This is Salt Battery: a study of whether a water-based sodium battery can be a company. Nothing has been built yet. Everything you'll see is a simulation, a calculation or a cited source."),
    (2, f"The problem. Lithium is cheap, but indoors it now brings fire engineering. Yet codes reward tested, listed chemistries: an unlisted battery gets a {v('C-008')} kilowatt-hour threshold, stricter than lithium's {v('C-007')}."),
    (4, f"The concept is a twelve-volt block in the lead-acid box size, with a manganese-oxide cathode, a titanium-phosphate anode, and salt water as the electrolyte."),
    (5, "We started with a belief: indoors, we only need lead-acid energy density, and we'd win on installed cost. Our own numbers withdrew that belief. What survived is narrower: codes reward tested chemistries."),
    (7, f"Simulations show a rate cliff. At forty milligrams per square centimetre, a fifteen-minute discharge keeps about {v('C-104').split(' ')[0]} of capacity; thicker electrodes collapse. Our electrochemical model failed its own validation gate, so we use it for trends only."),
    (8, "Safety. There is no thermal-runaway chain: the electrolyte cannot burn, and water absorbs the heat. But hydrogen and the plastic case remain real hazards."),
    (10, f"Competition is honest and hard. Aquion built this chemistry class at {v('C-013')} watt-hours per kilogram and went bankrupt. Non-aqueous sodium-ion firms already sell no-thermal-runaway batteries at far higher energy."),
    (11, f"Unit economics: about {v('C-122')} dollars per kilowatt-hour to make, against {v('C-005')} for a lithium iron phosphate pack. Indoors, it only wins if lithium's fire costs become very large."),
    (12, f"In India, this wedge is about {v('C-126')} million dollars a year, and the part that cares about being allowed indoors is about {v('C-127')} million."),
    (13, "So the first experiment isn't in a lab. It's twenty buyer interviews and two fire-protection quotes. If fewer than three buyers face a large lithium premium, we stop."),
    (14, "Every step on the roadmap has a kill gate, and spending beyond week twelve depends on passing them."),
    (16, "Our verdict: no-go on a factory company today. Go, with conditions, on a twelve-week falsification sprint, and if it fails, pivot to battery fire-code software, where the 2026 code change created real demand."),
]


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip())


def srt_time(t):
    h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"


def main():
    pdf = pdfium.PdfDocument(str(PDF))
    segs, srt, t0 = [], [], 0.0
    for k, (slide, text) in enumerate(SCRIPT):
        img = TMP / f"s{k:02d}.png"
        pdf[slide - 1].render(scale=1.44).to_pil().resize((1920, 1080)).save(img)
        aud = TMP / f"a{k:02d}.aiff"
        subprocess.run(["say", "-r", "175", "-o", str(aud), text], check=True)
        d = dur(aud) + 0.6
        seg = TMP / f"seg{k:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(img), "-i", str(aud), "-c:v", "libx264", "-tune", "stillimage",
                        "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "aac", "-b:a", "128k", "-af", "apad=pad_dur=0.6", "-t", f"{d:.2f}", str(seg)], check=True)
        segs.append(seg)
        srt.append(f"{k+1}\n{srt_time(t0)} --> {srt_time(t0 + d - 0.3)}\n{text}\n")
        t0 += d
    lst = TMP / "list.txt"; lst.write_text("".join(f"file '{s}'\n" for s in segs))
    mp4 = OUT / "SaltBattery_explainer.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(mp4)], check=True)
    (OUT / "SaltBattery_explainer.srt").write_text("\n".join(srt))
    print(f"{mp4} {t0:.1f} s, {len(segs)} segments")


if __name__ == "__main__":
    main()
