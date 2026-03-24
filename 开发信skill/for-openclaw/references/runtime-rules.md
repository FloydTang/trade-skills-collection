# OpenClaw Runtime Rules

OpenClaw 版只负责“上下文整合 + 保守生成”，不负责复杂业务判断。

## 输入优先级

1. `operator_input`
2. `public_context`
3. 根目录脚本默认值

## 合并原则

- 已明确给出的字段不覆盖
- 公开资料摘要只能进入 `customer_profile_summary`
- 历史沟通只进入 `previous_contact_context`
- 风险提示只转换成更强的人审约束，不直接改写邮件事实

## 不做什么

- 不自动推断产品
- 不自动编造成交意向
- 不自动改写操作员明确目标
