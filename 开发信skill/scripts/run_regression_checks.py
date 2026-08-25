#!/usr/bin/env python3
import json
import importlib.util
import subprocess
import sys
from copy import deepcopy
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
BUILD_SCRIPT = SCRIPT_DIR / "build_email_draft.py"
SCHEMA_PATH = SKILL_ROOT / "schemas" / "email-draft-input.schema.json"
BRIDGE_SCRIPT = SCRIPT_DIR / "build_email_input_from_customer_intel.py"
OPENCLAW_SCRIPT = SKILL_ROOT / "for-openclaw" / "scripts" / "build_email_draft_from_openclaw.py"
OPENCLAW_SAMPLE = SKILL_ROOT / "for-openclaw" / "examples" / "sample-input.json"
CUSTOMER_INTEL_FIXTURE = SKILL_ROOT / "examples" / "customer-intel-report.json"

CASES = [
    {
        "label": "first-touch",
        "input_path": SKILL_ROOT / "examples" / "first-touch.json",
        "must_include": [
            "Email Type: First Touch",
            "Send Policy: manual_review_only",
            "Our purpose is simple:",
            "Please let me know if you would be open to a short exchange on this.",
            "邮件中涉及客户画像摘要的信息时，应核对其是否来自已确认的公开资料。",
        ],
    },
    {
        "label": "follow-up",
        "input_path": SKILL_ROOT / "examples" / "follow-up.json",
        "must_include": [
            "Email Type: Follow Up",
            "I wanted to check in specifically about our earlier introduction",
            "跟进内容引用了历史沟通背景，请确认时间点、附件和表达与实际一致。",
            "## Unconfirmed Facts",
            "Please let me know whether it would be helpful for me to send the next product details and specifications.",
        ],
    },
    {
        "label": "solar-first-touch",
        "input_path": SKILL_ROOT / "examples" / "solar-first-touch.json",
        "must_include": [
            "Residential Hybrid Inverter Systems Supply for SunGrid Solutions",
            "We understand your team is active in the Chile market.",
            "Shenzhen PowerNest Energy",
        ],
    },
    {
        "label": "textile-follow-up",
        "input_path": SKILL_ROOT / "examples" / "textile-follow-up.json",
        "must_include": [
            "Checking Whether Washed Linen Table Textile Collections Details Would Help",
            "I wanted to check in specifically about our catalog sharing",
            "Keep the follow-up soft and design-oriented.",
        ],
    },
]


