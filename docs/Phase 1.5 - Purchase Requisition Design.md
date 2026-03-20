# Phase 1.5 - Purchase Requisition DesignDesign Philosophy

**1\. Module objective**

The **Purchase Requisition** module is the formal internal control point that converts an approved procurement need into an approved, budget-cleared, execution-ready procurement demand.

It sits here:

**APP → Procurement Plan Item → Purchase Requisition → Tender**

That means this module must do five things well:

- translate APP planning into a real procurement request
- validate budget and create commitment/encumbrance at the right point
- enforce internal approvals and segregation of duties
- prevent demand fragmentation and uncontrolled changes
- produce a clean, locked handoff to Phase 2 tendering

This is not supplier-facing. It is not tendering. It is the last internal gate before market interaction.

**2\. Public-sector design stance**

For Kenyan public-sector use, the requisition module should be designed as:

- **mandatory before tendering**
- **budget-controlled**
- **approval-driven**
- **department-originated but centrally governed**
- **auditable and non-destructive**
- **able to support emergency exceptions without bypassing traceability**

The source requirements make that clear: departments create requisitions, they must map to APP lines or be justified as one-off, finance validates budget, requisition approval encumbers budget, deleted requisitions are soft-delete only, and the system should detect attempts to split requisitions to avoid thresholds.

**3\. Scope of Phase 1.5**

**In scope**

- requisition creation from APP item(s)
- controlled one-off requisition path
- multi-line requisitions
- budget and commitment validation
- approval workflow
- anti-split controls
- amendment, cancellation, and soft-delete governance
- emergency requisition path
- handoff to tender creation
- dashboards, reports, and audit trail

**Out of scope**

- supplier registration
- tender publication
- bid submission/opening/evaluation/award
- contract administration

**4\. Recommended module structure**

I would split Phase 1.5 into **6 submodules**.

**Module 1 — Requisition Creation & Demand Capture**

Purpose: let departments formally request procurement against approved APP lines.

**Design rule**

A requisition should normally be created **from one or more approved Procurement Plan Items**. Manual standalone requisitions should be rare and heavily controlled.

**Requisition types**

- Standard Requisition
- Aggregated Requisition
- Emergency Requisition
- One-Off Requisition
- Amendment Requisition
- Cancellation Request

**Core business logic**

- a requisition may reference one or more APP items if aggregation is legitimate
- one APP item may feed multiple requisitions over time only where partial execution is allowed and tracked
- one-off requisition is allowed only with justification and exceptional approval
- once requisition enters tendering, core scope fields become non-editable

**Module 2 — Budget Validation & Commitment Control**

Purpose: ensure no requisition proceeds without funding discipline.

**Core rule**

**Encumbrance / commitment should happen at requisition approval**, not just at APP level. That is consistent with the source requirements and architecture.

**Controls**

- validate budget head, vote, program code, cost center/project, and available balance
- compare requisition total to remaining APP item balance
- block or warn based on budget control rules
- create commitment record on approval
- support partial commitments and releases on cancellation/reduction

**Module 3 — Approval Workflow & Segregation of Duties**

Purpose: enforce internal public-sector approvals.

**Recommended standard workflow**

**Requestor → Head of Department → Finance/Budget Officer → Accounting Officer → Head of Procurement**

That exact sequence is strong and should remain the baseline unless policy rules change by entity.

**SoD controls**

- requestor cannot approve own requisition
- finance validates funds but cannot alter technical need
- procurement confirms route to method/tender readiness
- accounting officer authorizes commitment of public funds

**Module 4 — Requisition Change Control**

Purpose: stop uncontrolled edits after approval.

**Must support**

- amendment before tender
- cancellation
- partial reduction
- scope/date adjustment with reason
- soft delete only
- full field-level change history

**Critical rule**

After approval, material fields cannot be silently edited:

- source APP item(s)
- quantities
- specifications
- amount
- delivery timeline
- budget allocation
- department ownership

Material changes should create an **amendment flow**, not direct overwrite.

**Module 5 — Exception & Emergency Controls**

Purpose: support reality without breaking governance.

**Exception paths**

