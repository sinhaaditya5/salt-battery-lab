"""Forbidden-phrase and every-number-has-a-claim linter over the generated investor documents."""
import pathlib
import pytest
from lint import lint

DOCS = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab/DELIVERABLES/1_investor_docs")
FILES = ["SaltBattery_Investor_Deck.pptx", "SaltBattery_Technical_and_Business_Report.docx", "SaltBattery_OnePager.docx"]


@pytest.mark.parametrize("name", FILES)
def test_document_lint(name):
    p = DOCS / name
    assert p.exists(), f"{name} not generated"
    n, problems = lint(p)
    assert n > 10, "suspiciously few quantitative statements parsed"
    assert not problems, "\n".join(f"{w} [{k}] {h}: {t}" for w, k, h, t in problems[:40])
