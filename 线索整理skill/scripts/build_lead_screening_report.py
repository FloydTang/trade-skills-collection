#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = next(
    (root for root in SCRIPT_DIR.parents if (root / "workflow_runtime" / "contracts.py").is_file()),
    None,
)
if REPO_ROOT is None:
    raise RuntimeError("Could not locate workflow_runtime/contracts.py.")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow_runtime.contracts import screening_action_legacy


PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "163.com",
    "126.com",
    "qq.com",
    "icloud.com",
    "yahoo.com",
    "proton.me",
    "protonmail.com",
}


def load_json(path: str | None) -> object:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.loads(sys.stdin.read())


def dump_json(data: object, path: str | None) -> None:
    if not path:
        return
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dump_text(text: str, path: str | None) -> None:
    if not path:
        return
    Path(path).write_text(text, encoding="utf-8")


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize_email(value: object) -> str:
    return normalize_text(value).lower()


def normalize_url(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        return text
    if "." in text and " " not in text:
        return f"https://{text}"
    return text


def normalize_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [normalize_text(item) for item in value if normalize_text(item)]


def normalize_seller_context(value: object, product_or_offer: str, target_customer_type: str) -> dict:
    raw = value if isinstance(value, dict) else {}
    return {
        "company_name": normalize_text(raw.get("company_name")),
        "product_or_offer": normalize_text(raw.get("product_or_offer")) or product_or_offer,
        "product_categories": normalize_list(raw.get("product_categories")),
        "target_customer_types": normalize_list(raw.get("target_customer_types"))
        or ([target_customer_type] if target_customer_type else []),
        "target_industries": normalize_list(raw.get("target_industries")),
        "value_propositions": normalize_list(raw.get("value_propositions")),
        "certifications": normalize_list(raw.get("certifications")),
        "proof_points": normalize_list(raw.get("proof_points")),
        "authorized_materials": normalize_list(raw.get("authorized_materials")),
        "excluded_customer_signals": normalize_list(raw.get("excluded_customer_signals")),
        "forbidden_claims": normalize_list(raw.get("forbidden_claims")),
    }


def email_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.split("@", 1)[1].lower()


def website_domain(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def clue_count(lead: dict) -> int:
    return sum(
        1
        for key in ["company_name", "company_website", "person_name", "email"]
        if normalize_text(lead.get(key))
    )


def validate_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON object.")
    leads = payload.get("leads")
    if not isinstance(leads, list) or not leads:
        raise ValueError("Input must include a non-empty leads array.")
    product_or_offer = normalize_text(payload.get("product_or_offer"))
    target_customer_type = normalize_text(payload.get("target_customer_type"))
    validated = {
        "default_country_or_market": normalize_text(payload.get("default_country_or_market")),
        "operator_notes": normalize_text(payload.get("operator_notes")),
        "product_or_offer": product_or_offer,
        "target_customer_type": target_customer_type,
        "industry_lens": normalize_text(payload.get("industry_lens")) or "auto",
        "seller_context": normalize_seller_context(
            payload.get("seller_context"), product_or_offer, target_customer_type
        ),
        "leads": [],
    }
    for index, lead in enumerate(leads, start=1):
        if not isinstance(lead, dict):
            raise ValueError(f"Lead #{index} must be an object.")
        normalized = {
            "company_name": normalize_text(lead.get("company_name")),
            "company_website": normalize_url(lead.get("company_website")),
            "person_name": normalize_text(lead.get("person_name")),
            "email": normalize_email(lead.get("email")),
            "country_or_market": normalize_text(lead.get("country_or_market")),
            "source_url": normalize_url(lead.get("source_url")),
            "linkedin_url": normalize_url(lead.get("linkedin_url")),
            "notes": normalize_text(lead.get("notes")),
            "evidence_grade": normalize_text(lead.get("evidence_grade")).upper(),
            "match_reason": normalize_text(lead.get("match_reason")),
            "evidence_summary": normalize_text(lead.get("evidence_summary")),
            "discovery_missing_fields": [
                normalize_text(item)
                for item in (lead.get("discovery_missing_fields") or [])
                if normalize_text(item)
            ],
            "discovery_next_action": normalize_text(lead.get("discovery_next_action")),
            "product_keywords": normalize_text(lead.get("product_keywords")),
            "source_type": normalize_text(lead.get("source_type")),
            "source_name": normalize_text(lead.get("source_name")),
            "source_url_or_note": normalize_text(lead.get("source_url_or_note")),
            "freshness": normalize_text(lead.get("freshness")),
            "confidence": normalize_text(lead.get("confidence")),
            "match_basis": normalize_text(lead.get("match_basis")),
        }
        if clue_count(normalized) == 0:
            raise ValueError(f"Lead #{index} must include at least one clue field.")
        validated["leads"].append(normalized)
    return validated


def classify_lead(lead: dict) -> str:
    has_company = bool(lead["company_name"])
    has_website = bool(lead["company_website"])
    has_person = bool(lead["person_name"])
    has_email = bool(lead["email"])

    if has_company and has_website and has_person and has_email:
        return "website_company_full_contact"
    if has_company and has_website and (has_person or has_email):
        return "website_company_partial_contact"
    if has_company and has_email and not has_website:
        return "company_email_no_website"
    if has_company and has_website:
        return "website_company_basic"
    if has_email and not has_company and not has_website:
        return "email_only_clue"
    if has_website and not has_company:
        return "website_only_clue"
    if has_company:
        return "company_only_clue"
    return "weak_clue"


def review_reasons(lead: dict) -> list[str]:
    reasons = []
    domain_from_email = email_domain(lead["email"])
    domain_from_website = website_domain(lead["company_website"])
    if lead["email"] and domain_from_email in PUBLIC_EMAIL_DOMAINS:
        reasons.append("邮箱使用公共域名，不能直接当作企业身份强证据。")
    if lead["email"] and not lead["company_name"] and not lead["company_website"]:
        reasons.append("当前只有邮箱线索，建议先补公司名或官网再进入客户背调。")
    if lead["person_name"] and not lead["company_name"] and not lead["company_website"]:
        reasons.append("当前只有联系人线索，联系人与公司关系较弱，需人工复核。")
    if domain_from_email and domain_from_website and domain_from_email != domain_from_website:
        reasons.append("邮箱域名与官网域名不一致，需确认是否同一主体。")
    if lead["company_name"] and lead["company_website"] and domain_from_website:
        compact_name = lead["company_name"].lower().replace(" ", "")
        compact_domain = domain_from_website.replace("-", "").replace(".", "")
        if compact_name[:6] and compact_name[:6] not in compact_domain:
            reasons.append("公司名与官网域名对应关系较弱，建议人工确认主体匹配。")
    if lead.get("discovery_next_action") == "reject_low_evidence":
        reasons.append("搜索阶段已判定为低证据候选，不建议直接推进。")
    return reasons


FIT_STOPWORDS = {
    "and", "for", "the", "with", "from", "into", "supply", "supplier",
    "company", "product", "products", "service", "services", "solution", "solutions",
}


def fit_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9+-]{2,}", text.lower())
        if token not in FIT_STOPWORDS
    }


