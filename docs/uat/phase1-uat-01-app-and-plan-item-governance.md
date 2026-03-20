# Phase 1 UAT-01: APP and Plan Item Governance

## Scope
Validate that Phase 1 enforces:
- required governance fields on APP header and APP line items,
- strategic alignment constraints,
- approval matrix chain generation and controlled approval progression,
- and immutability after lock/publish boundaries (once implemented).

## Preconditions
1. `kentender.midas.com` site is migrated and cache cleared.
2. Required policy/reference masters are created:
   - `Procurement Policy Profile` (Active)
   - `Approval Matrix Rule` rows covering the selected `company` and `estimated_budget` band
   - `Procurement Threshold Rule` rows needed for procurement method recommendation
3. Strategic objective hierarchy exists:
   - `National Development Plan`
   - `Strategic Objective` (at least one) linked to the required hierarchy
4. Roles:
   - user with permission to create APP and plan items (e.g., `Procurement User`)
   - role(s) included in approval matrix (e.g., `Accounting Officer`, `Procurement Manager`)

## Test Scenarios
### 1. APP Draft validation (negative)
1. Create a `Procurement Plan` record with missing required fields (use placeholders from your updated requirements).
Expected:
- Validation throws a clear “missing required field” error.

### 2. APP line creation (negative)
1. Create a `Procurement Plan Item` referencing a non-approved APP header (or missing strategic objective references).
Expected:
- Validation blocks approval transitions and/or submit progression depending on the final workflow.

### 3. Plan Item approval chain progression (positive)
1. Create a valid APP and APP item with:
   - required strategic references
   - required budget/estimated_cost reference fields
2. Transition plan item status to the state that triggers approval chain generation (per final workflow).
3. Call the whitelisted approval API (or perform workflow transition) step-by-step as roles change.
Expected:
- `approvals` table populates deterministically from the `Approval Matrix Rule`.
- Status moves forward only when the correct approver role approves each level.

### 4. Manual status mutation hardening (negative)
1. Attempt to directly set plan item `status` to an approved state without the approved levels completed (using UI or API).
Expected:
- Validation blocks manual status change unless the action is performed through the controlled API/flag path.

## Verification (optional)
Add SQL checks once your updated requirements finalize:
- counts of approval rows by level
- plan totals after line states change
- presence of audit events / audit packs

## Execution Evidence (2026-03-20)
Environment:
- Site: `kentender.midas.com`
- User context: `Administrator` (System Admin validation as requested)
- Policy profile used: `2h5tpnm8n6` (Active; entity `Midas (Demo)`, FY `2025-2026`)

### Scenario 5. APP header governance full path (positive)
Record used:
- `Procurement Plan`: `PP-2026-00047`
- Type: `Supplementary` (used to avoid single-active-original annual APP conflict)

Workflow actions executed:
1. `Consolidate` (`Draft -> Department Consolidation`)
2. `Send to Procurement Review`
3. `Send to Finance`
4. `Submit for Approval`
5. `Approve`
6. `Publish`
7. `Lock`

Expected and observed:
- All transitions executed successfully in sequence.
- `status` reached `Locked`.
- `published_date` auto-populated at publish.
- `locked_on` and `locked_by` auto-populated at lock.
- `Published Plan Record` snapshot count for `PP-2026-00047` = `1`.

### Scenario 6. APP header post-submit transition hardening (fix validation)
Issue encountered during UAT run:
- Transition `Approved -> Published` failed initially with `UpdateAfterSubmitError` because field `status` was not allowed on submitted docs.

Fix applied:
- `Procurement Plan.status` updated with `allow_on_submit = 1`.
- Site migrated and cache cleared.

Re-test result:
- `Approved -> Published -> Locked` completed successfully after fix.

### Scenario 7. Locked APP immutability (negative)
Action:
- Attempted to edit `budget_reference` on locked plan `PP-2026-00047`.

Expected and observed:
- Change blocked with `UpdateAfterSubmitError`.
- Confirms immutability boundary after lock for core APP header fields.

### Scenario 8. Invalid backward transition after lock (negative)
Action:
- Attempted controlled API transition `Locked -> Published`.

Expected and observed:
- Blocked by server transition guard.
- Error: `Invalid Procurement Plan status transition: Locked -> Published`.

### Scenario 9. Threshold/method hardening smoke validation (technical-positive)
Actions:
1. Executed in-memory validator smoke run for `_phase1_validate_item_before_first_approval` using APP-linked test payload.
2. Verified deduplicated override evidence behavior by calling `_phase1_upsert_budget_override_record` twice for same item and override type.

Observed:
- Validator output returned governance fields without error:
  - `system_recommended_method = RFQ`
  - `budget_status = Available`
  - `risk_score = 20`
  - `risk_level = Low`
- Override dedupe check result:
  - `Budget Override Record` draft count for (`Procurement Plan Item` = `PPI-2026-00008`, `override_type` = `Method`) remained `1` after two upsert calls.

Note:
- No active `Procurement Threshold Rule` rows were present in this site run, so ambiguity and allowed-method negative-path assertions remain pending in the next seeded-rule UAT cycle.

### Scenario 10. Revision publish orchestration and parent supersede (positive)
Actions:
1. Created `Procurement Plan Revision` `p6cdnlu4id` for parent APP `PP-2026-00047` (`revision_type = Supplementary`).
2. Moved revision to `Under Review` using workflow action `Submit Revision`.
3. Executed controlled publish service `phase1_publish_procurement_plan_revision`.
4. Refreshed workflows using `phase1_setup_procurement_plan_workflows` to include explicit `Supersede` actions from `Approved`/`Published`/`Locked`.

Observed:
- Revision final `status = Published`.
- Parent APP `PP-2026-00047` transitioned from `Locked` to `Superseded`.
- Revision approval metadata stamped:
  - `approved_by = Administrator`
  - `approved_on` populated.

Result:
- Revision publication sequencing now enforces controlled parent supersede orchestration instead of manual post-publish cleanup.

### Scenario 11. Reporting snapshot + CSV export smoke validation (positive)
Actions:
1. Executed `phase1_get_reporting_snapshot('Midas (Demo)', '2025-2026')`.
2. Executed `phase1_download_reporting_snapshot_csv('Midas (Demo)', '2025-2026')`.

Observed:
- Snapshot returned aggregate APP/plan-item/override/PR/handoff metrics.
- Returned handoff row included:
  - `RTH-2026-00054`
  - `purchase_requisition = PR-2026-00050`
  - `tender_reference = TN-2026-00053`
- CSV export response generated non-empty content (smoke length check passed).

Result:
- Phase 1 reporting and export APIs are operational for baseline dashboard/evidence extraction flows.

