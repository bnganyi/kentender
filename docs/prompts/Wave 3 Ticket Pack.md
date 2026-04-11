# Wave 3 Ticket PackEpic Overview

**EPIC-PROC-003 — Tender Management**

Owns:

- tender creation from plan item
- lots
- criteria
- tender documents
- clarifications
- amendments
- approval and publication
- supplier visibility rules

**EPIC-PROC-004 — Bid Submission**

Owns:

- bid draft
- bid sections
- bid documents
- final submission
- receipt generation
- withdrawal and resubmission
- sealed access foundations

**EPIC-PROC-005 — Bid Opening**

Owns:

- opening session
- opening attendance
- candidate bid resolution
- atomic opening action
- register generation
- opening event logging

**Recommended Wave 3 Build Order**

**Tender**

1.  PROC-STORY-023 — Tender DocType
2.  PROC-STORY-024 — Tender Lot
3.  PROC-STORY-025 — Tender Criteria
4.  PROC-STORY-026 — Tender Document
5.  PROC-STORY-027 — Tender Approval Record
6.  PROC-STORY-028 — Tender Visibility Rule
7.  PROC-STORY-029 — Tender Clarification
8.  PROC-STORY-030 — Tender Amendment
9.  PROC-STORY-031 — create tender from plan item service
10. PROC-STORY-032 — tender validation and publication readiness service
11. PROC-STORY-033 — tender approval/publish actions
12. PROC-STORY-034 — clarification/amendment actions
13. PROC-STORY-035 — tender queue/report scaffolding and tests

**Bid Submission**

1.  PROC-STORY-036 — Bid Submission
2.  PROC-STORY-037 — Bid Envelope Section
3.  PROC-STORY-038 — Bid Document
4.  PROC-STORY-039 — Bid Submission Event
5.  PROC-STORY-040 — Bid Receipt
6.  PROC-STORY-041 — Bid Withdrawal Record
7.  PROC-STORY-042 — Bid Validation Issue
8.  PROC-STORY-043 — bid draft/create/validate services
9.  PROC-STORY-044 — final submit and receipt generation service
10. PROC-STORY-045 — withdraw/resubmit services
11. PROC-STORY-046 — sealed access integration and tests
12. PROC-STORY-047 — bid queue/report scaffolding and tests

**Bid Opening**

1.  PROC-STORY-048 — Bid Opening Session
2.  PROC-STORY-049 — Bid Opening Attendance
3.  PROC-STORY-050 — Bid Opening Register and lines
4.  PROC-STORY-051 — Bid Opening Event Log
5.  PROC-STORY-052 — opening precondition validation service
6.  PROC-STORY-053 — candidate bid set resolution service
7.  PROC-STORY-054 — atomic opening execution service
8.  PROC-STORY-055 — register locking and post-opening status updates
9.  PROC-STORY-056 — opening queue/report scaffolding and tests

## Wave 3 — Repo hygiene and Minimal Golden UAT

Applies to every story that adds or changes **user-visible** tender/bid/opening behaviour in `kentender_procurement` (DocTypes, services, permissions, or data shapes the desk and personas exercise).

1. **`bench migrate`** on the target site when DocType JSON changes.
2. **`bench run-tests --app kentender_procurement`** — keep the suite green for the story.
3. **Minimal Golden UAT** — follow [`Minimal Golden UAT`](../../.cursor/rules/kentender-minimal-golden-uat.mdc) (Cursor rule) and [`uat/seed_packs/minimal_golden/README.md`](../../uat/seed_packs/minimal_golden/README.md). Use the **canonical users and roles** from [`minimal_golden_canonical.json`](../../kentender/kentender/uat/minimal_golden/data/minimal_golden_canonical.json) (e.g. `procurement.test@ken-tender.test` → **Procurement Officer**).
   - **Extend** the canonical JSON (and the mirror under `uat/seed_packs/minimal_golden/`), **`load_*`** helpers, **`reset_minimal_golden_data`**, and **`verify_minimal_golden`** whenever the story should leave a **deterministic row** in the golden dataset (or document in the story/PR why not).
   - **On dev/UAT sites** used for implementation follow-along, after the story’s code is in place, run the **full seed** and **verify** so the database matches the loaders (replace `<site>` with your site name):

     ```bash
     bench --site <site> execute kentender.uat.minimal_golden.commands.seed_minimal_golden_console
     bench --site <site> execute kentender.uat.minimal_golden.commands.verify_minimal_golden_console
     ```

