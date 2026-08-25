#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PACKAGE_ROOT.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

LOCAL_SUBSKILL_ROOT = PACKAGE_ROOT / "子Skill与工具本体"
REQUIRED_SKILL_DIRS = ["客户搜索skill", "线索整理skill", "客户背调skill", "开发信skill"]


def resolve_skill_root() -> Path:
    if all((LOCAL_SUBSKILL_ROOT / name).is_dir() for name in REQUIRED_SKILL_DIRS):
        return LOCAL_SUBSKILL_ROOT
    return WORKSPACE_ROOT


SKILL_ROOT = resolve_skill_root()
SEARCH_SKILL = SKILL_ROOT / "客户搜索skill"
SCREENING_SKILL = SKILL_ROOT / "线索整理skill"
INTEL_SKILL = SKILL_ROOT / "客户背调skill"
EMAIL_SKILL = SKILL_ROOT / "开发信skill"

from export_feishu_workflow_bundle import export_default_artifacts


class WorkflowConfigError(ValueError):
    pass


class StageExecutionError(RuntimeError):
    def __init__(self, stage: str, message: str, returncode: int = 1):
        super().__init__(message)
        self.stage = stage
        self.returncode = returncode


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowConfigError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowConfigError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise WorkflowConfigError(f"Expected a JSON object in {path}.")
    return payload


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(path)


def fresh_temp_path(path: Path) -> Path:
    temp_path = path.with_suffix(path.suffix + ".stage-tmp")
    if temp_path.exists():
        temp_path.unlink()
    return temp_path


TRANSACTION_MARKER_NAME = ".stage-transaction.json"


def transaction_marker_path(pairs: list[tuple[Path, Path]]) -> Path:
    parents = {final.parent.resolve() for _, final in pairs}
    if len(parents) != 1:
        raise StageExecutionError(
            "stage_commit",
            "Stage outputs must share one output directory for transactional commit.",
        )
    return next(iter(parents)) / TRANSACTION_MARKER_NAME


def transaction_paths(transaction: dict[str, Any]) -> list[dict[str, Any]]:
    pairs = transaction.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise OSError("Stage transaction marker has no output pairs.")
    normalized: list[dict[str, Any]] = []
    for pair in pairs:
        if not isinstance(pair, dict):
            raise OSError("Stage transaction marker contains an invalid pair.")
        normalized.append(pair)
    return normalized


def finish_transaction(marker_path: Path, transaction: dict[str, Any]) -> None:
    backup_dir = Path(str(transaction.get("backup_dir") or ""))
    if backup_dir.is_dir():
        shutil.rmtree(backup_dir)
    if marker_path.exists():
        marker_path.unlink()


def rollback_transaction(marker_path: Path, transaction: dict[str, Any]) -> None:
    transaction["phase"] = "rolling_back"
    try:
        atomic_write_json(marker_path, transaction)
    except OSError:
        # The original marker is still useful if this status write is interrupted.
        pass
    for pair in reversed(transaction_paths(transaction)):
        final = Path(str(pair["final"]))
        temp = Path(str(pair["temp"]))
        backup = Path(str(pair["backup"]))
        had_final = bool(pair.get("had_final"))
        if backup.exists():
            if final.exists():
                final.unlink()
            backup.replace(final)
        elif not had_final and final.exists():
            final.unlink()
        if temp.exists():
            temp.unlink()
    backup_dir = Path(str(transaction.get("backup_dir") or ""))
    if backup_dir.is_dir():
        shutil.rmtree(backup_dir)
    if marker_path.exists():
        marker_path.unlink()


def commit_stage_outputs(stage: str, pairs: list[tuple[Path, Path]]) -> None:
    missing = [str(temp) for temp, _ in pairs if not temp.exists()]
    if missing:
        raise StageExecutionError(stage, f"Stage completed without expected outputs: {', '.join(missing)}")
    if not pairs:
        raise StageExecutionError(stage, "Stage completed without expected outputs.")
    marker_path = transaction_marker_path(pairs)
    if marker_path.exists():
        raise StageExecutionError(
            stage,
            f"A previous stage commit is still recoverable at {marker_path}; resume to recover it.",
        )
    output_dir = marker_path.parent
    backup_dir = output_dir / f".stage-backup-{uuid.uuid4().hex}"
    transaction: dict[str, Any] = {
        "version": 1,
        "stage": stage,
        "phase": "prepared",
        "backup_dir": str(backup_dir),
        "pairs": [
            {
                "temp": str(temp.resolve()),
                "final": str(final.resolve()),
                "backup": str((backup_dir / f"{index}-{final.name}").resolve()),
                "had_final": final.exists(),
            }
            for index, (temp, final) in enumerate(pairs)
        ],
    }
    try:
        atomic_write_json(marker_path, transaction)
        backup_dir.mkdir(parents=True, exist_ok=True)
        transaction["phase"] = "backing_up"
        atomic_write_json(marker_path, transaction)
        for pair in transaction_paths(transaction):
            final = Path(str(pair["final"]))
            backup = Path(str(pair["backup"]))
            final.parent.mkdir(parents=True, exist_ok=True)
            if final.exists():
                final.replace(backup)
        transaction["phase"] = "committing"
        atomic_write_json(marker_path, transaction)
        for pair in transaction_paths(transaction):
            temp = Path(str(pair["temp"]))
            final = Path(str(pair["final"]))
            temp.replace(final)
        transaction["phase"] = "committed"
        atomic_write_json(marker_path, transaction)
        finish_transaction(marker_path, transaction)
    except StageExecutionError:
        raise
    except OSError as exc:
        if transaction.get("phase") == "committed":
            raise StageExecutionError(
                stage,
                f"Stage commit completed but backup cleanup was interrupted; resume to finish recovery: {exc}",
            ) from exc
        try:
            rollback_transaction(marker_path, transaction)
        except OSError as rollback_exc:
            transaction["phase"] = "rollback_pending"
            try:
                atomic_write_json(marker_path, transaction)
            except OSError:
                pass
            raise StageExecutionError(
                stage,
                f"Atomic stage commit failed; recovery marker retained at {marker_path}: {exc}; rollback failed: {rollback_exc}",
            ) from exc
        raise StageExecutionError(stage, f"Atomic stage commit failed and was rolled back: {exc}") from exc


def cleanup_stage_temps(output_dir: Path) -> None:
    if not output_dir.is_dir():
        return
    for path in output_dir.glob("*.stage-tmp"):
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass


