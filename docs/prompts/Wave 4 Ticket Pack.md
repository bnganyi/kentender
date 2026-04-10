# Wave 4 Ticket Pack

**Sprint tracking:** [`WAVE 4 BACKLOG.md`](../dev/WAVE%204%20BACKLOG.md) — update **Status** / **Notes** per story when acceptance is met; keep this pack canonical for prompts and criteria.

**Wave 4 Epic Overview**

**EPIC-PROC-006 — Evaluation**

Owns:

- evaluation session
- evaluator assignments
- conflict declarations
- scoring records
- disqualification
- aggregation
- evaluation report

**EPIC-PROC-007 — Award & Approval**

Owns:

- award decision
- approval chain
- deviation handling
- notifications
- standstill
- readiness for contract

**EPIC-PROC-008 — Contract**

Owns:

- contract creation from award
- milestones and deliverables
- signing
- activation
- variations
- lifecycle events

**Recommended Wave 4 Build Order**

**Evaluation**

1.  PROC-STORY-057 — Evaluation Session
2.  PROC-STORY-058 — Evaluation Stage
3.  PROC-STORY-059 — Evaluator Assignment
4.  PROC-STORY-060 — Conflict of Interest Declaration
5.  PROC-STORY-061 — Evaluation Record
6.  PROC-STORY-062 — Evaluation Score Line
7.  PROC-STORY-063 — Evaluation Disqualification Record
8.  PROC-STORY-064 — Evaluation Aggregation Result
9.  PROC-STORY-065 — Evaluation Report
10. PROC-STORY-066 — Evaluation Approval / Submission Record
11. PROC-STORY-067 — initialize evaluation from opening service
12. PROC-STORY-068 — conflict declaration and evaluator access service
13. PROC-STORY-069 — scoring submission and stage progression services
14. PROC-STORY-070 — aggregation and ranking services
15. PROC-STORY-071 — evaluation report generation/submission services
16. PROC-STORY-072 — evaluation queue/report scaffolding and tests

**Award**

1.  PROC-STORY-073 — Award Decision
2.  PROC-STORY-074 — Award Approval Record
3.  PROC-STORY-075 — Award Deviation Record
4.  PROC-STORY-076 — Award Notification
5.  PROC-STORY-077 — Standstill Period
6.  PROC-STORY-078 — Award Outcome Line
7.  PROC-STORY-079 — Award Return Record
8.  PROC-STORY-080 — create award from evaluation service
9.  PROC-STORY-081 — award approval and final approval services
10. PROC-STORY-082 — deviation detection and handling service
11. PROC-STORY-083 — notification and standstill services
12. PROC-STORY-084 — contract readiness gate service
13. PROC-STORY-085 — award queue/report scaffolding and tests

**Contract**

1.  PROC-STORY-086 — Contract
2.  PROC-STORY-087 — Contract Party
3.  PROC-STORY-088 — Contract Milestone
4.  PROC-STORY-089 — Contract Deliverable
5.  PROC-STORY-090 — Contract Variation
6.  PROC-STORY-091 — Contract Approval Record
7.  PROC-STORY-092 — Contract Signing Record
8.  PROC-STORY-093 — Contract Status Event
9.  PROC-STORY-094 — create contract from award service
10. PROC-STORY-095 — contract approval and signature services
11. PROC-STORY-096 — activate contract service
12. PROC-STORY-097 — variation request/apply services
13. PROC-STORY-098 — contract lifecycle services (suspend/resume/terminate/close)
14. PROC-STORY-099 — contract queue/report scaffolding and tests

**EPIC-PROC-006 — Evaluation**

**PROC-STORY-057 — Implement Evaluation Session**

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-057
- Epic: EPIC-PROC-006
- Title: Implement Evaluation Session

Context:

- App: kentender_procurement
- Evaluation Session is the controlled evaluation process for a tender after bid opening.
- It must link to opened bids and tender criteria context.

Task:  
Implement the Evaluation Session DocType.

Required fields:

- business_id
- tender
- status
- workflow_state
- procuring_entity
- procurement_method
- evaluation_mode
- opening_session
- opening_register
- related_tender_criteria_snapshot_hash
- evaluation_committee_chair
- evaluation_secretariat_user
- committee_assignment_ref
- total_assigned_evaluators
- conflict_clearance_status
- conflict_clearance_completed_on
- candidate_bid_count
- disqualified_bid_count
- responsive_bid_count
- recommended_bid_submission
- recommended_supplier
- recommended_amount
- currency
- evaluation_start_datetime
- evaluation_end_datetime
- submission_datetime
- is_locked_for_edit
- returned_reason
- exception_record
- remarks

Requirements:

1.  Create the DocType.
2.  Keep it linked to opened-bid context only.
3.  Add basic validation for tender/opening linkage.
4.  Add tests for valid create and invalid missing-opening context.

Constraints:

- Do not implement stages or scoring here.
- Keep controller thin and workflow-ready.

Acceptance criteria:

- DocType exists
- opening linkage validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-058 — Implement Evaluation Stage**

**Cursor prompt**

Writing

Implement Evaluation Stage in kentender_procurement.

Required fields:

- evaluation_session
- stage_type
- stage_order
- status
- started_on
- completed_on
- is_scoring_stage
- is_disqualifying_stage
- minimum_pass_mark
- notes

Requirements:

- support stages such as Preliminary Examination, Eligibility Review, Mandatory Compliance, Technical Evaluation, Financial Evaluation, Combined Ranking
- enforce unique stage_order per session
- add tests for valid stage creation and duplicate-order blocking

Constraints:

- do not implement stage progression service here

**PROC-STORY-059 — Implement Evaluator Assignment**

**Cursor prompt**

Writing

Implement Evaluator Assignment in kentender_procurement.

Required fields:

- evaluation_session
- user
- committee_role
- assignment_status
- appointed_on
- withdrawn_on
- replacement_user
- is_scoring_member
- notes

Requirements:

- support Chair, Member, Secretary, Observer
- add tests for valid assignment linkage and representative status changes

Constraints:

- do not implement access service here

**PROC-STORY-060 — Implement Conflict of Interest Declaration**

**Cursor prompt**

Writing

Implement Conflict of Interest Declaration in kentender_procurement.

Required fields:

- evaluation_session
- evaluator_user
- declaration_status
- declaration_datetime
- conflict_summary
- reviewed_by
- reviewed_on
- review_notes
- related_supplier
- related_bid_submission

Requirements:

- support statuses such as Pending, Declared No Conflict, Declared Conflict, Rejected from Participation, Reviewed and Cleared
- add tests for valid creation and linkage

Constraints:

- do not implement review workflow service here

**PROC-STORY-061 — Implement Evaluation Record**

**Cursor prompt**

Writing

Implement Evaluation Record in kentender_procurement.

Required fields:

- business_id
- evaluation_session
- evaluation_stage
- bid_submission
- evaluator_user
- supplier
- status
- total_stage_score
- pass_fail_result
- summary_comments
- submitted_on
- locked_on

Requirements:

- one evaluator-stage-bid active record model
- add tests for valid create and duplicate-active record blocking where reasonable

Constraints:

- do not implement score submission service here

**PROC-STORY-062 — Implement Evaluation Score Line**

**Cursor prompt**

Writing

Implement Evaluation Score Line under Evaluation Record in kentender_procurement.

Required fields:

- tender_criteria
- criteria_type
- criteria_title
- score_value
- pass_fail_result
- max_score
- weight_percentage
- weighted_score
- comments
- is_disqualifying_failure
- formula_result_json

Requirements:

- support pass/fail and numeric scoring
- validate score ranges coherently
- add tests for numeric and pass/fail criteria behavior

Constraints:

- do not implement final aggregation here

**PROC-STORY-063 — Implement Evaluation Disqualification Record**

**Cursor prompt**

Writing

Implement Evaluation Disqualification Record in kentender_procurement.

Required fields:

- evaluation_session
- evaluation_stage
- bid_submission
- supplier
- disqualification_reason_type
- reason_details
- decided_by_user
- decided_on
- status
- exception_record

