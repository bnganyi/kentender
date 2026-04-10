# WF implementation tracker

Checklist for stories in [KenTender Cursor Workflow Implementation Pack v2](KenTender%20Cursor%20Workflow%20Implementation%20Pack%20v2.md). Update **Status** and **Notes** as work lands.

**Specification (must read for behavior):** [KenTender Approval Workflow Specification v2](KenTender%20Approval%20Workflow%20Specification%20v2.md).

**Delivery order:** WF-001 → WF-016 unless a ticket explicitly unblocks a subset.

**App note:** The pack names `kentender_core`. Implement shared engine under **`kentender`** (`kentender.workflow_engine`, DocTypes in module **KenTender**).

**Status values:** `Not started` · `In progress` · `Partial` · `Done` · `Blocked` · `N/A`.

**Wave linkage:** See [KenTender Master Epic Map](../dev/KenTender%20Master%20Epic%20Map.md), [WAVE 0 BACKLOG](../dev/WAVE%200%20BACKLOG.md) (WF platform follow-on), [WAVE 2 BACKLOG](../dev/WAVE%202%20BACKLOG.md) (WF-011 + planning alignment).

---

| ID | Story | Target | Wave / epic | Status | Notes |
|----|-------|--------|-------------|--------|-------|
| WF-001 | Workflow engine architecture skeleton | `docs/workflow/` + `kentender.workflow_engine` | Wave 0 follow-on | Done | [Workflow Engine Architecture](Workflow%20Engine%20Architecture.md); package `policies`, `routes`, `actions`, `safeguards`, `hooks` |
| WF-002 | Approval-controlled field protection | `workflow_engine/safeguards.py` + `hooks.py` | Wave 0 follow-on | Partial | PR: **workflow_state** only (STAT-004/005); derived `status` in `validate`; `workflow_mutation_context` + `allow_approved_requisition_mutation` + `ignore_workflow_field_protection` |
| WF-003 | Global approval action record | DocType **KenTender Approval Action** | Wave 0 follow-on | Done | Append-only validate; requisition transitions log rows |
| WF-004 | Workflow policy model | DocType **KenTender Workflow Policy** | Wave 0 follow-on | Done | Config for route resolution |
| WF-005 | Approval route template + steps | **KenTender Approval Route Template**, **KenTender Approval Route Template Step** | Wave 0 follow-on | Done | Child table `steps` |
| WF-006 | Approval route instance + steps | **KenTender Approval Route Instance**, **KenTender Approval Route Step** | Wave 0 follow-on | Done | Runtime route state |
| WF-007 | Route resolver service | `workflow_engine/routes.py` + `policies.py` | Wave 0 follow-on | Done | Extended `policy_matches_document`; `evaluation_order` on policy; `list_matching_policies` sorted; `get_or_create_active_route`; `resolved_on`; first route step **Active** |
| WF-008 | Workflow action execution service | `workflow_engine/execution.py` + `actions.py` | Wave 0 follow-on | Done | `apply_step_decision`, `get_current_step_row`, `assert_actor_allowed_on_step`; logs + hooks after route mutation (**assignment_required** on template still deferred) |
| WF-009 | SoD enforcement helpers | `workflow_engine/policies.py` | Wave 0 follow-on | Partial | `assert_no_blocking_sod` → `separation_of_duty_service` |
| WF-010 | Side-effect hook framework | `workflow_engine/hooks.py` | Wave 0 follow-on | Partial | `register_side_effect_hook`, `run_side_effects` |
| WF-011 | Requisition workflow implementation | `kentender_procurement` | Wave 2 | Done | Spec v2 §7.1 stages; submit resolves route (fail if no policy); 1–2 step templates; `apply_step_decision` after PR save; budget reservation **final step only**; `approve_requisition_hod` / `approve_requisition_finance` |
| WF-012 | Award workflow | future | Wave 3+ | Not started | When award DocTypes exist |
| WF-013 | Contract workflow | future | Wave 3+ | Not started | |
| WF-014 | Acceptance dynamic workflow | future | Wave 3+ | Not started | |
| WF-015 | Complaint dynamic workflow | future | Wave 3+ | Not started | |
| WF-016 | Workflow test suite | `kentender.tests` | Ongoing | Partial | [`test_workflow_engine.py`](../../kentender/kentender/tests/test_workflow_engine.py) — resolver, execution, policy ordering/threshold |

---

## Planning chain (Wave 2)

| Tracker row | PROC stories | Rule |
|---------------|--------------|------|
| Planning workflow alignment | PROC-011–022 | Do **not** add a second bespoke approval engine; **Procurement Plan** approvals use `workflow_engine` + spec v2 once templates exist (after WF-007/008 hardening). |

---

## Checkbox roll-up

- [x] WF-001  
- [ ] WF-002 (extend to more DocTypes)  
- [x] WF-003  
- [x] WF-004  
- [x] WF-005  
- [x] WF-006  
- [x] WF-007  
- [x] WF-008 (core route-step path; template `assignment_required` TBD)  
- [ ] WF-009  
- [ ] WF-010  
- [x] WF-011 (requisition engine-backed; 1–2 steps)  
- [ ] WF-012 — WF-015  
- [ ] WF-016  

---

## How to use

1. Every workflow PR cites **spec section** + **WF-ID** in the description.  
2. After merge, update this table and the relevant **WAVE n BACKLOG** row.  
3. Keep [PERM Implementation Tracker](../permissions/PERM%20Implementation%20Tracker.md) in sync where reports/list views depend on workflow state.
