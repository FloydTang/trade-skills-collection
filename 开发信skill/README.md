# 开发信 Skill

当前状态：可交付

这个 Skill 用于把已确认的客户信息和客户画像摘要，转成可人工修改后发送的英文邮件草稿。

它的当前公开定位是：`复核型开发信工作台`。

## 这个 Skill 解决什么问题

- 已经有了客户基础信息
- 想更快生成首轮开发信或跟进邮件草稿
- 但不希望把不确定信息写成事实

## 职责边界

- 负责把结构化输入转成英文草稿
- 负责给出中文复核提示
- 不负责自动发送
- 不负责替代搜索、初筛和背调

## 当前默认能力

- `first_touch` 首轮开发信草稿
- `follow_up` 跟进邮件草稿
- 标题候选
- 中文复核提示
- 关键输入依据回显
- 依据过的证据列表
- 未确认事实清单
- 固定发送策略 `manual_review_only`

## 当前不默认承诺

- 自动发送邮件
- 完全自动化个性化触达
- 在弱证据下生成客户事实

## 最小输入输出

- 输入：邮件类型、客户名与公司名、产品或报价方向、客户摘要、发件人信息
- 输出：标题候选、英文正文草稿、中文复核提示、证据依据、未确认事实清单、发送策略

## 固定提醒

- 发送前必须人工复核
- 没有确认过的客户事实，不应写死到邮件里
- 当前最稳的是基于公司级确认信息生成草稿

## Quick Start

```bash
python3 ./scripts/build_email_draft.py \
  --input-json ./examples/first-touch.json \
  --markdown-out /tmp/first-touch-email.md \
  --json-out /tmp/first-touch-email.json
```

## 增强权益入口

如需数据留存、统一编排、多代理协作或飞书落地，请查看飞书文档：

- <https://evenbetter.feishu.cn/wiki/W6GnwTZGFiUdJ0kXZv6cV4PSnpf>
