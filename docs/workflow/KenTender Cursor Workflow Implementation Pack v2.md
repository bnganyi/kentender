# KenTender Cursor Workflow Implementation Pack v2

**Implementation status tracker:** [`WF Implementation Tracker.md`](WF%20Implementation%20Tracker.md) (WF-001–WF-016).

**Implementation goal**

Build a reusable workflow/approval engine that can support both:

- **fixed routes**  
    like requisition approvals

and

- **dynamic routes**  
    like acceptance, contract variation, complaint review, high-value awards

**Delivery order**

Build in this order:

1.  WF-001 — workflow engine architecture skeleton
2.  WF-002 — approval-controlled field protection layer
3.  WF-003 — global approval action record model
4.  WF-004 — workflow policy model
5.  WF-005 — approval route template model
6.  WF-006 — approval route instance model
7.  WF-007 — workflow route resolver service
8.  WF-008 — workflow action execution service
9.  WF-009 — separation-of-duty enforcement helpers
10. WF-010 — side-effect hook framework
11. WF-011 — requisition workflow implementation
12. WF-012 — award workflow implementation
13. WF-013 — contract workflow implementation
14. WF-014 — acceptance dynamic workflow implementation
15. WF-015 — complaint dynamic workflow implementation
16. WF-016 — workflow test suite and verification fixtures

**Global implementation rules for Cursor**

Before the stories, these rules apply to all of them:

- never let users edit approval-controlled fields directly
- never change workflow state by raw field mutation in application logic
- always create an approval action record for material transitions
- always validate:
    - role
    - current state
    - current route step
    - assignment if required
    - SoD conflicts
- always emit audit events for material transitions
- keep workflow engine logic in backend services
- do not bury approval logic in client scripts or ad hoc DocType methods

**WF-001 — Create workflow engine architecture skeleton**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow-engine architecture task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-001
- Title: Create workflow engine architecture skeleton

Context:

- KenTender requires a reusable workflow/approval engine supporting:
    - stable object lifecycle states
    - dynamic approval routing
    - backend-controlled transitions
    - approval action records
    - side-effect hooks
- The implementation must support requisitions, awards, contracts, acceptance, complaints, and future approval-controlled objects.

Task:  
Create the workflow engine architecture skeleton in kentender_core.

Requirements:

1.  Add a workflow architecture package structure such as:
    - workflow_engine/
    - workflow_engine/policies.py
    - workflow_engine/routes.py
    - workflow_engine/actions.py
    - workflow_engine/safeguards.py
    - workflow_engine/hooks.py
2.  Add a developer-facing architecture note that explains:
    - stable lifecycle vs dynamic route
    - why approval-controlled fields are backend-managed
    - how downstream apps should integrate
3.  Keep the skeleton reusable across apps.

Constraints:

- Do not implement all business rules yet.
- Do not build one-off logic for one DocType only.
- Keep this foundational and clean.

Acceptance criteria:

- workflow engine skeleton exists
- architecture note exists
- later workflow stories have clear integration points

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  final package structure

**WF-002 — Implement approval-controlled field protection layer**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow safety task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-002
- Title: Implement approval-controlled field protection layer

Context:

- KenTender approval-controlled fields must be system-managed and never directly editable by normal user actions.
- This includes fields such as:
    - workflow_state
    - approval_status
    - current_approval_step
    - route_status
    - is_locked
    - final_approval_datetime
    - acceptance_status
    - publication_status
    - standstill_status
    - budget_reservation_status
    - commitment_status

Task:  
Implement a reusable protection layer for approval-controlled fields.

Requirements:

1.  Add a reusable mechanism to declare approval-controlled fields per DocType or DocType family.
2.  Prevent unauthorized direct mutation of these fields outside approved service context.
3.  Provide a controlled internal override mechanism for workflow services only.
4.  Add tests for:
    - unauthorized direct field mutation blocked
    - workflow-service-authorized mutation allowed

Constraints:

- Do not rely only on frontend read-only flags.
- Keep this backend-enforced.
- Keep the mechanism maintainable and explicit.

Acceptance criteria:

- approval-controlled field protection exists
- unauthorized direct changes are blocked
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  protection mechanism summary

**WF-003 — Implement global approval action record model**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow audit model task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-003
- Title: Implement global approval action record model

Context:

- Every approval or return action in KenTender must create an append-only action record.
- This model must be reusable across requisitions, awards, contracts, acceptance, complaints, and future approval-controlled objects.

Task:  
Implement the global Approval Action Record model.

Suggested fields:

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

Requirements:

1.  Create the model in a reusable location.
2.  Keep it append-only in practical behavior.
3.  Add tests for valid record creation and linkage basics.

Constraints:

- Do not implement all workflow actions here.
- Keep the model general-purpose.

Acceptance criteria:

- approval action record model exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  model summary

**WF-004 — Implement workflow policy model**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow policy modeling task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-004
- Title: Implement workflow policy model

Context:

- Dynamic approval routes in KenTender are selected based on policy inputs such as:
    - object_type
    - category
    - contract_type
    - procurement_method
    - threshold range
    - complexity
    - sector
    - professional signoff requirement
    - committee requirement
    - risk level

Task:  
Implement the Workflow Policy model.

Suggested fields:

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
- linked_template

Requirements:

1.  Keep the model expressive enough for dynamic route selection.
2.  Keep it configuration-oriented, not one-off hardcoded logic.
3.  Add tests for valid policy creation and representative matching intent fields.

Constraints:

- Do not implement full route resolution here.
- Keep the model lean but future-proof.

Acceptance criteria:

- workflow policy model exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  policy model summary

**WF-005 — Implement approval route template model**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow template modeling task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-005
- Title: Implement approval route template model

Context:

- KenTender needs reusable approval route templates such as:
    - Simple Goods Acceptance
    - Complex Technical Acceptance
    - Works Acceptance with Professional Opinion
    - High-Value Award Approval
    - Complaint Review Route

Task:  
Implement:

1.  Approval Route Template
2.  Approval Route Template Step

Suggested route template fields:

- template_code
- template_name
- object_type
- description
- active

Suggested step fields:

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

Requirements:

1.  Keep templates reusable and explicit.
2.  Enforce unique step order per template.
3.  Add tests for valid template and step creation.

Constraints:

- Do not implement route instances yet.
- Keep step semantics readable and structured.

Acceptance criteria:

- route template model exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  template model summary

**WF-006 — Implement approval route instance model**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow runtime modeling task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-006
- Title: Implement approval route instance model

Context:

- When a record enters approval, KenTender must create a route instance for that specific object.

Task:  
Implement:

1.  Approval Route Instance
2.  Approval Step Instance

Suggested route instance fields:

- object_type
- object_id
- template_used
- status
- current_step_no
- resolved_on
- resolved_by_policy

Suggested step instance fields:

- route_instance
- step_order
- step_name
- assigned_role
- assigned_user
- status
- decision
- acted_on
- comments

Requirements:

1.  Keep the model suitable for dynamic approval execution.
2.  Allow active step tracking.
3.  Add tests for valid route instance creation and step instance creation.

Constraints:

- Do not implement the full resolver here.
- Keep runtime state explicit and auditable.

Acceptance criteria:

- route instance models exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  route instance summary

**WF-007 — Implement workflow route resolver service**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow route resolution service in a modular Frappe-based system called KenTender.

Story:

- ID: WF-007
- Title: Implement workflow route resolver service

Context:

- When an object enters approval, KenTender must resolve the correct approval route based on workflow policy and object attributes.

Task:  
Implement a reusable workflow route resolver service.

Requirements:

1.  Accept an object_type and object reference/input context.
2.  Evaluate applicable workflow policies.
3.  Resolve the correct route template.
4.  Create an approval route instance and step instances.
5.  Return a structured route resolution result.
6.  Add tests for representative cases:
    - simple fixed route
    - dynamic route by complexity
    - dynamic route by threshold
    - no valid route found

Constraints:

- Keep logic explainable and deterministic.
- Do not bury policy logic inside one-off domain code.

Acceptance criteria:

- route resolver exists
- route instances can be created from policy/template
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  supported route resolution patterns

**WF-008 — Implement workflow action execution service**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow execution service in a modular Frappe-based system called KenTender.

Story:

- ID: WF-008
- Title: Implement workflow action execution service

Context:

- KenTender workflow actions must be executed through a reusable backend service.

Task:  
Implement a reusable workflow action execution service.

Suggested service capabilities:

- submit_object_for_approval(...)
- approve_current_step(...)
- reject_current_step(...)
- return_current_step(...)
- finalize_route_if_complete(...)

Requirements:

1.  Validate current object state.
2.  Validate active route instance and current step.
3.  Validate actor role and assignment.
4.  Enforce SoD checks via helper layer.
5.  Apply state transition.
6.  Create Approval Action Record.
7.  Advance or close the route instance.
8.  Trigger side-effect hooks.
9.  Add tests for representative allow/deny and transition cases.

Constraints:

- Do not implement all domain-specific side effects here.
- Keep the engine generic and reusable.

