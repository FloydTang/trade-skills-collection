# Meta Leads Visible Table Validation

## One-Line Conclusion

The visible Meta Lead Center table is a valid real-business source, but it is too thin for safe customer grouping; the correct result is to request the full lead form export before drafting segmented outreach.

## Input Quality

- Customer count: 8 redacted visible rows.
- Source type: private Meta Business Suite Lead Center table, visible fields only.
- Usable facts: paid acquisition, completed form status, email channel, under-consideration stage, unassigned.
- Main gaps: country, company, role, project type, building area, budget, timeline, requested service, special requirements.

## Blocking Recommendation

Do not force groups from this table view.

Reason: the current table only proves that each person completed a paid Meta lead form. It does not show enough business facts to separate warehouse, factory, hangar, distributor, contractor, or low-quality inquiry segments.

Recommended next action:

- Download the complete Meta lead export from Lead Center.
- Remove email, phone, WhatsApp, and raw personal names from the test artifact.
- Keep project fields such as country, project type, area, budget, timeline, role, and requirement notes.
- Rerun `trade-mail-group` on 5-10 redacted leads with those fields.

## Handoff

- To customer intel: complete Meta lead export, redacted project fields, country, company or role, project type, budget, timeline, and message notes.
- To outreach email: none yet; wait for safe grouping after form-field export.

## Non-Goals

- No automatic sending.
- No sending infrastructure setup.
- No reply-rate promise.
- No contact data stored in examples.
- No guessing from names.
