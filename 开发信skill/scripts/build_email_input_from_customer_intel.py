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


def infer_goal(report: dict, email_type: str) -> str:
    sales_angles = report.get("sales_angles") or []
    if sales_angles and isinstance(sales_angles[0], dict):
        angle = str(sales_angles[0].get("en", "")).strip()
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


def infer_constraints(report: dict) -> str:
    parts = ["Use only public, confirmed information.", "Avoid hard claims about demand, pricing, or purchasing intent."]
    if str(report.get("risk_rating", "")).strip().lower() == "high":
        parts.append("High-risk lead: review manually before any outreach.")
    intel_decision = report.get("intel_decision") or {}
    if intel_decision.get("recommended_next_action") == "hold_for_manual_review":
        parts.append("Pause at manual review if the intel stage has not cleared the lead for outreach drafting.")
    return " ".join(parts)


def build_bridge_payload(
    report: dict,
    email_type: str,
    product_or_offer: str,
    sender_name: str,
    sender_company: str,
) -> dict:
    identity = report.get("identity_snapshot") or {}
    company_profile = report.get("company_profile") or {}
    intel_decision = report.get("intel_decision") or {}
    evidence = report.get("evidence") or []
    payload = {
        "email_type": email_type,
        "customer_name": first_non_empty(identity.get("person_name"), "there"),
        "company_name": first_non_empty(identity.get("company_name")),
        "product_or_offer": product_or_offer.strip(),
        "goal": infer_goal(report, email_type),
        "country_or_market": first_non_empty(identity.get("country_or_market")),
        "customer_profile_summary": first_non_empty(company_profile.get("apparent_business")),
        "previous_contact_context": "",
        "tone": "professional,conservative",
        "sender_name": sender_name.strip(),
        "sender_company": sender_company.strip(),
        "signature": "",
        "constraints": infer_constraints(report),
        "source_context": {
            "risk_rating": report.get("risk_rating"),
            "entity_confidence": identity.get("entity_confidence"),
            "evidence_sufficiency": intel_decision.get("evidence_sufficiency"),
            "intel_recommended_next_action": intel_decision.get("recommended_next_action"),
            "ambiguity_notes": identity.get("ambiguity_notes") or [],
            "unconfirmed_fact_list": report.get("unconfirmed_fact_list") or [],
            "evidence_titles": [item.get("title") for item in evidence[:5] if isinstance(item, dict) and item.get("title")],
            "recommended_sales_angle_en": first_non_empty(
                (report.get("sales_angles") or [{}])[0].get("en") if report.get("sales_angles") else "",
                report.get("summary_en"),
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
    parser.add_argument("--json-out", help="Optional path to save the bridged JSON payload.")
    args = parser.parse_args()

    report = load_input(args.input_json)
    payload = build_bridge_payload(
        report,
        args.email_type,
        args.product_or_offer,
        args.sender_name,
        args.sender_company,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
