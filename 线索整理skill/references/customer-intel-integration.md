# 与客户背调 Skill 的衔接说明

这个 Skill 的目标不是替代客户背调，而是把零散线索整理成更稳定的背调输入。

## 输出给客户背调 Skill 的字段

每条线索默认桥接出：

- `company_name`
- `person_name`
- `email`
- `company_website`
- `country_or_market`
- `notes`

## 设计原则

- 只桥接保守字段
- 不把分类结果直接写成事实
- 不把推断性标签塞进 `company_name` 或 `notes`
- `notes` 可保留来源与复核提醒

## 推荐顺序

1. 先运行线索整理 / 初筛 Skill
2. 从结果里挑出 `recommended_next_action = enter_customer_intel` 的线索
3. 再交给 `客户背调skill/` 深入处理

## 桥接边界

- 如果只有邮箱且域名很弱，应先人工补查
- 如果官网和邮箱冲突，不建议直接批量送背调
- 如果联系人匹配不稳，背调阶段必须继续保守处理
