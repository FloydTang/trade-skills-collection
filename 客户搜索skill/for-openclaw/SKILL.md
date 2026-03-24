---
name: trade-lead-discovery-openclaw
description: Discover prospect companies from a structured OpenClaw search brief and output a conservative candidate list ready for lead screening.
---

# 客户搜索 / 线索发现 Skill for OpenClaw

## Overview

这个变体假设搜索意图已经由 OpenClaw 工作流整理好。

Python 层只负责：

- 生成查询
- 发现候选客户
- 输出可桥接到线索整理 Skill 的结果
