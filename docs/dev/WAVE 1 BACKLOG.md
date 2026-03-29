# Wave 1 backlog (tracking)

**Wave 1 status: Closed** (2026-03-28). All **26** stories in the execution sequence (steps **1–10** strategy, **11–26** budget) are **Done** in the table below. Follow-on work is **Wave 2+** (section at end of this file; also [`KenTender Master Epic Map.md`](KenTender%20Master%20Epic%20Map.md)).

**Purpose:** Sprint and PR tracking only. Do **not** duplicate full objectives, scope, acceptance criteria, tests, or Cursor prompts here.

**Maintenance:** After each merged story (or agreed milestone), update the **Status** and **Notes** columns for that row. Use `Done` only when the ticket’s acceptance criteria in the pack are met.

**Canonical source:** Every Wave 1 story’s full ticket lives in [`Wave 1 Ticket Pack.md`](../prompts/Wave%201%20Ticket%20Pack.md) under the matching `**STORY-STRAT-xxx**` or `**STORY-BUD-xxx**` heading.

**Execution order:** Follow the pack’s **Recommended Wave 1 execution order** (steps **1–26** below). **Do not** assume numeric story order for strategy: **STORY-STRAT-006** runs at **step 9**, after **STORY-STRAT-007**, **008**, and **009**, because revision work depends on indicators, targets, and linkage validation.

Recommended sequence (copy for quick reference):

1. STORY-STRAT-001  
2. STORY-STRAT-002  
3. STORY-STRAT-003  
4. STORY-STRAT-004  
5. STORY-STRAT-005  
6. STORY-STRAT-007  
7. STORY-STRAT-008  
8. STORY-STRAT-009  
9. STORY-STRAT-006  
10. STORY-STRAT-010  
11. STORY-BUD-001  
12. STORY-BUD-002  
13. STORY-BUD-003  
14. STORY-BUD-004  
15. STORY-BUD-005  
16. STORY-BUD-006  
17. STORY-BUD-007  
18. STORY-BUD-008  
19. STORY-BUD-009  
20. STORY-BUD-010  
21. STORY-BUD-011  
22. STORY-BUD-012  
23. STORY-BUD-013  
24. STORY-BUD-014  
25. STORY-BUD-015  
26. STORY-BUD-016  

**Before STRAT-001 (environment):**

- **Apps:** `kentender_strategy` (`required_apps`: `kentender`); `kentender_budget` (`kentender`, `kentender_strategy`). Ensure both are installed on the target site.
- **Migrate:** Run `bench migrate` after new DocTypes land.
- **Tests:** `bench run-tests --app kentender_strategy` and later `--app kentender_budget`; `required_apps` encodes core + strategy for budget.
- **Wave 0 upstream:** Stories depend on **STORY-CORE-004**, **006**, **007**, **008**, **013**, **016** (e.g. Procuring Entity, master data, `business_id_generation`, entity scope, workflow guards, audit). Wave 0 closure: [`WAVE 0 BACKLOG.md`](Wave%200%20BACKLOG.md).

