from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def heading_block(text: str, level: int = 1) -> dict[str, Any]:
    return {"type": "heading", "level": level, "text": text}


def paragraph_block(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "text": text}


def bullet_block(items: list[str], title: str | None = None) -> dict[str, Any]:
    payload = {"type": "bullets", "items": [item for item in items if normalize_text(item)]}
    if title:
        payload["title"] = title
    return payload


def kv_block(title: str, fields: dict[str, Any]) -> dict[str, Any]:
    return {"type": "kv", "title": title, "fields": compact_dict(fields)}


def table_block(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "table", "title": title, "rows": [compact_dict(row) for row in rows]}


def code_block(language: str, content: Any, title: str | None = None) -> dict[str, Any]:
    rendered = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2)
    payload = {"type": "code", "language": language, "content": rendered}
    if title:
        payload["title"] = title
    return payload


def master_table_schema() -> dict[str, Any]:
    return {
        "table_name": "Lead Workflow Master",
        "description": "全链路主表。每行代表一条线索在主动开发流程中的当前状态和资产链接。",
        "fields": [
            {"name": "workflow_id", "type": "text", "required": True},
            {"name": "lead_id", "type": "text", "required": True},
            {"name": "company_name", "type": "text", "required": True},
            {"name": "person_name", "type": "text"},
            {"name": "email", "type": "text"},
            {"name": "country_or_market", "type": "text"},
            {"name": "source_stage", "type": "single_select"},
            {"name": "current_stage", "type": "single_select"},
            {"name": "current_status", "type": "single_select"},
            {"name": "recommended_next_action", "type": "single_select"},
            {"name": "risk_rating", "type": "single_select"},
            {"name": "entity_confidence", "type": "single_select"},
            {"name": "owner", "type": "text"},
            {"name": "next_follow_up_date", "type": "date"},
            {"name": "last_updated_at", "type": "datetime"},
            {"name": "search_doc_url", "type": "url"},
            {"name": "screening_table_record_url", "type": "url"},
            {"name": "intel_doc_url", "type": "url"},
            {"name": "email_doc_url", "type": "url"},
            {"name": "combo_run_id", "type": "text"},
            {"name": "asset_keys", "type": "multiline_text"},
            {"name": "failure_reason", "type": "multiline_text"},
        ],
    }