**EPIC-PROC-003 — Tender Management**

**PROC-STORY-023 — Implement Tender DocType**

**App:** kentender_procurement  
**Priority:** Critical  
**Depends on:** plan item model, plan-to-tender link foundation

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-023
- Epic: EPIC-PROC-003
- Title: Implement Tender DocType

Context:

- App: kentender_procurement
- Tender is the formal market-facing solicitation object.
- It must originate from an approved procurement plan item and carry planning, strategy, and budget context forward.

Task:  
Implement the Tender DocType.

Required fields:

- business_id
- title
- tender_number
- status
- workflow_state
- approval_status
- procurement_plan
- procurement_plan_item
- plan_to_tender_link
- origin_type
- procuring_entity
- requesting_department
- responsible_department
- procurement_officer
- head_of_procurement_user
- procurement_category
- procurement_method
- tender_type
- is_multi_lot
- is_framework_related
- is_re_tender
- parent_tender
- is_emergency_path
- description
- short_description
- scope_summary
- estimated_amount
- currency
- bid_validity_days
- tender_security_required
- tender_security_description
- submission_mode
- allows_withdrawal_before_deadline
- allows_resubmission_before_deadline
- entity_strategic_plan
- program
- sub_program
- output_indicator
- performance_target
- national_objective
- budget
- budget_line
- funding_source
- budget_alignment_status
- publication_datetime
- clarification_deadline
- submission_deadline
- opening_datetime
- evaluation_start_target
- award_target_date
- contract_start_target_date
- visibility_scope
- supplier_eligibility_rule_mode
- reserved_group_type
- public_disclosure_stage
- is_publicly_disclosable
- submission_status
- amendment_count
- clarification_count
- latest_amendment_ref
- cancellation_reason
- withdrawal_reason
- is_locked
- lock_reason
- remarks
- sensitivity_class

Requirements:

1.  Create the DocType.
2.  Keep it workflow-ready and publication-controlled.
3.  Validate core date relationships at a basic level.
4.  Keep planning, strategy, and budget fields structured for inherited linkage.
5.  Add tests for:
    - valid create
    - invalid deadline sequencing
    - missing plan item blocked where required

Constraints:

- Do not implement tender lots/criteria/documents here.
- Do not implement publication service here.
- Keep the controller thin; business actions belong in services.

Acceptance criteria:

- Tender DocType exists
- basic structural validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-024 — Implement Tender Lot**

**Cursor prompt**

Writing

Implement Tender Lot in kentender_procurement.

Required fields:

- tender
- lot_no
- lot_title
- description
- estimated_amount
- currency
- budget_line
- procurement_method
- status
- award_status
- requires_separate_financial_quote

Requirements:

- validate parent tender is multi-lot when lots exist
- support lot numbering and amount capture
- add tests for valid lot creation and invalid non-multi-lot usage

Constraints:

- do not implement lot award logic here
- keep as a structured tender child/linked object

**PROC-STORY-025 — Implement Tender Criteria**

**Cursor prompt**

Writing

Implement Tender Criteria in kentender_procurement.

Required fields:

- tender
- lot
- criteria_type
- criteria_code
- criteria_title
- description
- score_type
- max_score
- weight_percentage
- minimum_pass_mark
- display_order
- is_required
- applies_to_stage
- status

Requirements:

- support mandatory, technical, financial, eligibility, and preliminary criteria
- validate score-related fields coherently
- add tests for pass/fail vs numeric score validation

Constraints:

- do not implement evaluation aggregation here
- criteria become locked after publication later, but only scaffold that behavior if needed

**PROC-STORY-026 — Implement Tender Document**

**Cursor prompt**

Writing

Implement Tender Document in kentender_procurement.

Required fields:

- tender
- lot
- document_type
- file
- document_title
- document_version_no
- status
- is_mandatory_for_supplier_response
- sensitivity_class
- uploaded_by
- uploaded_at
- hash_value
- supersedes_document

Requirements:

- integrate with shared typed attachment/document concepts where appropriate
- support versioning/supersession basics
- add tests for valid linkage and required metadata

Constraints:

- do not implement supplier response validation here
- do not expose raw file access shortcuts

**PROC-STORY-027 — Implement Tender Approval Record**

**Cursor prompt**

Writing

Implement Tender Approval Record in kentender_procurement.

Required fields:

- tender
- workflow_step
- approver_user
- approver_role
- action_type
- action_datetime
- comments
- decision_level
- exception_record

Requirements:

- keep append-only in practical use
- align with other approval record patterns
- add linkage tests

**PROC-STORY-028 — Implement Tender Visibility Rule**

**Cursor prompt**

Writing

Implement Tender Visibility Rule in kentender_procurement.

Required fields:

- tender
- rule_type
- rule_value
- status
- remarks

Rule types should support:

- Supplier Category
- Invitation List
- Reserved Group
- Compliance Gate
- Geographic Restriction
- Prequalification List

Requirements:

- create a flexible but simple first-pass visibility rule model
- add tests for valid rule creation

Constraints:

- do not implement full supplier eligibility engine here

**PROC-STORY-029 — Implement Tender Clarification**

**Cursor prompt**

Writing

Implement Tender Clarification in kentender_procurement.

Required fields:

- business_id
- tender
- supplier
- question_submitted_by
- question_datetime
- question_text
- response_text
- response_datetime
- responded_by_user
- status
- visibility_mode
- is_response_official
- related_amendment

Requirements:

- create the DocType
- support question/response lifecycle
- add tests for valid create and basic status transitions

Constraints:

- do not implement portal submission flow here
- do not implement final fairness publication logic here

**PROC-STORY-030 — Implement Tender Amendment**

**Cursor prompt**

Writing

Implement Tender Amendment in kentender_procurement.

Required fields:

- business_id
- tender
- amendment_no
- amendment_type
- change_summary
- reason
- effective_datetime
- requires_deadline_extension
- new_submission_deadline
- new_opening_datetime
- status
- approved_by
- published_by
- published_at
- related_document

Requirements:

- create the DocType
- support explicit post-publication change records
- add tests for valid amendment creation and deadline field coherence

Constraints:

- do not apply amendments automatically in this story

**PROC-STORY-031 — Implement create-tender-from-plan-item service**

**Cursor prompt**

Writing

You are implementing a bounded service-action feature in a modular Frappe-based system called KenTender.

Story:

- ID: PROC-STORY-031
- Epic: EPIC-PROC-003
- Title: Implement create-tender-from-plan-item service

Context:

- Tender must originate from an approved procurement plan item.
- Critical inherited data must come from the plan item, not manual re-entry.

Task:  
Implement create_tender_from_plan_item(plan_item_id).

Requirements:

1.  Validate plan item eligibility for tender creation.
2.  Create Tender with inherited planning, strategy, budget, entity, and schedule context.
3.  Create Plan to Tender Link.
4.  Update plan item tender creation status fields.
5.  Add tests for:
    - successful create
    - ineligible item blocked
    - inherited fields copied correctly

Constraints:

- Do not publish the tender here.
- Do not create lots/criteria/documents automatically unless clearly justified and minimal.
- Keep logic service-based and auditable.