def assess_business_fit(lead: dict, payload: dict) -> dict:
    seller_context = payload["seller_context"]
    context_terms = [
        payload["product_or_offer"],
        payload["target_customer_type"],
        *seller_context["product_categories"],
        *seller_context["target_customer_types"],
        *seller_context["target_industries"],
    ]
    context_terms = list(dict.fromkeys(term for term in context_terms if term))
    context_present = bool(context_terms)
    haystack = " ".join(
        str(lead.get(key, ""))
        for key in (
            "company_name", "notes", "product_keywords", "match_basis",
            "match_reason", "evidence_summary",
        )
    ).lower()
    excluded = [
        term for term in seller_context["excluded_customer_signals"]
        if term.lower() in haystack
    ]
    if excluded:
        return {
            "rating": "low",
            "context_present": context_present,
            "matched_terms": [],
            "reasons": [f"命中排除信号：{', '.join(excluded)}"],
        }
    if not context_present:
        return {
            "rating": "unknown",
            "context_present": False,
            "matched_terms": [],
            "reasons": ["未提供我方产品或目标客户上下文，暂不判断业务匹配度。"],
        }
    haystack_tokens = fit_tokens(haystack)
    matched: list[str] = []
    overlap_tokens: set[str] = set()
    for term in context_terms:
        term_tokens = fit_tokens(term)
        overlap = term_tokens & haystack_tokens
        if term.lower() in haystack or len(overlap) >= 2:
            matched.append(term)
        overlap_tokens.update(overlap)
    if matched or len(overlap_tokens) >= 2:
        rating = "high"
    elif overlap_tokens:
        rating = "medium"
    else:
        rating = "unknown"
    reasons = (
        [f"候选公开描述与目标上下文匹配：{', '.join(matched[:4] or sorted(overlap_tokens)[:4])}"]
        if rating in {"high", "medium"}
        else ["现有线索未证明该客户与我方产品匹配，需要补业务线或采购场景证据。"]
    )
    return {
        "rating": rating,
        "context_present": True,
        "matched_terms": matched[:6] or sorted(overlap_tokens)[:6],
        "reasons": reasons,
    }


