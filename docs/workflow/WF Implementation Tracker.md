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
| WF-002 | Approval-controlled field protection | `workflow_engine/safeguards.py` + `hooks.py` + `approval_field_registry.py` | Wave 0 follow-on | Done | **`workflow_state`** for **Purchase Requisition**, **Tender**, **Procurement Plan**, **Award Decision**, **Procurement Contract**, **Acceptance Record**, **Complaint**; `doc_events` **`*`** `validate` → `document_validate_approval_controlled_fields`; derived `status` via STAT-003; `workflow_mutation_context` + flags |
| WF-003 | Global approval action record | DocType **KenTender Approval Action** | Wave 0 follow-on | Done | Append-only validate; requisition transitions log rows |
| WF-004 | Workflow policy model | DocType **KenTender Workflow Policy** | Wave 0 follow-on | Done | Config for route resolution |
| WF-005 | Approval route template + steps | **KenTender Approval Route Template**, **KenTender Approval Route Template Step** | Wave 0 follow-on | Done | Child table `steps` |
| WF-006 | Approval route instance + steps | **KenTender Approval Route Instance**, **KenTender Approval Route Step** | Wave 0 follow-on | Done | Runtime route state |
| WF-007 | Route resolver service | `workflow_engine/routes.py` + `policies.py` | Wave 0 follow-on | Done | Extended `policy_matches_document` (incl. **Acceptance Record** `accepted_value_amount` for thresholds; **Complaint** `complaint_type` vs policy `category`); `evaluation_order` on policy; `list_matching_policies` sorted; `get_or_create_active_route`; `resolved_on`; first route step **Active** |
| WF-008 | Workflow action execution service | `workflow_engine/execution.py` + `actions.py` | Wave 0 follow-on | Done | `apply_step_decision`, `get_current_step_row`, `assert_actor_allowed_on_step`; logs + hooks after route mutation (**assignment_required** on template still deferred) |
| WF-009 | SoD enforcement helpers | `workflow_engine/policies.py` | Wave 0 follow-on | Done | `assert_no_blocking_sod` (+ `proposed_role` / `scope_key`); [`test_workflow_policies_sod.py`](../../kentender/kentender/tests/test_workflow_policies_sod.py); requisition uses wrapper |
| WF-010 | Side-effect hook framework | `workflow_engine/hooks.py` | Wave 0 follow-on | Done | `register_side_effect_hook` / `run_side_effects`; optional per-**action** filter; `emit_post_transition` from `execution.apply_step_decision` |
| WF-011 | Requisition workflow implementation | `kentender_procurement` | Wave 2 | Done | Spec v2 §7.1 stages; submit resolves route (fail if no policy); 1–2 step templates; `apply_step_decision` after PR save; budget reservation **final step only**; `approve_requisition_hod` / `approve_requisition_finance` |
| WF-012 | Award workflow | `kentender_procurement` | Wave 3+ | Done | `award_approval_services.py`: submit + route + `apply_step_decision`; SoD + controlled gates; [`test_award_workflow_engine.py`](../../kentender_procurement/kentender_procurement/tests/test_award_workflow_engine.py) |
| WF-013 | Contract workflow | `kentender_procurement` | Wave 3+ | Done | `contract_approval_signature_services.py` + `contract_activation_service.py` (`workflow_mutation_context`); signing unchanged; [`test_contract_workflow_engine.py`](../../kentender_procurement/kentender_procurement/tests/test_contract_workflow_engine.py) |
| WF-014 | Acceptance dynamic workflow | `kentender_procurement` | Wave 3+ | Done | `acceptance_workflow_actions.py`; `submit_acceptance_decision(..., use_engine_workflow=True)` → draft + submit pipeline; policy thresholds via `accepted_value_amount`; [`test_acceptance_workflow_engine.py`](../../kentender_procurement/kentender_procurement/tests/test_acceptance_workflow_engine.py) |
| WF-015 | Complaint dynamic workflow | `kentender_governance` | Wave 3+ | Done | `complaint_workflow_actions.py`; intake attaches route; admissibility review completes step; holds unchanged; [`test_complaint_workflow_engine.py`](../../kentender_governance/kentender_governance/tests/test_complaint_workflow_engine.py) |
| WF-016 | Workflow test suite | `kentender.tests` | Ongoing | Done | [`test_workflow_engine.py`](../../kentender/kentender/tests/test_workflow_engine.py) — safeguards (PR/Tender/PP), resolver, execution, side-effect hooks + action filter; [`test_workflow_policies_sod.py`](../../kentender/kentender/tests/test_workflow_policies_sod.py) |

---

## Planning chain (Wave 2)

| Tracker row | PROC stories | Rule |
|---------------|--------------|------|
| Planning workflow alignment | PROC-011–022 | **WF-PLAN-001** done — [`procurement_plan_workflow_actions.py`](../../kentender_procurement/kentender_procurement/services/procurement_plan_workflow_actions.py) + tests; policies/templates per site (see pack). |

---

## Checkbox roll-up

- [x] WF-001  
- [x] WF-002  
- [x] WF-003  
- [x] WF-004  
- [x] WF-005  
- [x] WF-006  
- [x] WF-007  
- [x] WF-008 (core route-step path; template `assignment_required` TBD)  
- [x] WF-009  
- [x] WF-010  
- [x] WF-011 (requisition engine-backed; 1–2 steps)  
- [x] WF-012 — WF-015  
- [x] WF-016  

---

## How to use

1. Every workflow PR cites **spec section** + **WF-ID** in the description.  
2. After merge, update this table and the relevant **WAVE n BACKLOG** row.  
3. Keep [PERM Implementation Tracker](../permissions/PERM%20Implementation%20Tracker.md) in sync where reports/list views depend on workflow state.
