# PERM implementation tracker

Checklist for user stories in [KenTender Permissions Cursor Implementation Pack](KenTender%20Permissions%20Cursor%20Implementation%20Pack.md). Update status and notes as work lands.

**Delivery order:** follow the story sequence (PERM-001 → PERM-015) unless dependencies clearly allow parallel prep.

**App note:** The pack references `kentender_core`. In this monorepo, shared permission code lives under the **`kentender`** app (`kentender.permissions`, `kentender.services.*`), not a separate `kentender_core` package.

**Status values:** `Not started` · `In progress` · `Partial` · `Done` · `Blocked` (explain in Notes) · `N/A` (e.g. domain not shipped yet).

**Related:** [Matrix audit tracking](Matrix%20audit%20tracking.md) (DocTypes, reports, workspaces vs guidance matrices).

**Progressive delivery:** Permission work is applied **with** domain user stories, not as a standalone full-repo audit. Use the checklist in [Permissions Architecture — Story-driven permission updates](Permissions%20Architecture.md#story-driven-permission-updates-progressive-delivery). After each relevant merge, update this tracker and the matrix audit. Do **not** bulk-change DocType `permissions` ahead of stories; baseline gaps (e.g. §3B planning DocTypes vs matrix) close under the owning PERM row when that story is scheduled.

---

| ID | Story (from pack) | Target | Status | Notes |
|----|-------------------|--------|--------|-------|
| PERM-001 | Permission architecture conventions | `kentender` + `docs/permissions` | Done | [Permissions Architecture](Permissions%20Architecture.md); `kentender/permissions/` package layout |
| PERM-002 | Role constants and permission registry | `kentender.permissions.registry` | Done | `BUSINESS_ROLE`, `UAT_ROLE`, helpers; tests in `kentender.tests.test_permissions_registry` |
| PERM-003 | Row-level scope helper framework | `kentender.services` + `kentender.permissions.scope` | Partial | `permission_query_service`, `entity_scope_service`, `assignment_access_service`; `scope.py` re-exports; extend with dept/HOD/finance patterns as domains need |
| PERM-004 | Report and queue access control framework | `kentender.permissions.reports` + domain queries | Partial | `user_can_open_script_report`; report `roles` JSON + row filters per report (see Matrix audit) |
| PERM-005 | Workflow action authorization framework | `kentender.services.controlled_action_service` | Partial | `run_controlled_action_gate`; adopt on all critical transitions domain-by-domain |
| PERM-006 | Assignment-based access hardening | `kentender.services.assignment_access_service` | Partial | Core helpers exist; wire into tender/evaluation/etc. when those flows ship |
| PERM-007 | Sensitivity and sealed-access enforcement | `protected_file_access_service`, `sensitivity_classification` | Partial | Extend coverage as DocTypes/files grow |
| PERM-008 | Requisition permission implementation | `kentender_procurement` | Partial | Queues + report row scope; DocType JSON vs §3B still to tighten |
| PERM-009 | Planning permission implementation | `kentender_procurement` | Partial | Reports + queue scoping in place; **DocType JSON vs §3B** (e.g. Requisitioner **X** on PP/PPI, HOD/Finance **RO/F**) ships **with** this story—see Architecture checklist. No preemptive bulk tighten elsewhere. |
| PERM-010 | Tender and bid permission implementation | future app / module | Not started | When tender DocTypes exist |
| PERM-011 | Evaluation permission implementation | future app / module | Not started | When evaluation DocTypes exist |
| PERM-012 | Award and contract permission implementation | future app / module | Not started | When award/contract DocTypes exist |
| PERM-013 | Inspection / stores / assets permission implementation | future app / module | Not started | When those DocTypes exist |
| PERM-014 | Report and queue permission implementation (cross-cutting) | all `kentender_*` | Partial | Align every shipped report + queue to §4+; strategy reports done; add new rows as reports appear |
| PERM-015 | Permission test suite and verification fixtures | `kentender` + domain `tests` | Partial | `test_permissions_*`, `test_requisition_queue_queries`; expand per domain |

---

## Quick checkbox roll-up (optional)

Use when you prefer a short sprint board; keep the table above as the source of truth.

- [x] PERM-001 — Architecture + skeleton  
- [x] PERM-002 — Role registry  
- [ ] PERM-003 — Row scope framework (complete cross-domain patterns)  
- [ ] PERM-004 — Report/queue framework (all reports + queries)  
- [ ] PERM-005 — Workflow actions (all critical paths)  
- [ ] PERM-006 — Assignment hardening  
- [ ] PERM-007 — Sensitivity / sealed  
- [ ] PERM-008 — Requisition (complete §3B + tests)  
- [ ] PERM-009 — Planning (complete)  
- [ ] PERM-010 — Tender / bid  
- [ ] PERM-011 — Evaluation  
- [ ] PERM-012 — Award / contract  
- [ ] PERM-013 — Inspection / stores / assets  
- [ ] PERM-014 — Reports/queues program-wide  
- [ ] PERM-015 — Test suite / fixtures program-wide  

---

## How to use

1. After each merge, set **Status** and a one-line **Note** (PR link, file paths, or gap).  
2. For **Not started** domain stories (PERM-010–013), switch to `In progress` only when the first DocType in that area lands.  
3. Reconcile this file with [Matrix audit tracking](Matrix%20audit%20tracking.md) so DocType/report rows and PERM rows do not contradict each other.
4. For **feature PRs** that touch security surfaces, confirm the story-driven checklist in [Permissions Architecture](Permissions%20Architecture.md#story-driven-permission-updates-progressive-delivery) was considered; update **Notes** here if a PERM slice moved (even if the main story ID is not PERM-00x).