- one-off requisition not in APP
- emergency requisition
- threshold override
- budget override
- retrospective justification route where law/policy permits

**Required controls**

- reason mandatory
- elevated approvals
- automatic exception register entry
- mandatory post-facto review for emergency cases

**Module 6 — Tender Handoff**

Purpose: produce a clean, locked demand package for Phase 2.

**Handoff principle**

A Tender should be created **from approved requisition(s)**, not from raw APP lines directly.

**Handoff payload**

Tender creation should inherit or reference:

- requisition header
- requisition lines
- originating APP item(s)
- quantities/spec summaries
- budget ceiling/reference
- delivery location
- required timeline
- attachments/specification documents
- approval trail

**5\. Core DocTypes for Phase 1.5**

**Transaction DocTypes**

- **Purchase Requisition**
- **Requisition Item**
- **Requisition Amendment**
- **Requisition Commitment**
- **Requisition Exception Record**
- **Requisition Approval Log**
- **Requisition Snapshot**
- **Requisition-to-Tender Handoff**

**Reused/linked records**

- Procurement Plan
- Procurement Plan Item
- Budget / Cost Center / Project / GL structures
- Approval Matrix Rule
- Budget Control Rule
- Exception Register Entry

**6\. Detailed DocType design**

**6.1 Purchase Requisition**

Purpose: requisition header and approval container.

**Core fields**

- requisition_number — autogenerated unique ID
- entity — Company
- department — Department
- requestor — User
- requisition_type — Standard / Aggregated / Emergency / One-Off / Amendment
- financial_year
- request_date
- required_by_date
- justification — mandatory
- technical_summary
- delivery_location
- budget_reference
- program_code
- cost_center
- project
- currency
- total_estimated_cost
- total_committed_amount
- status — Draft / Submitted / HoD Review / Finance Review / AO Review / Procurement Review / Approved / Rejected / Cancelled / Closed
- approval_status
- budget_status — Unchecked / Available / Warning / Blocked / Committed / Released
- emergency_flag
- one_off_flag
- exception_flag
- source_mode — APP Linked / One-Off
- tender_readiness_status
- linked_tender_count
- submitted_on
- approved_on
- cancelled_on
- closed_on

**Header rules**

- department and requestor mandatory
- either APP-linked lines or approved one-off justification required
- no submission without at least one requisition line
- total cost computed from lines
- if emergency_flag = 1, exception workflow mandatory

**6.2 Requisition Item**

Purpose: atomic demand lines within the requisition.

**Core fields**

- parent_requisition
- procurement_plan_item — optional only for one-off
- line_number
- item_description
- technical_specification
- procurement_type
- category
- quantity
- uom
- estimated_unit_cost
- estimated_total_cost
- delivery_timeline
- delivery_location
- budget_head
- cost_center
- project
- funding_source
- procurement_method_hint
- line_status
- remaining_app_balance
- commitment_amount
- tendered_amount
- awarded_amount
- received_amount

**Line rules**

- if APP-linked, line must inherit/validate against approved Procurement Plan Item
- requisition line cannot exceed remaining approved balance unless authorized amendment exists
- one requisition line may map to one APP item for clean traceability
- aggregated requisition may contain multiple lines from multiple APP items, but each line should preserve its source APP item

**6.3 Requisition Amendment**

Purpose: controlled post-submission or post-approval change.

**Fields**

- purchase_requisition
- amendment_number
- amendment_type — scope / quantity / budget / timeline / cancellation / administrative
- reason
- requested_by
- approved_by
- status
- effective_date

**Child table**

- changed field
- old value
- new value
- reason

**Rule**

If tender has not yet started, approved amendment may update active requisition state.  
If tender has started, material changes should block and force procurement-side decision: cancel/re-tender or tightly controlled addendum path later in Phase 2.

**6.4 Requisition Commitment**

Purpose: record encumbrance at requisition stage.

**Fields**

- commitment_number
- purchase_requisition
- requisition_item
- budget_head
- cost_center
- project
- committed_amount
- actualized_amount
- released_amount
- status — Active / Partially Consumed / Consumed / Released / Cancelled
- created_from_approval_stage
- release_reason

