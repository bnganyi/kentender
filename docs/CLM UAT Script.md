# KenTender CLM UAT Script (Workflow-Hardened)

## Scope

This script validates the implemented CLM backbone with workflow hardening:

- Contract creation/signing/activation
- Milestone and certificate gating
- Retention deduction
- Variation/claim/dispute baseline
- Termination and DLP lifecycle
- Role-gated workflow transition APIs
- Retention release governance
- Close-out readiness and dashboard/reporting APIs

Use site: `kentender.midas.com`.

## Split UAT (Recommended)
For tractability, the full UAT script has been split into module-focused documents:
- `docs/uat/uat-01-contract-milestones-certificates-and-retention-deduction.md` (UAT-1..4)
- `docs/uat/uat-02-variations-claims-and-disputes.md` (UAT-5 + FRS 4.16 depth)
- `docs/uat/uat-03-termination-dlp-and-closeout.md` (UAT-6..7)
- `docs/uat/uat-04-monitoring-and-dashboard-apis.md` (UAT-8)
- `docs/uat/uat-05-retention-release-governance.md` (UAT-9)
- `docs/uat/uat-06-governance-sessions-and-penalties.md` (UAT-10 + FRS 4.14 penalty automation)


## Preconditions

- Bench and site are up.
- Latest migration and cache clear done:
  - `bench --site kentender.midas.com migrate`
  - `bench --site kentender.midas.com clear-cache`
- There is at least one awarded tender and related tender submission.


## UAT-1 Contract Creation and Activation

1. Create contract from awarded tender:
   - `bench --site kentender.midas.com execute kentender.kentender.api.create_contract_from_award --args "['<TENDER>','<SUBMISSION>']"`
2. Sign as supplier:
   - `bench --site kentender.midas.com execute kentender.kentender.api.sign_contract --args "['<CONTRACT>','Supplier']"`
3. Sign as accounting officer:
   - `bench --site kentender.midas.com execute kentender.kentender.api.sign_contract --args "['<CONTRACT>','Accounting Officer']"`

Expected:
- Contract status becomes `Active`
- `signed_by_supplier=1`, `signed_by_accounting_officer=1`
- `project` is auto-created and linked


## UAT-2 Milestone Rules on Task

1. Negative test (Completed without supplier confirmation):
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_task_milestone --args "['<PROJECT>','<CONTRACT>','Milestone A','Completed',0]"`
2. Positive test:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_task_milestone --args "['<PROJECT>','<CONTRACT>','Milestone B','Completed',1]"`

Expected:
- First call fails with supplier confirmation message
- Second call succeeds and returns Task name


## UAT-3 Certificate Gate Before Invoice

1. Negative invoice test:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_contract_purchase_invoice --args "['<CONTRACT>',1000,0]"`
2. Create certificate (draft):
   - `bench --site kentender.midas.com execute kentender.kentender.api.create_acceptance_certificate_for_contract --args "['<CONTRACT>','Interim Acceptance','Approved',1]"`
3. Move certificate to Issued workflow state:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_acceptance_certificate --args "['<CERT_NAME>','Pending Technical Review','technical check passed']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_acceptance_certificate --args "['<CERT_NAME>','Pending Accounting Officer Approval','user dept endorsed']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_acceptance_certificate --args "['<CERT_NAME>','Issued','finance approved',1]"`
4. Positive invoice test:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_contract_purchase_invoice --args "['<CONTRACT>',1000,1,'<CERT_NAME>']"`

Expected:
- Invoice without certificate is blocked
- Invoice with approved submitted certificate in `Issued` workflow state is created


## UAT-4 Retention Deduction

1. Set retention percentage on Contract (example 10%).
2. Submit a contract-linked Purchase Invoice:
   - `bench --site kentender.midas.com execute kentender.kentender.api.submit_purchase_invoice_for_test --args "['<PINV_NAME>']"`
3. Verify ledger:
   - `SELECT name, retention_type, amount, balance_after_transaction FROM \`tabRetention Ledger\` WHERE contract='<CONTRACT>' ORDER BY creation DESC LIMIT 5;`

Expected:
- Retention Ledger row created with `retention_type=Deduction`, `status=Held`


