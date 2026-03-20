# Contract Signing, Activation, and Archive-grade Closeout (FRS 4.1/4.2/4.18)

## Scope
This module explains:
- How contracts become `Active` (signatures + evidence)
- How contracts become `Closed` (closeout prerequisites)
- How the system produces an immutable closeout archive snapshot and locks the contract record

## Core guarantees (non-negotiable gates)
### Contract activation (to `Active`)
When a `Contract` is set to `Active`:
- Both supplier signature and accounting officer signature must be completed.
- If `signature_mode = External Verified`, external verification evidence (hash + timestamp fields) must be present.

Implementation: `apps/kentender/kentender/api.py` -> `validate_contract()`.

### Contract closeout (to `Closed`)
When transitioning a `Contract` to `Closed`, the system checks:
- `final_acceptance_certificate` exists
- `all_payments_completed = 1`
- `handover_completed = 1`

If checks pass:
- The system creates an immutable `Contract Closeout Archive` snapshot.
- It sets closeout marker fields on the `Contract`.

Implementation:
- `apps/kentender/kentender/api.py` -> `_maybe_create_contract_closeout_archive()`
- Triggered from `validate_contract()` when status transitions to `Closed`.

## Archive-grade immutability (what cannot be changed)
If a contract is `Closed` and its closeout has been archived:
- Further saves on the same contract are blocked unless `frappe.flags.in_override` is enabled for controlled operations.

Also:
- `Contract Closeout Archive` records are create-only:
  - cannot be edited after creation
  - cannot be deleted

Implementation:
- `validate_contract_closeout_archive()`
- `prevent_delete_contract_closeout_archive()`

## Key data fields to validate (audit / traceability)
On `Contract`:
- `status`
- `closeout_archived`
- `closeout_archived_on`
- `closeout_archive_ref`
- `closeout_archive_sequence`

On `Contract Closeout Archive`:
- `snapshot_json` (immutable JSON snapshot payload)

## Whitelisted / bench helper entry points (used in UAT)
- `kentender.kentender.api.create_contract_from_award(tender_name, submission_name=None)`
- `kentender.kentender.api.sign_contract(contract_name, signer_role, signature_token=None)`
- `kentender.kentender.api.try_set_contract_status(contract_name, status, final_acceptance_certificate=None, all_payments_completed=0, handover_completed=0)`
- `kentender.kentender.api.get_contract_closeout_readiness(contract_name)`

## Where to look for the closeout snapshot
Use the `Contract` fields:
- `closeout_archive_ref` to locate the corresponding `Contract Closeout Archive`

In archive records, the authoritative audit data is:
- `snapshot_json`

