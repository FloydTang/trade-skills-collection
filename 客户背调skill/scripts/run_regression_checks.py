#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
OPENCLAW_SCRIPT = SKILL_ROOT / "for-openclaw" / "scripts" / "build_customer_intel_report_from_evidence.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trade_customer_intel_openclaw", OPENCLAW_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
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

    print("Customer-intel v2 regression checks passed.")


if __name__ == "__main__":
    main()
