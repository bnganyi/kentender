# KenTender CLM Coverage Checkpoint Matrix

Date: 2026-03-18  
Scope reviewed against:
- `clm-inputs/Ken Tender — Phase 2 Contract Management Requirements.md`
- `clm-inputs/KenTender CLM Design.md`
- `clm-inputs/CLM REQUIREMENTS TRACEABILITY MATRIX.md`
- current implementation (`doctype/*.json`, `hooks.py`, `api.py`)

## Coverage Legend

- **Covered**: Implemented and enforceable in current code.
- **Partial**: Basic implementation exists, but workflow depth/integration/automation is incomplete.
- **Gap**: Not implemented yet in codebase.

## Requirement-to-Implementation Matrix

| FRS Area | Status | Current Implementation | Main Gaps / Improvement Target |
|---|---|---|---|
| 4.1 Contract preparation | Partial | `create_contract_from_award()` auto-populates contract core fields from award/submission. | Attachments/version control/template generation not yet enforced as controlled workflow. |
| 4.2 Contract execution and signing | Partial | `sign_contract()` and `activate_contract()` with strict sequence and activation guardrails; status transition hardening in `validate_contract()`. | No true digital-signature integration (cryptographic/non-repudiation); currently role/action based. |
| 4.3 CIT appointment | Partial | `Contract Implementation Team Member` doctype + duplicate/eligibility validation (`validate_cit_member`). | Explicit recommendation/approval workflow state machine still missing. |
| 4.4 Implementation activities (works/goods) | Covered (baseline) | Milestone model on ERPNext `Task` + project integration at activation, with formal acceptance/minutes captured via auto-created `Governance Session` proceedings. | None for the baseline; remaining enhancement work is focused on evidence registry/signature depth and adapter execution controls. |
| 4.5 Milestone monitoring | Covered (Wave-1 level) | `Task` custom fields + validations; baseline **milestone seeding** on contract activation (hook + idempotent tasks). | No SLA/escalation automation or milestone delay alerts yet. |
| 4.6 Inspection committee | Partial | `Inspection Committee Member` doctype + duplicate checks. | Committee appointment workflow and recommendation chain not fully formalized. |
| 4.7 Inspection testing | Partial | Acceptance Certificate links to `Quality Inspection` and `Purchase Receipt`; design direction aligns to ERPNext Quality. | No dedicated Inspection Test Plan/Inspection Report governance workflow and no auto quality artifact generation from milestone events. |
| 4.8 Certification | Covered (governed) | `Acceptance Certificate` doctype + workflow-state hardening + role-gated transitions (`transition_acceptance_certificate`). | Certificate subtype-specific rules can be deepened (e.g., stricter FAC-only closeout path checks by role). |
| 4.9 Invoice submission | Covered (gated) | Contract-linked invoice validation via `validate_purchase_invoice_certificate()`. | Supporting-doc checklist and tax breakdown quality checks not yet formalized. |
| 4.10 Payment processing | Partial | Retention deduction from invoice on submit; closeout flags on contract. | No full payment voucher workflow orchestration (review-forward-certify-process) as explicit state machine. |
| 4.11 Statutory compliance | Gap | No tax-register/treasury integration code in app layer. | Add statutory deduction engine + external reporting integration API adapters. |
| 4.12 Retention management | Covered (core) | Deduction ledger + balance math + governed release (`release_contract_retention`) with closeout/DLP prerequisites. | Reminder scheduler for retention expiry and auto release scheduling still missing. |
| 4.13 Contract monitoring | Covered (baseline) | Monthly report generation scheduler + dashboard/summary APIs. | Report approval workflow and richer KPI dimensions still pending. |
| 4.14 Claims management | Covered (baseline) | Claim validation now auto-calculates `amount` for penalty/LD claim types using deterministic contract milestone delay inputs; retention release readiness/execution blocks when unresolved approved penalty claims exist. | None for baseline |
| 4.15 Dispute management | Partial | Dispute doctype + stage/status controls + role-gated transition API (`transition_dispute_case`). | Stop Work governance is incomplete (field exists, but controlled issuance/contract suspension orchestration should be explicit API). |
| 4.16 Contract variations | Covered (governed baseline + multi-level) | Validation + transitions + apply-on-submit behavior + role-gated transition API (`transition_contract_variation`), with threshold-based second-level approval required for high-impact variations. | None for baseline |
| 4.17 Contract termination | Covered (core governance + evidence bundle) | Termination record settlement completion is blocked until legal/evidence checklist is satisfied (`legal_advice_reference`, `notice_issued_to_supplier`, `supporting_documents_provided`) in `transition_termination_record_settlement()`. | None for baseline |
| 4.18 Contract close-out | Covered (governed) | Closeout blocker checks + readiness API, and **immutable closeout snapshots** via `Contract Closeout Archive` on transition into `Closed` with contract edit lock semantics. | None (archive-grade closeout baseline implemented). |
| 4.19 Defect liability period | Covered (core) | DLP start, expiry monitor, defect-case validation, contract reopen handling. | DLP warning notifications/escalations before expiry still missing. |
| Audit trail requirement | Covered (baseline) | Workflow comments written across critical transitions. | Add normalized audit doctype/event stream for analytics and forensic reporting. |
| ERP data model completeness | Partial | Most Wave-1 CLM doctypes in place (`Contract`, `Acceptance Certificate`, `Retention Ledger`, `Variation`, `Claim`, `Dispute`, `Termination`, `DLP Case`). | Missing dedicated `Payment Voucher`, `Inspection Test Plan`, `Inspection Report` doctypes/workflows. |

