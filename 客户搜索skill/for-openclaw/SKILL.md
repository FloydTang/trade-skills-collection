---
name: trade-lead-discovery-openclaw
description: Discover prospect companies from a structured OpenClaw search brief and output a conservative candidate list ready for lead screening.
openclaw_role: stage_worker
workspace_owner_skill: trade-active-outreach-combo
single_skill_policy: attach_only
feishu_container_creation: forbidden
requires_master_base: true
requires_master_record: true
---

# 客户搜索 / 线索发现 Skill for OpenClaw

## Overview

这个变体假设搜索意图已经由 OpenClaw 工作流整理好。

Python 层只负责：

- 生成查询
- 发现候选客户
- 输出可桥接到线索整理 Skill 的结果

## Enhancement Entry

增强权益不在仓库中展开正文。

如需飞书落地、统一编排或多代理协作，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/ADmiwiultihx6Yk1p2UcjfmVn6d>
