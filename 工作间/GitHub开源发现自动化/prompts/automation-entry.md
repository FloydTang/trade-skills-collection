# Codex GitHub Discovery Automation Entry — v3.3

> 用途：直接粘贴到 Codex Automation 的 prompt 输入框中
> 更新日期：2026-04-01
> 变更说明：补齐 Obsidian 同步与验收动作；长期规则以 `discovery-rules.md` 为准，这里只保留执行必需信息

---

Work inside `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/GitHub开源发现自动化`.

Before doing any search or writing, first read these local docs in order:

- `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/GitHub开源发现自动化/prompts/discovery-rules.md`
- `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/GitHub开源发现自动化/README.md`
- `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/README.md`
- `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/开源工具总表.md`
- `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/路线映射.md`
- `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/skill需求池.md`

Treat `discovery-rules.md` as the rule master. Follow it unless this execution prompt adds a narrower automation-only instruction.

Perform one full GitHub discovery cycle for the external-trade skill roadmap. Do not rely on OpenClaw or any external private discovery repository. Search GitHub directly, generate today's discovery report under `reports/`, then sync only the reusable conclusions into:

- `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/开源工具总表.md`
- `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/路线映射.md`

Top-level principle: `实事求是、简洁高效`.

## Automation-Specific Rules

- This prompt is an execution entrypoint, not the master spec.
- Do not restate or duplicate large chunks of the daily-discovery master into new files.
- Prefer updating existing `工作间/` records over creating any new long-term document.
- Keep the output aligned with the current lightweight strategy, especially for competitor monitoring.
- When a record is clearly long-term and human-facing, keep it compatible with later Obsidian presentation under `工具工作间/外贸skill`.

### Daily Review Actions

1. Search GitHub across the three business lines and two tracks
2. Deduplicate against `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/开源工具总表.md`
3. Generate today's report under `reports/YYYY-MM-DD.md`
4. For each retained candidate, record only the fields required by the master prompt and the existing `工作间/` docs.
5. Update `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/开源工具总表.md` using a single-row-per-project model with statuses like:
   - `观察中`
   - `待判断`
   - `已结论`
6. Update `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/路线映射.md` with Codex's judgment on what should be:
   - `建议纳入工具库` (recommend adding to tool library)
   - `建议进入需求池` (recommend adding to skill demand pool)
   - `建议继续观察` (recommend continued observation)
   - `不建议处理` (not recommended for action)
7. If `工作间/` or `skill需求池.md` changed, run:
   - `/Users/evenbetter/Downloads/C&CStudio/工具库/外贸skill/工作间/GitHub开源发现自动化/scripts/sync_obsidian_workspace.sh`
8. Verify the Obsidian mirror reflects the same updates at:
   - `/Users/evenbetter/Downloads/半斤九两/Obsidian Vault/工具工作间/外贸skill/开源工具总表.md`
   - `/Users/evenbetter/Downloads/半斤九两/Obsidian Vault/工具工作间/外贸skill/路线映射.md`
   - `/Users/evenbetter/Downloads/半斤九两/Obsidian Vault/工具工作间/外贸skill/skill需求池.md`
9. Do not maintain separate long-term watchlist/backlog/decision documents. Those older files are migration stubs only.
10. Only recommend upgrading into `skill需求池.md` when the project already has:
   - a clear business direction
   - a clear landing approach
   - a clear attachment target
   - a clear next action
11. When a conclusion is likely to be reused in courses, branding, or product explanation, make sure it is written in a way that can be shown in Obsidian later, rather than only as execution noise.

### Special Rules for Competitor Monitoring

- `changedetection.io` is already the confirmed upstream monitoring base for the first version of `竞品监控 Skill`.
- For similar candidates, compare them against that baseline rather than reopening the upstream choice from scratch.
- Favor lightweight monitoring, field focus, concise summaries, and manual review guidance.
- Do not recommend turning this direction into a heavy monitoring platform.

### Key Constraints

- Select no more than 4-6 candidates per day (2-3 per track)
- Do not repeatedly promote/reject the same repository across days
- Do not create extra summary files unless they will actually be reused
- Keep long-term documentation minimal and collaborative so Floyd can edit it directly
- Keep recommendations compatible with the current “minimal usable version first” strategy
- Avoid recommendations that would expand the current task from a lightweight skill into a full system

### Weekly Summary (Sundays only)

On Sundays, in addition to the daily review, generate a weekly summary covering:
- Total candidates per track and per business line
- Candidates that entered backlog this week
- Landing approach distribution (new Skill vs integrate vs reference only)
- Watchlist changes
- Recommended focus directions for next week
