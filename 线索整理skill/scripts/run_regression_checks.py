#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
BUILD_SCRIPT = SCRIPT_DIR / "build_lead_screening_report.py"

CASES = [
    {
        "label": "sample-leads",
        "input_path": SKILL_ROOT / "examples" / "sample-leads.json",
        "must_include": [
            "Ready for Customer Intel: 2",
            "lead-002",
            "当前只有邮箱线索，建议先补公司名或官网再进入客户背调。",
            "\"company_name\": \"GreenHarvest Foods\"",
        ],
    },
    {
        "label": "textile-leads",
        "input_path": SKILL_ROOT / "examples" / "textile-leads.json",
        "must_include": [
            "Need Enrichment: 1",
            "邮箱使用公共域名，不能直接当作企业身份强证据。",
            "atelier-loom.de",
            "enrich_then_customer_intel",
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
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, f"{case['label']}: failed with {proc.stderr.strip() or proc.stdout.strip()}"
    output = proc.stdout
    checks = ["# Lead Screening Package", "## Summary", "## lead-001", "Customer Intel Input"]
    missing = [item for item in checks if item not in output]
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