Requirements:

- support explicit disqualification reasons
- add tests for valid create/linkage

Constraints:

- do not implement stage removal logic here

**PROC-STORY-064 — Implement Evaluation Aggregation Result**

**Cursor prompt**

Writing

Implement Evaluation Aggregation Result in kentender_procurement.

Required fields:

- evaluation_session
- bid_submission
- supplier
- preliminary_result
- technical_score_total
- technical_score_average
- financial_score
- combined_score
- ranking_position
- overall_result
- calculation_status

Requirements:

- create derived-result storage model
- add tests for valid create/linkage

Constraints:

- do not implement calculation service here
- keep it service-owned, not manually edited

**PROC-STORY-065 — Implement Evaluation Report**

**Cursor prompt**

Writing

Implement Evaluation Report in kentender_procurement.

Required fields:

- business_id
- evaluation_session
- tender
- status
- recommended_bid_submission
- recommended_supplier
- recommended_amount
- currency
- responsive_bid_count
- non_responsive_bid_count
- disqualified_bid_count
- process_summary
- evaluation_method_summary
- committee_observations
- recommendation_justification
- special_conditions_notes
- submitted_by_user
- submitted_on
- approved_for_submission_by_chair
- locked_hash
- report_file

Requirements:

- create the DocType
- add tests for valid create and required recommendation justification behavior

Constraints:

- do not generate or submit report here

**PROC-STORY-066 — Implement Evaluation Approval / Submission Record**

**Cursor prompt**

Writing

Implement Evaluation Approval / Submission Record in kentender_procurement.

Required fields:

- evaluation_session
- evaluation_report
- actor_user
- actor_role
- action_type
- action_datetime
- comments

Action types:

- Finalize
- Submit
- Return for Revision
- Lock

Requirements:

- create model
- add tests for valid linkage/create

Constraints:

- do not implement action services here

**PROC-STORY-067 — Implement initialize-evaluation-from-opening service**

**Cursor prompt**

Writing

Implement initialize_evaluation_session(tender_id or opening_session_id) in kentender_procurement.

Requirements:

- create Evaluation Session from a completed opening context
- derive candidate bid count from opened bids
- initialize default evaluation stages based on configured mode
- add tests for successful initialization and invalid pre-opening case blocking

Constraints:

- do not assign evaluators automatically unless minimally needed and clearly justified

**PROC-STORY-068 — Implement conflict declaration and evaluator access service**

**Cursor prompt**

Writing

Implement evaluator conflict/access service logic in kentender_procurement.

Suggested service goals:

- submit_conflict_declaration(...)
- validate_evaluator_access(evaluation_session, user, bid_submission=None)

Requirements:

- evaluator must be assigned
- evaluator must have acceptable conflict declaration status before access
- use assignment-based access patterns
- add tests for allowed and denied access scenarios

Constraints:

- keep peer score visibility rules separate from this story if cleaner

**PROC-STORY-069 — Implement scoring submission and stage progression services**

**Cursor prompt**

Writing

Implement evaluation scoring/stage services in kentender_procurement.

Suggested actions:

- submit_evaluation_record(record_id)
- start_evaluation_stage(stage_id)
- complete_evaluation_stage(stage_id)
- propose_disqualification(...)
- confirm_disqualification(...)

Requirements:

- lock score records on submit
- prevent scoring by unassigned/uncleared evaluators
- support stage completion only when valid
- emit audit events
- add tests for representative flows

Constraints:

- do not implement final aggregation here
- keep actions explicit and server-side

**PROC-STORY-070 — Implement aggregation and ranking services**

**Cursor prompt**

Writing

Implement evaluation aggregation/ranking services in kentender_procurement.

Suggested actions:

- aggregate_technical_scores(...)
- calculate_financial_score(...)
- calculate_final_ranking(...)
- aggregate_evaluation_results(...)

Requirements:

- keep aggregation service-owned
- support average technical score and weighted final score first-pass logic
- store outputs in Evaluation Aggregation Result
- add tests for representative scoring/ranking cases

