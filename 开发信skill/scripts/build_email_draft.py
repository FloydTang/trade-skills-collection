#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ALLOWED_EMAIL_TYPES = {"first_touch", "follow_up"}
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_SCHEMA_PATH = SKILL_ROOT / "schemas" / "email-draft-input.schema.json"
_SAMPLE_TERM_RE = re.compile(r"\bsamples?\b|样品|打样|寄样", flags=re.IGNORECASE)
_SAMPLE_OBJECT_EN = r"samples?(?!\s+(?:policy|sheet|program|information|details|data|list|catalog|form|document))\b"
_SAMPLE_OBJECT_ZH = r"(?:样品|打样|寄样)(?!政策|资料|清单|表|信息|说明|目录)"
_SAMPLE_NEGATION_RE = re.compile(
    r"(?:"
    r"\b(?:no|not|never|cannot|can['’]t|unable(?:\s+to)?|without|unavailable|"
    r"isn['’]t|aren['’]t|won['’]t|will\s+not|must\s+not|mustn['’]t|"
    r"should\s+not|shouldn['’]t|do(?:es)?\s+(?:not|n['’]t)|"
    r"prohibit(?:s|ed)?|forbid(?:s|den)?|disallow(?:s|ed)?|"
    r"not\s+(?:allowed|permitted|available)|does\s+(?:not|n['’]t)\s+(?:allow|permit)|"
    r"do(?:es)?\s+(?:not|n['’]t)\s+(?:allow|permit))\b"
    r".{0,60}\bsamples?\b|"
    r"\bsamples?\b.{0,60}\b(?:no|not|never|cannot|can['’]t|unable(?:\s+to)?|"
    r"isn['’]t|aren['’]t|won['’]t|will\s+not|do(?:es)?\s+(?:not|n['’]t)|unavailable|"
    r"prohibit(?:s|ed)?|forbid(?:s|den)?|disallow(?:s|ed)?|"
    r"not\s+(?:allowed|permitted|available)|does\s+(?:not|n['’]t)\s+(?:allow|permit)|"
    r"do(?:es)?\s+(?:not|n['’]t)\s+(?:allow|permit))\b|"
    r"(?:不|未|暂不|暂无|没有|无|无法|不能|不可|禁止|严禁|不允许|不可以|不支持|未能|暂无法)"
    r"[^。；，,!?！？]{0,20}(?:样品|打样|寄样)|"
    r"(?:样品|打样|寄样)[^。；，,!?！？]{0,30}"
    r"(?:不提供|不支持|不允许|不可以|无法|不能|不可|没有|暂无|禁止|严禁|未提供|暂不|不)"
    r")",
    flags=re.IGNORECASE,
)
_NEGATION_CUE_RE = re.compile(
    r"(?:"
    r"\b(?:no|not|never|cannot|can['’]t|unable|unavailable|"
    r"isn['’]t|aren['’]t|wasn['’]t|weren['’]t|won['’]t|wouldn['’]t|"
    r"don['’]t|doesn['’]t|didn['’]t|mustn['’]t|shouldn['’]t|"
    r"prohibit(?:s|ed)?|forbid(?:s|den)?|disallow(?:s|ed)?|"
    r"refuse(?:s|d)?|decline(?:s|d)?|out\s+of\s+stock)\b|"
    r"(?:不|未|暂不|暂无|没有|无|无法|不能|不可|禁止|严禁|不允许|不可以|不支持|未能|暂无法)"
    r")",
    flags=re.IGNORECASE,
)
_SAMPLE_POSITIVE_RE = re.compile(
    r"(?:"
    r"\b(?:can|are able to|will|have the capability to|provide|offer|send|dispatch|ship|supply|prepare)\b"
    r"(?:\s+[a-z][a-z-]*){0,3}\s+"
    + _SAMPLE_OBJECT_EN
    + r"|"
    r"\bsamples?\b\s+(?:are\s+)?(?:currently\s+)?available\b|"
    r"\b(?:currently\s+)?available\s+" + _SAMPLE_OBJECT_EN + r"|"
    r"\bsamples?\b\s+(?:can|will|are\s+able\s+to)\s+(?:be\s+)?"
    r"(?:provided|offered|sent|dispatched|shipped|supplied|prepared)\b|"
    r"\b(?:sample\s+availability|availability\s+of\s+samples?)\b"
    r"\s*(?:is|remains|has\s+been)?\s*(?:currently\s+)?(?:available|confirmed)\b|"
    r"\bsamples?\s*[:\-]\s*(?:available|yes)\b|"
    r"(?:可|可以|能够|能|提供|支持|安排|准备|寄送|寄|发送|发)\s*"
    r"(?:提供|支持|安排|准备|寄送|寄|发送|发)?\s*(?:评估|测试|确认)?\s*"
    + _SAMPLE_OBJECT_ZH
    + r"|"
    r"(?:样品|打样|寄样)[^。；，,!?！？]{0,12}"
    r"(?:可用|可提供|可以提供|能够提供|支持寄样|可寄送|可寄|可发送|可发)|"
    r"(?:现有|备有|有)\s*"
    + _SAMPLE_OBJECT_ZH
    + r")",
    flags=re.IGNORECASE,
)


