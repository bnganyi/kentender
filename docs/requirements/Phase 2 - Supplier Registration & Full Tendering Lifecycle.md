# Phase 2 - Supplier Registration & Full Tendering LifecyclePhase 2 objective

This phase starts **after** demand has already been authorized internally through:

- Procurement Plan Item
- Purchase Requisition
- budget validation
- approval and commitment control

So Phase 2 is the **market-facing execution layer**.

The clean boundary is now:

**APP → Purchase Requisition → Tender → Submission → Opening → Evaluation → Award → Contract handoff**

That is the right structure.

# Phase 2 design synthesis

**Supplier Registration & Full Tendering Lifecycle**

**1\. Public-sector design stance**

This phase must be built as a **public procurement control system**, not a generic sourcing or RFQ tool.

That means the design must enforce:

- equal treatment of bidders
- controlled supplier eligibility
- public-sector approvals and committee actions
- confidentiality before opening
- immutable opening and evaluation records
- transparent award reasoning
- challenge / review defensibility
- auditable handoff into contract management

This phase should feel like a regulated government procurement platform, not a private procurement app with tender labels added on top.

**2\. Phase 2 scope**

**In scope**

- supplier registration and supplier governance
- supplier compliance and eligibility management
- tender initiation from approved requisition(s)
- lotting and tender structuring
- tender document control
- publication and bidder communication
- bid submission and secure closing
- opening ceremony and opening records
- evaluation workflow and committee controls
- award recommendation and award decision
- notifications, regret letters, standstill/challenge handling
- handoff to contract / PO baseline

**Out of scope**

- full contract administration
- inspection and acceptance
- delivery tracking
- invoice/payment administration
- supplier performance management beyond initial award baseline

Those belong to the next phase.

**3\. Recommended Phase 2 module structure**

I recommend dividing Phase 2 into **8 submodules**.

**Module 1 — Supplier Registration & Supplier Master Governance**

Purpose: build a controlled supplier registry, not just a vendor list.

This module should cover:

- supplier application
- company/legal identity
- statutory compliance
- tax and registration documents
- beneficial ownership
- bank details
- category registration
- suspension/debarment/blacklisting
- renewal and expiry tracking
- approval and activation

**Core principle**

A supplier should **not become fully eligible to bid** just because they filled in a profile. Eligibility must be governed by:

- registration status
- document validity
- category approval
- debarment/suspension status
- tender-specific eligibility conditions

**Module 2 — Tender Initiation & Tender Structuring**

Purpose: create a valid tender from approved requisition demand.

Tender creation should start from:

- one approved requisition
- or several approved requisitions in a controlled aggregated tender

**This module should define:**

- tender header
- tender method
- linked requisition(s)
- linked APP lineage
- procurement type
- tender lots
- approval chain for tender launch
- timelines
- tender security rules
- eligibility rules
- opening/evaluation method
- document pack readiness

**Hard rule**

No normal tender should be created without an approved requisition reference.

**Module 3 — Tender Document Management & Publication**

Purpose: manage controlled tender documents and controlled communication.

This module should handle:

- invitation / tender notice
- instructions to tenderers
- specifications / TOR / SOW
- BOQ / price schedules
- qualification criteria
- evaluation criteria
- addenda
- clarifications
- publication logs
- download/access control where needed

**Public-sector requirement**

Clarifications and addenda must be issued in a way that preserves fairness. Material information should not be released privately to one bidder only where rules require equal disclosure.

**Module 4 — Bid Submission, Secure Receipt & Closing**

Purpose: receive bids securely and prevent premature access.

This module must support:

- supplier submission workflow
- deadline enforcement
- withdrawal/replacement before deadline where allowed
- hard close at deadline
- server-time-based cutoff
- no admin preview of commercial contents before opening
- receipt logging
- late bid handling rules

**This is non-negotiable**

Before official opening:

- submissions must remain sealed
- evaluation users must not see content
- procurement users must not inspect price content casually

If this is weak, the entire system loses credibility.

**Module 5 — Tender Opening**

Purpose: create a formal opening event and immutable opening record.

This module should include:

- opening committee attendance
- opening date/time
- bid register
- bid readout
- tender security confirmation
- late bid notes
- opening minutes
- digital signatures / approvals of committee members
- automatic opening record generation

**Design principle**

Opening is not a technical unlock event only.  
It is a **governed ceremonial and audit event**.

**Module 6 — Evaluation Workflow**

Purpose: support defensible and role-controlled bid evaluation.

This needs structured stages:

1.  **Preliminary / Mandatory Responsiveness**
    - required documents
    - statutory compliance
    - tender security
    - signed forms
    - responsiveness
