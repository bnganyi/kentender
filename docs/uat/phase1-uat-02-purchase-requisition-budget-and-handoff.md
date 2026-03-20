# Phase 1 UAT-02: Purchase Requisition Budget Lifecycle and Handoff

## Scope
Validate Phase 1.5 Purchase Requisition (PR) controls:
- PR model and line-level APP linkage,
- budget and commitment lifecycle updates at approval,
- cancellation/release controls,
- tender-readiness state updates,
- amendment evidence behavior.

## Preconditions
1. Site migrated after Phase 1.5 changes.
2. `Purchase Requisition Workflow` active.
3. Required masters exist:
   - `Procurement Plan Item` approved line(s),
   - `Spend Category`,
   - `Funding Source`,
   - `Cost Center`,
   - `UOM`.
4. Roles for route stages exist in the system.

## Scenario 1: Requisition model setup (positive)
1. Open `Purchase Requisition`.
2. Confirm Phase 1.5 fields are visible (`source_mode`, `required_by_date`, `items`, `approvals`, budget and readiness fields).
Expected:
- Fields are present and writable in draft mode.

## Scenario 2: APP-linked line validation (negative)
1. Create a PR in `APP Linked` mode with at least one line missing `procurement_plan_item`.
Expected:
- Validation blocks save/submit with row-level APP linkage error.

## Scenario 3: Exceed APP remaining balance (negative)
1. Create APP-linked line amount greater than remaining APP balance.
Expected:
- Validation blocks with explicit balance exceed error.

## Scenario 4: Approval creates commitments (positive)
1. Progress PR status through workflow to `Approved`.
2. Verify:
   - `Purchase Requisition Commitment` records exist for the PR,
   - PR `budget_status = Committed`,
   - PR `tender_readiness_status = Ready for Tender`,
   - linked APP line `committed_amount` increased and line budget status updated.

## Scenario 5: Cancellation releases commitments (positive)
1. Move approved PR to `Cancelled`.
2. Verify commitment record status updates to `Released` with release metadata.

## Scenario 6: Amendment evidence (positive)
1. Submit a `Purchase Requisition Amendment` for an approved PR.
Expected:
- `Purchase Requisition Snapshot` entry created with `snapshot_type = Amendment Approval`.

## Execution evidence (2026-03-20 baseline)
- Existing approved requisition `PR-.#####` was processed through Phase 1.5 commitment path.
- Observed:
  - `Purchase Requisition Commitment` count = 1 for requisition,
  - `Purchase Requisition Snapshot` count = 1,
  - requisition `budget_status = Committed`,
  - requisition `tender_readiness_status = Ready for Tender`,
  - requisition `total_committed_amount = 1000.0`.

## Execution evidence (2026-03-20 fresh full-run)
- Requisition created: `PR-2026-00050` (autoname fixed to `PR-{YYYY}-{#####}`).
- Workflow path executed:
  - `Submit -> Route to HoD -> Approve HoD -> Approve Finance -> Approve AO -> Approve Final`.
- Final observed state:
  - `status = Approved`
  - `budget_status = Committed`
  - `tender_readiness_status = Ready for Tender`
  - `total_estimated_cost = 750.0`
  - `total_committed_amount = 750.0`
  - `approved_on` populated
- Evidence artifacts:
  - `Purchase Requisition Commitment`: `PRC-2026-00051` (`committed_amount = 750.0`, `status = Active`)
  - `Purchase Requisition Snapshot`: `PRS-2026-00052` (`snapshot_type = Approval`)

Refactor correction captured:
- `Purchase Requisition.status` options expanded to include Phase 1.5 workflow states
  (`HoD Review`, `Finance Review`, `AO Review`, `Procurement Review`, etc.).

## Execution evidence (2026-03-20 handoff integration run)
- Controlled handoff API executed:
  - `phase15_handoff_requisition_to_tender('PR-2026-00050', 1, 'UAT handoff integration run')`
- Result:
  - `created_tenders = ['TN-2026-00053']`
  - `reused_tenders = []`
  - `handoff = 'RTH-2026-00054'`
  - `linked_tender_count = 1`
  - `tender_readiness_status = Fully Handed Off`
- Record verification:
  - PR `PR-2026-00050`: `status = Approved`, `linked_tender_count = 1`, `tender_readiness_status = Fully Handed Off`
  - Handoff `RTH-2026-00054`: `handoff_status = Tender Created`, `tender_reference = TN-2026-00053`
  - Tender `TN-2026-00053`: `status = Published`, `procurement_plan_item = PPI-2026-00010`
- Idempotency check:
  - Re-running handoff on same PR created no duplicate tender and reused `TN-2026-00053`.
