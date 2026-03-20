# KenTender Phase 2 UAT Script (Index)

## Scope
End-to-end UAT coverage for **Phase 2: Supplier Registration and Full Tendering Lifecycle**.

## Terminology conventions
- `APP` = Annual Procurement Plan (`Procurement Plan` + `Procurement Plan Item`).
- `Purchase Requisition (PR)` = approved upstream demand record.
- `Phase 2 chain` = `Supplier -> Tender -> Submission -> Evaluation -> Award -> Handoff`.

## UAT split
- `docs/uat/phase2-uat-01-supplier-to-award-lifecycle.md`

## Latest validated evidence
- Supplier registration and activation:
  - `SRA-2026-00057` -> `SUPM-2026-00058`
- Tender and submission:
  - `TN-2026-00059` -> `TS-2026-00061`
- Evaluation and award:
  - `EVD-2026-00062`, `EVW-2026-00063`, `AR-2026-00064`, `AD-2026-00065`
- Challenge hold and finalization:
  - `CRC-2026-00066` blocked award finalization until resolution.
- Handoff and downstream artifact:
  - `ACH-2026-00067` and `PUR-ORD-2026-00013`

## Preconditions (common baseline)
- Phase 1/1.5 upstream controls are active.
- At least one approved `Procurement Plan Item` exists for tender lineage.
- Supplier compliance profile controls are active.
- Phase 2 workflows are provisioned (`Supplier Registration Workflow`, `Tender Workflow`).
