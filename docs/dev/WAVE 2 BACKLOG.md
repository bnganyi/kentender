# Wave 2 backlog (tracking)

**Purpose:** Sprint and PR tracking only. Do **not** duplicate full objectives, scope, acceptance criteria, tests, or Cursor prompts here.

**Maintenance:** After each merged story (or agreed milestone), update the **Status** and **Notes** columns for that row. Use `Done` only when the ticket’s acceptance criteria in the pack are met.

**Canonical source:** Every Wave 2 story’s full ticket lives in [`Wave 2 Ticket Pack.md`](../prompts/Wave%202%20Ticket%20Pack.md) under the matching `**PROC-STORY-xxx**` heading.

**Execution order:** Follow the pack’s **Recommended build order** (steps **1–22** below): requisition chain **1–10**, then planning chain **11–22**. Do **not** start planning epics before the requisition foundation they consume unless the pack explicitly allows a parallel stub.

**Prerequisites**

- **Upstream:** Wave 0 and Wave 1 closed for the target environment ([`WAVE 0 BACKLOG.md`](Wave%200%20BACKLOG.md), [`WAVE 1 BACKLOG.md`](Wave%201%20BACKLOG.md)).
- **App:** `kentender_procurement` — scaffold under [`kentender_procurement/`](../../kentender_procurement/); `required_apps`: `kentender`, `kentender_strategy`, `kentender_budget` (see [`app-dependencies-and-boundaries.md`](../architecture/app-dependencies-and-boundaries.md)). Install on the site and run `bench migrate` as DocTypes land.
- **Tests:** `bench run-tests --app kentender_procurement` once tests exist; keep green per story where applicable.

| Story ID | Title (short) | Epic | Depends on (pack) | Step # | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| PROC-STORY-001 | Implement Purchase Requisition DocType | EPIC-PROC-001 | Wave 0 + Wave 1 complete | 1 | Not Started | |
| PROC-STORY-002 | Purchase Requisition Item child table | EPIC-PROC-001 | PROC-STORY-001 | 2 | Not Started | |
| PROC-STORY-003 | Requisition totals and validation logic | EPIC-PROC-001 | PROC-STORY-001, PROC-STORY-002, strategy/budget services | 3 | Not Started | |
| PROC-STORY-004 | Requisition Approval Record | EPIC-PROC-001 | PROC-STORY-001 | 4 | Not Started | |
| PROC-STORY-005 | Requisition workflow action services | EPIC-PROC-001 | PROC-STORY-004; workflow guard + SoD framework (Wave 0) | 5 | Not Started | |
| PROC-STORY-006 | Budget reservation on final approval | EPIC-PROC-001 | PROC-STORY-005; budget services | 6 | Not Started | |
| PROC-STORY-007 | Requisition Amendment Record | EPIC-PROC-001 | PROC-STORY-001 | 7 | Not Started | |
| PROC-STORY-008 | Amendment application service | EPIC-PROC-001 | PROC-STORY-007; budget services | 8 | Not Started | |
| PROC-STORY-009 | Requisition Planning Link + planning status | EPIC-PROC-001 | PROC-STORY-001 | 9 | Not Started | |
| PROC-STORY-010 | Requisition tests + queue/report scaffolding | EPIC-PROC-001 | PROC-STORY-001 … 009 | 10 | Not Started | |
| PROC-STORY-011 | Procurement Plan DocType | EPIC-PROC-002 | Requisition foundation; strategy; budget | 11 | Not Started | |
| PROC-STORY-012 | Procurement Plan Item DocType | EPIC-PROC-002 | PROC-STORY-011 | 12 | Not Started | |
| PROC-STORY-013 | Plan Consolidation Source | EPIC-PROC-002 | PROC-STORY-012; requisition planning link model | 13 | Not Started | |
| PROC-STORY-014 | Plan totals and reconciliation logic | EPIC-PROC-002 | PROC-STORY-011, 012, 013 | 14 | Not Started | |
| PROC-STORY-015 | Procurement Plan Approval Record | EPIC-PROC-002 | PROC-STORY-011 | 15 | Not Started | |
| PROC-STORY-016 | Plan Fragmentation Alert | EPIC-PROC-002 | PROC-STORY-012 | 16 | Not Started | |
| PROC-STORY-017 | Fragmentation scan service | EPIC-PROC-002 | PROC-STORY-016, PROC-STORY-012 | 17 | Not Started | |
| PROC-STORY-018 | Requisition-to-plan consolidation service | EPIC-PROC-002 | Planning link; plan item; consolidation source | 18 | Not Started | |
| PROC-STORY-019 | Procurement Plan Revision + revision lines | EPIC-PROC-002 | PROC-STORY-011, PROC-STORY-012 | 19 | Not Started | |
| PROC-STORY-020 | Plan revision apply service | EPIC-PROC-002 | PROC-STORY-019 | 20 | Not Started | |
| PROC-STORY-021 | Plan to Tender Link + tender eligibility gate | EPIC-PROC-002 | Plan item model | 21 | Not Started | |
| PROC-STORY-022 | Plan tests + queue/report scaffolding | EPIC-PROC-002 | PROC-STORY-011 … 021 | 22 | Not Started | |

**Depends on:** Values follow explicit `**Depends on:**` lines in the Ticket Pack; narrative dependencies (e.g. “workflow guard framework”) map to Wave 0 **STORY-CORE-012**–**014** / related services.

**Status values:** `Not Started` | `In Progress` | `Blocked` | `Done`

## Wave 3+

Not tracked here. High-level follow-ons remain in [`KenTender Master Epic Map.md`](KenTender%20Master%20Epic%20Map.md) until a dedicated ticket pack exists.
