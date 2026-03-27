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
    "09-feishu-workflow-bundle.json",
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


def assert_feishu_bundle(output_dir: Path) -> None:
    bundle = load_json(output_dir / "09-feishu-workflow-bundle.json")
    stage_assets = bundle.get("stage_assets") or {}
    master_records = bundle.get("master_records") or []

    required_stages = {"lead_discovery", "lead_screening", "customer_intel", "outreach_email"}
    if set(stage_assets) != required_stages:
        raise SystemExit("Feishu bundle is missing one or more stage assets.")
    if len(master_records) != 3:
        raise SystemExit("Feishu master records should include all 3 demo leads.")

    selected = next((item for item in master_records if item.get("lead_id") == "lead-002"), None)
    if not selected:
        raise SystemExit("Selected lead is missing from Feishu master records.")
    if selected.get("current_stage") != "outreach_email" or selected.get("current_status") != "draft_ready":
        raise SystemExit("Selected lead did not progress to outreach_email/draft_ready in the master records.")

    enrich_lead = next((item for item in master_records if item.get("lead_id") == "lead-001"), None)
    if not enrich_lead:
        raise SystemExit("Lead requiring enrichment is missing from Feishu master records.")
    asset_keys = json.loads(enrich_lead.get("asset_keys", "{}"))
    if "intel" in asset_keys or "email" in asset_keys:
        raise SystemExit("Lead-001 should not receive intel/email assets before enrichment.")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="trade-skill-combo-check-") as temp_dir:
        output_dir = Path(temp_dir) / "demo"
        run_demo(output_dir)
        assert_outputs_exist(output_dir)
        assert_selected_lead_matches_fixture(output_dir)
        assert_email_artifacts(output_dir)
        assert_feishu_bundle(output_dir)

    print("Combo package regression checks passed.")


if __name__ == "__main__":
    main()
