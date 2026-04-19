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
    "09-container-bundle.json",
    "09-feishu-workflow-bundle.json",
    "10-container-bundle.md",
    "11-lead-workflow.csv",
    "12-feishu-sandbox-bundle.json",
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
    if email_output.get("send_policy") != "manual_review_only":
        raise SystemExit("Email draft JSON should declare manual_review_only send policy.")
    if "GreenHarvest Foods" not in email_markdown:
        raise SystemExit("Email draft markdown does not mention the expected company.")
    if "Recommended Next Action: ready_for_manual_send" not in email_markdown:
        raise SystemExit("Email draft markdown should expose the workflow guidance section.")


def assert_container_bundle(output_dir: Path) -> None:
    bundle = load_json(output_dir / "09-container-bundle.json")
    markdown = (output_dir / "10-container-bundle.md").read_text(encoding="utf-8")
    csv_text = (output_dir / "11-lead-workflow.csv").read_text(encoding="utf-8")

    if bundle.get("data_containers", {}).get("classroom_sandbox") != "feishu":
        raise SystemExit("Container bundle should declare Feishu as the classroom sandbox adapter.")
    if "LeadRecord" not in (bundle.get("handoff_contract") or {}).get("core_entities", []):
        raise SystemExit("Container bundle should expose the shared core entities.")
    if "## Data Containers" not in markdown:
        raise SystemExit("Container bundle markdown is missing the data container summary.")
    if "recommended_next_action" not in csv_text or "legacy_recommended_next_action" not in csv_text:
        raise SystemExit("Lead workflow CSV is missing the expected contract columns.")