def follow_up_suggestions(lead: dict, reasons: list[str], business_fit: dict) -> list[str]:
    suggestions = []
    if not lead["company_name"]:
        suggestions.append("补公司正式名称或官网标题。")
    if not lead["company_website"] and lead["email"]:
        suggestions.append("先根据邮箱域名确认官网是否存在。")
    if not lead["email"]:
        suggestions.append("如后续要开发信，可优先补公司邮箱或联系人邮箱。")
    if not lead["country_or_market"]:
        suggestions.append("补国家市场，方便背调和后续触达语言判断。")
    if reasons:
        suggestions.append("先处理人工复核项，再决定是否进入客户背调。")
    if business_fit["rating"] == "unknown" and business_fit["context_present"]:
        suggestions.append("补充客户业务线、产品或采购场景证据，确认与我方产品是否匹配。")
    if business_fit["rating"] == "low":
        suggestions.append("已命中排除信号，除非人工纠正，否则不进入客户背调。")
    if lead.get("evidence_grade") in {"C", "D"}:
        suggestions.append("优先补官网、LinkedIn 或主体可验证字段，再进入客户背调。")
    if not suggestions:
        suggestions.append("可直接进入客户背调，并在背调阶段继续核对实体匹配。")
    return suggestions


def recommended_action(lead: dict, reasons: list[str], business_fit: dict) -> str:
    strong_clues = 0
    if lead["company_name"]:
        strong_clues += 1
    if lead["company_website"]:
        strong_clues += 1
    if lead["email"] and email_domain(lead["email"]) not in PUBLIC_EMAIL_DOMAINS:
        strong_clues += 1
    if lead["person_name"]:
        strong_clues += 1

    evidence_grade = lead.get("evidence_grade") or ""
    discovery_next_action = lead.get("discovery_next_action") or ""

    if discovery_next_action == "reject_low_evidence":
        return "hold_for_manual_review"
    if business_fit["rating"] == "low":
        return "hold_for_manual_review"
    fit_allows_progress = business_fit["rating"] in {"high", "medium"} or not business_fit["context_present"]
    if evidence_grade in {"A", "B"} and strong_clues >= 2 and len(reasons) <= 1 and fit_allows_progress:
        return "ready_for_customer_intel"
    if strong_clues >= 1:
        return "needs_enrichment"
    return "hold_for_manual_review"


