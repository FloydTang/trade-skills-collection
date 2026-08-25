#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PACKAGE_ROOT.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_workflow as workflow_impl


DEMO_SCRIPT = SCRIPT_DIR / "run_minimal_demo.py"
WORKFLOW_SCRIPT = SCRIPT_DIR / "run_workflow.py"
FIXTURE_REPORT = PACKAGE_ROOT / "examples" / "reviewed-customer-intel-report.json"
LOCAL_SUBSKILL_ROOT = PACKAGE_ROOT / "子Skill与工具本体"
SKILL_ROOT = (
    LOCAL_SUBSKILL_ROOT
    if (LOCAL_SUBSKILL_ROOT / "客户背调skill").is_dir()
    else WORKSPACE_ROOT
)
SIEGER_INPUT = SKILL_ROOT / "客户背调skill" / "for-openclaw" / "examples" / "sieger-golden-input.json"
SPARSE_INPUT = SKILL_ROOT / "客户背调skill" / "for-openclaw" / "examples" / "sample-input.json"
FROZEN_FOOD_SEARCH_INPUT = SKILL_ROOT / "客户搜索skill" / "examples" / "frozen-food-search.json"
FROZEN_FOOD_SEARCH_FIXTURES = SKILL_ROOT / "客户搜索skill" / "examples" / "frozen-food-fixtures.json"

EXPECTED_OUTPUTS = [
    "01-lead-discovery-output.json",
    "02-lead-screening-input.json",
    "03-lead-screening-output.json",
    "03-lead-screening-output.md",
    "04-customer-intel-batch.json",
    "05-selected-customer-intel-input.json",
    "06-customer-intel-report.json",
    "07-email-input.json",
    "08-email-draft.json",
    "08-email-draft.md",
    "09-container-bundle.json",
    "09-feishu-workflow-bundle.json",
    "10-container-bundle.md",
    "11-lead-workflow.csv",
    "12-feishu-sandbox-bundle.json",
]


def run_demo(output_dir: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(DEMO_SCRIPT), "--output-dir", str(output_dir)],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_artifact_hash_coverage(output_dir: Path, required_keys: set[str] | None = None) -> None:
    manifest = load_json(output_dir / "00-run-manifest.json")
    artifacts = manifest.get("artifacts") or {}
    hashes = manifest.get("artifact_sha256") or {}
    if set(artifacts) != set(hashes):
        missing = sorted(set(artifacts) - set(hashes))
        extra = sorted(set(hashes) - set(artifacts))
        raise SystemExit(f"Artifact hash coverage mismatch. Missing: {missing}; extra: {extra}")
    if required_keys and not required_keys.issubset(artifacts):
        missing = sorted(required_keys - set(artifacts))
        raise SystemExit(f"Manifest is missing required artifact registrations: {', '.join(missing)}")
    for key, relative_path in artifacts.items():
        path = output_dir / str(relative_path)
        if not path.is_file() or file_sha256(path) != hashes.get(key):
            raise SystemExit(f"Artifact hash does not cover the current file: {key}")


def run_workflow(config_path: Path, output_dir: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(WORKFLOW_SCRIPT),
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            *extra_args,
        ],
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def production_config(run_id: str, input_path: Path) -> dict:
    return {
        "contract_version": "1.0",
        "run_id": run_id,
        "start_mode": "customer_intel",
        "customer_intel": {
            "mode": "evidence",
            "input_json": str(input_path),
        },
        "outreach": {
            "email_type": "first_touch",
            "product_or_offer": "industrial automation components",
            "sender_name": "Workflow Tester",
            "sender_company": "Authorized Test Supplier",
        },
        "exports": {
            "container_bundle": False,
            "feishu_sandbox": False,
        },
    }


