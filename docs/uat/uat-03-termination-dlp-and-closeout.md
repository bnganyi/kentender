# UAT-06..07: Termination Evidence, DLP, and Archive-grade Closeout

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