def recover_interrupted_commits(output_dir: Path) -> None:
    if not output_dir.is_dir():
        return
    marker_path = output_dir / TRANSACTION_MARKER_NAME
    if marker_path.exists():
        try:
            transaction = load_json(marker_path)
            phase = str(transaction.get("phase") or "")
            if phase == "committed":
                finish_transaction(marker_path, transaction)
            else:
                rollback_transaction(marker_path, transaction)
        except (OSError, WorkflowConfigError, KeyError, TypeError, ValueError) as exc:
            raise StageExecutionError(
                "resume_recovery",
                f"Could not recover interrupted stage commit at {marker_path}: {exc}",
            ) from exc
    for backup in output_dir.glob("*.stage-backup"):
        final_name = backup.name.removesuffix(".stage-backup")
        final = backup.with_name(final_name)
        try:
            if final.exists():
                final.unlink()
            backup.replace(final)
        except OSError as exc:
            raise StageExecutionError(
                "resume_recovery",
                f"Could not recover legacy stage backup {backup}: {exc}",
            ) from exc
    cleanup_stage_temps(output_dir)
    export_temp_dir = output_dir / ".exports-stage-tmp"
    if export_temp_dir.is_dir():
        try:
            shutil.rmtree(export_temp_dir)
        except OSError as exc:
            raise StageExecutionError(
                "resume_recovery",
                f"Could not remove interrupted export staging directory: {exc}",
            ) from exc


