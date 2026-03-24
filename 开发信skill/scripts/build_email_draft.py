#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path


ALLOWED_EMAIL_TYPES = {"first_touch", "follow_up"}
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_SCHEMA_PATH = SKILL_ROOT / "schemas" / "email-draft-input.schema.json"


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
    }
    for key in fields:
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


def scenario_label(email_type: str) -> str:
    return "First Touch" if email_type == "first_touch" else "Follow Up"


def build_subjects(data: dict) -> list[str]:
    company = data["company_name"]
    product = data["product_or_offer"]
    company_possessive = f"{company}'" if company.endswith("s") else f"{company}'s"
    if data["email_type"] == "first_touch":
        return [
            f"{product.title()} Supply for {company}",
            f"Possible Support for {company_possessive} {product.title()} Needs",
        ]
    return [
        f"Following Up on {product.title()} for {company}",
        f"Checking Whether {product.title()} Samples Would Help",
    ]


def build_opening(data: dict) -> str:
    customer = data["customer_name"]
    if data["email_type"] == "first_touch":
        return f"Dear {customer},\n\nI hope you are doing well."
    return f"Dear {customer},\n\nI hope you have been well since my last email."


def build_context_line(data: dict) -> str:
    company = data["company_name"]
    product = data["product_or_offer"]
    market = data["country_or_market"]
    summary = data["customer_profile_summary"]
    if data["email_type"] == "first_touch":
        base = (
            f"I am reaching out from {data['sender_company']} regarding our {product} "
            f"and the possibility of supporting {company}."
        )
        if market:
            base += f" We understand your team is active in the {market} market."
        if summary:
            base += " Based on the profile information provided, your business appears relevant to this offer."
        return base
    previous_touch = extract_previous_touch(data["previous_contact_context"])
    base = (
        f"I wanted to follow up regarding our earlier note about {product} "
        f"and see whether it may be relevant for {company}."
    )
    if previous_touch:
        base += f" In my last message, I shared {previous_touch}."
    return base


def build_goal_line(data: dict) -> str:
    goal = data["goal"].rstrip(".")
    if data["email_type"] == "first_touch":
        return f"Our purpose is simple: {goal}."
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


def build_support_line(data: dict) -> str:
    tone = data["tone"].lower()
    softener = "If useful" if "warm" in tone or "helpful" in tone else "If appropriate"
    if data["email_type"] == "first_touch":
        return (
            f"{softener}, I can share a brief product overview, standard specifications, "
            "and a starting point for discussion."
        )
    return (
        f"{softener}, I can resend the key product details and prepare sample information "
        "for your review."
    )


def build_cta(data: dict) -> str:
    if data["email_type"] == "first_touch":
        return "Please let me know if you would be open to a short exchange on this."
    return "Please let me know whether it would be helpful for me to send the next details or samples."


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
    previous_touch = extract_previous_touch(data["previous_contact_context"])

    version_a = "\n\n".join([opening, context_line, goal_line, support_line, cta, signature])
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
        version_b = "\n\n".join(
            [
                opening,
                f"I am contacting you about {data['product_or_offer']} and would like to {data['goal'].rstrip('.')}.",
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


def render_markdown(data: dict, subjects: list[str], drafts: dict, notes: list[str], signals: list[str]) -> str:
    lines = [
        "# Email Draft Package",
        "",
        "## Scenario",
        f"- Email Type: {scenario_label(data['email_type'])}",
        f"- Goal: {data['goal']}",
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
    lines.extend(["", "## Input Signals Used"])
    lines.extend([f"- {signal}" for signal in signals])
    return "\n".join(lines) + "\n"


def maybe_write(path_arg: str | None, content: str) -> None:
    if path_arg:
        Path(path_arg).write_text(content, encoding="utf-8")


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

    markdown = render_markdown(data, subjects, drafts, notes, signals)
    payload = {
        "scenario": {
            "email_type": data["email_type"],
            "goal": data["goal"],
        },
        "subject_options": subjects,
        "drafts": drafts,
        "review_notes": notes,
        "input_signals_used": signals,
    }

    if args.markdown_out:
        maybe_write(args.markdown_out, markdown)
    if args.json_out:
        maybe_write(args.json_out, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