**Rule**

Created when requisition is approved.  
Reduced or released when requisition is cancelled, reduced, or fully passed into contract/PO lifecycle later.

**6.5 Requisition Exception Record**

Purpose: centralize non-standard cases.

**Fields**

- purchase_requisition
- exception_type — One-Off / Emergency / Budget Override / Split Risk / Threshold Override / Retrospective Justification
- reason
- risk_level
- requested_by
- reviewed_by
- approved_by
- status
- post_review_required

**6.6 Requisition Snapshot**

Purpose: immutable state at key moments.

**Snapshot events**

- submission
- approval
- amendment approval
- cancellation
- tender handoff

This matters because public-sector controls live or die on evidence.

**7\. Workflow design**

**7.1 Standard requisition workflow**

**Draft → Submitted → HoD Review → Finance Review → Accounting Officer Review → Procurement Review → Approved**

This sequence is defensible and matches the source direction.

**Transition logic**

- Draft → Submitted  
    requestor
- Submitted → HoD Review  
    system / route
- HoD Review → Finance Review  
    HoD approval
- Finance Review → AO Review  
    budget confirmed
- AO Review → Procurement Review  
    commitment authority approval
- Procurement Review → Approved  
    procurement accepts for execution readiness

**Why Procurement Review after AO can still make sense**

Because Finance/AO validate internal authority and commitment of funds; Procurement confirms the requisition is complete and executable before it enters tendering. If you want a different order later, it can be policy-driven, but this sequence is valid.

**7.2 Alternative workflow for some entities**

**Draft → HoD → Procurement → Finance → AO → Approved**

That variant may also work. The approval matrix should allow configuration by entity, but the default should remain close to the source pack.

**7.3 Emergency requisition workflow**

**Draft Emergency → HoD / Emergency Authority → Finance Fast Review → AO Fast Approval → Procurement Review → Approved Emergency**

**Rules**

- mandatory emergency rationale
- mandatory exception record
- mandatory post-facto review
- no silent bypass of audit trail

**7.4 Cancellation workflow**

**Approved → Cancellation Requested → Review → Cancelled**  
with commitment release logic and full logging.

**8\. Core business rules**

**8.1 APP linkage rule**

Normal requisitions must map to approved APP lines.

**Allowed exception**

One-off requisition may proceed only if:

- explicit justification exists
- proper exceptional approvals exist
- exception is logged for audit

**8.2 Budget rule**

No requisition may be approved unless budget availability has been checked.

**Possible outcomes**

- pass
- warning with override
- block

based on Budget Control Rule.

**8.3 Encumbrance rule**

Approval of requisition creates commitment/encumbrance.

This is one of the most important controls in the module.

**8.4 Anti-split rule**

The system should detect probable fragmentation through heuristics such as:

- similar descriptions/specifications
- same department
- same category
- same budget head
- close request dates
- values clustering around method thresholds

**Outcome**

- warning
- block
- exception review

**8.5 Soft-delete only**

Deleted requisitions must never vanish. They should be marked cancelled/voided with:

- reason
- user
- timestamp
- approving authority where required

**8.6 Change lock rule**

After approval, direct editing of material fields is blocked. Use amendment workflow instead.

**8.7 Tender handoff rule**

Once requisition is linked to an active tender:

- scope changes are restricted
- cancellation requires higher control
- line values cannot be casually edited

**9\. Aggregation and splitting model**

This is where many systems get sloppy. Don’t let that happen.

**Allowed aggregation**

Multiple APP items may be consolidated into one requisition where:

- same department or coordinated demand
- same procurement objective/category
- same timing window
- same funding logic or compatible allocations
- aggregation improves compliance and efficiency

**Allowed splitting**

One APP item may be consumed by multiple requisitions where:

- staged procurement is legitimate
- framework/call-off style need exists later
- phased delivery is justified
- remaining balance is tracked clearly

**Not allowed**

Artificial splitting to stay below threshold or avoid approval route.

**System design response**

Track at both levels:

- APP item available balance
- requisition lineage and cumulative consumption

**10\. Roles and permissions**

**Roles**

