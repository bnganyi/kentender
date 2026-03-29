# Wave 2 Ticket Pack

**Epic overview**

**EPIC-PROC-001 — Purchase Requisition**

Owns:

- requisition header and items
- approvals
- amendments
- planning linkage
- budget reservation trigger
- strategy and budget validation consumption

**EPIC-PROC-002 — Procurement Plan**

Owns:

- procurement plan header and items
- requisition-to-plan consolidation
- anti-fragmentation controls
- plan revisions
- tender creation gate

**Recommended build order**

Build in this order:

1.  PROC-STORY-001 — Purchase Requisition DocType
2.  PROC-STORY-002 — Purchase Requisition Item child table
3.  PROC-STORY-003 — requisition totals and validation logic
4.  PROC-STORY-004 — Requisition Approval Record
5.  PROC-STORY-005 — requisition workflow action services
6.  PROC-STORY-006 — budget reservation integration on final approval
7.  PROC-STORY-007 — Requisition Amendment Record
8.  PROC-STORY-008 — amendment application service
9.  PROC-STORY-009 — Requisition Planning Link and planning status derivation
10. PROC-STORY-010 — requisition tests and queue/report scaffolding

Then planning:

1.  PROC-STORY-011 — Procurement Plan DocType
2.  PROC-STORY-012 — Procurement Plan Item DocType
3.  PROC-STORY-013 — Plan Consolidation Source
4.  PROC-STORY-014 — plan totals and reconciliation logic
5.  PROC-STORY-015 — Procurement Plan Approval Record
6.  PROC-STORY-016 — Plan Fragmentation Alert
7.  PROC-STORY-017 — fragmentation scan service
8.  PROC-STORY-018 — requisition-to-plan consolidation service
9.  PROC-STORY-019 — Procurement Plan Revision and revision lines
10. PROC-STORY-020 — plan revision apply service
11. PROC-STORY-021 — Plan to Tender Link and tender eligibility gate
12. PROC-STORY-022 — plan tests and queue/report scaffolding

That gives you a clean path from requisition to tender-ready plan item.

**EPIC-PROC-001 — Purchase Requisition**

**PROC-STORY-001 — Implement Purchase Requisition DocType**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** Wave 0 + Wave 1 complete

**Objective**  
Create the requisition header object as the formal internal procurement demand record.

**Scope**

- requisition header
- strategy linkage fields
- budget linkage fields
- organizational context
- justification and request metadata
- planning status fields

**Out of scope**

- child items
- approvals
- reservation logic
- amendments

**Acceptance criteria**

- DocType exists
- strategy/budget/organization fields are structured correctly
- basic validation works
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-001
- Epic: EPIC-PROC-001
- Title: Implement Purchase Requisition DocType

Context:

- App: kentender_procurement
- Purchase Requisition is the formal operational entry point of procurement demand.
- It must link organizational context, strategy context, and budget context.
- It will later feed approvals, budget reservation, and procurement planning.

Task:  
Implement the Purchase Requisition DocType.

Required fields:

- business_id
- title
- requisition_type
- status
- workflow_state
- approval_status
- procuring_entity
- requesting_department
- requested_by_user
- hod_user
- finance_reviewer_user
- procurement_receiver_user
- fiscal_year
- request_date
- required_by_date
- priority_level
- entity_strategic_plan
- program
- sub_program
- output_indicator
- performance_target
- national_objective
- budget_control_period
- budget
- budget_line
- funding_source
- requested_amount
- reserved_amount
- available_budget_at_check
- budget_check_datetime
- budget_reservation_status
- business_justification
- procurement_objective
- specification_summary
- delivery_location
- requested_delivery_period_days
- is_emergency_request
- emergency_justification
- is_multi_department
- beneficiary_summary
- planning_status
- planned_amount
- unplanned_amount
- latest_procurement_plan
- latest_procurement_plan_item
- is_locked
- lock_reason
- last_budget_action_ref
- exception_record
- cancellation_reason
- closure_notes
- remarks
- sensitivity_class
- is_publicly_disclosable

Requirements:

1.  Create the DocType.
2.  Keep it backend-first and workflow-ready.
3.  Add basic validations for required fields and date sanity.
4.  Keep budget and strategy linkage fields structured for later service validation.
5.  Add tests for:
    - valid create
    - emergency justification required when emergency flag is set
    - invalid date sanity scenarios

Constraints:

- Do not implement child item logic here.
- Do not implement approval flow here.
- Do not hardcode business logic that belongs in service methods.
- Keep DocType controller thin.

Acceptance criteria:

- DocType exists
- basic validations work
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-002 — Implement Purchase Requisition Item child table**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** PROC-STORY-001

**Objective**  
Create requisition line items with quantity, cost, and specification detail.

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-002
- Epic: EPIC-PROC-001
- Title: Implement Purchase Requisition Item child table

Context:

- App: kentender_procurement
- Requisition items are line-level demand records under a purchase requisition.
- Requested amount on the requisition header will later derive from item totals.

Task:  
Implement the Purchase Requisition Item child table.

Required fields:

- item_description
- item_specification
- category
- uom
- quantity
- estimated_unit_cost
- line_total
- required_delivery_date
- beneficiary_department
- notes

Requirements:

1.  Create the child table.
2.  Add backend calculation/validation support for line_total = quantity \* estimated_unit_cost.
3.  Validate that quantity and estimated unit cost are positive.
4.  Add tests for:
    - valid line create
    - invalid zero/negative quantity blocked
    - invalid zero/negative unit cost blocked
    - line total calculation

Constraints:

- Do not depend on ERPNext Item master here.
- Do not place critical calculation only in client-side code.
- Keep line item structure generic enough for public procurement demand capture.

Acceptance criteria:

- child table exists
- validations work
- line totals calculate correctly
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-003 — Implement requisition totals and validation logic**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** PROC-STORY-001, PROC-STORY-002, strategy/budget services

**Objective**  
Calculate header totals and enforce core structural validation.

**Cursor prompt**

Writing

You are implementing a bounded validation/service feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-003
- Epic: EPIC-PROC-001
- Title: Implement requisition totals and validation logic

Context:

- App: kentender_procurement
- Requested amount on the requisition header must derive from child line totals.
- Requisition must have valid structure before approval workflow begins.

Task:  
Implement backend totals and validation logic for Purchase Requisition.

Requirements:

1.  Recompute requested_amount from line totals.
2.  Validate that requisition has at least one item before submission-ready states.
3.  Integrate backend strategy structure validation using shared strategy services where appropriate.
4.  Integrate budget line validation structure checks using shared budget services where appropriate.
5.  Add tests for:
    - requested amount derived from items
    - requisition with no items blocked
    - invalid strategy/budget linkage blocked at validation boundary as appropriate

Constraints:

- Do not implement final approval flow here.
- Do not reserve budget in this story.
- Do not duplicate strategy or budget service logic.

Acceptance criteria:

- header total is derived correctly
- empty requisitions are blocked
- linkage validations are enforced appropriately
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-004 — Implement Requisition Approval Record**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-001

**Cursor prompt**

Writing

You are implementing a bounded audit/control feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-004
- Epic: EPIC-PROC-001
- Title: Implement Requisition Approval Record

Context:

- App: kentender_procurement
- Requisition approvals must be stored as formal records, not inferred only from workflow state.

Task:  
Implement Requisition Approval Record.

Required fields:

- purchase_requisition
- workflow_step
- approver_user
- approver_role
- action_type
- action_datetime
- comments
- exception_record
- decision_level

Action types:

- Approve
- Reject
- Return for Revision
- Recommend
- Request Clarification

Requirements:

1.  Create the DocType.
2.  Keep it append-only in practical behavior.
3.  Add tests for valid approval record creation and linkage.

Constraints:

- Do not implement the approval service in this story.
- Keep this as a formal audit/control object.

Acceptance criteria:

- approval record exists
- linkage works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-005 — Implement requisition workflow action services**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** PROC-STORY-004, workflow guard framework, separation-of-duty framework

**Objective**  
Create server-side requisition actions for submit, approve, reject, return.

**Cursor prompt**

Writing