def search_stage_payload(report: dict[str, Any], combo_run_id: str) -> dict[str, Any]:
    lead_inputs = (report.get("lead_screening_input") or {}).get("leads") or []
    records: list[dict[str, Any]] = []
    for index, candidate in enumerate(report.get("candidates") or [], start=1):
        lead_input = lead_inputs[index - 1] if index - 1 < len(lead_inputs) else {}
        lead_id = f"lead-{index:03d}"
        records.append(
            {
                "workflow_meta": {
                    "combo_run_id": combo_run_id,
                    "generated_at": utc_now_iso(),
                    "source_stage": "lead_discovery",
                },
                "lead_identity": compact_dict(
                    {
                        "lead_id": lead_id,
                        "company_name": candidate.get("company_name"),
                        "person_name": lead_input.get("person_name"),
                        "email": lead_input.get("email"),
                        "country_or_market": candidate.get("country_or_market"),
                    }
                ),
                "stage_name": "lead_discovery",
                "stage_status": "completed",
                "summary_fields": compact_dict(
                    {
                        "product_or_offer": (report.get("summary") or {}).get("product_or_offer"),
                        "target_market": (report.get("summary") or {}).get("target_market"),
                        "customer_type": (report.get("summary") or {}).get("customer_type"),
                        "candidate_count": (report.get("summary") or {}).get("candidate_count"),
                    }
                ),
                "table_fields": compact_dict(
                    {
                        "candidate_id": candidate.get("candidate_id"),
                        "lead_id": lead_id,
                        "company_name": candidate.get("company_name"),
                        "company_website": candidate.get("company_website"),
                        "source_url": candidate.get("source_url"),
                        "linkedin_url": candidate.get("linkedin_url"),
                        "country_or_market": candidate.get("country_or_market"),
                        "visible_contact_clues": "\n".join(candidate.get("visible_contact_clues") or []),
                        "search_query_used": "\n".join(candidate.get("search_query_used") or []),
                        "search_snippet": candidate.get("search_snippet"),
                        "follow_up_suggestion": candidate.get("follow_up_suggestion"),
                        "enter_screening": "yes",
                    }
                ),
                "document_blocks": [
                    heading_block(f"{candidate.get('candidate_id')} | {candidate.get('company_name')}", level=2),
                    kv_block(
                        "线索摘要",
                        {
                            "Lead ID": lead_id,
                            "Website": candidate.get("company_website"),
                            "LinkedIn": candidate.get("linkedin_url"),
                            "Country / Market": candidate.get("country_or_market"),
                            "Source Type": candidate.get("source_type"),
                        },
                    ),
                    paragraph_block(candidate.get("search_snippet") or "未提供搜索摘要。"),
                    bullet_block(candidate.get("visible_contact_clues") or [], title="可见联系人线索"),
                    bullet_block(candidate.get("search_query_used") or [], title="使用过的搜索词"),
                    paragraph_block(candidate.get("follow_up_suggestion") or ""),
                ],
                "upstream_refs": [],
                "next_action": "screening_ready",
                "review_required": [
                    "确认候选主体是否值得进入初筛。",
                    "如联系人线索较弱，补官网或 LinkedIn 后再推进。",
                ],
                "asset_binding": {
                    "asset_mode": "table_record",
                    "target_table_name": "Lead Discovery Results",
                    "asset_key": f"search-record:{combo_run_id}:{lead_id}",
                    "reuse_strategy": "upsert_by_combo_run_and_lead_id",
                },
            }
        )
    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "generated_at": utc_now_iso(),
            "stage_scope": "lead_discovery_batch",
        },
        "lead_identity": None,
        "stage_name": "lead_discovery",
        "stage_status": "completed",
        "summary_fields": compact_dict(report.get("summary") or {}),
        "table_fields": None,
        "document_blocks": [
            heading_block("Lead Discovery Batch Summary"),
            kv_block("搜索摘要", report.get("summary") or {}),
        ],
        "upstream_refs": [],
        "next_action": "screening_ready",
        "review_required": ["先确认哪些候选要进入初筛。"],
        "record_payloads": records,
    }


