#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
BUILD_SCRIPT = SCRIPT_DIR / "build_email_draft.py"
SCHEMA_PATH = SKILL_ROOT / "schemas" / "email-draft-input.schema.json"

CASES = [
    {
        "label": "first-touch",
        "input_path": SKILL_ROOT / "examples" / "first-touch.json",
        "must_include": [
            "Email Type: First Touch",
            "Our purpose is simple:",
            "Please let me know if you would be open to a short exchange on this.",
            "邮件中涉及客户画像摘要的信息时，应核对其是否来自已确认的公开资料。",
        ],
    },
    {
        "label": "follow-up",
        "input_path": SKILL_ROOT / "examples" / "follow-up.json",
        "must_include": [
            "Email Type: Follow Up",
            "I wanted to check in specifically about our earlier introduction",
            "跟进内容引用了历史沟通背景，请确认时间点、附件和表达与实际一致。",
            "Please let me know whether it would be helpful for me to send the next details or samples.",
        ],
    },
    {
        "label": "solar-first-touch",
        "input_path": SKILL_ROOT / "examples" / "solar-first-touch.json",
        "must_include": [
            "Residential Hybrid Inverter Systems Supply for SunGrid Solutions",
            "We understand your team is active in the Chile market.",
            "Shenzhen PowerNest Energy",
        ],
    },
    {
        "label": "textile-follow-up",
        "input_path": SKILL_ROOT / "examples" / "textile-follow-up.json",
        "must_include": [
            "Checking Whether Washed Linen Table Textile Collections Samples Would Help",
            "I wanted to check in specifically about our catalog sharing",
            "Keep the follow-up soft and design-oriented.",
        ],
    },
]


def run_case(case: dict) -> tuple[bool, str]:
    label = case["label"]
    input_path = case["input_path"]
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--input-json",
            str(input_path),
            "--schema-path",
            str(SCHEMA_PATH),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, f"{label}: failed with {proc.stderr.strip() or proc.stdout.strip()}"

    output = proc.stdout
    checks = [
        "# Email Draft Package",
        "## Subject Options",
        "## Draft Version A",
        "## Review Notes",
        "## Input Signals Used",
    ]
    missing = [item for item in checks if item not in output]
    if missing:
        return False, f"{label}: missing expected sections: {', '.join(missing)}"
    missing_phrases = [item for item in case.get("must_include", []) if item not in output]
    if missing_phrases:
        return False, f"{label}: missing expected phrases: {', '.join(missing_phrases)}"
    return True, f"{label}: ok"


def main() -> None:
    results = []
    failed = False
    for case in CASES:
        ok, message = run_case(case)
        results.append({"case": case["label"], "ok": ok, "message": message})
        if not ok:
            failed = True

    sys.stdout.write(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
