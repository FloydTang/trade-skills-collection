# 开发信 Skill

当前状态：可交付

这个目录用于把客户基础信息、客户画像摘要和跟进阶段，转成可人工修改后发送的外贸英文邮件草稿。

定位：

- 把客户基础信息、客户画像、产品信息和跟进阶段转成可直接修改发送的外贸邮件
- 优先覆盖首轮开发信、报价邮件、跟进邮件

当前立项范围：

- 首版先聚焦“首轮开发信 + 跟进邮件”
- 先不做报价邮件，避免输入项和业务分支过早膨胀
- 输出以可直接人工修改的英文邮件草稿为主，中文说明用于复核

当前目录结构：

```text
.
├── README.md
├── SKILL.md
├── 立项方案.md
├── 验收记录.md
├── scripts/
│   ├── build_email_draft.py
│   ├── build_email_input_from_customer_intel.py
│   ├── run_regression_checks.py
│   └── run_pre_release_gate.py
├── examples/
│   ├── first-touch.json
│   ├── follow-up.json
│   ├── solar-first-touch.json
│   ├── textile-follow-up.json
│   └── customer-intel-report.json
└── references/
    ├── input-fields.md
    ├── output-template.md
    ├── review-rules.md
    └── customer-intel-integration.md
└── schemas/
    └── email-draft-input.schema.json
└── for-openclaw/
    ├── README.md
    ├── SKILL.md
    ├── examples/
    ├── references/
    ├── schemas/
    └── scripts/
```

当前最小能力：

- 输入 `first_touch` 或 `follow_up` 两类邮件场景
- 输出英文标题候选、英文正文草稿、中文复核提示、输入依据回显
- 默认本地运行，不依赖联网
- 支持把“客户背调 Skill”的 JSON 报告桥接成开发信输入
- 已提供固定样例输出，适合课程演示和后续改造
- 已补正式输入 schema 和字段说明
- 已提供最小回归检查脚本
- 已提供发布前 gate 脚本
- 已补最小 `for-openclaw/` 变体

当前结论：

- 已达到“可演示”
- 已达到“可交付”
- 后续增强项见 `/Users/evenbetter/Downloads/C&CStudio/外贸skill/开发信skill/验收记录.md`
- 采用“双轨逻辑”维护：可作为独立仓库发布，也可作为合集仓库中的稳定节点副本分发

后续进入开发或扩展前请先完成：

1. 更新 `/Users/evenbetter/Downloads/C&CStudio/外贸skill/skill需求池.md`
2. 填写 `/Users/evenbetter/Downloads/C&CStudio/外贸skill/模板/skill立项模板.md`
3. 明确最小输入、输出格式和边界
4. 参考 `/Users/evenbetter/Downloads/C&CStudio/外贸skill/开发信skill/立项方案.md` 收敛首版实现范围

## 快速运行

```bash
python3 ./scripts/build_email_draft.py \
  --input-json ./examples/first-touch.json \
  --markdown-out /tmp/first-touch-email.md \
  --json-out /tmp/first-touch-email.json
```

```bash
python3 ./scripts/build_email_draft.py \
  --input-json ./examples/follow-up.json
```

```bash
python3 ./scripts/build_email_input_from_customer_intel.py \
  --input-json ./examples/customer-intel-report.json \
  --email-type first_touch \
  --product-or-offer "frozen mixed vegetables" \
  --sender-name "Leo" \
  --sender-company "Ningbo FreshGrow Foods" \
  --json-out /tmp/email-input-from-intel.json
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
2. 如有模板改动，重新生成受影响的 `examples/*-output.md` 和 `examples/*-output.json`
3. 确认 `README.md`、`验收记录.md` 和 `for-openclaw/README.md` 没有状态漂移

## OpenClaw 变体

`for-openclaw/` 是这个 Skill 的 OpenClaw-native 包装版本：

- 保留当前本地版的保守输出原则
- 假设客户背景摘要、历史沟通、风险提示等上游上下文由 OpenClaw 工作流先整理
- Python 包装脚本只负责把 OpenClaw 输入合并并转交给核心草稿生成器

## 作者

半斤九两科技