def assert_feishu_bundle(output_dir: Path) -> None:
    bundle = load_json(output_dir / "12-feishu-sandbox-bundle.json")
    install_contract = bundle.get("openclaw_install_contract") or {}
    workspace_container = bundle.get("workspace_container") or {}
    stage_assets = bundle.get("stage_assets") or {}
    master_records = bundle.get("master_records") or []
    handoff = bundle.get("openclaw_handoff") or {}

    required_stages = {"lead_discovery", "lead_screening", "customer_intel", "outreach_email"}
    if set(stage_assets) != required_stages:
        raise SystemExit("Feishu bundle is missing one or more stage assets.")
    if len(master_records) != 3:
        raise SystemExit("Feishu master records should include all 3 demo leads.")
    if workspace_container.get("container_type") != "single_base_workspace":
        raise SystemExit("Feishu bundle should declare a single-base workspace container.")
    if not workspace_container.get("forbid_parallel_bases_for_each_stage"):
        raise SystemExit("Feishu bundle should explicitly forbid creating parallel bases for each stage.")
    if workspace_container.get("workspace_owner_skill") != "trade-active-outreach-combo":
        raise SystemExit("Feishu bundle should declare the combo package as the workspace owner skill.")
    if not workspace_container.get("single_skill_attach_only"):
        raise SystemExit("Feishu bundle should force single-skill runs into attach-only mode.")
    if not workspace_container.get("forbid_stage_level_base_bootstrap"):
        raise SystemExit("Feishu bundle should forbid stage-level base bootstrap.")

    if install_contract.get("container_owner") != "active_outreach_combo":
        raise SystemExit("Install contract should declare the combo package as the container owner.")
    if install_contract.get("container_mode") != "single_base_multi_table":
        raise SystemExit("Install contract should declare single_base_multi_table container mode.")
    if install_contract.get("single_skill_policy") != "attach_only":
        raise SystemExit("Install contract should require attach_only for single-skill runs.")
    workflow_owner = install_contract.get("workflow_owner") or {}
    if workflow_owner.get("skill_name") != "trade-active-outreach-combo":
        raise SystemExit("Install contract should declare trade-active-outreach-combo as workflow owner.")
    worker_names = {item.get("skill_name") for item in install_contract.get("stage_workers") or []}
    if worker_names != {
        "trade-lead-discovery-openclaw",
        "trade-lead-screening-openclaw",
        "trade-customer-intel-for-openclaw",
        "trade-outreach-email-for-openclaw",
    }:
        raise SystemExit("Install contract should enumerate all four stage workers.")
    for worker in install_contract.get("stage_workers") or []:
        if worker.get("feishu_container_creation") != "forbidden":
            raise SystemExit("Stage workers must explicitly forbid Feishu container creation.")
        if not worker.get("requires_master_base") or not worker.get("requires_master_record"):
            raise SystemExit("Stage workers must require the master base and master record.")

    table_names = {item.get("table_name") for item in workspace_container.get("tables") or []}
    if table_names != {"Lead Workflow Master", "Lead Discovery Results", "Lead Screening Results"}:
        raise SystemExit("Workspace container is missing one or more required Feishu tables.")

    for stage_name, payload in stage_assets.items():
        runtime_contract = payload.get("feishu_runtime_contract") or {}
        if runtime_contract.get("workspace_owner_skill") != "trade-active-outreach-combo":
            raise SystemExit(f"{stage_name} payload should point back to the combo workspace owner.")
        if runtime_contract.get("feishu_container_creation") != "forbidden":
            raise SystemExit(f"{stage_name} payload should not imply independent container creation.")
        if not runtime_contract.get("requires_master_base") or not runtime_contract.get("requires_master_record"):
            raise SystemExit(f"{stage_name} payload should require the master base and master record.")

    selected = next((item for item in master_records if item.get("lead_id") == "lead-002"), None)
    if not selected:
        raise SystemExit("Selected lead is missing from Feishu master records.")
    if selected.get("current_stage") != "outreach_email" or selected.get("current_status") != "draft_ready":
        raise SystemExit("Selected lead did not progress to outreach_email/draft_ready in the master records.")
    if selected.get("recommended_next_action") != "ready_for_customer_intel":
        raise SystemExit("Selected lead should keep the screening next action in the master records.")
    if "search_asset_ref" not in selected or "intel_asset_ref" not in selected or "email_asset_ref" not in selected:
        raise SystemExit("Master records should use text asset_ref fields instead of URL-only fields.")

    waiting_lead = next((item for item in master_records if item.get("lead_id") == "lead-001"), None)
    if not waiting_lead:
        raise SystemExit("A non-selected waiting lead is missing from Feishu master records.")
    asset_keys = json.loads(waiting_lead.get("asset_keys", "{}"))
    if "intel" in asset_keys or "email" in asset_keys:
        raise SystemExit("Non-selected leads should not receive intel/email assets in the stable demo.")
    if waiting_lead.get("search_asset_ref") != "search-record:demo-run:lead-001":
        raise SystemExit("Lead-001 search_asset_ref should point to the stable search asset key.")
    if waiting_lead.get("current_status") != "waiting_selection":
        raise SystemExit("Lead-001 should remain in waiting_selection state.")

    failure_policy = handoff.get("failure_writeback_policy") or {}
    rerun_policy = handoff.get("rerun_policy") or {}
    attach_rules = handoff.get("single_skill_attach_rules") or []
    if not failure_policy.get("always_write_master_status"):
        raise SystemExit("Feishu bundle should require master writeback even when stage execution fails.")
    if "master_record" not in rerun_policy:
        raise SystemExit("Feishu bundle rerun policy should describe master-record reuse.")
    if len(attach_rules) < 3:
        raise SystemExit("Feishu bundle should describe how single-skill runs attach back to the master table.")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="trade-skill-combo-check-") as temp_dir:
        output_dir = Path(temp_dir) / "demo"
        run_demo(output_dir)
        assert_outputs_exist(output_dir)
        assert_selected_lead_matches_fixture(output_dir)
        assert_email_artifacts(output_dir)
        assert_container_bundle(output_dir)
        assert_feishu_bundle(output_dir)

    print("Combo package regression checks passed.")


if __name__ == "__main__":
    main()
