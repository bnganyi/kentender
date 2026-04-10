# Wave 5 Ticket Pack

**Sprint tracking:** [`WAVE 5 BACKLOG.md`](../dev/WAVE%205%20BACKLOG.md) — update **Status** / **Notes** per story when acceptance is met; keep this pack canonical for prompts and criteria.

**Wave 5 Epic Overview**

**EPIC-PROC-009 — Inspection & Acceptance**

Owns:

- inspection records
- checklist and parameter testing
- evidence
- acceptance decisions
- non-conformance
- reinspection
- contract progress updates

**EPIC-GOV-001 — Deliberations**

Owns:

- deliberation sessions
- agenda items
- attendance
- minutes
- recommendations
- resolutions
- follow-up actions

**EPIC-GOV-002 — Complaints & Disputes**

Owns:

- complaint intake
- admissibility
- review assignments
- evidence
- decisions
- actions
- appeal
- procurement hold integration

# Recommended Wave 5 Build Order

**Inspection & Acceptance**

1.  PROC-STORY-100 — Inspection Method Template
2.  PROC-STORY-101 — Inspection Record
3.  PROC-STORY-102 — Inspection Checklist Line
4.  PROC-STORY-103 — Inspection Parameter Line
5.  PROC-STORY-104 — Inspection Test Result
6.  PROC-STORY-105 — Sample Record
7.  PROC-STORY-106 — Inspection Evidence
8.  PROC-STORY-107 — Non Conformance Record
9.  PROC-STORY-108 — Acceptance Record
10. PROC-STORY-109 — Reinspection Record
11. PROC-STORY-110 — Inspection Status Event
12. PROC-STORY-111 — create inspection from contract scope service
13. PROC-STORY-112 — checklist/parameter result recording and tolerance evaluation services
14. PROC-STORY-113 — acceptance decision service
15. PROC-STORY-114 — non-conformance and reinspection services
16. PROC-STORY-115 — contract progress update integration service
17. PROC-STORY-116 — inspection queue/report scaffolding and tests

**Deliberations**

1.  GOV-STORY-001 — Deliberation Session
2.  GOV-STORY-002 — Deliberation Agenda Item
3.  GOV-STORY-003 — Deliberation Attendance
4.  GOV-STORY-004 — Deliberation Minute
5.  GOV-STORY-005 — Recommendation Record
6.  GOV-STORY-006 — Resolution Record
7.  GOV-STORY-007 — Follow Up Action
8.  GOV-STORY-008 — Deliberation Status Event
9.  GOV-STORY-009 — deliberation session lifecycle services
10. GOV-STORY-010 — resolution/follow-up action services
11. GOV-STORY-011 — deliberation queue/report scaffolding and tests

**Complaints**

1.  GOV-STORY-012 — Complaint
2.  GOV-STORY-013 — Complaint Party
3.  GOV-STORY-014 — Complaint Evidence
4.  GOV-STORY-015 — Complaint Review Panel Assignment
5.  GOV-STORY-016 — Complaint Review Record
6.  GOV-STORY-017 — Complaint Decision
7.  GOV-STORY-018 — Complaint Action
8.  GOV-STORY-019 — Appeal Record
9.  GOV-STORY-020 — Complaint Status Event
10. GOV-STORY-021 — complaint intake and admissibility services
11. GOV-STORY-022 — complaint hold application/release services
12. GOV-STORY-023 — complaint review and decision services
13. GOV-STORY-024 — complaint action execution services
14. GOV-STORY-025 — complaint queue/report scaffolding and tests

**EPIC-PROC-009 — Inspection & Acceptance**

**PROC-STORY-100 — Implement Inspection Method Template**

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-100
- Epic: EPIC-PROC-009
- Title: Implement Inspection Method Template

Context:

- App: kentender_procurement
- Inspection in KenTender supports checklist, parameter-based, field measurement, and sampling/lab methods.
- Templates make inspection repeatable and suitable for sector-specific verification.

Task:  
Implement the Inspection Method Template DocType.

Required fields:

- template_code
- template_name
- inspection_domain
- applicable_contract_type
- inspection_method_type
- description
- active
- requires_sampling
- requires_lab_test
- requires_field_measurement
- requires_checklist
- requires_parameter_testing
- standards_reference_summary
- default_pass_logic

Requirements:

1.  Create the DocType.
2.  Keep it reusable across contracts and deliverables.
3.  Add tests for valid create and duplicate-code blocking.

Constraints:

- Do not implement template child definitions deeply here unless minimally necessary.
- Keep the model ready for later domain expansion.

Acceptance criteria:

- DocType exists
- basic validation works
- tests pass

**PROC-STORY-101 — Implement Inspection Record**

**Cursor prompt**

Writing

Implement Inspection Record in kentender_procurement.

Required fields:

- business_id
- contract
- status
- workflow_state
- inspection_scope_type
- contract_milestone
- contract_deliverable
- inspection_title
- inspection_description
- inspection_method_type
- inspection_method_template
- requires_sampling
- requires_lab_test
- requires_field_measurement
- requires_third_party_test_certificate
- procuring_entity
- responsible_department
- inspection_officer_user
- inspection_team_lead_user
- contract_manager_user
- scheduled_inspection_datetime
- actual_inspection_datetime
- inspection_location
- supplier_representative_name
- supplier_representative_contact
- inspection_result
- checklist_items_count
- parameter_tests_count
- parameter_tests_passed_count
- parameter_tests_failed_count
- non_conformance_count
- acceptance_record
- acceptance_status
- is_reinspection_required
- reinspection_due_date
- is_locked
- exception_record
- remarks

Requirements:

- validate contract/scope linkage coherently
- keep inspection and acceptance separate
- add tests

**PROC-STORY-102 — Implement Inspection Checklist Line**

**Cursor prompt**

Writing

Implement Inspection Checklist Line under Inspection Record in kentender_procurement.

Required fields:

- check_item_no
- requirement_type
- requirement_title
- expected_requirement
- observed_result
- result_status
- severity_if_failed
- related_deliverable
- related_milestone
- notes

Requirements:

- support visual/document/procedural checks
- add validation and tests

**PROC-STORY-103 — Implement Inspection Parameter Line**

**Cursor prompt**

Writing

Implement Inspection Parameter Line in kentender_procurement.

Required fields:

- inspection_record
- parameter_code
- parameter_name
- parameter_category
- specification_reference
- test_method_reference
- unit_of_measure
- expected_min_value
- expected_max_value
- target_value
- tolerance_type
- tolerance_value
- sample_required
- lab_test_required
- mandatory_for_acceptance
- status

Requirements:

- support measurable technical verification
- validate tolerance field coherence
- add tests

**PROC-STORY-104 — Implement Inspection Test Result**

**Cursor prompt**

Writing

Implement Inspection Test Result in kentender_procurement.

Required fields:

- inspection_record
- inspection_parameter_line
- observed_numeric_value
- observed_text_value
- observed_boolean_value
- result_unit
- result_datetime
- test_performed_by_user
- test_location
- test_method_used
- equipment_used
- equipment_calibration_reference
- lab_reference_no
- certificate_reference
- pass_fail_result
- result_notes

Requirements:

- create model
- support numeric/text/boolean result capture
- add tests

**PROC-STORY-105 — Implement Sample Record**

**Cursor prompt**

Writing

Implement Sample Record in kentender_procurement.

Required fields:

- inspection_record
- sample_code
- sample_type
- sample_description
- collected_by_user
- collection_datetime
- collection_location
- quantity_collected
- unit_of_measure
- chain_of_custody_reference
- submitted_to_lab_name
- submitted_on
- received_result_on
- sample_status
- remarks

Requirements:

- support sample chain traceability
- add tests

**PROC-STORY-106 — Implement Inspection Evidence**

**Cursor prompt**

Writing

Implement Inspection Evidence in kentender_procurement.

Required fields:

- inspection_record
- acceptance_record
- non_conformance_record
- evidence_type
- file
- title
- uploaded_by_user
- uploaded_on
- hash_value
- sensitivity_class
- remarks

Requirements:

- integrate with typed attachment/file control patterns where appropriate
- add tests

**PROC-STORY-107 — Implement Non Conformance Record**

**Cursor prompt**

Writing

Implement Non Conformance Record in kentender_procurement.

Required fields:

- business_id
- inspection_record
- contract
- contract_milestone
- contract_deliverable
- checklist_line_ref
- issue_type
- issue_title
- issue_description
- severity
- status
- required_corrective_action
- corrective_action_due_date
- resolved_on
- resolution_summary
- resolved_by_user
- waiver_approved_by_user
- remarks

Requirements:

- support formal defect/non-compliance tracking
- add tests

**PROC-STORY-108 — Implement Acceptance Record**

**Cursor prompt**

Writing

Implement Acceptance Record in kentender_procurement.

Required fields:

- business_id
- inspection_record
- contract
- status
- workflow_state
- acceptance_decision
- decision_datetime
- approved_by_user
- decision_reason
- accepted_value_amount
- accepted_quantity_summary
- accepted_scope_notes
- technical_acceptance_basis
- standards_compliance_status
- contract_progress_update_required
- payment_eligibility_signal_status
- next_action_type
- is_locked
- lock_reason
- remarks

Requirements:

- create the DocType
- keep acceptance separate from inspection completion
- add tests

**PROC-STORY-109 — Implement Reinspection Record**

**Cursor prompt**

Writing

Implement Reinspection Record in kentender_procurement.

Required fields:

- inspection_record
- contract
- trigger_reason
- scheduled_datetime
- actual_datetime
- status
- outcome_summary
- linked_followup_inspection
- created_by_user
- remarks

Requirements:

- support follow-up inspection traceability
- add tests

**PROC-STORY-110 — Implement Inspection Status Event**

**Cursor prompt**

Writing

Implement Inspection Status Event in kentender_procurement.

Required fields:

- inspection_record
- event_type
- event_datetime
- actor_user
- summary
- related_acceptance_record
- related_non_conformance_record
- event_hash

Requirements:

- append-only lifecycle event model
- add tests

**PROC-STORY-111 — Implement create-inspection-from-contract-scope service**

**Cursor prompt**

Writing

Implement create_inspection_for_contract_scope(contract_id, scope_ref, scope_type) in kentender_procurement.

Requirements:

- create inspection from contract, milestone, or deliverable scope
- inherit contract context
- optionally apply inspection template reference
- add tests for representative scope types

Constraints:

- do not decide acceptance here

**PROC-STORY-112 — Implement result recording and tolerance evaluation services**

**Cursor prompt**

Writing

Implement inspection result/tolerance services in kentender_procurement.

Suggested actions:

- apply_inspection_template(...)
- record_checklist_result(...)
- record_parameter_result(...)
- evaluate_parameter_tolerance(...)
- recompute_inspection_result(...)

Requirements:

- evaluate parameter results against tolerance rules
- update inspection summary counts
- add tests for pass/fail/inconclusive parameter scenarios

Constraints:

- keep formulas readable and explicit

**PROC-STORY-113 — Implement acceptance decision service**

**Cursor prompt**

Writing

Implement submit_acceptance_decision(inspection_record_id, decision_data) in kentender_procurement.

Requirements:

- require completed inspection
- block full acceptance where mandatory failures remain unresolved
- create Acceptance Record
- update inspection acceptance status
- emit audit events
- add tests for accepted, partial, and rejected outcomes

Constraints:

- do not update payment ledgers here

**PROC-STORY-114 — Implement non-conformance and reinspection services**

**Cursor prompt**

Writing

Implement non-conformance/reinspection services in kentender_procurement.

Suggested actions:

- raise_non_conformance(...)
- submit_corrective_action_resolution(...)
- approve_non_conformance_resolution(...)
- create_reinspection(...)

Requirements:

- keep non-conformance formal and auditable
- support reinspection chain
- add tests for representative flows

**PROC-STORY-115 — Implement contract progress update integration service**

**Cursor prompt**

Writing

Implement inspection-to-contract progress update integration in kentender_procurement.

Requirements:

- update milestone/deliverable progress through controlled service methods
- recalculate contract completion percent where appropriate
- keep contract module as owner of final contract state
- add tests for representative accepted/partial/rejected outcomes

Constraints:

- do not directly mutate arbitrary contract fields from random code paths

**PROC-STORY-116 — Implement inspection queue/report scaffolding and tests**

**Cursor prompt**

Writing

Implement inspection test suite and lightweight queue/report scaffolding in kentender_procurement.

Suggested queues/reports:

- Scheduled Inspections
- Inspections Awaiting Acceptance
- Non-Conformance Register
- Reinspections Due
- Partial/Rejection Summary

Requirements:

- meaningful coverage
- workspace-friendly scaffolding

Constraints:

- no heavy dashboard buildout

**EPIC-GOV-001 — Deliberations**

**GOV-STORY-001 — Implement Deliberation Session**

**Cursor prompt**

Writing

Implement Deliberation Session in kentender_governance.

Required fields:

- business_id
- session_title
- session_type
- status
- procuring_entity
- scheduled_datetime
- actual_start_datetime
- actual_end_datetime
- location
- chair_user
- secretariat_user
- linked_doctype
- linked_docname
- summary_notes
- is_locked

Requirements:

- support procurement-related governance sessions
- add tests

**GOV-STORY-002 — Implement Deliberation Agenda Item**

**Cursor prompt**

Writing

Implement Deliberation Agenda Item in kentender_governance.

Required fields:

- deliberation_session
- item_no
- title
- description
- linked_doctype
- linked_docname
- status

Requirements:

- add tests for valid linkage/order behavior

**GOV-STORY-003 — Implement Deliberation Attendance**

**Cursor prompt**

Writing

Implement Deliberation Attendance in kentender_governance.

Required fields:

- deliberation_session
- user
- attendee_name
- role_type
- attendance_status

Requirements:

- support internal/external attendees
- add tests

**GOV-STORY-004 — Implement Deliberation Minute**

**Cursor prompt**

Writing

Implement Deliberation Minute in kentender_governance.

Required fields:

- deliberation_session
- agenda_item
- minute_text
- recorded_by_user
- recorded_on
- status

Requirements:

- support draft/finalized/locked states
- add tests

**GOV-STORY-005 — Implement Recommendation Record**

**Cursor prompt**

Writing

Implement Recommendation Record in kentender_governance.

Required fields:

- deliberation_session
- agenda_item
- recommendation_type
- recommendation_text
- related_doctype
- related_docname
- recommended_by_user
- status

Requirements:

- add tests

**GOV-STORY-006 — Implement Resolution Record**

**Cursor prompt**

Writing

Implement Resolution Record in kentender_governance.

Required fields:

- deliberation_session
- agenda_item
- resolution_text
- resolution_date
- effective_status
- related_doctype
- related_docname

Requirements:

- add tests

**GOV-STORY-007 — Implement Follow Up Action**

**Cursor prompt**

Writing

Implement Follow Up Action in kentender_governance.

Required fields:

- deliberation_session
- resolution_record
- action_title
- action_description
- assigned_to_user
- due_date
- status
- completion_notes

Requirements:

- add tests

**GOV-STORY-008 — Implement Deliberation Status Event**

**Cursor prompt**

Writing

Implement Deliberation Status Event in kentender_governance.

Required fields:

- deliberation_session
- event_type
- event_datetime
- actor_user
- summary
- event_hash

Requirements:

- append-only event model
- add tests

**GOV-STORY-009 — Implement deliberation lifecycle services**

**Cursor prompt**

Writing

Implement deliberation lifecycle services in kentender_governance.

Suggested actions:

- schedule_deliberation_session(...)
- start_deliberation_session(...)
- complete_deliberation_session(...)
- lock_deliberation_session(...)

Requirements:

- create status events
- enforce sensible state transitions
- add tests

**GOV-STORY-010 — Implement resolution and follow-up action services**

**Cursor prompt**

Writing

Implement resolution/follow-up services in kentender_governance.

Suggested actions:

- issue_resolution(...)
- create_follow_up_action(...)
- complete_follow_up_action(...)