def assert_production_pause_resume(temp_root: Path) -> None:
    config_path = temp_root / "sieger-workflow.json"
    output_dir = temp_root / "sieger-run"
    write_json(config_path, production_config("sieger-delivery-regression", SIEGER_INPUT))

    first = run_workflow(config_path, output_dir)
    if first.returncode != 10:
        raise SystemExit(f"Production workflow should pause with code 10: {first.stderr or first.stdout}")
    manifest = load_json(output_dir / "00-run-manifest.json")
    if manifest.get("status") != "awaiting_sales_angle_approval":
        raise SystemExit("Production workflow did not enter the approval wait state.")
    if len(str(manifest.get("review_report_sha256") or "")) != 64:
        raise SystemExit("Approval wait state did not bind to the reviewed report hash.")
    if (output_dir / "08-email-draft.json").exists():
        raise SystemExit("Production workflow generated an email before angle approval.")

    invalid_approval_path = temp_root / "invalid-approval.json"
    write_json(
        invalid_approval_path,
        {
            "contract_version": "1.0",
            "run_id": "sieger-delivery-regression",
            "report_sha256": "0" * 64,
            "angle_id": "ANGLE-01",
            "reviewer": "Regression Reviewer",
            "approved_at": "2026-08-25T00:00:00+00:00",
        },
    )
    mismatch = run_workflow(
        config_path,
        output_dir,
        "--resume",
        "--approval-json",
        str(invalid_approval_path),
    )
    if mismatch.returncode != 2:
        raise SystemExit("A mismatched report hash should be rejected as invalid approval input.")
    mismatch_manifest = load_json(output_dir / "00-run-manifest.json")
    if mismatch_manifest.get("status") != "failed" or mismatch_manifest.get("exit_code") != 2:
        raise SystemExit("Invalid approval input left the run manifest in a stale running state.")

    resumed = run_workflow(
        config_path,
        output_dir,
        "--resume",
        "--approved-sales-angle-id",
        "ANGLE-01",
        "--reviewer",
        "Regression Reviewer",
    )
    if resumed.returncode != 0:
        raise SystemExit(f"Approved production workflow did not complete: {resumed.stderr or resumed.stdout}")
    manifest = load_json(output_dir / "00-run-manifest.json")
    approval = load_json(output_dir / "05-sales-angle-approval.json")
    email = load_json(output_dir / "08-email-draft.json")
    if manifest.get("status") != "completed" or manifest.get("exit_code") != 0:
        raise SystemExit("Completed production workflow has the wrong manifest state.")
    if approval.get("report_sha256") != manifest.get("review_report_sha256"):
        raise SystemExit("Approval record lost its reviewed-report hash binding.")
    if approval.get("reviewer") != "Regression Reviewer":
        raise SystemExit("Approval record lost the human reviewer identifier.")
    if email.get("send_policy") != "manual_review_only":
        raise SystemExit("Production workflow must keep the final email in manual-review-only mode.")
    email_text = json.dumps(email.get("drafts") or {}, ensure_ascii=False)
    if "Dear there" in email_text or "?." in email_text:
        raise SystemExit("Company-level production email contains a placeholder greeting or broken punctuation.")
    email_source = email.get("source_context") or {}
    if email_source.get("approved_angle_id") != "ANGLE-01":
        raise SystemExit("Final email artifact lost the approved angle ID.")
    if not email_source.get("selected_claims") or not email_source.get("selected_evidence"):
        raise SystemExit("Final email artifact lost its structured claim/evidence audit trail.")
    assert_artifact_hash_coverage(
        output_dir,
        {
            "customer_intel_evidence_input",
            "outreach_email_markdown",
            "sales_angle_approval",
        },
    )
    repeated = run_workflow(config_path, output_dir, "--resume")
    if repeated.returncode != 0:
        raise SystemExit("A completed production run should be idempotent on resume.")
    email_path = output_dir / "08-email-draft.json"
    original_email_hash = manifest["artifact_sha256"]["outreach_email"]
    email_path.write_text(email_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    tampered = run_workflow(config_path, output_dir, "--resume")
    if tampered.returncode != 3:
        raise SystemExit("A changed completed artifact should be rejected during resume validation.")
    tampered_manifest = load_json(output_dir / "00-run-manifest.json")
    if tampered_manifest.get("current_stage") != "resume_validation":
        raise SystemExit("Completed-artifact tampering was not attributed to resume_validation.")
    if tampered_manifest["artifact_sha256"]["outreach_email"] != original_email_hash:
        raise SystemExit("Resume validation blessed a modified artifact by replacing its recorded hash.")


def assert_registered_artifact_removal_rejected(temp_root: Path) -> None:
    config_path = temp_root / "missing-email-markdown-workflow.json"
    output_dir = temp_root / "missing-email-markdown-run"
    write_json(config_path, production_config("missing-email-markdown-regression", SIEGER_INPUT))
    if run_workflow(config_path, output_dir).returncode != 10:
        raise SystemExit("Missing-email-Markdown fixture did not reach the review gate.")
    completed = run_workflow(
        config_path,
        output_dir,
        "--resume",
        "--approved-sales-angle-id",
        "ANGLE-01",
        "--reviewer",
        "Regression Reviewer",
    )
    if completed.returncode != 0:
        raise SystemExit(f"Missing-email-Markdown fixture did not complete: {completed.stderr}")
    manifest = load_json(output_dir / "00-run-manifest.json")
    expected_hash = manifest["artifact_sha256"]["outreach_email_markdown"]
    (output_dir / "08-email-draft.md").unlink()
    rejected = run_workflow(config_path, output_dir, "--resume")
    if rejected.returncode != 3:
        raise SystemExit("Deleting a registered email Markdown artifact did not fail resume validation.")
    rejected_manifest = load_json(output_dir / "00-run-manifest.json")
    if rejected_manifest.get("current_stage") != "resume_validation":
        raise SystemExit("Missing email Markdown was not attributed to resume_validation.")
    if rejected_manifest["artifact_sha256"]["outreach_email_markdown"] != expected_hash:
        raise SystemExit("Resume validation replaced the recorded hash for missing email Markdown.")


def assert_fresh_stale_approval_rejection(temp_root: Path) -> None:
    config_path = temp_root / "fresh-stale-approval-workflow.json"
    output_dir = temp_root / "fresh-stale-approval-run"
    write_json(config_path, production_config("fresh-stale-approval-regression", SIEGER_INPUT))
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        output_dir / "05-sales-angle-approval.json",
        {
            "contract_version": "1.0",
            "run_id": "fresh-stale-approval-regression",
            "report_sha256": "0" * 64,
            "angle_id": "ANGLE-01",
            "reviewer": "Stale Approval Fixture",
            "approved_at": "2026-08-25T00:00:00+00:00",
        },
    )
    fresh = run_workflow(config_path, output_dir)
    if fresh.returncode != 2:
        raise SystemExit("A fresh run consumed a stale approval file instead of rejecting it.")
    if (output_dir / "00-run-manifest.json").exists():
        raise SystemExit("Fresh stale-approval rejection should happen before creating a run manifest.")
    if not (output_dir / "05-sales-angle-approval.json").exists():
        raise SystemExit("Fresh stale-approval rejection unexpectedly removed the stale input.")

    for stale_name in ("08-email-draft.json", "11-lead-workflow.csv"):
        stale_output_dir = temp_root / f"fresh-stale-{stale_name.replace('.', '-')}-run"
        stale_output_dir.mkdir(parents=True, exist_ok=True)
        (stale_output_dir / stale_name).write_text("stale pipeline artifact\n", encoding="utf-8")
        rejected = run_workflow(config_path, stale_output_dir)
        if rejected.returncode != 2:
            raise SystemExit(f"Fresh run accepted stale pipeline artifact {stale_name}.")
        if (stale_output_dir / "00-run-manifest.json").exists():
            raise SystemExit(f"Fresh stale-artifact rejection created a manifest for {stale_name}.")
        if not (stale_output_dir / stale_name).exists():
            raise SystemExit(f"Fresh stale-artifact rejection removed {stale_name}.")


def reviewed_report_discovery_config(run_id: str, report_path: Path) -> dict:
    return {
        "contract_version": "1.0",
        "run_id": run_id,
        "start_mode": "discovery",
        "lead_discovery": {
            "mode": "fixture",
            "selected_lead_id": "lead-002",
            "input_json": str(FROZEN_FOOD_SEARCH_INPUT),
            "fixtures_json": str(FROZEN_FOOD_SEARCH_FIXTURES),
        },
        "customer_intel": {
            "mode": "reviewed_report",
            "report_json": str(report_path),
        },
        "outreach": {
            "email_type": "first_touch",
            "product_or_offer": "frozen mixed vegetables",
            "sender_name": "Workflow Tester",
            "sender_company": "Authorized Test Supplier",
        },
        "exports": {"container_bundle": False, "feishu_sandbox": False},
    }


