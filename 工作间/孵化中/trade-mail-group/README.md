---
title: trade-mail-group / 客群分组开发信 Skill
aliases: []
type: tool
status: active
area: tool
updated: '2026-05-28'
tags:
- 主题/AI外贸
- 主题/客户开发
- 主题/工具系统
- 资产/Skill
- 工作流/Skill开发
- 主题/知识库
- 主题/课程交付
related:
- "[[路线映射]]"
business_scenes:
- 外贸主动开发
- 知识库与资料承接
- 工具评估与Agent治理
- 课程与交付
---
# trade-mail-group / 客群分组开发信 Skill

当前状态：可交付扩展节点，已通过 HomeMac OpenClaw `skill_tester` 复核，并迁入正式工具库。

这个目录用于把作战台里的 `Mail Group 专用执行词` 升级成可验证的单节点 Skill。

## 定位

面向已经有一批客户名单、但还没有分组触达策略的主动开发场景。

它不负责发信，不配置 SMTP，不承诺回复率。它只负责把客户名单整理成可人工复核的分组、触达角度、标题候选、首封草稿和跟进节奏。

## 当前落地边界

- Skill 本体源：当前目录
- Obsidian 展现层：`工具工作间/02_场景拆解/外贸业务主干Skill/制作中/trade-mail-group`
- 最终工具库：`半斤九两工具库/外贸业务主干Skill/主动开发链路组合包/子Skill与工具本体/客群分组开发信skill`

## 当前已有材料

- `立项方案.md`
- `验收清单.md`
- `SKILL.md`
- `examples/minimal-input.json`
- `examples/minimal-output.md`
- `examples/minimal-output.json`
- `examples/public-germany-input.json`
- `examples/public-germany-output.md`
- `examples/public-germany-output.json`
- `examples/jitsteel-real-business-public-input.json`
- `examples/jitsteel-real-business-public-output.md`
- `examples/jitsteel-real-business-public-output.json`
- `examples/meta-leads-visible-redacted-input.json`
- `examples/meta-leads-visible-redacted-output.md`
- `examples/meta-leads-visible-redacted-output.json`
- `agents/openai.yaml`
- `scripts/validate_examples.py`

## 下一步

1. 工具库正式读取。
2. 如果后续继续用 Meta 线索做真实业务分组，先导出完整表单字段并脱敏。
