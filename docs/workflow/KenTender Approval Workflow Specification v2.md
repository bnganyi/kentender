# KenTender Approval Workflow Specification v20. Purpose

This specification defines how approval-controlled business objects in KenTender must behave, including:

- approval stages
- state transitions
- role responsibilities
- dynamic route resolution
- approval records
- backend enforcement
- UI behavior for approval-controlled fields

**Engineering tracker:** [WF Implementation Tracker](WF%20Implementation%20Tracker.md) (WF-001–WF-016 vs this specification).

This applies across:

- requisitions
- plans
- tenders
- evaluation reports
- awards
- contracts
- acceptance
- complaints
- variations
- other approval-driven objects

# 1\. Core Principles

## 1.1 Stable object lifecycle, dynamic approval path

Each object must have a **stable lifecycle**, but the **approval route may vary** based on policy.

Example:

- all acceptance records may use the same high-level states
- but a simple goods acceptance may use 1 approver
- a complex works acceptance may use inspector + professional opinion + committee

So:

- **Lifecycle = stable**
- **Approval route = dynamic**

## 1.2 All approval mutations are backend-controlled

Users do not directly change approval fields.

All approval actions must go through explicit backend services such as:

- submit
- approve
- reject
- return
- finalize
- publish
- activate
- accept
- close

## 1.3 Every approval action must create a formal record

Every approval or return action must create an append-only action record with:

- actor
- role
- stage
- decision
- comments
- previous state
- new state
- timestamp

## 1.4 Separation of duty must be enforced in services

Role conflicts must not be handled only in UI.

Examples:

- evaluator cannot final-approve award
- supplier cannot participate in internal acceptance
- requisitioner may not approve own requisition, subject to policy

## 1.5 Assignment-based controls apply where required

For sensitive processes, role alone is insufficient.

Examples:

- evaluation
- opening
- complaint review
- specialized inspection
- committee-based acceptance

# 2\. Approval Architecture

## 2.1 Approval architecture layers

KenTender approval behavior is composed of 4 layers:

**Layer A — Object lifecycle**

Stable states of the business object.

**Layer B — Approval route policy**

Rules that determine which approval route applies.

**Layer C — Approval route instance**

The actual approval chain created for a specific record.

**Layer D — Action authorization**

Who may act on the current step.

## 2.2 Stable lifecycle vs dynamic routing

**Example: Acceptance Record lifecycle**

Possible states:

- Draft
- Pending Technical Review
- Pending Acceptance Approval
- Accepted
- Partially Accepted
- Rejected

These states remain stable.

But route varies:

**Simple goods**

- Inspector decides
- GRN allowed

**Complex medical equipment**

- Inspector
- Professional opinion
- Acceptance committee

**Works**

- Inspector
- Engineer/consultant certification
- Committee approval

**Scientific/lab-tested goods**

- Sample/lab result
- Technical reviewer
- Approval step

That is the required model.

# 3\. Approval-Controlled Fields Rule

## 3.1 Rule

**All approval-controlled fields are system-managed and must never be directly editable by end users.**

This includes fields such as:

- workflow_state
- approval_status
- status where lifecycle-controlled
- current_approval_step
- route_status
- is_locked
- final_approval_datetime
- acceptance_status
- publication_status
- standstill_status
- budget_reservation_status
- commitment_status

## 3.2 User behavior

Users may only trigger explicit actions:

- Submit
- Approve
- Reject
- Return
- Finalize
- Publish
- Activate
- Accept
- Close
- Release
- Reopen, where policy allows

They do not type status values into fields.

## 3.3 System behavior

The backend service must:

- validate actor
- validate current state
- validate route step
- apply state transition
- create approval/action record
- update approval-controlled fields
- trigger side effects
- emit audit events

## 3.4 UI behavior

Approval-controlled fields must be:

- read-only on forms
- non-editable in quick entry
- excluded from inline list editing
- not mass-updatable through normal user actions
- displayed clearly to users as current status indicators

## 3.5 Import and patch behavior

Approval-controlled fields must not be casually mutated by:

- imports
- data patch scripts
- ad hoc bulk updates
- client-side scripts

Any administrative override must be:

- restricted
- auditable
- exceptional

**4\. Approval Route Model**

# 4.1 Workflow Policy

Determines when a route applies.

**Suggested fields**

- policy_code
- object_type
- category
- contract_type
- procurement_method
- threshold_min
- threshold_max
- complexity_level
- sector
- requires_professional_opinion
- requires_committee
- risk_level
- active

## 4.2 Approval Route Template

Reusable route pattern.

**Suggested fields**

- template_code
- template_name
- object_type
- description
- active

## 4.3 Approval Route Template Step

Defines the steps inside the template.

**Suggested fields**

- parent_template
- step_order
- step_name
- actor_type
- role_required
- assignment_required
- professional_signoff_required
- committee_required
- can_approve
- can_reject
- can_return
- requires_comments
- terminal_on_reject

