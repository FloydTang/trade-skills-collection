#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
OPENCLAW_SCRIPT = SKILL_ROOT / "for-openclaw" / "scripts" / "build_customer_intel_report_from_evidence.py"
CLASSIC_SCRIPT = SKILL_ROOT / "scripts" / "build_customer_intel_report.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trade_customer_intel_openclaw", OPENCLAW_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_classic_module():
    spec = importlib.util.spec_from_file_location("trade_customer_intel_classic", CLASSIC_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_payload(name: str) -> dict:
    path = SKILL_ROOT / "for-openclaw" / "examples" / name
    return json.loads(path.read_text(encoding="utf-8"))


def assert_reference_integrity(report: dict) -> None:
    evidence_ids = {item["evidence_id"] for item in report["evidence_ledger"]}
    claim_ids = {item["claim_id"] for item in report["claim_ledger"]}
    for claim in report["claim_ledger"]:
        unknown = set(claim.get("evidence_ids") or []) - evidence_ids
        if unknown:
            raise SystemExit(f"Claim {claim['claim_id']} references unknown evidence: {sorted(unknown)}")
        if claim["statement_type"] == "fact" and not claim.get("evidence_ids"):
            raise SystemExit(f"Fact claim {claim['claim_id']} has no evidence reference.")
    for angle in report["sales_angles"]:
        if set(angle.get("claim_ids") or []) - claim_ids:
            raise SystemExit(f"Angle {angle['angle_id']} references an unknown claim.")
        if angle.get("approval_status") != "proposed":
            raise SystemExit("The intel generator must not auto-approve a sales angle.")


def build(module, payload: dict) -> dict:
    lead, evidence_bundle = module.normalize_payload(payload)
    return module.build_report(lead, evidence_bundle)


def main() -> None:
    module = load_module()
    runtime_module = importlib.import_module("workflow_runtime.customer_intel_v2")

    sample = build(module, load_payload("sample-input.json"))
    if sample.get("contract_version") != "2.0":
        raise SystemExit("Sample report did not use the v2 contract.")
    if sample["intel_decision"]["recommended_next_action"] != "hold_for_manual_review":
        raise SystemExit("Sparse sample should remain on hold.")
    if sample["verdict_card"]["score"] is not None:
        raise SystemExit("Sparse sample must not receive a fabricated score.")
    assert_reference_integrity(sample)

    sieger = build(module, load_payload("sieger-golden-input.json"))
    if sieger["intel_decision"]["recommended_next_action"] != "ready_for_email_draft":
        raise SystemExit(f"SIEGER golden case did not clear gates: {sieger['intel_decision']['decision_gates']}")
    if (sieger["verdict_card"]["score"] or 0) < 8:
        raise SystemExit("SIEGER golden case should receive an evidence-backed high score.")
    if sieger["verdict_card"]["customer_grade"] != "A":
        raise SystemExit("SIEGER golden case should be graded A under the fixture evidence.")
    if sieger["industry_lens"] != "industrial":
        raise SystemExit("SIEGER golden case should use the industrial lens.")
    if not sieger["seller_context"]["authorized_materials"]:
        raise SystemExit("Seller authorization context was lost before the intel stage.")
    assert_reference_integrity(sieger)

    food = module.upgrade_customer_intel_report(
        lead={
            "company_name": "Food Buyer Example",
            "company_website": "https://food-buyer.example",
            "country_or_market": "Poland",
            "product_or_offer": "frozen mixed vegetables",
            "industry_lens": "food",
            "seller_context": {
                "company_name": "Food Supplier Example",
                "product_or_offer": "frozen mixed vegetables",
                "product_categories": ["frozen vegetables"],
                "target_customer_types": ["importer", "private-label buyer"],
                "target_industries": ["frozen food", "retail food"],
                "value_propositions": ["stable specifications", "packaging coordination"],
                "proof_points": ["Authorized regression capability record."],
                "authorized_materials": ["test-fixture:food-capability-record"],
            },
        },
        raw_evidence=[
            {
                "title": "Food Buyer Official Portfolio",
                "url": "https://food-buyer.example",
                "source_type": "official_website",
                "source_quality": "primary",
                "claims": [
                    {
                        "statement": "The company imports frozen vegetables for private-label retail programs.",
                        "category": "business_line",
                        "statement_type": "fact",
                        "confidence": "high",
                    },
                    {
                        "statement": "A private-label frozen vegetable offer is a plausible fit, but purchase intent is not proven.",
                        "category": "product_fit",
                        "statement_type": "hypothesis",
                        "confidence": "medium",
                        "dimension": "product_fit",
                        "rating": 4,
                    },
                ],
            },
            {
                "title": "Food Buyer Official Retail Page",
                "url": "https://food-buyer.example/retail",
                "source_type": "official_website",
                "source_quality": "primary",
                "claims": [
                    {
                        "statement": "The retail page describes frozen-food distribution and packaging programs.",
                        "category": "business_line",
                        "statement_type": "fact",
                        "confidence": "high",
                    },
                    {
                        "statement": "The next step is to confirm SKU, pack size, certification and cold-chain requirements.",
                        "category": "procurement_clue",
                        "statement_type": "hypothesis",
                        "confidence": "medium",
                    },
                ],
            },
        ],
        company_summary="Frozen vegetable importer and private-label retail supplier.",
        official_website="https://food-buyer.example",
        recent_signals=[],
        market_signals=[],
        sales_angles=[
            {
                "cn": "从 private-label 冷冻蔬菜的 SKU、包装和认证要求切入；不要误写成电机、驱动、仓储自动化、物料搬运、工业自动化模块、工程集成或与BOM成本相关的项目。",
                "en": "Open with the private-label frozen vegetable program and ask about SKU, pack size and certification requirements.",
                "why": "This keeps the first touch tied to the buyer's public food program.",
                "avoid": "Do not claim a current sourcing project.",
            }
        ],
        risk_rating="Low",
        risk_reasons=[],
        entity_confidence="high",
        ambiguity_notes=[],
    )
    food_angle_text = " ".join(
        str((food.get("sales_angles") or [{}])[0].get(key) or "")
        for key in ("cn", "en", "why")
    ).lower()
    if food.get("industry_lens") != "food" or "private-label" not in food_angle_text:
        raise SystemExit("Food lens lost its domain-specific sales angle.")
    food_leaked_terms = (
        "asrs",
        "motor",
        "drive or control",
        "installed bom",
        "电机",
        "驱动",
        "仓储自动化",
        "物料搬运",
        "工业自动化模块",
        "工程集成",
        "bom",
    )
    if any(term in food_angle_text for term in food_leaked_terms):
        raise SystemExit("Food lens was contaminated by industrial sales-angle copy.")
    assert_reference_integrity(food)

    exact_concept_claim = [
        {
            "statement": "The buyer mentions 电机、驱动、仓储自动化、物料搬运、工业自动化模块、工程集成与BOM成本 requirements.",
            "claim_id": "CL-EXACT",
        }
    ]
    exact_concept_seller = {
        "product_or_offer": "电机驱动、仓储自动化、物料搬运、工业自动化模块和工程集成方案，支持BOM成本核对",
        "product_categories": [],
        "value_propositions": [],
    }
    exact_concepts = runtime_module._supported_industrial_concepts(exact_concept_claim, exact_concept_seller)
    expected_concepts = {
        "motor",
        "drive",
        "warehouse-automation",
        "material-handling",
        "industrial-automation",
        "engineering-integration",
        "bom",
    }
    if not expected_concepts.issubset(exact_concepts):
        raise SystemExit(f"Chinese industrial concepts were not matched exactly: {sorted(exact_concepts)}")
    exact_copy = runtime_module._sanitize_angle_text(
        "电机、驱动、仓储自动化、物料搬运、工业自动化模块、工程集成与BOM成本都可作为切入点。",
        exact_concept_claim,
        exact_concept_seller,
    )
    if any(
        term not in exact_copy
        for term in ("电机", "驱动", "仓储自动化", "物料搬运", "工业自动化模块", "工程集成", "BOM")
    ):
        raise SystemExit("Supported Chinese industrial concepts were sanitized despite exact seller support.")

    anonymous = module.upgrade_customer_intel_report(
        lead={
            "company_name": "Anonymous Evidence Buyer",
            "product_or_offer": "industrial sensors",
            "industry_lens": "industrial",
            "seller_context": {
                "company_name": "Authorized Sensor Seller",
                "product_or_offer": "industrial sensors",
                "product_categories": ["industrial sensors"],
                "target_customer_types": ["manufacturer"],
                "target_industries": ["industrial automation"],
                "value_propositions": ["specification review"],
                "proof_points": ["Authorized regression capability record."],
                "authorized_materials": ["test-fixture:sensor-capability-record"],
            },
        },
        raw_evidence=[
            {
                "note": "Anonymous caller-supplied record one.",
                "source_type": "official_website",
                "source_quality": "primary",
                "claims": [
                    {
                        "statement": "The buyer appears to operate a manufacturing line.",
                        "category": "business_line",
                        "statement_type": "fact",
                        "confidence": "high",
                    }
                ],
            },
            {
                "title": "Untitled evidence",
                "note": "Anonymous caller-supplied record two.",
                "source_type": "official_website",
                "source_quality": "primary",
                "claims": [
                    {
                        "statement": "Industrial sensors may fit, but demand is not proven.",
                        "category": "product_fit",
                        "statement_type": "hypothesis",
                        "confidence": "medium",
                        "dimension": "product_fit",
                        "rating": 4,
                    }
                ],
            },
        ],
        company_summary="Manufacturing buyer with no auditable source identity.",
        official_website="",
        recent_signals=[],
        market_signals=[],
        sales_angles=[],
        risk_rating="Low",
        risk_reasons=[],
        entity_confidence="high",
        ambiguity_notes=[],
    )
    if anonymous.get("evidence_ledger"):
        raise SystemExit("Anonymous URL-less evidence was accepted into the auditable evidence ledger.")
    if anonymous["intel_decision"]["recommended_next_action"] != "hold_for_manual_review":
        raise SystemExit("Anonymous caller-declared primary evidence cleared the customer-intel gates.")

    for source_type in ("unofficial_blog", "financial_rumor"):
        quality = runtime_module.classify_source_quality(
            f"https://{source_type.replace('_', '-')}.example/article",
            source_type,
            "",
        )
        if quality in {"primary", "strong_secondary"}:
            raise SystemExit(f"Free-form source label {source_type!r} was promoted to {quality!r}.")
    spoofed_source_probes = (
        ("https://tenant.co.uk/company", "official_website", "https://co.uk"),
        ("https://registry.gov.xyz/company", "government_registry", ""),
        ("https://registry.gov.zz/company", "government_registry", ""),
        ("https://registry.gov.io/company", "government_registry", ""),
        ("https://registry.gob.net/company", "government_registry", ""),
        ("https://registry.gov.attacker.example.com/company", "government_registry", ""),
    )
    for url, source_type, official_website in spoofed_source_probes:
        quality = runtime_module.classify_source_quality(url, source_type, official_website)
        if quality == "primary":
            raise SystemExit(f"Spoofable source URL was promoted to primary: {url}")
    if runtime_module._independent_source_key("https://alpha.linkedin.com/company/a") != runtime_module._independent_source_key(
        "https://beta.linkedin.com/company/b"
    ):
        raise SystemExit("Subdomains of the same strong platform were counted as independent sources.")

    weak_bound = module.upgrade_customer_intel_report(
        lead={
            "company_name": "Weak Bound Buyer",
            "company_website": "https://weak-bound.example",
            "product_or_offer": "industrial sensors",
            "industry_lens": "industrial",
            "seller_context": {
                "company_name": "Authorized Sensor Seller",
                "product_or_offer": "industrial sensors",
                "product_categories": ["industrial sensors"],
                "target_customer_types": ["manufacturer"],
                "target_industries": ["industrial automation"],
                "value_propositions": ["specification review"],
                "proof_points": ["Authorized regression capability record."],
                "authorized_materials": ["test-fixture:sensor-capability-record"],
            },
        },
        raw_evidence=[
            {
                "title": "Official facility page",
                "url": "https://weak-bound.example/facility",
                "source_type": "official_website",
                "claims": [
                    {
                        "statement": "The public page shows a production facility.",
                        "category": "facility",
                        "statement_type": "fact",
                        "confidence": "high",
                    }
                ],
            },
            {
                "title": "LinkedIn management profile",
                "url": "https://www.linkedin.com/company/weak-bound-buyer",
                "source_type": "linkedin",
                "claims": [
                    {
                        "statement": "A public profile names a managing director.",
                        "category": "management",
                        "statement_type": "fact",
                        "confidence": "high",
                    }
                ],
            },
            {
                "title": "Unverified business directory",
                "url": "https://directory.example/weak-bound-buyer",
                "source_type": "search",
                "claims": [
                    {
                        "statement": "The directory claims this is the target company.",
                        "category": "identity",
                        "statement_type": "fact",
                        "confidence": "high",
                    },
                    {
                        "statement": "The directory claims the company manufactures automation equipment.",
                        "category": "business_line",
                        "statement_type": "fact",
                        "confidence": "high",
                    },
                    {
                        "statement": "Industrial sensors may fit the listed automation equipment.",
                        "category": "product_fit",
                        "statement_type": "hypothesis",
                        "confidence": "medium",
                        "dimension": "product_fit",
                        "rating": 4,
                    },
                ],
            },
        ],
        company_summary="Automation equipment manufacturer according to an unverified directory.",
        official_website="https://weak-bound.example",
        recent_signals=[],
        market_signals=[],
        sales_angles=[],
        risk_rating="Low",
        risk_reasons=[],
        entity_confidence="high",
        ambiguity_notes=[],
    )
    weak_bound_gates = weak_bound["intel_decision"]["decision_gates"]
    if weak_bound_gates["evidence"]["status"] == "pass":
        raise SystemExit("Unrelated strong sources cleared weakly bound identity/business claims.")
    if weak_bound_gates["product_fit"]["status"] == "pass":
        raise SystemExit("A product-fit claim backed only by a weak directory cleared its gate.")
    if weak_bound["intel_decision"]["recommended_next_action"] != "hold_for_manual_review":
        raise SystemExit("Weakly bound core claims incorrectly cleared the customer-intel decision.")

    lens_probes = (
        ("food processing equipment", "food"),
        ("consumer electronics components", "consumer"),
        ("retail equipment", {"consumer", "general"}),
    )
    for probe_text, expected in lens_probes:
        probe_context = {"product_or_offer": probe_text, "product_categories": [], "target_industries": []}
        resolved = runtime_module.resolve_industry_lens("auto", probe_context, probe_text)
        allowed = {expected} if isinstance(expected, str) else expected
        if resolved not in allowed:
            raise SystemExit(f"Industry lens probe {probe_text!r} resolved to {resolved!r}.")
    tie_context = {"product_or_offer": "food retail products", "product_categories": [], "target_industries": []}
    tie_results = [runtime_module.resolve_industry_lens("auto", tie_context, "food retail") for _ in range(3)]
    if tie_results != ["general", "general", "general"]:
        raise SystemExit(f"Industry lens ties must deterministically fall back to general: {tie_results}")

    unrelated_industrial = module.upgrade_customer_intel_report(
        lead={
            "company_name": "PharmaPack Integrators",
            "company_website": "https://pharmapack.example",
            "product_or_offer": "industrial valves and seals",
            "industry_lens": "auto",
            "seller_context": {
                "company_name": "Authorized Valve Seller",
                "product_or_offer": "industrial valves and seals",
                "product_categories": ["industrial valves"],
                "target_customer_types": ["packaging-line integrator"],
                "target_industries": ["pharmaceutical packaging"],
                "value_propositions": ["specification review", "compliance documentation"],
                "proof_points": ["Authorized regression capability record."],
                "authorized_materials": ["test-fixture:industrial-valves"],
            },
        },
        raw_evidence=[
            {
                "title": "PharmaPack Official Portfolio",
                "url": "https://pharmapack.example",
                "source_type": "official_website",
                "source_quality": "primary",
                "claims": [
                    {
                        "statement": "The company designs pharmaceutical packaging lines and validates regulated production requirements.",
                        "category": "business_line",
                        "statement_type": "fact",
                        "confidence": "high",
                    },
                    {
                        "statement": "An industrial valve offer may fit maintenance specification review, but current purchasing is not proven.",
                        "category": "product_fit",
                        "statement_type": "hypothesis",
                        "confidence": "medium",
                        "dimension": "product_fit",
                        "rating": 3,
                    },
                    {
                        "statement": "The next step is to confirm valve size, pressure, material and compliance requirements.",
                        "category": "procurement_clue",
                        "statement_type": "hypothesis",
                        "confidence": "medium",
                    },
                ],
            }
        ],
        company_summary="Pharmaceutical packaging-line integrator.",
        official_website="https://pharmapack.example",
        recent_signals=[],
        market_signals=[],
        sales_angles=[
            {
                "cn": "从阀门规格和合规文件确认切入。",
                "en": "Open with valve specifications and compliance documentation.",
                "why": "This stays within the public packaging-line evidence.",
            }
        ],
        risk_rating="Low",
        risk_reasons=[],
        entity_confidence="high",
        ambiguity_notes=[],
    )
    if unrelated_industrial.get("industry_lens") != "industrial":
        raise SystemExit("The unrelated industrial fixture should resolve to the industrial lens.")
    unrelated_angle_text = json.dumps(unrelated_industrial.get("sales_angles"), ensure_ascii=False).lower()
    unsupported_terms = (
        "asrs",
        "bom",
        "motor",
        "drive",
        "storage",
        "material-handling",
        "material handling",
        "engineering team",
        "研发/系统集成",
    )
    if any(term in unrelated_angle_text for term in unsupported_terms):
        raise SystemExit("Unrelated industrial evidence angles leaked unsupported industrial vocabulary.")
    business_line_only_terms = (
        "engineering-fit",
        "engineering contact",
        "engineering team",
        "r&d",
        "研发能力",
        "system integration",
        "系统集成",
    )
    if any(term in unrelated_angle_text for term in business_line_only_terms):
        raise SystemExit("business_line alone implied R&D, system integration, or an engineering team.")
    if "application-fit review" not in unrelated_angle_text or "product or sourcing" not in unrelated_angle_text:
        raise SystemExit("business_line-only conditional angle was not preserved.")
    assert_reference_integrity(unrelated_industrial)

    try:
        module.normalize_payload({"lead": {"company_name": "Acme"}, "evidence_bundle": {"errors": {}}})
    except SystemExit:
        pass
    else:
        raise SystemExit("Malformed evidence-bundle arrays must be rejected before report generation.")

    classic = load_classic_module()
    classic_input = classic.normalize_input(
        {
            "company_name": "Offline Example Co",
            "product_or_offer": "industrial sensors",
            "seller_context": {
                "company_name": "Authorized Seller",
                "product_or_offer": "industrial sensors",
                "product_categories": ["industrial sensors"],
            },
        }
    )
    degraded = classic.build_report(
        classic_input,
        [],
        {},
        [
            {
                "stage": "search",
                "query_or_url": "offline test",
                "error_type": "TimeoutError",
                "message": "simulated timeout",
            }
        ],
    )
    if degraded.get("collection_status") != "failed":
        raise SystemExit("A total collection outage must be exposed as collection_status=failed.")
    if degraded["intel_decision"]["recommended_next_action"] != "hold_for_manual_review":
        raise SystemExit("A total collection outage must fail closed at the intel gate.")
    try:
        classic.normalize_input({"company_name": {"invalid": True}})
    except SystemExit:
        pass
    else:
        raise SystemExit("Malformed classic input must be rejected instead of coerced to text.")

    print("Customer-intel v2 and delivery-boundary regression checks passed.")


if __name__ == "__main__":
    main()
