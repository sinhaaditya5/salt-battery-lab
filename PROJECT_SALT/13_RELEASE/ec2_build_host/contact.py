#!/usr/bin/env python3
"""PDF -> page PNGs -> contact sheets for visual QA.  usage: contact.py <pdf> <out_prefix> [per_sheet=6] [cols=3] [scale=1.0]"""
import sys
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image
pdf, pre = sys.argv[1], sys.argv[2]; per = int(sys.argv[3]) if len(sys.argv) > 3 else 6; cols = int(sys.argv[4]) if len(sys.argv) > 4 else 3
sc = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
doc = pdfium.PdfDocument(pdf); pages = [doc[i].render(scale=sc).to_pil().convert("RGB") for i in range(len(doc))]
w = max(p.width for p in pages); h = max(p.height for p in pages); rows = (per + cols - 1) // cols
for k in range(0, len(pages), per):
    sheet = Image.new("RGB", (cols * w, rows * h), "white")
    for i, p in enumerate(pages[k:k + per]): sheet.paste(p, ((i % cols) * w, (i // cols) * h))
    sheet.save(f"{pre}_{k // per + 1:02d}.png")
print(len(pages), "pages")