2.  **Technical Evaluation**
    - pass/fail or scored
    - evaluator assignments
    - criteria weighting
    - comments and evidence
3.  **Financial Evaluation**
    - price comparison
    - arithmetic checks
    - currency normalization if enabled
    - ranking logic
4.  **Post-Qualification / Due Diligence**
    - supplier verification
    - category/eligibility confirmation
    - possible reference checks
5.  **Consensus / Committee Recommendation**
    - evaluator declarations
    - consolidation of results
    - recommendation record

**Critical controls**

- evaluator assignment must be formal
- conflict-of-interest declarations required
- evaluators should not casually edit each other’s records
- consensus should not overwrite individual scoring without traceability
- disqualification reasons must be explicit

**Module 7 — Award, Notifications, Standstill & Review**

Purpose: move from evaluation outcome to defensible award.

This module should cover:

- professional opinion / award recommendation
- approval of recommendation
- notice of intention to award if required
- regret notifications
- standstill/challenge window handling
- final award decision
- award publication

**Important point**

Award should **not** auto-jump to PO just because someone scored highest.

The system must support:

- recommendation
- approval
- notifications
- challenge/review handling
- finalization

Only then should it hand off.

**Module 8 — Award Handoff to Contract / PO**

Purpose: create a controlled bridge to Phase 3.

This module should support:

- award-to-contract handoff
- award-to-PO handoff where appropriate
- lot-level award mapping
- supplier activation/update if needed
- baseline supplier performance record
- preservation of full award lineage

**Boundary**

This is only the handoff and baseline.  
Full contract management belongs to the next phase.

**4\. Recommended core DocTypes for Phase 2**

**Supplier side**

- Supplier Registration Application
- Supplier Master
- Supplier Category Registration
- Supplier Compliance Document
- Supplier Beneficial Ownership Record
- Supplier Bank Detail
- Supplier Status Action
- Suspension / Debarment Register
- Supplier Renewal Review

**Tender initiation and document side**

- Tender
- Tender Lot
- Tender Document Pack
- Tender Addendum
- Tender Clarification
- Tender Publication Record
- Tender Eligibility Rule
- Tender Security Rule

**Bid side**

- Tender Submission
- Tender Submission Item / Lot Response
- Bid Attachment
- Bid Receipt Log
- Bid Opening Register
- Bid Opening Record

**Evaluation side**

- Evaluation Committee
- Evaluator Declaration
- Evaluation Criterion Template
- Evaluation Worksheet
- Evaluation Score Record
- Evaluation Consensus Record
- Post-Qualification Check

**Award side**

- Award Recommendation
- Award Decision
- Notification Log
- Challenge / Review Case
- Award Publication Record

**Handoff side**

- Award Contract Handoff
- Award PO Handoff
- Supplier Performance Baseline

**5\. Workflow architecture**

**5.1 Supplier Registration workflow**

**Draft → Submitted → Compliance Review → Procurement Review → Approved / Rejected / Suspended**

**Notes**

- supplier cannot self-approve
- document expiry may move supplier into restricted or expired status
- suspended/debarred supplier must be blocked from tender participation

**5.2 Tender workflow**

**Draft → Internal Review → Approved for Publication → Published → Closed → Opened → Under Evaluation → Award Recommended → Award Approved → Award Published / Cancelled**

**Key rule**

Tender should not skip directly from Draft to Published.

There must be an internal control point to confirm:

- valid requisition source
- document pack completeness
- timeline validity
- eligibility criteria
- evaluation setup
- committee readiness where required

**5.3 Submission workflow**

**Draft Response → Submitted → Locked at Deadline → Opened → Evaluated → Responsive / Non-Responsive / Withdrawn**

**Controls**

- withdrawal/replacement only before deadline
- no edit after deadline
- no opening before official opening event

**5.4 Evaluation workflow**

**Pending Assignment → Under Review → Submitted by Evaluator → Consensus Review → Recommended / Disqualified**

**Controls**

- declarations before scoring
- stage-by-stage progression
- no financial opening before passing required earlier stages if policy requires separation

**5.5 Award workflow**

**Draft Recommendation → Committee Review → Approval → Intention to Award / Notification → Challenge Window → Final Award**

This keeps the award process defensible.

**6\. Key public-sector controls that must be built in**

**Supplier-side controls**

- supplier category approval
- statutory document expiry tracking
- suspension/debarment status
- beneficial ownership capture
- duplicate supplier detection
- controlled status changes

**Tender controls**