## UAT-5 Variation / Claim / Dispute

1. Variation validation negative:
   - missing justification should fail
2. Variation positive:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_contract_variation --args "['<CONTRACT>','Cost Adjustment','Scope correction',250]"`
3. Transition variation:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Under Review','procurement review started']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Approved','approved by accounting officer']"`
4. Claim create:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_claim --args "['<CONTRACT>','Supplier','Compensation Claim','Compensation request']"`
5. Claim transition:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_claim --args "['<CLAIM>','Under Review','procurement review']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_claim --args "['<CLAIM>','Approved','liability accepted']"`
6. Dispute create:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_dispute_case --args "['<CONTRACT>','Dispute on valuation']"`
7. Dispute transition:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_dispute_case --args "['<DISPUTE>','In Progress','escalated for hearing']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_dispute_case --args "['<DISPUTE>','Resolved','settlement reached']"`

Expected:
- Variation/claim/dispute transitions follow allowed state graph and role checks
- Audit comments are written for each transition

### Variation governance depth (FRS 4.16): high-impact needs extra approval
Preconditions:
- Set `kentender_variation_high_financial_impact_threshold` (default 1,000,000) low enough for the test, OR use a very large `financial_impact`.
- Second-level approval role: `Head of Finance` (or `kentender_variation_second_level_approval_role`).
1. Create a high-impact `Contract Variation` in `Draft` (do NOT auto-Approved yet):
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_contract_variation --args "['<CONTRACT>','Cost Adjustment','High impact variation',2000000,0,None,None,'Draft',0]"`
2. Move to `Under Review`:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Under Review','procurement review started']"`
3. Attempt to move to `Approved` (should fail because second-level approval is missing):
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Approved','approved by accounting officer']"`
4. Record second-level approval:
   - `bench --site kentender.midas.com execute kentender.kentender.api.second_approve_contract_variation --args "['<VARIATION>','second-level approval by Head of Finance']"`
5. Now attempt `Approved` again (should succeed):
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Approved','approved by accounting officer after second-level approval']"`


## UAT-6 Termination and DLP

1. Create/submit termination record:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_termination_record --args "['<CONTRACT>','Termination reason','Pending',1]"`
2. Start DLP:
   - `bench --site kentender.midas.com execute kentender.kentender.api.start_defect_liability_period --args "['<CONTRACT>']"`
3. Create defect case:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_defect_liability_case --args "['<CONTRACT>','Defect found','Open',1]"`
4. Termination settlement workflow:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_termination_record_settlement --args "['<TERM_REC>','In Progress','settlement started']"`
   - Set checklist items except legal evidence:
     - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_termination_record_evidence --args "['<TERM_REC>','',0,0,1,'<DISCH_DOC>']"`
   - Attempt completion (should fail):
     - `bench --site kentender.midas.com execute kentender.kentender.api.transition_termination_record_settlement --args "['<TERM_REC>','Completed','should fail: missing legal evidence']"`
   - Set full evidence checklist:
     - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_termination_record_evidence --args "['<TERM_REC>','LEGAL_ADVICE_REF',1,1,1,'<DISCH_DOC>']"`
   - Complete settlement:
     - `bench --site kentender.midas.com execute kentender.kentender.api.transition_termination_record_settlement --args "['<TERM_REC>','Completed','settlement evidence bundle satisfied']"`

Expected:
- Termination record transitions contract appropriately when submitted
- DLP dates/status are set
- Defect case creation works during active/reopened DLP
- Settlement completion is blocked until all evidence checklist items are set:
  - `handover_completed = 1`
  - `discharge_document_reference` set
  - `legal_advice_reference` set
  - `notice_issued_to_supplier = 1`
  - `supporting_documents_provided = 1`


## UAT-7 Close-Out Governance

1. Negative close attempt:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_contract_status --args "['<CONTRACT>','Closed']"`
2. Positive close attempt after setting prerequisites:
   - ensure final acceptance certificate exists
   - set `all_payments_completed=1` and `handover_completed=1`
   - call `try_set_contract_status(..., 'Closed', '<FINAL_CERT>', 1, 1)`

Expected:
- Close is blocked until prerequisites are met
- Close succeeds when prerequisites are complete
- Upon successful close:
  - A new `Contract Closeout Archive` is created for that `Contract`
  - `Contract.closeout_archived = 1`