def screening_stage_payload(report: dict[str, Any], combo_run_id: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for lead in report.get("leads") or []:
        records.append(
            {
                "workflow_meta": {
                    "combo_run_id": combo_run_id,
                    "generated_at": utc_now_iso(),
                    "source_stage": "lead_screening",
                },
                "lead_identity": compact_dict(
                    {
                        "lead_id": lead.get("lead_id"),
                        "company_name": lead.get("normalized_company_name"),
                        "person_name": lead.get("normalized_person_name"),
                        "email": lead.get("email"),
                        "country_or_market": lead.get("country_or_market"),
                    }
                ),
                "stage_name": "lead_screening",
                "stage_status": "completed",
                "summary_fields": {
                    "recommended_next_action": lead.get("recommended_next_action"),
                    "lead_bucket": lead.get("lead_bucket"),
                    "manual_review_count": len(lead.get("manual_review_reasons") or []),
                },
                "table_fields": compact_dict(
                    {
                        "lead_id": lead.get("lead_id"),
                        "company_name": lead.get("normalized_company_name"),
                        "person_name": lead.get("normalized_person_name"),
                        "email": lead.get("email"),
                        "company_website": lead.get("company_website"),
                        "country_or_market": lead.get("country_or_market"),
                        "lead_bucket": lead.get("lead_bucket"),
                        "missing_fields": "\n".join(lead.get("missing_fields") or []),
                        "manual_review_reasons": "\n".join(lead.get("manual_review_reasons") or []),
                        "recommended_next_action": lead.get("recommended_next_action"),
                        "follow_up_suggestions": "\n".join(lead.get("follow_up_suggestions") or []),
                    }
                ),
                "document_blocks": [
                    heading_block(f"{lead.get('lead_id')} | {lead.get('normalized_company_name')}", level=2),
                    kv_block(
                        "标准化字段",
                        {
                            "Person": lead.get("normalized_person_name"),
                            "Email": lead.get("email"),
                            "Website": lead.get("company_website"),
                            "Country / Market": lead.get("country_or_market"),
                            "Lead Bucket": lead.get("lead_bucket"),
                            "Recommended Next Action": lead.get("recommended_next_action"),
                        },
                    ),
                    bullet_block(lead.get("missing_fields") or [], title="缺失字段"),
                    bullet_block(lead.get("manual_review_reasons") or [], title="人工复核原因"),
                    bullet_block(lead.get("follow_up_suggestions") or [], title="后续建议"),
                    code_block("json", lead.get("customer_intel_input") or {}, title="客户背调桥接输入"),
                ],
                "upstream_refs": [
                    {"stage_name": "lead_discovery", "asset_key": f"search-record:{combo_run_id}:{lead.get('lead_id')}"}
                ],
                "next_action": lead.get("recommended_next_action"),
                "review_required": [
                    "核对推荐下一步动作是否符合当前业务节奏。",
                    "如存在人工复核原因，处理后再进入客户背调。",
                ],
                "asset_binding": {
                    "asset_mode": "table_record",
                    "target_table_name": "Lead Screening Results",
                    "asset_key": f"screening-record:{combo_run_id}:{lead.get('lead_id')}",
                    "reuse_strategy": "upsert_by_combo_run_and_lead_id",
                },
            }
        )
    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "generated_at": utc_now_iso(),
            "stage_scope": "lead_screening_batch",
        },
        "lead_identity": None,
        "stage_name": "lead_screening",
        "stage_status": "completed",
        "summary_fields": compact_dict(report.get("summary") or {}),
        "table_fields": None,
        "document_blocks": [
            heading_block("Lead Screening Batch Summary"),
            kv_block("初筛摘要", report.get("summary") or {}),
        ],
        "upstream_refs": [{"stage_name": "lead_discovery", "asset_key_prefix": f"search-record:{combo_run_id}:"}],
        "next_action": "customer_intel_selection",
        "review_required": ["先确认本轮要推进哪条 lead。"],
        "record_payloads": records,
    }


