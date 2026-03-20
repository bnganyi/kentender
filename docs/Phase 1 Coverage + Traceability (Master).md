# KenTender Phase 1 Coverage + Traceability (Master)

Date: 2026-03-20

Scope (initial):
- `docs/requirements/Phase 1 - Procurement Planning and Budgeting Design.md`
- `docs/requirements/Ken Tender eProcurement System Architecture.md`
- current Phase 1 implementation evidence in `doctype/*.json`, `hooks.py`, and `kentender/api.py`

## Documentation for users/developers
- Technical reference (module-focused): `docs/Phase 1 Technical Reference Index.md`
- UAT index: `docs/Phase 1 UAT Script.md`

## Terminology conventions
- `APP` = Annual Procurement Plan (`Procurement Plan` and `Procurement Plan Item`).
- `Purchase Requisition (PR)` = pre-tender demand-finalization record.
- Use `PR` after first explicit expansion.

## Coverage Legend
- **Covered**: Implemented and enforceable in current code.
- **Partial**: Basic implementation exists, but workflow depth/integration/automation is incomplete.
- **Gap**: Not implemented yet in codebase.

## Requirement-to-Implementation Matrix (current baseline)
This table reflects the current validated implementation baseline and will be updated as Phase 1 deepens.

| Phase 1 Area | Status | Current Implementation Evidence | Main Gaps / Improvement Target |
|---|---|---|---|
| Strategic alignment enforcement | **Partial** | Enforced at plan-item approval gate in `_phase1_validate_item_before_first_approval` (`kentender/kentender/api.py`) via `strategic_objective` + derived/required `national_priority` | Add stricter header-level strategy references and cross-plan consistency checks |
| APP header governance (versioning, approval, locking) | **Covered** | `Procurement Plan` hooks wired in `kentender/hooks.py`: `phase1_procurement_plan_before_insert`, `phase1_procurement_plan_validate`, `phase1_procurement_plan_on_submit`, `phase1_procurement_plan_on_update_after_submit`; transition map + controlled API `phase1_transition_procurement_plan_status` | Optional: centralize all status moves through a single whitelisted service and UI action wrappers |
| Plan item governance + approval chain | **Covered** | `validate_plan_item`, `generate_approval_chain`, `approve_plan_item`, `reject_plan_item` in `kentender/kentender/api.py`; controlled status hardening + matrix-driven level approvals | Expand role segregation test coverage and edge-case matrix conflicts |
| Budget lifecycle + commitment reservation | **Partial** | Refactored through Phase 1.5 Purchase Requisition (PR) controls: `phase1_validate_purchase_requisition`, `phase1_on_update_purchase_requisition`, `Purchase Requisition Commitment`, `Purchase Requisition Snapshot`; linked APP line commitment updates + parent APP total rollup | Commitment release/consumption rules and deep ERPNext budget/GL integration still need hardening |
| Threshold/method advisory engine + anti-split | **Covered** | `_phase1_recommend_procurement_method_for_item` + `_phase1_find_matching_threshold_rule` enforce recommendation, ambiguity hard-stop, and allowed-method validation; non-competitive justification gate + anti-split risk scoring + deduplicated override evidence (`_phase1_upsert_budget_override_record`) | Seed and run full negative UAT with overlapping threshold rules and disallowed method selections |
| Supplementary/revision flow after lock | **Covered** | `Procurement Plan Revision` governance wired with `phase1_procurement_plan_revision_validate`, `phase1_publish_procurement_plan_revision`, and `_phase1_apply_revision_publish_side_effects`; workflow now includes `Supersede` transitions from `Approved`/`Published`/`Locked` APP states | Deepen to full revised-APP artifact generation and side-by-side change-pack exports |
| Publication snapshots + audit packs | **Covered** | `_phase1_create_published_snapshot` creates `Published Plan Record` with hash and metadata during `Published` transition | Replace placeholder attachment handling with generated signed exports |
| Requisition handoff gates | **Covered** | Controlled handoff service `phase15_handoff_requisition_to_tender` now creates/reuses `Tender` records from approved PR lines, upserts `Requisition Tender Handoff`, updates PR handoff counters/readiness, and writes audit events | Extend to multi-stage tender package generation and richer handoff packet exports |
| Reporting/dashboards for APP/budget lifecycle | **Partial** | `phase1_get_reporting_snapshot` provides APP, plan-item, override, PR readiness, and handoff aggregates for API-driven dashboards | Add Desk-native charts/report pages and scheduled report packaging |
| Auditability and evidence exports | **Partial** | `KenTender Audit Event` exports + `phase1_download_reporting_snapshot_csv` provide baseline evidence extraction for handoff/reporting flows | Extend to multi-section APP evidence bundle with signed export packaging |