- Immutability check:
  - Attempt to save the same `Contract` again while still `Closed` should fail with `Archived closed Contract cannot be modified`


## UAT-8 Monitoring and Dashboard APIs

1. Generate monthly reports:
   - `bench --site kentender.midas.com execute kentender.kentender.api.create_monthly_contract_monitoring_reports`
2. Check close-out readiness:
   - `bench --site kentender.midas.com execute kentender.kentender.api.get_contract_closeout_readiness --args "['<CONTRACT>']"`
3. Get dashboard:
   - `bench --site kentender.midas.com execute kentender.kentender.api.get_clm_dashboard_summary`

Expected:
- Monthly report rows created
- Readiness returns `ready` plus explicit blockers
- Dashboard returns contract/legal/quality/finance/monitoring aggregates


## UAT-9 Retention Release Governance

1. Negative release attempt while contract is active or DLP not completed:
   - `bench --site kentender.midas.com execute kentender.kentender.api.release_contract_retention --args "['<CONTRACT>',100,'negative test']"`
2. Ensure prerequisites:
   - Contract status is `Closed` or `Terminated`
   - Contract `dlp_status` is `Completed`
   - Retention balance exists
3. Positive release:
   - `bench --site kentender.midas.com execute kentender.kentender.api.release_contract_retention --args "['<CONTRACT>',100,'partial release']"`
4. Full release:
   - `bench --site kentender.midas.com execute kentender.kentender.api.release_contract_retention --args "['<CONTRACT>']"`

Expected:
- Release is blocked unless close-out and DLP conditions are met
- Release amount cannot exceed retention balance
- `Retention Ledger` gets `Release` rows with reduced running balance


## UAT-10 Governance Sessions MVP (Proceedings MVP)

### Preconditions
- Contract exists and is `Active`
- At least one milestone `Task` exists with `is_contract_milestone = 1`

### A) Milestone completion creates milestone verification proceedings
1. Open any contract milestone `Task` with:
   - `is_contract_milestone = 1`
   - `milestone_status = Pending`
2. Set `supplier_confirmed = 1`
3. Change `milestone_status` to `Completed` and Save

Expected:
- A new `Governance Session` is created:
  - `session_type = CIT Meeting`
  - `status = Draft`
  - `context_reference_doctype = Task`
  - `context_reference_name = <TASK_NAME>`
  - `quorum_required = 2`
- A new `Session Agenda Item` is created for that session:
  - `sequence = 1`
  - `subject = Milestone Progress Review`
  - `reference_doctype = Task`
  - `reference_name = <TASK_NAME>`
  - `decision_required = 1`

### B) Locked sessions become immutable
1. Open the created `Governance Session`
2. Ensure quorum (add 2 participants with `Present` attendance):
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_add_session_participant --args "['<GS_NAME>','Member','Present']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_add_session_participant --args "['<GS_NAME>','Member','Present']"`
3. Resolution gating while the parent session is still `Draft`:
   - Identify the `Session Agenda Item` created in step `A` as `<SAI_NAME>`
   - Create a `Session Resolution` in `Draft`:
     - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_session_resolution --args "['<GS_NAME>','<SAI_NAME>','Recommend Approval','CIT approves milestone','Draft']"`
   - Capture the created resolution name as `<SR_NAME>`
   - Attempt to move the resolution to `Approved` while parent session is `Draft` (should fail):
     - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_session_resolution_status --args "['<SR_NAME>','Approved']"`
4. Move minutes workflow to `Approved` (run as `System Manager`), but do NOT lock yet:
   - `bench --site kentender.midas.com execute kentender.kentender.api.schedule_governance_session --args "['<GS_NAME>']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.start_governance_session --args "['<GS_NAME>']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.draft_governance_session_minutes --args "['<GS_NAME>']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.submit_governance_session_minutes --args "['<GS_NAME>']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.approve_governance_session --args "['<GS_NAME>']"`
