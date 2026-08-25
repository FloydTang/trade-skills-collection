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
            "Please let me know whether it would be helpful for me to send the next details or samples.",
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
            "Checking Whether Washed Linen Table Textile Collections Samples Would Help",
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
    core.validate(core.normalize(approved_payload), approved_payload, schema)

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

    openclaw_ok, openclaw_message = run_openclaw_gate_case()
    results.append({"case": "openclaw-gate", "ok": openclaw_ok, "message": openclaw_message})
    failed = failed or not openclaw_ok

    sys.stdout.write(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
