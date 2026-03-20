# Invoices, Payments, and Retention Governance (FRS 4.9/4.10/4.12)

## Scope
This module covers:
- Invoice submission gating by acceptance certificates
- Retention deduction posting
- Retention release readiness checks and execution blocking

## Invoice gate (must have valid certificate)
Before a `Purchase Invoice` is accepted for contract-linked processing:
1. The invoice must reference an `Acceptance Certificate`
2. The certificate must be submitted and in workflow state `Issued`
3. The certificate decision must be `Approved`
4. The certificate must belong to the same `Contract`

Implementation:
- `apps/kentender/kentender/api.py` -> `validate_purchase_invoice_certificate()`

## Retention deduction on invoice submit
When submitting a contract-linked invoice:
- Retention deduction entries are posted into `Retention Ledger`

Operational expectation:
- You will see ledger rows with held retention balances.

## Retention release governance (blocked until conditions are met)
Two key functions:
- `get_retention_release_readiness(contract_name)` (exposes blockers)
- `release_contract_retention(contract_name, amount=None, remarks=None)` (executes release)

What blocks release:
- Contract/closeout prerequisites not satisfied
- DLP not completed
- Pending approved penalty/LD claims (deterministic penalty automation already integrated)

Implementation:
- `apps/kentender/kentender/api.py`
  - `get_retention_release_readiness()`
  - `release_contract_retention()`

## Key data to inspect for retention compliance
On `Contract`:
- `status`, `closeout_archived`, `dlp_status`
On `Retention Ledger`:
- held deduction rows and release rows by contract
On `Claim`:
- penalty/LD type claims in `Approved` status

## Relevant bench/UAT helpers
- `try_create_contract_purchase_invoice(contract_name, amount, use_certificate=0, certificate_name=None)`
- `submit_purchase_invoice_for_test(invoice_name)`
- `release_contract_retention(contract_name, amount, remarks)`
- `get_retention_release_readiness(contract_name)`