Acceptance criteria:

- workflow action execution service exists
- transitions, action records, and route progression work
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  supported actions

**WF-009 — Implement separation-of-duty enforcement helpers**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow safeguard task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-009
- Title: Implement separation-of-duty enforcement helpers

Context:

- KenTender requires explicit SoD enforcement, including examples such as:
    - requisitioner cannot approve own requisition where policy applies
    - evaluator cannot approve award
    - supplier cannot perform internal approval actions
    - complaint reviewer should not be the original disputed decision-maker where policy requires

Task:  
Implement reusable SoD enforcement helpers.

Requirements:

1.  Support object-type-specific SoD rules.
2.  Make the checks usable by workflow execution services.
3.  Add tests for representative allow/deny cases.

Constraints:

- Do not hardcode only one role pair.
- Keep the logic extensible and readable.

Acceptance criteria:

- SoD helpers exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  SoD patterns supported

**WF-010 — Implement workflow side-effect hook framework**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow side-effect framework in a modular Frappe-based system called KenTender.

Story:

- ID: WF-010
- Title: Implement workflow side-effect hook framework

Context:

- Workflow completion or approval transitions in KenTender often trigger downstream effects, such as:
    - requisition approval -> budget reservation
    - award approval -> notification + standstill
    - contract activation -> commitment and progress availability
    - acceptance approval -> GRN eligibility

Task:  
Implement a reusable workflow side-effect hook framework.

Requirements:

1.  Provide a clean hook registration/execution pattern by object_type and action/stage.
2.  Make it easy for downstream apps to attach side-effect handlers.
3.  Ensure hooks run only after successful action execution.
4.  Add tests for representative hook registration and execution behavior.

Constraints:

- Do not implement every business side effect in this story.
- Keep the framework generic and deterministic.

Acceptance criteria:

- hook framework exists
- downstream integration is possible
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  hook execution model

**WF-011 — Implement requisition workflow using engine**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded domain workflow integration task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-011
- Title: Implement requisition workflow using engine

Context:

- Requisition uses a mostly fixed route:
    1.  HOD approval
    2.  Finance approval
- The object lifecycle includes:
    1.  Draft
    2.  Submitted
    3.  Pending HOD Approval
    4.  Pending Finance Approval
    5.  Approved
    6.  Rejected
    7.  Returned for Amendment

Task:  
Integrate Purchase Requisition with the workflow engine.

Requirements:

1.  Register/use a route template appropriate for requisitions.
2.  Implement service actions:
    - submit_requisition(...)
    - approve_requisition_hod(...)
    - approve_requisition_finance(...)
    - reject_requisition(...)
    - return_requisition(...)
3.  Enforce actor role and scope checks.
4.  Protect approval-controlled fields from direct mutation.
5.  Trigger requisition final-approval side effects such as budget reservation.
6.  Add tests for full happy path and representative blocked cases.

Constraints:

- Do not reintroduce ad hoc direct state writes.
- Keep behavior aligned with Approval Workflow Specification v2.

Acceptance criteria:

- requisition workflow runs through engine-backed actions
- records and side effects are created properly
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  requisition workflow summary

**WF-012 — Implement award workflow using engine**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement award workflow using the workflow engine in kentender_procurement.

Context:

- Award uses a mostly fixed route:
    1.  Procurement submits/prepares
    2.  Accounting Officer final-approves
- Stable states include:
    1.  Draft
    2.  Submitted
    3.  Pending Final Approval
    4.  Approved
    5.  Rejected
    6.  Returned
    7.  Standstill Active
    8.  Finalized

Requirements:

1.  Integrate Award Decision with the workflow engine.
2.  Implement service actions:
    - submit_award_for_approval(...)
    - final_approve_award(...)
    - reject_award(...)
    - return_award(...)
3.  Enforce evaluator ≠ award approver SoD rule.
4.  Trigger side effects:
    - notifications
    - standstill initialization
5.  Add tests for representative allow/deny and state progression cases.

Constraints:

- keep contract creation separate
- keep final approval service-driven

**WF-013 — Implement contract workflow using engine**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement contract workflow using the workflow engine in kentender_procurement.

Context:

- Contract stable lifecycle includes:
    - Draft
    - Submitted
    - Approved
    - Pending Signature
    - Signed
    - Active
    - Suspended
    - Terminated
    - Closed

Requirements:

1.  Integrate contract workflow with the workflow engine where appropriate.
2.  Implement service actions:
    - submit_contract_for_review(...)
    - approve_contract(...)
    - record_contract_signature(...)
    - activate_contract(...)
