# 输入字段说明

这份说明和 `/Users/evenbetter/Downloads/C&CStudio/外贸skill/开发信skill/schemas/email-draft-input.schema.json` 配套使用。

## 必填字段

- `email_type`
  - 取值：`first_touch` 或 `follow_up`
  - 含义：本次生成的是首轮开发信还是跟进邮件
- `customer_name`
  - 含义：客户联系人名
  - 规则：未知时不要硬填具体人名
- `company_name`
  - 含义：客户公司名
- `product_or_offer`
  - 含义：你要介绍的产品、品类或方案
  - 规则：这是销售方自有输入，不从客户背调结果自动推断
- `goal`
  - 含义：本封邮件要达成的动作
  - 建议：写成一句可执行表达，例如“introduce our factory and ask whether they are open to new suppliers”

## 选填字段

- `country_or_market`
  - 用途：帮助邮件轻度本地化，但不应夸大对客户市场的了解
- `customer_profile_summary`
  - 用途：写进邮件前需要人工复核的客户画像摘要
- `previous_contact_context`
  - 用途：仅用于跟进邮件引用历史沟通
- `tone`
  - 用途：控制语气，如 `professional,warm`、`professional,helpful`
- `sender_name`
- `sender_company`
- `signature`
- `constraints`

## 保守规则

- 没有输入就不补
- 输入如果属于推断，只能保守使用
- `customer_profile_summary` 可以帮助定位角度，但不等于已确认事实
- `previous_contact_context` 不完整时，应提醒人工复核
