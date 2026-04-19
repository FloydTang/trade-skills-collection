from __future__ import annotations

from typing import Any

from .container_bundle import (
    email_stage_asset,
    intel_stage_asset,
    master_index_schema,
    master_records,
    screening_stage_asset,
    search_stage_asset,
)
from .contracts import STAGE_WORKER_SKILLS, WORKFLOW_OWNER_SKILL, compact_dict, utc_now_iso


def _feishuize(payload: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(payload)
    runtime_contract = adapted.pop("runtime_contract", None)
    if runtime_contract:
        adapted["feishu_runtime_contract"] = dict(runtime_contract)
        adapted["feishu_runtime_contract"]["feishu_container_creation"] = adapted["feishu_runtime_contract"].pop(
            "container_creation"
        )
        adapted["feishu_runtime_contract"]["requires_master_base"] = adapted["feishu_runtime_contract"].pop(
            "requires_master_container"
        )
        adapted["feishu_runtime_contract"]["forbid_stage_level_base_bootstrap"] = adapted[
            "feishu_runtime_contract"
        ].pop("forbid_stage_level_container_bootstrap")
    return adapted


def search_stage_payload(report: dict[str, Any], combo_run_id: str) -> dict[str, Any]:
    return _feishuize(search_stage_asset(report, combo_run_id))


def screening_stage_payload(report: dict[str, Any], combo_run_id: str) -> dict[str, Any]:
    return _feishuize(screening_stage_asset(report, combo_run_id))


def intel_stage_payload(
    report: dict[str, Any],
    combo_run_id: str,
    lead_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    return _feishuize(intel_stage_asset(report, combo_run_id, lead_id, workflow_id))


def email_stage_payload(
    email_input: dict[str, Any],
    email_output: dict[str, Any],
    combo_run_id: str,
    lead_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    return _feishuize(email_stage_asset(email_input, email_output, combo_run_id, lead_id, workflow_id))


def master_table_schema() -> dict[str, Any]:
    schema = dict(master_index_schema())
    schema["table_name"] = schema.pop("schema_name")
    return schema


def build_feishu_sandbox_bundle(
    search_payload: dict[str, Any],
    screening_payload: dict[str, Any],
    intel_payload: dict[str, Any] | None,
    email_payload: dict[str, Any] | None,
    combo_run_id: str,
    selected_lead_id: str,
    workflow_id: str,
) -> dict[str, Any]:
    return {
        "workflow_meta": {
            "combo_run_id": combo_run_id,
            "selected_lead_id": selected_lead_id,
            "workflow_id": workflow_id,
            "generated_at": utc_now_iso(),
            "bundle_scope": "trade-skill-collection-feishu-sandbox-handoff",
            "workspace_owner_skill": WORKFLOW_OWNER_SKILL,
        },
        "openclaw_install_contract": {
            "container_owner": "active_outreach_combo",
            "container_mode": "single_base_multi_table",
            "single_skill_policy": "attach_only",
            "workflow_owner": {
                "skill_name": WORKFLOW_OWNER_SKILL,
                "role": "workflow_owner",
                "repo_path": "主动开发链路组合包",
            },
            "stage_workers": [
                {
                    "skill_name": STAGE_WORKER_SKILLS["lead_discovery"],
                    "role": "stage_worker",
                    "stage_name": "lead_discovery",
                    "feishu_container_creation": "forbidden",
                    "requires_master_base": True,
                    "requires_master_record": True,
                },
                {
                    "skill_name": STAGE_WORKER_SKILLS["lead_screening"],
                    "role": "stage_worker",
                    "stage_name": "lead_screening",
                    "feishu_container_creation": "forbidden",
                    "requires_master_base": True,
                    "requires_master_record": True,
                },
                {
                    "skill_name": STAGE_WORKER_SKILLS["customer_intel"],
                    "role": "stage_worker",
                    "stage_name": "customer_intel",
                    "feishu_container_creation": "forbidden",
                    "requires_master_base": True,
                    "requires_master_record": True,
                },
                {
                    "skill_name": STAGE_WORKER_SKILLS["outreach_email"],
                    "role": "stage_worker",
                    "stage_name": "outreach_email",
                    "feishu_container_creation": "forbidden",
                    "requires_master_base": True,
                    "requires_master_record": True,
                },
            ],
        },
        "workspace_container": {
            "container_type": "single_base_workspace",
            "base_name": "Trade Lead Workflow Hub",
            "base_reuse_policy": "reuse_existing_base_before_create",
            "create_new_base_when_missing": True,
            "forbid_parallel_bases_for_each_stage": True,
            "workspace_owner_skill": WORKFLOW_OWNER_SKILL,
            "single_skill_attach_only": True,
            "forbid_stage_level_base_bootstrap": True,
            "tables": [
                {
                    "table_name": "Lead Workflow Master",
                    "role": "master_index",
                    "bootstrap_mode": "create_if_missing_then_reuse",
                },
                {
                    "table_name": "Lead Discovery Results",
                    "role": "stage_table",
                    "bootstrap_mode": "create_if_missing_then_reuse",
                },
                {
                    "table_name": "Lead Screening Results",
                    "role": "stage_table",
                    "bootstrap_mode": "create_if_missing_then_reuse",
                },
            ],
            "doc_spaces": [
                "Customer Intel Docs",
                "Outreach Email Docs",
                "Run Logs",
                "Failure Notes",
            ],
        },
        "master_table_schema": master_table_schema(),
        "stage_assets": {
            "lead_discovery": search_payload,
            "lead_screening": screening_payload,
            "customer_intel": intel_payload,
            "outreach_email": email_payload,
        },
        "master_records": master_records(
            search_payload,
            screening_payload,
            intel_payload,
            email_payload,
            combo_run_id,
            selected_lead_id,
        ),
        "openclaw_handoff": {
            "execution_order": [
                "create_or_open_workspace_base",
                "create_or_open_required_tables",
                "create_or_open_master_table",
                "resolve_or_create_master_record",
                "upsert_lead_discovery_records",
                "upsert_lead_screening_records",
                "create_or_update_customer_intel_doc_for_selected_lead",
                "create_or_update_outreach_email_doc_for_selected_lead",
                "write_back_master_records",
            ],
            "stage_asset_types": {
                "lead_discovery": "table_record_batch",
                "lead_screening": "table_record_batch",
                "customer_intel": "doc",
                "outreach_email": "doc",
            },
            "master_writeback_rules": [
                "搜索阶段写回 evidence_grade、next_action 和主表 current_status。",
                "recommended_next_action=ready_for_customer_intel 但未被本轮选中时，current_status=waiting_selection。",
                "recommended_next_action=needs_enrichment 时，不创建背调文档。",
                "开发信草稿完成后，主表 current_stage=outreach_email, current_status=draft_ready。",
                "URL 字段不是首次试跑硬前置，主表默认写文本 asset_ref。",
                "失败时也要回写 current_stage/current_status/failure_reason/last_updated_at。",
            ],
            "single_skill_attach_rules": [
                "单独跑客户背调时，也必须先查 Lead Workflow Master。",
                "单独跑开发信时，也必须先查 Lead Workflow Master。",
                "同一 lead 后续补跑其他节点时，优先更新原主记录。",
                "找不到原记录时，才允许创建最小主记录。",
            ],
            "workflow_owner_rules": [
                "只有主动开发链路组合包允许声明或初始化飞书课堂沙盘容器。",
                "单节点 Skill 只允许产出阶段 payload，不允许独立创建 Base 或主表。",
                "OpenClaw 安装入口默认先识别 workflow_owner，再加载 stage_worker。",
            ],
            "lead_match_policy": {
                "primary_key": "lead_id",
                "secondary_keys": [
                    "company_name",
                    "company_website_or_domain",
                    "email",
                ],
                "on_ambiguity": "write_failure_reason_and_hold_for_manual_review",
            },
            "rerun_policy": {
                "table_records": "按 combo_run_id + lead_id upsert，避免重复插入。",
                "intel_doc": "优先复用已存在文档，再追加本次版本区块。",
                "email_doc": "优先复用已存在文档，再追加新草稿版本。",
                "master_record": "优先复用原 lead 主记录，不新建平行 lead。",
            },
            "failure_writeback_policy": {
                "always_write_master_status": True,
                "required_fields": [
                    "current_stage",
                    "current_status",
                    "failure_reason",
                    "last_updated_at",
                ],
                "keep_partial_assets": True,
            },
        },
    }

