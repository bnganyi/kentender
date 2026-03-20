# KenTender CLM Coverage Checkpoint Matrix

Date: 2026-03-18  
Scope reviewed against:
- `clm-inputs/Ken Tender — Phase 2 Contract Management Requirements.md`
- `clm-inputs/KenTender CLM Design.md`
- `clm-inputs/CLM REQUIREMENTS TRACEABILITY MATRIX.md`
- current implementation (`doctype/*.json`, `hooks.py`, `api.py`)

## Documentation for users/developers
- UI-based user guide: `docs/CLM UI User Guide.md`
- Technical-operator guide: `docs/CLM User Guide.md`
- Technical reference (module-focused): `docs/CLM Technical Reference Index.md`

## Coverage Legend

- **Covered**: Implemented and enforceable in current code.
- **Partial**: Basic implementation exists, but workflow depth/integration/automation is incomplete.
- **Gap**: Not implemented yet in codebase.

## Requirement-to-Implementation Matrix

| FRS Area | Status | Current Implementation | Main Gaps / Improvement Target |
|---|---|---|---|
| 4.1 Contract preparation | Partial | `create_contract_from_award()` auto-populates contract core fields from award/submission. | Attachments/version control/template generation not yet enforced as controlled workflow. |
| 4.2 Contract execution and signing | Partial | `sign_contract` / `activate_contract`; **External Verified** + conf verifier + cert/ref metadata; **strict** disables fallback. | Tenant-specific e-sign provider wiring and end-user signing UX. |
| 4.3 CIT appointment | Partial | CIT member doctype + **Proposed → Approved (AO) → Active (HoP)** + `transition_cit_member` + audit. | Formal “recommendation” DocType / multi-step routing optional. |
| 4.4 Implementation activities (works/goods) | Partial | Milestone model on ERPNext `Task` + project integration at activation. | Site handover, meeting minutes, delivery logs are not modeled as first-class controlled records. |
| 4.5 Milestone monitoring | Covered (Wave-1 level) | `Task` custom fields + validations; **baseline milestone seeding** on first **Active** transition (`Contract` `on_update` → `_seed_contract_milestone_tasks`). | No SLA/escalation automation or milestone delay alerts yet. |
| 4.6 Inspection committee | Partial | ICM doctype + **Proposed → Approved (AO) → Active (HoP)** + dissolve path + `transition_inspection_committee_member` + audit. | Separate recommendation record optional. |
| 4.7 Inspection testing | Partial | `Inspection Test Plan` + `Inspection Report` + AC linkage; milestone→draft ITP; ERPNext **Quality Inspection** remains execution record. | Auto **QI** from milestone optional; committee appointment now status-governed (ICM). |
| 4.8 Certification | Covered (governed) | `Acceptance Certificate` doctype + workflow-state hardening + role-gated transitions (`transition_acceptance_certificate`). | Certificate subtype-specific rules can be deepened (e.g., stricter FAC-only closeout path checks by role). |
| 4.9 Invoice submission | Covered (gated) | Contract-linked invoice validation via `validate_purchase_invoice_certificate()`. | Supporting-doc checklist and tax breakdown quality checks not yet formalized. |
| 4.10 Payment processing | Partial (ERPNext-first) | `Payment Entry` CLM fields + `transition_payment_entry_clm`; `before_submit` requires full certification + PI references; PI/contract/supplier alignment checks; timestamps + `get_contract_payment_governance_chain`; dashboard finance counters. | Deeper ERPNext Workflow UI / printed payment register templates optional. |
| 4.11 Statutory compliance | Gap | No tax-register/treasury integration code in app layer. | Add statutory deduction engine + external reporting integration API adapters. |
| 4.12 Retention management | Covered (core) | Deduction/balance/release; daily reminders + due list + readiness API + dashboard; optional **Planned** ledger rows. | Auto **Payment Entry** for release still manual via API/links. |
| 4.13 Contract monitoring | Covered (baseline) | Monthly report generation scheduler + dashboard/summary APIs. | Report approval workflow and richer KPI dimensions still pending. |
| 4.14 Claims management | Covered (baseline) | Claim validation now deterministically auto-calculates `Claim.amount` for penalty/LD types using contract milestone delay inputs; retention release readiness/execution blocks when unresolved approved penalty claims exist. | None for baseline |
| 4.15 Dispute management | Partial | Dispute doctype + stage/status controls + role-gated transition API (`transition_dispute_case`); Stop Work APIs with contract resume semantics. | Deeper recommendation evidence / arbitration automation still open. |
| 4.16 Contract variations | Covered (governed baseline + multi-level) | Threshold-based second-level approval gating for high-impact variations before `Approved`, via `second_approve_contract_variation()`, enforced in `validate_contract_variation()` + `transition_contract_variation()`. | None for baseline |
| 4.17 Contract termination | Covered (core governance) | Termination record validation/on-submit + settlement transition API with prerequisite checks. | Legal-advice attachment enforcement and stronger evidence bundle checks can be added. |
| 4.18 Contract close-out | Covered (governed) | Closeout blocker checks in `validate_contract()` and readiness API. | Archive/immutable archival snapshot behavior not yet implemented. |
| 4.19 Defect liability period | Covered (core) | DLP start, expiry monitor, defect-case validation, contract reopen handling. | DLP warning notifications/escalations before expiry still missing. |
| Audit trail requirement | Covered (baseline) | Workflow comments + audit stream + **JSON/CSV export APIs** (contract-scoped or global). | Scheduled packs to File attachments; analytics workspace. |
| ERP data model completeness | Partial | Most Wave-1 CLM doctypes in place (`Contract`, `Acceptance Certificate`, `Retention Ledger`, `Variation`, `Claim`, `Dispute`, `Termination`, `DLP Case`). | Missing dedicated `Payment Voucher`, `Inspection Test Plan`, `Inspection Report` doctypes/workflows. |

