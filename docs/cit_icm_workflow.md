# CIT & Inspection Committee workflows (FRS 4.3 / 4.6)

## Lifecycle

### Contract Implementation Team (CIT) member

| From | To | Who (typical) |
|------|-----|----------------|
| Proposed | Approved | **Accounting Officer** or System Manager |
| Proposed | Removed | **Accounting Officer**, **Head of Procurement**, or System Manager |
| Approved | Active | **Head of Procurement** or System Manager |
| Approved | Removed | AO, HoP, or System Manager |
| Active | Removed | AO, HoP, or System Manager |

New records must start as **unless** created by **System Manager**.

### Inspection Committee member

| From | To | Who (typical) |
|------|-----|----------------|
| Proposed | Approved | **Accounting Officer** or System Manager |
| Proposed | Dissolved | AO, HoP, or System Manager |
| Approved | Active | **Head of Procurement** or System Manager |
| Approved | Dissolved | AO, HoP, or System Manager |
| Active | Dissolved | AO, HoP, or System Manager |

Same **new record = Proposed** rule (System Manager exception).

## APIs (role-gated)

- `transition_cit_member(member_name, next_status, remarks=None)` → returns new status  
- `transition_inspection_committee_member(member_name, next_status, remarks=None)` → returns new status  

On **Approved** or **Active**, **`appointed_by`** / **`appointed_on`** are set if missing.

## Desk / `save`

Direct edits that change **`status`** are validated the same way: invalid transitions or wrong roles **throw** on save.

## Audit

Transitions call `log_ken_tender_audit_event` with actions `cit_member_transition` and `inspection_committee_member_transition`.

## Contract eligibility

Members can only be added while the **Contract** is in: Draft, Pending Supplier Signature, Pending Accounting Officer Signature, Active, or Suspended.
