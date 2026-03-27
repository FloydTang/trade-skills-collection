#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = WORKSPACE_ROOT
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow_runtime.feishu_payloads import (
    dump_json,
    email_stage_payload,
    intel_stage_payload,
    load_json,
    make_workflow_id,
    master_records,
    master_table_schema,
    screening_stage_payload,
    search_stage_payload,
    utc_now_iso,
)


def build_bundle(output_dir: Path, combo_run_id: str, selected_lead_id: str) -> dict:
    discovery_report = load_json(output_dir / "01-lead-discovery-output.json")
    screening_report = load_json(output_dir / "03-lead-screening-output.json")
    intel_report = load_json(output_dir / "06-customer-intel-report.json")
    email_input = load_json(output_dir / "07-email-input.json")
    email_output = load_json(output_dir / "08-email-draft.json")

    search_payload = search_stage_payload(discovery_report, combo_run_id)
    screening_payload = screening_stage_payload(screening_report, combo_run_id)

    selected_company = ""
    for record in screening_payload.get("record_payloads") or []:
        identity = record.get("lead_identity") or {}
        if identity.get("lead_id") == selected_lead_id:
            selected_company = str(identity.get("company_name", ""))
            break
    workflow_id = make_workflow_id(combo_run_id, selected_lead_id, selected_company)

    intel_payload = intel_stage_payload(intel_report, combo_run_id, selected_lead_id, workflow_id)
    email_payload = email_stage_payload(email_input, email_output, combo_run_id, selected_lead_id, workflow_id)

    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "selected_lead_id": selected_lead_id,
            "workflow_id": workflow_id,
            "generated_at": utc_now_iso(),
            "bundle_scope": "trade-skill-collection-feishu-handoff",
        },
        "master_table_schema": master_table_schema(),
        "stage_assets": {
            "lead_discovery": search_payload,
            "lead_screening": screening_payload,
            "customer_intel": intel_payload,
            "outreach_email": email_payload,
        },
        "master_records": master_records(
            search_payload,
            screening_payload,
            intel_payload,
            email_payload,
            combo_run_id,
            selected_lead_id,
        ),
        "openclaw_handoff": {
            "execution_order": [
                "create_or_open_master_table",
                "upsert_lead_discovery_records",
                "upsert_lead_screening_records",
                "create_or_update_customer_intel_doc_for_selected_lead",
                "create_or_update_outreach_email_doc_for_selected_lead",
                "write_back_master_records",
            ],
            "stage_asset_types": {
                "lead_discovery": "table_record_batch",
                "lead_screening": "table_record_batch",
                "customer_intel": "doc",
                "outreach_email": "doc",
            },
            "master_writeback_rules": [
                "搜索完成后写主表 current_stage=lead_discovery 或 lead_screening。",
                "recommended_next_action=enter_customer_intel 但未被本轮选中时，current_status=waiting_selection。",
                "recommended_next_action=enrich_then_customer_intel 时，不创建背调文档。",
                "开发信草稿完成后，主表 current_stage=outreach_email, current_status=draft_ready。",
            ],
            "rerun_policy": {
                "table_records": "按 combo_run_id + lead_id upsert，避免重复插入。",
                "intel_doc": "优先复用已存在文档，再追加本次版本区块。",
                "email_doc": "优先复用已存在文档，再追加新草稿版本。",
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a Feishu/OpenClaw workflow bundle from combo outputs.")
    parser.add_argument(
        "--output-dir",
        default=str(PACKAGE_ROOT / "outputs" / "demo-run"),
        help="Directory containing combo stage outputs.",
    )
    parser.add_argument("--combo-run-id", default="demo-run", help="Stable combo run identifier.")
    parser.add_argument("--selected-lead-id", default="lead-002", help="Selected lead ID for intel/email stages.")
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional bundle JSON path. Defaults to <output-dir>/09-feishu-workflow-bundle.json.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    json_out = Path(args.json_out).resolve() if args.json_out else output_dir / "09-feishu-workflow-bundle.json"
    bundle = build_bundle(output_dir, args.combo_run_id, args.selected_lead_id)
    dump_json(bundle, json_out)
    print(f"Feishu workflow bundle generated at: {json_out}")


if __name__ == "__main__":
    main()
