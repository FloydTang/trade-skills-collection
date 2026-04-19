from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from .contracts import (
    STAGE_WORKER_SKILLS,
    WORKFLOW_OWNER_SKILL,
    compact_dict,
    make_workflow_id,
    screening_action_legacy,
    utc_now_iso,
)


def stage_runtime_contract(stage_name: str) -> dict[str, Any]:
    return {
        "workspace_owner_skill": WORKFLOW_OWNER_SKILL,
        "stage_worker_skill": STAGE_WORKER_SKILLS[stage_name],
        "role": "stage_worker",
        "single_skill_attach_only": True,
        "container_creation": "forbidden",
        "requires_master_container": True,
        "requires_master_record": True,
        "forbid_stage_level_container_bootstrap": True,
    }


def heading_block(text: str, level: int = 1) -> dict[str, Any]:
    return {"type": "heading", "level": level, "text": text}


def paragraph_block(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "text": text}


def bullet_block(items: list[str], title: str | None = None) -> dict[str, Any]:
    payload = {"type": "bullets", "items": [item for item in items if str(item).strip()]}
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


def master_index_schema() -> dict[str, Any]:
    return {
        "schema_name": "Lead Workflow Master",
        "description": "全链路主索引。每行代表一条线索在主动开发流程中的当前状态、关键判断与容器资产引用。",
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
            {"name": "legacy_recommended_next_action", "type": "single_select"},
            {"name": "evidence_grade", "type": "single_select"},
            {"name": "risk_rating", "type": "single_select"},
            {"name": "entity_confidence", "type": "single_select"},
            {"name": "evidence_sufficiency", "type": "single_select"},
            {"name": "send_policy", "type": "single_select"},
            {"name": "last_updated_at", "type": "datetime"},
            {"name": "search_asset_ref", "type": "text"},
            {"name": "screening_asset_ref", "type": "text"},
            {"name": "intel_asset_ref", "type": "text"},
            {"name": "email_asset_ref", "type": "text"},
            {"name": "combo_run_id", "type": "text"},
            {"name": "asset_keys", "type": "multiline_text"},
            {"name": "failure_reason", "type": "multiline_text"},
        ],
    }


def search_stage_asset(report: dict[str, Any], combo_run_id: str) -> dict[str, Any]:
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
                        "evidence_grade": candidate.get("evidence_grade"),
                        "match_reason": candidate.get("match_reason"),
                        "missing_fields": "\n".join(candidate.get("missing_fields") or []),
                        "evidence_summary": candidate.get("evidence_summary"),
                        "next_action": candidate.get("next_action"),
                        "follow_up_suggestion": candidate.get("follow_up_suggestion"),
                    }
                ),
                "document_blocks": [
                    heading_block(f"{candidate.get('candidate_id')} | {candidate.get('company_name')}", level=2),
                    kv_block(
                        "候选线索摘要",
                        {
                            "Lead ID": lead_id,
                            "Website": candidate.get("company_website"),
                            "LinkedIn": candidate.get("linkedin_url"),
                            "Country / Market": candidate.get("country_or_market"),
                            "Source Type": candidate.get("source_type"),
                            "Evidence Grade": candidate.get("evidence_grade"),
                            "Next Action": candidate.get("next_action"),
                        },
                    ),
                    paragraph_block(candidate.get("evidence_summary") or "未提供证据摘要。"),
                    paragraph_block(candidate.get("match_reason") or ""),
                    bullet_block(candidate.get("missing_fields") or [], title="待补字段"),
                    bullet_block(candidate.get("visible_contact_clues") or [], title="可见联系人线索"),
                    bullet_block(candidate.get("search_query_used") or [], title="搜索策略"),
                    paragraph_block(candidate.get("follow_up_suggestion") or ""),
                ],
                "upstream_refs": [],
                "next_action": candidate.get("next_action"),
                "review_required": [
                    "确认候选主体是否值得进入线索整理。",
                    "证据等级为 C/D 时，先补关键字段或人工判断，不要强行推进。",
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
        "runtime_contract": stage_runtime_contract("lead_discovery"),
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
        "next_action": "ready_for_screening",
        "review_required": ["先确认哪些候选要进入线索整理。"],
        "record_payloads": records,
    }


