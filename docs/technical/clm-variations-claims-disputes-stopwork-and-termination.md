# Variations, Claims, Disputes/Stop Work, and Termination + DLP + FRS 4.17/4.19

## Scope
This module covers:
- Contract variations and second-level approval for high-impact cases (FRS 4.16)
- Claims, including deterministic penalty/liquidated damages automation (FRS 4.14)
- Dispute lifecycle controls and Stop Work issuance + contract suspension/resume (FRS 4.15)
- Termination settlement evidence bundle enforcement (FRS 4.17)
- DLP lifecycle integration and closeout readiness effects (FRS 4.19)

## Contract variations (with second-level approval for high impact)
Rules:
- Variations require justification and required impact fields depending on variation type.
- If a variation is high-impact (based on configurable thresholds):
  - it cannot transition to `Approved` until `second_level_approved = 1`

Implementation:
- `apps/kentender/kentender/api.py`
  - `validate_contract_variation()`
  - `transition_contract_variation()`
  - `second_approve_contract_variation()`

Configurable thresholds:
- `kentender_variation_high_financial_impact_threshold`
- `kentender_variation_high_time_extension_days_threshold`

Second-level role:
- `kentender_variation_second_level_approval_role` (default: Head of Finance)

## Claims and deterministic penalty/liquidated damages automation
Applies to:
- Claim types: `Liquidated Damages`, `Performance Penalty`
- Claim by: `Procuring Entity`

Behavior:
- During `Claim` validation, the system auto-calculates:
  - penalty delay days (expected vs actual proxy completion date)
  - penalty amount (delay_days * rate_per_day)
  - trace fields: `penalty_rate_per_day`, `penalty_formula`, `penalty_expected_completion_date`,
    `penalty_actual_completion_date`, `penalty_delay_days`

Retention release effect:
- `get_retention_release_readiness()` and `release_contract_retention()` block release when unresolved approved penalty claims exist.

Implementation:
- `apps/kentender/kentender/api.py` -> `_maybe_calculate_penalty_for_claim()`
- `validate_claim()`
- `get_retention_release_readiness()`, `release_contract_retention()`

## Disputes and Stop Work issuance
Stop Work issuance requires:
- Accounting Officer role
- CIT recommendation present
- Head of Procurement recommendation present
- No duplicate Stop Work already issued for that dispute
- Contract is not already Closed/Terminated

Contract state effects:
- First active Stop Work suspends the contract.
- With multiple disputes, contract can only resume when the last active Stop Work is withdrawn.
- Resume status is stored so non-Stop-Work suspensions are not disturbed.

Implementation:
- `apps/kentender/kentender/api.py`
  - `issue_stop_work_order(dispute_name, reason)`
  - `withdraw_stop_work_order(dispute_name, reason)`
  - `validate_dispute_case()` evidence checks when `stop_work_order_issued = 1`

## Termination evidence bundle enforcement (settlement completion gate)
Settlement completion (`Termination Record` -> `Completed`) is blocked unless all checklist items are satisfied:
- `handover_completed = 1`
- `discharge_document_reference` is set
- `legal_advice_reference` is set
- `notice_issued_to_supplier = 1`
- `supporting_documents_provided = 1`

Bench helper:
- `kentender.kentender.api.try_set_termination_record_evidence(...)`

Implementation:
- `apps/kentender/kentender/api.py`
  - `transition_termination_record_settlement()`

## DLP lifecycle integration
Key functions:
- `start_defect_liability_period(contract_name)`
- `try_create_defect_liability_case(...)`
- contract reopen behavior on defect updates

Operational expectation:
- DLP completion affects retention release due/readiness and contract closeout flow.

Implementation:
- `apps/kentender/kentender/api.py`