def assert_discovery_reviewed_report_materialization(temp_root: Path) -> None:
    reviewed_report = load_json(FIXTURE_REPORT)
    for angle in reviewed_report.get("sales_angles") or []:
        angle["approval_status"] = "proposed"
    reviewed_report_path = temp_root / "reviewed-report-source.json"
    write_json(reviewed_report_path, reviewed_report)

    config_path = temp_root / "discovery-reviewed-report-workflow.json"
    output_dir = temp_root / "discovery-reviewed-report-run"
    write_json(config_path, reviewed_report_discovery_config("discovery-reviewed-report-regression", reviewed_report_path))
    first = run_workflow(config_path, output_dir)
    if first.returncode != 10:
        raise SystemExit(f"Discovery + reviewed_report did not pause for approval: {first.stderr or first.stdout}")
    materialized = load_json(output_dir / "06-customer-intel-report.json")
    selected = load_json(output_dir / "05-selected-customer-intel-input.json")
    selected_company = str(selected.get("company_name") or "").strip()
    report_company = str((materialized.get("identity_snapshot") or {}).get("company_name") or "").strip()
    if selected_company != "GreenHarvest Foods" or report_company != selected_company:
        raise SystemExit("Discovery + reviewed_report did not preserve the selected company match.")
    if not (output_dir / "06-customer-intel-report.json").is_file():
        raise SystemExit("reviewed_report was not materialized into the run output directory.")

    mismatch_report = json.loads(json.dumps(reviewed_report, ensure_ascii=False))
    mismatch_report["identity_snapshot"]["company_name"] = "Different Company"
    mismatch_report_path = temp_root / "mismatched-reviewed-report.json"
    write_json(mismatch_report_path, mismatch_report)
    mismatch_config_path = temp_root / "mismatched-discovery-reviewed-report-workflow.json"
    mismatch_output_dir = temp_root / "mismatched-discovery-reviewed-report-run"
    write_json(
        mismatch_config_path,
        reviewed_report_discovery_config("mismatched-discovery-reviewed-report-regression", mismatch_report_path),
    )
    mismatch = run_workflow(mismatch_config_path, mismatch_output_dir)
    if mismatch.returncode != 3:
        raise SystemExit("A discovery-selected company mismatch was not rejected at customer_intel.")
    mismatch_manifest = load_json(mismatch_output_dir / "00-run-manifest.json")
    if mismatch_manifest.get("current_stage") != "customer_intel":
        raise SystemExit("Selected-company mismatch was not attributed to customer_intel.")
    if (mismatch_output_dir / "08-email-draft.json").exists():
        raise SystemExit("A selected-company mismatch generated an email draft.")

    for mismatch_kind, field, value in (
        ("website", "website", "https://different-entity.example"),
        ("market", "country_or_market", "Germany"),
    ):
        entity_mismatch = json.loads(json.dumps(reviewed_report, ensure_ascii=False))
        entity_mismatch["identity_snapshot"][field] = value
        entity_mismatch_path = temp_root / f"mismatched-reviewed-report-{mismatch_kind}.json"
        write_json(entity_mismatch_path, entity_mismatch)
        entity_config_path = temp_root / f"mismatched-discovery-reviewed-report-{mismatch_kind}.json"
        entity_output_dir = temp_root / f"mismatched-discovery-reviewed-report-{mismatch_kind}-run"
        write_json(
            entity_config_path,
            reviewed_report_discovery_config(
                f"mismatched-discovery-reviewed-report-{mismatch_kind}",
                entity_mismatch_path,
            ),
        )
        entity_result = run_workflow(entity_config_path, entity_output_dir)
        if entity_result.returncode != 3:
            raise SystemExit(f"Reviewed-report {mismatch_kind} mismatch was not rejected conservatively.")
        entity_manifest = load_json(entity_output_dir / "00-run-manifest.json")
        if entity_manifest.get("current_stage") != "customer_intel":
            raise SystemExit(f"Reviewed-report {mismatch_kind} mismatch was not attributed to customer_intel.")


def assert_discovery_reviewed_report_requires_corroboration(temp_root: Path) -> None:
    reviewed_report = load_json(FIXTURE_REPORT)
    for angle in reviewed_report.get("sales_angles") or []:
        angle["approval_status"] = "proposed"

    for missing_kind, fields in (
        (
            "domain",
            ("website", "domain", "email_domain", "company_website"),
        ),
        (
            "market",
            ("country_or_market", "market", "target_market"),
        ),
    ):
        missing_report = json.loads(json.dumps(reviewed_report, ensure_ascii=False))
        missing_identity = missing_report.setdefault("identity_snapshot", {})
        for field in fields:
            missing_identity.pop(field, None)
            missing_report.pop(field, None)
        report_path = temp_root / f"missing-{missing_kind}-reviewed-report.json"
        config_path = temp_root / f"missing-{missing_kind}-reviewed-report-workflow.json"
        output_dir = temp_root / f"missing-{missing_kind}-reviewed-report-run"
        write_json(report_path, missing_report)
        write_json(
            config_path,
            reviewed_report_discovery_config(
                f"missing-{missing_kind}-reviewed-report-regression",
                report_path,
            ),
        )
        result = run_workflow(config_path, output_dir)
        if result.returncode != 3:
            raise SystemExit(
                f"Reviewed-report missing {missing_kind} corroboration was not rejected: "
                f"{result.stderr or result.stdout}"
            )
        manifest = load_json(output_dir / "00-run-manifest.json")
        if manifest.get("current_stage") != "customer_intel":
            raise SystemExit(
                f"Reviewed-report missing {missing_kind} corroboration was not attributed to customer_intel."
            )
        if (output_dir / "08-email-draft.json").exists():
            raise SystemExit(f"Reviewed-report missing {missing_kind} corroboration generated an email draft.")


def assert_source_snapshots_reject_changed_contents(temp_root: Path) -> None:
    evidence_source = temp_root / "source-snapshot-evidence.json"
    write_json(evidence_source, load_json(SIEGER_INPUT))
    evidence_config = temp_root / "source-snapshot-evidence-workflow.json"
    evidence_output = temp_root / "source-snapshot-evidence-run"
    write_json(evidence_config, production_config("source-snapshot-evidence", evidence_source))
    if run_workflow(evidence_config, evidence_output).returncode != 10:
        raise SystemExit("Evidence source snapshot fixture did not reach the review gate.")
    evidence_manifest = load_json(evidence_output / "00-run-manifest.json")
    evidence_materialized = evidence_output / "05-customer-intel-evidence-input.json"
    materialized_hash = file_sha256(evidence_materialized)
    if evidence_manifest.get("sources", {}).get("customer_intel_evidence", {}).get("sha256") != file_sha256(evidence_source):
        raise SystemExit("Evidence source SHA-256 was not recorded in the manifest.")
    evidence_payload = load_json(evidence_source)
    evidence_payload["source_mutated_after_snapshot"] = True
    write_json(evidence_source, evidence_payload)
    changed = run_workflow(evidence_config, evidence_output, "--resume")
    if changed.returncode != 3:
        raise SystemExit("Changed evidence source contents were accepted on resume.")
    changed_manifest = load_json(evidence_output / "00-run-manifest.json")
    if changed_manifest.get("current_stage") != "resume_validation":
        raise SystemExit("Changed evidence source was not attributed to resume_validation.")
    if file_sha256(evidence_materialized) != materialized_hash:
        raise SystemExit("Changed evidence source overwrote the frozen materialized copy.")

    source_input = temp_root / "source-snapshot-discovery-input.json"
    source_fixtures = temp_root / "source-snapshot-discovery-fixtures.json"
    source_report = temp_root / "source-snapshot-discovery-report.json"
    source_input.write_text(FROZEN_FOOD_SEARCH_INPUT.read_text(encoding="utf-8"), encoding="utf-8")
    source_fixtures.write_text(FROZEN_FOOD_SEARCH_FIXTURES.read_text(encoding="utf-8"), encoding="utf-8")
    reviewed_report = load_json(FIXTURE_REPORT)
    for angle in reviewed_report.get("sales_angles") or []:
        angle["approval_status"] = "proposed"
    write_json(source_report, reviewed_report)
    discovery_config = temp_root / "source-snapshot-discovery-workflow.json"
    discovery_output = temp_root / "source-snapshot-discovery-run"
    discovery_config_payload = reviewed_report_discovery_config("source-snapshot-discovery", source_report)
    discovery_config_payload["lead_discovery"]["input_json"] = str(source_input)
    discovery_config_payload["lead_discovery"]["fixtures_json"] = str(source_fixtures)
    write_json(discovery_config, discovery_config_payload)
    if run_workflow(discovery_config, discovery_output).returncode != 10:
        raise SystemExit("Discovery source snapshot fixture did not reach the review gate.")
    discovery_manifest = load_json(discovery_output / "00-run-manifest.json")
    source_hashes = discovery_manifest.get("sources") or {}
    for source_key, source_path in (
        ("lead_discovery_input", source_input),
        ("lead_discovery_fixtures", source_fixtures),
        ("customer_intel_report", source_report),
    ):
        if source_hashes.get(source_key, {}).get("sha256") != file_sha256(source_path):
            raise SystemExit(f"Source SHA-256 was not recorded for {source_key}.")
    frozen_report = discovery_output / "06-customer-intel-report.json"
    frozen_report_hash = file_sha256(frozen_report)
    report_payload = load_json(source_report)
    report_payload["source_mutated_after_snapshot"] = True
    write_json(source_report, report_payload)
    changed_report = run_workflow(discovery_config, discovery_output, "--resume")
    if changed_report.returncode != 3:
        raise SystemExit("Changed reviewed-report source contents were accepted on resume.")
    if file_sha256(frozen_report) != frozen_report_hash:
        raise SystemExit("Changed reviewed-report source overwrote the frozen report copy.")


