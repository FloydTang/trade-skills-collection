#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
FOR_OPENCLAW_ROOT = SCRIPT_DIR.parent
SKILL_ROOT = FOR_OPENCLAW_ROOT.parent
CORE_SCRIPT_PATH = SKILL_ROOT / "scripts" / "build_email_draft.py"
OPENCLAW_SCHEMA_PATH = FOR_OPENCLAW_ROOT / "schemas" / "openclaw-email-input.json"
CORE_SCHEMA_PATH = SKILL_ROOT / "schemas" / "email-draft-input.schema.json"
REQUIRED_DECISION_GATES = ("identity", "evidence", "seller_offer", "product_fit", "risk")
GENERIC_SOURCE_IDENTITIES = {
    "evidence",
    "n/a",
    "na",
    "none",
    "source",
    "unknown",
    "untitled",
    "untitled evidence",
    "web",
    "website",
}


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
    properties = schema.get("properties") or {}
    for section_name in ("operator_input", "public_context"):
        section = payload[section_name]
        section_schema = properties.get(section_name) or {}
        section_missing = [key for key in section_schema.get("required", []) if key not in section]
        if section_missing:
            raise SystemExit(
                f"Missing required {section_name} fields: {', '.join(section_missing)}"
            )


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _ids(value: object) -> tuple[list[str], bool]:
    if not isinstance(value, list) or not value:
        return [], False
    normalized = [_text(item) for item in value]
    return normalized, all(normalized) and len(normalized) == len(set(normalized))


def _usable_source_identity(evidence: dict) -> bool:
    for key in ("source_id", "source_name", "source_title", "source_identity", "title"):
        identity = " ".join(_text(evidence.get(key)).lower().split())
        if (
            identity
            and identity not in GENERIC_SOURCE_IDENTITIES
            and not identity.startswith("unknown ")
            and not identity.startswith("untitled ")
        ):
            return True
    return False


def _usable_evidence(evidence: dict) -> bool:
    url = _text(evidence.get("url") or evidence.get("source_url"))
    parsed = urlparse(url)
    return (parsed.scheme in {"http", "https"} and bool(parsed.netloc)) or _usable_source_identity(evidence)


def derive_authorization(public_context: dict) -> tuple[str, list[str]]:
    """Recompute authorization from the report contract; never trust one caller-supplied flag."""
    reasons: list[str] = []
    if public_context.get("draft_authorization") != "approved":
        supplied = public_context.get("authorization_reasons")
        if isinstance(supplied, list):
            reasons.extend(_text(item) for item in supplied if _text(item))
        if not reasons:
            reasons.append("draft_authorization is not approved")

    if public_context.get("intel_recommended_next_action") != "ready_for_email_draft":
        reasons.append("customer intel did not clear ready_for_email_draft")
    if public_context.get("manual_review_required") is not False:
        reasons.append("customer intel still requires manual review")
    if _text(public_context.get("sieger_status")) != "ready_for_email_draft":
        reasons.append("SIEGER status is not ready_for_email_draft")
    if _text(public_context.get("entity_confidence")).lower() != "high":
        reasons.append("entity confidence is not high")
    if _text(public_context.get("evidence_sufficiency")).lower() != "sufficient":
        reasons.append("evidence sufficiency is not sufficient")
    risk_rating = _text(public_context.get("risk_rating")).lower()
    if risk_rating not in {"low", "medium"}:
        reasons.append("risk rating is not an allowed outreach value")
    if risk_rating == "high":
        reasons.append("risk rating is high")

    gates = public_context.get("decision_gates")
    if not isinstance(gates, dict):
        reasons.append("decision_gates are missing")
    else:
        missing_gates = [name for name in REQUIRED_DECISION_GATES if name not in gates]
        if missing_gates:
            reasons.append("decision_gates are incomplete: " + ", ".join(missing_gates))
        failed_gates = [
            str(name)
            for name, gate in gates.items()
            if not isinstance(gate, dict) or gate.get("status") != "pass"
        ]
        if failed_gates:
            reasons.append("decision_gates did not all pass: " + ", ".join(failed_gates))

    angle = public_context.get("selected_sales_angle")
    if not isinstance(angle, dict) or angle.get("approval_status") != "approved" or not _text(angle.get("angle_id")):
        reasons.append("selected sales angle is not explicitly approved")
        angle = {}
    claim_ids, valid_claim_ids = _ids(angle.get("claim_ids"))
    evidence_ids, valid_evidence_ids = _ids(angle.get("evidence_ids"))
    if not valid_claim_ids:
        reasons.append("selected sales angle has invalid claim_ids")
    if not valid_evidence_ids:
        reasons.append("selected sales angle has invalid evidence_ids")

    selected_claims = public_context.get("selected_claims")
    selected_evidence = public_context.get("selected_evidence")
    claim_by_id = {
        _text(item.get("claim_id")): item
        for item in selected_claims
        if isinstance(item, dict) and _text(item.get("claim_id"))
    } if isinstance(selected_claims, list) else {}
    evidence_by_id = {
        _text(item.get("evidence_id")): item
        for item in selected_evidence
        if isinstance(item, dict) and _text(item.get("evidence_id"))
    } if isinstance(selected_evidence, list) else {}
    if not isinstance(selected_claims, list) or len(claim_by_id) != len(selected_claims):
        reasons.append("selected_claims are missing or contain invalid/duplicate IDs")
    if not isinstance(selected_evidence, list) or len(evidence_by_id) != len(selected_evidence):
        reasons.append("selected_evidence are missing or contain invalid/duplicate IDs")
    if set(claim_ids) != set(claim_by_id):
        reasons.append("selected claim IDs do not resolve exactly")
    if set(evidence_ids) != set(evidence_by_id):
        reasons.append("selected evidence IDs do not resolve exactly")

    strong_evidence_ids = {
        evidence_id
        for evidence_id, evidence in evidence_by_id.items()
        if _text(evidence.get("source_quality")).lower() in {"primary", "strong_secondary"}
    }
    if evidence_by_id and not strong_evidence_ids:
        reasons.append("selected evidence does not include a strong source")
    product_fit_claims = []
    for evidence_id, evidence in evidence_by_id.items():
        if not _usable_evidence(evidence):
            reasons.append(f"selected evidence {evidence_id} has no auditable URL or source identity")
    for claim_id, claim in claim_by_id.items():
        if not _text(claim.get("statement")):
            reasons.append(f"selected claim {claim_id} has no statement")
        status = _text(claim.get("status")).lower()
        statement_type = _text(claim.get("statement_type")).lower()
        if status != "supported" and not (
            status == "needs_review" and statement_type in {"hypothesis", "inference"}
        ):
            reasons.append(f"selected claim {claim_id} has an unauthorized status")
        linked_ids, linked_ids_valid = _ids(claim.get("evidence_ids"))
        if not linked_ids_valid or not set(linked_ids).issubset(evidence_by_id):
            reasons.append(f"selected claim {claim_id} has invalid evidence_ids")
        elif not set(linked_ids).intersection(evidence_ids):
            reasons.append(f"selected claim {claim_id} is not bound to the selected evidence")
        if _text(claim.get("category")).lower() == "product_fit":
            product_fit_claims.append(claim_id)
            if not set(linked_ids).intersection(strong_evidence_ids):
                reasons.append(f"selected product_fit claim {claim_id} is not bound to strong evidence")
    if claim_by_id and not product_fit_claims:
        reasons.append("selected claims do not include product_fit")

    return ("hold", list(dict.fromkeys(reasons))) if reasons else ("approved", [])


