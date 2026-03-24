#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
REGRESSION_SCRIPT = SCRIPT_DIR / "run_regression_checks.py"
OPENCLAW_SCRIPT = SKILL_ROOT / "for-openclaw" / "scripts" / "build_lead_discovery_from_openclaw.py"
OPENCLAW_SAMPLE = SKILL_ROOT / "for-openclaw" / "examples" / "sample-input.json"

REQUIRED_FILES = [
    SKILL_ROOT / "README.md",
    SKILL_ROOT / "SKILL.md",
    SKILL_ROOT / "验收记录.md",
    SKILL_ROOT / "schemas" / "lead-discovery-input.schema.json",
    SKILL_ROOT / "examples" / "frozen-food-output.md",
    SKILL_ROOT / "examples" / "textile-output.md",
    SKILL_ROOT / "for-openclaw" / "README.md",
    SKILL_ROOT / "for-openclaw" / "SKILL.md",
]


def run_command(args: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    message = proc.stdout.strip() or proc.stderr.strip()
    return proc.returncode == 0, message


def main() -> None:
    results = []
    failed = False
    missing_files = [str(path) for path in REQUIRED_FILES if not path.exists()]
    if missing_files:
        failed = True
        results.append(
            {
                "check": "required-files",
                "ok": False,
                "message": f"Missing required files: {', '.join(missing_files)}",
            }
        )
    else:
        results.append({"check": "required-files", "ok": True, "message": "required files present"})

    ok, message = run_command([sys.executable, str(REGRESSION_SCRIPT)])
    results.append({"check": "regression", "ok": ok, "message": message})
    failed = failed or not ok

    ok, message = run_command(
        [
            sys.executable,
            str(OPENCLAW_SCRIPT),
            "--input-json",
            str(OPENCLAW_SAMPLE),
        ]
    )
    results.append({"check": "openclaw-sample", "ok": ok, "message": message})
    failed = failed or not ok

    sys.stdout.write(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
