# Milestones, Inspection/Certificates, and Governance Sessions (FRS 4.4/4.7/4.8 + Proceedings depth)

## Scope
This module covers:
- Contract milestone execution (ERPNext `Task` milestones)
- The governance “minutes” proceedings auto-created for key events
- Inspection report and certificate gating chain used to allow invoicing

## Milestone completion rules
Milestones are stored in `Task` with:
- `is_contract_milestone = 1`

Rules enforced:
- Supplier confirmation (`supplier_confirmed`) is required before allowing milestone completion.

Implementation:
- `apps/kentender/kentender/api.py` -> `validate_task_milestone()` (hook on `Task`)

## Governance Sessions: what is created automatically
On the “first occurrence” of key events, the system creates a **draft** `Governance Session` plus a starter `Session Agenda Item`.

Key triggers:
- Milestone completion (`Task` becomes `Completed`)
- Contract site handover (`Contract.handover_completed`)
- Inspection Report submission
- Acceptance Certificate decisions
- Contract Variation decisions
- Claim decisions
- Dispute resolution
- Stop Work order issuance
- Monthly monitoring report status -> `Reviewed`

Implementation (session auto-creators):
- `apps/kentender/kentender/api.py`
  - `_maybe_create_governance_session_for_milestone_completed(...)`
  - `_maybe_create_governance_session_for_contract_variation_decision(...)`
  - `_maybe_create_governance_session_for_claim_decision(...)`
  - `_maybe_create_governance_session_for_dispute_resolution(...)`
  - `_maybe_create_governance_session_for_stop_work_issued(...)`
  - `_maybe_create_governance_session_for_monthly_monitoring_report(...)`

## Governance Sessions controls (Layer 2 depth already implemented)
Core governance guarantees:
- Quorum is enforced before Approved/Locked outcomes.
- Minutes workflow transitions require correct prerequisites.
- When a governance session is `Locked`, it and its linked children become immutable.
- Resolution gating: `Session Resolution` cannot advance to Approved/Implemented/Closed unless the parent `Governance Session` is `Approved` or `Locked`.

Implementation:
- `apps/kentender/kentender/api.py` -> `validate_governance_session()` + child validation functions
- `transition_governance_session()` for controlled transitions
- `validate_session_resolution()` for parent-state gating

## Inspection and certificates: gating chain
High-level rule:
- An `Acceptance Certificate` cannot be issued unless its required inspection chain exists and is submitted in the proper state.

Implementation:
- `apps/kentender/kentender/api.py` -> `validate_acceptance_certificate()` and related helpers

Operational expectation for users:
- Ensure the `Quality Inspection` and `Inspection Test Plan` / `Inspection Report` links are in place before issuing certificates.

## Key governance-related bench helper APIs (UAT / automation)
- `kentender.kentender.api.try_add_session_participant(session_name, participant_role, attendance_status)`
- `kentender.kentender.api.schedule_governance_session(session_name)`
- `kentender.kentender.api.start_governance_session(session_name)`
- `kentender.kentender.api.draft_governance_session_minutes(session_name)`
- `kentender.kentender.api.submit_governance_session_minutes(session_name)`
- `kentender.kentender.api.approve_governance_session(session_name)`
- `kentender.kentender.api.lock_governance_session(session_name)`
- `kentender.kentender.api.try_create_session_resolution(session_name, agenda_item, resolution_type, resolution_text, status)`
- `kentender.kentender.api.try_set_session_resolution_status(session_resolution_name, next_status)`

For deeper procurement proceedings details, see:
- `apps/kentender/docs/governance_sessions_mvp.md`

