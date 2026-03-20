# KenTender Phase 1 Coverage Checkpoint Matrix

Date: 2026-03-20

## Terminology conventions
- `APP` = Annual Procurement Plan (`Procurement Plan` and `Procurement Plan Item`).
- `Purchase Requisition (PR)` = pre-tender demand-finalization record.
- Use `PR` after first explicit expansion.

## Coverage Legend
- **Covered**: Implemented and enforceable in current code.
- **Partial**: Basic implementation exists, but workflow depth/integration/automation is incomplete.
- **Gap**: Not implemented yet in codebase.

## Requirement-to-Implementation Matrix (checkpoint view)
This is a condensed “what we have right now” view. We fill it as we rewrite Phase 1.

| Phase 1 Area | Status | Current Implementation | Main Gaps / Improvement Target |
|---|---|---|---|
| Strategic alignment enforcement | **Partial** | Plan-item approval gate enforces `strategic_objective` and required/derived `national_priority` in `kentender/kentender/api.py` | Add stricter APP header strategic linkage checks and cross-plan consistency controls |
| APP workflow controls | **Covered** | Active `Procurement Plan Workflow` + server controls (`phase1_procurement_plan_*` hooks, status transition map, controlled transition API) | Improve UX guardrails to route all status moves through one canonical action path |
| Plan item approval matrix + controlled progression | **Covered** | `generate_approval_chain`, `validate_plan_item`, `approve_plan_item`, `reject_plan_item` enforce matrix-driven progression | Expand UAT for role segregation edge cases and matrix overlap handling |
| Budget discipline and commitment statuses | **Partial** | Phase 1.5 Purchase Requisition (PR)-centric controls now active (`Purchase Requisition Commitment`, PR approval commitment creation, APP line committed rollup) | Full release/consumption lifecycle orchestration and deep budget/GL service integration pending |
| Threshold/method advisory + anti-split | **Covered** | Recommendation + ambiguity hard-stop + allowed-method enforcement (`_phase1_find_matching_threshold_rule` / `_phase1_recommend_procurement_method_for_item`), non-competitive justification gate, anti-split risk scoring, deduplicated override evidence upsert | Complete seeded negative UAT for overlapping rules and disallowed method attempts |
| Locking/publication/snapshots/versioning | **Covered** | `Published Plan Record` snapshot at publish, lock metadata (`locked_on`, `locked_by`), lock immutability, and revision publish orchestration (`phase1_publish_procurement_plan_revision`) with parent supersede side effects | Replace placeholder export attachments with generated signed publication bundles |
| Requisition handoff gates | **Covered** | `phase15_handoff_requisition_to_tender` performs controlled PR handoff, creates/reuses `Tender`, upserts `Requisition Tender Handoff`, and updates PR readiness counters/status | Add richer handoff package export + multi-stage tender packet generation |
| Reporting/dashboards for APP lifecycle | **Partial** | `phase1_get_reporting_snapshot` provides API-ready APP/PR/handoff aggregates; `phase1_download_reporting_snapshot_csv` provides handoff evidence CSV export | Add Desk dashboard/report UI and scheduled packaged distribution |
| Audit evidence chain | **Partial** | `KenTender Audit Event` logging/export and Phase 1 reporting CSV exports provide baseline evidence extraction | Add APP-focused multi-section audit package and signed evidence bundles |

## Documentation for users/developers
- Technical reference: `docs/Phase 1 Technical Reference Index.md`
- UAT index: `docs/Phase 1 UAT Script.md`

## Latest checkpoint (2026-03-20)
- Header governance validated end-to-end on test APP `PP-2026-00047`:
  - `Draft -> Department Consolidation -> Procurement Review -> Finance Review -> Submitted -> Approved -> Published -> Locked`.
- Runtime correction made during validation:
  - `Procurement Plan.status` set to `allow_on_submit = 1` to allow valid post-submit workflow transitions.
- Control evidence confirmed:
  - publish side effects (`published_date`, snapshot creation) and lock side effects (`locked_on`, `locked_by`) working;
  - negative checks passed (locked edit blocked, backward transition from `Locked` blocked).
- Phase 1.5 checkpoint added:
  - Purchase Requisition (PR) full-treatment model and workflow activated.
  - Budgeting dependency refactored from header-only PR linkage to PR line/module controls.
- Fresh Purchase Requisition (PR) evidence run completed:
  - `PR-2026-00050` reached `Approved` through full route.
  - `PRC-2026-00051` and `PRS-2026-00052` created.
  - PR finalized as `Committed` and `Ready for Tender`.
- Runtime compatibility corrections captured:
  - PR naming corrected to `PR-{YYYY}-{#####}`.
  - PR status option set aligned with Phase 1.5 workflow states.
- Threshold/method hardening checkpoint:
  - Ambiguity and allowed-method threshold guards implemented.
  - Non-competitive method justification enforced by policy profile flag.
  - Anti-split risk scoring and deduplicated override evidence capture implemented.
  - Smoke evidence captured in `phase1-uat-01` Scenario 9.
- Revision/supplementary orchestration checkpoint:
  - Added APP workflow supersede transitions from `Approved`/`Published`/`Locked`.
  - Added controlled revision publish service with parent supersede side effects.
  - Validated with revision `p6cdnlu4id` and parent APP `PP-2026-00047`.
- PR handoff integration checkpoint:
  - Handoff service validated on PR `PR-2026-00050`.
  - Created handoff `RTH-2026-00054` and tender `TN-2026-00053`.
  - Idempotency verified (re-run reused existing tender, no duplicate creation).
- Reporting/export checkpoint:
  - Snapshot API validated on scope `Midas (Demo)` / `2025-2026`.
  - Handoff evidence row returned for `RTH-2026-00054` -> `TN-2026-00053`.
  - CSV export generation smoke test passed.