## User Traceability Matrix Integration

The user-provided traceability matrix has been merged into this checkpoint as a second lens.  
Where the user matrix and codebase evidence differ, this section records the reconciliation.

| Traceability Area | User Matrix Signal | Code-Evidence Reconciliation | Consolidated Status |
|---|---|---|---|
| Contract templates/version control | Marked missing | No explicit template generator/version registry in current app logic. | Gap |
| Electronic signatures | Marked partial (flags only) | Matches current implementation (`sign_contract()` flags + role controls; no signature provider integration). | Partial |
| CIT/Inspection committee workflows | Marked green | Doctypes + validation exist; formal workflow JSON/fixture definitions are still absent. | Partial |
| Milestone auto-population from tender | Marked missing | Baseline seeding at **Active**: `Contract` hook + `seed_contract_milestones`; tender/PPI/Item context in subject; see `docs/milestone_seeding.md`. | Partial |
| Inspection test plan/report traceability | Marked partial | Quality linkage exists, but explicit test-plan/report governance layer not yet implemented. | Partial |
| Payment voucher generation | Marked missing | Confirmed missing from custom doctypes and service APIs. | Gap |
| Retention reminders | Marked green | Current schedulers cover DLP and monthly monitoring; no retention reminder scheduler implemented yet. | Gap |
| Dispute stop-work enforcement | Marked green | `stop_work_order_issued` field exists, but no dedicated controlled issuance API + suspension automation yet. | Partial |
| Termination document support | Marked missing | Termination evidence checklist is enforced before settlement completion (`legal_advice_reference`, `notice_issued_to_supplier`, `supporting_documents_provided`) in `transition_termination_record_settlement()`. | Covered (baseline) |
| Close-out archiving | Marked green | Closeout guardrails exist, and archive-grade closeout is implemented via `Contract Closeout Archive` + `Contract.closeout_archived` edit lock when status is `Closed`. | Covered (baseline) |
| Dashboard layer | Marked missing UI | API-level dashboard exists (`get_clm_dashboard_summary()`), dedicated frontend dashboard page not implemented. | Partial |
| Audit trail centralization | Marked partial | Workflow comments are present; centralized audit event model/reporting is still missing. | Partial |

## Consolidated Traceability Table (Comprehensive)