## Reconciliation Note
When the user-provided traceability matrix differs from current code evidence, record the reconciliation signal and the consolidated status here.

## Latest Validation Checkpoint (2026-03-20)
- UAT execution record updated in: `docs/uat/phase1-uat-01-app-and-plan-item-governance.md`.
- Header governance flow validated end-to-end on `PP-2026-00047`:
  - `Draft -> Department Consolidation -> Procurement Review -> Finance Review -> Submitted -> Approved -> Published -> Locked`.
- Runtime fix captured during validation:
  - `Procurement Plan.status` updated with `allow_on_submit = 1` to permit valid post-submit workflow transitions.
- Controls confirmed:
  - Publish side effects (`published_date`, snapshot creation) and lock side effects (`locked_on`, `locked_by`) are working.
  - Negative checks pass: locked-field edit blocked; invalid `Locked -> Published` transition blocked.
- Phase 1.5 incorporation completed:
  - Purchase Requisition (PR) full-treatment model introduced (items, approvals, commitments, exceptions, amendments, snapshots, handoff scaffolds).
  - Budget lifecycle logic refactored to PR-centric commitment creation and APP line rollup updates.
- Fresh UAT evidence completed after Phase 1.5 refactor:
  - Purchase Requisition (PR) `PR-2026-00050` progressed through full workflow to `Approved`.
  - Commitment `PRC-2026-00051` and snapshot `PRS-2026-00052` created.
  - PR ended `Committed` and `Ready for Tender` with committed total rollup.
- Supporting refactor correction:
  - `Purchase Requisition` autoname corrected to `PR-{YYYY}-{#####}`.
  - `Purchase Requisition.status` options aligned with Phase 1.5 workflow states.
- Threshold/method + anti-split hardening checkpoint:
  - Added threshold ambiguity detection and allowed-method enforcement.
  - Added non-competitive method justification gate from active policy profile.
  - Added anti-split risk scoring (`risk_score`, `risk_level`) and deduplicated override evidence upsert.
  - Smoke validation evidence captured in `docs/uat/phase1-uat-01-app-and-plan-item-governance.md` (Scenario 9).
- Revision/supplementary orchestration checkpoint:
  - Added controlled revision publish service and revision governance validation hooks.
  - Added APP workflow `Supersede` transitions from `Approved`, `Published`, and `Locked`.
  - Validated on revision `p6cdnlu4id`: parent APP `PP-2026-00047` moved to `Superseded` after publish.
- PR handoff-to-tender integration checkpoint:
  - Added controlled service `phase15_handoff_requisition_to_tender`.
  - Validated on `PR-2026-00050` with evidence records:
    - Handoff `RTH-2026-00054`
    - Tender `TN-2026-00053`
  - Confirmed idempotent rerun reuses existing tender without duplicates.
- Reporting/evidence export checkpoint:
  - Added `phase1_get_reporting_snapshot` and `phase1_download_reporting_snapshot_csv`.
  - Validated scoped reporting snapshot for `Midas (Demo)` / `2025-2026`.
  - Confirmed non-empty CSV export generation for handoff evidence rows.

