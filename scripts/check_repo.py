#!/usr/bin/env python3
"""Repository integrity gate (standard library only; runs in CI and as a pre-commit hook).

Checks every tracked file for:
  * leaked credentials (AWS keys, private keys, GitHub/Slack/OpenAI-style tokens);
  * files over the size budget (GitHub rejects > 100 MB; we cap at 50 MB);
  * JSON that does not parse and CSV that the csv module cannot read;
  * Python that does not compile;
  * shell scripts without a shebang (files named *env.sh are sourced, so they are exempt).

Usage: python scripts/check_repo.py [--max-mb 50]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = {
    "AWS access key id": re.compile(rb"\b(AKIA|ASIA)[A-Z0-9]{16}\b"),
    "AWS secret key assignment": re.compile(rb"(?i)aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+]{40}"),
    "private key block": re.compile(rb"-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    "GitHub token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "Slack token": re.compile(rb"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    "OpenAI/Anthropic-style key": re.compile(rb"\bsk-(ant-)?[A-Za-z0-9_-]{32,}"),
}
FORBIDDEN_NAMES = {"rootkey.csv", "credentials", ".env"}
TEXT_SUFFIXES = {".py", ".sh", ".md", ".txt", ".json", ".csv", ".yml", ".yaml", ".toml", ".cfg", ".ini",
                 ".m", ".c", ".h", ".in", ".log", ".jsonl", ".svg", ".scad", ".ps1", ".srt", ".xml", ".html"}


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True).stdout
        return [ROOT / p for p in out.decode().split("\0") if p]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-mb", type=float, default=50.0)
    args = ap.parse_args()

    problems: list[str] = []
    files = [p for p in tracked_files() if p.is_file()]
    counts = {"json": 0, "csv": 0, "py": 0, "sh": 0}

    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        size_mb = p.stat().st_size / 1e6
        if size_mb > args.max_mb:
            problems.append(f"{rel}: {size_mb:.1f} MB exceeds {args.max_mb:g} MB budget")
        if p.name in FORBIDDEN_NAMES:
            problems.append(f"{rel}: credential-like filename must never be committed")

        if p.suffix.lower() in TEXT_SUFFIXES and size_mb < 20:
            data = p.read_bytes()
            for label, rx in SECRET_PATTERNS.items():
                if rx.search(data):
                    problems.append(f"{rel}: possible {label}")

        if p.suffix == ".json":
            counts["json"] += 1
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except (ValueError, UnicodeDecodeError) as e:
                problems.append(f"{rel}: invalid JSON ({e})")
        elif p.suffix == ".csv":
            counts["csv"] += 1
            try:
                with p.open(newline="", encoding="utf-8-sig") as fh:
                    sum(1 for _ in csv.reader(fh))
            except (csv.Error, UnicodeDecodeError) as e:
                problems.append(f"{rel}: unreadable CSV ({e})")
        elif p.suffix == ".py":
            counts["py"] += 1
            try:
                compile(p.read_text(encoding="utf-8"), rel, "exec", dont_inherit=True)
            except (SyntaxError, UnicodeDecodeError) as e:
                problems.append(f"{rel}: does not compile ({e})")
        elif p.suffix == ".sh":
            counts["sh"] += 1
            sourced = p.name.endswith("env.sh")          # meant for `source`, not execution
            if not sourced and not p.read_bytes().startswith(b"#!") and "/out/" not in rel and "/runs" not in rel:
                problems.append(f"{rel}: shell script without a shebang")

    print(f"checked {len(files)} files: {counts['py']} Python, {counts['json']} JSON, "
          f"{counts['csv']} CSV, {counts['sh']} shell")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for msg in problems:
            print(f"  - {msg}")
        return 1
    print("repository integrity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