def assert_export_failure_does_not_repeat_email(temp_root: Path) -> None:
    reviewed_report = load_json(FIXTURE_REPORT)
    for angle in reviewed_report.get("sales_angles") or []:
        angle["approval_status"] = "proposed"
    report_path = temp_root / "export-failure-email-skip-report.json"
    write_json(report_path, reviewed_report)
    full_config = reviewed_report_discovery_config(
        "export-failure-email-skip-regression",
        report_path,
    )
    full_config["exports"] = {"container_bundle": True, "feishu_sandbox": False}
    config_path = temp_root / "export-failure-email-skip-workflow.json"
    output_dir = temp_root / "export-failure-email-skip-run"
    write_json(config_path, full_config)
    if run_workflow(config_path, output_dir).returncode != 10:
        raise SystemExit("Export-failure fixture did not reach the review gate.")

    original_export = workflow_impl.export_default_artifacts

    def fail_export(*args, **kwargs):
        raise RuntimeError("simulated export-only failure")

    workflow_impl.export_default_artifacts = fail_export
    try:
        try:
            workflow_impl.run_workflow(
                full_config,
                config_path,
                output_dir,
                resume=True,
                approval_override="ANGLE-01",
                reviewer="Regression Reviewer",
                approval_json="",
            )
        except workflow_impl.StageExecutionError as exc:
            if exc.stage != "exports":
                raise SystemExit(f"Injected export failure hit the wrong stage: {exc.stage}")
        else:
            raise SystemExit("Injected export failure was not surfaced.")
    finally:
        workflow_impl.export_default_artifacts = original_export

    interrupted_manifest = load_json(output_dir / "00-run-manifest.json")
    email_attempt = interrupted_manifest["stages"]["outreach_email"]["attempt"]
    email_hash = interrupted_manifest["artifact_sha256"]["outreach_email"]
    resumed = run_workflow(config_path, output_dir, "--resume")
    if resumed.returncode != 0:
        raise SystemExit(f"Resume after export-only failure did not complete: {resumed.stderr or resumed.stdout}")
    completed_manifest = load_json(output_dir / "00-run-manifest.json")
    if completed_manifest["stages"]["outreach_email"]["attempt"] != email_attempt:
        raise SystemExit("Export-only retry regenerated the email stage or incremented its attempt.")
    if completed_manifest["artifact_sha256"]["outreach_email"] != email_hash:
        raise SystemExit("Export-only retry changed the completed email artifact.")


def approval_record(manifest: dict, angle_id: str = "ANGLE-01") -> dict:
    return {
        "contract_version": "1.0",
        "run_id": manifest["run_id"],
        "report_sha256": manifest["review_report_sha256"],
        "angle_id": angle_id,
        "reviewer": "Crash Recovery Fixture",
        "approved_at": "2026-08-25T00:00:00+00:00",
    }


def mark_pending_approval(output_dir: Path, record: dict) -> None:
    manifest_path = output_dir / "00-run-manifest.json"
    manifest = load_json(manifest_path)
    manifest.update(
        {
            "status": "applying_approval",
            "current_stage": "customer_intel",
            "next_action": "完成可恢复的销售角度审批事务。",
            "pending_approval": record,
        }
    )
    write_json(manifest_path, manifest)


def assert_approval_transaction_recovery(temp_root: Path) -> None:
    before_report_config = temp_root / "approval-crash-before-report-workflow.json"
    before_report_output = temp_root / "approval-crash-before-report-run"
    write_json(before_report_config, production_config("approval-crash-before-report", SIEGER_INPUT))
    if run_workflow(before_report_config, before_report_output).returncode != 10:
        raise SystemExit("Approval recovery fixture did not reach the review gate.")
    before_report_manifest = load_json(before_report_output / "00-run-manifest.json")
    mark_pending_approval(before_report_output, approval_record(before_report_manifest))
    recovered_before_report = run_workflow(before_report_config, before_report_output, "--resume")
    if recovered_before_report.returncode != 0:
        raise SystemExit(f"Approval recovery failed before report mutation: {recovered_before_report.stderr}")
    recovered_manifest = load_json(before_report_output / "00-run-manifest.json")
    if recovered_manifest.get("status") != "completed" or "pending_approval" in recovered_manifest:
        raise SystemExit("Recovery did not clear the pending approval after applying the report mutation.")

    after_report_config = temp_root / "approval-crash-after-report-workflow.json"
    after_report_output = temp_root / "approval-crash-after-report-run"
    write_json(after_report_config, production_config("approval-crash-after-report", SIEGER_INPUT))
    if run_workflow(after_report_config, after_report_output).returncode != 10:
        raise SystemExit("Second approval recovery fixture did not reach the review gate.")
    after_report_manifest = load_json(after_report_output / "00-run-manifest.json")
    report_path = after_report_output / "06-customer-intel-report.json"
    report = load_json(report_path)
    for angle in report.get("sales_angles") or []:
        angle["approval_status"] = "approved" if angle.get("angle_id") == "ANGLE-01" else "proposed"
    write_json(report_path, report)
    record = approval_record(after_report_manifest)
    mark_pending_approval(after_report_output, record)
    recovered_after_report = run_workflow(after_report_config, after_report_output, "--resume")
    if recovered_after_report.returncode != 0:
        raise SystemExit(f"Approval recovery failed after report mutation: {recovered_after_report.stderr}")
    approval_path = after_report_output / "05-sales-angle-approval.json"
    if load_json(approval_path).get("angle_id") != "ANGLE-01":
        raise SystemExit("Approval recovery did not materialize the pending approval record.")
    assert_artifact_hash_coverage(after_report_output, {"sales_angle_approval"})


