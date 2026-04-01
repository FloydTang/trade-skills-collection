# changedetection Watch 落地口径

这份说明只解决一件事：

把当前 3 个真实页面，尽量稳妥地落进 `changedetection.io`。

当前原则不变：

- 先让 watch 建起来
- 先让页面主内容可复查
- 先让摘要层能接收变化
- 不伪造“已经稳定的 CSS 选择器”

## 当前已确认的页面文本信号

这些信号来自公开页面文本快照，只能证明“当前页面上看得到这些字段”，不能证明对应选择器已经稳定。

### 1. 产品详情页

- 页面：`https://www.allbirds.com/products/mens-tree-runners`
- 当前可见文本信号：
  - `Men's Tree Runner`
  - `$100`
  - `Add to Cart - $100`
  - `Thoughtfully designed`
- 适合先观察的字段：
  - 产品标题
  - 价格
  - 规格关键词
  - CTA 文案

### 2. 新品集合页

- 页面：`https://www.allbirds.com/collections/mens-new-arrivals`
- 当前可见文本信号：
  - `Men's Tree Glider`
  - `Men's Varsity Airy`
  - `Men's Dasher NZ Relay`
  - `NEW`
  - `New Color`
- 适合先观察的字段：
  - 主推产品
  - 上新标识
  - 集合页主文案
  - CTA 文案

### 3. 首页促销区

- 页面：`https://www.allbirds.com/`
- 当前可见文本信号：
  - `Shop Men's Sale`
  - `Final Few`
  - `NEW IN MEN'S APPAREL`
- 适合先观察的字段：
  - 促销文案
  - 折扣文案
  - CTA 文案

## GUI 建 watch 的最小顺序

1. 先按 `examples/changedetection-watch-seed.json` 建 3 个 watch
2. 首次不要急着写很细的 include filters
3. 先确认抓到的文本里，重点字段是否都出现
4. 如果整页噪音太大，再逐步缩到页面主内容区
5. 只有在真实 watch 中连续稳定后，才把 CSS/XPath 选择器固化进文档

## 当前字段校验口径

### 产品详情页

- 必看：产品标题、价格、CTA 文案
- 可选：规格关键词
- 不先看：推荐商品区、评论区、页脚

### 新品集合页

- 必看：前几张产品卡、NEW 标识
- 可选：集合页主文案
- 不先看：排序、分页、推荐模块

### 首页促销区

- 必看：促销标题、折扣表达、主 CTA
- 不先看：导航、页脚、帮助入口、隐私或条款

## 出现过滤失败时怎么处理

- 第一步：放宽范围，只缩到页面主内容块，不要继续细抠字段
- 第二步：先保留整页 watch，让摘要脚本做人读级降噪
- 第三步：确认页面是否属于 JS / 轮播 / 个性化渲染过重，再决定是否换抓取后端

## 当前不要写死的东西

- 不把未验证过的 CSS 选择器写成“推荐稳定方案”
- 不把一时出现的营销文案写成长期固定字段
- 不把当前页面文本快照写成永远存在的事实