def _string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _contains_sample_term(text: str) -> bool:
    return bool(_SAMPLE_TERM_RE.search(text))


def _explicit_sample_negation(text: str) -> bool:
    return bool(
        _SAMPLE_NEGATION_RE.search(text)
        or (_contains_sample_term(text) and _NEGATION_CUE_RE.search(text))
    )


def _explicit_sample_support(text: str) -> bool:
    lowered = " ".join(text.strip().split()).lower()
    if not _contains_sample_term(lowered):
        return False
    if _explicit_sample_negation(lowered):
        return False
    return bool(_SAMPLE_POSITIVE_RE.search(lowered))


def has_authorized_sample_support(data: dict) -> bool:
    """Allow sample language only when an authorized seller field says so explicitly."""
    source_context = data.get("source_context") or {}
    candidate_texts: list[str] = []
    forbidden_texts: list[str] = []
    sample_availability_texts: list[str] = []
    seller_context = source_context.get("seller_context")
    if isinstance(seller_context, dict):
        for key in (
            "capabilities",
            "capability",
            "availability",
            "sample_availability",
            "value_propositions",
            "proof_points",
            "authorized_materials",
        ):
            candidate_texts.extend(_string_values(seller_context.get(key)))
        forbidden_texts.extend(_string_values(seller_context.get("forbidden_claims")))
        sample_availability_texts.extend(_string_values(seller_context.get("sample_availability")))
    for key in (
        "seller_capabilities",
        "seller_capability",
        "seller_availability",
        "seller_sample_availability",
        "seller_value_propositions",
        "seller_proof_points",
        "seller_authorized_materials",
    ):
        candidate_texts.extend(_string_values(source_context.get(key)))
    forbidden_texts.extend(_string_values(source_context.get("seller_forbidden_claims")))
    sample_availability_texts.extend(_string_values(source_context.get("seller_sample_availability")))
    if any(_contains_sample_term(text) for text in forbidden_texts):
        return False
    if any(_NEGATION_CUE_RE.search(text) for text in sample_availability_texts):
        return False
    combined_candidate_text = " ".join(candidate_texts)
    if _contains_sample_term(combined_candidate_text) and _NEGATION_CUE_RE.search(combined_candidate_text):
        return False
    if any(_explicit_sample_negation(text) for text in candidate_texts):
        return False
    return any(_explicit_sample_support(text) for text in candidate_texts)


def load_input(path_arg: str | None) -> dict:
    if path_arg:
        return json.loads(Path(path_arg).read_text(encoding="utf-8"))
    return json.load(sys.stdin)


