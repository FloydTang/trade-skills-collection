---
title: trade-social-account-scan / 社媒账号初步调研 Skill
aliases: []
type: tool
status: draft
area: tool
updated: '2026-05-21'
tags:
- 主题/AI外贸
- 主题/工具系统
- 资产/Skill
- 工作流/Skill开发
- 主题/B2B营销
- 主题/知识库
- 主题/课程交付
related:
- "[[路线映射]]"
business_scenes:
- 外贸主动开发
- 竞品监控与市场情报
- 知识库与资料承接
- 工具评估与Agent治理
- 课程与交付
---
# trade-social-account-scan / 社媒账号初步调研 Skill

当前状态：可演示前验证中

这个目录用于把作战台里的 `社媒账号初步调研执行词` 升级成可验证的单节点 Skill。

## 定位

面向主动开发前的公开来源补查。它帮助业务员判断某家公司或竞品是否存在值得继续背调的公开社媒线索。

它不是官方账号确认器，不下载对方内容，不复刻对方账号，不把个人账号直接当公司账号。

2026-05-21 起，TikTok / 视频营销深度拆解并入 `外贸业务主干Skill` 的内容营销 / TikTok 陪跑分支。本 Skill 只保留客户或竞品公开社媒账号初筛和证据边界。

## 当前落地边界

- 仓库真实源：当前目录
- Obsidian 展现层：`工具工作间/02_场景拆解/外贸业务主干Skill/制作中/trade-social-account-scan`
- 最终工具库：暂不进入，等公开样例验证通过后再判断

## 当前已有材料

- `立项方案.md`
- `验收清单.md`
- `examples/minimal-input.json`

## 下一步

1. 先用公开网页搜索路径跑 3 类样例：客户公司、竞品公司、弱社媒公司。
2. 再验证 Sherlock / Maigret 是否能降低搜索成本，而不是增加误报。
3. 如发现值得深挖的 TikTok / 视频内容信号，只输出到外贸业务主干 Skill 的内容营销分支，不在本 Skill 内继续展开。
4. 样例稳定后，再补 `SKILL.md` 和输出样例。