- Requestor
- Head of Department
- Finance/Budget Officer
- Accounting Officer
- Procurement Officer
- Head of Procurement
- Internal Auditor
- System Administrator

**Permission summary**

**Requestor**

- create draft requisition
- edit own draft
- submit
- cannot approve own requisition

**Head of Department**

- review need legitimacy
- approve/reject/return departmental requisition

**Finance/Budget Officer**

- validate funds
- confirm budget allocation
- recommend/block override
- cannot alter technical need

**Accounting Officer**

- approve commitment of public funds
- approve exceptional one-off or emergency routes above threshold

**Procurement Officer / Head of Procurement**

- validate procurement completeness
- confirm readiness for tender creation
- return incomplete requisitions
- cannot silently rewrite business need

**Internal Auditor**

- read-only access to logs, snapshots, exceptions, amendments, commitment history

**11\. UI / workspace design**

**Requisition Workspace**

For requestors and departments:

- Create Requisition
- My Drafts
- Returned for Correction
- Requisitions Awaiting HoD Action
- Department Demand Register

**Finance Workspace**

- Budget Validation Queue
- Blocked/Warning Requisitions
- Commitment Register
- Override Queue

**Procurement Workspace**

- Approved Requisitions Awaiting Tendering
- Incomplete/Returned Requisitions
- Emergency Requisition Queue
- Split-Risk Alerts

**Audit / Executive Workspace**

- Pending AO Approvals
- Exception Register
- Amendment Register
- Cancellation Register
- Requisition-to-Tender Traceability

**12\. Reports and dashboards**

**Mandatory operational reports**

- Requisitions by Department
- Requisitions by Status
- Budget vs Committed by Requisition
- Requisition Aging Report
- Requisition Approval Turnaround
- APP-to-Requisition Traceability
- Split/Fragmentation Alert Report
- One-Off and Emergency Requisition Register
- Cancelled Requisition Report
- Requisition-to-Tender Conversion Report

**Mandatory audit reports**

- Requisition Approval Trail
- Requisition Amendment Log
- Budget Override Log
- Commitment Creation and Release Log
- Deleted/Voided Requisition Report
- User Action Audit Log

**13\. ERPNext implementation approach**

**Reuse**

Use ERPNext structures for:

- Company
- Fiscal Year
- Department
- User
- Cost Center
- Project
- Budget / GL structures
- UOM

**Keep custom in KenTender**

Create custom DocTypes for:

- Purchase Requisition
- Requisition Item
- Requisition Amendment
- Requisition Commitment
- Requisition Exception Record
- Requisition Snapshot

**Important implementation call**

Do **not** reduce requisition to a generic Material Request clone.  
Public-sector requisition in this system has stronger APP linkage, budget controls, approvals, and audit requirements.

**14\. Acceptance criteria**

This module is acceptable only if all of these pass:

1.  A requisition cannot be approved without valid budget status.
2.  A normal requisition cannot proceed without APP linkage.
3.  One-off requisitions require exception justification and elevated approval.
4.  Requestor cannot approve own requisition.
5.  Approval creates commitment/encumbrance.
6.  Cancellation or reduction releases commitment correctly.
7.  Approved requisition cannot be materially edited without amendment flow.
8.  Probable split requisitions are flagged or blocked.
9.  Tender cannot be created without approved requisition reference, except controlled emergency policy path.
10. Every requisition preserves full audit history.

**15\. Recommended final design stance**

For Kentender, **Purchase Requisition should now be treated as a full standalone control module inside Phase 1**, not a side note.

That means:

- APP controls the plan
- Requisition controls the approved demand
- Tender controls the market process

That boundary is clean, strong, and defensible.

# Phase 1.5 Build-Ready Specification

**Module: Purchase Requisition / Demand Finalization**

**1\. Build objective**

Build a requisition module that:

- converts approved APP demand into executable procurement requests,
- enforces budget validation and encumbrance,
- routes through public-sector approvals,
- prevents threshold avoidance and uncontrolled edits,
- and hands off only approved, locked demand into tendering.

This is the last **internal** control point before market interaction.

**2\. Final module scope**

**In scope**