def load_schema(schema_path: Path) -> dict:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def normalize(raw: dict) -> dict:
    fields = {
        "email_type": "",
        "customer_name": "",
        "company_name": "",
        "product_or_offer": "",
        "goal": "",
        "country_or_market": "",
        "customer_profile_summary": "",
        "previous_contact_context": "",
        "tone": "",
        "sender_name": "",
        "sender_company": "",
        "signature": "",
        "constraints": "",
        "source_context": {},
    }
    for key in fields:
        if key == "source_context":
            value = raw.get(key, {})
            fields[key] = value if isinstance(value, dict) else {}
            continue
        value = raw.get(key, "")
        fields[key] = value.strip() if isinstance(value, str) else value
    return fields


def validate_against_schema(raw: dict, schema: dict) -> None:
    if not isinstance(raw, dict):
        raise SystemExit("Input JSON must be an object.")

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    missing = [key for key in required if not raw.get(key)]
    if missing:
        raise SystemExit(f"Missing required fields: {', '.join(missing)}")

    for key, spec in properties.items():
        if key not in raw:
            continue
        value = raw[key]
        expected_type = spec.get("type")
        if expected_type == "string" and not isinstance(value, str):
            raise SystemExit(f"Field '{key}' must be a string.")
        if expected_type == "object" and not isinstance(value, dict):
            raise SystemExit(f"Field '{key}' must be an object.")
        if expected_type == "string" and "minLength" in spec and isinstance(value, str):
            if len(value.strip()) < int(spec["minLength"]):
                raise SystemExit(f"Field '{key}' must not be empty.")
        if "enum" in spec and value not in spec["enum"]:
            allowed = ", ".join(spec["enum"])
            raise SystemExit(f"Field '{key}' must be one of: {allowed}")


def validate(data: dict, raw: dict, schema: dict) -> None:
    validate_against_schema(raw, schema)
    if data["email_type"] not in ALLOWED_EMAIL_TYPES:
        raise SystemExit("email_type must be one of: first_touch, follow_up")
    if data["email_type"] == "follow_up" and not data["previous_contact_context"]:
        raise SystemExit("follow_up emails require previous_contact_context for conservative drafting.")
    source_context = data.get("source_context") or {}
    if source_context and source_context.get("draft_authorization") != "approved":
        reasons = source_context.get("authorization_reasons") or ["missing approved customer-intel angle"]
        raise SystemExit("Draft blocked: " + "; ".join(str(item) for item in reasons))


def scenario_label(email_type: str) -> str:
    return "First Touch" if email_type == "first_touch" else "Follow Up"


def selected_angle_en(data: dict) -> str:
    source_context = data.get("source_context") or {}
    selected = source_context.get("selected_sales_angle") or {}
    return str(selected.get("en") or source_context.get("recommended_sales_angle_en") or "").strip()


def is_industrial_evidence_angle(data: dict) -> bool:
    source_context = data.get("source_context") or {}
    return bool(selected_angle_en(data)) and source_context.get("industry_lens") == "industrial"


def build_customer_visible_angle_line(data: dict) -> str:
    """Turn the approved strategy into safe copy without exposing its drafting instructions."""
    if not selected_angle_en(data):
        return ""
    industry_lens = str((data.get("source_context") or {}).get("industry_lens") or "general")
    if industry_lens == "industrial":
        return (
            "Rather than assume your current setup, I would like to confirm the requirements for one "
            "relevant application before suggesting a technical fit."
        )
    if industry_lens == "food":
        return (
            "Rather than assume your current sourcing setup, I would like to confirm the product and "
            "supply requirements that matter to your team."
        )
    if industry_lens == "consumer":
        return (
            "Rather than assume your current assortment or supply setup, I would like to confirm the "
            "product requirements that matter to your team."
        )
    return (
        "Rather than assume your current priorities, I would like to understand the relevant product "
        "and business requirements before suggesting a fit."
    )


def ensure_sentence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    return cleaned if cleaned.endswith((".", "?", "!")) else cleaned + "."


def compact_product_label(product: str) -> str:
    parts = [part.strip() for part in re.split(r",|\band\b", product) if part.strip()]
    if len(parts) >= 2:
        return f"{parts[0]} and {parts[1]}"
    return product.strip()


