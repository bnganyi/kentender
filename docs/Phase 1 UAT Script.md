# KenTender Phase 1 UAT Script (Index)

## Scope
End-to-end UAT coverage for **Phase 1: Procurement Planning and Budgeting**.

## Terminology conventions
- `APP` = Annual Procurement Plan (`Procurement Plan` and its plan items).
- `Purchase Requisition (PR)` = pre-tender demand-finalization and commitment control record.
- UAT docs use `PR` only after first expansion.

## Recommended split (module-focused)
For tractability, UAT is split into small documents:
- `docs/uat/phase1-uat-01-app-and-plan-item-governance.md`
- `docs/uat/phase1-uat-02-purchase-requisition-budget-and-handoff.md`

Latest validated evidence:
- APP governance run: `PP-2026-00047` (full status path to `Locked`) documented in `phase1-uat-01`.
- Requisition full-run: `PR-2026-00050` with `PRC-2026-00051` and `PRS-2026-00052` documented in `phase1-uat-02`.

Current priority modules to add next:
- Desk dashboard/report UI packaging (API layer already validated)
- scheduled evidence-bundle packaging and distribution controls

Phase 2 UAT baseline:
- `docs/uat/phase2-uat-01-supplier-to-award-lifecycle.md`
- `docs/Phase 2 UAT Script.md`

## Preconditions (common baseline)
- Bench and site are up.
- Policy profiles / threshold rules / approval matrix rules are created and active.
- At least one valid strategic objective hierarchy exists for strategic alignment enforcement tests.
- Roles are configured according to the Phase 1 SoD (segregation of duties) rules.