def assert_multi_file_commit_recovery(temp_root: Path) -> None:
    rollback_dir = temp_root / "multi-file-commit-rollback"
    rollback_dir.mkdir(parents=True, exist_ok=True)
    first_temp = rollback_dir / "first.json.stage-tmp"
    second_temp = rollback_dir / "second.json.stage-tmp"
    first_final = rollback_dir / "first.json"
    second_final = rollback_dir / "second.json"
    first_temp.write_text("new-first", encoding="utf-8")
    second_temp.write_text("new-second", encoding="utf-8")
    first_final.write_text("old-first", encoding="utf-8")
    second_final.write_text("old-second", encoding="utf-8")

    original_replace = Path.replace

    def fail_second_commit(source: Path, target: Path) -> Path:
        if source.resolve() == second_temp.resolve() and Path(target).resolve() == second_final.resolve():
            raise OSError("simulated second-file commit failure")
        return original_replace(source, target)

    Path.replace = fail_second_commit
    try:
        try:
            workflow_impl.commit_stage_outputs(
                "rollback_regression",
                [(first_temp, first_final), (second_temp, second_final)],
            )
        except workflow_impl.StageExecutionError:
            pass
        else:
            raise SystemExit("Multi-file commit failure was not surfaced as StageExecutionError.")
    finally:
        Path.replace = original_replace

    if first_final.read_text(encoding="utf-8") != "old-first" or second_final.read_text(encoding="utf-8") != "old-second":
        raise SystemExit("Multi-file commit did not restore all pre-commit files after rollback.")
    marker_path = rollback_dir / workflow_impl.TRANSACTION_MARKER_NAME
    backup_dirs = list(rollback_dir.glob(".stage-backup-*"))
    if any(path.exists() for path in (first_temp, second_temp, first_final.with_name("first.json.stage-backup"), second_final.with_name("second.json.stage-backup"))) or marker_path.exists() or backup_dirs:
        raise SystemExit("Multi-file rollback left temporary or backup files behind.")

    recovery_dir = temp_root / "interrupted-backup-recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    recovered_final = recovery_dir / "recovered.json"
    recovered_backup = recovery_dir / "recovered.json.stage-backup"
    recovered_temp = recovery_dir / "recovered.json.stage-tmp"
    recovered_final.write_text("new-after-crash", encoding="utf-8")
    recovered_backup.write_text("old-before-crash", encoding="utf-8")
    recovered_temp.write_text("orphaned-temp", encoding="utf-8")
    export_temp_dir = recovery_dir / ".exports-stage-tmp"
    export_temp_dir.mkdir()
    (export_temp_dir / "partial.json").write_text("partial", encoding="utf-8")

    workflow_impl.recover_interrupted_commits(recovery_dir)
    if recovered_final.read_text(encoding="utf-8") != "old-before-crash":
        raise SystemExit("Interrupted backup recovery did not restore the previous artifact.")
    if recovered_backup.exists() or recovered_temp.exists() or export_temp_dir.exists():
        raise SystemExit("Interrupted backup recovery left crash debris behind.")


def assert_commit_cleanup_failure_recovery(temp_root: Path) -> None:
    output_dir = temp_root / "commit-cleanup-failure-recovery"
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_path = output_dir / "artifact.json.stage-tmp"
    final_path = output_dir / "artifact.json"
    temp_path.write_text("new-generation", encoding="utf-8")
    final_path.write_text("old-generation", encoding="utf-8")

    original_rmtree = workflow_impl.shutil.rmtree

    def fail_backup_cleanup(path, *args, **kwargs):
        if Path(path).name.startswith(".stage-backup-"):
            raise OSError("simulated backup cleanup interruption")
        return original_rmtree(path, *args, **kwargs)

    workflow_impl.shutil.rmtree = fail_backup_cleanup
    try:
        try:
            workflow_impl.commit_stage_outputs("cleanup_regression", [(temp_path, final_path)])
        except workflow_impl.StageExecutionError as exc:
            if "cleanup" not in str(exc).lower():
                raise SystemExit("Backup cleanup interruption lost its recovery context.")
        except OSError as exc:
            raise SystemExit(f"Backup cleanup leaked raw OSError: {exc}")
        else:
            raise SystemExit("Injected backup cleanup interruption was not surfaced.")
    finally:
        workflow_impl.shutil.rmtree = original_rmtree

    marker_path = output_dir / ".stage-transaction.json"
    if not marker_path.exists():
        raise SystemExit("Backup cleanup interruption did not leave a transaction marker.")
    if final_path.read_text(encoding="utf-8") != "new-generation":
        raise SystemExit("Backup cleanup interruption left the final artifact on the old generation.")
    if any(path.name.endswith(".stage-backup") for path in output_dir.iterdir()):
        raise SystemExit("Backup cleanup interruption left a visible legacy backup artifact.")

    workflow_impl.recover_interrupted_commits(output_dir)
    if marker_path.exists() or any(path.name.startswith(".stage-backup-") for path in output_dir.iterdir()):
        raise SystemExit("Crash recovery did not finish the interrupted backup cleanup.")
    if final_path.read_text(encoding="utf-8") != "new-generation":
        raise SystemExit("Crash recovery changed the committed new generation.")