def screening_stage_asset(report: dict[str, Any], combo_run_id: str) -> dict[str, Any]:
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
                    "legacy_recommended_next_action": lead.get("legacy_recommended_next_action"),
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
                        "evidence_grade": lead.get("evidence_grade"),
                        "discovery_next_action": lead.get("discovery_next_action"),
                        "missing_fields": "\n".join(lead.get("missing_fields") or []),
                        "manual_review_reasons": "\n".join(lead.get("manual_review_reasons") or []),
                        "recommended_next_action": lead.get("recommended_next_action"),
                        "legacy_recommended_next_action": lead.get("legacy_recommended_next_action"),
                        "follow_up_suggestions": "\n".join(lead.get("follow_up_suggestions") or []),
                    }
                ),
                "document_blocks": [
                    heading_block(f"{lead.get('lead_id')} | {lead.get('normalized_company_name')}", level=2),
                    kv_block(
                        "线索整理结果",
                        {
                            "Person": lead.get("normalized_person_name"),
                            "Email": lead.get("email"),
                            "Website": lead.get("company_website"),
                            "Country / Market": lead.get("country_or_market"),
                            "Lead Bucket": lead.get("lead_bucket"),
                            "Evidence Grade": lead.get("evidence_grade"),
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
                    "不满足桥接条件时，先补证据或人工复核，再进入客户背调。",
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
        "runtime_contract": stage_runtime_contract("lead_screening"),
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
        "next_action": "ready_for_customer_intel",
        "review_required": ["先确认本轮要推进哪条 lead。"],
        "record_payloads": records,
    }


def intel_stage_asset(
    report: dict[str, Any],
    combo_run_id: str,
    lead_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    identity = report.get("identity_snapshot") or {}
    company = report.get("company_profile") or {}
    evidence_rows = report.get("evidence") or []
    decision = report.get("intel_decision") or {}
    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "workflow_id": workflow_id,
            "generated_at": report.get("generated_at") or utc_now_iso(),
        },
        "runtime_contract": stage_runtime_contract("customer_intel"),
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
                "evidence_sufficiency": decision.get("evidence_sufficiency"),
                "recommended_next_action": decision.get("recommended_next_action"),
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
                "evidence_sufficiency": decision.get("evidence_sufficiency"),
                "recommended_next_action": decision.get("recommended_next_action"),
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
                    "Evidence Sufficiency": decision.get("evidence_sufficiency"),
                    "Recommended Next Action": decision.get("recommended_next_action"),
                },
            ),
            kv_block("Company Profile", company),
            bullet_block(identity.get("ambiguity_notes") or [], title="Ambiguity Notes"),
            bullet_block(report.get("unconfirmed_fact_list") or [], title="未确认事实清单"),
            table_block("Digital Footprint", report.get("digital_footprint") or []),
            table_block("Interest Signals", report.get("interest_signals") or []),
            table_block("Sales Angles", report.get("sales_angles") or []),
            bullet_block(report.get("risk_reasons") or [], title="Risk Reasons"),
            table_block("Evidence", evidence_rows),
        ],
        "upstream_refs": [
            {"stage_name": "lead_screening", "asset_key": f"screening-record:{combo_run_id}:{lead_id}"}
        ],
        "next_action": decision.get("recommended_next_action"),
        "review_required": [
            "人工确认主体匹配、风险评级和销售切入角度。",
            "仅在确认公开事实无误且证据充足时再进入开发信。",
        ],
        "asset_binding": {
            "asset_mode": "doc",
            "target_doc_folder": "Customer Intel Docs",
            "asset_key": f"intel-doc:{workflow_id}",
            "reuse_strategy": "reuse_existing_doc_then_append_version_section",
        },
    }


