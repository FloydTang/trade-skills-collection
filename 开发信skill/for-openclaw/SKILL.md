---
name: trade-outreach-email-for-openclaw
description: OpenClaw-native version of the foreign-trade outreach email skill. Use structured operator input plus public-context summaries to generate conservative first-touch or follow-up email drafts without overstating inferred facts.
openclaw_role: stage_worker
workspace_owner_skill: trade-active-outreach-combo
single_skill_policy: attach_only
feishu_container_creation: forbidden
requires_master_base: true
requires_master_record: true
---

# 开发信 Skill for OpenClaw

## Overview

这个版本面向 OpenClaw 云端工作流。

它假设操作员输入和公开资料摘要已经由上游节点整理好，然后由当前脚本进行保守合并，并调用根目录里的核心草稿生成器输出统一结构的邮件包。

## Inputs

最终输入应为：

```json
{
  "operator_input": {},
  "public_context": {}
}
```

其中：

- `operator_input` 提供邮件场景、产品、目标、发件人等明确业务输入
- `public_context` 提供客户画像摘要、历史沟通、风险提示和推荐切入角度

## Rules

- 以 `operator_input` 为主，不自动覆盖
- 以 `public_context` 为辅，只做保守补充
- `High` 风险时提醒人工复核，不默认终止输出
- `follow_up` 仍要求有历史沟通上下文

## Main Script

使用 [build_email_draft_from_openclaw.py](./scripts/build_email_draft_from_openclaw.py)。

```bash
python3 ./for-openclaw/scripts/build_email_draft_from_openclaw.py \
  --input-json ./for-openclaw/examples/sample-input.json
```

## Output

- 输出结构与根目录版本一致
- 保留中文复核提示
- 不自动发送邮件

## Feishu Runtime Contract

- 当前角色固定为 `stage_worker`
- 默认只允许附着到 `Trade Lead Workflow Hub`
- 不允许独立创建 Base、主表或平行工作容器