- requisition creation from APP items
- controlled one-off requisitions
- multi-line requisitions
- budget validation and commitment creation
- approval workflow and SoD
- amendment and cancellation
- emergency and exception routing
- tender handoff control
- audit logs, dashboards, and reports

**Out of scope**

- supplier interaction
- tender publication
- bid handling
- evaluation and award
- contract administration

**3\. Final DocType architecture**

**Core transaction DocTypes**

1.  **Purchase Requisition**
2.  **Purchase Requisition Item**
3.  **Purchase Requisition Amendment**
4.  **Purchase Requisition Commitment**
5.  **Purchase Requisition Exception**
6.  **Purchase Requisition Snapshot**
7.  **Purchase Requisition Approval**
8.  **Requisition Tender Handoff**

**Reused/linked DocTypes**

- Procurement Plan
- Procurement Plan Item
- Budget Control Rule
- Approval Matrix Rule
- Cost Center
- Project
- Department
- Company
- Fiscal Year
- Account / Budget Head
- User

**4\. Exact DocType definitions**

**4.1 Purchase Requisition**

Purpose: header record for internal procurement demand.

**Fields**

- requisition_number — Data — unique, autoname
- entity — Link Company — req
- department — Link Department — req
- requestor — Link User — req
- financial_year — Link Fiscal Year — req
- requisition_type — Select:
    - Standard
    - Aggregated
    - Emergency
    - One-Off
    - Amendment
    - Cancellation  
        — req
- source_mode — Select:
    - APP Linked
    - One-Off  
        — req
- request_date — Date — req
- required_by_date — Date — req
- justification — Long Text — req
- technical_summary — Small Text
- delivery_location — Data — req
- budget_reference — Data
- program_code — Data
- cost_center — Link Cost Center
- project — Link Project
- currency — Link Currency — req
- total_estimated_cost — Currency — read only
- total_committed_amount — Currency — read only
- total_released_amount — Currency — read only
- budget_status — Select:
    - Unchecked
    - Available
    - Warning
    - Blocked
    - Committed
    - Released  
        — default Unchecked
- tender_readiness_status — Select:
    - Not Ready
    - Ready for Tender
    - Tender Created
    - Fully Handed Off
- status — Select:
    - Draft
    - Submitted
    - HoD Review
    - Finance Review
    - AO Review
    - Procurement Review
    - Approved
    - Rejected
    - Cancelled
    - Closed  
        — req
- approval_status — Select:
    - Pending
    - Approved
    - Rejected
    - Returned
- emergency_flag — Check
- one_off_flag — Check
- exception_flag — Check
- linked_tender_count — Int — default 0
- submitted_on — Datetime
- approved_on — Datetime
- cancelled_on — Datetime
- closed_on — Datetime
- remarks — Small Text

**Child tables**

- items → Purchase Requisition Item
- approvals → Purchase Requisition Approval
- attachments
- milestones optional

**Rules**

- no submission without at least one line
- total_estimated_cost = sum of active line totals
- if source_mode = One-Off, one_off_flag must be true
- if emergency_flag = 1, exception record mandatory
- once approved, material fields become locked

**4.2 Purchase Requisition Item**

Purpose: demand lines inside the requisition.

**Fields**

- parent_requisition — Link Purchase Requisition — req
- line_number — Int — req
- procurement_plan_item — Link Procurement Plan Item
- item_description — Data — req
- technical_specification — Long Text — req
- procurement_type — Select:
    - Goods
    - Works
    - Non-Consulting Services
    - Consulting Services
    - Asset Disposal  
        — req
- category — Link Spend Category — req
- quantity — Float — req
- uom — Link UOM — req
- estimated_unit_cost — Currency — req
- estimated_total_cost — Currency — read only
- delivery_timeline — Data
- delivery_location — Data
- budget_head — Data / Link Account — req
- cost_center — Link Cost Center — req
- project — Link Project
- funding_source — Link Funding Source — req
- procurement_method_hint — Data
- remaining_app_balance — Currency — read only
- commitment_amount — Currency — read only
- tendered_amount — Currency — read only
- awarded_amount — Currency — read only
- received_amount — Currency — read only
- line_status — Select:
    - Draft
    - Validated
    - Approved
    - Tendered
    - Awarded
    - Closed
    - Cancelled

