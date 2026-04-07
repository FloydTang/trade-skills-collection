# 线索整理 / 初筛 Skill

当前状态：可交付

## 开源权益默认包含什么

- 单独可运行的线索整理能力
- 固定样例输入输出
- 客户背调桥接输入生成
- 最小脚本入口

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
- 标记缺失项和人工复核原因
- 给出保守的下一步动作建议
- 生成兼容 `客户背调skill` 的桥接输入

## 当前不默认承诺

- 自动判断客户一定值不值得做
- 替代人工完成最终筛选
- 跳过背调直接生成外发内容

## 输入输出

输入：

- 候选客户名单
- 来源链接
- 联系人或公司基础字段

输出：

- 结构化线索池
- 缺失字段
- 人工复核原因
- 下一步动作建议
- 客户背调桥接输入

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

- <https://evenbetter.feishu.cn/wiki/ADmiwiultihx6Yk1p2UcjfmVn6d>