3.  Enforce:
    - no activation before signing
    - readiness gate from award/standstill
4.  Trigger relevant side effects and status events.
5.  Add tests for representative progression and blocked cases.

Constraints:

- do not bypass engine-backed state control
- keep variation lifecycle separate

**WF-014 — Implement acceptance dynamic workflow using engine**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement acceptance dynamic workflow using the workflow engine in kentender_procurement.

Context:

- Acceptance must support dynamic routes depending on type/complexity, for example:
    - simple goods -> inspector only
    - technical goods -> inspector + professional opinion
    - works -> inspector + engineer/consultant + committee
    - scientific/lab-tested goods -> result review + technical reviewer + approval

Stable acceptance states include:

- Draft
- Pending Technical Review
- Pending Acceptance Approval
- Accepted
- Partially Accepted
- Rejected

Requirements:

1.  Model at least two route templates initially:
    - Simple Goods Acceptance
    - Complex Technical Acceptance
2.  Resolve route dynamically from acceptance/contract context.
3.  Implement service actions for:
    - submit_acceptance_for_approval(...)
    - approve_acceptance_step(...)
    - reject_acceptance(...)
    - return_acceptance(...)
4.  Enforce mandatory-failure blocking for full acceptance.
5.  Trigger side effect for GRN eligibility only when allowed.
6.  Add tests for simple and complex route cases.

Constraints:

- do not hardcode only one acceptance pattern
- keep lifecycle stable and route dynamic

**WF-015 — Implement complaint dynamic workflow using engine**

**App:** kentender_governance  
**Priority:** High

**Cursor prompt**

Writing

Implement complaint dynamic workflow using the workflow engine in kentender_governance.

Context:

- Complaint processes may vary by complaint type, stage affected, hold requirement, and review panel requirement.

Suggested stable states:

- Draft
- Admissibility Pending
- Under Review
- Decision Draft
- Decided
- Appealed
- Closed

Requirements:

1.  Integrate Complaint workflow with dynamic route resolution.
2.  Support at least:
    - admissibility review route
    - full review route with reviewer/panel
3.  Implement actions:
    - submit_complaint(...)
    - review_complaint_admissibility(...)
    - submit_complaint_review(...)
    - issue_complaint_decision(...)
4.  Integrate hold application/release side effects through controlled hooks.
5.  Add tests for representative route and decision cases.

Constraints:

- do not bypass downstream hold-sensitive service layers
- keep complaint review assignment-aware

**WF-016 — Implement workflow regression test suite and fixtures**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow verification task in a modular Frappe-based system called KenTender.

Story:

- ID: WF-016
- Title: Implement workflow regression test suite and fixtures

Context:

- KenTender now has a workflow engine and must verify:
    - approval-controlled field protection
    - route resolution
    - action execution
    - SoD checks
    - side-effect hooks
    - domain workflow integrations

Task:  
Implement a workflow regression test suite and fixtures.

Minimum coverage:

1.  direct mutation of approval-controlled fields blocked
2.  requisition route resolved and executed correctly
3.  award route resolved and executed correctly
4.  contract cannot activate before signing
5.  acceptance simple route works
6.  acceptance complex route resolves different steps
7.  evaluator cannot approve award
8.  approval action records are created for all material actions
9.  side-effect hooks fire only on successful transitions

Requirements:

- keep tests organized and maintainable
- use realistic fixtures where practical
- ensure regression value is high

Constraints:

- do not rely only on UI tests
- focus on backend correctness

**Recommended execution order**

Use this order exactly:

1.  WF-001
2.  WF-002
3.  WF-003
4.  WF-004
5.  WF-005
6.  WF-006
7.  WF-007
8.  WF-008
9.  WF-009
10. WF-010
11. WF-011
12. WF-012
13. WF-013
14. WF-014
15. WF-015
16. WF-016

**What to review after every Cursor run**

For each story, verify:

- did it preserve backend-controlled state mutation?
- did it avoid direct field editing shortcuts?
- is the route or action behavior explicit and auditable?
- are approval action records created where expected?
- are SoD rules enforced in backend logic?
- are side effects separated from core transition logic?

**Strong recommendation**

Start implementation with:

- WF-002
- WF-003
- WF-008
- WF-011

Because those will immediately stop the most dangerous failure mode:  
**users or code changing approval state directly without passing through a controlled workflow path.**

After that, dynamic routing for acceptance is the highest-value advanced workflow to implement first.

If you want, the next best artifact is a **workflow developer runbook** that explains how engineers should use the engine in daily module development so they do not accidentally bypass it.