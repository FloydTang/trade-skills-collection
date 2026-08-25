#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_DECISION_GATES = ("identity", "evidence", "seller_offer", "product_fit", "risk")
STRONG_SOURCE_QUALITIES = frozenset({"primary", "strong_secondary"})
GENERIC_EVIDENCE_IDENTITIES = frozenset(
    {
        "evidence",
        "n/a",
        "na",
        "none",
        "null",
        "source",
        "unknown",
        "untitled",
        "untitled evidence",
        "web",
        "website",
    }
)


def load_input(path_arg: str | None) -> dict:
    if path_arg:
        return json.loads(Path(path_arg).read_text(encoding="utf-8"))
    return json.load(sys.stdin)


def first_non_empty(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _usable_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _usable_source_identity(value: object) -> str:
    if not isinstance(value, str):
        return ""
    identity = " ".join(value.strip().lower().split())
    if not identity or identity in GENERIC_EVIDENCE_IDENTITIES:
        return ""
    if identity.startswith("unknown ") or identity.startswith("untitled "):
        return ""
    return value.strip()


def _source_identity(evidence: dict) -> str:
    for value in (
        evidence.get("source_id"),
        evidence.get("source_name"),
        evidence.get("source_title"),
        evidence.get("title"),
    ):
        identity = _usable_source_identity(value)
        if identity:
            return identity
    return ""


def _ledger_index(items: object, id_key: str) -> tuple[dict[str, dict], list[str]]:
    indexed: dict[str, dict] = {}
    duplicate_ids: list[str] = []
    if not isinstance(items, list):
        return indexed, duplicate_ids
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = first_non_empty(item.get(id_key))
        if not item_id:
            continue
        if item_id in indexed:
            duplicate_ids.append(item_id)
            continue
        indexed[item_id] = item
    return indexed, duplicate_ids


def _selected_ids(angle: dict, key: str) -> tuple[list[str], list[str]]:
    value = angle.get(key)
    label = "claim_ids" if key == "claim_ids" else "evidence_ids"
    if not isinstance(value, list) or not value:
        return [], [f"人工批准的销售角度缺少非空 {label}。"]
    ids = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    reasons = []
    if len(ids) != len(value):
        reasons.append(f"人工批准的销售角度的 {label} 含有空或非字符串 ID。")
    if len(ids) != len(set(ids)):
        reasons.append(f"人工批准的销售角度的 {label} 含有重复 ID。")
    if not ids:
        reasons.append(f"人工批准的销售角度缺少非空 {label}。")
    return ids, reasons


def report_gates_ready(report: dict) -> tuple[bool, list[str]]:
    intel_decision = report.get("intel_decision") or {}
    reasons = []
    if intel_decision.get("recommended_next_action") != "ready_for_email_draft":
        reasons.append("客户背调尚未通过 ready_for_email_draft 门槛。")

    gates = intel_decision.get("decision_gates")
    if not isinstance(gates, dict) or not gates:
        reasons.append("客户背调缺少可验证的 decision_gates，不能授权。")
    else:
        missing_gates = [name for name in REQUIRED_DECISION_GATES if name not in gates]
        if missing_gates:
            reasons.append("客户背调缺少完整决策门槛：" + ", ".join(missing_gates) + "。")
        failed_gates = [
            name
            for name, gate in gates.items()
            if not isinstance(gate, dict) or gate.get("status") != "pass"
        ]
        if failed_gates:
            reasons.append(
                "客户背调决策门槛未全部通过："
                + ", ".join(str(name) for name in failed_gates)
                + "。"
            )
    if intel_decision.get("manual_review_required") is True:
        reasons.append("客户背调仍标记为需要人工复核。")
    return not reasons, reasons


def validate_approved_angle(
    report: dict, approved_angle: dict
) -> tuple[list[dict], list[dict], list[str]]:
    if not approved_angle:
        return [], [], ["没有人工批准的销售角度。"]

    reasons = []
    if not first_non_empty(approved_angle.get("angle_id")):
        reasons.append("人工批准的销售角度缺少 angle_id。")

    selected_claim_ids, claim_id_reasons = _selected_ids(approved_angle, "claim_ids")
    selected_evidence_ids, evidence_id_reasons = _selected_ids(approved_angle, "evidence_ids")
    reasons.extend(claim_id_reasons)
    reasons.extend(evidence_id_reasons)

    claim_by_id, duplicate_claim_ids = _ledger_index(report.get("claim_ledger") or [], "claim_id")
    evidence_by_id, duplicate_evidence_ids = _ledger_index(
        report.get("evidence_ledger") or [], "evidence_id"
    )
    if duplicate_claim_ids:
        reasons.append("claim_ledger 含有重复 claim_id：" + ", ".join(sorted(set(duplicate_claim_ids))) + "。")
    if duplicate_evidence_ids:
        reasons.append(
            "evidence_ledger 含有重复 evidence_id："
            + ", ".join(sorted(set(duplicate_evidence_ids)))
            + "。"
        )

    missing_claim_ids = [item for item in selected_claim_ids if item not in claim_by_id]
    if missing_claim_ids:
        reasons.append("销售角度引用了不存在的 claim_id：" + ", ".join(missing_claim_ids) + "。")
    missing_evidence_ids = [item for item in selected_evidence_ids if item not in evidence_by_id]
    if missing_evidence_ids:
        reasons.append("销售角度引用了不存在的 evidence_id：" + ", ".join(missing_evidence_ids) + "。")

    selected_claims = [claim_by_id[item] for item in selected_claim_ids if item in claim_by_id]
    selected_evidence = [evidence_by_id[item] for item in selected_evidence_ids if item in evidence_by_id]
    strong_selected_evidence_ids = {
        first_non_empty(item.get("evidence_id"))
        for item in selected_evidence
        if first_non_empty(item.get("source_quality")).lower() in STRONG_SOURCE_QUALITIES
    }
    if selected_evidence and not strong_selected_evidence_ids:
        reasons.append("人工批准的销售角度没有引用 primary 或 strong_secondary 证据。")

    selected_product_fit_claims = []
    for claim in selected_claims:
        claim_id = first_non_empty(claim.get("claim_id")) or "(missing claim_id)"
        statement = claim.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            reasons.append(f"选中的 claim {claim_id} 的 statement 为空。")
            continue
        status = first_non_empty(claim.get("status")).lower()
        statement_type = first_non_empty(claim.get("statement_type")).lower()
        reviewable = status == "needs_review" and statement_type in {"hypothesis", "inference"}
        if status != "supported" and not reviewable:
            reasons.append(
                f"选中的 claim {claim_id} 不满足授权状态："
                f"status={status or '(missing)'}，statement_type={statement_type or '(missing)'}。"
            )
        claim_evidence_ids = claim.get("evidence_ids")
        if not isinstance(claim_evidence_ids, list) or not claim_evidence_ids:
            reasons.append(f"选中的 claim {claim_id} 缺少 evidence_ids。")
            continue
        normalized_claim_evidence_ids = {
            item.strip()
            for item in claim_evidence_ids
            if isinstance(item, str) and item.strip()
        }
        if len(normalized_claim_evidence_ids) != len(claim_evidence_ids):
            reasons.append(f"选中的 claim {claim_id} 的 evidence_ids 含有空值、非字符串或重复 ID。")
        dangling_claim_evidence = sorted(normalized_claim_evidence_ids - set(evidence_by_id))
        if dangling_claim_evidence:
            reasons.append(
                f"选中的 claim {claim_id} 引用了不存在的 evidence_id："
                + ", ".join(dangling_claim_evidence)
                + "。"
            )
        if not normalized_claim_evidence_ids.intersection(selected_evidence_ids):
            reasons.append(f"选中的 claim {claim_id} 与销售角度 evidence_ids 没有交集。")
        if first_non_empty(claim.get("category")).lower() == "product_fit":
            selected_product_fit_claims.append(claim)
            if not normalized_claim_evidence_ids.intersection(strong_selected_evidence_ids):
                reasons.append(f"选中的 product_fit claim {claim_id} 未绑定强证据。")

    if selected_claims and not selected_product_fit_claims:
        reasons.append("人工批准的销售角度缺少 product_fit 主张。")

    for evidence in selected_evidence:
        evidence_id = first_non_empty(evidence.get("evidence_id")) or "(missing evidence_id)"
        url = first_non_empty(evidence.get("url"), evidence.get("source_url"))
        if not _usable_url(url) and not _source_identity(evidence):
            reasons.append(f"选中的 evidence {evidence_id} 缺少可用 URL 或来源身份。")

    return selected_claims, selected_evidence, reasons


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
        industry_lens = str(report.get("industry_lens") or "general").strip().lower()
        if email_type == "follow_up":
            if industry_lens == "industrial":
                return "follow up on a technical fit review for one relevant application"
            if industry_lens == "food":
                return "follow up on our product and sourcing fit"
            return "follow up on our product and business fit"
        if industry_lens == "industrial":
            return "check whether a technical fit review for one relevant application would be useful"
        if industry_lens == "food":
            return "check whether our product and sourcing fit may be relevant"
        return "check whether our product and business fit may be relevant"
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


def _selected_evidence_urls(selected_evidence: list[dict]) -> set[str]:
    urls = set()
    for evidence in selected_evidence:
        for key in ("url", "source_url"):
            value = evidence.get(key)
            if _usable_url(value):
                urls.add(value.strip())
    return urls


def _signal_is_linked_to_selected_evidence(
    signal: dict, selected_evidence_ids: set[str], selected_evidence_urls: set[str]
) -> bool:
    signal_evidence_ids = signal.get("evidence_ids")
    if isinstance(signal_evidence_ids, list):
        normalized_signal_ids = {
            item.strip()
            for item in signal_evidence_ids
            if isinstance(item, str) and item.strip()
        }
        if normalized_signal_ids.intersection(selected_evidence_ids):
            return True

    source_url = signal.get("source_url")
    return isinstance(source_url, str) and source_url.strip() in selected_evidence_urls


def recommended_opening_signal(
    report: dict,
    selected_evidence_ids: set[str] | None = None,
    selected_evidence_urls: set[str] | None = None,
) -> str:
    selected_evidence_ids = selected_evidence_ids or set()
    selected_evidence_urls = selected_evidence_urls or set()
    for key in ("recent_signals", "market_signals"):
        signals = report.get(key) or []
        for signal in signals:
            if not isinstance(signal, dict):
                continue
            title = str(signal.get("title", "")).strip()
            confidence = str(signal.get("confidence", "")).strip()
            if (
                title
                and confidence in {"high", "medium"}
                and _signal_is_linked_to_selected_evidence(
                    signal, selected_evidence_ids, selected_evidence_urls
                )
            ):
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
    previous_contact_context: str = "",
) -> dict:
    identity = report.get("identity_snapshot") or {}
    company_profile = report.get("company_profile") or {}
    intel_decision = report.get("intel_decision") or {}
    verdict_card = report.get("verdict_card") or {}
    evidence = report.get("evidence") or []
    recent_signals = report.get("recent_signals") or []
    market_signals = report.get("market_signals") or []
    approved_angle = select_approved_angle(report, approved_sales_angle_id)
    intel_ready, gate_reasons = report_gates_ready(report)
    selected_claims, selected_evidence, angle_reasons = validate_approved_angle(report, approved_angle)
    authorization_reasons = list(gate_reasons)
    authorization_reasons.extend(angle_reasons)
    draft_authorization = "approved" if intel_ready and approved_angle and not angle_reasons else "hold"
    selected_evidence_ids = {
        item_id
        for item in selected_evidence
        if (item_id := first_non_empty(item.get("evidence_id")))
    }
    selected_evidence_urls = _selected_evidence_urls(selected_evidence)
    opening_signal = (
        recommended_opening_signal(report, selected_evidence_ids, selected_evidence_urls)
        if draft_authorization == "approved"
        else ""
    )
    payload = {
        "email_type": email_type,
        "customer_name": first_non_empty(
            identity.get("person_name"),
            f"{first_non_empty(identity.get('company_name'))} team",
        ),
        "company_name": first_non_empty(identity.get("company_name")),
        "product_or_offer": product_or_offer.strip(),
        "goal": infer_goal(report, email_type, approved_angle),
        "country_or_market": first_non_empty(identity.get("country_or_market")),
        "customer_profile_summary": first_non_empty(company_profile.get("apparent_business")),
        "previous_contact_context": previous_contact_context.strip(),
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
            "manual_review_required": intel_decision.get("manual_review_required"),
            "decision_gates": intel_decision.get("decision_gates") or {},
            "sieger_status": intel_decision.get("sieger_status") or verdict_card.get("intel_decision"),
            "industry_lens": report.get("industry_lens") or "general",
            "seller_context": report.get("seller_context") or {},
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
            "selected_claims": selected_claims,
            "selected_evidence": selected_evidence,
            "evidence_titles": [item.get("title") for item in evidence[:5] if isinstance(item, dict) and item.get("title")],
            "evidence_refs": [item.get("url") for item in evidence[:5] if isinstance(item, dict) and item.get("url")],
            "recent_signals": [summarize_signal(item) for item in recent_signals[:3] if summarize_signal(item)],
            "market_signals": [summarize_signal(item) for item in market_signals[:3] if summarize_signal(item)],
            "recommended_opening_signal_en": opening_signal,
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
        "--previous-contact-context",
        default="",
        help="Required factual summary of the prior touch when email-type is follow_up.",
    )
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
        args.previous_contact_context,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
