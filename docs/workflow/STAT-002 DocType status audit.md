# STAT-002 — DocType status field audit

Inventory of status-like fields in **kentender_platform** at STAT delivery. Use this to sequence refactors.

**Legend:** **A** lifecycle · **B** authoritative workflow · **C** derived summary · **D** deprecated duplicate · **Inv** investigate

## Shipped DocTypes (this repo)

| DocType | workflow_state | status | approval_status | read_only (workflow) | Report / filter usage | Classification |
|---------|----------------|--------|-----------------|----------------------|-------------------------|----------------|
| **Purchase Requisition** | Select | Select | Select | Yes (all three UI) | Queues use `workflow_state` for stage; list fields included legacy columns | **B** + **C** (derived) + **D** (hidden mirror) — STAT-005 applied |
| **Budget** | Data | Select (Active/Superseded/…) | Select | Partial | Downstream budget validation | **Inv** — operational `status` ≠ approval stage; not mapped to STAT PR model |
| **Budget Line** | — | Select | — | — | Operational | **Inv** |
| **Entity Strategic Plan** | Select | ? | Select | workflow read_only | Strategy tests | **Inv** — align in future wave |
| **Requisition Approval Record** | — | — | — | — | Child of PR | N/A |
| **Requisition Amendment Record** | — | Select | — | — | Amendment lifecycle | N/A |

## Priority pack DocTypes — not in repo (STAT-006–010)

| DocType | Note |
|---------|------|
| Procurement Plan, Procurement Plan Item | Not shipped — **N/A** |
| Tender, Bid Submission | Not shipped — **N/A** |
| Evaluation Session, Evaluation Report, Award Decision | Not shipped — **N/A** |
| Contract, Acceptance Record | Not shipped — **N/A** |
| Goods Receipt Note, Asset | Not shipped — **N/A** |

## Overlap / conflict findings

1. **Purchase Requisition (before STAT-005):** Three parallel selects (`status`, `workflow_state`, `approval_status`) could diverge; services wrote all three. **Fix:** authoritative **B** = `workflow_state`; **C** = `status` derived; **D** = `approval_status` hidden, mirrored to `workflow_state` for legacy reads.
2. **Budget:** `status` mixes version lifecycle (Active, Superseded) with `approval_status` and loose `workflow_state` Data field — **do not** apply PR summary mapping without a separate design.
3. **Reports:** Requisition script reports delegate to `requisition_queue_queries`; filters already stage on `workflow_state`. Column labels updated in STAT-011/012.

## Assumptions

- “Approval-controlled” in WF-002 sense applies first to DocTypes that use `requisition_workflow_actions` / engine transitions.
- Import/Data Migration may set fields with `workflow_mutation_context` or patch flags (see safeguards).

## Open questions

- Unified **Budget** workflow model vs strategy ESP — defer to budget/strategy epic.
- Whether to drop `approval_status` column entirely (DB migration) vs hidden mirror — mirror chosen for low-risk rollout.