## User Traceability Matrix Integration

The user-provided traceability matrix has been merged into this checkpoint as a second lens.  
Where the user matrix and codebase evidence differ, this section records the reconciliation.

| Traceability Area | User Matrix Signal | Code-Evidence Reconciliation | Consolidated Status |
|---|---|---|---|
| Contract templates/version control | Marked missing | No explicit template generator/version registry in current app logic. | Gap |
| Electronic signatures | Marked partial (flags only) | **`kentender_signature_verifier`** adapter + metadata fields + strict mode; Role Based still available. | Partial until provider-specific implementation deployed. |
| CIT/Inspection committee workflows | Marked green | Governed status transitions + APIs; ERPNext **Workflow** definitions still optional. | Partial |
| Milestone auto-population from tender | Marked missing | **Baseline done**: `seed_contract_milestones_on_contract_activation` seeds ERPNext `Task` rows (`is_contract_milestone`) with payment %, deliverables/AC text, optional dates from contract window; context label from Tender → PPI → Item; idempotent; `seed_contract_milestones` manual retry; conf: `kentender_milestone_seed_count`, `kentender_skip_milestone_seeding`. | Partial (baseline template, not full tender schedule import) |
| Inspection test plan/report traceability | Marked partial | Quality linkage exists, but explicit test-plan/report governance layer not yet implemented. | Partial |
| Payment voucher generation | Marked missing | **ERPNext-first**: governance implemented on **`Payment Entry`** + PI chain (no parallel voucher doctype). | Partial (by design) |
| Retention reminders | Marked green | Current schedulers cover DLP and monthly monitoring; no retention reminder scheduler implemented yet. | Gap |
| Dispute stop-work enforcement | Marked green | Role-gated `issue_stop_work_order` / `withdraw_stop_work_order`, CIT+HoP checks, contract suspend/resume with `resume_status_after_stop_work` (multi-dispute safe), audit events. | Covered (baseline) |
| Termination document support | Marked missing | Termination fields exist; attachment/evidence bundle is not policy-enforced in validation. | Partial |
| Close-out archiving | Marked green | Closeout guardrails exist, and archive-grade closeout is implemented via `Contract Closeout Archive` + `Contract.closeout_archived` edit lock when status is `Closed`. | Covered (baseline) |
| Dashboard layer | Marked missing UI | API-level dashboard exists (`get_clm_dashboard_summary()`), dedicated frontend dashboard page not implemented. | Partial |
| Audit trail centralization | Marked partial | Audit Event + **export/report APIs** for external review. | Native desk Report Builder / charts optional. |

## Consolidated Traceability Table (Comprehensive)

