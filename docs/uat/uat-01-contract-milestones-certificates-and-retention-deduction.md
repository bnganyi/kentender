# UAT-01..04: Contract, Milestones, Certificates, Retention Deduction

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

