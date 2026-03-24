#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


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
    validated = {
        "default_country_or_market": normalize_text(payload.get("default_country_or_market")),
        "operator_notes": normalize_text(payload.get("operator_notes")),
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
            "product_keywords": normalize_text(lead.get("product_keywords")),
            "source_type": normalize_text(lead.get("source_type")),
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
    return reasons


def follow_up_suggestions(lead: dict, reasons: list[str]) -> list[str]:
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
    if not suggestions:
        suggestions.append("可直接进入客户背调，并在背调阶段继续核对实体匹配。")
    return suggestions


def recommended_action(lead: dict, reasons: list[str]) -> str:
    strong_clues = 0
    if lead["company_name"]:
        strong_clues += 1
    if lead["company_website"]:
        strong_clues += 1
    if lead["email"] and email_domain(lead["email"]) not in PUBLIC_EMAIL_DOMAINS:
        strong_clues += 1
    if lead["person_name"]:
        strong_clues += 1

    if strong_clues >= 3 and len(reasons) <= 1:
        return "enter_customer_intel"
    if strong_clues >= 1:
        return "enrich_then_customer_intel"
    return "hold_for_manual_review"


def build_notes(lead: dict, reasons: list[str]) -> str:
    parts = []
    if lead["notes"]:
        parts.append(lead["notes"])
    if lead["source_url"]:
        parts.append(f"Source URL: {lead['source_url']}")
    if lead["linkedin_url"]:
        parts.append(f"LinkedIn URL: {lead['linkedin_url']}")
    if reasons:
        parts.append("Review: " + "；".join(reasons))
    return " | ".join(parts)


def normalize_lead(lead: dict, default_country_or_market: str, index: int) -> dict:
    normalized = dict(lead)
    if not normalized["country_or_market"] and default_country_or_market:
        normalized["country_or_market"] = default_country_or_market

    domain_clue = email_domain(normalized["email"])
    reasons = review_reasons(normalized)
    action = recommended_action(normalized, reasons)
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
        "lead_bucket": classify_lead(normalized),
        "missing_fields": missing,
        "manual_review_reasons": reasons,
        "recommended_next_action": action,
        "follow_up_suggestions": follow_up_suggestions(normalized, reasons),
        "customer_intel_input": {
            "company_name": normalized["company_name"],
            "person_name": normalized["person_name"],
            "email": normalized["email"],
            "company_website": normalized["company_website"],
            "country_or_market": normalized["country_or_market"],
            "notes": build_notes(normalized, reasons),
        },
    }
    return result


def build_report(payload: dict) -> dict:
    normalized_leads = [
        normalize_lead(lead, payload["default_country_or_market"], index)
        for index, lead in enumerate(payload["leads"], start=1)
    ]
    summary = {
        "total_leads": len(normalized_leads),
        "ready_for_customer_intel": sum(
            1 for lead in normalized_leads if lead["recommended_next_action"] == "enter_customer_intel"
        ),
        "need_enrichment": sum(
            1 for lead in normalized_leads if lead["recommended_next_action"] == "enrich_then_customer_intel"
        ),
        "manual_review": sum(
            1 for lead in normalized_leads if lead["recommended_next_action"] == "hold_for_manual_review"
        ),
        "operator_notes": payload["operator_notes"],
    }
    return {"summary": summary, "leads": normalized_leads}


def render_markdown(report: dict) -> str:
    lines = [
        "# Lead Screening Package",
        "",
        "## Summary",
        f"- Total Leads: {report['summary']['total_leads']}",
        f"- Ready for Customer Intel: {report['summary']['ready_for_customer_intel']}",
        f"- Need Enrichment: {report['summary']['need_enrichment']}",
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
                f"- Recommended Next Action: {lead['recommended_next_action']}",
                "- Missing Fields: " + (", ".join(lead["missing_fields"]) if lead["missing_fields"] else "(none)"),
            ]
        )
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
