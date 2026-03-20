# KenTender Phase 1.5: Purchase Requisition / Demand Finalization (Technical Reference)

## Scope
Phase 1.5 treats `Purchase Requisition (PR)` as a standalone internal control module between APP and tendering:
- `Procurement Plan / Procurement Plan Item -> Purchase Requisition (PR) -> Tender`.

This module is now the operational gate for:
- demand finalization,
- PR-level budget discipline,
- commitment creation,
- and tender-readiness evidence.

## Design Inputs Incorporated
- `docs/Phase 1.5 - Purchase Requisition Design.md`
- `purchase-requisition-inputs/*` (doctypes, workflow, hook scaffolds)

## Implemented Data Model (current baseline)

### Existing requisition header (extended via custom fields)
- `Purchase Requisition` now includes Phase 1.5 governance fields such as:
  - `entity`, `requestor`, `financial_year`, `requisition_type`, `source_mode`,
  - `required_by_date`, `delivery_location`, `currency`,
  - `total_estimated_cost`, `total_committed_amount`, `total_released_amount`,
  - `budget_status`, `approval_status`, `emergency_flag`, `one_off_flag`, `exception_flag`,
  - `tender_readiness_status`, `submitted_on`, `approved_on`, `cancelled_on`, `closed_on`,
  - table links: `items` (`Purchase Requisition Item`) and `approvals` (`Purchase Requisition Approval`).

### New Phase 1.5 DocTypes added
- `Purchase Requisition Item` (child table)
- `Purchase Requisition Approval` (child table)
- `Purchase Requisition Commitment`
- `Purchase Requisition Exception`
- `Purchase Requisition Snapshot`
- `Purchase Requisition Amendment`
- `Requisition Tender Handoff`

## Server-Side Enforcement (live hooks)
- Hook file: `kentender/hooks.py`
- Active handlers:
  - `Purchase Requisition.validate -> phase1_validate_purchase_requisition`
  - `Purchase Requisition.on_update -> phase1_on_update_purchase_requisition`
  - `Purchase Requisition Amendment.on_submit -> phase15_on_submit_purchase_requisition_amendment`

## Budget Lifecycle Refactor (from APP-line-only to requisition-centric)

### Before refactor
- Budget commitment logic depended on a single header field (`procurement_plan_item`) and created one generic commitment record.

### After refactor
- Validation supports full line-level requisition controls:
  - line-level APP linkage checks for `source_mode = APP Linked`,
  - remaining APP balance checks per linked line,
  - aggregated `total_estimated_cost`,
  - one-off control path (`source_mode = One-Off`) requiring exception governance.
- On requisition approval (`status = Approved`):
  - create `Purchase Requisition Commitment` record(s),
  - update linked APP line(s) commitment lifecycle (`committed_amount`, `budget_status`, `line_status`),
  - update parent APP totals,
  - create `Purchase Requisition Snapshot` (Approval),
  - set requisition `budget_status = Committed`,
  - set requisition `tender_readiness_status = Ready for Tender`.
- On cancellation (`status = Cancelled`):
  - release active requisition commitments,
  - stamp cancellation metadata.

## Workflow
- Active workflow record: `Purchase Requisition Workflow`
- Setup function: `phase15_setup_purchase_requisition_workflow()`
- Default state path:
  - `Draft -> Submitted -> HoD Review -> Finance Review -> AO Review -> Procurement Review -> Approved`
  - with return/reject/cancel paths.

## Migrate-Time Model Setup
- `after_migrate` hook calls `phase1_after_migrate_setup` which:
  - ensures required `Custom Field` extensions on `Purchase Requisition`,
  - ensures table links (`items`, `approvals`),
  - ensures workflow dependencies/record setup.

## Validation checkpoint (2026-03-20)
- Fresh line-based requisition `PR-2026-00050` validated through full workflow:
  - `Submit -> Route to HoD -> Approve HoD -> Approve Finance -> Approve AO -> Approve Final`.
- Final state and control outcomes confirmed:
  - `status = Approved`
  - `budget_status = Committed`
  - `tender_readiness_status = Ready for Tender`
  - `total_estimated_cost = 750.0`, `total_committed_amount = 750.0`
- Evidence records created:
  - `Purchase Requisition Commitment`: `PRC-2026-00051`
  - `Purchase Requisition Snapshot`: `PRS-2026-00052` (`snapshot_type = Approval`)
- Runtime compatibility corrections confirmed in baseline:
  - requisition autoname set to `PR-{YYYY}-{#####}`,
  - requisition status options aligned with full Phase 1.5 workflow states.

## Requisition handoff to Tender integration (2026-03-20)
- Controlled handoff service implemented:
  - `phase15_handoff_requisition_to_tender(requisition_name, publish_immediately, remarks)`
- Behavior:
  - enforces `Purchase Requisition (PR)` status = `Approved`,
  - enforces readiness gate (`Ready for Tender`/`Tender Created`/`Fully Handed Off`),
  - resolves linked `Procurement Plan Item` rows from PR lines,
  - creates `Tender` records where none exist (or reuses open tenders),
  - upserts `Requisition Tender Handoff` evidence (`handoff_status = Tender Created`),
  - updates PR rollup fields (`linked_tender_count`, `tender_readiness_status`),
  - writes immutable audit event (`phase15_requisition_tender_handoff`).
- Validation evidence:
  - PR: `PR-2026-00050`
  - Handoff: `RTH-2026-00054`
  - Tender created: `TN-2026-00053`
  - PR state after handoff: `linked_tender_count = 1`, `tender_readiness_status = Fully Handed Off`
  - Idempotent rerun reused existing tender (`created_tenders = []`, `reused_tenders = ['TN-2026-00053']`).

## Current Gaps / Next Hardening Targets
- Exception and anti-split routes are partially scaffolded; matrix-driven escalation depth should be tightened.
- Scheduled controls (aging alerts, emergency post-review SLA) still pending.