5. Now that the parent session is `Approved`, move the resolution to `Approved` (should succeed):
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_session_resolution_status --args "['<SR_NAME>','Approved']"`
6. Lock the governance session:
   - `bench --site kentender.midas.com execute kentender.kentender.api.lock_governance_session --args "['<GS_NAME>']"`
7. Attempt to transition the session back to `Approved`:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_governance_session --args "['<GS_NAME>','Approved','should fail']"`

Expected:
- Transition fails (session is locked / transition is not allowed)
- Resolution move to `Approved` fails while parent session is `Draft`
- Resolution move to `Approved` succeeds after parent session becomes `Approved`
- Editing any child record linked to the session also fails once locked

### C) Contract handover completion creates site handover proceedings
1. Open the `Contract`
2. Set `handover_completed = 1` and Save (ensure it was previously 0)

Expected:
- A new `Governance Session` is created (idempotent on repeat):
  - `session_type = Site Handover`
  - `status = Draft`
  - `context_reference_doctype = Contract`
  - `context_reference_name = <CONTRACT_NAME>`

### D) Inspection Report submission creates an inspection session
1. Create and submit a `Quality Inspection` (ensure it is submitted and has the correct contract/milestone links).
2. Create an `Inspection Report` linked to:
   - the same `Contract`
   - an `Inspection Test Plan`
   - the submitted `Quality Inspection`
3. Submit the `Inspection Report`

Expected:
- A new `Governance Session` is created:
  - `session_type = Inspection Session`
  - `status = Draft`
  - `context_reference_doctype = Inspection Report`
  - `context_reference_name = <INSPECTION_REPORT_NAME>`
- A new `Session Agenda Item` is created for that session:
  - `sequence = 1`
  - `subject = Inspection Findings`
  - `reference_doctype = Task`
  - `reference_name = <MILESTONE_TASK_FROM_INSPECTION>`

### E) Acceptance Certificate decision creates an acceptance committee sitting
1. Create an `Acceptance Certificate` linked to:
   - the relevant `Contract`
   - the relevant `Task` (optional if your certificate design uses `task` linkage)
   - a valid chain of `Quality Inspection` and `Inspection Report` as required by your certificate type
2. Move the acceptance certificate into `workflow_state = Issued` (or `Rejected`) using:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_acceptance_certificate --args "['<CERT_NAME>','Issued','approved']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Acceptance Committee Sitting`
  - `status = Draft`
  - `context_reference_doctype = Acceptance Certificate`
  - `context_reference_name = <CERT_NAME>`
- A new `Session Agenda Item` is created for that session recording the decision (`workflow_state`).

### F) Contract Variation decision creates a proceedings session
1. Create a `Contract Variation` (defaults to `Approved` in the bench helper):
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_contract_variation --args "['<CONTRACT>','Cost Adjustment','Scope correction',250]"`
2. Re-apply the decision via controlled transition (so the auto-creator runs):
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Approved','approved by accounting officer']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Variation Review`
  - `status = Draft`
  - `context_reference_doctype = Contract Variation`
  - `context_reference_name = <VARIATION>`

### G) Claim decision creates a proceedings session
1. Create a `Claim`:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_claim --args "['<CONTRACT>','Supplier','Compensation Claim','Compensation request']"`
2. Transition the claim to Under Review:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_claim --args "['<CLAIM>','Under Review','procurement review started']"`
3. Transition the claim to Approved:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_claim --args "['<CLAIM>','Approved','liability accepted']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Claim Decision`
  - `status = Draft`
  - `context_reference_doctype = Claim`
  - `context_reference_name = <CLAIM>`

### H) Dispute resolution creates a proceedings session
1. Create a `Dispute Case`:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_dispute_case --args "['<CONTRACT>','Dispute on valuation']"`
2. Resolve the dispute:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_dispute_case --args "['<DISPUTE>','Resolved','settlement reached']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Dispute Resolution`
  - `status = Draft`
  - `context_reference_doctype = Dispute Case`
  - `context_reference_name = <DISPUTE>`

### I) Stop Work issuance creates a proceedings session
1. Create a `Dispute Case`:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_dispute_case --args "['<CONTRACT>','Dispute on execution']"`
2. Set recommendations required for Stop Work issuance:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_dispute_recommendations --args "['<DISPUTE>',1,1]"`
3. Issue Stop Work Order:
   - `bench --site kentender.midas.com execute kentender.kentender.api.issue_stop_work_order --args "['<DISPUTE>','Stop work due to non-compliance']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Dispute Session`
  - `status = Draft`
  - `context_reference_doctype = Dispute Case`
  - `context_reference_name = <DISPUTE>`

