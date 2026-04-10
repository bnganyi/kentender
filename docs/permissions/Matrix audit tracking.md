# Matrix audit tracking (DocTypes and reports)

Living checklist against [Roles and Permissions Guidance](Roles%20and%20Permissions%20Guidance.md). Update as DocTypes ship or matrices change.

**Implementation-pack stories:** track PERM-001–015 in [PERM Implementation Tracker](PERM%20Implementation%20Tracker.md).

**Progressive alignment:** Rows below move toward **OK** / **Done** **when the owning user story or PERM story** updates DocType JSON, reports, workspaces, and row filters—not via a standalone “fix all permissions” pass. Follow [Permissions Architecture — Story-driven permission updates](Permissions%20Architecture.md#story-driven-permission-updates-progressive-delivery). Known baseline drift (e.g. Requisitioner edit on PP/PPI) is **accepted until PERM-009** (or equivalent) tightens §3B planning objects.

## DocType baseline (§3)

| App | Area | Status | Notes |
|-----|------|--------|-------|
| kentender_strategy | §3A Strategy / budget refs | Partial | National / entity / program chain exists; diff each DocType `permissions` vs matrix (R/RO/X cells). |
| kentender_budget | §3A Budget Control Period, Budget, lines | Partial | Same — confirm Requisitioner/HOD **X** on Budget / Ledger where matrix says **X**. |
| kentender_procurement | §3B Requisition / planning | Partial | Purchase Requisition: matrix **HOD R/A/F** vs JSON (may still grant broad **write**); tighten in a focused change after workflow SoD review. |
| kentender_procurement | §3B Planning objects | Partial | Matrix: Procurement **C/R/W/S/A**; Requisitioner **X** on PP/PPI. Baseline JSON may still be broad until **PERM-009** / planning-permissions story; track deltas per Architecture checklist. |
| kentender_* (future) | §3C Tender / bids | Not shipped | No matrix sign-off until DocTypes land. |
| kentender_* (future) | §3D Evaluation / award | Not shipped | — |
| kentender_* (future) | §3E Contract / stores / assets | Not shipped | — |

## Reports (§4+)

| Report | App | Matrix alignment | Notes |
|--------|-----|------------------|-------|
| My Requisitions | kentender_procurement | OK | Requisitioner **Yes**; optional others. |
| Pending Requisition Approvals | kentender_procurement | Updated | Requisitioner **No**; HOD, Finance, Procurement (optional), Auditor, Admin. |
| Planning Ready Requisitions | kentender_procurement | Updated | Procurement **Yes**; Requisitioner/HOD **No**; Finance optional; Auditor/Admin. |
| Strategy Active Plans By Entity | kentender_strategy | Updated | Strategy / budget / requisitioner-family **RO** read path. |
| Strategy Indicators And Targets By Entity | kentender_strategy | Updated | Same. |
| Strategy Programs By Objective | kentender_strategy | Updated | Same. |

## Row filters (§§5–7)

| Surface | Status | Implementation |
|---------|--------|----------------|
| Pending Requisition Approvals (query) | Implemented | `requisition_queue_queries.get_pending_requisition_approvals` — entity scope + HOD/Finance assignment fields + procurement/auditor/central patterns. |
| Planning Ready Requisitions (query) | Implemented | Restricted to procurement/finance/auditor/central roles; entity scope. |

Further domains should call `kentender.permissions.scope.merge_entity_scope_filters` and registry-driven role checks in their own query modules.

## Workspaces (Layer A)

| Workspace | Change |
|-----------|--------|
| KenTender Approvals | New: **Pending Requisition Approvals** for HOD, Finance, Procurement, Auditor, System Manager. |
| KenTender My Work | Approval/planning report shortcuts removed so requisitioners are not shown reports they cannot open. |
| KenTender Procurement | **KT UAT Requisitioner**, HOD, and Finance removed from workspace roles; **KT UAT Auditor** added. Pending report links removed (use Approvals). |
