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

from workflow_runtime.feishu_payloads import dump_json, load_json, search_stage_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Feishu/OpenClaw payload from lead-discovery output.")
    parser.add_argument("--input-json", required=True, help="Path to the lead-discovery JSON output.")
    parser.add_argument("--combo-run-id", default="manual-run", help="Stable combo run identifier.")
    parser.add_argument("--json-out", help="Optional path to save the Feishu payload JSON.")
    args = parser.parse_args()

    report = load_json(args.input_json)
    payload = search_stage_payload(report, args.combo_run_id)
    if args.json_out:
        dump_json(payload, args.json_out)
    else:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