def email_stage_asset(
    email_input: dict[str, Any],
    email_output: dict[str, Any],
    combo_run_id: str,
    lead_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    scenario = email_output.get("scenario") or {}
    workflow_guidance = email_output.get("workflow_guidance") or {}
    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "workflow_id": workflow_id,
            "generated_at": utc_now_iso(),
        },
        "runtime_contract": stage_runtime_contract("outreach_email"),
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
                "send_policy": email_output.get("send_policy"),
                "recommended_next_action": workflow_guidance.get("recommended_next_action"),
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
                "send_policy": email_output.get("send_policy"),
                "recommended_next_action": workflow_guidance.get("recommended_next_action"),
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
                    "Send Policy": email_output.get("send_policy"),
                },
            ),
            bullet_block(email_output.get("subject_options") or [], title="Subject Options"),
            paragraph_block((email_output.get("drafts") or {}).get("version_a") or ""),
            paragraph_block((email_output.get("drafts") or {}).get("version_b") or ""),
            bullet_block(email_output.get("review_notes") or [], title="Review Notes"),
            bullet_block(email_output.get("evidence_signals_used") or [], title="Evidence Signals Used"),
            bullet_block(email_output.get("unconfirmed_fact_checklist") or [], title="未确认事实清单"),
        ],
        "upstream_refs": [
            {"stage_name": "customer_intel", "asset_key": f"intel-doc:{workflow_id}"}
        ],
        "next_action": workflow_guidance.get("recommended_next_action"),
        "review_required": [
            "复核邮件中所有客户事实和商务表述。",
            "默认只允许人工确认后发送，不进入自动外发。",
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
        if (intel_payload.get("summary_fields") or {}).get("recommended_next_action") == "ready_for_email_draft":
            return "customer_intel", "ready_for_email_draft"
        return "customer_intel", "hold_for_manual_review"
    if action == "ready_for_customer_intel":
        return "lead_screening", "waiting_selection"
    if action == "needs_enrichment":
        return "lead_screening", "needs_enrichment"
    return "lead_screening", "hold_for_manual_review"


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
        search_fields = (search_index.get(lead_id) or {}).get("table_fields") or {}
        screening_fields = screening_record.get("table_fields") or {}
        intel_fields = intel_payload.get("table_fields") if intel_payload and lead_id == selected_lead_id else {}
        email_fields = email_payload.get("table_fields") if email_payload and lead_id == selected_lead_id else {}
        search_asset_key = ((search_index.get(lead_id) or {}).get("asset_binding") or {}).get("asset_key")
        screening_asset_key = (screening_record.get("asset_binding") or {}).get("asset_key")
        intel_asset_key = (intel_payload.get("asset_binding") or {}).get("asset_key") if intel_payload and lead_id == selected_lead_id else ""
        email_asset_key = (email_payload.get("asset_binding") or {}).get("asset_key") if email_payload and lead_id == selected_lead_id else ""
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
                    "legacy_recommended_next_action": screening_action_legacy(
                        screening_fields.get("recommended_next_action", "")
                    ),
                    "evidence_grade": search_fields.get("evidence_grade"),
                    "risk_rating": (intel_fields or {}).get("risk_rating"),
                    "entity_confidence": (intel_fields or {}).get("entity_confidence"),
                    "evidence_sufficiency": (intel_fields or {}).get("evidence_sufficiency"),
                    "send_policy": (email_fields or {}).get("send_policy"),
                    "last_updated_at": utc_now_iso(),
                    "search_asset_ref": search_asset_key,
                    "screening_asset_ref": screening_asset_key,
                    "intel_asset_ref": intel_asset_key,
                    "email_asset_ref": email_asset_key,
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


def render_container_bundle_markdown(bundle: dict[str, Any]) -> str:
    meta = bundle.get("workflow_meta") or {}
    lines = [
        "# Container Bundle",
        "",
        "## Summary",
        f"- Combo Run ID: {meta.get('combo_run_id', '')}",
        f"- Selected Lead ID: {meta.get('selected_lead_id', '')}",
        f"- Bundle Scope: {meta.get('bundle_scope', '')}",
        "",
        "## Modes",
        "- 课堂稳定模式：固定样例、固定桥接、稳定演示。",
        "- 真实业务模式：真实输入、结果受公开数据质量影响。",
        "",
        "## Data Containers",
        "- 保底容器：JSON / Markdown / CSV",
        "- 课堂标准沙盘：Feishu Sandbox Adapter",
        "- 企业真实容器：CRM / ERP / 邮箱草稿箱（本轮只留扩展位）",
        "",
        "## Lead Workflow Master",
    ]
    for row in bundle.get("master_records") or []:
        lines.extend(
            [
                "",
                f"### {row.get('lead_id')} | {row.get('company_name')}",
                f"- Current Stage: {row.get('current_stage')}",
                f"- Current Status: {row.get('current_status')}",
                f"- Recommended Next Action: {row.get('recommended_next_action')}",
                f"- Evidence Grade: {row.get('evidence_grade', '') or '(missing)'}",
                f"- Risk Rating: {row.get('risk_rating', '') or '(missing)'}",
                f"- Send Policy: {row.get('send_policy', '') or '(missing)'}",
            ]
        )
    return "\n".join(lines) + "\n"


def render_master_records_csv(rows: list[dict[str, Any]]) -> str:
    fieldnames = [
        "workflow_id",
        "lead_id",
        "company_name",
        "person_name",
        "email",
        "country_or_market",
        "current_stage",
        "current_status",
        "recommended_next_action",
        "legacy_recommended_next_action",
        "evidence_grade",
        "risk_rating",
        "entity_confidence",
        "evidence_sufficiency",
        "send_policy",
        "search_asset_ref",
        "screening_asset_ref",
        "intel_asset_ref",
        "email_asset_ref",
        "combo_run_id",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in fieldnames})
    return buffer.getvalue()


def dump_text(text: str, path: str | Path) -> None:
    Path(path).write_text(text, encoding="utf-8")

