---
name: trade-active-outreach-combo
description: Run a minimal active-outreach workflow by reusing four existing foreign-trade skills: lead discovery, lead screening, customer intel, and outreach email. Use when an operator wants a conservative end-to-end demo with visible intermediate artifacts and a final editable email draft.
openclaw_role: workflow_owner
container_owner: active_outreach_combo
container_mode: single_base_multi_table
single_skill_policy: attach_only
---

# 主动开发最小闭环链路组合包

## Overview

用这个组合包把以下 4 个已可用节点串成一条最小主动开发闭环：

`客户搜索skill -> 线索整理skill -> 客户背调skill -> 开发信skill`

只做三件事：

- 串联 4 个现有节点
- 保留中间产物
- 明确人工复核点
- 输出中立容器 bundle，再按需派生到课堂沙盘

## Workflow

1. Run lead discovery in fixture-backed classroom mode for a stable demo start.
2. Convert discovery output into the lead-screening input shape.
3. Run lead screening and export the customer-intel batch payload.
4. Select one lead for the reviewed customer-intel stage.
5. Reuse the reviewed customer-intel fixture for stable downstream demonstration.
6. Bridge the intel report into outreach-email input.
7. Generate editable English outreach drafts and review notes.
8. Export `ContainerBundle` to JSON / Markdown / CSV and Feishu Sandbox Adapter.

## Output Requirements

- 必须生成阶段化中间产物
- 必须保留人工复核点
- 必须明确这是固定样例链路，不是实时联网结果承诺
- 必须输出最终邮件草稿和中间桥接 JSON
- 必须输出容器中立的 `ContainerBundle`
- 不能把推断写成确定事实
- 不能把邮件草稿写成可直接自动发送
- 不能把飞书写成唯一数据容器

## Main Script

- [run_minimal_demo.py](./scripts/run_minimal_demo.py)

### Example

```bash
python3 ./主动开发链路组合包/scripts/run_minimal_demo.py
```

## Enhancement Entry

如需数据留存、统一编排、多代理协作或飞书落地，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>

仓库内不展开增强权益正文。
