# Trade Lead Discovery

用公开网页和 LinkedIn 结果线索，找出第一批可继续进入线索整理的候选客户。

An open-source Codex skill for discovering the first batch of public-web prospect companies and turning them into a structured lead list ready for screening.

当前状态：可交付

角色定位：`客户搜索员`

职责边界：

- 负责公开线索发现和候选名单生成
- 不负责字段标准化初筛
- 不负责深度客户背调
- 不负责开发信生成

上下游关系：

- 上游：产品、市场、客户类型、关键词 brief
- 下游：`线索整理skill`

## 这个仓库适合谁

- 知道产品、市场和客户类型，但不会系统搜客户的人
- 想快速做出一批公开候选名单的人
- 想搭建 `客户搜索 -> 线索整理 -> 客户背调 -> 开发信` 链路的人

## What It Does

- 生成固定搜索查询
- 搜公开网页结果和 LinkedIn 公司结果线索
- 去重并整理成结构化候选名单
- 输出来源链接、可见联系人线索和补查建议
- 桥接成 `线索整理skill/` 输入

## Repository Structure

```text
.
├── README.md
├── SKILL.md
├── 立项方案.md
├── 验收记录.md
├── scripts/
│   ├── build_lead_discovery_report.py
│   ├── build_lead_screening_input.py
│   ├── run_regression_checks.py
│   └── run_pre_release_gate.py
├── examples/
├── references/
├── schemas/
└── for-openclaw/
```

## Quick Start

```bash
python3 ./scripts/build_lead_discovery_report.py \
  --input-json ./examples/frozen-food-search.json \
  --markdown-out /tmp/lead-discovery.md \
  --json-out /tmp/lead-discovery.json
```

```bash
python3 ./scripts/build_lead_screening_input.py \
  --input-json ./examples/frozen-food-output.json \
  --json-out /tmp/lead-screening-input.json
```

```bash
python3 ./scripts/run_regression_checks.py
```

```bash
python3 ./scripts/run_pre_release_gate.py
```

## Verification Status

当前版本包含：

- 固定样例输入输出
- 回归检查
- pre-release gate
- 最小 `for-openclaw/` 变体
- 与 `线索整理skill/` 的桥接输出
- 独立仓库：`https://github.com/FloydTang/trade-lead-discovery`

真实联网验证情况：

- 当前脚本已验证到“联网搜索失败时不崩溃”
- 在当前环境下，真实搜索结果仍受 DuckDuckGo / 搜索源可用性影响，可能返回空候选
- 因此发布判断主要基于固定 fixtures、回归脚本和 gate，而不是实时搜索结果数量

## Chain Position

推荐链路：

`客户搜索skill -> 线索整理skill -> 客户背调skill -> 开发信skill`

关联仓库：

- 线索整理 Skill: [trade-lead-screening](https://github.com/FloydTang/trade-lead-screening)
- 客户背调 Skill: [trade-customer-intel](https://github.com/FloydTang/trade-customer-intel)
- 开发信 Skill: [trade-outreach-email](https://github.com/FloydTang/trade-outreach-email)

## OpenClaw Variant

`for-openclaw/` 提供最小 OpenClaw 包装版本：

- 假设搜索参数已由上游流程整理
- 输出仍保持保守候选发现逻辑

如果你要在龙虾多代理模式里使用这个节点，优先看：

- 仓库内安装范围说明：`../OPENCLAW.md`
- 当前推荐安装顺序：`../当前推荐安装清单.md`

这里再固定一条口径，避免误读：

- 当前节点开源版可以独立使用
- 但在 OpenClaw 安装语境下，当前节点不是平级安装归口，而是 `主动开发链路组合包` 下的 `stage_worker`
- `for-openclaw/` 是运行时变体，不是新的主安装包
- 飞书增强入口只认仓库根目录的 `README.md`、`OPENCLAW.md`、`当前推荐安装清单.md`

## 作者

半斤九两科技