**Rules**

- estimated_total_cost = quantity \* estimated_unit_cost
- if APP-linked, line must reference approved Procurement Plan Item
- if APP-linked, cost cannot exceed remaining available APP balance unless approved amendment exists
- if one-off, justification must exist at header or line level
- each line should preserve one source APP item for traceability

**4.3 Purchase Requisition Approval**

Purpose: store approval actions and route history.

**Fields**

- parent_requisition — Link Purchase Requisition — req
- approval_stage — Select:
    - Submission
    - HoD Review
    - Finance Review
    - AO Review
    - Procurement Review
    - Final Approval
- approver_role — Data — req
- approver_user — Link User
- action — Select:
    - Pending
    - Approved
    - Rejected
    - Returned
    - Skipped
- action_date — Datetime
- comments — Small Text

**Rules**

- route generated from approval matrix or default sequence
- requestor cannot approve own requisition
- all mandatory stages must complete before final approval

**4.4 Purchase Requisition Commitment**

Purpose: budget encumbrance created at approval.

**Fields**

- commitment_number — Data — unique
- purchase_requisition — Link Purchase Requisition — req
- requisition_item — Link Purchase Requisition Item — req
- entity — Link Company — req
- financial_year — Link Fiscal Year — req
- budget_head — Data / Link Account — req
- cost_center — Link Cost Center — req
- project — Link Project
- committed_amount — Currency — req
- actualized_amount — Currency — default 0
- released_amount — Currency — default 0
- status — Select:
    - Active
    - Partially Consumed
    - Consumed
    - Released
    - Cancelled
- created_from_stage — Data
- created_on — Datetime
- released_on — Datetime
- release_reason — Small Text

**Rules**

- created on requisition approval
- one record per requisition line by default
- release on cancellation/reduction
- reduce on downstream award/PO consumption later

**4.5 Purchase Requisition Exception**

Purpose: non-standard requisition governance.

**Fields**

- purchase_requisition — Link Purchase Requisition — req
- exception_type — Select:
    - One-Off
    - Emergency
    - Budget Override
    - Threshold Override
    - Split Risk
    - Retrospective Justification
- reason — Long Text — req
- risk_level — Select:
    - Low
    - Medium
    - High
- requested_by — Link User — req
- reviewed_by — Link User
- approved_by — Link User
- status — Select:
    - Draft
    - Under Review
    - Approved
    - Rejected
    - Closed
- post_review_required — Check
- post_review_due_date — Date

**Rules**

- mandatory for one-off and emergency
- auto-create for anti-split breach or budget override
- post-review mandatory for emergency path

**4.6 Purchase Requisition Amendment**

Purpose: controlled changes after submission/approval.

**Fields**

- amendment_number — Data — unique
- purchase_requisition — Link Purchase Requisition — req
- amendment_type — Select:
    - Scope
    - Quantity
    - Budget
    - Timeline
    - Cancellation
    - Administrative
- reason — Long Text — req
- requested_by — Link User — req
- submitted_on — Datetime
- approved_by — Link User
- approved_on — Datetime
- status — Select:
    - Draft
    - Under Review
    - Approved
    - Rejected
    - Applied

**Child table**

- changes
    - field_name
    - old_value
    - new_value
    - reason

**Rules**

- no silent edits to approved requisitions
- if tender already exists, material changes block and require cancellation/reissue or controlled downstream handling
- cancellation amendment triggers commitment release

**4.7 Purchase Requisition Snapshot**

Purpose: immutable audit snapshots.

**Fields**

- purchase_requisition — Link Purchase Requisition — req
- snapshot_type — Select:
    - Submission
    - Approval
    - Amendment Approval
    - Cancellation
    - Tender Handoff
- snapshot_json — Long Text / Code
- created_by — Link User
- created_on — Datetime

**Rule**

- create automatically at key state transitions

**4.8 Requisition Tender Handoff**

Purpose: controlled transition into Phase 2.

**Fields**