def build_subjects(data: dict) -> list[str]:
    company = data["company_name"]
    product = data["product_or_offer"]
    if is_industrial_evidence_angle(data):
        compact_product = compact_product_label(product)
        return [
            f"{compact_product} application fit for {company}",
            f"A technical fit question for {company}",
        ]
    company_possessive = f"{company}'" if company.endswith("s") else f"{company}'s"
    if data["email_type"] == "first_touch":
        return [
            f"{product.title()} Supply for {company}",
            f"Possible Support for {company_possessive} {product.title()} Needs",
        ]
    subjects = [f"Following Up on {product.title()} for {company}"]
    if has_authorized_sample_support(data):
        subjects.append(f"Checking Whether {product.title()} Samples Would Help")
    else:
        subjects.append(f"Checking Whether {product.title()} Details Would Help")
    return subjects


def build_opening(data: dict) -> str:
    customer = data["customer_name"].strip()
    greeting = "Hello" if customer.lower() in {"", "there", "unknown", "n/a"} else f"Dear {customer}"
    if data["email_type"] == "first_touch":
        return f"{greeting},\n\nI hope you are doing well."
    return f"{greeting},\n\nI hope you have been well since my last email."


def build_context_line(data: dict) -> str:
    company = data["company_name"]
    product = data["product_or_offer"]
    market = data["country_or_market"]
    summary = data["customer_profile_summary"]
    source_context = data.get("source_context") or {}
    opening_signal = str(source_context.get("recommended_opening_signal_en", "")).strip()
    if _contains_sample_term(opening_signal) and not has_authorized_sample_support(data):
        opening_signal = ""
    if data["email_type"] == "first_touch":
        if is_industrial_evidence_angle(data):
            return (
                f"I am reaching out from {data['sender_company']}. We supply {product}, and I came across "
                f"{company}'s public industrial portfolio."
            )
        base = (
            f"I am reaching out from {data['sender_company']} regarding our {product} "
            f"and the possibility of supporting {company}."
        )
        if market:
            base += f" We understand your team is active in the {market} market."
        if summary:
            base += " Based on the profile information provided, your business appears relevant to this offer."
        if opening_signal:
            base += (
                f" I also noticed a public signal around {opening_signal}, "
                "so I wanted to keep this note specific rather than send a generic introduction."
            )
        return base
    previous_touch = customer_visible_previous_touch(data)
    base = (
        f"I wanted to follow up regarding our earlier note about {product} "
        f"and see whether it may be relevant for {company}."
    )
    if previous_touch:
        base += f" In my last message, I shared {previous_touch}."
    return base


def build_goal_line(data: dict) -> str:
    goal = data["goal"].strip().rstrip(".")
    unauthorized_sample_goal = _contains_sample_term(goal) and not has_authorized_sample_support(data)
    if data["email_type"] == "first_touch":
        if unauthorized_sample_goal:
            return "Our purpose is simple: to review the relevant product details and specifications."
        return ensure_sentence(f"Our purpose is simple: {goal}")
    if unauthorized_sample_goal:
        return (
            "I wanted to check in specifically about our earlier introduction and ask whether reviewing "
            "the next product details and specifications would be useful."
        )
    lowered = goal.lower()
    if lowered.startswith("follow up on"):
        return f"I wanted to check in specifically about {goal[len('follow up on '):]}."
    if lowered.startswith("follow up"):
        return f"I wanted to check in specifically about {goal[len('follow up '):]}."
    return f"I am following up to {goal}."


def extract_previous_touch(previous_contact_context: str) -> str:
    text = previous_contact_context.strip().rstrip(".")
    if not text:
        return ""
    lowered = text.lower()
    replacements = [
        ("we shared ", ""),
        ("we sent ", ""),
        ("we introduced ", ""),
        ("we mentioned ", ""),
        ("we provided ", ""),
    ]
    for prefix, replacement in replacements:
        if lowered.startswith(prefix):
            return replacement + text[len(prefix):]
    first_clause = re.split(r"[.;]", text, maxsplit=1)[0].strip()
    return first_clause


def customer_visible_previous_touch(data: dict) -> str:
    previous_touch = extract_previous_touch(data["previous_contact_context"])
    if _contains_sample_term(previous_touch) and not has_authorized_sample_support(data):
        return "our earlier product details"
    return previous_touch


