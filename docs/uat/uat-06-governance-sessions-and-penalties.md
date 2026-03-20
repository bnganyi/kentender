# UAT-10: Governance Sessions MVP + FRS 4.14 Penalty Automation (Proceedings)

## Preconditions
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
1. Create and submit a `Quality Inspection`
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
- A new `Session Agenda Item` is created for that session recording the inspection findings.

### E) Acceptance Certificate decision creates an acceptance committee sitting
1. Create an `Acceptance Certificate` linked to:
   - the relevant `Contract`
   - the relevant `Task` (optional)
   - required `Quality Inspection` + `Inspection Report` chain
2. Move the certificate to `workflow_state = Issued` (or `Rejected`):
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_acceptance_certificate --args "['<CERT_NAME>','Issued','approved']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Acceptance Committee Sitting`
  - `status = Draft`
  - `context_reference_doctype = Acceptance Certificate`
  - `context_reference_name = <CERT_NAME>`

### F) Contract Variation decision creates a proceedings session
1. Create a `Contract Variation` (defaults to `Approved` in the bench helper):
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_contract_variation --args "['<CONTRACT>','Cost Adjustment','Scope correction',250]"`
2. Re-apply the decision via controlled transition:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_contract_variation --args "['<VARIATION>','Approved','approved by accounting officer']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Variation Review`
  - `status = Draft`

### G) Claim decision creates a proceedings session
1. Create a `Claim`
2. Transition claim to Under Review and Approved using:
   - `transition_claim(..., 'Under Review', ...)`
   - `transition_claim(..., 'Approved', ...)`

Expected:
- A new `Governance Session` is created:
  - `session_type = Claim Decision`

### H) Dispute resolution creates a proceedings session
1. Create a `Dispute Case`
2. Resolve dispute:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_dispute_case --args "['<DISPUTE>','Resolved','settlement reached']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Dispute Resolution`

### I) Stop Work issuance creates a proceedings session
1. Create a `Dispute Case`
2. Set recommendations:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_dispute_recommendations --args "['<DISPUTE>',1,1]"`
3. Issue Stop Work Order:
   - `bench --site kentender.midas.com execute kentender.kentender.api.issue_stop_work_order --args "['<DISPUTE>','Stop work due to non-compliance']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Dispute Session`

### J) Monthly monitoring review creates a proceedings session
1. Generate monthly monitoring reports:
   - `bench --site kentender.midas.com execute kentender.kentender.api.create_monthly_contract_monitoring_reports`
2. Mark report as reviewed:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_set_monthly_contract_monitoring_report_status --args "['<MCMR_NAME>','Reviewed']"`

Expected:
- A new `Governance Session` is created:
  - `session_type = Monitoring Review`

## K) Claim penalty/liquidated damages automation (FRS 4.14)
Preconditions:
- Contract is `Active`
- At least one milestone `Task` exists with `is_contract_milestone = 1`
- `Contract.end_date` is set in the past

1. Choose a milestone `Task` and complete it:
   - set `supplier_confirmed = 1`
   - set `milestone_status = Completed`
2. Create a penalty claim:
   - `bench --site kentender.midas.com execute kentender.kentender.api.try_create_claim --args "['<CONTRACT>','Procuring Entity','Liquidated Damages','Late completion LD']"`
3. Transition claim to `Approved`:
   - `bench --site kentender.midas.com execute kentender.kentender.api.transition_claim --args "['<CLAIM>','Approved','approving penalty auto-calculation']"`

Expected:
- `Claim.penalty_delay_days > 0`
- `Claim.penalty_rate_per_day` equals `kentender_penalty_rate_per_day` (default `1000`)
- `Claim.amount == Claim.penalty_delay_days * Claim.penalty_rate_per_day`
- `Claim.penalty_expected_completion_date == Contract.end_date`
- `Claim.penalty_actual_completion_date` derived from milestone task completion proxy

## SQL Verification Snippets (same as CLM UAT script)
```sql
SELECT name, contract, claim_by, claim_type, amount, status,
       penalty_delay_days, penalty_rate_per_day,
       penalty_expected_completion_date, penalty_actual_completion_date, penalty_formula
FROM `tabClaim` ORDER BY creation DESC LIMIT 10;

SELECT name, session_type, context_reference_doctype, context_reference_name
FROM `tabGovernance Session`
ORDER BY creation DESC LIMIT 10;

SELECT name, status, closeout_archived, closeout_archive_sequence, closeout_archive_ref
FROM `tabContract`
ORDER BY creation DESC LIMIT 10;
```

