#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PACKAGE_ROOT.parent
DEMO_SCRIPT = SCRIPT_DIR / "run_minimal_demo.py"
FIXTURE_REPORT = PACKAGE_ROOT / "examples" / "reviewed-customer-intel-report.json"

EXPECTED_OUTPUTS = [
    "01-lead-discovery-output.json",
    "02-lead-screening-input.json",
    "03-lead-screening-output.json",
    "03-lead-screening-output.md",
    "04-customer-intel-batch.json",
    "05-selected-customer-intel-input.json",
    "06-customer-intel-report.json",
    "07-email-input.json",
    "08-email-draft.json",
    "08-email-draft.md",
]


def run_demo(output_dir: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(DEMO_SCRIPT), "--output-dir", str(output_dir)],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_outputs_exist(output_dir: Path) -> None:
    missing = [name for name in EXPECTED_OUTPUTS if not (output_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing expected outputs: {', '.join(missing)}")


def assert_selected_lead_matches_fixture(output_dir: Path) -> None:
    selected = load_json(output_dir / "05-selected-customer-intel-input.json")
    report = load_json(output_dir / "06-customer-intel-report.json")
    fixture = load_json(FIXTURE_REPORT)

    selected_company = str(selected.get("company_name", "")).strip()
    report_company = str((report.get("identity_snapshot") or {}).get("company_name", "")).strip()
    fixture_company = str((fixture.get("identity_snapshot") or {}).get("company_name", "")).strip()

    if not selected_company or not report_company:
        raise SystemExit("Selected lead or generated report is missing company_name.")
    if selected_company != report_company or report_company != fixture_company:
        raise SystemExit(
            "Mismatch between selected lead, generated report, and combo-package fixture."
        )


def assert_email_artifacts(output_dir: Path) -> None:
    email_input = load_json(output_dir / "07-email-input.json")
    email_output = load_json(output_dir / "08-email-draft.json")
    email_markdown = (output_dir / "08-email-draft.md").read_text(encoding="utf-8")

    if str(email_input.get("company_name", "")).strip() != "GreenHarvest Foods":
        raise SystemExit("Email bridge payload company_name does not match the stable combo demo.")
    if "subject_options" not in email_output:
        raise SystemExit("Email draft JSON is missing subject_options.")
    if "GreenHarvest Foods" not in email_markdown:
        raise SystemExit("Email draft markdown does not mention the expected company.")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="trade-skill-combo-check-") as temp_dir:
        output_dir = Path(temp_dir) / "demo"
        run_demo(output_dir)
        assert_outputs_exist(output_dir)
        assert_selected_lead_matches_fixture(output_dir)
        assert_email_artifacts(output_dir)

    print("Combo package regression checks passed.")


if __name__ == "__main__":
    main()