- tender must originate from approved requisition(s)
- lot structure must be explicit
- method and thresholds should align with upstream policy rules
- addenda must be versioned and logged
- publication must be logged

**Submission controls**

- sealed submissions before opening
- deadline hard lock
- server time as source of truth
- no invisible edits after submission
- late submission status preserved

**Opening controls**

- opening committee attendance
- generated opening minutes
- immutable readout record
- digital acknowledgment/signoff

**Evaluation controls**

- evaluator assignment
- evaluator declarations
- structured criteria
- stage separation
- explicit disqualification reasons
- consensus traceability

**Award controls**

- recommendation separate from approval
- approval separate from publication
- regret/notification logging
- challenge/review recording
- final award handoff traceability

**7\. Role structure for Phase 2**

Recommended roles:

- Supplier / Bidder User
- Supplier Registration Officer
- Procurement Officer
- Head of Procurement
- Tender Committee Secretary
- Opening Committee Member
- Evaluation Committee Member
- Evaluation Committee Chair
- Accounting Officer
- Internal Auditor
- Oversight / Read-Only Reviewer
- System Administrator

**Role logic**

- suppliers interact only with supplier and submission-facing parts
- opening committee should not act as supplier approver
- evaluators should not have uncontrolled tender editing powers
- award approvers should review outcomes, not secretly alter scoring
- auditors get full read-only access

**8\. Important design boundaries we should preserve**

These are the boundaries that keep the system clean:

**Phase 1 / 1.5 owns:**

- planning
- budget control
- requisition approval
- demand authorization

**Phase 2 owns:**

- supplier governance
- tender setup
- market interaction
- submission
- opening
- evaluation
- award

**Phase 3 owns:**

- contract execution
- delivery
- inspection
- invoice/payment progression
- contract performance and variations

Do not let Tender creation absorb requisition logic.  
Do not let Contract phase absorb award logic.

**9\. Recommended final stance before build-ready spec**

For Kentender, I recommend we design Phase 2 around these truths:

- **Supplier Registration is a governed eligibility regime**
- **Tender is created only from approved requisition demand**
- **Submission must remain sealed until opening**
- **Opening is a formal event, not a casual system action**
- **Evaluation must be committee-structured and traceable**
- **Award must be recommendation-driven, approval-controlled, and reviewable**
- **Contract handoff happens only after award is fully finalized**

That is the right public-sector architecture.

# Phase 2 Build-Ready Specification

**Module: Supplier Registration & Full Tendering Lifecycle**

**1\. Build objective**

Build a public-sector tendering module that:

- governs supplier eligibility and registration,
- creates tenders only from approved requisition demand,
- protects bid confidentiality before opening,
- supports formal opening and committee-based evaluation,
- controls award approvals and notifications,
- preserves full auditability from requisition to award handoff.

**2\. Final module scope**

**In scope**

- supplier registration and approval
- supplier compliance and category eligibility
- suspension/debarment handling
- tender creation from requisition(s)
- lotting and tender structuring
- tender document management
- publication and bidder communication
- secure bid submission and closing
- bid opening
- evaluation workflow
- award recommendation and award decision
- regret notices / challenge logging
- award publication and handoff to contract/PO baseline

**Out of scope**

- full contract administration
- delivery, inspection, acceptance
- invoice and payment administration
- long-term supplier performance management beyond award baseline

**3\. Final DocType architecture**

**Supplier-side DocTypes**

1.  **Supplier Registration Application**
2.  **Supplier Master**
3.  **Supplier Category Registration**
4.  **Supplier Compliance Document**
5.  **Supplier Beneficial Ownership**
6.  **Supplier Bank Detail**
7.  **Supplier Status Action**
8.  **Suspension Debarment Register**
9.  **Supplier Renewal Review**

**Tender setup DocTypes**

1.  **Tender**
2.  **Tender Lot**
3.  **Tender Eligibility Rule**
4.  **Tender Security Rule**
5.  **Tender Document Pack**
6.  **Tender Document Version**
7.  **Tender Clarification**
8.  **Tender Addendum**
9.  **Tender Publication Record**

**Submission and opening DocTypes**

1.  **Tender Submission**
2.  **Tender Submission Lot Response**
3.  **Tender Submission Attachment**
4.  **Bid Receipt Log**
5.  **Bid Opening Register**
6.  **Bid Opening Record**

**Evaluation DocTypes**

1.  **Evaluation Committee**
2.  **Evaluator Declaration**
3.  **Evaluation Criterion Template**
4.  **Tender Evaluation Scheme**
5.  **Evaluation Worksheet**
6.  **Evaluation Score Record**
7.  **Evaluation Consensus Record**
8.  **Post Qualification Check**

