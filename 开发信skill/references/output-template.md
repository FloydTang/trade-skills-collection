# 输出模板

首版输出使用以下固定结构：

```text
# Email Draft Package

## Scenario
- Email Type
- Goal

## Subject Options
1. ...
2. ...

## Draft Version A
Dear ...

## Draft Version B
Dear ...

## Review Notes
- ...

## Input Signals Used
- ...
```

约束：

- `Draft Version A` 作为主版本，语气更稳
- `Draft Version B` 作为可选版本，语气略简洁
- `Review Notes` 必须用中文
- `Input Signals Used` 只回显实际使用到的输入，不要虚构来源
