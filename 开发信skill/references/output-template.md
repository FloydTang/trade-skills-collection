# 输出模板

首版输出使用以下固定结构：

```text
# Review-First Outreach Draft Package

## Scenario
- Email Type
- Goal
- Send Policy
- Recommended Next Action

## Subject Options
1. ...
2. ...

## Draft Version A
Dear ...

## Draft Version B
Dear ...

## Review Notes
- ...

## Evidence Signals Used
- ...

## Unconfirmed Facts
- ...

## Input Signals Used
- ...
```

约束：

- `Draft Version A` 作为主版本，语气更稳
- `Draft Version B` 作为可选版本，语气略简洁
- `Review Notes` 必须用中文
- `Evidence Signals Used` 必须只列出真实使用过的背调证据
- `Evidence Signals Used` 如包含 `recent_signal` 或 `market_signal`，必须来自上游 `source_context`
- `Unconfirmed Facts` 必须显式提醒人工确认
- `Input Signals Used` 只回显实际使用到的输入，不要虚构来源
- 开发信 Skill 不能自行生成客户近期动态或市场/合规变化
