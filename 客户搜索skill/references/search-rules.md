# 搜索规则

## 查询策略

首版固定使用三类查询：

1. `product_or_offer + target_market + customer_type`
2. `product_or_offer + target_market + importer/distributor/brand/buyer`
3. `site:linkedin.com/company ...`

## 搜索边界

- 只用公开网页结果
- 不做登录态抓取
- 不承诺完整名单
- 不做大规模爬取

## 结果处理

- 先按 URL 去重
- 再按官网优先、LinkedIn 次之、公司名再次去重
- 搜索节点只做候选发现，不做价值评分