def run_case(case: dict) -> tuple[bool, str]:
    label = case["label"]
    input_path = case["input_path"]
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--input-json",
            str(input_path),
            "--schema-path",
            str(SCHEMA_PATH),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, f"{label}: failed with {proc.stderr.strip() or proc.stdout.strip()}"

    output = proc.stdout
    checks = [
        "# Review-First Outreach Draft Package",
        "## Subject Options",
        "## Draft Version A",
        "## Review Notes",
        "## Evidence Signals Used",
        "## Unconfirmed Facts",
        "## Input Signals Used",
    ]
    missing = [item for item in checks if item not in output]
    if missing:
        return False, f"{label}: missing expected sections: {', '.join(missing)}"
    missing_phrases = [item for item in case.get("must_include", []) if item not in output]
    if missing_phrases:
        return False, f"{label}: missing expected phrases: {', '.join(missing_phrases)}"
    return True, f"{label}: ok"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_customer_intel_gate_case() -> tuple[bool, str]:
    bridge = load_module("email_bridge_gate_test", BRIDGE_SCRIPT)
    core = load_module("email_core_gate_test", BUILD_SCRIPT)
    report = json.loads(CUSTOMER_INTEL_FIXTURE.read_text(encoding="utf-8"))
    approved_payload = bridge.build_bridge_payload(
        report,
        "first_touch",
        "frozen mixed vegetables",
        "Leo",
        "Ningbo FreshGrow Foods",
    )
    if (approved_payload.get("source_context") or {}).get("draft_authorization") != "approved":
        return False, "customer-intel-gate: approved fixture did not receive draft authorization"
    schema = core.load_schema(SCHEMA_PATH)
    normalized = core.normalize(approved_payload)
    core.validate(normalized, approved_payload, schema)
    if (approved_payload.get("source_context") or {}).get("industry_lens") != "food":
        return False, "customer-intel-gate: industry lens was not preserved into email input"
    if (approved_payload.get("source_context") or {}).get("seller_context") != report.get("seller_context"):
        return False, "customer-intel-gate: authorized seller context was not preserved into email input"
    drafts = core.build_drafts(normalized)
    generated = " ".join([approved_payload["goal"], *drafts.values()]).lower()
    forbidden_industrial_terms = ("technical fit", "module", "motor", "drive", "bom", "automation")
    industry_lens = str((approved_payload.get("source_context") or {}).get("industry_lens") or "general").strip().lower()
    leaked = (
        [term for term in forbidden_industrial_terms if term in generated]
        if industry_lens != "industrial"
        else []
    )
    if leaked:
        return False, f"customer-intel-gate: {industry_lens} goal/drafts leaked industrial copy: {', '.join(leaked)}"
    raw_angle = str(((approved_payload.get("source_context") or {}).get("selected_sales_angle") or {}).get("en") or "")
    if raw_angle and raw_angle.lower() in generated:
        return False, "customer-intel-gate: internal sales-angle instruction leaked into customer-visible copy"
    if "open by referencing" in generated or "connect the note" in generated:
        return False, "customer-intel-gate: drafting instruction leaked into customer-visible copy"
    if "product and sourcing fit" not in approved_payload["goal"].lower():
        return False, "customer-intel-gate: food goal did not use product/sourcing fit wording"

    generic_industrial_report = deepcopy(report)
    generic_industrial_report["industry_lens"] = "industrial"
    generic_industrial_payload = bridge.build_bridge_payload(
        generic_industrial_report,
        "first_touch",
        "industrial sensors",
        "Leo",
        "Ningbo Sensor Works",
    )
    generic_industrial_normalized = core.normalize(generic_industrial_payload)
    core.validate(generic_industrial_normalized, generic_industrial_payload, schema)
    generic_industrial_copy = " ".join(
        [*core.build_subjects(generic_industrial_normalized), *core.build_drafts(generic_industrial_normalized).values()]
    ).lower()
    unsupported_specifics = (
        "automation module",
        "bom-level",
        "material-handling",
        "motor or drive",
        "voltage",
        "torque",
    )
    leaked_specifics = [term for term in unsupported_specifics if term in generic_industrial_copy]
    if leaked_specifics:
        return False, "customer-intel-gate: generic industrial draft asserted unsupported specifics: " + ", ".join(leaked_specifics)

    for label, mutate in (
        (
            "dangling-claim",
            lambda item: item["sales_angles"][0].update({"claim_ids": ["CL-MISSING"]}),
        ),
        (
            "claim-evidence-mismatch",
            lambda item: item["claim_ledger"][0].update({"evidence_ids": ["EV-MISSING"]}),
        ),
        (
            "generic-source-without-identity",
            lambda item: item["evidence_ledger"][0].update(
                {"url": "", "title": "", "source_id": "", "source_name": "", "source_title": "", "source_type": "web"}
            ),
        ),
    ):
        invalid_report = deepcopy(report)
        mutate(invalid_report)
        invalid_payload = bridge.build_bridge_payload(
            invalid_report,
            "first_touch",
            "frozen mixed vegetables",
            "Leo",
            "Ningbo FreshGrow Foods",
        )
        invalid_context = invalid_payload.get("source_context") or {}
        if invalid_context.get("draft_authorization") != "hold":
            return False, f"customer-intel-gate: {label} references were incorrectly authorized"
        if not invalid_context.get("authorization_reasons"):
            return False, f"customer-intel-gate: {label} hold did not expose a reason"

    incomplete_gates_report = deepcopy(report)
    incomplete_gates_report["intel_decision"]["decision_gates"] = {
        "risk": {"status": "pass", "reason": "Only one gate was supplied."}
    }
    incomplete_gates_payload = bridge.build_bridge_payload(
        incomplete_gates_report,
        "first_touch",
        "frozen mixed vegetables",
        "Leo",
        "Ningbo FreshGrow Foods",
    )
    if (incomplete_gates_payload.get("source_context") or {}).get("draft_authorization") != "hold":
        return False, "customer-intel-gate: incomplete decision gates were incorrectly authorized"

    unrelated_signal_report = deepcopy(report)
    unrelated_signal_report["recent_signals"] = [
        {
            "title": "Competitor opened a new factory",
            "source_url": "https://unrelated-competitor.example/news",
            "confidence": "high",
            "signal_type": "expansion",
        }
    ]
    unrelated_signal_payload = bridge.build_bridge_payload(
        unrelated_signal_report,
        "first_touch",
        "frozen mixed vegetables",
        "Leo",
        "Ningbo FreshGrow Foods",
    )
    unrelated_signal_context = unrelated_signal_payload.get("source_context") or {}
    if unrelated_signal_context.get("recommended_opening_signal_en"):
        return False, "customer-intel-gate: unbound signal entered the recommended opening"
    unrelated_signal_copy = " ".join(
        core.build_drafts(core.normalize(unrelated_signal_payload)).values()
    ).lower()
    if "competitor opened a new factory" in unrelated_signal_copy:
        return False, "customer-intel-gate: unbound signal entered customer-visible email copy"

    linked_signal_report = deepcopy(report)
    linked_signal_report["recent_signals"] = [
        {
            "title": "GreenHarvest Foods public profile update",
            "source_url": "https://greenharvestfoods.com/contact",
            "evidence_ids": ["EV-001"],
            "confidence": "medium",
            "signal_type": "profile_update",
        }
    ]
    linked_signal_payload = bridge.build_bridge_payload(
        linked_signal_report,
        "first_touch",
        "frozen mixed vegetables",
        "Leo",
        "Ningbo FreshGrow Foods",
    )
    if (linked_signal_payload.get("source_context") or {}).get("recommended_opening_signal_en") != "GreenHarvest Foods public profile update":
        return False, "customer-intel-gate: evidence-linked signal was not preserved"

    blocked_report = deepcopy(report)
    for angle in blocked_report.get("sales_angles") or []:
        angle["approval_status"] = "proposed"
    blocked_payload = bridge.build_bridge_payload(
        blocked_report,
        "first_touch",
        "frozen mixed vegetables",
        "Leo",
        "Ningbo FreshGrow Foods",
    )
    try:
        core.validate(core.normalize(blocked_payload), blocked_payload, schema)
    except SystemExit as exc:
        if "Draft blocked" not in str(exc):
            return False, f"customer-intel-gate: unexpected block reason: {exc}"
    else:
        return False, "customer-intel-gate: unapproved angle incorrectly generated a draft"
    return True, "customer-intel-gate: ok"


