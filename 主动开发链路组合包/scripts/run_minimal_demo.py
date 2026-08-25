#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PACKAGE_ROOT.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

LOCAL_SUBSKILL_ROOT = PACKAGE_ROOT / "子Skill与工具本体"
REQUIRED_SKILL_DIRS = ["客户搜索skill", "线索整理skill", "客户背调skill", "开发信skill"]


def resolve_skill_root() -> Path:
    if all((LOCAL_SUBSKILL_ROOT / name).is_dir() for name in REQUIRED_SKILL_DIRS):
        return LOCAL_SUBSKILL_ROOT
    return WORKSPACE_ROOT


SKILL_ROOT = resolve_skill_root()
SEARCH_SKILL = SKILL_ROOT / "客户搜索skill"
SCREENING_SKILL = SKILL_ROOT / "线索整理skill"
INTEL_SKILL = SKILL_ROOT / "客户背调skill"
EMAIL_SKILL = SKILL_ROOT / "开发信skill"

PACKAGE_EXAMPLES = PACKAGE_ROOT / "examples"

from export_feishu_workflow_bundle import export_default_artifacts


def run_python(args: list[str]) -> None:
    env = os.environ.copy()
    python_path_parts = [str(WORKSPACE_ROOT), str(SKILL_ROOT)]
    if env.get("PYTHONPATH"):
        python_path_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_path_parts)
    completed = subprocess.run(args, cwd=WORKSPACE_ROOT, env=env, capture_output=True, text=True)
    if completed.returncode != 0:
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_selected_customer_intel_input(screening_output_path: Path, selected_lead_id: str) -> dict:
    screening_output = load_json(screening_output_path)
    leads = screening_output.get("leads") or []
    for lead in leads:
        if lead.get("lead_id") != selected_lead_id:
            continue
        if lead.get("recommended_next_action") != "ready_for_customer_intel":
            raise SystemExit(
                f"Lead '{selected_lead_id}' is not ready for customer intel. "
                "Review the screening output before continuing."
            )
        return lead.get("customer_intel_input") or {}
    raise SystemExit(f"Lead '{selected_lead_id}' not found in screening output.")


def validate_fixture_matches_selected_input(selected_input: dict, fixture_report_path: Path) -> None:
    report = load_json(fixture_report_path)
    selected_company = str(selected_input.get("company_name", "")).strip()
    fixture_company = str((report.get("identity_snapshot") or {}).get("company_name", "")).strip()
    if selected_company and fixture_company and selected_company != fixture_company:
        raise SystemExit(
            "Selected lead does not match the reviewed customer-intel fixture. "
            f"Selected '{selected_company}', fixture '{fixture_company}'."
        )


def approve_sales_angle(report_path: Path, angle_id: str) -> None:
    report = load_json(report_path)
    if (report.get("intel_decision") or {}).get("recommended_next_action") != "ready_for_email_draft":
        raise SystemExit("Customer intel has not cleared ready_for_email_draft; angle approval is forbidden.")
    angles = report.get("sales_angles") or []
    selected = next((item for item in angles if item.get("angle_id") == angle_id), None)
    if not selected:
        raise SystemExit(f"Sales angle '{angle_id}' was not found in the customer-intel report.")
    for item in angles:
        item["approval_status"] = "approved" if item is selected else "proposed"
    write_json(report_path, report)