def intel_stage_payload(
    report: dict[str, Any],
    combo_run_id: str,
    lead_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    identity = report.get("identity_snapshot") or {}
    company = report.get("company_profile") or {}
    evidence_rows = report.get("evidence") or []
    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "workflow_id": workflow_id,
            "generated_at": report.get("generated_at") or utc_now_iso(),
        },
        "lead_identity": compact_dict(
            {
                "lead_id": lead_id,
                "company_name": identity.get("company_name"),
                "person_name": identity.get("person_name"),
                "email": identity.get("email"),
                "country_or_market": identity.get("country_or_market"),
            }
        ),
        "stage_name": "customer_intel",
        "stage_status": "completed",
        "summary_fields": compact_dict(
            {
                "risk_rating": report.get("risk_rating"),
                "entity_confidence": identity.get("entity_confidence"),
                "phase_2_status": report.get("phase_2_status"),
            }
        ),
        "table_fields": compact_dict(
            {
                "lead_id": lead_id,
                "company_name": identity.get("company_name"),
                "person_name": identity.get("person_name"),
                "risk_rating": report.get("risk_rating"),
                "entity_confidence": identity.get("entity_confidence"),
                "phase_2_status": report.get("phase_2_status"),
                "summary_cn": report.get("summary_cn"),
                "summary_en": report.get("summary_en"),
            }
        ),
        "document_blocks": [
            heading_block(f"客户背调 | {identity.get('company_name') or lead_id}"),
            paragraph_block(report.get("summary_cn") or ""),
            paragraph_block(report.get("summary_en") or ""),
            kv_block(
                "Identity Snapshot",
                {
                    "Lead ID": lead_id,
                    "Company": identity.get("company_name"),
                    "Person": identity.get("person_name"),
                    "Email": identity.get("email"),
                    "Website": identity.get("website"),
                    "Country / Market": identity.get("country_or_market"),
                    "Entity Confidence": identity.get("entity_confidence"),
                    "Risk Rating": report.get("risk_rating"),
                },
            ),
            kv_block("Company Profile", company),
            bullet_block(identity.get("ambiguity_notes") or [], title="Ambiguity Notes"),
            table_block("Digital Footprint", report.get("digital_footprint") or []),
            table_block("Interest Signals", report.get("interest_signals") or []),
            table_block("Sales Angles", report.get("sales_angles") or []),
            bullet_block(report.get("risk_reasons") or [], title="Risk Reasons"),
            table_block("Evidence", evidence_rows),
        ],
        "upstream_refs": [
            {"stage_name": "lead_screening", "asset_key": f"screening-record:{combo_run_id}:{lead_id}"}
        ],
        "next_action": "email_ready",
        "review_required": [
            "人工确认主体匹配、风险评级和销售切入角度。",
            "仅在确认公开事实无误后再进入开发信。",
        ],
        "asset_binding": {
            "asset_mode": "doc",
            "target_doc_folder": "Customer Intel Docs",
            "asset_key": f"intel-doc:{workflow_id}",
            "reuse_strategy": "reuse_existing_doc_then_append_version_section",
        },
    }


def email_stage_payload(
    email_input: dict[str, Any],
    email_output: dict[str, Any],
    combo_run_id: str,
    lead_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    scenario = email_output.get("scenario") or {}
    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "workflow_id": workflow_id,
            "generated_at": utc_now_iso(),
        },
        "lead_identity": compact_dict(
            {
                "lead_id": lead_id,
                "company_name": email_input.get("company_name"),
                "person_name": email_input.get("customer_name"),
                "country_or_market": email_input.get("country_or_market"),
            }
        ),
        "stage_name": "outreach_email",
        "stage_status": "draft_ready",
        "summary_fields": compact_dict(
            {
                "email_type": scenario.get("email_type"),
                "goal": scenario.get("goal"),
                "draft_status": "draft_ready",
            }
        ),
        "table_fields": compact_dict(
            {
                "lead_id": lead_id,
                "company_name": email_input.get("company_name"),
                "email_type": scenario.get("email_type"),
                "product_or_offer": email_input.get("product_or_offer"),
                "goal": scenario.get("goal"),
                "sender_name": email_input.get("sender_name"),
                "sender_company": email_input.get("sender_company"),
                "review_notes": "\n".join(email_output.get("review_notes") or []),
            }
        ),
        "document_blocks": [
            heading_block(f"开发信草稿 | {email_input.get('company_name') or lead_id}"),
            kv_block(
                "Scenario",
                {
                    "Email Type": scenario.get("email_type"),
                    "Goal": scenario.get("goal"),
                    "Product / Offer": email_input.get("product_or_offer"),
                    "Sender": email_input.get("sender_name"),
                    "Sender Company": email_input.get("sender_company"),
                },
            ),
            bullet_block(email_output.get("subject_options") or [], title="Subject Options"),
            paragraph_block((email_output.get("drafts") or {}).get("version_a") or ""),
            paragraph_block((email_output.get("drafts") or {}).get("version_b") or ""),
            bullet_block(email_output.get("review_notes") or [], title="Review Notes"),
            bullet_block(email_output.get("input_signals_used") or [], title="Input Signals Used"),
        ],
        "upstream_refs": [
            {"stage_name": "customer_intel", "asset_key": f"intel-doc:{workflow_id}"}
        ],
        "next_action": "manual_send_review",
        "review_required": [
            "复核邮件中所有客户事实和商务表述。",
            "人工确认后再把主表状态改为 ready_to_send 或 hold。",
        ],
        "asset_binding": {
            "asset_mode": "doc",
            "target_doc_folder": "Outreach Email Docs",
            "asset_key": f"email-doc:{workflow_id}",
            "reuse_strategy": "reuse_existing_doc_then_append_new_draft_version",
        },
    }