Constraints:

- do not allow manual editing of derived aggregation results
- keep formulas explicit and readable

**PROC-STORY-071 — Implement evaluation report generation/submission services**

**Cursor prompt**

Writing

Implement evaluation report generation/submission services in kentender_procurement.

Suggested actions:

- generate_evaluation_report(evaluation_session_id)
- submit_evaluation_report(evaluation_report_id)
- return_evaluation_for_revision(...)

Requirements:

- require finalized aggregation context before generation/submission
- compile recommendation summary and counts
- lock report appropriately on submission
- create submission records and audit events
- add tests for generation, submission, and return flows

Constraints:

- do not create award decision here

**PROC-STORY-072 — Implement evaluation queue/report scaffolding and tests**

**Cursor prompt**

Writing

Implement evaluation test suite and lightweight queue/report scaffolding in kentender_procurement.

Suggested queues/reports:

- My Assigned Evaluations
- Conflict Declarations Pending
- Evaluation Sessions In Progress
- Evaluation Reports Awaiting Submission
- Disqualification Summary
- Ranked Bid Summary

Requirements:

- provide meaningful evaluation coverage
- keep queue/report scaffolding workspace-friendly

Constraints:

- no heavy dashboards
- focus on correctness and UAT utility

**EPIC-PROC-007 — Award & Approval**

**PROC-STORY-073 — Implement Award Decision**

**Cursor prompt**

Writing

Implement Award Decision in kentender_procurement.

Required fields:

- business_id
- tender
- evaluation_session
- evaluation_report
- status
- workflow_state
- approval_status
- recommended_bid_submission
- recommended_supplier
- recommended_amount
- currency
- approved_bid_submission
- approved_supplier
- approved_amount
- award_type
- approval_decision_date
- final_approval_datetime
- accounting_officer_user
- head_of_procurement_user
- tender_committee_ref
- is_deviation_from_recommendation
- deviation_record
- standstill_required
- standstill_period
- ready_for_contract_creation
- exception_record
- responsive_bid_count
- non_responsive_bid_count
- disqualified_bid_count
- award_summary_notes
- decision_justification
- notification_status
- successful_notification_sent_on
- unsuccessful_notification_sent_on
- is_locked
- lock_reason
- remarks

Requirements:

- create the DocType
- keep it approval-controlled and contract-gating ready
- add tests

Constraints:

- do not implement approval services here

**PROC-STORY-074 — Implement Award Approval Record**

**Cursor prompt**

Writing

Implement Award Approval Record in kentender_procurement.

Required fields:

- award_decision
- workflow_step
- approver_user
- approver_role
- action_type
- action_datetime
- comments
- decision_level
- exception_record

Requirements:

- create model
- align with other approval record patterns
- add tests

**PROC-STORY-075 — Implement Award Deviation Record**

**Cursor prompt**

Writing

Implement Award Deviation Record in kentender_procurement.

Required fields:

- award_decision
- recommended_bid_submission
- approved_bid_submission
- recommended_supplier
- approved_supplier
- deviation_type
- deviation_reason
- authorized_by_user
- authorized_on
- status
- exception_record

Requirements:

- create model
- support explicit deviation capture
- add tests

Constraints:

- do not handle approval flow here

**PROC-STORY-076 — Implement Award Notification**

**Cursor prompt**

Writing

Implement Award Notification in kentender_procurement.

Required fields:

- business_id
- award_decision
- tender
- supplier
- bid_submission
- notification_type
- status
- channel
- subject
- message_body
- sent_on
- delivery_status
- delivery_reference
- generated_by_user
- acknowledged_on
- standstill_message_included

Requirements:

- create the DocType
- support successful/unsuccessful/cancellation styles
- add tests

**PROC-STORY-077 — Implement Standstill Period**

**Cursor prompt**

Writing

Implement Standstill Period in kentender_procurement.

Required fields:

- award_decision
- start_datetime
- end_datetime
- status
- triggered_by_notification_datetime
- complaint_hold_flag
- hold_reason
- released_for_contract_on
- remarks