def build_notes(lead: dict, reasons: list[str]) -> str:
    parts = []
    if lead["notes"]:
        parts.append(lead["notes"])
    if lead.get("evidence_summary"):
        parts.append(f"Evidence Summary: {lead['evidence_summary']}")
    if lead.get("match_reason"):
        parts.append(f"Match Reason: {lead['match_reason']}")
    if lead["source_url"]:
        parts.append(f"Source URL: {lead['source_url']}")
    if lead.get("source_type"):
        parts.append(f"Source Type: {lead['source_type']}")
    if lead.get("source_name"):
        parts.append(f"Source Name: {lead['source_name']}")
    if lead.get("source_url_or_note"):
        parts.append(f"Source Note: {lead['source_url_or_note']}")
    if lead.get("freshness"):
        parts.append(f"Freshness: {lead['freshness']}")
    if lead.get("confidence"):
        parts.append(f"Confidence: {lead['confidence']}")
    if lead.get("match_basis"):
        parts.append(f"Match Basis: {lead['match_basis']}")
    if lead["linkedin_url"]:
        parts.append(f"LinkedIn URL: {lead['linkedin_url']}")
    if reasons:
        parts.append("Review: " + "；".join(reasons))
    return " | ".join(parts)


def normalize_lead(lead: dict, payload: dict, index: int) -> dict:
    normalized = dict(lead)
    if not normalized["country_or_market"] and payload["default_country_or_market"]:
        normalized["country_or_market"] = payload["default_country_or_market"]

    domain_clue = email_domain(normalized["email"])
    reasons = review_reasons(normalized)
    business_fit = assess_business_fit(normalized, payload)
    action = recommended_action(normalized, reasons, business_fit)
    missing = [
        key
        for key in ["company_name", "company_website", "person_name", "email", "country_or_market"]
        if not normalize_text(normalized.get(key))
    ]
    result = {
        "lead_id": f"lead-{index:03d}",
        "normalized_company_name": normalized["company_name"],
        "normalized_person_name": normalized["person_name"],
        "email": normalized["email"],
        "email_domain_clue": domain_clue,
        "company_website": normalized["company_website"],
        "country_or_market": normalized["country_or_market"],
        "source_url": normalized["source_url"],
        "linkedin_url": normalized["linkedin_url"],
        "product_keywords": normalized["product_keywords"],
        "source_type": normalized["source_type"],
        "source_name": normalized["source_name"],
        "source_url_or_note": normalized["source_url_or_note"],
        "freshness": normalized["freshness"],
        "confidence": normalized["confidence"],
        "match_basis": normalized["match_basis"],
        "evidence_grade": normalized["evidence_grade"] or "C",
        "match_reason": normalized["match_reason"],
        "evidence_summary": normalized["evidence_summary"],
        "discovery_missing_fields": normalized["discovery_missing_fields"],
        "discovery_next_action": normalized["discovery_next_action"],
        "lead_bucket": classify_lead(normalized),
        "business_fit": business_fit,
        "missing_fields": missing,
        "manual_review_reasons": reasons,
        "recommended_next_action": action,
        "legacy_recommended_next_action": screening_action_legacy(action),
        "follow_up_suggestions": follow_up_suggestions(normalized, reasons, business_fit),
        "customer_intel_input": {
            "company_name": normalized["company_name"],
            "person_name": normalized["person_name"],
            "email": normalized["email"],
            "company_website": normalized["company_website"],
            "country_or_market": normalized["country_or_market"],
            "product_or_offer": payload["product_or_offer"] or payload["seller_context"]["product_or_offer"],
            "industry_lens": payload["industry_lens"],
            "seller_context": payload["seller_context"],
            "screening_context": {
                "business_fit": business_fit,
                "evidence_grade": normalized["evidence_grade"] or "C",
                "recommended_next_action": action,
            },
            "notes": build_notes(normalized, reasons),
        },
    }
    return result


