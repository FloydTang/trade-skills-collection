# Trade Customer Intel

中英双语的开源 Codex Skill，用公开网页线索为外贸销售、客户开发和线索筛查生成结构化客户情报报告。

An open-source Codex skill that turns sparse public-web signals into bilingual, structured customer intelligence reports for sales research, lead verification, and conservative outreach preparation.

## Version Strategy

这个仓库现在并行维护两套版本：

- `classic`：当前根目录版本，面向 Codex / 本地 Python 直接运行
- `for-openclaw`：面向云端 OpenClaw 的独立变体，使用 OpenClaw 工具编排搜索和抓取，再交给 Python 汇总器生成报告

如果你要在 OpenClaw 中落地，请优先查看 [for-openclaw/README.md](./for-openclaw/README.md) 和 [for-openclaw/SKILL.md](./for-openclaw/SKILL.md)。

## Why This Exists

很多外贸线索只有公司名、联系人名、邮箱或手机号，公开信息分散、真假难辨，而且销售同事往往没有时间手工整理。

This project exists to make that first-pass research faster and safer:

- 用公开网页信息补全公司与联系人画像
- 对弱证据保持保守，不把推断写成事实
- 输出适合 CRM、销售协作和首轮触达的双语报告

## What It Produces

输入可以很稀疏，例如：

```json
{
  "company_name": "Acme Industrial",
  "person_name": "Jane Smith",
  "email": "jane@acme-industrial.com",
  "company_website": "",
  "country_or_market": "United States",
  "notes": ""
}
```

输出会包含：

- `Executive Summary / 执行摘要`
- `Identity Snapshot / 身份快照`
- `Company Profile / 公司画像`
- `Digital Footprint / 数字足迹`
- `Interest & Topic Signals / 主题信号`
- `Sales Angles / 销售切入角度`
- `Outreach Persona Card / 开发画像卡`
- `Personalized Outreach Pack / 英文触达草稿`
- `Risk Rating / 风险评级`
- `Evidence / 证据清单`

## Core Principles

- Public web only
- Conservative entity matching
- Conservative risk scoring
- No private-data claims
- No invented personalization

对应中文原则：

- 只用公开网络信息
- 实体匹配偏保守
- 风险判断偏保守
- 不暗示使用私有数据
- 不捏造个性化信息

## Search Workflow

默认按这个顺序找证据：

1. 官网与域名线索
2. LinkedIn 公司页与个人页
3. Facebook 与 Instagram
4. X / Twitter 与 YouTube
5. 通用网页搜索与新闻结果

如果证据不足，仍然会出报告，但会明确降低置信度并提示人工复核。

## Repository Structure

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── report-template.md
│   └── source-playbook.md
├── scripts/
│   └── build_customer_intel_report.py
├── for-openclaw/
│   ├── SKILL.md
│   ├── README.md
│   ├── examples/
│   ├── references/
│   ├── schemas/
│   └── scripts/
├── examples/
│   └── sample-input.json
└── .github/
```

## Quick Start

### Run with a JSON file

```bash
python3 ./scripts/build_customer_intel_report.py \
  --input-json ./examples/sample-input.json \
  --markdown-out /tmp/customer-intel.md \
  --json-out /tmp/customer-intel.json
```

### Run by piping JSON

```bash
cat <<'EOF' | python3 ./scripts/build_customer_intel_report.py
{
  "company_name": "Acme Industrial",
  "person_name": "Jane Smith",
  "email": "jane@acme-industrial.com",
  "country_or_market": "United States"
}
EOF
```

## Search Behavior

- If `tvly` is installed, the script uses it first.
- Otherwise it falls back to DuckDuckGo HTML search.
- Page snapshots use `r.jina.ai` when available.
- Sparse evidence still produces output, with lower confidence.

## Using It As a Codex Skill

主要定义文件在 [SKILL.md](./SKILL.md)。

输出结构与来源规则分别在：

- [references/report-template.md](./references/report-template.md)
- [references/source-playbook.md](./references/source-playbook.md)

代理配置在 [agents/openai.yaml](./agents/openai.yaml)。

## OpenClaw Variant

`for-openclaw/` 是一个并行维护的 OpenClaw-native 版本：

- 不替换当前 baseline
- 不依赖 Tavily / DuckDuckGo HTML / r.jina.ai
- 假设搜索由 `coze-web-search` 提供
- 假设主抓取由 `scrapling-official` 提供
- 假设抓取降级由 `coze-web-fetch` 提供
- 假设 Python 只负责“证据驱动汇总”，不直接联网搜索

## Suggested Use Cases

- 外贸询盘首轮筛查
- 销售开发前的公开信息核验
- CRM 入库前的背景补全
- 弱线索的官网/社媒/公司实体定位
- 低风险线索的英文首触达草稿准备

## Current Limits

- 不是 KYC 或法律尽调工具
- 不保证每次都能找到官网或社媒主页
- 对同名联系人只做保守匹配
- 需要人工审阅后再发送外部开发邮件

## Open Source Notes

This repository is intended to be practical and hackable:

- 你可以直接改搜索策略
- 你可以替换搜索源
- 你可以接入 CRM 或自动化流程
- 你也可以把报告模板改成更适合自己团队的版本

欢迎 PR 和 issue。

## License

Released under the MIT License. See [LICENSE](./LICENSE).

## Attribution

Created and maintained by 半斤九两科技.