Requirements:

- keep governance trail explicit
- emit audit events
- add tests

**GOV-STORY-011 — Implement deliberation queue/report scaffolding and tests**

**Cursor prompt**

Writing

Implement deliberation test suite and lightweight queue/report scaffolding in kentender_governance.

Suggested queues/reports:

- Scheduled Deliberations
- Open Follow-Up Actions
- Resolution Register
- Deliberations by Linked Object

Requirements:

- meaningful coverage
- workspace-friendly scaffolding

**EPIC-GOV-002 — Complaints & Disputes**

**GOV-STORY-012 — Implement Complaint**

**Cursor prompt**

Writing

Implement Complaint in kentender_governance.

Required fields:

- business_id
- complaint_title
- status
- workflow_state
- complaint_type
- complaint_stage
- tender
- bid_submission
- evaluation_session
- award_decision
- contract
- complainant_type
- supplier
- complainant_name
- complainant_contact_email
- complainant_contact_phone
- complaint_summary
- complaint_details
- requested_remedy
- submission_datetime
- received_by_user
- admissibility_status
- admissibility_reason
- reviewed_by_user
- reviewed_on
- affects_award_process
- affects_contract_execution
- hold_required
- hold_scope
- hold_status
- decision_due_date
- actual_decision_date
- appeal_deadline
- closure_date
- is_anonymous
- is_locked
- exception_record
- remarks

Requirements:

- create the DocType
- require meaningful complaint details
- add tests

**GOV-STORY-013 — Implement Complaint Party**

**Cursor prompt**

Writing

Implement Complaint Party in kentender_governance.

Required fields:

- complaint
- party_role
- party_name
- supplier
- contact_details
- remarks

Requirements:

- add tests

**GOV-STORY-014 — Implement Complaint Evidence**

**Cursor prompt**

Writing

Implement Complaint Evidence in kentender_governance.

Required fields:

- complaint
- submitted_by_user
- submitted_by_party
- evidence_type
- file
- description
- submitted_on
- hash_value
- sensitivity_class
- remarks

Requirements:

- integrate with file control patterns where appropriate
- add tests

**GOV-STORY-015 — Implement Complaint Review Panel Assignment**

**Cursor prompt**

Writing

Implement Complaint Review Panel Assignment in kentender_governance.

Required fields:

- complaint
- user
- role_type
- assignment_status
- assigned_on
- notes

Requirements:

- add tests

**GOV-STORY-016 — Implement Complaint Review Record**

**Cursor prompt**

Writing

Implement Complaint Review Record in kentender_governance.

Required fields:

- complaint
- reviewer_user
- review_summary
- analysis_notes
- recommended_outcome
- submitted_on
- status

Requirements:

- add tests

**GOV-STORY-017 — Implement Complaint Decision**

**Cursor prompt**

Writing

Implement Complaint Decision in kentender_governance.

Required fields:

- business_id
- complaint
- status
- decision_datetime
- decided_by_user
- decision_result
- decision_summary
- detailed_reasoning
- remedy_type
- remedy_details
- award_decision_affected
- contract_affected
- requires_hold_release
- hold_release_datetime
- is_locked
- remarks

Requirements:

- add tests

**GOV-STORY-018 — Implement Complaint Action**

**Cursor prompt**

Writing

Implement Complaint Action in kentender_governance.

Required fields:

- complaint
- decision
- action_type
- target_object_type
- target_reference
- status
- executed_on
- executed_by_user
- notes

Requirements:

- add tests

**GOV-STORY-019 — Implement Appeal Record**

**Cursor prompt**

Writing

Implement Appeal Record in kentender_governance.

Required fields:

- complaint
- complaint_decision
- appeal_submitted_by
- appeal_summary
- appeal_details
- status
- decision_outcome
- decision_datetime
- remarks

Requirements:

- add tests

**GOV-STORY-020 — Implement Complaint Status Event**

**Cursor prompt**

Writing

Implement Complaint Status Event in kentender_governance.

Required fields:

- complaint
- event_type
- event_datetime
- actor_user
- summary
- event_hash

Requirements:

- append-only event model
- add tests

**GOV-STORY-021 — Implement complaint intake and admissibility services**

**Cursor prompt**

Writing

Implement complaint intake/admissibility services in kentender_governance.

Suggested actions:

- submit_complaint(...)
- review_complaint_admissibility(...)
- withdraw_complaint(...)

Requirements:

- require structured complaint details
- update admissibility state explicitly
- create status events
- add tests

**GOV-STORY-022 — Implement complaint hold application/release services**

**Cursor prompt**

Writing

Implement complaint hold services in kentender_governance.

Suggested actions:

- apply_procurement_hold(complaint_id)
- release_procurement_hold(complaint_id)

Requirements:

- support hold against award and/or contract progression
- integrate with award/contract readiness state through service calls
- add tests for representative hold/release cases

Constraints:

- do not directly mutate unrelated objects without controlled service calls

**GOV-STORY-023 — Implement complaint review and decision services**

**Cursor prompt**

Writing

Implement complaint review/decision services in kentender_governance.

Suggested actions:

- assign_complaint_reviewer(...)
- submit_complaint_review(...)
- issue_complaint_decision(...)

Requirements:

- use assignment-based access
- require admissibility before full review
- create status events
- add tests for representative flows

**GOV-STORY-024 — Implement complaint action execution services**

**Cursor prompt**

Writing

Implement complaint action execution services in kentender_governance.

Suggested action:

- execute_complaint_decision(decision_id)

Requirements:

- create and/or execute Complaint Action records
- trigger controlled downstream actions such as hold, resume, reopen evaluation, cancel award, suspend contract, etc.
- keep execution auditable
- add tests for representative cases

Constraints:

- do not bypass downstream service layers

**GOV-STORY-025 — Implement complaint queue/report scaffolding and tests**

**Cursor prompt**

Writing

Implement complaint test suite and lightweight queue/report scaffolding in kentender_governance.

Suggested queues/reports:

- Complaints Awaiting Admissibility
- Complaints Under Review
- Complaints With Active Hold
- Complaint Decisions
- Appeals

Requirements:

- meaningful coverage
- workspace-friendly scaffolding

**Recommended Cursor Execution Order**

Run in this order:

**Inspection**

1.  PROC-STORY-100
2.  PROC-STORY-101
3.  PROC-STORY-102
4.  PROC-STORY-103
5.  PROC-STORY-104
6.  PROC-STORY-105
7.  PROC-STORY-106
8.  PROC-STORY-107
9.  PROC-STORY-108
10. PROC-STORY-109
11. PROC-STORY-110
12. PROC-STORY-111
13. PROC-STORY-112
14. PROC-STORY-113
15. PROC-STORY-114
16. PROC-STORY-115
17. PROC-STORY-116

**Deliberations**

1.  GOV-STORY-001
2.  GOV-STORY-002
3.  GOV-STORY-003
4.  GOV-STORY-004
5.  GOV-STORY-005
6.  GOV-STORY-006
7.  GOV-STORY-007
8.  GOV-STORY-008
9.  GOV-STORY-009
10. GOV-STORY-010
11. GOV-STORY-011

**Complaints**

1.  GOV-STORY-012
2.  GOV-STORY-013
3.  GOV-STORY-014
4.  GOV-STORY-015
5.  GOV-STORY-016
6.  GOV-STORY-017
7.  GOV-STORY-018
8.  GOV-STORY-019
9.  GOV-STORY-020
10. GOV-STORY-021
11. GOV-STORY-022
12. GOV-STORY-023
13. GOV-STORY-024
14. GOV-STORY-025

**What this unlocks**

Once Wave 5 lands, you can run:

- **AT-INSP-001**
- governance meeting/minute tests
- **AT-CMP-001**

And you’ll have the final major public-sector control layers:

- verified delivery
- formal deliberation traceability
- lawful challenge and hold mechanisms

**Best next move**

After this, the natural continuation is the **Wave 6 ticket pack** for:

- Stores
- Assets
- Audit / Oversight hardening
- cross-cutting reporting and transparency

That is the downstream custody and compliance hardening layer.