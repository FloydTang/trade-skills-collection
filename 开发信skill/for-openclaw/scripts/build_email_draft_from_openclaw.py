#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
FOR_OPENCLAW_ROOT = SCRIPT_DIR.parent
SKILL_ROOT = FOR_OPENCLAW_ROOT.parent
CORE_SCRIPT_PATH = SKILL_ROOT / "scripts" / "build_email_draft.py"
OPENCLAW_SCHEMA_PATH = FOR_OPENCLAW_ROOT / "schemas" / "openclaw-email-input.json"
CORE_SCHEMA_PATH = SKILL_ROOT / "schemas" / "email-draft-input.schema.json"


def load_json(path_arg: str | None) -> dict:
    if path_arg:
        return json.loads(Path(path_arg).read_text(encoding="utf-8"))
    return json.load(sys.stdin)


def load_core_module():
    spec = importlib.util.spec_from_file_location("build_email_draft_core", CORE_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def validate_openclaw_payload(payload: dict, schema: dict) -> None:
    if not isinstance(payload, dict):
        raise SystemExit("OpenClaw input must be a JSON object.")
    required = schema.get("required", [])
    missing = [key for key in required if key not in payload]
    if missing:
        raise SystemExit(f"Missing required top-level fields: {', '.join(missing)}")
    if not isinstance(payload.get("operator_input"), dict):
        raise SystemExit("operator_input must be an object.")
    if not isinstance(payload.get("public_context"), dict):
        raise SystemExit("public_context must be an object.")


def merge_payload(payload: dict) -> dict:
    operator_input = dict(payload.get("operator_input") or {})
    public_context = dict(payload.get("public_context") or {})

    merged = {
        "email_type": operator_input.get("email_type", ""),
        "customer_name": operator_input.get("customer_name", ""),
        "company_name": operator_input.get("company_name", ""),
        "product_or_offer": operator_input.get("product_or_offer", ""),
        "goal": operator_input.get("goal", ""),
        "country_or_market": operator_input.get("country_or_market", ""),
        "customer_profile_summary": operator_input.get("customer_profile_summary")
        or public_context.get("customer_profile_summary", ""),
        "previous_contact_context": operator_input.get("previous_contact_context")
        or public_context.get("previous_contact_context", ""),
        "tone": operator_input.get("tone", ""),
        "sender_name": operator_input.get("sender_name", ""),
        "sender_company": operator_input.get("sender_company", ""),
        "signature": operator_input.get("signature", ""),
        "constraints": operator_input.get("constraints") or public_context.get("constraints", ""),
    }

    if str(public_context.get("risk_rating", "")).strip().lower() == "high":
        extra = "High-risk lead from upstream context. Review manually before sending."
        merged["constraints"] = (merged["constraints"] + " " + extra).strip()

    return merged


def maybe_write(path_arg: str | None, content: str) -> None:
    if path_arg:
        Path(path_arg).write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build outreach email drafts from OpenClaw-wrapped input.")
    parser.add_argument("--input-json", help="Path to the OpenClaw wrapper JSON input.")
    parser.add_argument("--markdown-out", help="Path to write Markdown output.")
    parser.add_argument("--json-out", help="Path to write JSON output.")
    args = parser.parse_args()

    core = load_core_module()
    payload = load_json(args.input_json)
    openclaw_schema = core.load_schema(OPENCLAW_SCHEMA_PATH)
    validate_openclaw_payload(payload, openclaw_schema)

    merged = merge_payload(payload)
    core_schema = core.load_schema(CORE_SCHEMA_PATH)
    normalized = core.normalize(merged)
    core.validate(normalized, merged, core_schema)

    subjects = core.build_subjects(normalized)
    drafts = core.build_drafts(normalized)
    notes = core.build_review_notes(normalized)
    signals = core.build_input_signals(normalized)
    markdown = core.render_markdown(normalized, subjects, drafts, notes, signals)
    result = {
        "merged_input": merged,
        "subject_options": subjects,
        "drafts": drafts,
        "review_notes": notes,
        "input_signals_used": signals,
    }

    maybe_write(args.markdown_out, markdown)
    maybe_write(args.json_out, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