| Story ID | Title (short) | Epic | Depends on | Step # | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| STORY-STRAT-001 | Implement National Framework DocType | EPIC-STRAT-001 | STORY-CORE-004, STORY-CORE-006 | 1 | Done | [`national_framework`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/national_framework/): `business_id` autoname, composite uniqueness `(framework_code, version_label)`, date range, Active+`is_locked_reference` immutability scaffold; [`test_national_framework.py`](../../kentender_strategy/kentender_strategy/tests/test_national_framework.py). |
| STORY-STRAT-002 | Implement National Pillar and National Objective DocTypes | EPIC-STRAT-001 | STORY-STRAT-001 | 2 | Done | **National Pillar** / **National Objective** ([`national_pillar`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/national_pillar/), [`national_objective`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/national_objective/)): scoped uniqueness `(national_framework, pillar_code)` / `(national_pillar, objective_code)`; objective framework aligned in `validate()` (no `fetch_from` so link phase cannot mask mismatches); [`test_national_pillar_and_objective.py`](../../kentender_strategy/kentender_strategy/tests/test_national_pillar_and_objective.py). |
| STORY-STRAT-003 | Implement national reference immutability rules | EPIC-STRAT-001 | STORY-STRAT-001, STORY-STRAT-002, STORY-CORE-013 | 3 | Done | [`national_reference_immutability.py`](../../kentender_strategy/kentender_strategy/services/national_reference_immutability.py): `enforce_active_locked_immutability` + `frappe.flags.ignore_national_reference_immutability` bypass; **National Pillar** / **National Objective** `is_locked_reference`; **National Framework** refactored to shared helper; [`test_national_reference_immutability.py`](../../kentender_strategy/kentender_strategy/tests/test_national_reference_immutability.py). |
| STORY-STRAT-004 | Implement Entity Strategic Plan DocType | EPIC-STRAT-002 | STORY-STRAT-001, STORY-CORE-004, STORY-CORE-007 | 4 | Done | **Entity Strategic Plan** ([`entity_strategic_plan`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/entity_strategic_plan/)): `business_id` autoname; Link **Procuring Entity** + **National Framework**; date range; unique `(procuring_entity, version_no)`; supersession links same-entity only; `is_current_active_version` demotes others per entity (`after_insert`/`on_update`); [`test_entity_strategic_plan.py`](../../kentender_strategy/kentender_strategy/tests/test_entity_strategic_plan.py). |
| STORY-STRAT-005 | Implement Program and Sub Program DocTypes | EPIC-STRAT-002 | STORY-STRAT-004, STORY-STRAT-002 | 5 | Done | **Strategic Program** / **Strategic Sub Program** ([`strategic_program`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_program/), [`strategic_sub_program`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_sub_program/)): plan→program→sub-program alignment; program `procuring_entity` and **National Objective** vs plan `primary_national_framework`; sub-program plan must match parent program (empty plan filled from program); [`test_strategic_program_and_sub_program.py`](../../kentender_strategy/kentender_strategy/tests/test_strategic_program_and_sub_program.py). |
| STORY-STRAT-007 | Implement Output Indicator DocType | EPIC-STRAT-003 | STORY-STRAT-005 | 6 | Done | **Output Indicator** ([`output_indicator`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/output_indicator/)): required links to plan/program/sub-program; unique `(sub_program, indicator_code)`; program and plan must match sub-program (empty values filled from sub-program); **Procuring Department** scoped to program entity; `unit_of_measure` as Data; [`test_output_indicator.py`](../../kentender_strategy/kentender_strategy/tests/test_output_indicator.py). |
| STORY-STRAT-008 | Implement Performance Target DocType | EPIC-STRAT-003 | STORY-STRAT-007 | 7 | Done | **Performance Target** ([`performance_target`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/performance_target/)): hierarchy from **Output Indicator** (fill or enforce plan/program/sub-program); period start ≤ end; **Numeric / Text / Percent** measurement with mutually exclusive value fields and 0–100 percent; department scoped to program entity; [`test_performance_target.py`](../../kentender_strategy/kentender_strategy/tests/test_performance_target.py). |
| STORY-STRAT-009 | Implement strategic linkage validation services | EPIC-STRAT-003 | STORY-STRAT-005, STORY-STRAT-007, STORY-STRAT-008 | 8 | Done | [`strategic_linkage_validation.py`](../../kentender_strategy/kentender_strategy/services/strategic_linkage_validation.py): `validate_program` / `validate_sub_program` / `validate_indicator` / `validate_target` (optional `as_of_date`) / `validate_strategic_linkage_set`; shared `sync_*` hierarchy + `assert_procuring_department_scoped` used by strategy DocTypes; re-exported from [`services/__init__.py`](../../kentender_strategy/kentender_strategy/services/__init__.py); [`test_strategic_linkage_validation.py`](../../kentender_strategy/kentender_strategy/tests/test_strategic_linkage_validation.py). |
| STORY-STRAT-006 | Implement strategic revision model | EPIC-STRAT-002 | STORY-STRAT-004, STORY-STRAT-005, STORY-CORE-016 | 9 | Done | **Strategic Revision Record** ([`strategic_revision_record`](../../kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_revision_record/)): `business_id` autoname; previous/new **Entity Strategic Plan** (same procuring entity, distinct docs); reason + optional request/approval users, effective date, impact summary, status; no automatic mutation of plans; [`test_strategic_revision_record.py`](../../kentender_strategy/kentender_strategy/tests/test_strategic_revision_record.py). |
| STORY-STRAT-010 | Implement strategy query helpers and reports | EPIC-STRAT-003 | STORY-STRAT-009 | 10 | Done | [`strategy_queries.py`](../../kentender_strategy/kentender_strategy/services/strategy_queries.py): active plans (`is_current_active_version`), programs by **National Objective**, indicators/targets by **Procuring Entity**; script reports **Strategy Active Plans By Entity**, **Strategy Programs By Objective**, **Strategy Indicators And Targets By Entity** ([`kentender_strategy/report/`](../../kentender_strategy/kentender_strategy/kentender_strategy/report/)); [`test_strategy_queries.py`](../../kentender_strategy/kentender_strategy/tests/test_strategy_queries.py). |
| STORY-BUD-001 | Implement Budget Control Period DocType | EPIC-BUD-001 | STORY-CORE-004, STORY-CORE-006 | 11 | Done | **Budget Control Period** ([`budget_control_period`](../../kentender_budget/kentender_budget/kentender_budget/doctype/budget_control_period/)): `business_id` autoname; one **Open** row per `(procuring_entity, fiscal_year)`; date range; [`test_budget_control_period.py`](../../kentender_budget/kentender_budget/tests/test_budget_control_period.py). |
| STORY-BUD-002 | Implement Budget DocType | EPIC-BUD-001 | STORY-BUD-001, STORY-CORE-007 | 12 | Done | **Budget** ([`budget`](../../kentender_budget/kentender_budget/kentender_budget/doctype/budget/)): header links entity + period; unique `(procuring_entity, budget_control_period, version_no)`; `supersedes_budget` same entity+period; [`test_budget.py`](../../kentender_budget/kentender_budget/tests/test_budget.py). |
| STORY-BUD-003 | Implement budget version/supersession logic | EPIC-BUD-001 | STORY-BUD-002 | 13 | Done | Covered in **Budget** controller: `is_current_active_version` demotion per `(procuring_entity, budget_control_period)`; supersession validation with BUD-002; tests in [`test_budget.py`](../../kentender_budget/kentender_budget/tests/test_budget.py). |
| STORY-BUD-004 | Implement Budget Line DocType | EPIC-BUD-002 | STORY-BUD-002, STORY-STRAT-009 | 14 | Done | **Budget Line** ([`budget_line`](../../kentender_budget/kentender_budget/kentender_budget/doctype/budget_line/)): sync from **Budget**/period fiscal year + currency; dept scope; strategy alignment + `validate_strategic_linkage_set`; amount fields documented non-authoritative; [`test_budget_line.py`](../../kentender_budget/kentender_budget/tests/test_budget_line.py). |
| STORY-BUD-005 | Implement budget line validation against strategy and entity scope | EPIC-BUD-002 | STORY-BUD-004, STORY-STRAT-009, STORY-CORE-008 | 15 | Done | [`budget_line_scope_validation.py`](../../kentender_budget/kentender_budget/services/budget_line_scope_validation.py): **Budget** / **Budget Control Period** / **Entity Strategic Plan** scoped via `record_belongs_to_entity` (CORE-008); plan–program–sub chain; `validate_strategic_linkage_set` + dept scope; **Budget Line** calls `validate_budget_line_scope_and_strategy`; extra cases in [`test_budget_line.py`](../../kentender_budget/kentender_budget/tests/test_budget_line.py). |
| STORY-BUD-006 | Implement budget line derived totals fields and recalculation hooks | EPIC-BUD-002 | STORY-BUD-004 | 16 | Done | [`budget_line_derived_totals.py`](../../kentender_budget/kentender_budget/services/budget_line_derived_totals.py): `compute_available_amount`, `recalculate_budget_line_derived_totals`, `on_budget_ledger_post_recalculate_line` (BUD-008 hook target); **Budget Line** denormalized amounts read-only in DocType; `validate` doc_event; [`test_budget_line_derived_totals.py`](../../kentender_budget/kentender_budget/tests/test_budget_line_derived_totals.py). |
| STORY-BUD-007 | Implement Budget Ledger Entry DocType | EPIC-BUD-003 | STORY-BUD-004, STORY-CORE-016 | 17 | Done | **Budget Ledger Entry** ([`budget_ledger_entry`](../../kentender_budget/kentender_budget/kentender_budget/doctype/budget_ledger_entry/)): append-only; `event_hash`; entry types/direction; source context; [`test_budget_ledger_entry.py`](../../kentender_budget/kentender_budget/tests/test_budget_ledger_entry.py). |
| STORY-BUD-008 | Implement ledger posting service | EPIC-BUD-003 | STORY-BUD-007, STORY-CORE-016 | 18 | Done | [`budget_ledger_posting.py`](../../kentender_budget/kentender_budget/services/budget_ledger_posting.py): `reserve_budget`, `release_reservation`, `commit_budget`, `release_commitment`; `log_audit_event`; sync line denorm; [`test_budget_ledger_posting.py`](../../kentender_budget/kentender_budget/tests/test_budget_ledger_posting.py). |
| STORY-BUD-009 | Implement availability calculation service | EPIC-BUD-003 | STORY-BUD-007, STORY-BUD-008 | 19 | Done | [`budget_availability.py`](../../kentender_budget/kentender_budget/services/budget_availability.py): `get_budget_availability`, `aggregate_ledger_buckets`, `availability_headroom`; posting uses same aggregation; [`test_budget_availability.py`](../../kentender_budget/kentender_budget/tests/test_budget_availability.py). |
| STORY-BUD-010 | Implement idempotency and concurrency protection for budget actions | EPIC-BUD-003 | STORY-BUD-008, STORY-BUD-009 | 20 | Done | Unique `idempotency_key` on ledger; `SELECT FOR UPDATE` on **Budget Line** before post; dedupe returns existing entry without duplicate audit; [`test_budget_ledger_idempotency.py`](../../kentender_budget/kentender_budget/tests/test_budget_ledger_idempotency.py). |
| STORY-BUD-011 | Implement Budget Allocation DocType | EPIC-BUD-004 | STORY-BUD-004 | 21 | Done | **Budget Allocation** ([`budget_allocation`](../../kentender_budget/kentender_budget/kentender_budget/doctype/budget_allocation/)); positive amount; header sync from line; [`test_budget_allocation.py`](../../kentender_budget/kentender_budget/tests/test_budget_allocation.py). |
| STORY-BUD-012 | Implement Budget Revision and Budget Revision Line DocTypes | EPIC-BUD-004 | STORY-BUD-011, STORY-BUD-004 | 22 | Done | **Budget Revision** + child **Budget Revision Line** ([`budget_revision`](../../kentender_budget/kentender_budget/kentender_budget/doctype/budget_revision/), [`budget_revision_line`](../../kentender_budget/kentender_budget/kentender_budget/doctype/budget_revision_line/)); Increase/Decrease/Transfer rules; [`test_budget_revision.py`](../../kentender_budget/kentender_budget/tests/test_budget_revision.py). |
| STORY-BUD-013 | Implement budget revision apply service | EPIC-BUD-004 | STORY-BUD-012, STORY-BUD-008, STORY-BUD-009 | 23 | Done | [`budget_revision_apply.apply_budget_revision`](../../kentender_budget/kentender_budget/services/budget_revision_apply.py); `minimum_allocated_envelope`; **Budget Allocation** trail; [`test_budget_revision_apply.py`](../../kentender_budget/kentender_budget/tests/test_budget_revision_apply.py). |
| STORY-BUD-014 | Implement downstream validation APIs | EPIC-BUD-005 | STORY-BUD-009 | 24 | Done | [`budget_downstream.py`](../../kentender_budget/kentender_budget/services/budget_downstream.py): `validate_budget_line`, `get_budget_availability`, `validate_funds_or_raise`; [`test_budget_downstream.py`](../../kentender_budget/kentender_budget/tests/test_budget_downstream.py). |
| STORY-BUD-015 | Implement budget audit event integration | EPIC-BUD-005 | STORY-BUD-008, STORY-BUD-013, STORY-CORE-016 | 25 | Done | [`budget_audit.log_budget_audit`](../../kentender_budget/kentender_budget/services/budget_audit.py); ledger posting uses it; revision + allocation emit `kt.budget.revision.applied` / `kt.budget.allocation.applied`; [`test_budget_audit_integration.py`](../../kentender_budget/kentender_budget/tests/test_budget_audit_integration.py). |
| STORY-BUD-016 | Implement budget unit/integration tests | EPIC-BUD-005 | STORIES BUD-001 through BUD-015 | 26 | Done | Cross-cutting flows in [`test_budget_integration.py`](../../kentender_budget/kentender_budget/tests/test_budget_integration.py); **Budget Revision** teardown uses `frappe.delete_doc` so child **Budget Revision Line** rows are removed (fixes orphan lines + triple-apply under `db.delete`). |

**Depends on:** Values match explicit `**Depends on:**` lines in the Ticket Pack. **STORY-BUD-004** and **STORY-BUD-005** explicitly depend on **STORY-STRAT-009**; completing the full strategy track through step **10** before step **14** satisfies that chain.

**Status values:** `Not Started` | `In Progress` | `Blocked` | `Done`

## Wave 2+

**Wave 2 (procurement)** is in flight: tracker [`WAVE 2 BACKLOG.md`](Wave%202%20BACKLOG.md), prompts [`docs/prompts/Wave 2 Ticket Pack.md`](../prompts/Wave%202%20Ticket%20Pack.md). The `docs/dev/Wave 2 Ticket Pack.md` file is a pointer to the prompts pack.

Later waves remain outlined in [`KenTender Master Epic Map.md`](KenTender%20Master%20Epic%20Map.md) until more ticket packs exist.
