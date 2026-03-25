---
name: trade-active-outreach-combo
description: Run a minimal active-outreach workflow by reusing four existing foreign-trade skills: lead discovery, lead screening, customer intel, and outreach email. Use when an operator, student, or agent user wants a conservative, reproducible end-to-end demo with visible intermediate artifacts, clear review checkpoints, and a final editable email draft.
---

# 主动开发最小闭环链路组合包

## Overview

用这个组合包把以下 4 个已可用节点串成一条最小主动开发闭环：

`客户搜索skill -> 线索整理skill -> 客户背调skill -> 开发信skill`

它的目标不是替代四个单节点，也不是直接做总编排器，而是：

- 给学员和 agent 用户一个能直接跑起来的闭环样板
- 保留每一步中间产物，方便复核、教学和排错
- 让公开仓库用户更容易理解这 4 个节点如何衔接

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