def approved_angle_id(report_path: Path) -> str:
    report = load_json(report_path)
    for item in report.get("sales_angles") or []:
        if item.get("approval_status") == "approved" and item.get("angle_id"):
            return str(item["angle_id"])
    return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the minimal active-outreach combo demo by reusing the four node-level skills."
    )
    parser.add_argument(
        "--output-dir",
        default=str(PACKAGE_ROOT / "outputs" / "demo-run"),
        help="Directory for generated stage outputs.",
    )
    parser.add_argument(
        "--selected-lead-id",
        default="lead-002",
        help="Lead ID to carry from screening into the reviewed customer-intel stage.",
    )
    parser.add_argument(
        "--discovery-mode",
        choices=["fixture", "live"],
        default="fixture",
        help="Use fixed search fixtures for regression or run the discovery search providers live.",
    )
    parser.add_argument(
        "--search-input",
        default=str(SEARCH_SKILL / "examples" / "frozen-food-search.json"),
        help="Lead-discovery input JSON.",
    )
    parser.add_argument(
        "--customer-intel-mode",
        choices=["fixture", "live"],
        default="fixture",
        help="Use the reviewed fixture or execute the customer-intel search and report builder live.",
    )
    parser.add_argument(
        "--approved-sales-angle-id",
        default="",
        help="Explicit human approval for one ANGLE-* ID in live mode.",
    )
    parser.add_argument(
        "--product-or-offer",
        default="frozen mixed vegetables",
        help="Product or offer for the outreach email stage.",
    )
    parser.add_argument("--sender-name", default="Leo", help="Sender name for the email stage.")
    parser.add_argument(
        "--sender-company",
        default="Ningbo FreshGrow Foods",
        help="Sender company for the email stage.",
    )
    parser.add_argument(
        "--combo-run-id",
        default="demo-run",
        help="Stable combo run identifier for neutral container exports.",
    )
    parser.add_argument(
        "--skip-feishu-export",
        action="store_true",
        help="Skip exporting the Feishu sandbox adapter bundle.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    discovery_input_path = Path(args.search_input).resolve()
    discovery_fixture_path = SEARCH_SKILL / "examples" / "frozen-food-fixtures.json"
    discovery_output_path = output_dir / "01-lead-discovery-output.json"
    screening_input_path = output_dir / "02-lead-screening-input.json"
    screening_json_path = output_dir / "03-lead-screening-output.json"
    screening_md_path = output_dir / "03-lead-screening-output.md"
    customer_intel_batch_path = output_dir / "04-customer-intel-batch.json"
    selected_intel_input_path = output_dir / "05-selected-customer-intel-input.json"
    customer_intel_report_path = output_dir / "06-customer-intel-report.json"
    email_input_path = output_dir / "07-email-input.json"
    email_json_path = output_dir / "08-email-draft.json"
    email_md_path = output_dir / "08-email-draft.md"

    discovery_command = [
        sys.executable,
        str(SEARCH_SKILL / "scripts" / "build_lead_discovery_report.py"),
        "--input-json",
        str(discovery_input_path),
        "--json-out",
        str(discovery_output_path),
    ]
    if args.discovery_mode == "fixture":
        discovery_command.extend(["--fixtures-json", str(discovery_fixture_path)])
    run_python(discovery_command)

    run_python(
        [
            sys.executable,
            str(SEARCH_SKILL / "scripts" / "build_lead_screening_input.py"),
            "--input-json",
            str(discovery_output_path),
            "--json-out",
            str(screening_input_path),
        ]
    )

    run_python(
        [
            sys.executable,
            str(SCREENING_SKILL / "scripts" / "build_lead_screening_report.py"),
            "--input-json",
            str(screening_input_path),
            "--markdown-out",
            str(screening_md_path),
            "--json-out",
            str(screening_json_path),
        ]
    )

    run_python(
        [
            sys.executable,
            str(SCREENING_SKILL / "scripts" / "build_customer_intel_batch_input.py"),
            "--input-json",
            str(screening_json_path),
            "--json-out",
            str(customer_intel_batch_path),
        ]
    )

    selected_input = build_selected_customer_intel_input(screening_json_path, args.selected_lead_id)
    write_json(selected_intel_input_path, selected_input)

    if args.customer_intel_mode == "fixture":
        fixture_report_path = PACKAGE_EXAMPLES / "reviewed-customer-intel-report.json"
        validate_fixture_matches_selected_input(selected_input, fixture_report_path)
        shutil.copyfile(fixture_report_path, customer_intel_report_path)
    else:
        run_python(
            [
                sys.executable,
                str(INTEL_SKILL / "scripts" / "build_customer_intel_report.py"),
                "--input-json",
                str(selected_intel_input_path),
                "--json-out",
                str(customer_intel_report_path),
            ]
        )
        if args.approved_sales_angle_id:
            approve_sales_angle(customer_intel_report_path, args.approved_sales_angle_id)

    selected_angle_id = approved_angle_id(customer_intel_report_path)
    if not selected_angle_id:
        raise SystemExit(
            "Customer-intel output is complete, but no sales angle is approved. "
            "Review the report and rerun with --approved-sales-angle-id ANGLE-XX."
        )

    run_python(
        [
            sys.executable,
            str(EMAIL_SKILL / "scripts" / "build_email_input_from_customer_intel.py"),
            "--input-json",
            str(customer_intel_report_path),
            "--email-type",
            "first_touch",
            "--product-or-offer",
            args.product_or_offer,
            "--sender-name",
            args.sender_name,
            "--sender-company",
            args.sender_company,
            "--approved-sales-angle-id",
            selected_angle_id,
            "--json-out",
            str(email_input_path),
        ]
    )

    run_python(
        [
            sys.executable,
            str(EMAIL_SKILL / "scripts" / "build_email_draft.py"),
            "--input-json",
            str(email_input_path),
            "--markdown-out",
            str(email_md_path),
            "--json-out",
            str(email_json_path),
        ]
    )

    export_default_artifacts(
        output_dir,
        args.combo_run_id,
        args.selected_lead_id,
        include_feishu=not args.skip_feishu_export,
    )

    print(f"Demo outputs generated in: {output_dir}")
    print("Current customer-intel stage uses the combo package fixture for stable demonstration.")


if __name__ == "__main__":
    main()