def build_support_line(data: dict) -> str:
    tone = data["tone"].lower()
    softener = "If useful" if "warm" in tone or "helpful" in tone else "If appropriate"
    if data["email_type"] == "first_touch":
        if is_industrial_evidence_angle(data):
            return (
                f"{softener}, I can send a one-page selection checklist covering the application, "
                "specifications, interfaces, operating conditions, and qualification requirements."
            )
        return (
            f"{softener}, I can share a brief product overview, standard specifications, "
            "and a starting point for discussion."
        )
    if has_authorized_sample_support(data):
        return (
            f"{softener}, I can resend the key product details and prepare sample information "
            "for your review."
        )
    return f"{softener}, I can resend the key product details and specifications for your review."


def build_cta(data: dict) -> str:
    if data["email_type"] == "first_touch":
        if is_industrial_evidence_angle(data):
            return "Would it be useful to start with the requirements for one relevant application?"
        return "Please let me know if you would be open to a short exchange on this."
    if has_authorized_sample_support(data):
        return "Please let me know whether it would be helpful for me to send the next details or samples."
    return "Please let me know whether it would be helpful for me to send the next product details and specifications."


def build_signature(data: dict) -> str:
    if data["signature"]:
        return data["signature"]
    sender = data["sender_name"] or "Your Name"
    company = data["sender_company"] or "Your Company"
    return f"Best regards,\n{sender}\n{company}"


def build_drafts(data: dict) -> dict:
    opening = build_opening(data)
    context_line = build_context_line(data)
    goal_line = build_goal_line(data)
    support_line = build_support_line(data)
    cta = build_cta(data)
    signature = build_signature(data)
    previous_touch = customer_visible_previous_touch(data)
    evidence_angle = build_customer_visible_angle_line(data)

    version_a = "\n\n".join(
        [opening, context_line, evidence_angle or goal_line, support_line, cta, signature]
    )
    if data["email_type"] == "follow_up":
        follow_up_line = f"I am following up on {data['product_or_offer']}."
        if previous_touch:
            follow_up_line += f" Last time, I shared {previous_touch}."
        version_b = "\n\n".join(
            [
                opening,
                follow_up_line,
                "If this is still relevant for your team, I would be glad to send the next details.",
                cta,
                signature,
            ]
        )
    else:
        if evidence_angle:
            focused_context = (
                f"I came across {data['company_name']}'s public industrial portfolio and wanted to ask one focused technical question."
                if is_industrial_evidence_angle(data)
                else f"I reviewed {data['company_name']}'s public business profile and wanted to ask one focused question."
            )
            version_b = "\n\n".join(
                [
                    opening,
                    focused_context,
                    evidence_angle,
                    support_line,
                    cta,
                    signature,
                ]
            )
        else:
            version_b = "\n\n".join(
                [
                    opening,
                    ensure_sentence(
                        f"I am contacting you about {data['product_or_offer']} and would like to "
                        + (
                            "review the relevant product details and specifications"
                            if _contains_sample_term(data["goal"])
                            and not has_authorized_sample_support(data)
                            else data["goal"].rstrip(".")
                        )
                    ),
                    "If this is relevant for your team, I would be glad to share the next details.",
                    cta,
                    signature,
                ]
            )
    return {"version_a": version_a, "version_b": version_b}