def config_hash(config: dict[str, Any]) -> str:
    encoded = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_payload_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json_source(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkflowConfigError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise WorkflowConfigError(f"Expected a JSON object in {path}.")
    return payload, hashlib.sha256(raw).hexdigest()


def resolve_path(config_dir: Path, value: Any, field_name: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowConfigError(f"{field_name} must be a non-empty path.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = config_dir / path
    return path.resolve()


def materialize_object(
    section: dict[str, Any],
    *,
    inline_key: str,
    path_key: str,
    destination: Path,
    config_dir: Path,
    manifest: dict[str, Any],
    resume: bool,
    source_key: str,
) -> dict[str, Any]:
    sources = manifest.setdefault("sources", {})
    source_record = sources.get(source_key)
    source_path: Path | None = None
    if section.get(path_key):
        source_path = resolve_path(config_dir, section[path_key], path_key)

    if resume:
        if not isinstance(source_record, dict):
            raise StageExecutionError(
                "resume_validation",
                f"Materialized source '{source_key}' has no recorded source SHA-256.",
            )
        if source_path is not None:
            try:
                current_sha = file_sha256(source_path)
            except OSError as exc:
                raise StageExecutionError(
                    "resume_validation",
                    f"Registered source is unavailable: {source_path}",
                ) from exc
            if source_record.get("kind") != "path" or source_record.get("path") != str(source_path):
                raise StageExecutionError(
                    "resume_validation",
                    f"Registered source path changed for '{source_key}'.",
                )
        elif isinstance(section.get(inline_key), dict):
            current_sha = json_payload_sha256(section[inline_key])
            if source_record.get("kind") != "inline":
                raise StageExecutionError(
                    "resume_validation",
                    f"Registered source kind changed for '{source_key}'.",
                )
        else:
            raise WorkflowConfigError(f"Provide either {inline_key} or {path_key}.")
        if source_record.get("sha256") != current_sha:
            source_label = str(source_path or inline_key)
            raise StageExecutionError(
                "resume_validation",
                f"Registered source contents changed: {source_label}",
            )
        if not destination.is_file():
            raise StageExecutionError(
                "resume_validation",
                f"Materialized source snapshot is missing: {destination.name}",
            )
        return load_json(destination)

    inline = section.get(inline_key)
    if isinstance(inline, dict):
        payload = inline
        source_record = {
            "kind": "inline",
            "sha256": json_payload_sha256(payload),
            "materialized_artifact": destination.name,
        }
    elif source_path is not None:
        payload, source_sha = load_json_source(source_path)
        source_record = {
            "kind": "path",
            "path": str(source_path),
            "sha256": source_sha,
            "materialized_artifact": destination.name,
        }
    else:
        raise WorkflowConfigError(f"Provide either {inline_key} or {path_key}.")
    if destination.exists():
        raise WorkflowConfigError(
            f"Cannot overwrite an existing materialized source snapshot: {destination}"
        )
    atomic_write_json(destination, payload)
    sources[source_key] = source_record
    return payload


def run_stage(stage: str, args: list[str]) -> None:
    env = os.environ.copy()
    python_path_parts = [str(WORKSPACE_ROOT), str(SKILL_ROOT)]
    if env.get("PYTHONPATH"):
        python_path_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_path_parts)
    completed = subprocess.run(
        args,
        cwd=WORKSPACE_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return
    detail = (completed.stderr or completed.stdout or "stage failed without output").strip()
    raise StageExecutionError(stage, detail[-3000:], completed.returncode)


def stage_record(
    status: str,
    artifact: str = "",
    note: str = "",
    *,
    attempt: int = 1,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "attempt": attempt,
        "exit_code": 0 if status in {"completed", "skipped"} else None,
        "updated_at": utc_now(),
    }
    if artifact:
        payload["artifact"] = artifact
    if note:
        payload["note"] = note
    return payload


def begin_stage(manifest_path: Path, manifest: dict[str, Any], stage: str) -> None:
    stages = manifest.setdefault("stages", {})
    previous = stages.get(stage) or {}
    attempt = int(previous.get("attempt") or 0) + 1
    stages[stage] = stage_record("running", attempt=attempt)
    manifest.update(
        {
            "status": "running",
            "current_stage": stage,
            "next_action": f"执行 {stage} 阶段。",
            "error": None,
            "exit_code": None,
        }
    )
    save_manifest(manifest_path, manifest)


def complete_stage(
    manifest: dict[str, Any],
    stage: str,
    *,
    artifact: str = "",
    note: str = "",
    status: str = "completed",
) -> None:
    previous = (manifest.setdefault("stages", {}).get(stage) or {})
    attempt = max(1, int(previous.get("attempt") or 0))
    manifest["stages"][stage] = stage_record(
        status,
        artifact,
        note,
        attempt=attempt,
    )


def register_artifact(manifest: dict[str, Any], key: str, path: Path) -> None:
    manifest.setdefault("artifacts", {})[key] = path.name
    if path.is_file():
        manifest.setdefault("artifact_sha256", {})[key] = file_sha256(path)


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    output_dir = Path(str(manifest.get("output_dir") or path.parent))
    artifact_hashes = manifest.setdefault("artifact_sha256", {})
    for key, relative_path in (manifest.get("artifacts") or {}).items():
        artifact_path = output_dir / str(relative_path)
        if key not in artifact_hashes and artifact_path.is_file():
            artifact_hashes[key] = file_sha256(artifact_path)
    atomic_write_json(path, manifest)


def validate_recorded_artifacts(manifest: dict[str, Any], output_dir: Path) -> None:
    hashes = manifest.get("artifact_sha256") or {}
    if not isinstance(hashes, dict):
        raise StageExecutionError("resume_validation", "Recorded artifact hashes are not an object.")
    for key, relative_path in (manifest.get("artifacts") or {}).items():
        artifact_path = output_dir / str(relative_path)
        expected_hash = str(hashes.get(key) or "")
        if not artifact_path.is_file():
            raise StageExecutionError("resume_validation", f"Recorded artifact is missing: {relative_path}")
        if not expected_hash:
            raise StageExecutionError("resume_validation", f"Recorded artifact has no SHA-256: {relative_path}")
        if file_sha256(artifact_path) != expected_hash:
            raise StageExecutionError("resume_validation", f"Recorded artifact changed: {relative_path}")


def validate_recorded_sources(manifest: dict[str, Any]) -> None:
    sources = manifest.get("sources") or {}
    if not isinstance(sources, dict):
        raise StageExecutionError("resume_validation", "Recorded sources are not an object.")
    for source_key, record in sources.items():
        if not isinstance(record, dict):
            raise StageExecutionError(
                "resume_validation",
                f"Recorded source is invalid: {source_key}",
            )
        if record.get("kind") != "path":
            continue
        source_path = Path(str(record.get("path") or ""))
        expected_hash = str(record.get("sha256") or "")
        if not source_path.is_file() or not expected_hash:
            raise StageExecutionError(
                "resume_validation",
                f"Recorded source is unavailable or has no SHA-256: {source_key}",
            )
        try:
            current_hash = file_sha256(source_path)
        except OSError as exc:
            raise StageExecutionError(
                "resume_validation",
                f"Could not read registered source: {source_path}",
            ) from exc
        if current_hash != expected_hash:
            raise StageExecutionError(
                "resume_validation",
                f"Registered source contents changed: {source_path}",
            )


def stage_completed(manifest: dict[str, Any], stage: str, required_paths: list[Path]) -> bool:
    record = (manifest.get("stages") or {}).get(stage) or {}
    return record.get("status") == "completed" and all(path.is_file() for path in required_paths)


def stop_with_status(
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    status: str,
    current_stage: str,
    next_action: str,
    exit_code: int,
) -> int:
    manifest.update(
        {
            "status": status,
            "current_stage": current_stage,
            "next_action": next_action,
            "exit_code": exit_code,
        }
    )
    save_manifest(manifest_path, manifest)
    print(json.dumps({"status": status, "manifest": str(manifest_path)}, ensure_ascii=False))
    return exit_code


def selected_customer_intel_input(screening_output_path: Path, selected_lead_id: str) -> dict[str, Any]:
    screening_output = load_json(screening_output_path)
    for lead in screening_output.get("leads") or []:
        if lead.get("lead_id") != selected_lead_id:
            continue
        if lead.get("recommended_next_action") != "ready_for_customer_intel":
            raise StageExecutionError(
                "lead_screening",
                f"Lead '{selected_lead_id}' is not ready for customer intel.",
            )
        payload = lead.get("customer_intel_input") or {}
        if not isinstance(payload, dict) or not payload:
            raise StageExecutionError(
                "lead_screening",
                f"Lead '{selected_lead_id}' has no customer_intel_input payload.",
            )
        return payload
    raise StageExecutionError("lead_screening", f"Lead '{selected_lead_id}' was not found.")


def company_name_from_input(payload: dict[str, Any]) -> str:
    return str(payload.get("company_name") or "").strip()


def company_name_from_report(payload: dict[str, Any]) -> str:
    return str((payload.get("identity_snapshot") or {}).get("company_name") or "").strip()


def normalized_company_name(value: str) -> str:
    return " ".join(value.split()).casefold()


def normalized_market(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def normalized_domain(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urllib.parse.urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").strip().casefold().rstrip(".")
    return host.removeprefix("www.")


def entity_domain_from_payload(payload: dict[str, Any], *, report: bool = False) -> str:
    identity = payload.get("identity_snapshot") if report else None
    identity = identity if isinstance(identity, dict) else {}
    values = [
        identity.get("website"),
        identity.get("domain"),
        identity.get("email_domain"),
        payload.get("company_website"),
        payload.get("website"),
        payload.get("domain"),
        payload.get("email_domain"),
    ]
    for value in values:
        domain = normalized_domain(value)
        if domain:
            return domain
    return ""


def entity_market_from_payload(payload: dict[str, Any], *, report: bool = False) -> str:
    identity = payload.get("identity_snapshot") if report else None
    identity = identity if isinstance(identity, dict) else {}
    values = [
        identity.get("country_or_market"),
        identity.get("market"),
        identity.get("target_market"),
        payload.get("country_or_market"),
        payload.get("market"),
        payload.get("target_market"),
    ]
    for value in values:
        market = normalized_market(value)
        if market:
            return market
    return ""


def require_company_match(lead: dict[str, Any], report: dict[str, Any]) -> None:
    lead_company = company_name_from_input(lead)
    report_company = company_name_from_report(report)
    if not lead_company or not report_company:
        raise StageExecutionError(
            "customer_intel",
            "Selected lead and customer-intel report must both contain company_name.",
        )
    if normalized_company_name(lead_company) != normalized_company_name(report_company):
        raise StageExecutionError(
            "customer_intel",
            f"Customer-intel report company '{report_company}' does not match selected lead '{lead_company}'.",
        )
    lead_domain = entity_domain_from_payload(lead)
    report_domain = entity_domain_from_payload(report, report=True)
    if lead_domain:
        if not report_domain:
            raise StageExecutionError(
                "customer_intel",
                f"Customer-intel report is missing a corroborating domain for selected lead domain '{lead_domain}'.",
            )
        if report_domain != lead_domain:
            raise StageExecutionError(
                "customer_intel",
                f"Customer-intel report domain '{report_domain}' does not match selected lead domain '{lead_domain}'.",
            )
    lead_market = entity_market_from_payload(lead)
    report_market = entity_market_from_payload(report, report=True)
    if lead_market:
        if not report_market:
            raise StageExecutionError(
                "customer_intel",
                f"Customer-intel report is missing a corroborating market for selected lead market '{lead_market}'.",
            )
        if report_market != lead_market:
            raise StageExecutionError(
                "customer_intel",
                f"Customer-intel report market '{report_market}' does not match selected lead market '{lead_market}'.",
            )


def approve_angle(report_path: Path, angle_id: str) -> dict[str, Any]:
    report = load_json(report_path)
    action = (report.get("intel_decision") or {}).get("recommended_next_action")
    if action != "ready_for_email_draft":
        raise StageExecutionError("customer_intel", "Intel gates do not allow sales-angle approval.")
    require_sales_angle(report, angle_id)
    selected = None
    for angle in report.get("sales_angles") or []:
        if angle.get("angle_id") == angle_id:
            selected = angle
        angle["approval_status"] = "approved" if angle.get("angle_id") == angle_id else "proposed"
    if selected is None:
        available = [item.get("angle_id") for item in report.get("sales_angles") or [] if item.get("angle_id")]
        raise WorkflowConfigError(
            f"Sales angle '{angle_id}' was not found. Available angles: {', '.join(available) or 'none'}"
        )
    atomic_write_json(report_path, report)
    return report


def require_sales_angle(report: dict[str, Any], angle_id: str) -> None:
    if any(
        isinstance(angle, dict) and angle.get("angle_id") == angle_id
        for angle in report.get("sales_angles") or []
    ):
        return
    available = [
        item.get("angle_id")
        for item in report.get("sales_angles") or []
        if isinstance(item, dict) and item.get("angle_id")
    ]
    raise WorkflowConfigError(
        f"Sales angle '{angle_id}' was not found. Available angles: {', '.join(available) or 'none'}"
    )


def approved_angle_id(report: dict[str, Any]) -> str:
    for angle in report.get("sales_angles") or []:
        if angle.get("approval_status") == "approved" and angle.get("angle_id"):
            return str(angle["angle_id"])
    return ""


def proposed_report_sha256(report: dict[str, Any]) -> str:
    normalized = json.loads(json.dumps(report, ensure_ascii=False))
    for angle in normalized.get("sales_angles") or []:
        if isinstance(angle, dict):
            angle["approval_status"] = "proposed"
    encoded = (json.dumps(normalized, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def supplied_approval_record(
    *,
    config: dict[str, Any],
    config_dir: Path,
    review_report_hash: str,
    approval_override: str,
    reviewer: str,
    approval_json: str,
) -> dict[str, Any] | None:
    if approval_json.strip():
        return load_json(resolve_path(config_dir, approval_json, "approval_json"))
    if not approval_override.strip():
        return None
    if not reviewer.strip():
        raise WorkflowConfigError("--reviewer is required with --approved-sales-angle-id.")
    return {
        "contract_version": "1.0",
        "run_id": str(config["run_id"]),
        "report_sha256": review_report_hash,
        "angle_id": approval_override.strip(),
        "reviewer": reviewer.strip(),
        "approved_at": utc_now(),
    }


def validate_approval_record(
    approval_record: dict[str, Any],
    *,
    run_id: str,
    review_report_hash: str,
) -> None:
    required_fields = {
        "contract_version",
        "run_id",
        "report_sha256",
        "angle_id",
        "reviewer",
        "approved_at",
    }
    missing_fields = [
        key for key in required_fields if not str(approval_record.get(key) or "").strip()
    ]
    if missing_fields:
        raise WorkflowConfigError(f"Approval record is missing: {', '.join(sorted(missing_fields))}")
    if approval_record.get("contract_version") != "1.0":
        raise WorkflowConfigError("Approval contract_version must be '1.0'.")
    if approval_record.get("run_id") != run_id:
        raise WorkflowConfigError("Approval run_id does not match this workflow run.")
    if approval_record.get("report_sha256") != review_report_hash:
        raise WorkflowConfigError("Approval report_sha256 does not match the reviewed report.")


def recover_pending_approval(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    customer_intel_report_path: Path,
    approval_path: Path,
) -> None:
    approval_record = manifest.get("pending_approval")
    if not isinstance(approval_record, dict):
        return
    review_report_hash = str(manifest.get("review_report_sha256") or "")
    validate_approval_record(
        approval_record,
        run_id=str(manifest.get("run_id") or ""),
        review_report_hash=review_report_hash,
    )
    report = load_json(customer_intel_report_path)
    angle_id = str(approval_record["angle_id"])
    existing_angle_id = approved_angle_id(report)
    if existing_angle_id:
        if existing_angle_id != angle_id or proposed_report_sha256(report) != review_report_hash:
            raise StageExecutionError(
                "approval_recovery",
                "Pending approval does not match the current approved report.",
            )
    else:
        if file_sha256(customer_intel_report_path) != review_report_hash:
            raise StageExecutionError(
                "approval_recovery",
                "Pending approval cannot be applied because the reviewed report changed.",
            )
        approve_angle(customer_intel_report_path, angle_id)
    atomic_write_json(approval_path, approval_record)
    approved_hash = file_sha256(customer_intel_report_path)
    manifest["approved_report_sha256"] = approved_hash
    manifest["approval_record"] = approval_path.name
    manifest.setdefault("artifacts", {})["sales_angle_approval"] = approval_path.name
    manifest.setdefault("artifact_sha256", {})["customer_intel"] = approved_hash
    manifest.pop("pending_approval", None)
    manifest.update(
        {
            "status": "running",
            "current_stage": "customer_intel",
            "next_action": "继续生成开发信草稿。",
            "error": None,
            "exit_code": None,
        }
    )
    save_manifest(manifest_path, manifest)


def validate_config(config: dict[str, Any]) -> None:
    if config.get("contract_version") != "1.0":
        raise WorkflowConfigError("contract_version must be '1.0'.")
    if not str(config.get("run_id") or "").strip():
        raise WorkflowConfigError("run_id is required.")
    if config.get("start_mode") not in {"discovery", "customer_intel"}:
        raise WorkflowConfigError("start_mode must be discovery or customer_intel.")
    intel = config.get("customer_intel")
    if not isinstance(intel, dict) or intel.get("mode") not in {"live_web", "evidence", "reviewed_report"}:
        raise WorkflowConfigError(
            "customer_intel.mode must be live_web, evidence, or reviewed_report."
        )
    if str(intel.get("approved_sales_angle_id") or "").strip():
        raise WorkflowConfigError(
            "Do not place approval in workflow config. Resume with a report-bound approval instead."
        )
    if config.get("start_mode") == "discovery":
        discovery = config.get("lead_discovery")
        if not isinstance(discovery, dict) or discovery.get("mode") not in {"fixture", "live"}:
            raise WorkflowConfigError("lead_discovery.mode must be fixture or live.")
        if not str(discovery.get("selected_lead_id") or "").strip():
            raise WorkflowConfigError("lead_discovery.selected_lead_id is required.")
    outreach = config.get("outreach")
    if not isinstance(outreach, dict):
        raise WorkflowConfigError("outreach is required.")
    if not str(outreach.get("sender_company") or "").strip():
        raise WorkflowConfigError("outreach.sender_company is required.")
    email_type = str(outreach.get("email_type") or "first_touch")
    if email_type not in {"first_touch", "follow_up"}:
        raise WorkflowConfigError("outreach.email_type must be first_touch or follow_up.")
    if email_type == "follow_up" and not str(outreach.get("previous_contact_context") or "").strip():
        raise WorkflowConfigError("outreach.previous_contact_context is required for follow_up.")


def build_manifest(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return {
        "contract_version": "1.0",
        "run_id": str(config["run_id"]),
        "config_hash": config_hash(config),
        "status": "running",
        "current_stage": "initializing",
        "next_action": "run_workflow",
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "output_dir": str(output_dir),
        "stages": {},
        "artifacts": {},
        "sources": {},
        "error": None,
        "exit_code": None,
    }


def run_workflow(
    config: dict[str, Any],
    config_path: Path,
    output_dir: Path,
    *,
    resume: bool,
    approval_override: str,
    reviewer: str,
    approval_json: str,
) -> int:
    validate_config(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    if resume:
        recover_interrupted_commits(output_dir)
    elif any(output_dir.iterdir()):
        existing = ", ".join(sorted(path.name for path in output_dir.iterdir())[:8])
        raise WorkflowConfigError(
            "Fresh runs require an empty output directory; stale pipeline artifacts are present: "
            f"{existing}"
        )
    manifest_path = output_dir / "00-run-manifest.json"
    frozen_config_path = output_dir / "00-workflow-config.json"
    approval_path = output_dir / "05-sales-angle-approval.json"

    if not resume and (approval_override.strip() or approval_json.strip()):
        raise WorkflowConfigError(
            "Sales-angle approval is only accepted with --resume after the report has been generated for review."
        )
    if not resume and approval_path.exists():
        raise WorkflowConfigError(
            "Fresh runs cannot consume an existing sales-angle approval file. Use a clean output directory."
        )

    if resume:
        if not manifest_path.exists():
            raise WorkflowConfigError(f"Cannot resume because {manifest_path} does not exist.")
        manifest = load_json(manifest_path)
        if manifest.get("config_hash") != config_hash(config):
            raise WorkflowConfigError("The workflow config changed. Start a new run_id instead of resuming.")
        validate_recorded_sources(manifest)
        recover_pending_approval(
            manifest_path=manifest_path,
            manifest=manifest,
            customer_intel_report_path=output_dir / "06-customer-intel-report.json",
            approval_path=approval_path,
        )
        validate_recorded_artifacts(manifest, output_dir)
        if manifest.get("status") == "completed":
            print(json.dumps({"status": "completed", "manifest": str(manifest_path)}, ensure_ascii=False))
            return 0
        manifest["status"] = "running"
        manifest["error"] = None
        manifest["exit_code"] = None
    else:
        if manifest_path.exists():
            raise WorkflowConfigError(
                f"Run manifest already exists at {manifest_path}. Use --resume or choose another output directory."
            )
        manifest = build_manifest(config, output_dir)
        atomic_write_json(frozen_config_path, config)
        register_artifact(manifest, "workflow_config", frozen_config_path)
    save_manifest(manifest_path, manifest)

    config_dir = config_path.parent

    discovery_output_path = output_dir / "01-lead-discovery-output.json"
    screening_input_path = output_dir / "02-lead-screening-input.json"
    screening_json_path = output_dir / "03-lead-screening-output.json"
    screening_md_path = output_dir / "03-lead-screening-output.md"
    customer_intel_batch_path = output_dir / "04-customer-intel-batch.json"
    selected_intel_input_path = output_dir / "05-selected-customer-intel-input.json"
    evidence_input_path = output_dir / "05-customer-intel-evidence-input.json"
    customer_intel_report_path = output_dir / "06-customer-intel-report.json"
    customer_intel_markdown_path = output_dir / "06-customer-intel-report.md"
    email_input_path = output_dir / "07-email-input.json"
    email_json_path = output_dir / "08-email-draft.json"
    email_md_path = output_dir / "08-email-draft.md"

    start_mode = str(config["start_mode"])
    selected_lead_id = "lead-001"
    intel_section = config["customer_intel"]
    intel_mode = str(intel_section["mode"])
    intel_required_paths = [customer_intel_report_path]
    if intel_mode != "reviewed_report":
        intel_required_paths.append(customer_intel_markdown_path)
    intel_stage_complete = resume and stage_completed(manifest, "customer_intel", intel_required_paths)

    if start_mode != "discovery" and not intel_stage_complete:
        begin_stage(manifest_path, manifest, "customer_intel")

    if start_mode == "discovery":
        discovery = config["lead_discovery"]
        selected_lead_id = str(discovery["selected_lead_id"])
        if not (resume and stage_completed(manifest, "lead_discovery", [discovery_output_path])):
            begin_stage(manifest_path, manifest, "lead_discovery")
            discovery_input_path = output_dir / "00-lead-discovery-input.json"
            materialize_object(
                discovery,
                inline_key="input",
                path_key="input_json",
                destination=discovery_input_path,
                config_dir=config_dir,
                manifest=manifest,
                resume=resume,
                source_key="lead_discovery_input",
            )
            register_artifact(manifest, "lead_discovery_input", discovery_input_path)
            discovery_output_temp = fresh_temp_path(discovery_output_path)
            command = [
                sys.executable,
                str(SEARCH_SKILL / "scripts" / "build_lead_discovery_report.py"),
                "--input-json",
                str(discovery_input_path),
                "--json-out",
                str(discovery_output_temp),
            ]
            if discovery["mode"] == "fixture":
                fixture_path = output_dir / "00-lead-discovery-fixtures.json"
                materialize_object(
                    discovery,
                    inline_key="fixtures",
                    path_key="fixtures_json",
                    destination=fixture_path,
                    config_dir=config_dir,
                    manifest=manifest,
                    resume=resume,
                    source_key="lead_discovery_fixtures",
                )
                register_artifact(manifest, "lead_discovery_fixtures", fixture_path)
                command.extend(["--fixtures-json", str(fixture_path)])
            save_manifest(manifest_path, manifest)
            run_stage("lead_discovery", command)
            commit_stage_outputs("lead_discovery", [(discovery_output_temp, discovery_output_path)])
        complete_stage(manifest, "lead_discovery", artifact=discovery_output_path.name)
        register_artifact(manifest, "lead_discovery", discovery_output_path)
        save_manifest(manifest_path, manifest)

        screening_stage_complete = resume and stage_completed(
            manifest,
            "lead_screening",
            [screening_input_path, screening_json_path, screening_md_path, customer_intel_batch_path],
        )
        if not screening_stage_complete:
            begin_stage(manifest_path, manifest, "lead_screening")
            screening_input_temp = fresh_temp_path(screening_input_path)
            run_stage(
                "lead_screening",
                [
                    sys.executable,
                    str(SEARCH_SKILL / "scripts" / "build_lead_screening_input.py"),
                    "--input-json",
                    str(discovery_output_path),
                    "--json-out",
                    str(screening_input_temp),
                ],
            )
            commit_stage_outputs("lead_screening", [(screening_input_temp, screening_input_path)])
            register_artifact(manifest, "lead_screening_input", screening_input_path)
            save_manifest(manifest_path, manifest)
            screening_json_temp = fresh_temp_path(screening_json_path)
            screening_md_temp = fresh_temp_path(screening_md_path)
            run_stage(
                "lead_screening",
                [
                    sys.executable,
                    str(SCREENING_SKILL / "scripts" / "build_lead_screening_report.py"),
                    "--input-json",
                    str(screening_input_path),
                    "--markdown-out",
                    str(screening_md_temp),
                    "--json-out",
                    str(screening_json_temp),
                ],
            )
            commit_stage_outputs(
                "lead_screening",
                [(screening_json_temp, screening_json_path), (screening_md_temp, screening_md_path)],
            )
            customer_intel_batch_temp = fresh_temp_path(customer_intel_batch_path)
            run_stage(
                "lead_screening",
                [
                    sys.executable,
                    str(SCREENING_SKILL / "scripts" / "build_customer_intel_batch_input.py"),
                    "--input-json",
                    str(screening_json_path),
                    "--json-out",
                    str(customer_intel_batch_temp),
                ],
            )
            commit_stage_outputs(
                "lead_screening",
                [(customer_intel_batch_temp, customer_intel_batch_path)],
            )
            selected_input = selected_customer_intel_input(screening_json_path, selected_lead_id)
            atomic_write_json(selected_intel_input_path, selected_input)
        else:
            selected_input = load_json(selected_intel_input_path)
        register_artifact(manifest, "selected_customer_intel_input", selected_intel_input_path)
        complete_stage(manifest, "lead_screening", artifact=screening_json_path.name)
        register_artifact(manifest, "lead_screening", screening_json_path)
        register_artifact(manifest, "lead_screening_markdown", screening_md_path)
        register_artifact(manifest, "customer_intel_batch", customer_intel_batch_path)
        save_manifest(manifest_path, manifest)
    else:
        complete_stage(
            manifest,
            "lead_discovery",
            status="skipped",
            note="Workflow starts at customer_intel.",
        )
        complete_stage(
            manifest,
            "lead_screening",
            status="skipped",
            note="Workflow starts at customer_intel.",
        )
        if intel_mode == "evidence":
            payload = materialize_object(
                intel_section,
                inline_key="input",
                path_key="input_json",
                destination=evidence_input_path,
                config_dir=config_dir,
                manifest=manifest,
                resume=resume,
                source_key="customer_intel_evidence",
            )
            selected_input = payload.get("lead") if isinstance(payload.get("lead"), dict) else {}
        elif intel_section["mode"] == "live_web":
            selected_input = materialize_object(
                intel_section,
                inline_key="input",
                path_key="input_json",
                destination=selected_intel_input_path,
                config_dir=config_dir,
                manifest=manifest,
                resume=resume,
                source_key="customer_intel_input",
            )
        else:
            report_source = materialize_object(
                intel_section,
                inline_key="report",
                path_key="report_json",
                destination=customer_intel_report_path,
                config_dir=config_dir,
                manifest=manifest,
                resume=resume,
                source_key="customer_intel_report",
            )
            selected_input = {
                "company_name": company_name_from_report(report_source),
                "seller_context": report_source.get("seller_context") or {},
            }
        if not selected_input:
            raise WorkflowConfigError("customer_intel input must contain a lead object.")
        if not (resume and selected_intel_input_path.exists()):
            atomic_write_json(selected_intel_input_path, selected_input)
        register_artifact(manifest, "selected_customer_intel_input", selected_intel_input_path)
        if evidence_input_path.is_file():
            register_artifact(manifest, "customer_intel_evidence_input", evidence_input_path)
        save_manifest(manifest_path, manifest)

    if not intel_stage_complete:
        if start_mode == "discovery":
            begin_stage(manifest_path, manifest, "customer_intel")
        if start_mode == "discovery" and intel_mode == "reviewed_report":
            materialize_object(
                intel_section,
                inline_key="report",
                path_key="report_json",
                destination=customer_intel_report_path,
                config_dir=config_dir,
                manifest=manifest,
                resume=resume,
                source_key="customer_intel_report",
            )
            register_artifact(manifest, "customer_intel", customer_intel_report_path)
            save_manifest(manifest_path, manifest)
        if intel_mode == "evidence":
            if start_mode == "discovery":
                evidence_source = materialize_object(
                    intel_section,
                    inline_key="evidence",
                    path_key="evidence_json",
                    destination=evidence_input_path,
                    config_dir=config_dir,
                    manifest=manifest,
                    resume=resume,
                    source_key="customer_intel_evidence",
                )
                evidence_bundle = evidence_source.get("evidence_bundle", evidence_source)
                if not resume:
                    atomic_write_json(
                        evidence_input_path,
                        {"lead": selected_input, "evidence_bundle": evidence_bundle},
                    )
                register_artifact(manifest, "customer_intel_evidence_input", evidence_input_path)
                save_manifest(manifest_path, manifest)
            customer_intel_report_temp = fresh_temp_path(customer_intel_report_path)
            customer_intel_markdown_temp = fresh_temp_path(customer_intel_markdown_path)
            run_stage(
                "customer_intel",
                [
                    sys.executable,
                    str(INTEL_SKILL / "for-openclaw" / "scripts" / "build_customer_intel_report_from_evidence.py"),
                    "--input-json",
                    str(evidence_input_path),
                    "--json-out",
                    str(customer_intel_report_temp),
                    "--markdown-out",
                    str(customer_intel_markdown_temp),
                ],
            )
            commit_stage_outputs(
                "customer_intel",
                [
                    (customer_intel_report_temp, customer_intel_report_path),
                    (customer_intel_markdown_temp, customer_intel_markdown_path),
                ],
            )
        elif intel_mode == "live_web":
            customer_intel_report_temp = fresh_temp_path(customer_intel_report_path)
            customer_intel_markdown_temp = fresh_temp_path(customer_intel_markdown_path)
            run_stage(
                "customer_intel",
                [
                    sys.executable,
                    str(INTEL_SKILL / "scripts" / "build_customer_intel_report.py"),
                    "--input-json",
                    str(selected_intel_input_path),
                    "--json-out",
                    str(customer_intel_report_temp),
                    "--markdown-out",
                    str(customer_intel_markdown_temp),
                ],
            )
            commit_stage_outputs(
                "customer_intel",
                [
                    (customer_intel_report_temp, customer_intel_report_path),
                    (customer_intel_markdown_temp, customer_intel_markdown_path),
                ],
            )
        elif not customer_intel_report_path.exists():
            raise WorkflowConfigError("reviewed_report mode requires report or report_json.")

    report = load_json(customer_intel_report_path)
    require_company_match(selected_input, report)
    complete_stage(manifest, "customer_intel", artifact=customer_intel_report_path.name)
    register_artifact(manifest, "customer_intel", customer_intel_report_path)
    if customer_intel_markdown_path.is_file():
        register_artifact(manifest, "customer_intel_markdown", customer_intel_markdown_path)
    current_report_hash = file_sha256(customer_intel_report_path)
    review_report_hash = str(manifest.get("review_report_sha256") or "")
    if not review_report_hash:
        manifest["review_report_sha256"] = current_report_hash
        review_report_hash = current_report_hash
    save_manifest(manifest_path, manifest)

    intel_action = (report.get("intel_decision") or {}).get("recommended_next_action")
    if intel_action != "ready_for_email_draft":
        focus = (report.get("intel_decision") or {}).get("review_focus") or []
        return stop_with_status(
            manifest_path,
            manifest,
            status="hold_for_manual_review",
            current_stage="customer_intel",
            next_action="；".join(str(item) for item in focus[:3]) or "补充证据后重新运行。",
            exit_code=11,
        )

    angle_id = approved_angle_id(report)
    supplied_record = supplied_approval_record(
        config=config,
        config_dir=config_dir,
        review_report_hash=review_report_hash,
        approval_override=approval_override,
        reviewer=reviewer,
        approval_json=approval_json,
    )
    if angle_id:
        if proposed_report_sha256(report) != review_report_hash:
            raise StageExecutionError(
                "customer_intel",
                "The approved report no longer matches the report that was reviewed.",
            )
        approval_record = supplied_record
        if approval_record is None and approval_path.exists():
            approval_record = load_json(approval_path)
        if approval_record is None:
            raise StageExecutionError(
                "customer_intel",
                "The report contains an approved angle but no report-bound approval record.",
            )
        validate_approval_record(
            approval_record,
            run_id=str(config["run_id"]),
            review_report_hash=review_report_hash,
        )
        if approval_record.get("angle_id") != angle_id:
            raise StageExecutionError("customer_intel", "Approval record and report angle do not match.")
        approved_hash = str(manifest.get("approved_report_sha256") or "")
        if approved_hash and current_report_hash != approved_hash:
            raise StageExecutionError("customer_intel", "Approved report hash does not match the current report.")
        if not approval_path.exists():
            atomic_write_json(approval_path, approval_record)
        manifest["approved_report_sha256"] = current_report_hash
        manifest["approval_record"] = approval_path.name
        register_artifact(manifest, "sales_angle_approval", approval_path)
        manifest.setdefault("artifact_sha256", {})["customer_intel"] = current_report_hash
        save_manifest(manifest_path, manifest)
    elif supplied_record is not None or approval_path.exists():
        if current_report_hash != review_report_hash:
            raise StageExecutionError(
                "customer_intel",
                "The report changed after review was requested. Start a new run before approving an angle.",
            )
        approval_record = supplied_record or load_json(approval_path)
        validate_approval_record(
            approval_record,
            run_id=str(config["run_id"]),
            review_report_hash=review_report_hash,
        )
        angle_id = str(approval_record["angle_id"])
        require_sales_angle(report, angle_id)
        manifest.update(
            {
                "status": "applying_approval",
                "current_stage": "customer_intel",
                "next_action": "完成可恢复的销售角度审批事务。",
                "pending_approval": approval_record,
            }
        )
        save_manifest(manifest_path, manifest)
        report = approve_angle(customer_intel_report_path, angle_id)
        current_report_hash = file_sha256(customer_intel_report_path)
        atomic_write_json(approval_path, approval_record)
        manifest["approved_report_sha256"] = current_report_hash
        manifest["approval_record"] = approval_path.name
        register_artifact(manifest, "sales_angle_approval", approval_path)
        manifest.setdefault("artifact_sha256", {})["customer_intel"] = current_report_hash
        manifest.pop("pending_approval", None)
        manifest["status"] = "running"
        save_manifest(manifest_path, manifest)
    else:
        if current_report_hash != review_report_hash:
            raise StageExecutionError(
                "customer_intel",
                "The report changed after review was requested. Start a new run before approving an angle.",
            )
        available = [item.get("angle_id") for item in report.get("sales_angles") or [] if item.get("angle_id")]
        manifest["available_sales_angle_ids"] = available
        return stop_with_status(
            manifest_path,
            manifest,
            status="awaiting_sales_angle_approval",
            current_stage="customer_intel",
            next_action=(
                "人工选择 ANGLE-*，再使用 --resume --approved-sales-angle-id ANGLE-XX "
                "--reviewer REVIEWER 续跑，或提供绑定报告哈希的 --approval-json。"
            ),
            exit_code=10,
        )

    outreach = config["outreach"]
    product_or_offer = str(outreach.get("product_or_offer") or "").strip()
    if not product_or_offer:
        product_or_offer = str((report.get("seller_context") or {}).get("product_or_offer") or "").strip()
    if not product_or_offer:
        raise WorkflowConfigError("outreach.product_or_offer is required when seller_context has no product.")

    outreach_stage_complete = resume and stage_completed(
        manifest,
        "outreach_email",
        [email_input_path, email_json_path, email_md_path],
    )
    if not outreach_stage_complete:
        begin_stage(manifest_path, manifest, "outreach_email")
        email_input_temp = fresh_temp_path(email_input_path)
        run_stage(
            "outreach_email",
            [
                sys.executable,
                str(EMAIL_SKILL / "scripts" / "build_email_input_from_customer_intel.py"),
                "--input-json",
                str(customer_intel_report_path),
                "--email-type",
                str(outreach.get("email_type") or "first_touch"),
                "--product-or-offer",
                product_or_offer,
                "--sender-name",
                str(outreach.get("sender_name") or ""),
                "--sender-company",
                str(outreach["sender_company"]),
                "--previous-contact-context",
                str(outreach.get("previous_contact_context") or ""),
                "--approved-sales-angle-id",
                angle_id,
                "--json-out",
                str(email_input_temp),
            ],
        )
        commit_stage_outputs("outreach_email", [(email_input_temp, email_input_path)])
        register_artifact(manifest, "outreach_email_input", email_input_path)
        save_manifest(manifest_path, manifest)
        email_json_temp = fresh_temp_path(email_json_path)
        email_md_temp = fresh_temp_path(email_md_path)
        run_stage(
            "outreach_email",
            [
                sys.executable,
                str(EMAIL_SKILL / "scripts" / "build_email_draft.py"),
                "--input-json",
                str(email_input_path),
                "--markdown-out",
                str(email_md_temp),
                "--json-out",
                str(email_json_temp),
            ],
        )
        commit_stage_outputs(
            "outreach_email",
            [(email_json_temp, email_json_path), (email_md_temp, email_md_path)],
        )
        complete_stage(manifest, "outreach_email", artifact=email_json_path.name)
        register_artifact(manifest, "outreach_email", email_json_path)
        register_artifact(manifest, "outreach_email_markdown", email_md_path)
        manifest["approved_sales_angle_id"] = angle_id
        save_manifest(manifest_path, manifest)
    else:
        angle_id = str(manifest.get("approved_sales_angle_id") or angle_id)

    exports = config.get("exports") if isinstance(config.get("exports"), dict) else {}
    if start_mode == "discovery" and exports.get("container_bundle", True):
        include_feishu = bool(exports.get("feishu_sandbox", False))
        export_names = [
            "09-container-bundle.json",
            "10-container-bundle.md",
            "11-lead-workflow.csv",
        ]
        if include_feishu:
            export_names.extend(
                ["09-feishu-workflow-bundle.json", "12-feishu-sandbox-bundle.json"]
            )
        export_paths = [output_dir / name for name in export_names]
        export_stage_complete = resume and stage_completed(manifest, "exports", export_paths)
        if not export_stage_complete:
            begin_stage(manifest_path, manifest, "exports")
            export_temp_dir = output_dir / ".exports-stage-tmp"
            try:
                if export_temp_dir.is_dir():
                    shutil.rmtree(export_temp_dir)
                export_temp_dir.mkdir(parents=True, exist_ok=True)
                export_default_artifacts(
                    output_dir,
                    str(config["run_id"]),
                    selected_lead_id,
                    include_feishu=include_feishu,
                    artifact_output_dir=export_temp_dir,
                )
                commit_stage_outputs(
                    "exports",
                    [(export_temp_dir / name, output_dir / name) for name in export_names],
                )
            except StageExecutionError:
                raise
            except OSError as exc:
                raise StageExecutionError("exports", f"Export staging failed: {exc}") from exc
            except Exception as exc:
                raise StageExecutionError("exports", f"Export stage failed: {exc}") from exc
            finally:
                if export_temp_dir.is_dir():
                    try:
                        shutil.rmtree(export_temp_dir)
                    except OSError:
                        pass
            complete_stage(manifest, "exports", artifact="09-container-bundle.json")
            register_artifact(manifest, "container_bundle", output_dir / "09-container-bundle.json")
            register_artifact(manifest, "container_bundle_markdown", output_dir / "10-container-bundle.md")
            register_artifact(manifest, "lead_workflow_csv", output_dir / "11-lead-workflow.csv")
            if include_feishu:
                register_artifact(manifest, "feishu_workflow_bundle", output_dir / "09-feishu-workflow-bundle.json")
                register_artifact(manifest, "feishu_sandbox", output_dir / "12-feishu-sandbox-bundle.json")
    else:
        complete_stage(
            manifest,
            "exports",
            status="skipped",
            note="Container export requires a discovery-start run or was disabled by config.",
        )

    manifest.update(
        {
            "status": "completed",
            "current_stage": "completed",
            "next_action": "人工复核邮件草稿；本工作流不会自动发送。",
            "exit_code": 0,
            "available_sales_angle_ids": [
                item.get("angle_id") for item in report.get("sales_angles") or [] if item.get("angle_id")
            ],
        }
    )
    save_manifest(manifest_path, manifest)
    print(json.dumps({"status": "completed", "manifest": str(manifest_path)}, ensure_ascii=False))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run or resume the deliverable active-outreach workflow with machine-readable state."
    )
    parser.add_argument("--config", required=True, help="Workflow config JSON matching workflow-input.schema.json.")
    parser.add_argument("--output-dir", required=True, help="Stable directory for this run's artifacts and manifest.")
    parser.add_argument("--resume", action="store_true", help="Resume an existing run without repeating completed upstream work.")
    parser.add_argument(
        "--approved-sales-angle-id",
        default="",
        help="Explicit approval override used only when resuming after human review.",
    )
    parser.add_argument(
        "--reviewer",
        default="",
        help="Human reviewer identifier required with --approved-sales-angle-id.",
    )
    parser.add_argument(
        "--approval-json",
        default="",
        help="Path to a report-bound approval record with run_id, report_sha256, angle_id, reviewer, and approved_at.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    manifest_path = output_dir / "00-run-manifest.json"
    config: dict[str, Any] | None = None
    try:
        config = load_json(config_path)
        code = run_workflow(
            config,
            config_path,
            output_dir,
            resume=args.resume,
            approval_override=args.approved_sales_angle_id,
            reviewer=args.reviewer,
            approval_json=args.approval_json,
        )
    except WorkflowConfigError as exc:
        if manifest_path.exists() and config is not None:
            cleanup_stage_temps(output_dir)
            manifest = load_json(manifest_path)
            if manifest.get("config_hash") == config_hash(config):
                manifest.update(
                    {
                        "status": "failed",
                        "next_action": "修复配置或审批输入后使用 --resume 续跑。",
                        "error": {
                            "stage": manifest.get("current_stage") or "configuration",
                            "message": str(exc),
                            "returncode": 2,
                        },
                        "exit_code": 2,
                    }
                )
                save_manifest(manifest_path, manifest)
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except StageExecutionError as exc:
        cleanup_stage_temps(output_dir)
        if manifest_path.exists():
            manifest = load_json(manifest_path)
            manifest.update(
                {
                    "status": "failed",
                    "current_stage": exc.stage,
                    "next_action": "修复失败原因后使用 --resume 续跑。",
                    "error": {
                        "stage": exc.stage,
                        "message": str(exc),
                        "returncode": exc.returncode,
                    },
                    "exit_code": 3,
                }
            )
            stages = manifest.setdefault("stages", {})
            previous_record = stages.get(exc.stage) or {}
            previous_attempt = int(previous_record.get("attempt") or 0)
            attempt = previous_attempt if previous_record.get("status") == "running" else previous_attempt + 1
            stages[exc.stage] = {
                "status": "failed",
                "attempt": max(1, attempt),
                "exit_code": exc.returncode,
                "updated_at": utc_now(),
                "note": str(exc),
            }
            save_manifest(manifest_path, manifest)
        print(f"Stage '{exc.stage}' failed: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc
    raise SystemExit(code)


if __name__ == "__main__":
    main()
