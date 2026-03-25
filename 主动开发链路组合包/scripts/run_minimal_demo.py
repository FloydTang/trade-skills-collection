#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PACKAGE_ROOT.parent

SEARCH_SKILL = WORKSPACE_ROOT / "客户搜索skill"
SCREENING_SKILL = WORKSPACE_ROOT / "线索整理skill"
EMAIL_SKILL = WORKSPACE_ROOT / "开发信skill"

PACKAGE_EXAMPLES = PACKAGE_ROOT / "examples"


def run_python(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=WORKSPACE_ROOT, capture_output=True, text=True)
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
        if lead.get("recommended_next_action") != "enter_customer_intel":
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
        "--customer-intel-mode",
        choices=["fixture"],
        default="fixture",
        help="Current stable mode. Uses the reviewed customer-intel fixture for repeatable demos.",
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    discovery_output_path = SEARCH_SKILL / "examples" / "frozen-food-output.json"
    screening_input_path = output_dir / "02-lead-screening-input.json"
    screening_json_path = output_dir / "03-lead-screening-output.json"
    screening_md_path = output_dir / "03-lead-screening-output.md"
    customer_intel_batch_path = output_dir / "04-customer-intel-batch.json"
    selected_intel_input_path = output_dir / "05-selected-customer-intel-input.json"
    customer_intel_report_path = output_dir / "06-customer-intel-report.json"
    email_input_path = output_dir / "07-email-input.json"
    email_json_path = output_dir / "08-email-draft.json"
    email_md_path = output_dir / "08-email-draft.md"

    # Stage 1 output is fixed for stable demo playback.
    shutil.copyfile(discovery_output_path, output_dir / "01-lead-discovery-output.json")

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

    if args.customer_intel_mode != "fixture":
        raise SystemExit("Only fixture mode is supported in the current combo package version.")
    fixture_report_path = PACKAGE_EXAMPLES / "reviewed-customer-intel-report.json"
    validate_fixture_matches_selected_input(selected_input, fixture_report_path)
    shutil.copyfile(fixture_report_path, customer_intel_report_path)

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

    print(f"Demo outputs generated in: {output_dir}")
    print("Current customer-intel stage uses the combo package fixture for stable demonstration.")


if __name__ == "__main__":
    main()