**Award and review DocTypes**

1.  **Award Recommendation**
2.  **Award Decision**
3.  **Tender Notification Log**
4.  **Challenge Review Case**
5.  **Award Publication Record**

**Handoff DocTypes**

1.  **Award Contract Handoff**
2.  **Award PO Handoff**
3.  **Supplier Performance Baseline**

**4\. Exact DocType definitions**

**4.1 Supplier Registration Application**

Purpose: intake and review record for prospective suppliers.

**Fields**

- application_number — Data — unique
- supplier_name — Data — req
- legal_name — Data — req
- registration_number — Data — req
- tax_id — Data — req
- vat_number — Data
- country — Data — req
- incorporation_date — Date
- supplier_type — Select:
    - Company
    - Partnership
    - Sole Proprietor
    - NGO
    - State Corporation
    - Other
- email — Data — req
- phone — Data — req
- physical_address — Small Text — req
- postal_address — Small Text
- website — Data
- application_status — Select:
    - Draft
    - Submitted
    - Compliance Review
    - Procurement Review
    - Approved
    - Rejected
    - Suspended
- requested_categories — Table
- remarks — Small Text
- submitted_on — Datetime
- approved_on — Datetime

**Child tables**

- compliance documents
- beneficial owners
- bank details
- category requests
- review log

**Rules**

- no approval without required compliance docs
- duplicate checks against legal name, tax ID, registration number
- approved application creates/updates Supplier Master

**4.2 Supplier Master**

Purpose: authoritative supplier record used across tenders and awards.

**Fields**

- supplier_code — Data — unique
- supplier_name — Data — req
- legal_name — Data — req
- registration_number — Data — req
- tax_id — Data — req
- email — Data — req
- phone — Data — req
- supplier_status — Select:
    - Draft
    - Active
    - Inactive
    - Suspended
    - Debarred
    - Expired Compliance
    - Blacklisted
- registration_status — Select:
    - Pending
    - Approved
    - Rejected
    - Renewal Due
- default_currency
- country
- physical_address
- bank_verification_status
- beneficial_ownership_verified — Check
- last_review_date
- next_review_date
- notes

**Rules**

- suspended/debarred suppliers cannot submit bids
- expired compliance may restrict participation
- controlled status changes only through Supplier Status Action

**4.3 Supplier Category Registration**

Purpose: approved eligibility by category/class.

**Fields**

- supplier — Link Supplier Master — req
- category — Link Spend Category — req
- registration_status — Select:
    - Pending
    - Approved
    - Expired
    - Suspended
    - Rejected
- effective_from — Date
- effective_to — Date
- approved_by
- remarks

**Rules**

- tender may require eligible category registration
- expiry prevents category-based bidding where mandatory

**4.4 Supplier Compliance Document**

Purpose: store statutory and qualification documents.

**Fields**

- supplier / application
- document_type — Select:
    - Certificate of Incorporation
    - Tax Compliance
    - VAT Certificate
    - Business Permit
    - CR12 / Shareholding
    - Professional License
    - Audited Statements
    - AGPO / Reserved Group Certificate
    - Other
- document_number
- issue_date
- expiry_date
- attachment
- verification_status — Pending / Verified / Rejected / Expired
- verified_by
- verified_on
- remarks

**Rules**

- expiry monitoring required
- some document types mandatory by supplier type/category/tender rule

**4.5 Supplier Beneficial Ownership**

Purpose: capture ownership transparency.

**Fields**

- supplier / application
- owner_name — req
- nationality
- id_passport
- ownership_percent
- role
- pep_flag
- sanctions_flag
- verified

**Rules**

- ownership totals should validate sensibly
- high-risk flags may trigger enhanced due diligence

**4.6 Supplier Bank Detail**

Purpose: controlled payment banking record.

**Fields**

- supplier
- bank_name
- branch_name
- account_name
- account_number
- swift_code
- verification_status
- verified_by
- verified_on

**4.7 Supplier Status Action**

Purpose: controlled state changes.

**Fields**

- supplier
- action_type — Activate / Suspend / Reinstate / Debar / Blacklist / Mark Expired / Reactivate
- reason
- requested_by
- approved_by
- effective_date
- end_date
- status

**Rules**

- this is the only route for substantive status changes
- all actions auditable and non-destructive

**4.8 Suspension Debarment Register**

Purpose: authoritative exclusion register.

**Fields**

- supplier
- action_type — Suspension / Debarment / Blacklist
- reason
- reference_number
- effective_from
- effective_to
- issuing_authority
- status

**Rules**

