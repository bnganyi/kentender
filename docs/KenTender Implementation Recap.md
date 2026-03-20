# KenTender Implementation Recap (Pre-CLM)

## 1) Objective and implementation approach

This document summarizes the system built so far before starting Contract Lifecycle Management (CLM).

The build has followed a code-first, test-as-we-go approach with three guiding principles:

- Keep the MVP ERPNext-native (reuse core `Company`, `Supplier`, `Item`, `Purchase Order`)
- Enforce governance and compliance in server-side code (not UI-only logic)
- Validate each discrete function with bench/UI checks before moving to the next phase


## 2) Final architecture choices made

### Multi-tenant model

- We intentionally **did not** keep a custom `Organization` DocType.
- Tenant isolation and ownership rely on ERPNext core `Company`.

### System style

- Lean, role-based public procurement flow
- Custom business rules in `kentender/kentender/kentender/api.py`
- Frappe DocType + hook-driven lifecycle validations


## 3) Core DocTypes implemented

### 3.1 Planning and tendering

- `Procurement Plan`
- `Procurement Plan Item` (submittable)
- `Tender`
- `Tender Submission`

### 3.2 Approval and evaluation

- `Approval Matrix`
- `Plan Item Approval` (child table)
- `Evaluation Criteria`
- `Submission Scores` (child table)

### 3.3 Compliance

- `Supplier Compliance Profile`
- `Compliance Requirement`
- `Supplier Compliance Record`


## 4) Key server logic implemented

Main file: `apps/kentender/kentender/kentender/api.py`

### 4.1 Approval engine

- Dynamic approval chain generation from `Approval Matrix`
- Level-based approval progression in `approve_plan_item()`
- Rejection flow in `reject_plan_item(docname, reason)` with mandatory reason
- Controlled admin override in `override_plan_item_status(docname, status, reason)` (System Manager only)

### 4.2 Tender submission and validation

- `validate_submission()` enforces:
  - Tender must be `Published`
  - Deadline not passed
  - Supplier compliance must be `Verified`
  - Exchange/base amount calculation

### 4.3 Evaluation and award

- Weighted scoring with `calculate_total_score()` and `Evaluation Criteria.weight`
- Winner selection in `_select_winning_submission()` with ranking/tie logic
- Compliance hardening in winner selection (non-verified suppliers excluded)
- `award_tender()` creates/submits ERPNext `Purchase Order` and logs award comment

### 4.4 Compliance engine

- `run_check(supplier)` evaluates `Compliance Requirement` records
- Mandatory requirement outcomes determine overall profile status:
  - `Verified`, `Partially Verified`, `Pending`, `Rejected`
- Updates per-requirement records in `Supplier Compliance Record`

### 4.5 Governance hardening

- Manual status change guard in `validate_plan_item()`
- Audit comments for critical operations (approval/rejection/override/award)
- Controlled methods use override flags and after-submit bypass only where required
- `allow_on_submit` tightened for `Procurement Plan Item.status` and `approvals`


## 5) Hooks and scheduled behavior

Current hook definitions in `apps/kentender/kentender/hooks.py`:

- `Procurement Plan Item.validate` -> `validate_plan_item`
- `Tender Submission.validate` -> `validate_submission`
- `Tender.on_submit` -> `validate_tender`
- Daily scheduler -> `recheck_supplier_compliance`


## 6) Major issues encountered and resolved

### 6.1 Warehouse/Purchase Order failures

- Resolved stock-item warehouse validation during `award_tender()`
- Added warehouse resolution logic (`Item Default` / company warehouse fallback)

### 6.2 Missing submit action / workflow interference

- Ensured `Procurement Plan Item` is submittable with required permissions
- Addressed conflicts from legacy workflows overriding submit behavior

### 6.3 List view/form mismatch

- Normalized list metadata and field display behavior
- Cleared cache and removed stale metadata overrides when needed

### 6.4 Permissions/ownership instability in WSL

- Frequent `Permission denied` issues due to mixed ownership (`midasuser` vs `bonface`)
- Established repeated operational fixes for:
  - app files
  - `sites/<site>/locks`
  - bench/site log directories