Acceptance criteria:

- tender can be created from eligible plan item only
- link and inherited fields are correct
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**PROC-STORY-032 — Implement tender validation and publication-readiness service**

**Cursor prompt**

Writing

Implement tender validation/publication-readiness service in kentender_procurement.

Required service goals:

- validate tender date coherence
- validate plan item linkage
- validate mandatory criteria presence
- validate mandatory document presence
- validate visibility rule presence where method requires it
- return structured readiness result

Requirements:

- reusable service under services/
- structured pass/fail output
- tests for readiness pass and fail scenarios

Constraints:

- do not perform publication in this story
- keep validation explainable

**PROC-STORY-033 — Implement tender approval and publish actions**

**Cursor prompt**

Writing

Implement tender action services in kentender_procurement:

- submit_tender_for_review
- approve_tender
- publish_tender
- cancel_tender
- withdraw_tender

Requirements:

- create approval records where appropriate
- use workflow guards
- use publication-readiness checks before publish
- set publication metadata and submission status correctly
- emit audit events
- add tests for happy path and blocking scenarios

Constraints:

- do not allow publication by direct field edit
- keep business actions explicit and server-side

**PROC-STORY-034 — Implement clarification and amendment actions**

**Cursor prompt**

Writing

Implement tender clarification and amendment action services in kentender_procurement.

Suggested actions:

- submit_clarification
- publish_clarification_response
- create_tender_amendment
- publish_tender_amendment

Requirements:

- preserve audit trail
- validate timing constraints where practical
- update tender amendment/clarification counts
- add tests for representative flows

Constraints:

- keep the logic service-driven
- do not silently overwrite published tender state

**PROC-STORY-035 — Implement tender tests and queue/report scaffolding**

**Cursor prompt**

Writing

Implement tender test suite and lightweight queue/report scaffolding in kentender_procurement.

Suggested queues/reports:

- Draft Tenders
- Tenders Under Review
- Published Tenders
- Tenders Closing Soon
- Tender Amendments
- Clarifications

Requirements:

- provide meaningful test coverage
- keep queue/report scaffolding lightweight and workspace-friendly

Constraints:

- do not build heavy dashboards
- focus on UAT usefulness and correctness

**EPIC-PROC-004 — Bid Submission**

**PROC-STORY-036 — Implement Bid Submission DocType**

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: PROC-STORY-036
- Epic: EPIC-PROC-004
- Title: Implement Bid Submission DocType

Context:

- Bid Submission is the supplier’s formal bid record against a tender.
- It must support sealed submission, locking, versioning, and receipt linkage.

Task:  
Implement the Bid Submission DocType.

Required fields:

- business_id
- tender
- tender_lot_scope
- status
- workflow_state
- submission_version_no
- supplier
- supplier_portal_user
- submitted_by_user
- submitted_on
- withdrawn_by_user
- withdrawn_on
- procuring_entity
- procurement_method
- submission_deadline
- opening_datetime
- visibility_scope
- is_final_submission
- is_locked
- sealed_status
- submission_token
- submission_hash
- receipt_no
- latest_receipt
- allows_resubmission
- active_submission_flag
- eligibility_check_status
- mandatory_document_check_status
- structure_check_status
- validation_status
- validation_summary
- quoted_total_amount
- currency
- bid_security_submitted
- bid_security_reference
- lot_count
- document_count
- is_opening_visible
- opened_on
- opened_by_session
- disqualification_reason
- remarks
- sensitivity_class

Requirements:

- create the DocType
- keep it sealed-access and workflow-ready
- add basic validation for tender/supplier presence and state sanity
- add tests

Constraints:

- do not implement submission service here
- do not expose sensitive fields casually

**PROC-STORY-037 — Implement Bid Envelope Section**

**Cursor prompt**

Writing

Implement Bid Envelope Section in kentender_procurement.

Required fields:

- bid_submission
- section_type
- section_title
- lot
- status
- display_order
- is_required
- completion_status
- section_hash

Requirements:

- support Mandatory Documents, Technical Proposal, Financial Proposal, Lot Response, Bid Security
- add tests for valid linkage and section create
- keep model ready for sealed-section logic later

Constraints:

- do not implement final submit behavior here

**PROC-STORY-038 — Implement Bid Document**

**Cursor prompt**

Writing

Implement Bid Document in kentender_procurement.

Required fields:

- bid_submission
- bid_envelope_section
- document_type
- file
- document_title
- status
- uploaded_by
- uploaded_at
- hash_value
- sensitivity_class
- is_mandatory
- is_opening_visible
- expiry_date
- validation_status
- validation_notes

Requirements:

- integrate with typed attachment/file control approach where appropriate
- add tests for valid create and metadata requirements

Constraints:

- do not implement final validation service here
- do not expose raw sealed document access

**PROC-STORY-039 — Implement Bid Submission Event**

**Cursor prompt**

Writing

Implement Bid Submission Event in kentender_procurement.

Required fields:

- bid_submission
- event_type
- event_datetime
- actor_user
- actor_role_context
- ip_address
- user_agent
- event_summary
- event_hash

Requirements:

- create event record model
- support major bid lifecycle events
- add tests for valid create/linkage

Constraints:

- do not replace shared audit service; this is bid-specific event history

**PROC-STORY-040 — Implement Bid Receipt**

**Cursor prompt**

Writing

Implement Bid Receipt in kentender_procurement.

Required fields:

- business_id
- bid_submission
- receipt_no
- tender
- supplier
- issued_on
- submission_timestamp
- submission_hash
- receipt_hash
- issued_to_user
- status

Requirements:

- create the DocType
- keep it suitable for final submission acknowledgement
- add tests

Constraints:

- do not generate receipts in this story

**PROC-STORY-041 — Implement Bid Withdrawal Record**

**Cursor prompt**

Writing

Implement Bid Withdrawal Record in kentender_procurement.

Required fields:

- bid_submission
- withdrawal_datetime
- withdrawn_by_user
- reason
- status

Requirements:

- create the DocType
- support auditable withdrawal history
- add tests

Constraints:

- do not implement withdrawal service here

**PROC-STORY-042 — Implement Bid Validation Issue**

**Cursor prompt**

Writing

Implement Bid Validation Issue in kentender_procurement.

Required fields:

- bid_submission
- issue_type
- severity
- issue_message
- detected_on
- resolved_flag
- resolved_on
- resolved_notes

Requirements:

- support blocking and warning issues
- add tests for valid issue creation

Constraints:

- do not implement all validation logic here

**PROC-STORY-043 — Implement bid draft/create/validate services**

**Cursor prompt**

Writing

Implement bid draft/create/validate services in kentender_procurement.

Suggested actions:

- create_bid_draft(tender_id, supplier_id)
- upload_bid_document(...)
- run_bid_validation(...)

Requirements:

- validate tender state and supplier eligibility at a basic service boundary
- create/update validation issues
- update bid validation summary fields
- add tests for draft creation and validation blocking scenarios

Constraints:

- do not implement final submission here
- do not hardcode supplier eligibility outside a service boundary

**PROC-STORY-044 — Implement final submit and receipt generation service**

**Cursor prompt**

Writing

Implement final bid submit and receipt generation service in kentender_procurement.

Suggested actions:

- submit_bid(bid_submission_id)
- generate_bid_receipt(bid_submission_id)

Requirements:

- enforce server-side submission deadline
- enforce mandatory structure/document validation
- compute submission hash/token
- create bid receipt
- lock the bid for pre-opening state
- emit audit and bid submission events
- add tests for success and blocking scenarios

Constraints:

- do not allow submission via direct field edits
- keep the operation explicit and auditable

**PROC-STORY-045 — Implement withdraw and resubmit services**

