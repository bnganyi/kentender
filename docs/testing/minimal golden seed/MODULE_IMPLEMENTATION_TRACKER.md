# Minimal Golden v2 — module implementation tracker

**Sources:** [KenTender Minimal Golden Scenario Seed Loader Implementation Pack v2](KenTender%20Minimal%20Golden%20Scenario%20Seed%20Loader%20Implementation%20Pack%20v2.md), UX specs under `docs/ux/`.

**Status values:** `Not started` | `In progress` | `Blocked` | `Done`

| Stage | Seed / data | Server rules & services | Desk UX | Automated tests | Manual UAT | Status |
| ----- | ----------- | ------------------------ | ------- | ----------------- | ---------- | ------ |
| Base reference | Entity, dept, funding, category, method (`base_ref` / JSON) | DocType validations | Links on workspaces | Exists in `verify_minimal_golden` | — | Done |
| Strategy | `load_strategy` + canonical JSON | `validate_strategic_linkage_set` after seed; DocType validators + `strategic_linkage_validation` | Strategy workspace: KPI report, alignment + exception reports, explorer report; roles extended | `test_verify_strategy_chain`, `test_strategy_load_validates_linkage` | [MINIMAL_GOLDEN_UAT_STRATEGY_CHECKLIST.md](MINIMAL_GOLDEN_UAT_STRATEGY_CHECKLIST.md) | Done |
| Templates | `template_codes` in JSON; `ensure_minimal_golden_template_codes` | No procurement/eval/accept template DocTypes yet — **reserved codes only** | — | — | — | Blocked (awaiting DocTypes) |
| Budget | `load_budget` — BL links strategy | `validate_budget_line_scope_and_strategy` | Report links from Strategy workspace | Extended `verify` for BL strategy fields | — | Done |
| Users | `users` seed + bootstrap roles | — | — | User rows in verify | — | Done |
| Requisition | PR seed | PR validation | — | verify | Scenario v2 | Not started |
| Planning | PP / PPI | — | — | verify | Not started |
| Tender → Assignments | E2E chain | — | — | verify / future | Not started |
| Verify + reset | `verify_minimal_golden`, `wipe_test_data` | — | — | — | — | Partial |

**Notes**

- **Templates:** Implementation Pack codes `ONT_STANDARD`, `QCBS_SIMPLE`, `GOODS_SIMPLE` are recorded in [`minimal_golden_canonical.json`](../../../kentender/kentender/uat/minimal_golden/data/minimal_golden_canonical.json) under `template_codes`. Full seed rows require future Procurement / Evaluation / Acceptance template DocTypes (see xlsx skip **Procurement Template / Version**).
- **Equivalence:** Seed modules remain under `kentender.uat.minimal_golden.*` (not `uat/seed_packs/minimal_golden_v2/`); behaviour matches Implementation Pack order when using `seed_minimal_golden` command sequence.
