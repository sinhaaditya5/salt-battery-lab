#!/usr/bin/env python3
"""Screenshots of the EC2 build-host work -> DELIVERABLES/11_screenshots/09_project_salt_ec2/

  spreadsheet_page_NN.png   SaltIron_Engineering_Model.xlsx as LibreOffice renders it (PDF export -> PNG)
  spreadsheet_Cell_BOM.png  the page that holds the Cell_BOM sheet
  kicad_schematic_pNN.png   SCM-1 schematic (kicad-cli PDF -> PNG);  kicad_pcb_top.png / kicad_pcb_bottom.png (kicad-cli pcb render)
  console_*.png             terminal captures: pytest, toolchain versions, DFT campaign log, Octave run, render times, drawing status
Usage (build host): python tools/ec2_build/make_screens.py
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
import pypdfium2 as pdfium

LAB = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(LAB / "tools"))
import snap  # noqa: E402
OUT = LAB / "DELIVERABLES/11_screenshots/09_project_salt_ec2"; OUT.mkdir(parents=True, exist_ok=True)
SOFF = os.environ.get("SOFFICE") or shutil.which("soffice"); KCLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli")


def pdf_pages(pdf, stem, scale=1.6, maxn=12):
    doc = pdfium.PdfDocument(str(pdf)); outs = []
    for i in range(min(len(doc), maxn)):
        p = OUT / f"{stem}_{'page' if 'spread' in stem else 'p'}{i + 1:02d}.png"; doc[i].render(scale=scale).to_pil().convert("RGB").save(p); outs.append((i, p, doc[i]))
    return doc, outs


def spreadsheet():
    x = LAB / "PROJECT_SALT/10_ECONOMICS/SaltIron_Engineering_Model.xlsx"; tmp = Path(tempfile.mkdtemp(dir="/tmp"))
    subprocess.run([SOFF, f"-env:UserInstallation=file://{tmp}/lo", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(x)], capture_output=True, timeout=180)
    pdf = tmp / (x.stem + ".pdf")
    if not pdf.exists(): return "no pdf"
    doc, outs = pdf_pages(pdf, "spreadsheet", 1.6, 20)
    for i, p, page in outs:
        if "Cell materials total" in page.get_textpage().get_text_range():
            shutil.copy(p, OUT / "spreadsheet_Cell_BOM.png"); break
    return f"{len(outs)} pages"


def kicad():
    b = LAB / "pcb/scell_monitor"; res = []
    pdf = b / "fab/scell_monitor-schematic.pdf"
    if pdf.exists(): _, o = pdf_pages(pdf, "kicad_schematic", 1.4, 6); res.append(f"{len(o)} schematic pages")
    for side in ("top", "bottom"):
        r = subprocess.run([KCLI, "pcb", "render", "--side", side, "--width", "1600", "--height", "1100", "-o", str(OUT / f"kicad_pcb_{side}.png"),
                            str(b / "scell_monitor.kicad_pcb")], capture_output=True, text=True, timeout=300)
        res.append(f"{side} render rc={r.returncode}")
    return res


def consoles():
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/", "-p", "no:cacheprovider"], cwd=LAB, capture_output=True, text=True, timeout=900)
    snap.render(r.stdout[-6000:], OUT / "console_pytest_ec2.png", title="pytest tests/ on the EC2 build host (c7i.8xlarge)")
    for src, name, title in (("/work/logs/versions.txt", "console_toolchain.png", "EC2 build-host toolchain (tools/ec2_build/bootstrap.sh)"),
                             (str(LAB / "sim/s11_dft_chlorides/runs/campaign.log"), "console_dft_campaign.png", "S11 DFT campaign log (M4 + EC2)"),
                             (str(LAB / "renders/out_salt/render_times.json"), "console_render_times.png", "Blender Cycles render times (CPU, 32 cores)"),
                             (str(LAB / "matlab/stem/stem_manifest.json"), "console_octave_stems.png", "MATLAB stem scripts executed with GNU Octave"),
                             (str(LAB / "PROJECT_SALT/10_ECONOMICS/salt_model_check.json"), "console_spreadsheet_check.png", "LibreOffice recalculation check")):
        if Path(src).exists():
            snap.render(Path(src).read_text()[-6000:], OUT / name, title=title)
    st = json.load(open(LAB / "cad/out/smodule/smodule_meta.json")).get("drawings", {})
    snap.render(json.dumps(st, indent=1), OUT / "console_cadcraft_drawings.png", title="CADCraft drawing status (cad/make_smodule.py)")
    return f"pytest rc={r.returncode}"


if __name__ == "__main__":
    print("spreadsheet:", spreadsheet()); print("kicad:", kicad()); print("consoles:", consoles())
    print(sorted(p.name for p in OUT.glob("*.png")))