def assert_production_hold_and_failure(temp_root: Path) -> None:
    sparse_config_path = temp_root / "sparse-workflow.json"
    sparse_output_dir = temp_root / "sparse-run"
    write_json(sparse_config_path, production_config("sparse-delivery-regression", SPARSE_INPUT))
    sparse = run_workflow(sparse_config_path, sparse_output_dir)
    if sparse.returncode != 11:
        raise SystemExit(f"Sparse workflow should stop with business-hold code 11: {sparse.stderr or sparse.stdout}")
    sparse_manifest = load_json(sparse_output_dir / "00-run-manifest.json")
    if sparse_manifest.get("status") != "hold_for_manual_review":
        raise SystemExit("Sparse workflow did not record hold_for_manual_review.")
    if (sparse_output_dir / "08-email-draft.json").exists():
        raise SystemExit("Sparse workflow must not generate an email draft.")

    bad_input_path = temp_root / "bad-evidence-input.json"
    bad_config_path = temp_root / "bad-workflow.json"
    bad_output_dir = temp_root / "bad-run"
    write_json(
        bad_input_path,
        {"lead": {"company_name": {"invalid": True}}, "evidence_bundle": {}},
    )
    write_json(bad_config_path, production_config("failed-delivery-regression", bad_input_path))
    failed = run_workflow(bad_config_path, bad_output_dir)
    if failed.returncode != 3:
        raise SystemExit("Malformed stage input should produce execution-failure code 3.")
    failed_manifest = load_json(bad_output_dir / "00-run-manifest.json")
    if failed_manifest.get("status") != "failed" or failed_manifest.get("current_stage") != "customer_intel":
        raise SystemExit("Execution failure was not recorded against the customer_intel stage.")
    evidence_path = bad_output_dir / "05-customer-intel-evidence-input.json"
    expected_evidence_hash = failed_manifest["artifact_sha256"]["customer_intel_evidence_input"]
    evidence_path.write_text(evidence_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    changed_evidence = run_workflow(bad_config_path, bad_output_dir, "--resume")
    if changed_evidence.returncode != 3:
        raise SystemExit("A changed materialized evidence input was accepted on resume.")
    changed_manifest = load_json(bad_output_dir / "00-run-manifest.json")
    if changed_manifest.get("current_stage") != "resume_validation":
        raise SystemExit("Changed evidence input was not attributed to resume_validation.")
    if changed_manifest["artifact_sha256"]["customer_intel_evidence_input"] != expected_evidence_hash:
        raise SystemExit("Resume validation replaced the recorded evidence-input hash.")


def assert_stale_approval_cannot_bypass_hash(temp_root: Path) -> None:
    config_path = temp_root / "stale-approval-workflow.json"
    output_dir = temp_root / "stale-approval-run"
    write_json(config_path, production_config("stale-approval-regression", SIEGER_INPUT))
    first = run_workflow(config_path, output_dir)
    if first.returncode != 10:
        raise SystemExit("Stale-approval test did not reach the review gate.")
    manifest = load_json(output_dir / "00-run-manifest.json")
    write_json(
        output_dir / "05-sales-angle-approval.json",
        {
            "contract_version": "1.0",
            "run_id": "stale-approval-regression",
            "report_sha256": manifest["review_report_sha256"],
            "angle_id": "ANGLE-01",
            "reviewer": "Stale Approval Fixture",
            "approved_at": "2026-08-25T00:00:00+00:00",
        },
    )
    report_path = output_dir / "06-customer-intel-report.json"
    report = load_json(report_path)
    report["tampered_after_review"] = True
    write_json(report_path, report)
    resumed = run_workflow(config_path, output_dir, "--resume")
    if resumed.returncode != 3:
        raise SystemExit("A stale approval file bypassed the reviewed-report hash check.")
    if (output_dir / "08-email-draft.json").exists():
        raise SystemExit("Stale approval plus a changed report generated an email draft.")

    invalid_config_path = temp_root / "invalid-angle-workflow.json"
    invalid_output_dir = temp_root / "invalid-angle-run"
    write_json(invalid_config_path, production_config("invalid-angle-regression", SIEGER_INPUT))
    if run_workflow(invalid_config_path, invalid_output_dir).returncode != 10:
        raise SystemExit("Invalid-angle test did not reach the review gate.")
    invalid = run_workflow(
        invalid_config_path,
        invalid_output_dir,
        "--resume",
        "--approved-sales-angle-id",
        "ANGLE-99",
        "--reviewer",
        "Regression Reviewer",
    )
    if invalid.returncode != 2:
        raise SystemExit("Unknown angle ID should be rejected as invalid approval input.")
    if (invalid_output_dir / "05-sales-angle-approval.json").exists():
        raise SystemExit("Unknown angle ID left a stale approval file behind.")


def assert_full_discovery_delivery_run(temp_root: Path) -> None:
    golden = load_json(SIEGER_INPUT)
    seller_context = {
        "company_name": "Authorized Test Supplier",
        "product_or_offer": "servo motors and gear motors",
        "product_categories": ["servo motors", "gear motors"],
        "target_customer_types": ["industrial automation equipment manufacturer", "system integrator"],
        "target_industries": ["industrial automation", "ASRS", "material handling"],
        "value_propositions": ["compatible replacement", "shorter lead time", "custom configuration"],
        "certifications": [],
        "proof_points": ["Authorized regression capability record."],
        "authorized_materials": ["test-fixture:authorized-seller-capability-record"],
        "excluded_customer_signals": [],
        "forbidden_claims": ["Do not claim current purchase intent or an existing supplier replacement project."],
    }
    query_one = "servo motors and gear motors India system integrator"
    query_two = "industrial automation India importer distributor brand buyer"
    query_three = "site:linkedin.com/company servo motors and gear motors India system integrator"
    fixtures = {
        query_one: [
            {
                "title": "SIEGER Global | Industrial Automation and Storage Systems",
                "url": "https://www.siegerglobal.net/",
                "snippet": "SIEGER manufactures textile automation, ASRS, material handling, sheet storage and automated parking systems in India.",
                "source": "fixture",
            }
        ],
        query_two: [
            {
                "title": "SIEGER ASTOR Automatic Storage Solutions",
                "url": "https://www.siegerglobal.net/storage-solutions.php",
                "snippet": "ASTOR includes ASRS, pallet shuttles, conveyors and WMS for industrial automation projects.",
                "source": "fixture",
            }
        ],
        query_three: [
            {
                "title": "SIEGER Global | LinkedIn",
                "url": "https://www.linkedin.com/company/sieger-global/",
                "snippet": "Industrial automation equipment manufacturer and system integrator serving global projects.",
                "source": "fixture",
            }
        ],
    }
    config = {
        "contract_version": "1.0",
        "run_id": "sieger-full-delivery-regression",
        "start_mode": "discovery",
        "lead_discovery": {
            "mode": "fixture",
            "selected_lead_id": "lead-001",
            "input": {
                "product_or_offer": "servo motors and gear motors",
                "target_market": "India",
                "customer_type": "system integrator",
                "industry_lens": "industrial",
                "seller_context": seller_context,
                "search_keywords": ["industrial automation"],
                "must_include": [],
                "exclude_terms": ["job", "recruitment"],
                "max_results": 5,
                "notes": "Delivery regression for an industrial automation target.",
            },
            "fixtures": fixtures,
        },
        "customer_intel": {
            "mode": "evidence",
            "evidence": golden["evidence_bundle"],
        },
        "outreach": {
            "email_type": "first_touch",
            "product_or_offer": "servo motors and gear motors",
            "sender_name": "Workflow Tester",
            "sender_company": "Authorized Test Supplier",
        },
        "exports": {"container_bundle": True, "feishu_sandbox": False},
    }
    config_path = temp_root / "full-discovery-workflow.json"
    output_dir = temp_root / "full-discovery-run"
    write_json(config_path, config)

    first = run_workflow(config_path, output_dir)
    if first.returncode != 10:
        raise SystemExit(f"Full discovery workflow did not reach approval wait: {first.stderr or first.stdout}")
    resumed = run_workflow(
        config_path,
        output_dir,
        "--resume",
        "--approved-sales-angle-id",
        "ANGLE-01",
        "--reviewer",
        "Regression Reviewer",
    )
    if resumed.returncode != 0:
        raise SystemExit(f"Full discovery workflow did not complete: {resumed.stderr or resumed.stdout}")
    manifest = load_json(output_dir / "00-run-manifest.json")
    required_stages = {"lead_discovery", "lead_screening", "customer_intel", "outreach_email", "exports"}
    if set(manifest.get("stages") or {}) != required_stages:
        raise SystemExit("Full discovery run did not record all five pipeline stages.")
    for stage in required_stages:
        stage_record = manifest["stages"].get(stage) or {}
        if stage_record.get("status") != "completed" or int(stage_record.get("attempt") or 0) < 1:
            raise SystemExit(f"Full discovery run did not record a completed attempt for {stage}.")
    if not (output_dir / "09-container-bundle.json").exists():
        raise SystemExit("Full discovery run did not produce the neutral container bundle.")
    assert_artifact_hash_coverage(
        output_dir,
        {
            "customer_intel_evidence_input",
            "outreach_email_markdown",
            "container_bundle",
            "container_bundle_markdown",
            "lead_workflow_csv",
        },
    )
    export_hash = manifest["artifact_sha256"]["lead_workflow_csv"]
    (output_dir / "11-lead-workflow.csv").unlink()
    missing_export = run_workflow(config_path, output_dir, "--resume")
    if missing_export.returncode != 3:
        raise SystemExit("Deleting a registered export artifact did not fail resume validation.")
    missing_export_manifest = load_json(output_dir / "00-run-manifest.json")
    if missing_export_manifest.get("current_stage") != "resume_validation":
        raise SystemExit("Missing export artifact was not attributed to resume_validation.")
    if missing_export_manifest["artifact_sha256"]["lead_workflow_csv"] != export_hash:
        raise SystemExit("Resume validation replaced the recorded hash for a missing export.")


def assert_follow_up_delivery_run(temp_root: Path) -> None:
    config = production_config("sieger-follow-up-regression", SIEGER_INPUT)
    config["outreach"]["email_type"] = "follow_up"
    config["outreach"]["previous_contact_context"] = (
        "We shared a short industrial automation component overview on 2026-08-20."
    )
    config_path = temp_root / "follow-up-workflow.json"
    output_dir = temp_root / "follow-up-run"
    write_json(config_path, config)

    first = run_workflow(config_path, output_dir)
    if first.returncode != 10:
        raise SystemExit("Follow-up workflow did not pause for report-bound angle approval.")
    resumed = run_workflow(
        config_path,
        output_dir,
        "--resume",
        "--approved-sales-angle-id",
        "ANGLE-01",
        "--reviewer",
        "Regression Reviewer",
    )
    if resumed.returncode != 0:
        raise SystemExit(f"Follow-up workflow did not complete: {resumed.stderr or resumed.stdout}")
    email_input = load_json(output_dir / "07-email-input.json")
    email_output = load_json(output_dir / "08-email-draft.json")
    if not email_input.get("previous_contact_context"):
        raise SystemExit("Follow-up context was not preserved into the email input.")
    email_text = json.dumps(email_output.get("drafts") or {}, ensure_ascii=False)
    if "Last time, I shared" not in email_text:
        raise SystemExit("Follow-up draft did not use the supplied previous-contact context.")


def assert_outputs_exist(output_dir: Path) -> None:
    missing = [name for name in EXPECTED_OUTPUTS if not (output_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing expected outputs: {', '.join(missing)}")


def assert_selected_lead_matches_fixture(output_dir: Path) -> None:
    selected = load_json(output_dir / "05-selected-customer-intel-input.json")
    report = load_json(output_dir / "06-customer-intel-report.json")
    fixture = load_json(FIXTURE_REPORT)

    selected_company = str(selected.get("company_name", "")).strip()
    report_company = str((report.get("identity_snapshot") or {}).get("company_name", "")).strip()
    fixture_company = str((fixture.get("identity_snapshot") or {}).get("company_name", "")).strip()

    if not selected_company or not report_company:
        raise SystemExit("Selected lead or generated report is missing company_name.")
    if selected_company != report_company or report_company != fixture_company:
        raise SystemExit(
            "Mismatch between selected lead, generated report, and combo-package fixture."
        )

    required_sieger_keys = {
        "verdict_card",
        "company_business_breakdown",
        "tech_capability_procurement_concerns",
        "scale_financial_signals",
        "sales_model_procurement_logic",
        "competition_map",
        "growth_opportunities",
        "image_summary",
        "sieger_standard",
    }
    if not required_sieger_keys.issubset(report):
        missing = ", ".join(sorted(required_sieger_keys - set(report)))
        raise SystemExit(f"Customer-intel report is missing SIEGER keys: {missing}")
    stable_angle_keys = {"cn", "en", "why", "avoid"}
    angle = (report.get("sales_angles") or [{}])[0]
    if not stable_angle_keys.issubset(angle):
        raise SystemExit("Customer-intel sales angle lost a stable downstream key.")
    if angle.get("approval_status") != "approved" or not angle.get("angle_id"):
        raise SystemExit("Stable combo fixture must include one explicitly approved sales angle.")
    if not report.get("evidence_ledger") or not report.get("claim_ledger"):
        raise SystemExit("Stable combo fixture must carry the v2 evidence and claim ledgers.")


def assert_email_artifacts(output_dir: Path) -> None:
    email_input = load_json(output_dir / "07-email-input.json")
    email_output = load_json(output_dir / "08-email-draft.json")
    email_markdown = (output_dir / "08-email-draft.md").read_text(encoding="utf-8")

    if str(email_input.get("company_name", "")).strip() != "GreenHarvest Foods":
        raise SystemExit("Email bridge payload company_name does not match the stable combo demo.")
    if "subject_options" not in email_output:
        raise SystemExit("Email draft JSON is missing subject_options.")
    if email_output.get("send_policy") != "manual_review_only":
        raise SystemExit("Email draft JSON should declare manual_review_only send policy.")
    source_context = email_input.get("source_context") or {}
    if source_context.get("draft_authorization") != "approved":
        raise SystemExit("Email bridge payload should carry explicit draft authorization.")
    if not (source_context.get("selected_sales_angle") or {}).get("angle_id"):
        raise SystemExit("Email bridge payload should carry the approved sales angle object.")
    if not source_context.get("selected_evidence") or not source_context.get("selected_claims"):
        raise SystemExit("Email bridge payload should preserve selected claims and evidence.")
    if not source_context.get("recent_signals") or not source_context.get("market_signals"):
        raise SystemExit("Email bridge payload should carry recent and market signals from customer intel.")
    if not source_context.get("verdict_card") or not source_context.get("sieger_standard"):
        raise SystemExit("Email bridge payload should carry optional SIEGER review context.")
    if "GreenHarvest Foods" not in email_markdown:
        raise SystemExit("Email draft markdown does not mention the expected company.")
    if "approved_angle_id: ANGLE-01" not in email_markdown:
        raise SystemExit("Email draft markdown should expose the approved angle ID.")
    if "Recommended Next Action: ready_for_manual_send" not in email_markdown:
        raise SystemExit("Email draft markdown should expose the workflow guidance section.")


def assert_container_bundle(output_dir: Path) -> None:
    bundle = load_json(output_dir / "09-container-bundle.json")
    markdown = (output_dir / "10-container-bundle.md").read_text(encoding="utf-8")
    csv_text = (output_dir / "11-lead-workflow.csv").read_text(encoding="utf-8")
    handoff = bundle.get("handoff_contract") or {}

    if bundle.get("data_containers", {}).get("classroom_sandbox") != "feishu":
        raise SystemExit("Container bundle should declare Feishu as the classroom sandbox adapter.")
    if "LeadRecord" not in handoff.get("core_entities", []):
        raise SystemExit("Container bundle should expose the shared core entities.")
    if handoff.get("enterprise_table_policy", {}).get("mode") != "adapt_existing_or_create_minimal":
        raise SystemExit("Container bundle should expose the enterprise table adaptation policy.")
    if handoff.get("skill_rule_capture_policy", {}).get("mode") != "ask_before_skill_update":
        raise SystemExit("Container bundle should expose the ask-before-skill-update capture policy.")
    if "## Data Containers" not in markdown:
        raise SystemExit("Container bundle markdown is missing the data container summary.")
    if "recommended_next_action" not in csv_text or "legacy_recommended_next_action" not in csv_text:
        raise SystemExit("Lead workflow CSV is missing the expected contract columns.")


def assert_feishu_bundle(output_dir: Path) -> None:
    bundle = load_json(output_dir / "12-feishu-sandbox-bundle.json")
    install_contract = bundle.get("openclaw_install_contract") or {}
    workspace_container = bundle.get("workspace_container") or {}
    stage_assets = bundle.get("stage_assets") or {}
    master_records = bundle.get("master_records") or []
    handoff = bundle.get("openclaw_handoff") or {}

    required_stages = {"lead_discovery", "lead_screening", "customer_intel", "outreach_email"}
    if set(stage_assets) != required_stages:
        raise SystemExit("Feishu bundle is missing one or more stage assets.")
    if len(master_records) != 3:
        raise SystemExit("Feishu master records should include all 3 demo leads.")
    if workspace_container.get("container_type") != "single_base_workspace":
        raise SystemExit("Feishu bundle should declare a single-base workspace container.")
    if not workspace_container.get("forbid_parallel_bases_for_each_stage"):
        raise SystemExit("Feishu bundle should explicitly forbid creating parallel bases for each stage.")
    if workspace_container.get("workspace_owner_skill") != "trade-active-outreach-combo":
        raise SystemExit("Feishu bundle should declare the combo package as the workspace owner skill.")
    if not workspace_container.get("single_skill_attach_only"):
        raise SystemExit("Feishu bundle should force single-skill runs into attach-only mode.")
    if not workspace_container.get("forbid_stage_level_base_bootstrap"):
        raise SystemExit("Feishu bundle should forbid stage-level base bootstrap.")

    if install_contract.get("container_owner") != "active_outreach_combo":
        raise SystemExit("Install contract should declare the combo package as the container owner.")
    if install_contract.get("container_mode") != "single_base_multi_table":
        raise SystemExit("Feishu sandbox compatibility install contract should declare single_base_multi_table mode.")
    if install_contract.get("single_skill_policy") != "attach_only":
        raise SystemExit("Install contract should require attach_only for single-skill runs.")
    workflow_owner = install_contract.get("workflow_owner") or {}
    if workflow_owner.get("skill_name") != "trade-active-outreach-combo":
        raise SystemExit("Install contract should declare trade-active-outreach-combo as workflow owner.")
    worker_names = {item.get("skill_name") for item in install_contract.get("stage_workers") or []}
    if worker_names != {
        "trade-lead-discovery-openclaw",
        "trade-lead-screening-openclaw",
        "trade-customer-intel-for-openclaw",
        "trade-outreach-email-for-openclaw",
    }:
        raise SystemExit("Install contract should enumerate all four stage workers.")
    for worker in install_contract.get("stage_workers") or []:
        if worker.get("feishu_container_creation") != "forbidden":
            raise SystemExit("Stage workers must explicitly forbid Feishu container creation.")
        if not worker.get("requires_master_base") or not worker.get("requires_master_record"):
            raise SystemExit("Stage workers must require the master base and master record.")

    table_names = {item.get("table_name") for item in workspace_container.get("tables") or []}
    if table_names != {"Lead Workflow Master", "Lead Discovery Results", "Lead Screening Results"}:
        raise SystemExit("Workspace container is missing one or more required Feishu tables.")

    for stage_name, payload in stage_assets.items():
        runtime_contract = payload.get("feishu_runtime_contract") or {}
        if runtime_contract.get("workspace_owner_skill") != "trade-active-outreach-combo":
            raise SystemExit(f"{stage_name} payload should point back to the combo workspace owner.")
        if runtime_contract.get("feishu_container_creation") != "forbidden":
            raise SystemExit(f"{stage_name} payload should not imply independent container creation.")
        if not runtime_contract.get("requires_master_base") or not runtime_contract.get("requires_master_record"):
            raise SystemExit(f"{stage_name} payload should require the master base and master record.")

    selected = next((item for item in master_records if item.get("lead_id") == "lead-002"), None)
    if not selected:
        raise SystemExit("Selected lead is missing from Feishu master records.")
    if selected.get("current_stage") != "outreach_email" or selected.get("current_status") != "draft_ready":
        raise SystemExit("Selected lead did not progress to outreach_email/draft_ready in the master records.")
    if selected.get("recommended_next_action") != "ready_for_customer_intel":
        raise SystemExit("Selected lead should keep the screening next action in the master records.")
    if "search_asset_ref" not in selected or "intel_asset_ref" not in selected or "email_asset_ref" not in selected:
        raise SystemExit("Master records should use text asset_ref fields instead of URL-only fields.")
    intel_payload = stage_assets.get("customer_intel") or {}
    intel_fields = intel_payload.get("table_fields") or {}
    if not intel_fields.get("top_recent_signal") or not intel_fields.get("top_market_signal"):
        raise SystemExit("Customer-intel payload should expose top recent and market signals.")

    waiting_lead = next((item for item in master_records if item.get("lead_id") == "lead-001"), None)
    if not waiting_lead:
        raise SystemExit("A non-selected waiting lead is missing from Feishu master records.")
    asset_keys = json.loads(waiting_lead.get("asset_keys", "{}"))
    if "intel" in asset_keys or "email" in asset_keys:
        raise SystemExit("Non-selected leads should not receive intel/email assets in the stable demo.")
    if waiting_lead.get("search_asset_ref") != "search-record:demo-run:lead-001":
        raise SystemExit("Lead-001 search_asset_ref should point to the stable search asset key.")
    if waiting_lead.get("current_status") != "waiting_selection":
        raise SystemExit("Lead-001 should remain in waiting_selection state.")

    failure_policy = handoff.get("failure_writeback_policy") or {}
    rerun_policy = handoff.get("rerun_policy") or {}
    attach_rules = handoff.get("single_skill_attach_rules") or []
    if not failure_policy.get("always_write_master_status"):
        raise SystemExit("Feishu bundle should require master writeback even when stage execution fails.")
    if "master_record" not in rerun_policy:
        raise SystemExit("Feishu bundle rerun policy should describe master-record reuse.")
    if len(attach_rules) < 3:
        raise SystemExit("Feishu bundle should describe how single-skill runs attach back to the master table.")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="trade-skill-combo-check-") as temp_dir:
        temp_root = Path(temp_dir)
        output_dir = temp_root / "demo"
        run_demo(output_dir)
        assert_outputs_exist(output_dir)
        assert_selected_lead_matches_fixture(output_dir)
        assert_email_artifacts(output_dir)
        assert_container_bundle(output_dir)
        assert_feishu_bundle(output_dir)
        assert_production_pause_resume(temp_root)
        assert_registered_artifact_removal_rejected(temp_root)
        assert_fresh_stale_approval_rejection(temp_root)
        assert_discovery_reviewed_report_materialization(temp_root)
        assert_discovery_reviewed_report_requires_corroboration(temp_root)
        assert_source_snapshots_reject_changed_contents(temp_root)
        assert_approval_transaction_recovery(temp_root)
        assert_multi_file_commit_recovery(temp_root)
        assert_commit_cleanup_failure_recovery(temp_root)
        assert_export_failure_does_not_repeat_email(temp_root)
        assert_production_hold_and_failure(temp_root)
        assert_stale_approval_cannot_bypass_hash(temp_root)
        assert_full_discovery_delivery_run(temp_root)
        assert_follow_up_delivery_run(temp_root)

    print("Combo package demo and production regression checks passed.")


if __name__ == "__main__":
    main()