- suppliers on active record are blocked from bidding/award

**4.9 Supplier Renewal Review**

Purpose: periodic compliance refresh.

**Fields**

- supplier
- review_date
- review_status — Pending / Approved / Rejected / Additional Info Required
- review_notes
- reviewed_by
- next_review_date

**4.10 Tender**

Purpose: central tender record created from approved requisition demand.

**Fields**

- tender_number — Data — unique
- entity — Link Company — req
- title — Data — req
- procurement_type — Select — req
- method — Select — req
- requisition_source_mode — Single / Multiple
- estimated_value — Currency
- currency
- advertisement_date
- closing_datetime — req
- opening_datetime — req
- submission_mode — Electronic / Manual / Hybrid
- evaluation_method — Pass-Fail / Weighted Score / Least Evaluated Cost / QCBS / Other
- tender_status — Select:
    - Draft
    - Internal Review
    - Approved for Publication
    - Published
    - Closed
    - Opened
    - Under Evaluation
    - Award Recommended
    - Award Approved
    - Award Published
    - Cancelled
- eligibility_scope
- security_required — Check
- security_amount
- clarification_deadline
- site_visit_required — Check
- prebid_required — Check
- prebid_datetime
- confidentiality_level
- linked_requisition_count
- award_status
- remarks

**Child tables**

- requisition links
- lots
- document pack refs
- publication log refs
- committee refs

**Rules**

- no normal tender without approved requisition link
- closing datetime must be after publication date
- opening cannot be before closing
- internal review required before publication

**4.11 Tender Lot**

Purpose: lot-based procurement structure.

**Fields**

- tender
- lot_number
- lot_title
- description
- estimated_value
- category
- delivery_location
- quantity_summary
- award_mode — Single Award / Multi Award / Framework
- status

**Rules**

- bids may respond to one or more lots
- evaluation and award may occur per lot

**4.12 Tender Eligibility Rule**

Purpose: tender-specific bidder qualification rules.

**Fields**

- tender
- rule_type — Category / Reserved Group / Financial Capacity / Experience / License / Geographic / Mandatory Document
- rule_description
- mandatory — Check
- pass_fail — Check
- weight
- evidence_required

**4.13 Tender Security Rule**

Purpose: define bid security requirements.

**Fields**

- tender
- security_required
- security_type
- security_amount
- validity_days
- acceptable_issuers
- forfeiture_conditions
- waiver_allowed

**4.14 Tender Document Pack**

Purpose: structured tender documents.

**Fields**

- tender
- document_pack_status — Draft / Reviewed / Approved / Published
- instructions_document
- specification_document
- boq_document
- qualification_document
- evaluation_criteria_document
- draft_contract_document
- notes

**Rules**

- publication blocked until required documents exist

**4.15 Tender Document Version**

Purpose: immutable document versioning.

**Fields**

- tender
- document_type
- version_number
- attachment
- change_summary
- published_flag
- created_by
- created_on

**4.16 Tender Clarification**

Purpose: bidder questions and official responses.

**Fields**

- tender
- supplier
- question_reference
- question_text
- submitted_on
- response_text
- responded_on
- response_visibility — Public to All / Private Administrative
- status

**Rules**

- material clarification should be public to all where required

**4.17 Tender Addendum**

Purpose: formal amendment to tender terms/docs.

**Fields**

- tender
- addendum_number
- title
- change_summary
- effective_date
- closing_date_extended — Check
- new_closing_datetime
- attachment
- status

**Rules**

- versioned and logged
- publication required if effective
- closing extension logic applied automatically

**4.18 Tender Publication Record**

Purpose: publication audit trail.

**Fields**

- tender
- publication_channel
- publication_date
- published_by
- notice_reference
- attachment
- status

**4.19 Tender Submission**

Purpose: bid response record.

**Fields**

- submission_number — unique
- tender
- supplier
- submission_status — Draft / Submitted / Locked / Withdrawn / Replaced / Late / Opened / Evaluated / Non-Responsive / Responsive
- submitted_on
- server_received_on
- withdrawn_on
- replacement_of_submission
- bid_validity_days
- security_provided — Check
- security_reference
- read_only_after_deadline — Check
- sealed_flag — Check
- confidentiality_status
- remarks

**Rules**

- only active eligible suppliers may submit
- hard lock at deadline
- no opening before official opening event
- withdrawal/replacement only before deadline

**4.20 Tender Submission Lot Response**

Purpose: lot-level response details.

**Fields**

- submission
- lot
- quoted_amount
- currency
- delivery_period
- lot_response_status

**4.21 Tender Submission Attachment**