**Cursor prompt**

Writing

Implement bid withdrawal and resubmission services in kentender_procurement.

Suggested actions:

- withdraw_bid(bid_submission_id)
- create_resubmission_from_withdrawn_bid(...)

Requirements:

- enforce deadline and tender rules
- preserve prior submission history
- support latest-active-version semantics
- add tests for valid withdrawal, blocked late withdrawal, and resubmission flow

Constraints:

- do not mutate old records invisibly
- keep version history explicit

**PROC-STORY-046 — Implement sealed access integration and tests**

**Cursor prompt**

Writing

Implement sealed access integration for bid content in kentender_procurement.

Requirements:

- integrate bid documents/submission access with protected file access patterns from core
- ensure pre-opening sensitive access goes through controlled service paths
- add tests for allowed and denied access scenarios using placeholder permission logic where needed

Constraints:

- do not implement the full final permission matrix here
- do not expose raw generic file retrieval

**PROC-STORY-047 — Implement bid tests and queue/report scaffolding**

**Cursor prompt**

Writing

Implement bid test suite and lightweight queue/report scaffolding in kentender_procurement.

Suggested queues/reports:

- Draft Bids
- Submitted Bids
- Withdrawn Bids
- Bids Awaiting Opening
- Submission Receipts

Requirements:

- provide meaningful coverage for draft, submit, withdraw, and receipt flows
- keep queue/report scaffolding workspace-friendly

Constraints:

- no heavy analytics dashboards
- focus on correctness and UAT utility

**EPIC-PROC-005 — Bid Opening**

**PROC-STORY-048 — Implement Bid Opening Session**

**Cursor prompt**

Writing

Implement Bid Opening Session in kentender_procurement.

Required fields:

- business_id
- tender
- status
- workflow_state
- scheduled_opening_datetime
- actual_opening_datetime
- session_closed_datetime
- procuring_entity
- opening_mode
- opening_location
- meeting_reference
- notes
- precondition_check_status
- opening_triggered_by
- opening_committee_chair
- opening_committee_assignment_ref
- opened_bid_count
- excluded_bid_count
- is_atomic_opening_complete
- register_generated
- register_locked
- exception_record
- opening_register
- latest_event_hash

Requirements:

- create the DocType
- validate one primary active opening session per tender at a sensible level
- add tests

Constraints:

- do not execute opening here

**PROC-STORY-049 — Implement Bid Opening Attendance**

**Cursor prompt**

Writing

Implement Bid Opening Attendance in kentender_procurement.

Required fields:

- bid_opening_session
- attendee_user
- attendee_name
- attendee_role_type
- supplier
- attendance_status
- joined_at
- remarks

Requirements:

- create the model
- support internal and external/manual attendees
- add tests

**PROC-STORY-050 — Implement Bid Opening Register and lines**

**Cursor prompt**

Writing

Implement Bid Opening Register and Bid Opening Register Line in kentender_procurement.

Register fields:

- business_id
- tender
- bid_opening_session
- status
- generated_on
- generated_by_user
- total_submitted_bids
- total_opened_bids
- total_excluded_bids
- opening_datetime
- summary_notes
- is_locked
- register_hash
- public_summary_allowed
- remarks

Line fields:

- bid_submission
- supplier
- submission_timestamp
- receipt_no
- was_opened
- was_excluded
- exclusion_reason
- quoted_total_amount
- currency
- bid_security_present
- lot_summary
- register_notes

Requirements:

- create models
- add tests for valid linkage and basic record creation

Constraints:

- do not generate the register here

**PROC-STORY-051 — Implement Bid Opening Event Log**

**Cursor prompt**

Writing

Implement Bid Opening Event Log in kentender_procurement.

Required fields:

- bid_opening_session
- event_type
- event_datetime
- actor_user
- event_summary
- related_bid_submission
- result_status
- event_hash

Requirements:

- create model
- support append-only event logging for opening actions
- add tests

**PROC-STORY-052 — Implement opening precondition validation service**

**Cursor prompt**

Writing

Implement opening precondition validation service in kentender_procurement.

Suggested action:

- validate_opening_preconditions(tender_id, opening_session_id)

Requirements:

- check deadline reached
- check tender state valid
- check not cancelled/withdrawn
- check session not already completed improperly
- return structured pass/fail result
- add tests

Constraints:

- do not open bids here
- keep validation explainable

**PROC-STORY-053 — Implement candidate bid set resolution service**

**Cursor prompt**

Writing

Implement candidate bid set resolution service in kentender_procurement.

Requirements:

- resolve latest active submitted bids for the tender
- exclude drafts, withdrawn bids, superseded versions, already-opened bids
- return structured candidate/exclusion result
- add tests for representative cases

Constraints:

- do not execute opening here
- preserve explainability of inclusion/exclusion basis

**PROC-STORY-054 — Implement atomic opening execution service**

**Cursor prompt**

Writing

Implement atomic bid opening execution service in kentender_procurement.

Suggested action:

- execute_bid_opening(session_id)

Requirements:

- re-check preconditions
- resolve candidate bid set
- mark valid bids opened
- create opening register and lines
- create opening events
- update session state
- keep operation as atomic/recoverable as practical
- add tests for success and blocking scenarios

Constraints:

- do not allow opening via direct field edits
- avoid partial silent completion states

**PROC-STORY-055 — Implement register locking and post-opening status updates**

**Cursor prompt**

Writing

Implement post-opening lock/update service logic in kentender_procurement.

Requirements:

- lock opening register after generation
- update tender/opening statuses coherently
- mark bids as opened in controlled manner
- emit audit events
- add tests for lock behavior and status changes

Constraints:

- keep logic explicit and service-driven

**PROC-STORY-056 — Implement opening tests and queue/report scaffolding**

**Cursor prompt**

Writing

Implement opening test suite and lightweight queue/report scaffolding in kentender_procurement.

Suggested queues/reports:

- Scheduled Opening Sessions
- Ready for Opening
- Completed Openings
- Opening Registers
- Opening Exceptions/Exclusions

Requirements:

- provide meaningful test coverage for preconditions, candidate resolution, and opening execution
- keep queue/report scaffolding workspace-friendly

Constraints:

- no heavy dashboard buildout
- focus on correctness and UAT utility

**Recommended Cursor Execution Order**

Run in this order:

**Tender**

1.  PROC-STORY-023
2.  PROC-STORY-024
3.  PROC-STORY-025
4.  PROC-STORY-026
5.  PROC-STORY-027
6.  PROC-STORY-028
7.  PROC-STORY-029
8.  PROC-STORY-030
9.  PROC-STORY-031
10. PROC-STORY-032
11. PROC-STORY-033
12. PROC-STORY-034
13. PROC-STORY-035

**Bid Submission**

1.  PROC-STORY-036
2.  PROC-STORY-037
3.  PROC-STORY-038
4.  PROC-STORY-039
5.  PROC-STORY-040
6.  PROC-STORY-041
7.  PROC-STORY-042
8.  PROC-STORY-043
9.  PROC-STORY-044
10. PROC-STORY-045
11. PROC-STORY-046
12. PROC-STORY-047

**Bid Opening**

1.  PROC-STORY-048
2.  PROC-STORY-049
3.  PROC-STORY-050
4.  PROC-STORY-051
5.  PROC-STORY-052
6.  PROC-STORY-053
7.  PROC-STORY-054
8.  PROC-STORY-055
9.  PROC-STORY-056

**What this unlocks**

Once Wave 3 lands, you can run real UAT for:

- AT-TDR-001
- AT-BID-001
- AT-OPEN-001

And you’ll have the true foundation for:

- evaluation
- award
- supplier-facing trust
- sealed-bid control