#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
BUILD_SCRIPT = SCRIPT_DIR / "build_lead_discovery_report.py"

CASES = [
    {
        "label": "frozen-food",
        "input_path": SKILL_ROOT / "examples" / "frozen-food-search.json",
        "fixture_path": SKILL_ROOT / "examples" / "frozen-food-fixtures.json",
        "must_include": [
            "GreenHarvest Foods",
            "https://www.linkedin.com/company/greenharvestfoods",
            "Follow-up Suggestion:",
            "Lead Screening Bridge",
        ],
    },
    {
        "label": "textile",
        "input_path": SKILL_ROOT / "examples" / "textile-search.json",
        "fixture_path": SKILL_ROOT / "examples" / "textile-fixtures.json",
        "must_include": [
            "Atelier Loom GmbH",
            "NordHaus Tableware",
            "Source Type: web",
            "table linen",
        ],
    },
]


def run_case(case: dict) -> tuple[bool, str]:
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--input-json",
            str(case["input_path"]),
            "--fixtures-json",
            str(case["fixture_path"]),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, f"{case['label']}: failed with {proc.stderr.strip() or proc.stdout.strip()}"
    output = proc.stdout
    required_sections = ["# Lead Discovery Package", "## Summary", "## Queries", "## candidate-001"]
    missing = [item for item in required_sections if item not in output]
    if missing:
        return False, f"{case['label']}: missing expected sections: {', '.join(missing)}"
    missing_phrases = [item for item in case["must_include"] if item not in output]
    if missing_phrases:
        return False, f"{case['label']}: missing expected phrases: {', '.join(missing_phrases)}"
    return True, f"{case['label']}: ok"


def main() -> None:
    results = []
    failed = False
    for case in CASES:
        ok, message = run_case(case)
        results.append({"case": case["label"], "ok": ok, "message": message})
        failed = failed or not ok
    sys.stdout.write(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