You are implementing a bounded workflow-action feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-005
- Epic: EPIC-PROC-001
- Title: Implement requisition workflow action services

Context:

- App: kentender_procurement
- Critical requisition lifecycle actions must be explicit server-side business actions.
- Approval actions must create formal approval records and respect workflow guards and conflict-of-duty rules.

Task:  
Implement requisition action services such as:

- submit_requisition
- approve_requisition_step
- reject_requisition
- return_requisition_for_revision

Requirements:

1.  Place logic in services, not only DocType controller methods.
2.  Integrate workflow guard framework.
3.  Integrate separation-of-duty checks where applicable.
4.  Create approval records as part of approval/reject/return actions.
5.  Emit audit events for material actions.
6.  Add tests for:
    - submit
    - approve
    - reject
    - return for revision
    - self-approval/conflict blocked where applicable

Constraints:

- Do not reserve budget in this story.
- Do not implement UI workflow customization here beyond what is needed.
- Keep business actions explicit and reusable.

Acceptance criteria:

- action services exist
- approval records are created
- guards/conflict checks are enforced
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-006 — Implement budget reservation integration on final approval**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** PROC-STORY-005, budget services

**Cursor prompt**

Writing

You are implementing a bounded cross-module integration feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-006
- Epic: EPIC-PROC-001
- Title: Implement budget reservation integration on final approval

Context:

- App: kentender_procurement
- Final requisition approval must trigger budget reservation through the budget service layer.
- Reservation must not be implemented as direct ledger writes in procurement code.

Task:  
Integrate requisition final approval with budget reservation services.

Requirements:

1.  On final approval, call shared budget validation/reservation services.
2.  Update requisition fields such as:
    - reserved_amount
    - available_budget_at_check
    - budget_check_datetime
    - budget_reservation_status
    - last_budget_action_ref
3.  Ensure rejection does not reserve.
4.  Ensure cancellation/reduction behavior can be supported later without architectural conflict.
5.  Add tests for:
    - successful reservation on final approval
    - insufficient funds blocking final approval
    - reservation status updates correctly

Constraints:

- Do not write ledger entries directly from procurement code.
- Do not bypass budget service methods.
- Keep the integration explicit and auditable.

Acceptance criteria:

- final approval reserves budget through service layer
- insufficient funds block correctly
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-007 — Implement Requisition Amendment Record**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-001

**Cursor prompt**

Writing

You are implementing a bounded change-control feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-007
- Epic: EPIC-PROC-001
- Title: Implement Requisition Amendment Record

Context:

- App: kentender_procurement
- Approved requisitions must not be silently edited. Material changes must flow through amendments.

Task:  
Implement Requisition Amendment Record.

Required fields:

- purchase_requisition
- amendment_type
- requested_by
- requested_on
- approved_by
- approved_on
- reason
- before_summary
- after_summary
- budget_adjustment_required
- status

Amendment types:

- Quantity Change
- Cost Estimate Change
- Strategic Linkage Correction
- Budget Line Change
- Need Specification Change
- Cancellation

Requirements:

1.  Create the DocType.
2.  Keep it suitable for auditable before/after change tracking.
3.  Add tests for valid amendment record creation.

Constraints:

- Do not apply amendments in this story.
- Do not allow this to become a casual comment object.

Acceptance criteria:

- amendment record exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-008 — Implement amendment application service**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-007, budget services

**Cursor prompt**

Writing

You are implementing a bounded service-action feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-008
- Epic: EPIC-PROC-001
- Title: Implement amendment application service

Context:

- App: kentender_procurement
- Approved requisitions may need controlled amendments that affect amount, budget linkage, or cancellation state.
- Amendment application must be explicit and auditable.

Task:  
Implement apply_requisition_amendment(amendment_id).

Requirements:

1.  Apply only approved amendments.
2.  Prevent direct mutation paths outside the amendment service.
3.  Integrate with budget reservation adjustment/release logic where relevant.
4.  Emit audit events.
5.  Add tests for:
    - valid amendment apply
    - invalid status blocked
    - budget-affecting amendment triggers correct budget service interaction

Constraints:

- Do not bypass budget service layer.
- Do not silently overwrite approved requisition state without amendment record linkage.
- Keep behavior explicit and auditable.

Acceptance criteria:

- amendment apply service exists
- budget-affecting amendments are handled through services
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-009 — Implement Requisition Planning Link and planning status derivation**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-001

**Cursor prompt**

Writing

You are implementing a bounded traceability feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-009
- Epic: EPIC-PROC-001
- Title: Implement Requisition Planning Link and planning status derivation

Context:

- App: kentender_procurement
- Requisitions may be planned fully, partially, or not at all.
- Planning linkage must be explicit and traceable.

Task:  
Implement:

1.  Requisition Planning Link
2.  backend planning-status derivation logic for requisitions

Required fields for link:

- purchase_requisition
- procurement_plan
- procurement_plan_item
- linked_amount
- linked_on
- status

Statuses:

- Active
- Released
- Superseded

Requirements:

1.  Create the link DocType.
2.  Derive and maintain requisition fields such as:
    - planned_amount
    - unplanned_amount
    - planning_status
3.  Add tests for:
    - no links -> Not Planned
    - partial links -> Partially Planned
    - full coverage -> Fully Planned / Converted to Plan

Constraints:

- Do not implement full planning module logic here.
- Keep linkage reusable for future consolidation scenarios.

Acceptance criteria:

- planning link exists
- requisition planning status derives correctly
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-010 — Implement requisition tests and queue/report scaffolding**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** PROC-STORY-001 through 009

**Cursor prompt**

Writing

You are implementing a bounded hardening/support task in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-010
- Epic: EPIC-PROC-001
- Title: Implement requisition tests and queue/report scaffolding

Context:

- App: kentender_procurement
- Requisition is the first major operational workflow and needs good coverage and UAT-friendly queue support.

Task:  
Add:

1.  a solid requisition test suite
2.  lightweight queue/report scaffolding for workspace integration

Suggested queue/report scaffolding:

- My Requisitions
- Pending Requisition Approvals
- Planning Ready Requisitions

Requirements:

- tests should cover core happy path and blocking scenarios
- queue/report scaffolding should be simple and extendable
- align labels with workspace/UAT design

Constraints:

- do not overbuild dashboards here
- keep queue/report work lightweight
- focus on correctness and UAT utility

Acceptance criteria:

- meaningful requisition test coverage exists
- queue/report scaffolding exists
- workspace integration can hook into it cleanly

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-PROC-002 — Procurement Plan**

**PROC-STORY-011 — Implement Procurement Plan DocType**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** requisition foundation, strategy, budget

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-011
- Epic: EPIC-PROC-002
- Title: Implement Procurement Plan DocType

Context:

- App: kentender_procurement
- Procurement Plan is a versioned, approval-controlled plan document that consolidates approved demand into executable procurement activities.

Task:  
Implement the Procurement Plan DocType.

Required fields:

- business_id
- plan_title
- procuring_entity
- fiscal_year
- budget_control_period
- version_no
- status
- workflow_state
- approval_status
- plan_period_label
- is_current_active_version
- supersedes_plan
- superseded_by_plan
- revision_reason
- planning_owner_user
- procurement_owner_user
- finance_review_user
- planning_authority_user
- total_estimated_amount
- total_item_count
- planned_requisition_count
- manual_item_count
- consolidated_item_count
- currency
- allow_manual_items
- allow_split_tendering
- allow_consolidation
- anti_fragmentation_status
- remarks
- sensitivity_class
- is_publicly_disclosable

Requirements:

1.  Create the DocType.
2.  Support version/supersession structure.
3.  Validate entity and budget-control context.
4.  Add tests for valid create and version integrity basics.

Constraints:

- Do not implement plan items here.
- Do not implement full approval flow here.
- Keep it a controlled planning document.

Acceptance criteria:

- DocType exists
- version model is in place
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-012 — Implement Procurement Plan Item DocType**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** PROC-STORY-011

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-012
- Epic: EPIC-PROC-002
- Title: Implement Procurement Plan Item DocType

Context:

- App: kentender_procurement
- Procurement Plan Item is the main executable planning unit and the mandatory source for tender creation later.