| Domain | Status | Implemented Controls | Pending to Reach Full FRS Parity |
|---|---|---|---|
| Contract prep/signing | Partial | Award-to-contract generation, role-gated signing sequence, activation controls. | Template/versioning, external digital signatures, stronger signing evidence chain. |
| Team governance (CIT/Inspection) | Partial | Status workflows + transition APIs + contract eligibility guards. | Dedicated recommendation documents / ERPNext Workflow JSON. |
| Milestone/implementation | Partial | ERPNext `Task`-based milestone model + **auto-seed at activation** + critical validations. | Import full tender schedule rows; implementation artifacts (minutes/site handover). |
| Inspection/testing | Partial | Quality/receipt linkage fields on acceptance flow. | Dedicated test plan/report governance and stronger traceability linkage. |
| Certification | Covered | Workflow-state transition API + invoice gate on issued/approved cert. | Tighten subtype-specific policies and role checks for FAC issuance. |
| Invoice/payment | Partial | Invoice gating, retention deduction, governed **Payment Entry** (submit gates + chain API). | Voucher-style printouts / ERPNext Workflow definitions optional. |
| Statutory/external integration | Gap | None implemented in app integration layer. | Tax/treasury/financial system adapters with secure API audit logs. |
| Retention | Partial | Ledger + release gates + reminders + due/readiness APIs + Planned scheduling rows. | Policy rules engine; automated bank/PE generation for release. |
| Variations/claims/disputes | Partial | Transition APIs + state guards + audit comments. | Stop-work controlled action and deeper penalty/arbitration automation. |
| Termination/closeout/DLP | Covered (baseline) | Termination record + settlement transitions + closeout blockers + DLP lifecycle; archive-grade closeout snapshot + edit lock are implemented. | None for baseline |
| Monitoring/reporting | Partial | Monthly monitoring report generator + dashboard summary API. | Frontend dashboard UX, richer KPI/risk scoring, approval workflow for reports. |
| Audit/compliance | Partial | Workflow comments on controlled actions. | Centralized immutable audit stream and external-audit-ready reports. |

## Critical Requirements Register (Explicit Tracking)

This section explicitly tracks cross-cutting requirements that may not be obvious when reading only lifecycle sections.

| Critical Requirement | Source | Current State | Status | Planned Closure |
|---|---|---|---|---|
| Digital signature capability (non-repudiation) | FRS 4.2 / Business Rules | `sign_contract` + **External Verified** + conf-hooked verifier + cert/ref metadata fields; **strict** mode for production. | Partial | Wire a real e-sign provider implementation per tenant; optional portal UX. |
| Time-stamped signing audit log | FRS 4.2 | Workflow comments capture action history; no centralized immutable signing ledger. | Partial | Add centralized audit event stream + report/query layer. |
| Payment voucher workflow | FRS 4.10 / Data Model | **`Payment Entry` CLM workflow** mirrors procurement/finance/certify/paid; submit + reporting APIs. | Partial | Optional: ERPNext Workflow + print formats for audit packs. |
| Inspection test plan/report governance | FRS 4.7 / Data Model | Quality linkages exist; explicit governed test plan/report layer not formalized. | Partial | Add strict wrappers/doctype governance for test plan + report evidence chain. |
| Stop Work controlled enforcement | FRS 4.15 | APIs + suspension + resume + overlap handling; optional deeper evidence (attachment matrix) can extend later. | Covered (baseline) | Optional: formal recommendation attachments / richer dispute stage gates. |
| Retention release reminders | FRS 4.12 | Daily scheduler + due list + readiness + dashboard + optional Planned ledger rows. | Covered (baseline) | Optional: email/notification to Head of Finance. |
| Archive-grade closeout | FRS 4.18 | Immutable `Contract Closeout Archive` snapshot is created automatically on `Contract.status -> Closed` and `Contract.closeout_archived` enforces the edit lock while still `Closed`. | Covered (baseline) | None for baseline |
| External statutory/treasury integrations | FRS 4.11 / 9 | No integration adapters implemented in app layer. | Gap | Add API integrations with secure logging and reconciliation hooks. |

## Comprehensive Gap-Closure Backlog

This backlog is expanded to ensure **every identified Partial/Gap item** has a closure path.

### P1 (Immediate Governance and Financial Control)