- handoff_number — Data — unique
- purchase_requisition — Link Purchase Requisition — req
- handoff_status — Select:
    - Draft
    - Ready
    - Tender Created
    - Closed
- prepared_by — Link User
- prepared_on — Datetime
- approved_for_tender_by — Link User
- approved_for_tender_on — Datetime
- tender_reference — Data / Link Tender
- notes — Small Text

**Rules**

- only approved requisitions can be handed off
- handoff freezes core scope fields
- one requisition may create one tender or contribute to an aggregated tender, but lineage must remain visible

**5\. Workflow design**

**5.1 Standard workflow**

**Draft → Submitted → HoD Review → Finance Review → AO Review → Procurement Review → Approved**

**Transition ownership**

- Draft → Submitted: Requestor
- Submitted → HoD Review: system route
- HoD Review → Finance Review: HoD
- Finance Review → AO Review: Finance/Budget Officer
- AO Review → Procurement Review: Accounting Officer
- Procurement Review → Approved: Procurement Officer / Head of Procurement

**Return paths**

Any review step may:

- Return to Draft
- Reject
- Escalate to Exception Review

**5.2 Emergency workflow**

**Draft Emergency → HoD / Emergency Authority → Finance Fast Review → AO Fast Approval → Procurement Review → Approved**

**Rules**

- mandatory emergency justification
- mandatory exception record
- mandatory post-facto review
- audit trail cannot be bypassed

**5.3 Cancellation workflow**

**Approved → Cancellation Requested → Review → Cancelled**

**Rules**

- release active commitments
- prevent deletion
- preserve full history

**5.4 Amendment workflow**

**Approved → Amendment Drafted → Review → Approved Amendment → Applied**

**Rules**

- if not yet handed off to tender, approved amendment may update active requisition
- if handed off, material changes should block and require procurement decision

**6\. Role and permission matrix**

**Roles**

- Requestor
- Head of Department
- Finance/Budget Officer
- Accounting Officer
- Procurement Officer
- Head of Procurement
- Internal Auditor
- System Administrator

**Permission summary**

**Requestor**

- create draft requisition
- edit own draft
- submit
- view own department requisitions where permitted
- cannot approve own requisition

**Head of Department**

- review and approve departmental need
- return or reject
- cannot create commitments directly

**Finance/Budget Officer**

- validate funds
- confirm budget status
- recommend override
- create/validate commitment records through approval action
- cannot change technical specs

**Accounting Officer**

- authorize financial commitment
- approve exceptions above authority thresholds

**Procurement Officer / Head of Procurement**

- validate completeness
- confirm readiness for tender
- return incomplete requisitions
- cannot rewrite departmental need silently

**Internal Auditor**

- read-only access to requisitions, amendments, exceptions, approvals, commitments, snapshots

**System Administrator**

- configuration and support only

**7\. Validation logic**

**Header-level validations**

On save/submit:

- department required
- requestor required
- required by date required
- justification required
- at least one line required
- total_estimated_cost must equal line sums

**Source validations**

- if source_mode = APP Linked, every active line must have procurement_plan_item
- if source_mode = One-Off, exception record required before submission
- one-off cannot use normal approval path without elevated exception stage where configured

**Budget validations**

At Finance Review:

- validate budget availability by budget head / cost center / project
- compare requisition line total against:
    - APP remaining balance
    - current budget available
    - existing commitments
- set budget status:
    - Available
    - Warning
    - Blocked
- follow Budget Control Rule for stop/warn behavior

**Approval validations**

At final approval:

- all mandatory approval stages completed
- no pending exception record
- no blocked budget lines
- commitments can be created successfully

**Amendment validations**

- direct edit of approved material fields blocked
- amendment required for:
    - quantity
    - cost
    - budget head
    - source APP item
    - required date
    - technical specification
- if tender already created, scope amendments blocked unless allowed by policy

**Anti-split validations**

Run at submit and finance review:

- detect similar descriptions
- same department
- same category
- same budget head
- same short date window
- threshold-edge values

**Outcomes**

- informational flag
- warning requiring review
- block with exception record

**Cancellation validations**

