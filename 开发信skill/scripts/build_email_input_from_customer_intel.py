#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_input(path_arg: str | None) -> dict:
    if path_arg:
        return json.loads(Path(path_arg).read_text(encoding="utf-8"))
    return json.load(sys.stdin)


def first_non_empty(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def select_approved_angle(report: dict, requested_angle_id: str = "") -> dict:
    approved = [
        item for item in (report.get("sales_angles") or [])
        if isinstance(item, dict) and item.get("approval_status") == "approved"
    ]
    if requested_angle_id:
        return next((item for item in approved if item.get("angle_id") == requested_angle_id), {})
    return approved[0] if approved else {}


def infer_goal(report: dict, email_type: str, approved_angle: dict) -> str:
    if approved_angle:
        angle = str(approved_angle.get("en", "")).strip()
        if angle:
            if email_type == "follow_up":
                return f"follow up with a short, relevant note around this angle: {angle}"
            return f"introduce our offer with a relevant angle: {angle}"
    summary_en = str(report.get("summary_en", "")).strip()
    if summary_en:
        if email_type == "follow_up":
            return "follow up with a short and relevant business note based on public information"
        return "introduce our offer with a relevant business angle based on public information"
    return "introduce our offer conservatively and check whether there is potential fit"


def summarize_signal(signal: dict) -> str:
    if not isinstance(signal, dict):
        return ""
    title = str(signal.get("title", "")).strip()
    signal_type = str(signal.get("signal_type", "")).strip()
    freshness = str(signal.get("freshness", "")).strip()
    confidence = str(signal.get("confidence", "")).strip()
    parts = [part for part in [title, signal_type, freshness, confidence] if part]
    return " | ".join(parts)


def recommended_opening_signal(report: dict) -> str:
    for key in ("recent_signals", "market_signals"):
        signals = report.get(key) or []
        for signal in signals:
            if not isinstance(signal, dict):
                continue
            title = str(signal.get("title", "")).strip()
            source_url = str(signal.get("source_url", "")).strip()
            confidence = str(signal.get("confidence", "")).strip()
            if title and source_url and confidence in {"high", "medium"}:
                return title
    return ""


def infer_constraints(report: dict) -> str:
    parts = ["Use only public, confirmed information.", "Avoid hard claims about demand, pricing, or purchasing intent."]
    if str(report.get("risk_rating", "")).strip().lower() == "high":
        parts.append("High-risk lead: review manually before any outreach.")
    intel_decision = report.get("intel_decision") or {}
    if intel_decision.get("recommended_next_action") == "hold_for_manual_review":
        parts.append("Pause at manual review if the intel stage has not cleared the lead for outreach drafting.")
    if intel_decision.get("sieger_status") == "needs_manual_review":
        parts.append("SIEGER Verdict Card requires manual review before using the report for outreach drafting.")
    return " ".join(parts)


def build_bridge_payload(
    report: dict,
    email_type: str,
    product_or_offer: str,
    sender_name: str,
    sender_company: str,
    approved_sales_angle_id: str = "",
) -> dict:
    identity = report.get("identity_snapshot") or {}
    company_profile = report.get("company_profile") or {}
    intel_decision = report.get("intel_decision") or {}
    verdict_card = report.get("verdict_card") or {}
    evidence = report.get("evidence") or []
    recent_signals = report.get("recent_signals") or []
    market_signals = report.get("market_signals") or []
    approved_angle = select_approved_angle(report, approved_sales_angle_id)
    intel_ready = intel_decision.get("recommended_next_action") == "ready_for_email_draft"
    draft_authorization = "approved" if intel_ready and approved_angle else "hold"
    authorization_reasons = []
    if not intel_ready:
        authorization_reasons.append("客户背调尚未通过 ready_for_email_draft 门槛。")
    if not approved_angle:
        authorization_reasons.append("没有人工批准的销售角度。")
    evidence_ledger = report.get("evidence_ledger") or []
    claim_ledger = report.get("claim_ledger") or []
    selected_evidence_ids = set(approved_angle.get("evidence_ids") or [])
    selected_claim_ids = set(approved_angle.get("claim_ids") or [])
    payload = {
        "email_type": email_type,
        "customer_name": first_non_empty(identity.get("person_name"), "there"),
        "company_name": first_non_empty(identity.get("company_name")),
        "product_or_offer": product_or_offer.strip(),
        "goal": infer_goal(report, email_type, approved_angle),
        "country_or_market": first_non_empty(identity.get("country_or_market")),
        "customer_profile_summary": first_non_empty(company_profile.get("apparent_business")),
        "previous_contact_context": "",
        "tone": "professional,conservative",
        "sender_name": sender_name.strip(),
        "sender_company": sender_company.strip(),
        "signature": "",
        "constraints": infer_constraints(report),
        "source_context": {
            "draft_authorization": draft_authorization,
            "authorization_reasons": authorization_reasons,
            "risk_rating": report.get("risk_rating"),
            "entity_confidence": identity.get("entity_confidence"),
            "evidence_sufficiency": intel_decision.get("evidence_sufficiency"),
            "intel_recommended_next_action": intel_decision.get("recommended_next_action"),
            "sieger_status": intel_decision.get("sieger_status") or verdict_card.get("intel_decision"),
            "verdict_card": verdict_card,
            "company_business_breakdown": report.get("company_business_breakdown") or {},
            "tech_capability_procurement_concerns": report.get("tech_capability_procurement_concerns") or {},
            "scale_financial_signals": report.get("scale_financial_signals") or {},
            "sales_model_procurement_logic": report.get("sales_model_procurement_logic") or {},
            "competition_map": report.get("competition_map") or {},
            "growth_opportunities": report.get("growth_opportunities") or [],
            "image_summary": report.get("image_summary") or {},
            "sieger_standard": report.get("sieger_standard") or {},
            "ambiguity_notes": identity.get("ambiguity_notes") or [],
            "unconfirmed_fact_list": report.get("unconfirmed_fact_list") or [],
            "selected_sales_angle": approved_angle,
            "selected_claims": [
                item for item in claim_ledger
                if isinstance(item, dict) and item.get("claim_id") in selected_claim_ids
            ],
            "selected_evidence": [
                item for item in evidence_ledger
                if isinstance(item, dict) and item.get("evidence_id") in selected_evidence_ids
            ],
            "evidence_titles": [item.get("title") for item in evidence[:5] if isinstance(item, dict) and item.get("title")],
            "evidence_refs": [item.get("url") for item in evidence[:5] if isinstance(item, dict) and item.get("url")],
            "recent_signals": [summarize_signal(item) for item in recent_signals[:3] if summarize_signal(item)],
            "market_signals": [summarize_signal(item) for item in market_signals[:3] if summarize_signal(item)],
            "recommended_opening_signal_en": recommended_opening_signal(report),
            "recommended_sales_angle_en": first_non_empty(
                approved_angle.get("en"),
            ),
        },
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bridge a customer-intel JSON report into the outreach-email input shape."
    )
    parser.add_argument("--input-json", help="Path to the customer-intel JSON report.")
    parser.add_argument(
        "--email-type",
        choices=["first_touch", "follow_up"],
        default="first_touch",
        help="Target email scenario for the generated payload.",
    )
    parser.add_argument("--product-or-offer", default="", help="Required business offer to add manually.")
    parser.add_argument("--sender-name", default="", help="Optional sender name.")
    parser.add_argument("--sender-company", default="", help="Optional sender company.")
    parser.add_argument(
        "--approved-sales-angle-id",
        default="",
        help="Optional approved angle ID. Without an approved angle, the bridge remains on hold.",
    )
    parser.add_argument("--json-out", help="Optional path to save the bridged JSON payload.")
    args = parser.parse_args()

    report = load_input(args.input_json)
    payload = build_bridge_payload(
        report,
        args.email_type,
        args.product_or_offer,
        args.sender_name,
        args.sender_company,
        args.approved_sales_angle_id,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