Requirements:

- create model
- validate date coherence
- add tests

**PROC-STORY-078 — Implement Award Outcome Line**

**Cursor prompt**

Writing

Implement Award Outcome Line under Award Decision in kentender_procurement.

Required fields:

- bid_submission
- supplier
- lot
- outcome_type
- evaluated_amount
- approved_amount
- ranking_position
- outcome_notes

Requirements:

- create model
- support lot-aware and whole-award cases
- add tests

**PROC-STORY-079 — Implement Award Return Record**

**Cursor prompt**

Writing

Implement Award Return Record in kentender_procurement.

Required fields:

- award_decision
- returned_by_user
- returned_by_role
- return_type
- return_reason
- returned_on
- status

Requirements:

- create model
- support explicit return-for-rework paths
- add tests

**PROC-STORY-080 — Implement create-award-from-evaluation service**

**Cursor prompt**

Writing

Implement create_award_decision_from_evaluation(evaluation_session_id) in kentender_procurement.

Requirements:

- require submitted evaluation report
- carry recommended bidder/supplier/amount into draft award decision
- create outcome lines from aggregation results as appropriate
- add tests for valid create and missing-report blocking

Constraints:

- do not final approve here

**PROC-STORY-081 — Implement award approval and final approval services**

**Cursor prompt**

Writing

Implement award approval services in kentender_procurement.

Suggested actions:

- approve_award_step(...)
- final_approve_award(...)
- reject_award(...)
- return_award_for_revision(...)

Requirements:

- enforce separation of duty from evaluation roles
- create approval records
- emit audit events
- add tests for representative flows and blocked invalid actors

Constraints:

- do not create contract here
- keep final approval explicit and server-side

**PROC-STORY-082 — Implement deviation detection and handling service**

**Cursor prompt**

Writing

Implement award deviation handling service in kentender_procurement.

Requirements:

- detect when approved outcome differs materially from recommendation
- create or require Award Deviation Record
- block final approval when deviation handling is incomplete
- add tests for no-deviation and deviation scenarios

Constraints:

- do not silently override recommendation

**PROC-STORY-083 — Implement notification and standstill services**

**Cursor prompt**

Writing

Implement award notification and standstill services in kentender_procurement.

Suggested actions:

- send_award_notifications(award_decision_id)
- initialize_standstill_period(award_decision_id)
- release_award_for_contract(award_decision_id)

Requirements:

- generate Award Notification records
- initialize standstill where required
- keep contract readiness blocked while standstill is active
- add tests for representative flows

Constraints:

- do not implement complaint module here
- keep external delivery abstract if needed

**PROC-STORY-084 — Implement contract readiness gate service**

**Cursor prompt**

Writing

Implement contract readiness gate logic in kentender_procurement.

Requirements:

- determine whether an award is ready for contract creation based on:
    - approval status
    - standstill state
    - complaint hold state
    - cancellation/rejection state
- add tests for ready and blocked cases

Constraints:

- keep logic reusable by contract creation service

**PROC-STORY-085 — Implement award queue/report scaffolding and tests**

**Cursor prompt**

Writing

Implement award test suite and lightweight queue/report scaffolding in kentender_procurement.

Suggested queues/reports:

- Awards Pending Approval
- Awards Pending Final Approval
- Standstill Active Awards
- Awards Ready for Contract
- Deviation Register
- Notification Status

Requirements:

- meaningful test coverage
- workspace-friendly queue/report scaffolding

Constraints:

- no heavy dashboards

**EPIC-PROC-008 — Contract**

**PROC-STORY-086 — Implement Contract**

**Cursor prompt**

Writing

Implement Contract in kentender_procurement.

Required fields:

- business_id
- contract_title
- status
- workflow_state
- approval_status
- award_decision
- tender
- procurement_plan_item
- evaluation_session
- approved_bid_submission
- supplier
- procuring_entity
- requesting_department
- responsible_department
- contract_manager_user
- procurement_officer_user
- entity_strategic_plan
- program
- sub_program
- output_indicator
- performance_target
- national_objective
- budget
- budget_line
- funding_source
- commitment_status
- related_budget_commitment_ref
- contract_type
- contract_value
- currency
- tax_inclusive_flag
- retention_applicable
- retention_terms
- performance_security_required
- performance_security_details
- payment_terms_summary
- contract_start_date
- contract_end_date
- signing_deadline
- actual_signed_date
- actual_activation_date
- planned_completion_date
- scope_summary
- special_conditions
- variation_count
- latest_variation_ref
- completion_percent
- is_locked
- lock_reason
- termination_reason
- closure_notes
- exception_record
- remarks
- draft_contract_document
- signed_contract_document
- generated_contract_version_hash
- signed_document_hash

Requirements:

- create the DocType
- validate core award linkage and date sanity
- add tests

Constraints:

- do not implement milestones/variations/signing services here

**PROC-STORY-087 — Implement Contract Party**

**Cursor prompt**

Writing

Implement Contract Party under Contract in kentender_procurement.

Required fields:

- party_type
- party_name
- supplier
- contact_person
- contact_email
- contact_phone
- role_summary

Requirements:

- create model
- support main entity/supplier parties first
- add tests

**PROC-STORY-088 — Implement Contract Milestone**

**Cursor prompt**

Writing

Implement Contract Milestone in kentender_procurement.

Required fields:

- business_id
- contract
- milestone_no
- title
- description
- planned_due_date
- actual_completion_date
- milestone_value
- completion_percent
- status
- deliverable_summary
- inspection_required
- notes

Requirements:

- create model
- validate milestone dates against contract range at a basic level
- add tests

**PROC-STORY-089 — Implement Contract Deliverable**

**Cursor prompt**

Writing

Implement Contract Deliverable in kentender_procurement.

Required fields:

- contract
- contract_milestone
- deliverable_title
- description
- expected_quantity
- uom
- expected_delivery_date
- status
- inspection_required
- notes

Requirements:

- create model
- support milestone-linked and unlinked deliverables
- add tests

**PROC-STORY-090 — Implement Contract Variation**

**Cursor prompt**

Writing

Implement Contract Variation in kentender_procurement.

Required fields:

- business_id
- contract
- variation_no
- variation_type
- status
- reason
- value_change_amount
- days_extension
- old_contract_value
- new_contract_value
- old_end_date
- new_end_date
- requested_by_user
- requested_on
- approved_by_user
- approved_on
- budget_validation_status
- exception_record
- impact_notes

Requirements:

- create model
- support value/time/scope adjustments
- add tests

Constraints:

- do not apply variation here

**PROC-STORY-091 — Implement Contract Approval Record**

**Cursor prompt**

Writing

Implement Contract Approval Record in kentender_procurement.

Required fields:

- contract
- workflow_step
- approver_user
- approver_role
- action_type
- action_datetime
- comments
- decision_level
- exception_record

Requirements:

- create model
- add tests

**PROC-STORY-092 — Implement Contract Signing Record**

**Cursor prompt**

Writing

Implement Contract Signing Record in kentender_procurement.

Required fields:

- contract
- signing_method
- signed_by_entity_user
- signed_by_supplier_name
- signed_by_supplier_user
- signed_on
- status
- signature_reference
- signed_document
- hash_value
- notes

Requirements:

- create model
- support manual and digital signature modes
- add tests

**PROC-STORY-093 — Implement Contract Status Event**

**Cursor prompt**

Writing

Implement Contract Status Event in kentender_procurement.

Required fields:

- contract
- event_type
- event_datetime
- actor_user
- summary
- related_variation
- related_milestone
- status_result
- event_hash

Requirements:

- create model
- support append-only lifecycle events
- add tests

**PROC-STORY-094 — Implement create-contract-from-award service**

**Cursor prompt**

Writing

Implement create_contract_from_award(award_decision_id) in kentender_procurement.

Requirements:

- require award to pass contract readiness gate
- inherit award/tender/plan/strategy/budget context
- create draft Contract
- create initial status event
- add tests for ready and blocked cases