### J) Monthly monitoring review creates a proceedings session
1. Generate the monthly monitoring report (for the current month or a chosen month):
   - `bench --site kentender.midas.com execute kentender.kentender.api.create_monthly_contract_monitoring_reports`
2. Capture the created `Monthly Contract Monitoring Report` name as `<MCMR_NAME>`
3. Mark the report as reviewed:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_monthly_contract_monitoring_report_status --args "['<MCMR_NAME>','Reviewed']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Monitoring Review`
  - `status = Draft`
  - `context_reference_doctype = Monthly Contract Monitoring Report`
  - `context_reference_name = <MCMR_NAME>`

### K) Claim penalty/liquidated damages automation (FRS 4.14)
Preconditions:
- Contract is `Active`
- At least one milestone `Task` exists with `is_contract_milestone = 1`
- `Contract.end_date` is set in the past (e.g. `5 days` earlier than today)

1. Choose a milestone `Task` with:
   - `milestone_status = Pending`
2. Set `supplier_confirmed = 1`
3. Change `milestone_status` to `Completed` and Save
4. Create a penalty claim:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_claim --args "['<CONTRACT>','Procuring Entity','Liquidated Damages','Late completion LD']"`
5. Transition the claim to `Approved`:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_claim --args "['<CLAIM>','Approved','approving penalty auto-calculation']"`

Expected:
- `Claim.penalty_delay_days` is > 0 (because milestone completion is after `Contract.end_date`)
- `Claim.penalty_rate_per_day` equals the configured `kentender_penalty_rate_per_day` (default `1000`)
- `Claim.amount == Claim.penalty_delay_days * Claim.penalty_rate_per_day`
- `Claim.penalty_expected_completion_date == Contract.end_date`
- `Claim.penalty_actual_completion_date` is the completion date proxy (derived from the milestone task `modified` date)

## SQL Verification Snippets

```sql
SELECT name, status, company, supplier, project
FROM `tabContract` ORDER BY creation DESC LIMIT 5;

SELECT name, contract, certificate_type, decision, docstatus
FROM `tabAcceptance Certificate` ORDER BY creation DESC LIMIT 5;

SELECT name, contract, workflow_state, decision, docstatus
FROM `tabAcceptance Certificate` ORDER BY creation DESC LIMIT 10;

SELECT name, contract, retention_type, amount, balance_after_transaction, status
FROM `tabRetention Ledger` ORDER BY creation DESC LIMIT 10;

SELECT name, contract, variation_type, status, docstatus
FROM `tabContract Variation` ORDER BY creation DESC LIMIT 10;

SELECT name, contract, claim_by, claim_type, amount, status,
       penalty_delay_days, penalty_rate_per_day,
       penalty_expected_completion_date, penalty_actual_completion_date, penalty_formula
FROM `tabClaim` ORDER BY creation DESC LIMIT 10;
SELECT name, contract, status FROM `tabDispute Case` ORDER BY creation DESC LIMIT 10;

SELECT name, status, session_type, context_reference_doctype, context_reference_name
FROM `tabGovernance Session`
ORDER BY creation DESC LIMIT 10;
SELECT name, session, subject, decision_required
FROM `tabSession Agenda Item`
ORDER BY creation DESC LIMIT 10;

SELECT name, contract, archive_sequence, archived_on
FROM `tabContract Closeout Archive`
ORDER BY creation DESC LIMIT 10;

SELECT name, status, closeout_archived, closeout_archive_sequence, closeout_archive_ref
FROM `tabContract`
ORDER BY creation DESC LIMIT 10;

SELECT name, contract, status FROM `tabDefect Liability Case` ORDER BY creation DESC LIMIT 10;
SELECT name, contract, docstatus FROM `tabTermination Record` ORDER BY creation DESC LIMIT 10;

SELECT name, contract, report_month, status
FROM `tabMonthly Contract Monitoring Report`
ORDER BY creation DESC LIMIT 10;
```