1. ~~**Stop Work governance completion (FRS 4.15)**~~ **Done (baseline)**
   - Implemented: `issue_stop_work_order` / `withdraw_stop_work_order` (Accounting Officer + System Manager), CIT + HoP recommendation gates, contract suspend with `resume_status_after_stop_work`, last-active SW restores prior status (does not disturb non-SW suspensions), overlap detection, audit events.
   - **Stretch**: attachment-based recommendation evidence, stage-specific dispute gates.

2. **Payment processing governance spine (FRS 4.10) — ERPNext-first** — **baseline done**
   - **`Payment Entry`**: CLM state machine, role-gated `transition_payment_entry_clm`, KenTender audit events, reviewer timestamps, `clm_paid_*` on Paid.
   - **`before_submit`**: contract-linked Pay entry must be **Procurement Certified** with all three reviewer links; must reference ≥1 **submitted** PI matching contract + supplier.
   - **Reporting**: `get_contract_payment_governance_chain(contract)`; dashboard `payment_entries_submitted_pending_clm_paid` + `payment_entries_certified_awaiting_submit`.
   - Run **`ensure_clm_custom_fields()`** after deploy if new Payment Entry fields are missing.

3. **Inspection testing formalization (FRS 4.7)** — **baseline done**
   - DocTypes **`Inspection Test Plan`** (submittable) + **`Inspection Report`** (submittable); validations + `before_submit` on Report (QI must be submitted; outcome vs QI status).
   - **`Acceptance Certificate`**: link **`Inspection Report`**; **Issued** requires submitted Report + submitted Plan; aligns with **QI**, contract, milestone; **Final Acceptance** now requires **QI** like other technical certs.
   - **Task `on_update`**: milestone first hits **Completed** → auto draft **ITP** (`create_inspection_test_plan_for_task` also whitelisted).
   - **Acceptance**: cannot issue governed certificate without Plan → QI → Report chain (where QI is required).

4. **Retention reminders and release scheduling (FRS 4.12)** — **baseline done**
   - **Daily** `remind_retention_release_due`: Workflow comment (deduped by day) with **release_ready** + **blockers**; optional monthly **`Retention Ledger`** row `retention_type=Planned` (excluded from balance; disable via `frappe.conf.kentender_skip_retention_planned_ledger`).
   - **`get_retention_release_due_contracts(lead_days, company?)`**: DLP completed or DLP end within window; retention balance > 0; broader contract statuses (incl. Active / Pending Close-Out) for planning.
   - **`get_retention_release_readiness(contract)`** (whitelisted): mirrors `release_contract_retention` gates.
   - **Dashboard**: `retention_release_due_contracts`, `retention_release_ready_contracts`; **`total_retention_held`** ignores Planned rows.

### P2 (Workflow Completeness and Audit Strength)

5. **Digital signature integration (FRS 4.2)** — **baseline done**
   - **`kentender_signature_verifier`** hook + optional **`kentender_signature_strict`** (disables token fallback; requires real verifier for External Verified).
   - Verifier may return **certificate subject/serial**, **verification_reference**, **signed_at**; stored on **Contract**; `sign_contract` audit enriched.
   - **`get_signature_integration_status()`** (System Manager); **Role Based** unchanged for offline pilots. See `docs/kentender_signature_adapter.md`.

6. **Centralized immutable audit stream (FRS audit/transparency)** — **baseline done**
   - **`KenTender Audit Event`** + `log_ken_tender_audit_event` (existing); **export**: `get_ken_tender_audit_event_report`, `download_ken_tender_audit_events_csv` (JSON + UTF-8 CSV) with contract-wide scope or global filters.
   - **Acceptance**: normalized actor/time/entity + `details_json`; external review via API/CSV (`docs/kentender_audit_export.md`). Deeper analytics UI optional.

7. **CIT and Inspection committee formal workflows (FRS 4.3/4.6)** — **baseline done**
   - Status machines: **Proposed → Approved (AO) → Active (HoP)**; removal/dissolve; transitions enforced on **save** + **`transition_cit_member`** / **`transition_inspection_committee_member`**.
   - **Acceptance**: cannot skip **Approved** before **Active**; audit events on API transitions (`docs/cit_icm_workflow.md`).