def build_review_notes(data: dict) -> list[str]:
    notes = ["建议人工复核后发送，不要把未确认信息直接写成既定事实。"]
    if data["customer_profile_summary"]:
        notes.append("邮件中涉及客户画像摘要的信息时，应核对其是否来自已确认的公开资料。")
    if data["previous_contact_context"]:
        notes.append("跟进内容引用了历史沟通背景，请确认时间点、附件和表达与实际一致。")
    if any(token in data["goal"].lower() for token in ("price", "quotation", "offer", "sample", "moq", "delivery")):
        notes.append("若涉及价格、样品、MOQ 或交期，请仅填写已内部确认的信息。")
    if data["constraints"]:
        notes.append(f"已应用输入约束：{data['constraints']}")
    source_context = data.get("source_context") or {}
    if source_context.get("evidence_sufficiency") in {"limited", "thin"}:
        notes.append("背调阶段证据仍有限，本草稿只适合作为复核底稿，不适合直接发送。")
    if source_context.get("intel_recommended_next_action") == "hold_for_manual_review":
        notes.append("上游背调尚未建议进入开发信，请先完成人工复核。")
    if source_context.get("sieger_status") == "needs_manual_review":
        notes.append("SIEGER Verdict Card 尚未通过人工复核，请先确认主体、采购角色和关键证据。")
    if source_context.get("recent_signals") or source_context.get("market_signals"):
        notes.append("本邮件引用了背调阶段的近期或市场信号，请确认来源、时间、新鲜度和语境后再发送。")
    if source_context.get("recommended_opening_signal_en"):
        notes.append("开头切入点来自客户背调输出，开发信 Skill 不负责重新验证该事实。")
    return notes


def build_input_signals(data: dict) -> list[str]:
    signals = [
        f"email_type: {data['email_type']}",
        f"customer_name: {data['customer_name']}",
        f"company_name: {data['company_name']}",
        f"product_or_offer: {data['product_or_offer']}",
        f"goal: {data['goal']}",
    ]
    for key in (
        "country_or_market",
        "customer_profile_summary",
        "previous_contact_context",
        "tone",
        "sender_name",
        "sender_company",
        "constraints",
    ):
        if data[key]:
            signals.append(f"{key}: {data[key]}")
    return signals


def build_evidence_signals(data: dict) -> list[str]:
    source_context = data.get("source_context") or {}
    signals = []
    if source_context.get("recommended_sales_angle_en"):
        signals.append(f"sales_angle: {source_context['recommended_sales_angle_en']}")
    if source_context.get("recommended_opening_signal_en"):
        signals.append(f"opening_signal: {source_context['recommended_opening_signal_en']}")
    if source_context.get("risk_rating"):
        signals.append(f"risk_rating: {source_context['risk_rating']}")
    if source_context.get("entity_confidence"):
        signals.append(f"entity_confidence: {source_context['entity_confidence']}")
    if source_context.get("evidence_sufficiency"):
        signals.append(f"evidence_sufficiency: {source_context['evidence_sufficiency']}")
    selected_angle = source_context.get("selected_sales_angle") or {}
    if selected_angle.get("angle_id"):
        signals.append(f"approved_angle_id: {selected_angle['angle_id']}")
    for item in source_context.get("selected_evidence") or []:
        if isinstance(item, dict):
            parts = [str(item.get(key) or "").strip() for key in ("evidence_id", "title", "url")]
            signals.append("evidence: " + " | ".join(part for part in parts if part))
    for title in source_context.get("evidence_titles") or []:
        signals.append(f"evidence_title: {title}")
    for signal in source_context.get("recent_signals") or []:
        signals.append(f"recent_signal: {signal}")
    for signal in source_context.get("market_signals") or []:
        signals.append(f"market_signal: {signal}")
    return signals


def build_unconfirmed_fact_checklist(data: dict) -> list[str]:
    source_context = data.get("source_context") or {}
    checklist = list(source_context.get("unconfirmed_fact_list") or [])
    checklist.extend(source_context.get("ambiguity_notes") or [])
    if source_context.get("recent_signals"):
        checklist.append("确认近期客户信号仍然有效，没有过时或被断章取义。")
    if source_context.get("market_signals"):
        checklist.append("确认市场、合规、关税或贸易政策信号只作为业务背景，不写成法律或确定采购结论。")
    if not checklist:
        checklist.append("确认客户画像摘要、销售切入点和任何具体需求判断都来自公开且已核实的信息。")
    return list(dict.fromkeys(checklist))