def build_report(payload: dict) -> dict:
    normalized_leads = [
        normalize_lead(lead, payload, index)
        for index, lead in enumerate(payload["leads"], start=1)
    ]
    summary = {
        "total_leads": len(normalized_leads),
        "ready_for_customer_intel": sum(
            1 for lead in normalized_leads if lead["recommended_next_action"] == "ready_for_customer_intel"
        ),
        "needs_enrichment": sum(
            1 for lead in normalized_leads if lead["recommended_next_action"] == "needs_enrichment"
        ),
        "manual_review": sum(
            1 for lead in normalized_leads if lead["recommended_next_action"] == "hold_for_manual_review"
        ),
        "operator_notes": payload["operator_notes"],
        "product_or_offer": payload["product_or_offer"],
        "industry_lens": payload["industry_lens"],
    }
    return {"summary": summary, "leads": normalized_leads}


def render_markdown(report: dict) -> str:
    lines = [
        "# Lead Screening Package",
        "",
        "## Summary",
        f"- Total Leads: {report['summary']['total_leads']}",
        f"- Ready for Customer Intel: {report['summary']['ready_for_customer_intel']}",
        f"- Needs Enrichment: {report['summary']['needs_enrichment']}",
        f"- Manual Review: {report['summary']['manual_review']}",
    ]
    if report["summary"]["operator_notes"]:
        lines.append(f"- Operator Notes: {report['summary']['operator_notes']}")
    for lead in report["leads"]:
        lines.extend(
            [
                "",
                f"## {lead['lead_id']}",
                f"- Company: {lead['normalized_company_name'] or '(missing)'}",
                f"- Person: {lead['normalized_person_name'] or '(missing)'}",
                f"- Email: {lead['email'] or '(missing)'}",
                f"- Website: {lead['company_website'] or '(missing)'}",
                f"- Country/Market: {lead['country_or_market'] or '(missing)'}",
                f"- Lead Bucket: {lead['lead_bucket']}",
                f"- Evidence Grade: {lead['evidence_grade']}",
                f"- Business Fit: {lead['business_fit']['rating']}",
                f"- Discovery Next Action: {lead['discovery_next_action'] or '(missing)'}",
                f"- Recommended Next Action: {lead['recommended_next_action']}",
                f"- Legacy Recommended Next Action: {lead['legacy_recommended_next_action']}",
                "- Missing Fields: " + (", ".join(lead["missing_fields"]) if lead["missing_fields"] else "(none)"),
                "- Discovery Missing Fields: "
                + (", ".join(lead["discovery_missing_fields"]) if lead["discovery_missing_fields"] else "(none)"),
            ]
        )
        if lead["evidence_summary"]:
            lines.append(f"- Evidence Summary: {lead['evidence_summary']}")
        if lead["match_reason"]:
            lines.append(f"- Match Reason: {lead['match_reason']}")
        for reason in lead["business_fit"]["reasons"]:
            lines.append(f"- Business Fit Reason: {reason}")
        if lead["source_type"]:
            lines.append(f"- Source Type: {lead['source_type']}")
        if lead["source_name"]:
            lines.append(f"- Source Name: {lead['source_name']}")
        if lead["freshness"]:
            lines.append(f"- Freshness: {lead['freshness']}")
        if lead["confidence"]:
            lines.append(f"- Confidence: {lead['confidence']}")
        if lead["match_basis"]:
            lines.append(f"- Match Basis: {lead['match_basis']}")
        if lead["manual_review_reasons"]:
            lines.append("- Manual Review Reasons:")
            for reason in lead["manual_review_reasons"]:
                lines.append(f"  - {reason}")
        else:
            lines.append("- Manual Review Reasons: (none)")
        lines.append("- Follow-up Suggestions:")
        for item in lead["follow_up_suggestions"]:
            lines.append(f"  - {item}")
        lines.append("- Customer Intel Input:")
        lines.append("```json")
        lines.append(json.dumps(lead["customer_intel_input"], ensure_ascii=False, indent=2))
        lines.append("```")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--schema-path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = validate_payload(load_json(args.input_json))
    report = build_report(payload)
    markdown = render_markdown(report)
    dump_json(report, args.json_out)
    dump_text(markdown, args.markdown_out)
    sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
