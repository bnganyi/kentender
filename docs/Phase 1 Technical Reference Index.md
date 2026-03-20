# KenTender Phase 1 Technical Reference Index

This directory contains module-focused technical documentation for KenTender **Phase 1: Procurement Planning and Budgeting**.

## Terminology conventions
- `APP` = Annual Procurement Plan (`Procurement Plan` + `Procurement Plan Item`).
- `Purchase Requisition (PR)` = Phase 1.5 demand-finalization record before tendering.
- Use `PR` only after first explicit mention as `Purchase Requisition (PR)`.

## Recommended reading order (module docs)
1. [`technical/phase1-procurement-planning-and-budgeting.md`](technical/phase1-procurement-planning-and-budgeting.md)
   - Strategic alignment enforcement
   - APP controls (versioning, approval, locking)
   - Plan item governance
   - Budget lifecycle and commitment rules
   - Threshold/method advisory + anti-split protections
   - Requisition handoff gates
   - Reporting / dashboards
2. [`technical/phase1-5-purchase-requisition-demand-finalization.md`](technical/phase1-5-purchase-requisition-demand-finalization.md)
   - Purchase Requisition as mandatory pre-tender control gate
   - Line-level APP linkage and budget/commitment controls
   - Approval, amendment, exception, snapshot, and tender handoff records
3. [`phase1_reporting_and_export.md`](phase1_reporting_and_export.md)
   - Phase 1 reporting snapshot API
   - CSV handoff export API
   - Validation evidence for reporting outputs

## Latest validation references
- Fresh requisition workflow and commitment evidence:
  - `docs/uat/phase1-uat-02-purchase-requisition-budget-and-handoff.md`
- Consolidated traceability checkpoints:
  - `docs/Phase 1 Coverage + Traceability (Master).md`
  - `docs/Phase 1 Coverage Checkpoint Matrix.md`

## Phase 2 extension references
- Technical baseline:
  - `docs/technical/phase2-supplier-registration-and-full-tendering-lifecycle.md`
- UAT baseline:
  - `docs/uat/phase2-uat-01-supplier-to-award-lifecycle.md`
 - Phase 2 technical index:
   - `docs/Phase 2 Technical Reference Index.md`
 - Phase 2 traceability:
   - `docs/Phase 2 Coverage + Traceability (Master).md`
   - `docs/Phase 2 Coverage Checkpoint Matrix.md`

