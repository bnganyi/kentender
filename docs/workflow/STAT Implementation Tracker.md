# STAT implementation tracker

Checklist for [KenTender Cursor Refactor Pack — Status Standardization](KenTender%20Cursor%20Refactor%20Pack%20%E2%80%94%20Status%20Standardization.md). Update **Status** and **Notes** as work lands.

**Canonical model:** [KenTender Standard Status Model (System-Wide)](KenTender%20Standard%20Status%20Model%20%28System-Wide%29.md).

**Workflow behavior (overlapping):** [KenTender Approval Workflow Specification v2](KenTender%20Approval%20Workflow%20Specification%20v2.md).

**Shared engine / field guards:** [WF Implementation Tracker](WF%20Implementation%20Tracker.md) (WF-002 cross-links STAT-004).

**App note:** Refactor pack names `kentender_core`. This bench implements shared code under **`kentender`** (same as WF tracker).

**Status values:** `Not started` · `In progress` · `Partial` · `Done` · `Blocked` · `N/A`.

---

| ID | Story | Target app / paths | Depends on | Status | Notes |
|----|-------|--------------------|------------|--------|-------|
| STAT-001 | Status standard + classification framework | `docs/workflow/`, `kentender/status_model/` | — | Done | [Developer framework](KenTender%20Status%20Standard%20%E2%80%94%20Developer%20Framework.md) |
| STAT-002 | DocType status audit | [STAT-002 DocType status audit](STAT-002%20DocType%20status%20audit.md) | STAT-001 | Done | Priority rows + gaps |
| STAT-003 | workflow_state → status mapping helpers | `kentender/status_model/derived_status.py`, tests | STAT-001 | Done | Per-doctype registry |
| STAT-004 | Backend read-only protection | `workflow_engine/safeguards.py`, hooks | STAT-001 | Done | workflow_state-only registry for PR; `ignore_workflow_field_protection` for scripted fixes |
| STAT-005 | Purchase Requisition status model | `kentender_procurement` | STAT-002–004, STAT-003 | Done | Derived `status`; deprecated hidden `approval_status` |
| STAT-006 | Procurement Plan + Plan Item | — | STAT-002 | N/A | DocTypes not in repo |
| STAT-007 | Tender + Bid Submission | — | STAT-002 | N/A | DocTypes not in repo |
| STAT-008 | Evaluation + Award | — | STAT-002 | N/A | DocTypes not in repo |
| STAT-009 | Contract + Acceptance | — | STAT-002 | N/A | DocTypes not in repo |
| STAT-010 | GRN + Asset | — | STAT-002 | N/A | DocTypes not in repo |
| STAT-011 | Reports / filters → workflow_state | `requisition_queue_queries.py`, reports | STAT-005 | Done | Requisition reports; no other shipped reports in scope |
| STAT-012 | Forms / UI labels | PR DocType JSON | STAT-005 | Done | Stage label; hidden derived duplicates |
| STAT-013 | Migration / patches | `patches`, [STAT-013 migration notes](STAT-013%20migration%20notes.md) | STAT-005 | Done | Backfill derived PR fields |
| STAT-014 | Regression test suite | `kentender_procurement/tests/test_status_consistency.py` | STAT-003–005, STAT-011 | Done | Backend + report smoke |

---

## WF alignment

- **WF-002:** Purchase Requisition approval-controlled registry is **`workflow_state` only**; derived `status` / legacy `approval_status` are enforced via `validate` + DocType metadata, not the mutation hook.
- **WF-011:** Requisition services mutate **`workflow_state`** only; summary fields follow `kentender.status_model.derived_status`.

---

## Checkbox roll-up

- [x] STAT-001  
- [x] STAT-002  
- [x] STAT-003  
- [x] STAT-004  
- [x] STAT-005  
- [x] STAT-006 — STAT-010 (N/A pending DocTypes)  
- [x] STAT-011  
- [x] STAT-012  
- [x] STAT-013  
- [x] STAT-014  

---

## How to use

1. Every status-standardization PR cites **STAT-ID** + spec section where relevant.  
2. After merge, update this table.  
3. When new procurement DocTypes ship (Plan, Tender, …), replace **N/A** rows with real paths and split work from this tracker.