def build_workflow_guidance(data: dict) -> dict:
    source_context = data.get("source_context") or {}
    intel_action = source_context.get("intel_recommended_next_action")
    authorized = source_context.get("draft_authorization") in {None, "", "approved"}
    next_action = (
        "ready_for_manual_send"
        if intel_action in {None, "", "ready_for_email_draft"} and authorized
        else "hold_for_manual_review"
    )
    return {
        "recommended_next_action": next_action,
        "send_policy": "manual_review_only",
    }


def render_markdown(
    data: dict,
    subjects: list[str],
    drafts: dict,
    notes: list[str],
    signals: list[str],
    evidence_signals: list[str],
    unconfirmed_fact_checklist: list[str],
    workflow_guidance: dict,
) -> str:
    lines = [
        "# Review-First Outreach Draft Package",
        "",
        "## Scenario",
        f"- Email Type: {scenario_label(data['email_type'])}",
        f"- Goal: {data['goal']}",
        f"- Send Policy: {workflow_guidance['send_policy']}",
        f"- Recommended Next Action: {workflow_guidance['recommended_next_action']}",
        "",
        "## Subject Options",
        f"1. {subjects[0]}",
        f"2. {subjects[1]}",
        "",
        "## Draft Version A",
        drafts["version_a"],
        "",
        "## Draft Version B",
        drafts["version_b"],
        "",
        "## Review Notes",
    ]
    lines.extend([f"- {note}" for note in notes])
    lines.extend(["", "## Evidence Signals Used"])
    lines.extend([f"- {signal}" for signal in evidence_signals])
    lines.extend(["", "## Unconfirmed Facts"])
    lines.extend([f"- {item}" for item in unconfirmed_fact_checklist])
    lines.extend(["", "## Input Signals Used"])
    lines.extend([f"- {signal}" for signal in signals])
    return "\n".join(lines) + "\n"


def maybe_write(path_arg: str | None, content: str) -> None:
    if path_arg:
        path = Path(path_arg)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a conservative foreign-trade email draft package.")
    parser.add_argument("--input-json", help="Path to the input JSON file.")
    parser.add_argument("--markdown-out", help="Path to write the Markdown output.")
    parser.add_argument("--json-out", help="Path to write the JSON output.")
    parser.add_argument(
        "--schema-path",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to the JSON schema used for input validation.",
    )
    args = parser.parse_args()

    raw = load_input(args.input_json)
    schema = load_schema(Path(args.schema_path))
    data = normalize(raw)
    validate(data, raw, schema)

    subjects = build_subjects(data)
    drafts = build_drafts(data)
    notes = build_review_notes(data)
    signals = build_input_signals(data)
    evidence_signals = build_evidence_signals(data)
    unconfirmed_fact_checklist = build_unconfirmed_fact_checklist(data)
    workflow_guidance = build_workflow_guidance(data)

    markdown = render_markdown(
        data,
        subjects,
        drafts,
        notes,
        signals,
        evidence_signals,
        unconfirmed_fact_checklist,
        workflow_guidance,
    )
    payload = {
        "scenario": {
            "email_type": data["email_type"],
            "goal": data["goal"],
            "customer_name": data["customer_name"],
            "company_name": data["company_name"],
            "product_or_offer": data["product_or_offer"],
        },
        "subject_options": subjects,
        "drafts": drafts,
        "review_notes": notes,
        "evidence_signals_used": evidence_signals,
        "unconfirmed_fact_checklist": unconfirmed_fact_checklist,
        "send_policy": workflow_guidance["send_policy"],
        "workflow_guidance": workflow_guidance,
        "input_signals_used": signals,
        "source_context": {
            "draft_authorization": (data.get("source_context") or {}).get("draft_authorization"),
            "approved_angle_id": ((data.get("source_context") or {}).get("selected_sales_angle") or {}).get("angle_id"),
            "selected_sales_angle": (data.get("source_context") or {}).get("selected_sales_angle") or {},
            "selected_claims": (data.get("source_context") or {}).get("selected_claims") or [],
            "selected_evidence": (data.get("source_context") or {}).get("selected_evidence") or [],
        },
    }

    if args.markdown_out:
        maybe_write(args.markdown_out, markdown)
    if args.json_out:
        maybe_write(args.json_out, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