## 4.4 Approval Route Instance

Created per business object.

**Suggested fields**

- object_type
- object_id
- template_used
- status
- current_step_no
- resolved_on
- resolved_by_policy

## 4.5 Approval Step Instance

Created per resolved route step.

**Suggested fields**

- route_instance
- step_order
- step_name
- assigned_role
- assigned_user
- status
- decision
- acted_on
- comments

# 5\. Dynamic Route Resolution Rules

## 5.1 General rule

When an approval-controlled object enters its first approval state, the system must:

1.  evaluate applicable workflow policy
2.  resolve the correct approval template
3.  create route instance
4.  create step instances
5.  set current approval step
6.  move object into the first pending approval state

## 5.2 Resolution inputs

Possible inputs for route selection include:

- goods / works / services
- threshold value
- emergency flag
- complexity level
- special sector
- professional signoff requirement
- lab/sample requirement
- committee requirement
- deviation present
- complaint hold present

## 5.3 Route resolution examples

**Example A — Simple goods acceptance**

Conditions:

- goods
- low complexity
- no professional signoff required

Route:

1.  Inspector approval

**Example B — Complex technical equipment**

Conditions:

- goods
- high complexity
- professional opinion required

Route:

1.  Inspector
2.  Technical specialist / professional opinion
3.  Acceptance approval

**Example C — Works completion acceptance**

Conditions:

- works
- consultant certification required
- committee required

Route:

1.  Inspector
2.  Engineer/consultant certification
3.  Acceptance committee chair
4.  Committee approval

**Example D — High-value award**

Conditions:

- award value exceeds threshold

Route:

1.  Procurement review
2.  Accounting officer final approval

Optional extension:  
3\. board / authority approval if policy requires

# 6\. Global Approval Action Record

## 6.1 Required record

Every approval step action must create an append-only record.

**Suggested fields**

- object_type
- object_id
- route_instance
- step_instance
- workflow_stage
- action
- decision
- actor_user
- actor_role
- timestamp
- comments
- previous_state
- new_state
- is_final_action

## 6.2 Action types

Supported actions:

- Submit
- Approve
- Reject
- Return
- Finalize
- Publish
- Activate
- Accept
- Close
- Release
- Override, if exceptional administrative process exists

# 7\. Object-Specific Workflow Specifications

## 7.1 Purchase Requisition

**Stable states**

- Draft
- Submitted
- Pending HOD Approval
- Pending Finance Approval
- Approved
- Rejected
- Returned for Amendment

**Standard route**

1.  HOD approval
2.  Finance approval

**Actions**

**Draft**

- Requisitioner may edit and submit

**Pending HOD Approval**

- HOD may:
    - Approve → Pending Finance Approval
    - Reject → Rejected
    - Return → Returned for Amendment

**Pending Finance Approval**

- Finance may:
    - Approve → Approved
    - Reject → Rejected
    - Return → Returned for Amendment

**Side effect on final approval**

- budget reservation process must run
- requisition becomes planning-eligible

## 7.2 Procurement Plan

**Stable states**

- Draft
- Submitted
- Approved
- Active
- Rejected
- Returned

**Standard route**

1.  Procurement review
2.  Planning/authority approval if policy requires

**Side effect on activation**

- plan items become tender-eligible

## 7.3 Tender

**Stable states**

- Draft
- Submitted for Review
- Approved
- Published
- Withdrawn
- Cancelled
- Closed

**Standard route**

1.  Procurement review
2.  Approval
3.  Publication

**Publish rules**

Tender cannot publish unless:

- source plan item valid
- required criteria exist
- required documents exist
- required visibility rules exist
- deadlines are coherent

## 7.4 Evaluation Report

**Stable states**

- Draft
- Submitted
- Accepted
- Returned

**Standard route**

1.  Evaluation Chair finalizes
2.  Evaluation report submitted
3.  Review/acceptance by authorized downstream role

**Rules**

- evaluator assignment required
- conflict declaration required before scoring
- only chair may finalize report
- evaluators cannot approve award

## 7.5 Award Decision

**Stable states**

- Draft
- Submitted
- Pending Final Approval
- Approved
- Rejected
- Returned
- Standstill Active
- Finalized

**Standard route**

1.  Procurement prepares/submits
2.  Accounting Officer final-approves

**Side effects**

On approval:

- award notifications generated
- standstill initialized if required

On standstill completion:

- object may become contract-ready

## 7.6 Contract

**Stable states**

- Draft
- Submitted
- Approved
- Pending Signature
- Signed
- Active
- Suspended
- Terminated
- Closed

**Standard route**

1.  Contract review/approval
2.  Signature
3.  Activation

**Rules**

- no activation before signing
- no contract creation if standstill/hold blocks readiness
- commitment logic must run at defined commitment point

## 7.7 Acceptance Record

**Stable states**

