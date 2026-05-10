# 线索整理 / 初筛 Skill

当前状态：可交付

这个 Skill 用于把搜索阶段得到的零散候选线索整理成可继续进入客户背调的标准输入。

## 这个 Skill 解决什么问题

- 搜索结果零散，字段不统一
- 线索看起来很多，但不知道哪些能继续
- 需要先做保守的字段统一和下一步建议

## 职责边界

- 负责字段统一
- 负责缺失识别
- 负责初步分类和下一步建议
- 负责桥接到 `客户背调skill`
- 不负责公开网页深度背调
- 不负责开发信生成

## 当前默认能力

- 标准化候选线索字段
- 接收搜索阶段证据等级和缺口
- 标记缺失项和人工复核原因
- 给出保守的下一步动作建议
- 生成兼容 `客户背调skill` 的桥接输入

## 当前不默认承诺

- 自动判断客户一定值不值得做
- 替代人工完成最终筛选
- 跳过背调直接生成外发内容

## 最小输入输出

- 输入：候选客户名单、来源链接、来源名称、匹配依据、联系人或公司基础字段
- 输出：结构化线索池、证据等级、缺失字段、人工复核原因、下一步动作建议、客户背调桥接输入

## 企业表格与规则沉淀

- 这是线索整理能力，不是固定表格模板。
- 企业已有表头优先沿用；没有可用表格时，再按产品、市场和筛选流程新建够用表。
- 用户确认新的字段、客户分级、来源字段、放行规则、暂停规则或表头映射后，先追问：`是否更新到对应 Skill 以便下次自动复用`，授权后再写入 Skill。

## 固定提醒

- 没有真实公开来源，不应强行推进下游
- 当前最稳的是公司级主线索
- 人名职位级是辅助补全
- 精准邮箱级仍不足

## Quick Start

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

## 增强权益入口

如需数据留存、统一编排、多代理协作或飞书落地，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>
