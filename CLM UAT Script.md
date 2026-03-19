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


## UAT-6 Termination and DLP

1. Create/submit termination record:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_termination_record --args "['<CONTRACT>','Termination reason','Pending',1]"`
2. Start DLP:
   - `bench --site kentender.midas.com execute kentender.kentender.api.start_defect_liability_period --args "['<CONTRACT>']"`
3. Create defect case:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_defect_liability_case --args "['<CONTRACT>','Defect found','Open',1]"`
4. Termination settlement workflow:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_termination_record_settlement --args "['<TERM_REC>','In Progress','settlement started']"`
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_termination_record_settlement --args "['<TERM_REC>','Completed','handover and discharge done']"`

Expected:
- Termination record transitions contract appropriately when submitted
- DLP dates/status are set
- Defect case creation works during active/reopened DLP
- Settlement completion is blocked until handover and discharge reference are set


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

SELECT name, contract, status FROM `tabClaim` ORDER BY creation DESC LIMIT 10;
SELECT name, contract, status FROM `tabDispute Case` ORDER BY creation DESC LIMIT 10;

SELECT name, contract, status FROM `tabDefect Liability Case` ORDER BY creation DESC LIMIT 10;
SELECT name, contract, docstatus FROM `tabTermination Record` ORDER BY creation DESC LIMIT 10;

SELECT name, contract, report_month, status
FROM `tabMonthly Contract Monitoring Report`
ORDER BY creation DESC LIMIT 10;
```