Purpose: bid documents.

**Fields**

- submission
- document_type
- attachment
- uploaded_on
- verified_presence — Check

**4.22 Bid Receipt Log**

Purpose: official receipt ledger.

**Fields**

- tender
- submission
- supplier
- received_datetime
- receipt_mode
- late_flag
- receipt_number

**4.23 Bid Opening Register**

Purpose: register of submissions presented at opening.

**Fields**

- tender
- opening_datetime
- total_submissions
- total_opened
- total_late
- register_status

**4.24 Bid Opening Record**

Purpose: immutable opening event outcome.

**Fields**

- tender
- submission
- lot
- opened_by_committee
- opening_datetime
- bid_price_readout
- security_confirmed
- late_bid_flag
- remarks
- signed_off

**Rules**

- generated during opening event
- immutable after signoff except formal correction note

**4.25 Evaluation Committee**

Purpose: official evaluation body.

**Fields**

- tender
- committee_name
- committee_type — Opening / Evaluation / Both
- chairperson
- secretary
- status

**Child table**

- members
- role
- appointed_on

**4.26 Evaluator Declaration**

Purpose: conflict/confidentiality declaration.

**Fields**

- tender
- committee_member
- declaration_type — COI / Confidentiality / Both
- status — Signed / Not Signed / Conflict Declared
- notes
- signed_on

**Rules**

- evaluation blocked until required declarations signed

**4.27 Evaluation Criterion Template**

Purpose: reusable criteria sets.

**Fields**

- template_name
- procurement_type
- evaluation_method
- status

**Child table**

- criterion
- stage
- weight
- pass_mark
- mandatory flag

**4.28 Tender Evaluation Scheme**

Purpose: actual criteria used on a tender.

**Fields**

- tender
- template
- scheme_status
- approval_status

**4.29 Evaluation Worksheet**

Purpose: evaluator-stage worksheet.

**Fields**

- tender
- submission
- evaluator
- evaluation_stage — Preliminary / Technical / Financial / Post Qualification
- worksheet_status
- submitted_on
- comments

**Rules**

- evaluators do not edit each other’s worksheets

**4.30 Evaluation Score Record**

Purpose: criterion-level scoring.

**Fields**

- worksheet
- criterion
- score
- pass_fail_result
- remarks
- evidence_reference

**4.31 Evaluation Consensus Record**

Purpose: committee-consolidated result.

**Fields**

- tender
- submission
- lot
- preliminary_result
- technical_score
- financial_score
- final_rank
- recommendation_status
- disqualification_reason
- consensus_notes
- approved_by_committee

**Rules**

- consensus must not erase individual worksheets
- disqualification reason mandatory where applicable

**4.32 Post Qualification Check**

Purpose: post-evaluation due diligence.

**Fields**

- tender
- submission
- supplier
- check_type
- result
- checked_by
- checked_on
- remarks

**4.33 Award Recommendation**

Purpose: formal recommendation for award.

**Fields**

- tender
- lot
- recommended_submission
- recommended_supplier
- recommended_amount
- recommendation_basis
- prepared_by
- prepared_on
- status

**4.34 Award Decision**

Purpose: approved award outcome.

**Fields**

- tender
- lot
- award_status — Draft / Approved / Rejected / Cancelled / Finalized
- approved_supplier
- approved_submission
- approved_amount
- decision_date
- approved_by
- decision_notes

**4.35 Tender Notification Log**

Purpose: all bidder notifications.

**Fields**

- tender
- supplier
- notification_type — Invitation / Clarification / Addendum / Regret / Intention to Award / Final Award
- sent_on
- channel
- status
- reference

**4.36 Challenge Review Case**

Purpose: standstill and review tracking.

**Fields**

- tender
- award_decision
- case_number
- supplier
- case_type — Complaint / Administrative Review / Appeal / Clarification
- filed_on
- status
- decision
- decision_date
- notes

**Rules**

- final award publication may be held where active review blocks progression

**4.37 Award Publication Record**

Purpose: final publication audit.

**Fields**

- award_decision
- publication_channel
- published_on
- published_by
- notice_reference
- attachment

**4.38 Award Contract Handoff**

Purpose: transition to contract phase.

**Fields**

- award_decision
- handoff_status
- prepared_by
- prepared_on
- contract_reference
- notes

**4.39 Award PO Handoff**

Purpose: transition where PO-based execution is appropriate.

**Fields**

- award_decision
- handoff_status
- prepared_by
- prepared_on
- po_reference
- notes

**4.40 Supplier Performance Baseline**

Purpose: create supplier baseline at award.

**Fields**