8. ~~**Milestone auto-seeding from award/tender package (FRS 4.1/4.5)**~~ — **baseline done**
   - **`Contract` `on_update`**: first transition to **Active** calls `_seed_contract_milestone_tasks` (skipped if milestone tasks already exist for that contract).
   - **Tasks**: subject phases by `contract_type` (when count=3), context from **Tender** / **Procurement Plan Item** / **Item**; equal **payment %** split (last row tops up to 100%); **deliverables** / **acceptance_criteria** text; **exp_start_date** / **exp_end_date** when contract dates exist; audit **`contract_milestones_seeded`**.
   - **Config**: `kentender_milestone_seed_count` (default 3, max 12); `kentender_skip_milestone_seeding` to disable. **API**: `seed_contract_milestones(contract_name)` (requires write on contract, idempotent). See `docs/milestone_seeding.md`.

9. **Implementation activity records (FRS 4.4)**
   - Covered (baseline): implementation activity records are stored on ERPNext `Task` rows (milestones) and the formal acceptance/minutes evidence for those `Task` activities is captured in `Governance Session` proceedings.
   - Auto-creates a draft session + agenda item on first **milestone `Task` completion** (`CIT Meeting`), **site handover** (`Contract.handover_completed`), **inspection report submission**, **acceptance certificate decision**, and **variation/claim/dispute decisions + stop-work issuance** (`Variation Review` / `Claim Decision` / `Dispute Session` / `Stop Work Review`).
   - `Locked` sessions become immutable; `Approved`/`Locked` governance is quorum-gated; minutes lock preconditions are enforced.

10. **Claim penalty/liquidated damages automation (FRS 4.14)**
   - Covered (baseline): deterministic penalty computation for `Liquidated Damages` and `Performance Penalty` claims using:
     - expected completion date (`Contract.end_date`, else milestone `exp_end_date`)
     - actual completion proxy (`Task.modified` date for completed milestones)
     - configurable rate per day (`kentender_penalty_rate_per_day`)
   - **Acceptance**: penalty calculation populates trace fields (`penalty_*`) and sets `Claim.amount` deterministically; retention release readiness/execution blocks on unresolved approved penalty claims.

11. **Variation governance depth (FRS 4.16)**
   - Covered (baseline): high-impact Contract Variations (based on `financial_impact` and `time_extension_days` thresholds) require a second-level approval before `Contract Variation.status` can reach `Approved`.
   - **Acceptance**: high-impact variation cannot reach `Approved` without second-level approval recorded via `second_approve_contract_variation()`. Thresholds and role are configurable via site config keys.

12. **Termination evidence bundle enforcement (FRS 4.17)** — **Done (baseline)**
   - Added `Termination Record` evidence checklist fields (`legal_advice_reference`, `notice_issued_to_supplier`, `supporting_documents_provided`) and enforce them in `transition_termination_record_settlement()` when moving to `Completed`.
   - **Acceptance**: settlement completion blocked until evidence checklist satisfied.

13. **Archive-grade closeout (FRS 4.18)**
   - Covered (baseline): `Contract Closeout Archive` immutable snapshot is created automatically when `Contract.status` transitions into `Closed`, and `Contract.closeout_archived` blocks further contract edits while still `Closed`.
   - **Acceptance**: closed contract snapshot cannot be altered except via the governed reopen route (Defect Liability reopening sets status back to `Active`).

### P3 (Integration and Reporting Maturity)

14. **Statutory + treasury integrations (FRS 4.11 / 9)**
   - Implement tax/statutory deduction adapters and treasury payment integration hooks.
   - Add reconciliation and failure-retry logging.
   - **Acceptance**: statutory posting and treasury handoff events are auditable end-to-end.

15. **Monitoring/reporting UX and approvals (FRS 4.13/8)**
   - Build dashboard UI on top of existing summary APIs.
   - Add workflow for monthly report submit/review and richer KPI/risk scoring.
   - **Acceptance**: monthly monitoring report has approval states and dashboard shows risk/payment/milestone trends.

16. **DLP early warning and escalation (FRS 4.19)**
   - Add pre-expiry and overdue notifications with escalation routing.
   - **Acceptance**: DLP alerts trigger automatically at configured lead times.

## Immediate Readiness Statement

- Current CLM implementation is **operationally strong for Wave-1 governance**: contract lifecycle controls, certificate-gated invoicing, retention accounting, legal transition guards, closeout blockers, and DLP controls are in place.
- For full parity with the complete FRS/design intent, the next critical layer is **inspection/payment orchestration + stop-work enforcement + statutory/digital integration**.