- Draft
- Pending Technical Review
- Pending Acceptance Approval
- Accepted
- Partially Accepted
- Rejected

**Dynamic route**

Resolved from policy.

Examples:

- simple goods: inspector only
- technical goods: inspector + professional opinion
- works: inspector + consultant + committee
- scientific goods: test result + technical reviewer + approval

**Rules**

- mandatory failures must block full acceptance
- partial acceptance must be explicit
- GRN must not proceed before required acceptance outcome

## 7.8 Contract Variation

**Stable states**

- Draft
- Submitted
- Pending Approval
- Approved
- Rejected
- Applied
- Cancelled

**Dynamic route inputs**

- value increase
- extension days
- scope change
- threshold
- emergency flag
- budget impact

## 7.9 Complaint Decision

**Stable states**

- Draft
- Admissibility Pending
- Under Review
- Decision Draft
- Decided
- Appealed
- Closed

**Dynamic route inputs**

- complaint type
- stage affected
- hold required
- review panel requirement
- appeal route requirement

# 8\. Workflow Authorization Rules

## 8.1 Authorization inputs

Every action must validate:

- actor role
- actor assignment, if required
- current object state
- current route step
- separation-of-duty rules
- policy-specific preconditions

## 8.2 Authorization outputs

Action results must be one of:

- allowed
- denied: wrong role
- denied: wrong state
- denied: wrong assignment
- denied: SoD conflict
- denied: unmet precondition
- denied: sensitivity restriction

# 9\. Separation of Duty Rules

## 9.1 Mandatory rules

At minimum:

- requisitioner cannot approve own requisition, subject to policy
- evaluator cannot approve award
- supplier cannot perform internal approval actions
- opening actor cannot open before deadline
- contract cannot activate before signing
- complaint reviewer should not be same actor as original disputed decision-maker where policy prohibits

## 9.2 Enforcement point

All SoD rules must be enforced:

- in backend services
- not only in UI visibility

# 10\. UI Rules

## 10.1 Button visibility

Buttons should appear only when:

- user has required role
- object is in correct state
- assignment is valid
- preconditions are met

## 10.2 Read-only approval fields

Fields such as:

- workflow state
- approval status
- current approval step
- route status  
    must be displayed but not directly editable.

## 10.3 Approval history visibility

Users with authorized access should see:

- approval history
- stage progression
- who acted
- comments
- timestamps

This is especially useful for:

- requisitions
- awards
- complaints
- contract variations

# 11\. Service-Layer Requirements

## 11.1 Mandatory pattern

Each approval-controlled object must be manipulated through explicit services.

Examples:

- submit_requisition(...)
- approve_requisition_hod(...)
- approve_requisition_finance(...)
- submit_evaluation_report(...)
- final_approve_award(...)
- record_contract_signature(...)
- activate_contract(...)
- submit_acceptance_decision(...)

## 11.2 Service responsibilities

Every service must:

1.  load object
2.  validate current state
3.  resolve or load approval route
4.  validate actor
5.  validate step
6.  enforce SoD
7.  apply transition
8.  create approval action record
9.  create audit event
10. apply downstream side effects

# 12\. Side-Effect Rules

## 12.1 Requisition final approval

- create or confirm budget reservation
- mark requisition planning-eligible

## 12.2 Tender publication

- set publication metadata
- open supplier visibility

## 12.3 Award approval

- generate notifications
- start standstill, where required

## 12.4 Contract activation

- trigger commitment logic if designed at activation point
- make inspection/delivery lifecycle available

## 12.5 Acceptance approval

- unlock GRN/store flow if accepted
- update contract progress through controlled service path

## 12.6 Complaint hold

- must block downstream progression until resolved or released

# 13\. Error and Return Behavior

## 13.1 Reject

Reject moves object to a terminal or blocked state unless policy allows restart.

## 13.2 Return

Return sends object back for correction without destroying history.

## 13.3 Reopen

Reopen should be exceptional and policy-controlled, not default behavior.

**14\. Audit Requirements**

Every state transition must record:

- object
- previous state
- new state
- action
- actor
- role
- timestamp
- route step
- comments
- side effects triggered

This is mandatory for audit-grade systems.

**15\. Recommended Initial Implementation Scope**

Implement dynamic approval routing first for:

- Acceptance
- Contract Variation
- Complaint Review
- High-value Award Approval

Keep simpler, fixed-stage routes initially for:

- Requisition
- Basic Planning
- Basic Tender Approval

That gives you flexibility where it is most needed without overcomplicating the entire system too early.

**16\. Final Design Rule**

**Users do not edit approval state. Users perform actions. The system changes state.**

That should be the governing principle across KenTender.

**17\. Recommended Next Artifact**

The next best step is:

**Cursor Workflow Implementation Pack v2**

This should implement:

- approval route policy model
- route template model
- route instance model
- approval action record model
- service-layer transition helpers
- read-only approval state enforcement

That is the natural implementation follow-on from this spec.