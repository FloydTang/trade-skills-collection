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

from workflow_runtime.container_bundle import (
    dump_text,
    email_stage_asset,
    intel_stage_asset,
    master_index_schema,
    master_records,
    render_container_bundle_markdown,
    render_master_records_csv,
    screening_stage_asset,
    search_stage_asset,
)
from workflow_runtime.contracts import dump_json, load_json, make_workflow_id, utc_now_iso
from workflow_runtime.feishu_adapter import (
    build_feishu_sandbox_bundle,
    email_stage_payload,
    intel_stage_payload,
    screening_stage_payload,
    search_stage_payload,
)


def resolve_selected_company(screening_payload: dict, selected_lead_id: str) -> str:
    for record in screening_payload.get("record_payloads") or []:
        identity = record.get("lead_identity") or {}
        if identity.get("lead_id") == selected_lead_id:
            return str(identity.get("company_name", ""))
    return ""


def build_container_bundle(output_dir: Path, combo_run_id: str, selected_lead_id: str) -> dict:
    discovery_report = load_json(output_dir / "01-lead-discovery-output.json")
    screening_report = load_json(output_dir / "03-lead-screening-output.json")
    intel_report = load_json(output_dir / "06-customer-intel-report.json")
    email_input = load_json(output_dir / "07-email-input.json")
    email_output = load_json(output_dir / "08-email-draft.json")

    search_payload = search_stage_asset(discovery_report, combo_run_id)
    screening_payload = screening_stage_asset(screening_report, combo_run_id)

    selected_company = resolve_selected_company(screening_payload, selected_lead_id)
    workflow_id = make_workflow_id(combo_run_id, selected_lead_id, selected_company)

    intel_payload = intel_stage_asset(intel_report, combo_run_id, selected_lead_id, workflow_id)
    email_payload = email_stage_asset(email_input, email_output, combo_run_id, selected_lead_id, workflow_id)

    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "selected_lead_id": selected_lead_id,
            "workflow_id": workflow_id,
            "generated_at": utc_now_iso(),
            "bundle_scope": "trade-skill-collection-container-bundle",
            "workspace_owner_skill": "trade-active-outreach-combo",
        },
        "public_modes": {
            "classroom_stable_mode": {
                "enabled": True,
                "description": "固定样例、固定桥接、稳定演示。",
            },
            "real_business_mode": {
                "enabled": True,
                "description": "真实输入，结果受公开数据质量、关键词和权限影响。",
            },
        },
        "data_containers": {
            "fallback_containers": ["json", "markdown", "csv"],
            "classroom_sandbox": "feishu",
            "future_enterprise_adapters": ["crm", "erp", "mail_draftbox"],
        },
        "master_index_schema": master_index_schema(),
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
        "handoff_contract": {
            "core_entities": [
                "LeadRecord",
                "EvidenceItem",
                "ScreeningDecision",
                "IntelDecision",
                "OutreachDraftPackage",
                "ContainerBundle",
            ],
            "default_send_policy": "manual_review_only",
            "notes": [
                "飞书只作为课堂标准沙盘，不是企业唯一数据容器。",
                "企业真实容器适配留在课后接入层，本轮只公开字段与容器抽象。",
            ],
        },
    }


def build_bundle(output_dir: Path, combo_run_id: str, selected_lead_id: str) -> dict:
    discovery_report = load_json(output_dir / "01-lead-discovery-output.json")
    screening_report = load_json(output_dir / "03-lead-screening-output.json")
    intel_report = load_json(output_dir / "06-customer-intel-report.json")
    email_input = load_json(output_dir / "07-email-input.json")
    email_output = load_json(output_dir / "08-email-draft.json")

    search_payload = search_stage_payload(discovery_report, combo_run_id)
    screening_payload = screening_stage_payload(screening_report, combo_run_id)

    selected_company = resolve_selected_company(screening_payload, selected_lead_id)
    workflow_id = make_workflow_id(combo_run_id, selected_lead_id, selected_company)

    intel_payload = intel_stage_payload(intel_report, combo_run_id, selected_lead_id, workflow_id)
    email_payload = email_stage_payload(email_input, email_output, combo_run_id, selected_lead_id, workflow_id)

    return build_feishu_sandbox_bundle(
        search_payload,
        screening_payload,
        intel_payload,
        email_payload,
        combo_run_id,
        selected_lead_id,
        workflow_id,
    )


def export_default_artifacts(
    output_dir: Path,
    combo_run_id: str,
    selected_lead_id: str,
    include_feishu: bool = True,
) -> None:
    container_bundle = build_container_bundle(output_dir, combo_run_id, selected_lead_id)
    markdown = render_container_bundle_markdown(container_bundle)
    csv_text = render_master_records_csv(container_bundle["master_records"])

    dump_json(container_bundle, output_dir / "09-container-bundle.json")
    dump_text(markdown, output_dir / "10-container-bundle.md")
    dump_text(csv_text, output_dir / "11-lead-workflow.csv")
    if include_feishu:
        feishu_bundle = build_bundle(output_dir, combo_run_id, selected_lead_id)
        dump_json(feishu_bundle, output_dir / "12-feishu-sandbox-bundle.json")
        dump_json(feishu_bundle, output_dir / "09-feishu-workflow-bundle.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export neutral container artifacts plus Feishu sandbox bundle.")
    parser.add_argument(
        "--output-dir",
        default=str(PACKAGE_ROOT / "outputs" / "demo-run"),
        help="Directory containing combo stage outputs.",
    )
    parser.add_argument("--combo-run-id", default="demo-run", help="Stable combo run identifier.")
    parser.add_argument("--selected-lead-id", default="lead-002", help="Selected lead ID for intel/email stages.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    export_default_artifacts(output_dir, args.combo_run_id, args.selected_lead_id)
    print(f"Container exports generated in: {output_dir}")


if __name__ == "__main__":
    main()
