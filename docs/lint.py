"""Claims linter for generated investor documents (docx/pptx/md).

Rules
1. Forbidden phrases never appear (case-insensitive).
2. Every text block (paragraph / table cell / text frame) that contains a quantitative number carries a
   claim tag ([LIT] [VENDOR] [CALC] [SIM] [ASSUMPTION] [TARGET]) or a claim id (C-nnn), or sits in a block
   that does (same table row / same slide text frame). Years, dates, IDs (S3, K1, D-05, SRC-...), page/slide
   numbers, section numbers and file names are not counted as quantitative numbers.
3. [MEASURED] never appears.
"""
from __future__ import annotations
import re, pathlib, sys

FORBIDDEN = ["zero risk", "cannot fail", "proven", "breakthrough", "5×", "5x energy", "1,500 km", "1500 km", "ev-ready",
             "patented", "partnership", "letter of intent", "[measured]"]
ALLOWED_CONTEXT = {"partnership": ["no partnership", "not a partnership", "partnership or loi"],
                   "letter of intent": ["non-binding letter of intent", "letter of intent (non-binding)"]}
TAG_RE = re.compile(r"\[(LIT|VENDOR|CALC|SIM|ASSUMPTION|TARGET)[^\]]*\]|C-\d{3}")
NUM_RE = re.compile(r"(?<![A-Za-z\-/_.])(\d[\d,]*\.?\d*)\s*(%|x|×|V|Wh|kWh|MWh|GWh|kg|Wh/kg|Wh/L|mAh|mg|cm|mm|K|°C|C\b|\$|M|k|kW|MW|GW|eV|Å|cycles|years|y\b|min|h\b|towers|lakh|crore|INR|₹|per)", re.I)
MONEY_RE = re.compile(r"[$₹]\s?\d")
SKIP_RE = re.compile(r"\b(19|20)\d{2}\b|\b[SKDC]-?\d{1,3}\b|SRC-\d+|page \d+|slide \d+|§\d|\bv\d\b|\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", re.I)


def quantitative(text: str) -> bool:
    t = SKIP_RE.sub(" ", text)
    return bool(NUM_RE.search(t) or MONEY_RE.search(t))


def forbidden_hits(text: str):
    low = text.lower()
    hits = []
    for f in FORBIDDEN:
        if f in low:
            if any(ok in low for ok in ALLOWED_CONTEXT.get(f, [])):
                continue
            if f == "proven" and re.search(r"\b(un)?proven\b", low) is None:
                continue
            hits.append(f)
    return hits


def blocks_docx(path):
    from docx import Document
    d = Document(path)
    for p in d.paragraphs:
        yield "para", p.text, p.text                      # strict: same paragraph
    for t in d.tables:
        for row in t.rows:
            rowtext = " | ".join(c.text for c in row.cells)
            for c in row.cells:
                yield "cell", c.text, rowtext


def blocks_pptx(path):
    from pptx import Presentation
    prs = Presentation(path)
    for i, s in enumerate(prs.slides, 1):
        slide_text = []
        for sh in s.shapes:
            if sh.has_text_frame:
                slide_text.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                for r in sh.table.rows:
                    slide_text.append(" | ".join(c.text for c in r.cells))
        for sh in s.shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    txt = "".join(r.text for r in p.runs)
                    yield f"slide {i}", txt, txt          # strict: the tag must be in the same paragraph
            if getattr(sh, "has_table", False) and sh.has_table:
                for r in sh.table.rows:
                    rt = " | ".join(c.text for c in r.cells)
                    for c in r.cells:
                        yield f"slide {i} table", c.text, rt
        if s.has_notes_slide:
            yield f"slide {i} notes", s.notes_slide.notes_text_frame.text, s.notes_slide.notes_text_frame.text


def lint(path):
    path = pathlib.Path(path)
    gen = blocks_docx(path) if path.suffix == ".docx" else blocks_pptx(path)
    problems = []
    n_quant = 0
    for where, text, context in gen:
        if not text.strip():
            continue
        for h in forbidden_hits(text):
            problems.append((where, "forbidden", h, text[:120]))
        if "notes" in where:
            continue
        if quantitative(text):
            n_quant += 1
            if not (TAG_RE.search(text) or TAG_RE.search(context)):
                problems.append((where, "untagged number", "", text[:140]))
    return n_quant, problems


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        n, probs = lint(p)
        print(f"{p}: {n} quantitative blocks, {len(probs)} problems")
        for w, kind, h, t in probs[:60]:
            print(f"  [{kind}] {w}: {h} :: {t}")
        bad += len(probs)
    sys.exit(1 if bad else 0)
