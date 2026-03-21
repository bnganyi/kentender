# Phase 2 Technical Reference - Supplier Registration and Full Tendering Lifecycle

## Scope Delivered

This implementation introduces the market-facing control layer after approved demand:

- Supplier registration and supplier master governance.
- Tender structuring and publication controls.
- Submission hard lock and sealed baseline fields.
- Opening, evaluation, award, challenge, and handoff records.
- Phase 2 workflow orchestration and daily controls.
- Desk-native `Phase 2 Hub` workspace and sidebar navigation.

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

## UI Layer

- Workspace: `kentender/kentender/kentender/workspace/phase_2_hub/phase_2_hub.json`
- Sidebar: `kentender/workspace_sidebar/phase_2_hub.json`

The hub mirrors the operational sequence:
Supplier governance -> Tender lifecycle -> Submission/opening/evaluation/award.

### Phase 2 Hub links (Desk routing)

Custom DocTypes linked as `DocType` from Workspace often fail to open the list from the sidebar. Hub links use **`link_type: Page`** pointing at thin **Page** stubs that run `frappe.set_route("List", "<DocType>", "List")` (same approach as Phase 1 Hub). After migrate, `phase2_sync_phase_2_hub_navigation()` reapplies sidebar/workspace JSON to the live DB so links stay in sync.

### Where Page stubs must live (read this before adding links)

The KenTender app’s **module package is nested**: working Desk pages live under **`kentender/kentender/kentender/page/`** (three `kentender` path segments), **not** `kentender/kentender/page/`. Phase 1 stubs (`purchase_requisition_commitment`, `tender`, etc.) are already there. If Phase 2 stubs are missing from that folder, sidebar links will 404 with `FileNotFoundError` even though JSON was edited.

**Convention (match Phase 1 Hub):**

| Piece | Example |
|-------|---------|
| Directory + `.js` / `.json` basename | `tender_document_version` (underscores) |
| `Page` JSON `name` / `page_name` + `link_to` + `frappe.pages[...]` key | `tender-document-version` (hyphens) |

Commit new `page/<folder>/` directories to git—empty folders are not tracked; without the files on disk, every bench clone breaks again.

## Validation Evidence (fresh run)

Reference run IDs (2026-03-21):

- `SRA-2026-00057` -> `SUPM-2026-00058`
- `TN-2026-00059` -> `TS-2026-00061`
- `EVD-2026-00062` + `EVW-2026-00063`
- `AR-2026-00064` -> `AD-2026-00065`
- Challenge hold: `CRC-2026-00066`
- Handoff + PO lineage: `ACH-2026-00067`, `PUR-ORD-2026-00013`