Constraints:

- do not activate contract here

**PROC-STORY-095 — Implement contract approval and signature services**

**Cursor prompt**

Writing

Implement contract approval/signature services in kentender_procurement.

Suggested actions:

- submit_contract_for_review(...)
- approve_contract(...)
- send_contract_for_signature(...)
- record_contract_signature(...)

Requirements:

- create approval records and signing records
- enforce signed vs approved distinction
- emit audit events
- add tests for representative flows

Constraints:

- do not activate contract here

**PROC-STORY-096 — Implement activate-contract service**

**Cursor prompt**

Writing

Implement activate_contract(contract_id) in kentender_procurement.

Requirements:

- require contract approval and completed signing
- require signed document/reference present
- set activation metadata and status
- create status event
- add tests for success and blocked preconditions

Constraints:

- do not bypass signing state

**PROC-STORY-097 — Implement variation request/apply services**

**Cursor prompt**

Writing

Implement contract variation services in kentender_procurement.

Suggested actions:

- request_contract_variation(...)
- approve_contract_variation(...)
- apply_contract_variation(variation_id)

Requirements:

- prevent silent edits to active contract core terms
- integrate budget validation service for upward value changes
- create status events
- add tests for representative variation cases

Constraints:

- do not write ledger directly from contract module

**PROC-STORY-098 — Implement contract lifecycle services**

**Cursor prompt**

Writing

Implement contract lifecycle services in kentender_procurement.

Suggested actions:

- suspend_contract(...)
- resume_contract(...)
- terminate_contract(...)
- close_contract(...)

Requirements:

- update status coherently
- create status events
- enforce incompatible-state blocking
- add tests for representative lifecycle transitions

Constraints:

- keep actions explicit and auditable

**PROC-STORY-099 — Implement contract queue/report scaffolding and tests**

**Cursor prompt**

Writing

Implement contract test suite and lightweight queue/report scaffolding in kentender_procurement.

Suggested queues/reports:

- Draft Contracts
- Contracts Pending Signature
- Active Contracts
- Variations Awaiting Action
- Contracts Near End Date
- Suspended/Terminated Contracts

Requirements:

- meaningful contract coverage
- workspace-friendly queue/report scaffolding

Constraints:

- no heavy dashboards

**Recommended Cursor Execution Order**

Run in this order:

**Evaluation**

1.  PROC-STORY-057
2.  PROC-STORY-058
3.  PROC-STORY-059
4.  PROC-STORY-060
5.  PROC-STORY-061
6.  PROC-STORY-062
7.  PROC-STORY-063
8.  PROC-STORY-064
9.  PROC-STORY-065
10. PROC-STORY-066
11. PROC-STORY-067
12. PROC-STORY-068
13. PROC-STORY-069
14. PROC-STORY-070
15. PROC-STORY-071
16. PROC-STORY-072

**Award**

1.  PROC-STORY-073
2.  PROC-STORY-074
3.  PROC-STORY-075
4.  PROC-STORY-076
5.  PROC-STORY-077
6.  PROC-STORY-078
7.  PROC-STORY-079
8.  PROC-STORY-080
9.  PROC-STORY-081
10. PROC-STORY-082
11. PROC-STORY-083
12. PROC-STORY-084
13. PROC-STORY-085

**Contract**

1.  PROC-STORY-086
2.  PROC-STORY-087
3.  PROC-STORY-088
4.  PROC-STORY-089
5.  PROC-STORY-090
6.  PROC-STORY-091
7.  PROC-STORY-092
8.  PROC-STORY-093
9.  PROC-STORY-094
10. PROC-STORY-095
11. PROC-STORY-096
12. PROC-STORY-097
13. PROC-STORY-098
14. PROC-STORY-099

**What this unlocks**

Once Wave 4 lands, you can run real UAT for:

- **AT-EVAL-001**
- **AT-AWD-001**
- **AT-CON-001**

And you’ll have the full decision-to-obligation chain:

- opened bids
- scored evaluation
- award approval
- contract creation and activation