| Domain | Status | Implemented Controls | Pending to Reach Full FRS Parity |
|---|---|---|---|
| Contract prep/signing | Partial | Award-to-contract generation, role-gated signing sequence, activation controls. | Template/versioning, external digital signatures, stronger signing evidence chain. |
| Team governance (CIT/Inspection) | Partial | Member doctypes, duplicate validation, role-permission baseline. | Formal recommendation/appointment workflows and action APIs. |
| Milestone/implementation | Partial | ERPNext `Task` milestones + **activation seeding** + validations. | Full tender schedule import; implementation artifacts (minutes/site handover). |
| Inspection/testing | Partial | Quality/receipt linkage fields on acceptance flow. | Dedicated test plan/report governance and stronger traceability linkage. |
| Certification | Covered | Workflow-state transition API + invoice gate on issued/approved cert. | Tighten subtype-specific policies and role checks for FAC issuance. |
| Invoice/payment | Partial | Invoice gating and retention deduction posting. | Payment voucher workflow and end-to-end payment orchestration trail. |
| Statutory/external integration | Gap | None implemented in app integration layer. | Tax/treasury/financial system adapters with secure API audit logs. |
| Retention | Partial | Ledger deductions, balance tracking, governed release after close-out + DLP completion. | Reminder/schedule automation and policy rules engine for release criteria. |
| Variations/claims/disputes | Partial | Transition APIs + state guards + audit comments. | Stop-work controlled action and deeper penalty/arbitration automation. |
| Termination/closeout/DLP | Covered (baseline) | Termination record + settlement transitions + closeout blockers + DLP lifecycle; archive-grade closeout snapshot + edit lock are implemented. | None for baseline |
| Monitoring/reporting | Partial | Monthly monitoring report generator + dashboard summary API. | Frontend dashboard UX, richer KPI/risk scoring, approval workflow for reports. |
| Audit/compliance | Partial | Workflow comments on controlled actions. | Centralized immutable audit stream and external-audit-ready reports. |

## Priority Gap Backlog (Recommended Next Sprint)

1. **P1 - Stop Work governance completion**
   - Add explicit action API: only Accounting Officer can issue Stop Work.
   - Require captured recommendations from CIT and Head of Procurement.
   - Auto-transition/suspend linked contract with audit record.

2. **P1 - Payment voucher workflow spine**
   - Implement Payment Voucher doctype or ERPNext-native mapping with workflow states:
     `Draft -> Procurement Reviewed -> Finance Verified -> Procurement Certified -> Paid`.
   - Link invoice-to-voucher-to-payment traceability.

3. ~~**P1 - Inspection testing formalization**~~ **Done (baseline)**
   - `Inspection Test Plan` + `Inspection Report` + AC `inspection_report` link; Issued requires submitted Plan/Report/QI alignment; milestone **Completed** auto draft ITP.

4. ~~**P1 - Retention reminders and release scheduling**~~ **Done (baseline)**
   - Daily reminders + `get_retention_release_due_contracts` / `get_retention_release_readiness` + dashboard + optional **Planned** retention ledger rows.

5. ~~**P2 - Digital signature integration**~~ **Done (baseline)**
   - `kentender_signature_verifier` + `kentender_signature_strict`; Contract cert/ref fields; `docs/kentender_signature_adapter.md`.

6. ~~**P2 - Centralized audit export**~~ **Done (baseline)**
   - `get_ken_tender_audit_event_report` + `download_ken_tender_audit_events_csv`; contract-scoped related-doc sweep; see `docs/kentender_audit_export.md`.

7. ~~**P2 - CIT & Inspection committee workflows**~~ **Done (baseline)**
   - `transition_cit_member` / `transition_inspection_committee_member`; AO approve → HoP activate; `docs/cit_icm_workflow.md`.

8. ~~**P2 - Milestone auto-seeding (FRS 4.1/4.5)**~~ **Done (baseline)**
   - `seed_contract_milestones_on_contract_activation` on **Contract** `on_update`; `seed_contract_milestones` API; see `docs/milestone_seeding.md`.

9. ~~**P2 - Archive-grade closeout**~~ **Done (baseline)**
   - Immutable `Contract Closeout Archive` snapshot created on transition into `Contract.status = Closed`.
   - `Contract.closeout_archived` blocks further contract edits while status remains `Closed`.

## Immediate Readiness Statement

- Current CLM implementation is **operationally strong for Wave-1 governance**: contract lifecycle controls, certificate-gated invoicing, retention accounting, legal transition guards, closeout blockers, and DLP controls are in place.
- For full parity with the complete FRS/design intent, the next critical layer is **inspection/payment orchestration + stop-work enforcement + statutory/digital integration**.

