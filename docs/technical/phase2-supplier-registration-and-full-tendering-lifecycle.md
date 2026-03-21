# Phase 2 Technical Reference - Supplier Registration and Full Tendering Lifecycle

## Scope Delivered

This implementation introduces the market-facing control layer after approved demand:

- Supplier registration and supplier master governance.
- Tender structuring and publication controls.
- Submission hard lock and sealed baseline fields.
- Opening, evaluation, award, challenge, and handoff records.
- Phase 2 workflow orchestration and daily controls.

## Core Artifacts Added

- Supplier governance DocTypes:
  - `Supplier Registration Application`
  - `Supplier Master`
  - `Supplier Category Registration`
  - `Supplier Compliance Document`
  - `Supplier Status Action`
  - `Suspension Debarment Register`
- Tender lifecycle DocTypes:
  - `Tender Lot`
  - `Tender Document Pack`
  - `Tender Document Version`
  - `Tender Clarification`
  - `Tender Addendum`
  - `Tender Publication Record`
- Submission/evaluation/award DocTypes:
  - `Bid Opening Record`
  - `Evaluation Committee`
  - `Evaluator Declaration`
  - `Evaluation Worksheet`
  - `Evaluation Consensus Record`
  - `Award Recommendation`
  - `Award Decision`
  - `Tender Notification Log`
  - `Challenge Review Case`
  - `Award Contract Handoff`

## Key Server Controls

Implemented in `kentender/kentender/api.py` and wired in `kentender/hooks.py`:

- `phase2_validate_supplier_registration_application`
- `phase2_sync_supplier_master_from_application`
- `phase2_validate_supplier_master`
- `phase2_apply_supplier_status_action`
- `validate_tender` (Phase 2 publication/readiness hardening)
- `validate_submission` (supplier status + lifecycle fields hardening)
- `phase2_validate_evaluation_worksheet`
- `phase2_validate_award_decision`
- `phase2_on_update_award_decision`
- `phase2_flag_expired_supplier_documents`
- `phase2_auto_close_due_tenders`
- `phase2_notify_challenge_window_expiry`
- `phase2_setup_workflows`

## Workflow Baseline

Provisioned through `phase2_setup_workflows()`:

- `Supplier Registration Workflow`
- `Tender Workflow`

These are applied during `phase1_after_migrate_setup()` when Phase 2 DocTypes are present.

## Desk navigation (UX)

Phase / CLM **Workspace**, **Workspace Sidebar**, **Page list-redirect stubs**, and the interim **CLM Hub** report were **removed** from the app so navigation can be reintroduced from a clean UX design. DocTypes, workflows, and server logic are unchanged; use **Awesome Bar**, **Role Permissions Manager**, and standard **Workspace** tooling (or new design) to expose menus.

## Validation Evidence (fresh run)

Reference run IDs (2026-03-21):

- `SRA-2026-00057` -> `SUPM-2026-00058`
- `TN-2026-00059` -> `TS-2026-00061`
- `EVD-2026-00062` + `EVW-2026-00063`
- `AR-2026-00064` -> `AD-2026-00065`
- Challenge hold: `CRC-2026-00066`
- Handoff + PO lineage: `ACH-2026-00067`, `PUR-ORD-2026-00013`