def run_follow_up_sample_authorization_case() -> tuple[bool, str]:
    core = load_module("email_sample_authorization_test", BUILD_SCRIPT)
    schema = core.load_schema(SCHEMA_PATH)
    base_payload = {
        "email_type": "follow_up",
        "customer_name": "Mia",
        "company_name": "Specification Review Buyer",
        "product_or_offer": "industrial sensors",
        "goal": "follow up on our earlier introduction and ask whether samples would be useful",
        "country_or_market": "Germany",
        "customer_profile_summary": "Industrial distributor reviewing component options.",
        "previous_contact_context": "We shared our product overview last week.",
        "tone": "professional,helpful",
        "sender_name": "Leo",
        "sender_company": "Authorized Sensor Seller",
        "signature": "Best regards,\nLeo\nAuthorized Sensor Seller",
        "source_context": {
            "draft_authorization": "approved",
            "selected_sales_angle": {
                "approval_status": "approved",
                "en": "Open by referencing the public application clue, then connect the note to a specification review.",
            },
            "seller_context": {
                "value_propositions": ["stable specifications"],
                "proof_points": ["Seller proof does not mention samples."],
                "authorized_materials": ["authorized:specification-sheet"],
            },
        },
    }

    sample_terms = ("sample", "samples", "样品", "打样", "寄样")
    negative_seller_texts = (
        ("cannot-dispatch", "We cannot dispatch samples."),
        ("no-samples", "No samples are available."),
        ("samples-unavailable", "Samples are unavailable."),
        ("samples-cannot-dispatch", "We can provide samples, but samples cannot be dispatched to Germany."),
        ("samples-arent-available", "Samples aren't available for Germany."),
        ("samples-curly-arent-available", "Samples aren’t available for Germany."),
        ("samples-wont-ship", "Samples won't ship to Germany."),
        ("wont-ship-samples", "We won't ship samples to Germany."),
        ("curly-wont-ship-samples", "We won’t ship samples to Germany."),
        ("arent-able-to-ship-samples", "We aren’t able to ship samples to Germany."),
        (
            "long-distance-pronoun-negation",
            "We can provide samples, but after checking the destination-specific logistics and current compliance constraints, they cannot be dispatched to Germany.",
        ),
        ("policy-prohibits", "Our sample policy prohibits dispatch."),
        ("mixed-positive-negative", "We can provide samples, but samples are unavailable in this market."),
        ("chinese-not-provide", "不提供样品。"),
        ("chinese-cannot-provide", "无法提供样品。"),
        ("chinese-policy-prohibits", "样品政策禁止寄样。"),
        ("chinese-unavailable", "样品不可用。"),
        ("generic-policy", "Our sample policy."),
        ("generic-sheet", "Our sample sheet."),
    )
    for label, seller_text in negative_seller_texts:
        negative_payload = deepcopy(base_payload)
        negative_payload["source_context"]["seller_context"] = {"capabilities": [seller_text]}
        normalized = core.normalize(negative_payload)
        core.validate(normalized, negative_payload, schema)
        if core.has_authorized_sample_support(normalized):
            return False, f"follow-up-samples: {label} incorrectly authorized sample promises"

    forbidden_payload = deepcopy(base_payload)
    forbidden_payload["source_context"]["seller_context"] = {
        "value_propositions": ["We can provide samples for qualified buyers."],
        "forbidden_claims": ["Do not send samples to Germany."],
    }
    forbidden = core.normalize(forbidden_payload)
    core.validate(forbidden, forbidden_payload, schema)
    if core.has_authorized_sample_support(forbidden):
        return False, "follow-up-samples: forbidden_claims did not override positive sample language"
    forbidden_copy = " ".join(
        [*core.build_subjects(forbidden), *core.build_drafts(forbidden).values()]
    ).lower()
    if any(term in forbidden_copy for term in sample_terms):
        return False, "follow-up-samples: forbidden sample promise leaked into customer-visible copy"

    cross_field_payload = deepcopy(base_payload)
    cross_field_payload["source_context"]["seller_context"] = {
        "capabilities": ["We can provide samples."],
        "sample_availability": "They aren’t available in Germany.",
    }
    cross_field = core.normalize(cross_field_payload)
    core.validate(cross_field, cross_field_payload, schema)
    if core.has_authorized_sample_support(cross_field):
        return False, "follow-up-samples: negative sample_availability did not override capability text"

    split_field_cases = (
        {
            "capabilities": ["We can provide samples.", "They cannot be dispatched to Germany."],
        },
        {
            "capabilities": ["We can provide samples."],
            "proof_points": ["They won’t be dispatched to Germany."],
        },
    )
    for index, seller_context in enumerate(split_field_cases, start=1):
        split_payload = deepcopy(base_payload)
        split_payload["source_context"]["seller_context"] = seller_context
        split_data = core.normalize(split_payload)
        core.validate(split_data, split_payload, schema)
        if core.has_authorized_sample_support(split_data):
            return False, f"follow-up-samples: split seller context case {index} bypassed negation"

    top_level_split_payload = deepcopy(base_payload)
    top_level_split_payload["source_context"].pop("seller_context", None)
    top_level_split_payload["source_context"]["seller_capabilities"] = ["We can provide samples."]
    top_level_split_payload["source_context"]["seller_proof_points"] = [
        "They cannot be dispatched to Germany."
    ]
    top_level_split = core.normalize(top_level_split_payload)
    core.validate(top_level_split, top_level_split_payload, schema)
    if core.has_authorized_sample_support(top_level_split):
        return False, "follow-up-samples: split top-level seller fields bypassed negation"

    for email_type, goal, previous_contact_context in (
        (
            "first_touch",
            "introduce our products and offer to send samples",
            "",
        ),
        (
            "follow_up",
            "follow up on our earlier introduction and ask whether samples would be useful",
            "We shared a sample sheet last week.",
        ),
    ):
        scrub_payload = deepcopy(base_payload)
        scrub_payload["email_type"] = email_type
        scrub_payload["goal"] = goal
        scrub_payload["previous_contact_context"] = previous_contact_context
        if email_type == "first_touch":
            scrub_payload["source_context"]["selected_sales_angle"] = {}
        normalized = core.normalize(scrub_payload)
        core.validate(normalized, scrub_payload, schema)
        copy = " ".join([*core.build_subjects(normalized), *core.build_drafts(normalized).values()]).lower()
        if any(term in copy for term in sample_terms):
            return False, f"follow-up-samples: unauthorized {email_type} copy leaked sample language"
        if "details" not in copy or "specifications" not in copy:
            return False, f"follow-up-samples: unauthorized {email_type} copy did not default to details/specifications"

    isolated_payload = deepcopy(base_payload)
    isolated_payload["source_context"]["selected_sales_angle"]["authorized_materials"] = [
        "Samples are available."
    ]
    isolated = core.normalize(isolated_payload)
    if core.has_authorized_sample_support(isolated):
        return False, "follow-up-samples: non-seller angle material incorrectly authorized samples"

    for label, seller_text in (
        ("capability", "We can dispatch evaluation samples for qualified review."),
        ("availability", "Samples are available for qualified review."),
        ("chinese-capability", "我司可提供评估样品。"),
    ):
        authorized_payload = deepcopy(base_payload)
        authorized_payload["source_context"]["seller_context"] = {"capabilities": [seller_text]}
        authorized = core.normalize(authorized_payload)
        core.validate(authorized, authorized_payload, schema)
        if not core.has_authorized_sample_support(authorized):
            return False, f"follow-up-samples: clear seller {label} language was not authorized"
        authorized_subjects = core.build_subjects(authorized)
        authorized_drafts = core.build_drafts(authorized)
        authorized_copy = " ".join([*authorized_subjects, *authorized_drafts.values()]).lower()
        if "samples" not in authorized_subjects[1].lower():
            return False, f"follow-up-samples: authorized seller {label} did not enable sample subject"
        if "sample information" not in authorized_copy or "or samples" not in authorized_copy:
            return False, f"follow-up-samples: authorized seller {label} did not enable sample body/CTA"

    unauthorized = core.normalize(base_payload)
    core.validate(unauthorized, base_payload, schema)
    unauthorized_copy = " ".join(
        [*core.build_subjects(unauthorized), *core.build_drafts(unauthorized).values()]
    ).lower()
    raw_angle = base_payload["source_context"]["selected_sales_angle"]["en"].lower()
    if raw_angle in unauthorized_copy or "open by referencing" in unauthorized_copy:
        return False, "follow-up-samples: internal angle drafting instruction leaked into customer-visible copy"
    return True, "follow-up-samples: ok"