def merge_payload(payload: dict) -> dict:
    operator_input = dict(payload.get("operator_input") or {})
    public_context = dict(payload.get("public_context") or {})
    draft_authorization, authorization_reasons = derive_authorization(public_context)

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
        "source_context": {
            "draft_authorization": draft_authorization,
            "authorization_reasons": authorization_reasons,
            "risk_rating": public_context.get("risk_rating", ""),
            "entity_confidence": public_context.get("entity_confidence", ""),
            "evidence_sufficiency": public_context.get("evidence_sufficiency", ""),
            "intel_recommended_next_action": public_context.get("intel_recommended_next_action", ""),
            "manual_review_required": public_context.get("manual_review_required"),
            "decision_gates": public_context.get("decision_gates", {}),
            "sieger_status": public_context.get("sieger_status", ""),
            "industry_lens": public_context.get("industry_lens", "general"),
            "verdict_card": public_context.get("verdict_card", {}),
            "company_business_breakdown": public_context.get("company_business_breakdown", {}),
            "tech_capability_procurement_concerns": public_context.get("tech_capability_procurement_concerns", {}),
            "scale_financial_signals": public_context.get("scale_financial_signals", {}),
            "sales_model_procurement_logic": public_context.get("sales_model_procurement_logic", {}),
            "competition_map": public_context.get("competition_map", {}),
            "growth_opportunities": public_context.get("growth_opportunities", []),
            "image_summary": public_context.get("image_summary", {}),
            "sieger_standard": public_context.get("sieger_standard", {}),
            "recommended_sales_angle_en": public_context.get("recommended_sales_angle_en", ""),
            "recommended_opening_signal_en": public_context.get("recommended_opening_signal_en", ""),
            "recent_signals": public_context.get("recent_signals", []),
            "market_signals": public_context.get("market_signals", []),
            "evidence_titles": public_context.get("evidence_titles", []),
            "evidence_refs": public_context.get("evidence_refs", []),
            "selected_sales_angle": public_context.get("selected_sales_angle", {}),
            "selected_claims": public_context.get("selected_claims", []),
            "selected_evidence": public_context.get("selected_evidence", []),
            "unconfirmed_fact_list": public_context.get("unconfirmed_fact_list", []),
            "ambiguity_notes": public_context.get("ambiguity_notes", []),
            "seller_context": operator_input.get("seller_context", {}),
        },
    }

    if str(public_context.get("risk_rating", "")).strip().lower() == "high":
        extra = "High-risk lead from upstream context. Review manually before sending."
        merged["constraints"] = (merged["constraints"] + " " + extra).strip()

    if str(public_context.get("sieger_status", "")).strip() == "needs_manual_review":
        extra = "SIEGER Verdict Card requires manual review before sending."
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
    evidence_signals = core.build_evidence_signals(normalized)
    unconfirmed_fact_checklist = core.build_unconfirmed_fact_checklist(normalized)
    workflow_guidance = core.build_workflow_guidance(normalized)
    markdown = core.render_markdown(
        normalized,
        subjects,
        drafts,
        notes,
        signals,
        evidence_signals,
        unconfirmed_fact_checklist,
        workflow_guidance,
    )
    result = {
        "merged_input": merged,
        "subject_options": subjects,
        "drafts": drafts,
        "review_notes": notes,
        "evidence_signals_used": evidence_signals,
        "unconfirmed_fact_checklist": unconfirmed_fact_checklist,
        "workflow_guidance": workflow_guidance,
        "input_signals_used": signals,
    }

    maybe_write(args.markdown_out, markdown)
    maybe_write(args.json_out, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
