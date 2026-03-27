#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow_runtime.feishu_payloads import dump_json, email_stage_payload, load_json, make_workflow_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Feishu/OpenClaw payload from outreach-email outputs.")
    parser.add_argument("--email-input-json", required=True, help="Path to the email bridge input JSON.")
    parser.add_argument("--email-output-json", required=True, help="Path to the email draft JSON output.")
    parser.add_argument("--combo-run-id", default="manual-run", help="Stable combo run identifier.")
    parser.add_argument("--lead-id", default="lead-001", help="Lead ID carried from the screening stage.")
    parser.add_argument("--workflow-id", default="", help="Optional explicit workflow ID.")
    parser.add_argument("--json-out", help="Optional path to save the Feishu payload JSON.")
    args = parser.parse_args()

    email_input = load_json(args.email_input_json)
    email_output = load_json(args.email_output_json)
    workflow_id = args.workflow_id or make_workflow_id(
        args.combo_run_id,
        args.lead_id,
        str(email_input.get("company_name", "")),
    )
    payload = email_stage_payload(email_input, email_output, args.combo_run_id, args.lead_id, workflow_id)
    if args.json_out:
        dump_json(payload, args.json_out)
    else:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