- supplier
- tender
- award_decision
- baseline_date
- starting_rating
- risk_notes

**5\. Workflow design**

**5.1 Supplier Registration workflow**

**Draft → Submitted → Compliance Review → Procurement Review → Approved / Rejected / Suspended**

**Rules**

- no approval without mandatory verified documents
- approved application creates or updates Supplier Master
- suspended/debarred suppliers blocked from bidding

**5.2 Tender workflow**

**Draft → Internal Review → Approved for Publication → Published → Closed → Opened → Under Evaluation → Award Recommended → Award Approved → Award Published / Cancelled**

**Transition rules**

- Draft → Internal Review: Procurement Officer
- Internal Review → Approved for Publication: Head of Procurement / approving authority
- Approved for Publication → Published: authorized procurement user
- Published → Closed: system at deadline
- Closed → Opened: Opening Committee
- Opened → Under Evaluation: Secretary / system after opening completion
- Under Evaluation → Award Recommended: Evaluation Committee
- Award Recommended → Award Approved: Approving Authority
- Award Approved → Award Published: authorized procurement user

**5.3 Submission workflow**

**Draft → Submitted → Locked at Deadline → Opened → Evaluated → Responsive / Non-Responsive / Withdrawn / Late**

**Rules**

- withdrawal/replacement only before deadline
- late submissions preserved as late, not deleted
- no edits after lock

**5.4 Evaluation workflow**

**Assigned → Under Review → Submitted by Evaluator → Consensus Review → Recommended / Disqualified**

**Rules**

- declarations mandatory before evaluation
- stage-based separation
- financial stage only after earlier required stages pass

**5.5 Award workflow**

**Draft Recommendation → Committee Review → Approved Decision → Intention / Notification → Challenge Window → Final Award**

**Rules**

- recommendation distinct from final approval
- challenge case may pause final publication

**6\. Role and permission matrix**

**Roles**

- Supplier Bidder User
- Supplier Registration Officer
- Procurement Officer
- Head of Procurement
- Tender Committee Secretary
- Opening Committee Member
- Evaluation Committee Member
- Evaluation Committee Chair
- Approving Authority / Accounting Officer
- Internal Auditor
- Oversight Viewer
- System Administrator

**Permission summary**

**Supplier Bidder User**

- manage own registration application
- submit bid
- view own submissions and notifications
- cannot view competitor data

**Supplier Registration Officer**

- review supplier applications
- verify documents
- recommend approval/rejection

**Procurement Officer**

- create tender
- manage documents
- publish tender
- manage clarifications/addenda
- cannot privately alter evaluation outcomes

**Head of Procurement**

- approve tender readiness
- review evaluation outputs
- approve procedural transitions where assigned

**Opening Committee Member**

- participate in opening only
- record opening data
- cannot edit sealed bids before opening

**Evaluation Committee Member**

- view allowed evaluation-stage data
- complete worksheets
- cannot publish award or rewrite tender core setup

**Evaluation Committee Chair**

- lead consensus
- approve committee records

**Approving Authority / Accounting Officer**

- approve award decision
- approve exceptional outcomes

**Internal Auditor / Oversight Viewer**

- full read-only access to audit trail, opening, evaluation, award, notifications

**System Administrator**

- configuration/support only

**7\. Validation logic**

**Supplier validations**

- no duplicate active supplier by legal name + registration/tax combo
- mandatory docs by supplier type/category
- suspended/debarred status blocks submission and award
- expired compliance may block tender participation where configured

**Tender validations**

- at least one approved requisition linked
- valid method and procurement type
- closing datetime > publication datetime
- opening datetime >= closing datetime
- document pack complete before publication
- evaluation scheme defined before publication
- committee assignment where required

**Submission validations**

- supplier eligible and active
- supplier not suspended/debarred
- submission before deadline
- required attachments present
- lot response valid
- security data present where required
- lock after deadline

**Opening validations**

- opening cannot occur before close
- opening committee assigned
- all opened bids logged
- late bids marked distinctly
- opening record immutable after signoff

**Evaluation validations**

- evaluator declaration signed
- stage progression enforced
- disqualification reason mandatory
- consensus cannot finalize without underlying worksheets
- no award recommendation without final consensus

**Award validations**

- award decision must reference recommendation
- notification logs required where applicable
- active challenge may hold finalization/publication
- handoff blocked until award finalized

**8\. Automations and hooks**

**Required server-side logic**

1.  supplier duplicate detection
2.  supplier status enforcement
3.  tender number generation
4.  deadline auto-lock
5.  sealed submission control
6.  opening register generation
7.  evaluation route control
8.  consensus aggregation
9.  award recommendation to award decision linkage
10. challenge hold logic
11. handoff creation
12. notification triggers