def infer_master_status(
    screening_record: dict[str, Any],
    selected_lead_id: str,
    intel_payload: dict[str, Any] | None,
    email_payload: dict[str, Any] | None,
) -> tuple[str, str]:
    lead_id = screening_record.get("lead_id")
    action = screening_record.get("recommended_next_action")
    if lead_id == selected_lead_id and email_payload:
        return "outreach_email", "draft_ready"
    if lead_id == selected_lead_id and intel_payload:
        return "customer_intel", "intel_ready"
    if action == "enter_customer_intel":
        return "lead_screening", "waiting_selection"
    if action == "enrich_then_customer_intel":
        return "lead_screening", "needs_enrichment"
    return "lead_screening", "hold"


def master_records(
    search_payload: dict[str, Any],
    screening_payload: dict[str, Any],
    intel_payload: dict[str, Any] | None,
    email_payload: dict[str, Any] | None,
    combo_run_id: str,
    selected_lead_id: str,
) -> list[dict[str, Any]]:
    search_index = {
        (record.get("lead_identity") or {}).get("lead_id"): record for record in search_payload.get("record_payloads") or []
    }
    records: list[dict[str, Any]] = []
    for screening_record in screening_payload.get("record_payloads") or []:
        lead_identity = screening_record.get("lead_identity") or {}
        lead_id = lead_identity.get("lead_id") or ""
        company_name = lead_identity.get("company_name") or ""
        workflow_id = make_workflow_id(combo_run_id, lead_id, company_name)
        current_stage, current_status = infer_master_status(
            screening_record.get("table_fields") or {},
            selected_lead_id,
            intel_payload if lead_id == selected_lead_id else None,
            email_payload if lead_id == selected_lead_id else None,
        )
        search_asset_key = ((search_index.get(lead_id) or {}).get("asset_binding") or {}).get("asset_key")
        screening_asset_key = (screening_record.get("asset_binding") or {}).get("asset_key")
        intel_asset_key = (intel_payload.get("asset_binding") or {}).get("asset_key") if intel_payload and lead_id == selected_lead_id else ""
        email_asset_key = (email_payload.get("asset_binding") or {}).get("asset_key") if email_payload and lead_id == selected_lead_id else ""
        screening_fields = screening_record.get("table_fields") or {}
        intel_fields = intel_payload.get("table_fields") if intel_payload and lead_id == selected_lead_id else {}
        records.append(
            compact_dict(
                {
                    "workflow_id": workflow_id,
                    "lead_id": lead_id,
                    "company_name": company_name,
                    "person_name": lead_identity.get("person_name"),
                    "email": lead_identity.get("email"),
                    "country_or_market": lead_identity.get("country_or_market"),
                    "source_stage": "lead_discovery",
                    "current_stage": current_stage,
                    "current_status": current_status,
                    "recommended_next_action": screening_fields.get("recommended_next_action"),
                    "risk_rating": (intel_fields or {}).get("risk_rating"),
                    "entity_confidence": (intel_fields or {}).get("entity_confidence"),
                    "owner": "",
                    "next_follow_up_date": "",
                    "last_updated_at": utc_now_iso(),
                    "search_doc_url": "",
                    "screening_table_record_url": "",
                    "intel_doc_url": "",
                    "email_doc_url": "",
                    "combo_run_id": combo_run_id,
                    "asset_keys": json.dumps(
                        compact_dict(
                            {
                                "search": search_asset_key,
                                "screening": screening_asset_key,
                                "intel": intel_asset_key,
                                "email": email_asset_key,
                            }
                        ),
                        ensure_ascii=False,
                    ),
                }
            )
        )
    return records

