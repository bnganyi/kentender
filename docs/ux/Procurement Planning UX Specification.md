# Procurement Planning UX Specification

**KenTender – Implementation Grade**

**1\. Purpose & Scope**

**1.1 Purpose**

The Procurement Planning module is responsible for:

- transforming **approved requisitions into structured procurement actions**
- defining **how procurement will be executed**
- configuring **downstream system behavior via templates**

**1.2 Role in System**

Planning is the:

👉 **Control layer of procurement**

It determines:

- procurement method
- evaluation model
- acceptance workflow
- approval structure

**1.3 Inputs & Outputs**

**Inputs**

- Approved Requisitions

**Outputs**

- Procurement Plans
- Procurement Plan Items
- Template-resolved execution configuration

**1.4 Key UX Requirement**

Planning must make visible:

- how demand is structured
- how process is configured
- how downstream behavior is determined

**2\. Actors & Roles**

**2.1 Procurement Officer (Primary User)**

Capabilities:

- create and manage plans
- define plan items
- allocate requisitions
- trigger template resolution

**2.2 Head of Department (HoD)**

Capabilities:

- approve template overrides
- review planning decisions

**2.3 Finance Officer (Optional)**

Capabilities:

- view funding and budget alignment
- validate financial fields

**2.4 Auditor**

Capabilities:

- read-only access
- view full traceability

**3\. Core UI Objects**

**3.1 Procurement Plan**

- container for planning period
- groups plan items
- governs approval and activation

**3.2 Procurement Plan Item**

👉 **Primary UX object**

Defines:

- procurement configuration
- template resolution
- allocation
- downstream behavior

**3.3 Requisition Allocation**

Tracks:

- which requisitions feed a plan item
- quantity allocation
- remaining demand

**3.4 Template Resolution**

System-generated:

- procurement template
- evaluation template
- acceptance template

**4\. Workspace Definition**

**4.1 Workspace Layout**

**Section 1 — Quick Actions**

Visible to Procurement Officer:

- Create Procurement Plan
- Add Plan Item
- Import Requisitions

**Section 2 — My Work Queue**

**Queue: Draft Plan Items**

- Filter: workflow_state = Draft
- Owner = current user

**Queue: Plan Items Pending Template Resolution**

- Filter:
    - template not resolved OR
    - match_quality = Partial
- Action required: resolve or override

**Queue: Plan Items Pending Override Approval**

- Visible to HoD
- Filter: override_status = Pending

**Queue: Plans Pending Submission**

- Draft plans with complete items

**Queue: Plans Pending Approval**

- Submitted plans awaiting approval

**Section 3 — Monitoring Panels**

**Panel: Requisitions Not Planned**

- Approved requisitions not linked to any plan item

**Panel: Partially Planned Requisitions**

- requisitions with remaining_quantity > 0

**Panel: Fully Planned Requisitions**

- requisitions fully allocated

**Panel: Active Plan Items**

- workflow_state = Active

**Panel: High-Value / High-Risk Plans**

- filtered by threshold / risk level

**Section 4 — Navigation / Drill-down**

- View Requisitions
- View Plan Items
- View Templates

**5\. Procurement Plan Form**

**5.1 Header**

Displays:

- Plan ID (name)
- Workflow State
- Owner
- Planning Period

**5.2 Tabs**

**Summary Tab**

Fields:

- Entity
- Planning Period
- Description

**Plan Items Tab**

Child table:

- Plan Item ID
- Category
- Estimated Value
- Template
- Workflow State

**Workflow Tab**

Displays:

- approval history
- current stage

**Audit Tab**

Displays:

- system logs
- changes
- actions

**5.3 Actions**

**Submit Plan**

- validates all plan items
- blocks if:
    - unresolved templates
    - allocation errors

**Approve Plan**

- locks structure

**Activate Plan**

Enables:

- tender creation

Locks:

- template
- procurement method

**6\. Procurement Plan Item Form**

**6.1 Header**

Displays:

- Plan Item ID
- Workflow State
- Template + Version
- Match Quality
- Override Status

**6.2 Sections**

**A. Source & Allocation Section**

**Linked Requisitions Table**

Columns:

- Requisition ID
- Requested Quantity
- Allocated Quantity
- Remaining Quantity

**Validation Rules**

- Allocated ≤ Requested
- Remaining = Requested − Allocated

**UI Behavior**

- highlight over-allocation in red
- show remaining quantities clearly

**B. Procurement Configuration Section**

Fields:

- Procurement Method
- Category (Goods / Works / Services)
- Complexity Classification
- Risk Level
- Funding Source

**Behavior**

- method required before template resolution
- complexity drives template selection

**C. Template Resolution Section**

**System Fields**

- Selected Template
- Template Version
- Match Quality

**Match Quality**

- Exact
- Partial

**Mismatch Details**

Example:

Requested: Complexity HIGH  
Matched: Complexity MEDIUM

**Override Panel**

Fields:

- Override Requested (checkbox)
- Override Reason (mandatory)
- Override Template (if applicable)
- Override Status

**UI Rules**

- cannot submit with unresolved partial match unless override requested
- cannot proceed if override pending

**D. Constraints & Requirements Section**

Fields:

- Eligibility Constraints
- Special Requirements
- Regulatory Flags

**Behavior**

- displayed downstream in Tender
- cannot be empty if required by template

**E. Packaging / Structure Section**

Fields:

- Packaging Strategy:
    - Single Lot
    - Multi-Lot

**If Multi-Lot:**

Display Lot Table:

- Lot Number
- Description
- Quantity

**F. Timeline Section**

Fields:

- Planned Start Date
- Publication Date
- Award Date

**G. System Context Panel (Read-only)**

Displays:

This Plan Item defines:  
\- Tender Method  
\- Evaluation Model  
\- Acceptance Workflow

👉 This is critical for user understanding

**6.3 Smart Buttons**

**View Template Details**

- opens template record

**Request Override**

- opens override dialog

**View Allocation Breakdown**

- detailed allocation view

**Create Tender**

Visible ONLY if:

- plan is Active
- template resolved
- no pending overrides

**7\. Template Interaction UX**

**7.1 Template Resolution Trigger**

Occurs when:

- required fields set
- or manually triggered

**7.2 Exact Match**

UI:

- green indicator
- no action required

**7.3 Partial Match**

UI:

- warning indicator
- mismatch explanation
- suggest override

**7.4 Override Flow**

Steps:

1.  User requests override
2.  HoD reviews
3.  Approves / rejects

**UX Behavior**

- show override status prominently
- block progression until resolved

**8\. Workflow & State Behavior**

**8.1 States**

- Draft
- Submitted
- Approved
- Active

**8.2 Behavior per State**

| **State** | **UX Behavior** |
| --- | --- |
| Draft | Fully editable |
| Submitted | Locked (except comments) |
| Approved | Locked |
| Active | Enables downstream |

**9\. Validation & Blocking UX**

**9.1 Blocking Conditions**

- Template not resolved
- Allocation invalid
- Override pending
- Missing required fields

**9.2 UI Messaging**

Example:

Cannot submit:  
\- Template not resolved  
\- Override pending approval

**10\. Integration Points**

**10.1 Requisitions**

- View source requisition
- Track planning status

**10.2 Tender**

- Tender must originate from Plan Item
- No manual tender creation

**11\. Role-Based Visibility**

**Procurement Officer**

- full access

**HoD**

- override approval only

**Finance**

- read / validate

**Auditor**

- read-only

**12\. UX Anti-Patterns**

❌ Manual procurement definition  
❌ Hidden template logic  
❌ Over-allocation without visibility  
❌ No grouping clarity

**13\. Acceptance Criteria**

Planning UX is complete when:

- user understands allocation clearly
- template logic is visible
- grouping/splitting is explicit
- constraints are clear
- downstream impact is understood

**Final Note**

This is now:

- complete
- implementation-grade
- aligned with your system