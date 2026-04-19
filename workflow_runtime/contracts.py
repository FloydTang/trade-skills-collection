from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORKFLOW_OWNER_SKILL = "trade-active-outreach-combo"

STAGE_WORKER_SKILLS = {
    "lead_discovery": "trade-lead-discovery-openclaw",
    "lead_screening": "trade-lead-screening-openclaw",
    "customer_intel": "trade-customer-intel-for-openclaw",
    "outreach_email": "trade-outreach-email-for-openclaw",
}

SEARCH_STAGE_ACTIONS = {
    "ready_for_screening",
    "needs_enrichment",
    "hold_for_manual_review",
    "reject_low_evidence",
}

SCREENING_STAGE_ACTIONS = {
    "ready_for_customer_intel",
    "needs_enrichment",
    "hold_for_manual_review",
}

INTEL_STAGE_ACTIONS = {
    "ready_for_email_draft",
    "hold_for_manual_review",
}

OUTREACH_STAGE_ACTIONS = {
    "ready_for_manual_send",
    "hold_for_manual_review",
}

SEARCH_GRADE_TO_ACTION = {
    "A": "ready_for_screening",
    "B": "ready_for_screening",
    "C": "needs_enrichment",
    "D": "reject_low_evidence",
}

SCREENING_ACTION_TO_LEGACY = {
    "ready_for_customer_intel": "enter_customer_intel",
    "needs_enrichment": "enrich_then_customer_intel",
    "hold_for_manual_review": "hold_for_manual_review",
}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(data: Any, path: str | Path) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def slugify(value: str) -> str:
    normalized = normalize_text(value).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "item"


def make_workflow_id(combo_run_id: str, lead_id: str, company_name: str) -> str:
    return f"{combo_run_id}-{lead_id}-{slugify(company_name)}"


def compact_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in ("", None, [], {})}


def screening_action_legacy(action: str) -> str:
    return SCREENING_ACTION_TO_LEGACY.get(action, action)

