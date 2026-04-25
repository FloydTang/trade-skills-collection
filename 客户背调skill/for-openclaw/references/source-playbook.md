# Source Playbook

## Priority Order

1. Official website and domain-level evidence
2. LinkedIn company page and personal profile
3. Facebook and Instagram
4. X and YouTube
5. General web search results and news pages

## Entity Resolution Rules

- Prefer direct identifiers over inferred ones: explicit website > email domain > search result guess.
- Do not merge two entities unless at least two signals align, such as company name plus matching domain or company name plus matching geography.
- When a person name is common, keep the person section tentative unless the profile clearly matches company, title, or market.

## Evidence Rules

- Attach a source URL to every material claim when possible.
- Mark a statement as inference when it is derived from patterns rather than stated directly.
- If website text and social text conflict, call out the conflict instead of choosing one silently.
- If only one weak source exists, keep confidence low and avoid firm wording.

## Deduping Rules

- Keep the highest-confidence URL per platform.
- Collapse mirrored URLs that point to the same page.
- Prefer official brand accounts over reseller, fan, or employee reposts.
- Prefer recent evidence when two sources say similar things.

## Search Layer Failure Handling

### 已知问题

1. `ddg_search()` 依赖 DuckDuckGo HTML 接口（`html.duckduckgo.com/html/`），**在中国境内网络环境下大概率超时**。
2. `fetch_snapshot()` 依赖 `r.jina.ai` 第三方转码服务，**在中国境内大概率不可达**。
3. 脚本没有网络超时后自动降级机制，搜索层崩溃会直接导致整个流程失败。

### 应急方案

当脚本搜索层不可用时：

**方案 A — 用 OpenClaw 内置 web_search 替代搜索层：**

```
# 不运行脚本，直接用 web_search 收集证据
web_search('"Kanoo Machinery" official website')
web_search('site:linkedin.com/company "Kanoo Machinery"')
# 收集完后手动构建报告
```

**方案 B — 分步执行：**

1. 用 `web_search` 收集所有搜索证据
2. 用 `web_fetch` 获取关键页面快照
3. 把这些证据整理后作为输入传递给报告生成逻辑
4. 跳过脚本的搜索层直接生成 Markdown 报告

### 固定规则

- 搜索层必须返回至少 3 条有效证据才能推进到报告生成
- 如果搜索全部失败（零结果），标记为 `intel_insufficient_evidence` 并输出失败原因
- 如果部分搜索成功但证据不足 4 条，风险评级至少为 Medium
- 不要用脚本内的 `ddg_search` 作为唯一搜索入口

## Risk Heuristics

### Low

- Website, domain, company naming, and social identity line up.
- Multiple public traces exist.
- No strong contradictions or suspicious patterns appear.

### Medium

- Public presence is thin or stale.
- Some company facts are unclear, but nothing is obviously wrong.
- Contact identity is partially matched rather than strongly verified.

### High

- Contact or company identity conflicts across sources.
- Website is missing, broken, placeholder-like, or inconsistent with the business claim.
- Email domain does not align with claimed company.
- There are strong signs of copied content, fake scale, or almost no public footprint.

## Recommended Search Patterns

- `"<company>" official website`
- `site:linkedin.com/company "<company>"`
- `site:linkedin.com/in "<person>" "<company>"`
- `site:facebook.com "<company>"`
- `site:instagram.com "<company>"`
- `site:x.com "<company>" OR site:twitter.com "<company>"`
- `site:youtube.com "<company>"`
- `"<email-domain>" company`

## Output Discipline

- Keep analysis in Chinese by default.
- Keep sales-facing angles bilingual.
- Keep risk scoring conservative.
- End with concrete next steps if evidence is weak.