**Suggested scheduled jobs**

- compliance expiry alerts
- tender closing reminders
- addendum notification reminders
- challenge window monitoring
- stale evaluation alerts

**9\. UI / workspace design**

**Supplier Portal Workspace**

- new registration
- my profile
- compliance documents
- category registrations
- my submissions
- notifications

**Supplier Governance Workspace**

- applications awaiting review
- document verification queue
- expiring compliance
- suspension/debarment register
- renewal reviews

**Tender Management Workspace**

- draft tenders
- internal review queue
- ready for publication
- published tenders
- clarification queue
- addenda queue

**Opening Workspace**

- tenders due for opening
- opening register
- opening minutes/signoff

**Evaluation Workspace**

- committee assignments
- declarations pending
- worksheets in progress
- consensus queue
- post-qualification queue

**Award Workspace**

- recommendations pending approval
- award decisions
- notifications
- challenge cases
- handoff queue

**Audit Workspace**

- full tender audit trail
- supplier status actions
- opening logs
- evaluation logs
- award logs

**10\. Reports to build**

**Supplier reports**

1.  Supplier Registration Status Report
2.  Supplier Compliance Expiry Report
3.  Supplier Category Eligibility Report
4.  Suspended/Debarred Supplier Register
5.  Supplier Renewal Due Report

**Tender reports**

1.  Tenders by Status
2.  Tender Publication Register
3.  Clarification and Addendum Log
4.  Bid Receipt Summary
5.  Late Submission Report
6.  Opening Register Report

**Evaluation and award reports**

1.  Evaluation Progress Report
2.  Non-Responsive Bid Report
3.  Consensus Ranking Report
4.  Award Recommendation Register
5.  Award Decision Register
6.  Notification Log Report
7.  Challenge/Review Case Register
8.  Requisition-to-Award Traceability Report

**Audit reports**

1.  Tender Full Audit Trail
2.  User Action Log
3.  Supplier Status Change Log
4.  Opening Record Audit Report
5.  Evaluation Worksheet Audit Report

**11\. User stories**

**Supplier side**

- As a supplier, I can register and upload statutory documents for review.
- As a supplier officer, I can verify documents and approve category eligibility.
- As the system, I block suspended or debarred suppliers from bidding.

**Tender setup**

- As procurement, I can create a tender from approved requisition demand.
- As procurement, I can define lots, documents, deadlines, and evaluation setup before publication.

**Submission and opening**

- As a bidder, I can submit a bid before the deadline and receive receipt logging.
- As opening committee, I can open bids only after closing and generate immutable opening records.

**Evaluation**

- As evaluator, I can score only assigned submissions after signing declarations.
- As committee chair, I can consolidate results without destroying individual evaluator records.

**Award**

- As approving authority, I can approve or reject award recommendations.
- As procurement, I can notify bidders and log challenge/review actions before final handoff.

**12\. Acceptance criteria**

The module is acceptable only if all of these pass:

1.  Supplier cannot bid unless active and eligible.
2.  Suspended/debarred supplier is blocked from submission and award.
3.  Tender cannot be published without approved requisition source and complete document pack.
4.  Submission locks automatically at deadline.
5.  Bid content remains sealed before opening.
6.  Opening generates immutable opening records.
7.  Evaluators must sign declarations before evaluation.
8.  Consensus result does not overwrite individual evaluator evidence.
9.  Award cannot be finalized without recommendation and approval.
10. Challenge case can hold final publication where configured.
11. Award handoff cannot happen before final award state.
12. Full audit trail exists from requisition to award handoff.

**13\. Recommended build sequence**

**Sprint 1**

- supplier registration application
- supplier master
- compliance docs
- status controls

**Sprint 2**

- tender
- lots
- eligibility/security rules
- document pack
- publication

**Sprint 3**

- submissions
- secure locking
- receipt logs
- opening register and record

**Sprint 4**

- committees
- declarations
- worksheets
- consensus
- post qualification

**Sprint 5**

- award recommendation
- award decision
- notifications
- challenge cases
- handoff records
- reports and hardening

**14\. Final design stance**

This is the clean public-sector Phase 2 architecture:

- **Supplier registration** governs who is eligible
- **Tender** governs market process from approved demand
- **Submission** preserves confidentiality
- **Opening** formalizes receipt and readout
- **Evaluation** is structured, committee-based, and traceable
- **Award** is recommendation-driven and approval-controlled
- **Handoff** bridges into contract/PO phase without swallowing contract management