Task:  
Implement the Procurement Plan Item DocType.

Required fields:

- business_id
- procurement_plan
- status
- origin_type
- manual_entry_justification
- source_summary
- procuring_entity
- requesting_department
- responsible_department
- beneficiary_summary
- title
- procurement_category
- procurement_method
- description
- estimated_amount
- currency
- priority_level
- lotting_strategy
- is_framework_related
- is_multi_year
- is_emergency_path
- entity_strategic_plan
- program
- sub_program
- output_indicator
- performance_target
- national_objective
- budget
- budget_line
- funding_source
- planned_budget_amount
- reserved_source_amount
- unbacked_amount
- budget_alignment_status
- planned_start_date
- planned_preparation_start_date
- planned_publication_date
- planned_submission_deadline
- planned_award_date
- planned_contract_start_date
- planned_completion_date
- latest_tender
- tender_creation_status
- execution_progress_status
- fragmentation_risk_score
- fragmentation_alert_status
- conversion_locked
- cancellation_reason
- remarks

Requirements:

1.  Create the DocType.
2.  Validate key structural requirements for strategy and budget linkage.
3.  Validate date sequencing at a basic level.
4.  Add tests for valid creation and invalid linkage/date scenarios.

Constraints:

- Do not implement consolidation logic here.
- Do not create tender integration here.
- Keep business logic backend-oriented.

Acceptance criteria:

- DocType exists
- structural validations work
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-013 — Implement Plan Consolidation Source**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-012, requisition planning link model

**Cursor prompt**

Writing

You are implementing a bounded traceability feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-013
- Epic: EPIC-PROC-002
- Title: Implement Plan Consolidation Source

Context:

- App: kentender_procurement
- A procurement plan item may be sourced from one or more requisitions.
- Consolidation must preserve source traceability.

Task:  
Implement Plan Consolidation Source.

Required fields:

- procurement_plan_item
- purchase_requisition
- source_type
- linked_amount
- linked_on
- status
- remarks

Source types:

- Requisition
- Manual
- Revision

Statuses:

- Active
- Released
- Superseded

Requirements:

1.  Create the DocType.
2.  Keep it suitable for many-to-one source linkage.
3.  Add tests for valid linkage creation.

Constraints:

- Do not implement full consolidation service here.
- Keep the record explicit and auditable.

Acceptance criteria:

- source link exists
- traceability model is in place
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-014 — Implement plan totals and reconciliation logic**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-011, PROC-STORY-012, PROC-STORY-013

**Cursor prompt**

Writing

You are implementing a bounded validation/reconciliation feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-014
- Epic: EPIC-PROC-002
- Title: Implement plan totals and reconciliation logic

Context:

- App: kentender_procurement
- Procurement plan totals and item/source link reconciliation must be derived consistently.

Task:  
Implement backend totals and reconciliation helpers for procurement plans and plan items.

Requirements:

1.  Derive plan totals such as:
    - total_estimated_amount
    - total_item_count
    - planned_requisition_count
    - consolidated_item_count
2.  Reconcile plan item source totals against linked source records where appropriate.
3.  Add tests for total derivation and mismatch detection.

Constraints:

- Do not implement full fragmentation scanning here.
- Keep this focused on totals and reconciliation.

Acceptance criteria:

- totals derive correctly
- source reconciliation logic exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-015 — Implement Procurement Plan Approval Record**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-011

**Cursor prompt**

Writing

You are implementing a bounded control/audit feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-015
- Epic: EPIC-PROC-002
- Title: Implement Procurement Plan Approval Record

Context:

- App: kentender_procurement
- Plan approval actions must be recorded formally, not inferred only from status changes.

Task:  
Implement Procurement Plan Approval Record.

Required fields:

- procurement_plan
- workflow_step
- approver_user
- approver_role
- action_type
- action_datetime
- comments
- decision_level
- exception_record

Requirements:

1.  Create the DocType.
2.  Keep it append-only in practical use.
3.  Add tests for linkage and valid record creation.

Constraints:

- Do not implement approval service here.
- Keep it aligned with requisition approval record style.

Acceptance criteria:

- approval record exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-016 — Implement Plan Fragmentation Alert**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-012

**Cursor prompt**

Writing

You are implementing a bounded compliance-control feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-016
- Epic: EPIC-PROC-002
- Title: Implement Plan Fragmentation Alert

Context:

- App: kentender_procurement
- Procurement planning must detect suspicious demand splitting and fragmentation risks.

Task:  
Implement Plan Fragmentation Alert.

Required fields:

- business_id
- procurement_plan
- related_plan_item
- alert_type
- severity
- risk_score
- rule_trigger_summary
- status
- raised_on
- raised_by_system
- reviewed_by
- review_notes
- exception_record

Alert types:

- Similar Demand Split
- Threshold Avoidance Risk
- Duplicate Department Demand
- Duplicate Schedule Window
- Repeated Same Supplier Pattern
- Manual Override Risk

Requirements:

1.  Create the DocType.
2.  Keep it suitable for system-generated and reviewer-managed alerts.
3.  Add tests for valid alert record creation.

Constraints:

- Do not implement alert detection logic here.
- Keep this as the record model only.

Acceptance criteria:

- alert record exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-017 — Implement fragmentation scan service**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-016, PROC-STORY-012

**Cursor prompt**

Writing

You are implementing a bounded compliance scanning feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-017
- Epic: EPIC-PROC-002
- Title: Implement fragmentation scan service

Context:

- App: kentender_procurement
- Fragmentation detection should identify suspicious planning patterns without hiding the basis of the flag.

Task:  
Implement a first-pass fragmentation scan service for plan items.

Requirements:

1.  Create a reusable scanning service that can evaluate candidate risk factors such as:
    - same/similar category
    - close schedule windows
    - same department or related departments
    - same budget line
    - similar descriptions/titles
2.  Produce Plan Fragmentation Alert records for triggered findings.
3.  Keep logic understandable and tunable.
4.  Add tests for representative alert-trigger scenarios.

Constraints:

- Do not overengineer AI/semantic matching.
- Keep first release practical and explainable.
- Do not auto-block everything; keep record generation and severity rational.

Acceptance criteria:

- scan service exists
- representative alerts are created
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-018 — Implement requisition-to-plan consolidation service**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** requisition planning link, plan item, consolidation source

**Cursor prompt**

Writing

You are implementing a bounded service-action feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-018
- Epic: EPIC-PROC-002
- Title: Implement requisition-to-plan consolidation service

Context:

- App: kentender_procurement
- Approved requisitions must be pulled into procurement planning through explicit consolidation/linking.
- Source traceability must be preserved.

Task:  
Implement a service for adding approved requisitions into a procurement plan and consolidating them into plan items where appropriate.

Requirements:

1.  Support:
    - one requisition -> one plan item
    - multiple requisitions -> one consolidated plan item
2.  Create Plan Consolidation Source records.
3.  Update requisition planning links/status using the requisition-side linkage model.
4.  Prevent over-planning beyond requisition amounts.
5.  Add tests for:
    - simple one-to-one planning
    - consolidated source scenario
    - over-planning blocked

Constraints:

- Do not create tenders here.
- Do not lose requisition source traceability.
- Keep consolidation explicit and auditable.

Acceptance criteria:

- service exists
- source traceability preserved
- over-planning blocked
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-019 — Implement Procurement Plan Revision and revision lines**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-011, PROC-STORY-012

**Cursor prompt**

Writing

You are implementing a bounded revision-control feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-019
- Epic: EPIC-PROC-002
- Title: Implement Procurement Plan Revision and revision lines

Context:

- App: kentender_procurement
- Approved/active plans must not be silently edited. Controlled revisions are required.

Task:  
Implement:

1.  Procurement Plan Revision
2.  Procurement Plan Revision Line

Suggested fields:

- revision business_id
- source_procurement_plan
- revision_type
- revision_reason
- requested_by
- requested_on
- approved_by
- approved_on
- status

Revision line fields:

- affected_plan_item
- action_type
- before_snapshot_ref
- after_snapshot_ref
- change_amount
- change_notes

Requirements:

1.  Create the DocTypes.
2.  Keep them suitable for explicit before/after traceability.
3.  Add tests for valid revision record creation.

Constraints:

- Do not apply revisions in this story.
- Do not silently mutate active plans.

Acceptance criteria:

- revision records exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-020 — Implement plan revision apply service**

**App:** kentender_procurement  
**Priority:** High  
**Depends on:** PROC-STORY-019

**Cursor prompt**

Writing

You are implementing a bounded service-action feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-020
- Epic: EPIC-PROC-002
- Title: Implement plan revision apply service

Context:

- App: kentender_procurement
- Procurement plan revisions must be applied explicitly and auditable.

Task:  
Implement apply_procurement_plan_revision(revision_id).

Requirements:

1.  Apply only approved revisions.
2.  Preserve historical traceability.
3.  Update plan/item state through controlled service logic.
4.  Emit audit events.
5.  Add tests for:
    - valid apply
    - invalid revision status blocked
    - affected plan items updated as expected

Constraints:

- Do not silently rewrite active plan history.
- Keep revision application explicit and service-driven.

Acceptance criteria:

- apply service exists
- revisions apply safely
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-021 — Implement Plan to Tender Link and tender eligibility gate**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** plan item model

**Cursor prompt**

Writing

You are implementing a bounded traceability/gating feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-021
- Epic: EPIC-PROC-002
- Title: Implement Plan to Tender Link and tender eligibility gate

Context:

- App: kentender_procurement
- Tenders must originate from approved active plan items.
- Plan-to-tender conversion needs traceability.

Task:  
Implement:

1.  Plan to Tender Link
2.  backend tender-eligibility gate/check helper for plan items

Required fields for link:

- procurement_plan_item
- tender
- linked_amount
- link_type
- status

Link types:

- Direct
- Split Tender
- Consolidated Tender

Statuses:

- Active
- Superseded
- Cancelled

Requirements:

1.  Create the link DocType.
2.  Implement helper logic to determine whether a plan item is eligible for tender creation.
3.  Add tests for:
    - eligible plan item
    - ineligible plan item blocked
    - link creation basics

Constraints:

- Do not implement the Tender DocType here.
- Keep this as the gate and traceability foundation.

Acceptance criteria:

- link model exists
- eligibility helper exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-022 — Implement plan tests and queue/report scaffolding**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** PROC-STORY-011 through 021

**Cursor prompt**

Writing

You are implementing a bounded hardening/support task in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-022
- Epic: EPIC-PROC-002
- Title: Implement plan tests and queue/report scaffolding

Context:

- App: kentender_procurement
- Procurement planning needs strong test coverage and UAT-friendly queue/report support.

Task:  
Add:

1.  a solid procurement plan test suite
2.  lightweight queue/report scaffolding

Suggested queue/report scaffolding:

- Planning Queue
- Draft Procurement Plans
- Active Procurement Plans
- Plan Items Ready for Tender
- Fragmentation Alerts

Requirements:

- cover consolidation, revisions, and tender readiness basics
- keep queue/report scaffolding simple and extendable
- align labels with workspace design

Constraints:

- do not build the Tender module here
- do not overbuild dashboards
- focus on correctness and UAT utility

Acceptance criteria:

- meaningful planning test coverage exists
- queue/report scaffolding exists
- workspace integration can hook in cleanly

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**Recommended execution order in Cursor**

Run in this order:

**Requisition**

1.  PROC-STORY-001
2.  PROC-STORY-002
3.  PROC-STORY-003
4.  PROC-STORY-004
5.  PROC-STORY-005
6.  PROC-STORY-006
7.  PROC-STORY-007
8.  PROC-STORY-008
9.  PROC-STORY-009
10. PROC-STORY-010

**Planning**

1.  PROC-STORY-011
2.  PROC-STORY-012
3.  PROC-STORY-013
4.  PROC-STORY-014
5.  PROC-STORY-015
6.  PROC-STORY-016
7.  PROC-STORY-017
8.  PROC-STORY-018
9.  PROC-STORY-019
10. PROC-STORY-020
11. PROC-STORY-021
12. PROC-STORY-022