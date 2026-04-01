---
name: trade-active-outreach-combo
description: Run a minimal active-outreach workflow by reusing four existing foreign-trade skills: lead discovery, lead screening, customer intel, and outreach email. Use when an operator, student, or agent user wants a conservative, reproducible end-to-end demo with visible intermediate artifacts, clear review checkpoints, and a final editable email draft.
openclaw_role: workflow_owner
container_owner: active_outreach_combo
container_mode: single_base_multi_table
single_skill_policy: attach_only
---

# 主动开发最小闭环链路组合包

## Overview

用这个组合包把以下 4 个已可用节点串成一条最小主动开发闭环：

`客户搜索skill -> 线索整理skill -> 客户背调skill -> 开发信skill`

角色定位：

- `主动开发编排员`
- 负责串联 4 个已完成节点、保留中间产物并设置人工复核点
- 不负责重写各节点内部逻辑，也不负责假装自己是新的总 Skill

编排范围：

- 上游：固定样例或人工给定的搜索 brief
- 下游：人工复核后的实际业务动作
- 当前只编排 `客户搜索skill`、`线索整理skill`、`客户背调skill`、`开发信skill`

它的目标不是替代四个单节点，也不是直接做总编排器，而是：

- 给学员和 agent 用户一个能直接跑起来的闭环样板
- 保留每一步中间产物，方便复核、教学和排错
- 让公开仓库用户更容易理解这 4 个节点如何衔接

当前边界：

- 当前只围绕这 4 个已完成节点运行
- 不把母目录里其他占位目录默认视为当前可调用链路的一部分
- 当前优先目标是把这 4 个节点持续测试、验证和修补稳定

## OpenClaw Ownership

这个组合包是当前唯一允许声明飞书工作容器的 OpenClaw 入口。

固定角色：

- `workflow_owner`
- 负责声明 `Trade Lead Workflow Hub`
- 负责声明 `Lead Workflow Master`、`Lead Discovery Results`、`Lead Screening Results`
- 负责要求单节点只以 attach 模式回挂主 Base 和主记录

## Standard Input

这个组合包当前优先使用固定样例模式。

组合包自带的入口样例在：

- [fixed-search-brief.json](./examples/fixed-search-brief.json)

当前脚本默认还会复用：

- `客户搜索skill/examples/frozen-food-output.json`
- `主动开发链路组合包/examples/reviewed-customer-intel-report.json`

如果只想先跑通，不需要先手工准备新的输入文件。

## Workflow

1. Reuse the fixed lead-discovery output for a stable demo start.
2. Convert discovery output into the lead-screening input shape.
3. Run lead screening and export the customer-intel batch payload.
4. Select one lead for the reviewed customer-intel stage.
5. Reuse the reviewed customer-intel fixture for stable downstream demonstration.
6. Bridge the intel report into outreach-email input.
7. Generate editable English outreach drafts and review notes.

## Output Requirements

- 必须生成阶段化中间产物
- 必须保留人工复核点
- 必须明确这是固定样例链路，不是实时联网结果承诺
- 必须输出最终邮件草稿和中间桥接 JSON
- 不能把推断写成确定事实
- 不能把邮件草稿写成“可直接自动发送”
- 不能复制四个节点的内部实现
- 不能把母目录其他占位 Skill 默认纳入当前编排范围

## Main Script

默认入口脚本：

- [run_minimal_demo.py](./scripts/run_minimal_demo.py)

### Example

```bash
python3 ./主动开发链路组合包/scripts/run_minimal_demo.py
```

```bash
python3 ./主动开发链路组合包/scripts/run_minimal_demo.py \
  --product-or-offer "frozen broccoli and mixed vegetables" \
  --sender-name "Leo" \
  --sender-company "Ningbo FreshGrow Foods"
```

## Review Checkpoints

以下节点默认必须人工复核：

- `03-lead-screening-output.*` 里的推荐下一步动作
- `05-selected-customer-intel-input.json` 是否与当前演示目标一致
- `06-customer-intel-report.json` 里的主体匹配、风险评级和销售角度
- `08-email-draft.md` 里的所有客户事实和商务表述

## Defaults

- 当前优先公开可安装版本
- 当前优先固定样例模式
- 当前不要求实时联网稳定可用
- 当前不做自动发信
- 当前不做 CRM 回写
- 当前输出优先服务演示、复用和后续改造