### 6.5 Governance loophole found during testing

- User demonstrated manual status edit on submitted plan item
- Root cause: `allow_on_submit` enabled on `status` and `approvals`
- Mitigation applied:
  - Set `allow_on_submit = 0` for both fields
  - Kept controlled update paths functional through explicit override flags/bypass


## 7) Test coverage done so far

The following tests were executed during implementation:

### 7.1 Approval chain and flow

- Approval rows generated for submitted plan items based on matrix
- Multi-level approval behavior verified in live data
- Controlled approve/reject transitions tested via whitelisted methods

### 7.2 Tender submission gating

- Submission blocked when supplier compliance is not `Verified`
- Improved error message now includes supplier and current compliance status

### 7.3 Compliance status calculation

- Requirement-level outcomes persisted in `Supplier Compliance Record`
- Overall status written to `Supplier Compliance Profile`

### 7.4 Evaluation + winner selection

- Weighted score calculation validated
- Award path tested with score-based winner selection
- Non-compliant supplier exclusion from winner selection validated

### 7.5 Governance checks

- Manual post-submit status update now blocked by Frappe core + governance settings
- Controlled method path remains functional


## 8) Test utilities added for reproducible checks

In `api.py`:

- `test_create_tender_submission(...)`
- `try_create_tender_submission(...)` -> structured `{ok, name/error}`
- `try_set_plan_item_status(...)` -> structured governance test helper

These helpers are intentionally lightweight and can be kept for QA/smoke testing.


## 9) Test checklist required before CLM

Run this as a formal pre-CLM gate:

- [ ] Attempt manual status edit on submitted `Procurement Plan Item` from UI -> must fail
- [ ] Approve pending plan item through controlled method/UI action -> must succeed + audit comment
- [ ] Reject pending plan item with empty reason -> must fail
- [ ] Reject with reason -> must succeed + audit comment
- [ ] Override as non-System Manager -> must fail
- [ ] Override as System Manager with reason -> must succeed + audit comment
- [ ] Create `Tender Submission` with non-verified supplier -> blocked with clear message
- [ ] Create submission with verified supplier -> succeeds
- [ ] Run `run_check()` and confirm requirement + profile statuses update
- [ ] Award tender with at least one non-compliant supplier in pool -> non-compliant supplier must not win


## 10) Operational notes

- Cache refresh is critical after metadata/security changes:
  - `bench --site kentender.midas.com clear-cache`
- Permission ownership still requires discipline in this environment.
- Prefer shared-group write strategy for log dirs to avoid repeated user ownership flips.


## 11) Current readiness status (before CLM)

The procurement foundation is now in place and materially hardened:

- Dynamic approvals
- Compliance-enforced submission gate
- Evaluation-driven awarding
- Governance controls and audit traces

System is ready to proceed into **Contract Lifecycle Management** after completing the pre-CLM checklist above in one clean pass and recording results.

## 12) CLM Progress Update (Iterations 1-6)

CLM has now been implemented iteratively from foundation to reporting/governance:

- **Iteration 1:** Contract master record + award-to-contract + dual-signature activation + project auto-link
- **Iteration 2:** Acceptance Certificate + core ERPNext custom field links + invoice certificate gate
- **Iteration 3:** Task milestone guardrails + CIT membership validation + retention ledger posting
- **Iteration 4:** Inspection committee + variation/claim/dispute foundation + variation application behavior
- **Iteration 5:** Termination record + DLP lifecycle + close-out enforcement guards
- **Iteration 6:** Monthly monitoring report generation + close-out readiness API + CLM dashboard summary API

### Current CLM baseline in place

- Contract governance and legal lifecycle backbone
- Operational execution tied to ERPNext-native objects (`Project`, `Task`, `Purchase Invoice`, `Payment Entry`)
- Financial controls (certificate gating + retention tracking)
- Legal/compliance controls (claims, disputes, termination, DLP)
- Monitoring/reporting APIs and monthly report generation

### UAT artifact

A formal end-to-end CLM UAT script has been prepared at:

- `apps/kentender/CLM UAT Script.md`

Use this script as the primary pilot validation checklist before production hardening.

