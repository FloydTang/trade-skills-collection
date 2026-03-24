# 线索整理 / 初筛 Skill

当前状态：可交付

这个目录用于把搜索阶段得到的零散客户名单、网址、联系人线索和备注，整理成可继续进入客户背调的标准输入。

定位：

- 把“搜到很多零散结果，但没法继续判断”的问题变成标准化整理动作
- 先服务主动开发链路中的中间承接层
- 首版优先解决字段统一、缺失识别和初步分类，不直接做复杂评分系统

当前立项范围：

- 首版先聚焦“线索整理 + 初筛提示”
- 先不做复杂 CRM、提醒系统或长期数据库
- 先保证输出能稳定进入 `客户背调skill/`

当前计划最小能力：

- 输入候选客户名单或单条线索 JSON
- 输出统一字段后的线索池
- 标注关键缺失项
- 给出初步分类和补查建议
- 产出可直接桥接到客户背调 Skill 的标准输入字段

与现有链路的关系：

- 上游：`客户搜索 / 线索发现`
- 下游：`客户背调skill/`
- 后续可继续承接：`开发信skill/`、`跟进优先级skill/`

当前目录结构：

```text
.
├── README.md
├── SKILL.md
├── 立项方案.md
├── 验收记录.md
├── scripts/
│   ├── build_lead_screening_report.py
│   ├── build_customer_intel_batch_input.py
│   ├── run_regression_checks.py
│   └── run_pre_release_gate.py
├── examples/
├── references/
├── schemas/
└── for-openclaw/
```

当前最小能力：

- 输入一批零散候选线索 JSON
- 输出统一字段后的结构化线索池
- 标注缺失字段、人工复核原因和下一步动作
- 生成兼容 `客户背调skill/` 的 `customer_intel_input`
- 提供固定样例输出、回归检查和发布前 gate
- 提供最小 `for-openclaw/` 变体

当前结论：

- 已达到“可演示”
- 已达到“可交付”
- 采用“双轨逻辑”维护：可作为独立仓库发布，也可作为合集仓库中的稳定节点副本分发
- 独立仓库：`https://github.com/FloydTang/trade-lead-screening`

## 快速运行

```bash
python3 ./scripts/build_lead_screening_report.py \
  --input-json ./examples/sample-leads.json \
  --markdown-out /tmp/lead-screening.md \
  --json-out /tmp/lead-screening.json
```

```bash
python3 ./scripts/build_customer_intel_batch_input.py \
  --input-json ./examples/sample-output.json \
  --json-out /tmp/customer-intel-batch.json
```

```bash
python3 ./scripts/run_regression_checks.py
```

```bash
python3 ./scripts/run_pre_release_gate.py
```

## 发布前流程

发布前固定执行：

1. `python3 ./scripts/run_pre_release_gate.py`
2. 如有规则或模板改动，重新生成受影响的 `examples/*-output.md` 和 `examples/*-output.json`
3. 确认 `README.md`、`验收记录.md` 和 `for-openclaw/README.md` 没有状态漂移

## OpenClaw 变体

`for-openclaw/` 是这个 Skill 的 OpenClaw-native 包装版本：

- 保留当前本地版的保守整理原则
- 假设上游搜索结果已经由 OpenClaw 工作流整理成线索包
- Python 包装脚本只负责字段规范化、初筛提示和下游背调桥接字段生成

## 作者

半斤九两科技