def run_openclaw_gate_case() -> tuple[bool, str]:
    wrapper = load_module("email_openclaw_gate_test", OPENCLAW_SCRIPT)
    core = load_module("email_openclaw_core_gate_test", BUILD_SCRIPT)
    payload = json.loads(OPENCLAW_SAMPLE.read_text(encoding="utf-8"))
    merged = wrapper.merge_payload(payload)
    schema = core.load_schema(SCHEMA_PATH)
    core.validate(core.normalize(merged), merged, schema)

    blocked_payload = deepcopy(payload)
    blocked_payload["public_context"]["draft_authorization"] = "hold"
    blocked_payload["public_context"]["authorization_reasons"] = ["sales angle not approved"]
    blocked = wrapper.merge_payload(blocked_payload)
    try:
        core.validate(core.normalize(blocked), blocked, schema)
    except SystemExit as exc:
        if "sales angle not approved" not in str(exc):
            return False, f"openclaw-gate: unexpected block reason: {exc}"
    else:
        return False, "openclaw-gate: hold authorization incorrectly generated a draft"

    adversarial_payload = deepcopy(payload)
    adversarial_context = adversarial_payload["public_context"]
    adversarial_context.update(
        {
            "draft_authorization": "approved",
            "risk_rating": "High",
            "intel_recommended_next_action": "hold_for_manual_review",
            "manual_review_required": True,
            "sieger_status": "needs_manual_review",
            "entity_confidence": "low",
            "evidence_sufficiency": "thin",
            "decision_gates": {
                "identity": {"status": "hold"},
                "evidence": {"status": "hold"},
                "seller_offer": {"status": "pass"},
                "product_fit": {"status": "hold"},
                "risk": {"status": "hold"},
            },
            "selected_sales_angle": {},
            "selected_claims": [],
            "selected_evidence": [],
        }
    )
    adversarial = wrapper.merge_payload(adversarial_payload)
    adversarial_context = adversarial.get("source_context") or {}
    if adversarial_context.get("draft_authorization") != "hold":
        return False, "openclaw-gate: blocking upstream states were self-authorized"
    adversarial_reasons = " ".join(adversarial_context.get("authorization_reasons") or []).lower()
    for expected in ("risk rating is high", "requires manual review", "not explicitly approved"):
        if expected not in adversarial_reasons:
            return False, f"openclaw-gate: missing derived block reason: {expected}"
    try:
        core.validate(core.normalize(adversarial), adversarial, schema)
    except SystemExit:
        pass
    else:
        return False, "openclaw-gate: adversarial upstream context generated a draft"

    single_flag_payload = {
        "operator_input": deepcopy(payload["operator_input"]),
        "public_context": {"draft_authorization": "approved"},
    }
    single_flag = wrapper.merge_payload(single_flag_payload)
    if (single_flag.get("source_context") or {}).get("draft_authorization") != "hold":
        return False, "openclaw-gate: a caller-supplied approval flag bypassed report validation"

    public_seller_claim = deepcopy(payload)
    public_seller_claim["public_context"]["seller_context"] = {
        "capabilities": ["We can provide samples."]
    }
    public_seller_merged = wrapper.merge_payload(public_seller_claim)
    if core.has_authorized_sample_support(core.normalize(public_seller_merged)):
        return False, "openclaw-gate: public context self-authorized a seller sample capability"

    operator_seller_claim = deepcopy(payload)
    operator_seller_claim["operator_input"]["seller_context"] = {
        "capabilities": ["We can provide samples for qualified review."]
    }
    operator_seller_merged = wrapper.merge_payload(operator_seller_claim)
    if not core.has_authorized_sample_support(core.normalize(operator_seller_merged)):
        return False, "openclaw-gate: explicit operator seller capability was not preserved"
    return True, "openclaw-gate: ok"


def main() -> None:
    results = []
    failed = False
    for case in CASES:
        ok, message = run_case(case)
        results.append({"case": case["label"], "ok": ok, "message": message})
        if not ok:
            failed = True

    gate_ok, gate_message = run_customer_intel_gate_case()
    results.append({"case": "customer-intel-gate", "ok": gate_ok, "message": gate_message})
    failed = failed or not gate_ok

    sample_ok, sample_message = run_follow_up_sample_authorization_case()
    results.append({"case": "follow-up-samples", "ok": sample_ok, "message": sample_message})
    failed = failed or not sample_ok

    openclaw_ok, openclaw_message = run_openclaw_gate_case()
    results.append({"case": "openclaw-gate", "ok": openclaw_ok, "message": openclaw_message})
    failed = failed or not openclaw_ok

    sys.stdout.write(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
