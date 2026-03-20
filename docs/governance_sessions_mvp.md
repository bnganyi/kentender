# Governance Sessions MVP (Proceedings MVP)

## Goal
Provide a legally defensible, audit-friendly structure to record official procurement deliberations (proceedings) as structured records:
- `Governance Session`
- `Session Agenda Item`
- (next iterations) `Session Resolution`, `Session Action`

This MVP focuses on controlled governance and traceability for key CLM events.

## Data model (module)
### `Governance Session`
Fields (key):
- `status`: `Draft` → `Scheduled` → `In Session` → `Minutes Drafted` → `Under Review` → `Approved` → `Locked` (and `Cancelled`)
- `context_type`: currently `Procurement`
- `context_reference_doctype` / `context_reference_name`: canonical reference for the session context
- `session_type`: e.g. `CIT Meeting`, `Inspection Session`, `Dispute Session`, `Monitoring Review`, `Site Handover`
- `meeting_date`

### `Session Agenda Item`
Fields (key):
- `session` (link)
- `subject`
- `discussion`
- `decision_required`

## Governance rules (hardening)
1. **Manual status changes are blocked** unless executed via the whitelisted transition APIs (server-side controlled paths).
2. **`Locked` sessions are immutable**
   - Changing the parent session after locking is blocked.
   - Editing children (`Session Agenda Item`, `Session Resolution`, `Session Action`) is blocked once the parent session is `Locked`.

## What gets created automatically (plain language)
To reduce manual duplication and keep audit evidence together, KenTender creates an initial “proceedings” record automatically in these moments:

1. **Milestone verification (milestone completion)**
   - When a milestone `Task` is changed to `milestone_status = Completed` the *first time*,
   - the system creates a new `Governance Session` in `Draft` status with:
     - `session_type = CIT Meeting`
     - context pointing to the milestone `Task`
   - It also creates one `Session Agenda Item` to start the formal verification record.

2. **Site handover (handover completion)**
   - When a `Contract` is updated with `handover_completed` from `0` to `1`,
   - the system creates a new `Governance Session` in `Draft` status with:
     - `session_type = Site Handover`
     - context pointing to the `Contract`
   - It also creates one `Session Agenda Item` to record the handover discussion.

3. **Inspection session (inspection report submission)**
   - When an `Inspection Report` is submitted the *first time*,
   - the system creates a new `Governance Session` in `Draft` status with:
     - `session_type = Inspection Session`
     - context pointing to the `Inspection Report`
   - It also creates one `Session Agenda Item` to record the inspection outcome.

4. **Acceptance committee sitting (acceptance certificate decision)**
   - When an `Acceptance Certificate` is moved into a decision state (`workflow_state` becomes `Issued` or `Rejected`) the *first time*,
   - the system creates a new `Governance Session` in `Draft` status with:
     - `session_type = Acceptance Committee Sitting`
     - context pointing to the `Acceptance Certificate`
   - It also creates one `Session Agenda Item` to record the committee decision.

5. **Variation / Claim / Dispute / Stop-work recommendation**
   - When a `Contract Variation` is decided (`status` becomes `Approved` or `Rejected`), a draft `Governance Session` is created with `session_type = Variation Review` (context = that variation).
   - When a `Claim` is decided (`status` becomes `Approved` or `Rejected`), a draft `Governance Session` is created with `session_type = Claim Decision` (context = that claim).
   - When a `Dispute Case` is resolved (`status` becomes `Resolved`), a draft `Governance Session` is created with `session_type = Dispute Resolution` (context = that dispute).
   - When a `Stop Work Order` is issued for a `Dispute Case`, a draft `Governance Session` is created with `session_type = Dispute Session` (context = that dispute).

6. **Monthly monitoring review**
   - When a `Monthly Contract Monitoring Report` is updated to `status = Reviewed` the *first time*,
   - the system creates a new draft `Governance Session` with `session_type = Monitoring Review` and a starter `Session Agenda Item`.

To avoid duplicates, KenTender checks whether a matching session already exists (using the same context reference + session type). If it exists, it does nothing.

## Whitelisted server APIs
All transitions write an audit comment to `KenTender Audit Event`.

- `kentender.kentender.api.transition_governance_session(session_name, next_state, remarks=None)`
- `kentender.kentender.api.schedule_governance_session(session_name, remarks=None)`
- `kentender.kentender.api.start_governance_session(session_name, remarks=None)`
- `kentender.kentender.api.draft_governance_session_minutes(session_name, remarks=None)`
- `kentender.kentender.api.submit_governance_session_minutes(session_name, remarks=None)`
- `kentender.kentender.api.approve_governance_session(session_name, remarks=None)`
- `kentender.kentender.api.lock_governance_session(session_name, remarks=None)`
- `kentender.kentender.api.sign_session_item(session_name, signer_role, target_type, target_name='', method_name='OTP')`
- `kentender.kentender.api.get_procurement_unlock_actions_for_resolution(resolution_name)`

Note: transition APIs are routed via **template-expected roles**, with **`System Manager`** always permitted.

## UAT (high level)
See `CLM UAT Script.md` → **UAT-10 Governance Sessions MVP** for end-to-end steps.