- only approved requisitions can enter cancellation flow
- active commitments must be released or reduced
- if active tender exists, cancellation must escalate

**8\. Automations and hooks**

**Required server-side logic**

1.  requisition number generation
2.  line total and header total aggregation
3.  APP balance check
4.  budget availability check
5.  approval-route generation
6.  commitment creation on approval
7.  commitment release on cancellation/reduction
8.  exception auto-creation for one-off/emergency/anti-split
9.  snapshot creation at major events
10. tender handoff lock

**Suggested hooks**

- validate
- before_submit
- on_update_after_submit
- on_cancel
- workflow action hooks

**Scheduled jobs**

- alert on aging requisitions
- alert on emergency requisitions awaiting post-review
- alert on approved requisitions not handed off to tender after SLA
- detect duplicate/split patterns periodically

**9\. UI / workspace design**

**Requisition Workspace**

For requestors and departments:

- New Requisition
- My Drafts
- Submitted Requisitions
- Returned for Correction
- Department Requisition Register

**Finance Workspace**

- Budget Validation Queue
- Warning/Blocked Requisitions
- Active Commitments
- Override Reviews

**Procurement Workspace**

- Approved Requisitions Awaiting Tender
- Incomplete Requisitions
- Emergency Queue
- Split-Risk Alerts
- Tender Handoff Queue

**Audit / Executive Workspace**

- Pending AO Reviews
- Exception Register
- Amendment Register
- Cancellation Register
- Requisition Audit Trail

**10\. Reports to build**

**Operational reports**

1.  Requisitions by Department
2.  Requisitions by Status
3.  Budget vs Committed by Requisition
4.  Requisition Aging
5.  Approval Turnaround Time
6.  APP-to-Requisition Traceability
7.  One-Off Requisition Register
8.  Emergency Requisition Register
9.  Split/Fragmentation Alert Report
10. Requisition-to-Tender Conversion Report

**Audit reports**

1.  Requisition Approval Trail
2.  Requisition Amendment Log
3.  Commitment Creation and Release Log
4.  Cancelled/Void Requisition Report
5.  Exception Register Report
6.  User Action Log

**11\. User stories**

**Demand creation**

- As a departmental requestor, I can create a requisition from approved APP items so procurement starts from authorized demand.
- As a departmental requestor, I can create a one-off requisition only with justification and exception routing.

**Budget and approval**

- As a finance officer, I can validate budget availability before approval.
- As an accounting officer, I can approve commitment of funds only after budget and departmental checks pass.

**Governance**

- As procurement, I can reject incomplete requisitions before tendering starts.
- As an auditor, I can view every approval, amendment, exception, and cancellation without relying on deleted history.

**Handoff**

- As procurement, I can create a tender only from approved requisitions with locked demand data.

**12\. Acceptance criteria**

The module is acceptable only if all of these pass:

1.  Requisition cannot be submitted without lines.
2.  Normal requisition cannot proceed without APP linkage.
3.  One-off requisition requires exception approval.
4.  Requestor cannot approve own requisition.
5.  Finance review sets valid budget status.
6.  Final approval creates commitment records.
7.  Approved requisition cannot be materially edited directly.
8.  Cancellation releases commitments correctly.
9.  Probable split requisitions are flagged or blocked.
10. Tender handoff requires approved requisition.
11. Snapshots are created at approval, amendment, cancellation, and handoff.
12. No requisition is hard-deleted from operational history.

**13\. Recommended build sequence**

**Sprint 1**

- Purchase Requisition
- Purchase Requisition Item
- numbering
- basic validation
- APP linkage

**Sprint 2**

- approval routing
- finance validation
- commitment creation
- role permissions

**Sprint 3**

- exceptions
- emergency workflow
- anti-split logic
- snapshots

**Sprint 4**

- amendments
- cancellations
- handoff to tender
- reports and dashboards

**14\. Final design stance**

This is the right architecture boundary:

- **Phase 1**: APP and demand authorization
- **Phase 1.5**: Purchase Requisition and commitment control
- **Phase 2**: Supplier registration and tendering lifecycle

That keeps planning, demand control, and market execution separate and clean.