# KenTender

Product Requirements Document

# Section 1: Product Scope & Definition

## 1.1 Product Name

**KenTender — Integrated Public Procurement, Planning & Budget Control System**

## 1.2 Product Vision

KenTender is a **national-grade digital governance platform** that manages and enforces the full lifecycle of public expenditure:

- Strategic planning
- Budget allocation and control
- Procurement execution
- Contract delivery and performance tracking

The system ensures that:

**Every shilling spent is traceable from national strategy → budget → procurement → outcome**

## 1.3 Core Value Proposition

KenTender is not:

- a tender portal
- a procurement tracking tool

It is:

**A compliance-enforced, performance-linked public expenditure system**

## 1.4 Problem Statement

Current public procurement ecosystems suffer from:

- Weak linkage between strategy and procurement
- Budget leakage and over-commitment
- Fragmented planning across departments
- Limited audit traceability
- Document-based, non-structured processes
- Low visibility of procurement outcomes vs intended impact

## 1.5 Solution Overview

KenTender solves this by enforcing:

**1\. Strategic Alignment**

Every procurement must link to:

- National Development Plan (e.g., Vision 2030 / CIDP / MTP)
- Ministerial / County Strategic Plans
- Corporate Plans
- Department Work Plans

**2\. Budget Control**

- Budget defined and allocated within system
- Real-time commitment tracking
- No procurement without budget

**3\. Structured Procurement Execution**

- End-to-end digital workflows
- Role-based approvals
- Secure bid handling

**4\. Performance Traceability**

Each procurement line must link to:

- Strategic objective code
- Program
- Sub-program
- Output indicator
- Performance target

## 1.6 System Scope (Expanded and Locked)

**INCLUDED**

**A. Strategic Planning Layer**

- National plan structures (reference/import)
- Institutional strategic plans
- Program and sub-program definition
- Output indicators and targets

**B. Budget Management Layer**

- Budget definition (annual / multi-year)
- Budget line creation
- Allocation by program / department
- Commitment tracking
- Budget utilization monitoring

**C. Demand & Requisition Layer**

- Department requisitions
- Justification and specification capture
- Mandatory linkage to:
    - Budget
    - Strategic structure

**D. Procurement Planning Layer**

- Consolidation of requisitions
- Procurement plan creation
- Approval workflows

**E. Procurement Execution Layer**

- Tender creation & publishing
- Bid submission & opening
- Evaluation & scoring
- Award & approvals

**F. Contract & Execution Layer**

- Contract creation
- Milestone tracking
- Deliverables and performance tracking

**G. Inspection & Acceptance**

- Goods/services verification
- Acceptance/rejection workflows

**H. Complaints & Disputes**

- Filing and tracking
- Resolution workflows

**I. Audit & Compliance**

- Full audit trail
- Compliance reporting
- Red flag detection

**J. Public Transparency Portal**

- Tender publication
- Award disclosure
- Contract visibility (controlled)

**K. Reporting & Analytics**

- Budget vs actual
- Procurement performance
- Strategic outcome tracking

**L. System Administration**

- Role management
- Workflow configuration
- Templates and thresholds

**EXCLUDED (But Integrated)**

- Full accounting (GL, payments)
- Treasury management
- Banking systems
- External identity systems

## 1.7 Strategic Alignment Model (Locked Requirement)

Every procurement line item MUST include:

- Strategic Objective Code
- Program
- Sub-Program
- Output Indicator
- Performance Target

**Enforcement:**

- Hard validation (cannot proceed without linkage)
- Alignment verified at:
    - Requisition stage
    - Planning stage

**Outcome:**

- Performance-based procurement
- End-to-end traceability
- Elimination of fragmented spending

## 1.8 Deployment Model

**National Multi-Tenant Platform**

- Single platform
- Multiple Procuring Entities
- Shared:
    - Standards
    - Strategic structures
    - Compliance rules

**Entity-Level Autonomy**

- Configurable workflows
- Role assignments
- Internal approval structures

## 1.9 Governance Model

**Central Authority**

- Defines:
    - Strategic frameworks
    - Compliance rules
    - Templates

**Procuring Entities**

- Execute procurement within defined constraints

**Oversight Bodies**

- Full visibility across entities
- Audit and compliance enforcement

## 1.10 Core Design Principles

**1\. Strategy → Budget → Procurement Integrity**

No activity can break this chain.

**2\. Budget as Control Mechanism**

Procurement is constrained by budget availability.

**3\. Structured Data First**

Everything must be machine-readable and analyzable.

**4\. Full Auditability**

Every action is logged and immutable.

**5\. Separation of Duties**

No role conflict allowed.

**6\. Configurable Workflows with Guardrails**

Flexibility without breaking compliance.

**7\. Security by Design**

- Encrypted bid handling
- Role-based access
- Controlled disclosures

## 1.11 Success Metrics (Revised)

**Strategic Alignment**

- % of procurement linked to strategic objectives
- % of budget aligned to national plans

**Financial Discipline**

- Budget deviation rates
- Over-commitment incidents

**Procurement Efficiency**

- Cycle time reduction
- Tender completion rates

**Transparency**

- Public disclosure rate
- Time to publish awards

**Performance Delivery**

- Procurement tied to achieved outputs
- Contract completion vs planned outcomes

# Section 2: User Roles & Actor Model

Defined roles are as follows.

## 2.1 Role Philosophy

- Roles represent **functional responsibilities**, not job titles
- Enforce:
    - Separation of duties
    - Traceability
    - Accountability

## 2.2 Role Categories

**A. Strategic & Planning Roles**

**Strategy Manager / Planning Authority**

- Defines strategic structures
- Validates alignment

**B. Budget & Finance Roles**

**Budget Officer**

- Creates and manages budget lines

**Finance Approver**

- Validates budget availability
- Approves financial commitments

**C. Demand & Requisition Roles**

**Department User (Requisitioner)**

- Initiates procurement need

**Head of Department (HOD)**

- Approves requisitions

**D. Procurement Roles**

**Procurement Officer**

- Executes procurement process

**Head of Procurement**

- Oversees compliance

**E. Evaluation Roles**

**Evaluation Committee Chair**

- Leads evaluation process

**Evaluation Committee Member**

- Evaluates bids

**F. Approval Roles**

**Tender Committee Member**

- Reviews evaluation outcome

**Accounting Officer**

- Final approval authority

**G. Post-Award Roles**

**Contract Manager**

**Inspection & Acceptance Officer**

**Stores Officer**

**H. Oversight Roles**

- Internal Auditor
- External Auditor
- Regulatory Authority

**I. System Roles**

**System Administrator**

- Configures system

## 2.3 Role Constraints (Critical)

- Requisitioner ≠ Approver
- Procurement Officer ≠ Evaluator
- Evaluator ≠ Approver
- Accounting Officer = final authority only

## 2.4 Role Assignment Model

- Multi-role support
- Entity-scoped roles
- Delegation allowed
- Time-bound assignments

# Section 3: Strategic Planning Module

## 3.1 Purpose

To establish a **structured, hierarchical strategic framework** that:

- Anchors all procurement activities to national and institutional priorities
- Enables performance-based procurement
- Ensures audit traceability from strategy → expenditure → outcomes

## 3.2 Architectural Position

This module sits at the **top of the system hierarchy**:

National Plans (Imported - Locked)  
↓  
Entity Strategic Plans  
↓  
Programs → Sub-Programs  
↓  
Output Indicators → Targets  
↓  
Budget Lines  
↓  
Procurement (Requisition → Plan → Tender)

## 3.3 Core Design Principles

**1\. National Plans Are Immutable**

- Imported into system
- Cannot be edited by entities
- Version-controlled by central authority only

**2\. Entity Plans Must Map Upwards**

Every entity-level structure must link to:

- National development framework
- Relevant strategic pillar / objective

**3\. Procurement Cannot Exist Without Strategic Linkage**

- Hard validation at requisition level

**4\. Performance is Measurable**

Every procurement must contribute to:

- Defined outputs
- Quantifiable targets

## 3.4 Core Entities

**1\. National Development Framework (Imported)**

**Fields:**

- Framework ID
- Name (e.g., Vision 2030, CIDP)
- Period (Start Year – End Year)
- Version
- Status (Active / Archived)

**2\. National Strategic Pillar**

- Pillar Code
- Name
- Description
- Parent Framework

**3\. National Strategic Objective**

- Objective Code
- Description
- Linked Pillar

These are **read-only for all non-central users**

**4\. Entity Strategic Plan**

**Fields:**

- Plan ID
- Entity
- Period
- Status (Draft / Approved / Active / Archived)

**5\. Program**

- Program Code
- Name
- Linked National Objective
- Description

**6\. Sub-Program**

- Sub-Program Code
- Name
- Parent Program
- Description

**7\. Output Indicator**

- Indicator Code
- Name
- Unit of Measure (e.g., km, units, %)
- Baseline Value
- Target Value
- Reporting Frequency

**8\. Performance Target**

- Target ID
- Linked Indicator
- Period (e.g., FY2026)
- Target Value
- Responsible Department

## 3.5 Relationships (Critical)

| **Entity** | **Must Link To** |
| --- | --- |
| Program | National Strategic Objective |
| Sub-Program | Program |
| Output Indicator | Sub-Program |
| Performance Target | Output Indicator |
| Budget Line | Sub-Program |
| Procurement Line | Output Indicator + Target |

This creates **full vertical traceability**

## 3.6 Workflow

**Entity Strategic Plan Lifecycle:**

1.  Draft
2.  Under Review
3.  Approved
4.  Active
5.  Archived

**Flow:**

Draft → Review → Approve → Activate

## 3.7 Functional Requirements

**FR-SP-001: Import National Plans**

- System must support:
    - Structured import (API / file)
    - Versioning
- Only central authority can update

**FR-SP-002: Create Entity Strategic Plan**

- Entities define their plans
- Must select:
    - Applicable national framework

**FR-SP-003: Define Programs & Sub-Programs**

- Must link to national objectives
- Cannot exist without linkage

**FR-SP-004: Define Output Indicators**

- Must be measurable
- Must include unit of measure

**FR-SP-005: Define Performance Targets**

- Must include:
    - Time period
    - Quantifiable value

**FR-SP-006: Enforce Strategic Mapping**

System must block:

- Budget creation without sub-program linkage
- Requisition without indicator linkage

**3.8 Validation Rules**

- No orphan entities (everything must link upward)
- Indicators must have measurable units
- Targets must be numeric or structured values
- Program codes must be unique per entity

**3.9 Versioning & Change Management**

- Strategic plans are versioned
- Changes require:
    - New version creation
    - Approval workflow

**Impact Handling:**

- Existing procurements remain linked to original version
- New procurements use updated version

## 3.10 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Import National Plans | Central Authority |
| Create Entity Plan | Strategy Manager |
| Approve Plan | Planning Authority |
| Modify Active Plan | Restricted (revision only) |

## 3.11 Audit Requirements

System must log:

- Plan creation
- Modifications
- Approvals
- Version changes
- Linkage changes

## 3.12 Outputs

- Structured strategic hierarchy
- Alignment dataset (used in reporting)
- Strategy → procurement traceability graph

## 3.13 Integration with Other Modules

**Budget Module**

- Budget lines must link to:
    - Sub-program
    - Indicator

**Requisition Module**

- Must link to:
    - Indicator
    - Performance target

**Reporting Module**

- Enables:
    - Outcome tracking
    - Performance reporting

# Section 4: Budget Management Module

## 4.1 Purpose

To define, allocate, control, and enforce the use of financial resources such that:

- No procurement occurs without an approved budget
- No spending exceeds allocated limits
- All commitments are tracked in real time
- Full traceability exists from budget → procurement → outcome

## 4.2 Core Design Principles

**1\. Budget is a Hard Constraint**

- System must **block** actions exceeding budget
- No overrides without formal reallocation

**2\. Commitment-Based Control**

Budget is consumed in stages:

- **Reserved** → at requisition
- **Committed** → at award
- **Actualized (external)** → during execution

**3\. Real-Time Budget Visibility**

At any time, system must show:

- Allocated
- Reserved
- Committed
- Available

**4\. No Orphan Spending**

Every budget line must link to:

- Strategic structure (Program/Sub-program)
- Funding source

## 4.3 Core Entities

**1\. Budget**

- Budget ID
- Entity
- Financial Year
- Status (Draft / Approved / Active / Closed)

**2\. Budget Line**

This is the core control unit.

**Fields:**

- Budget Line ID
- Program
- Sub-Program
- Output Indicator
- Department
- Funding Source
- Total Allocated Amount

**3\. Budget Allocation**

(Optional granular breakdown)

- Allocation ID
- Budget Line
- Amount
- Allocation Date

## 4\. Budget Ledger (Critical)

Tracks all financial movements.

**Fields:**

- Entry ID
- Budget Line
- Transaction Type:
    - Reservation (Requisition)
    - Commitment (Award)
    - Release (Cancellation)
- Amount
- Reference Document (Requisition ID, Tender ID, Contract ID)
- Timestamp

**5\. Budget Balance (Derived)**

System-calculated:

- Allocated
- Reserved
- Committed
- Available

## 4.4 Budget Lifecycle

**States:**

1.  Draft
2.  Submitted
3.  Approved
4.  Active
5.  Closed

**Flow:**

Draft → Submit → Approve → Activate → Close

**4.5 Functional Requirements**

**FR-BG-001: Create Budget**

- Budget created per financial year and entity

**FR-BG-002: Define Budget Lines**

- Must include:
    - Strategic linkage
    - Department
    - Allocation amount

**FR-BG-003: Budget Approval**

- Budget must be approved before activation

**FR-BG-004: Budget Activation**

- Only active budgets can be used

**FR-BG-005: Budget Reservation (Critical)**

When a requisition is created:

- System must:
    - Check available budget
    - Reserve amount

**Logic:**

IF Available Budget ≥ Requisition Amount  
THEN Reserve  
ELSE  
BLOCK

**FR-BG-006: Budget Commitment**

When award is approved:

- Convert reservation → commitment

**FR-BG-007: Budget Release**

If:

- Requisition cancelled
- Tender cancelled

→ Reserved/committed funds must be released

**FR-BG-008: Prevent Over-Commitment (Hard Rule)**

System must block:

- Any action exceeding available budget

**FR-BG-009: Budget Reallocation**

- Allows movement of funds between lines
- Requires:
    - Approval workflow
    - Full audit

## 4.6 Validation Rules

- Budget must exist before requisition
- Budget line must match:
    - Department
    - Strategic linkage
- Amount must be positive
- Cannot exceed available balance

## 4.7 Budget Enforcement Points

| **Stage** | **Enforcement** |
| --- | --- |
| Requisition | Reservation |
| Tender Creation | Validation |
| Award | Commitment |
| Contract | Validation |
| Execution | Tracking |

## 4.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Create Budget | Budget Officer |
| Approve Budget | Finance Authority |
| Allocate Funds | Budget Officer |
| Reallocate Budget | Finance Authority |
| View Budget | All authorized roles |

## 4.9 Audit Requirements

Every budget action must log:

- User
- Action
- Amount
- Before vs after balance
- Reference document

## 4.10 Edge Cases

**1\. Partial Awards**

- Only committed amount is finalized
- Remaining reserved funds released

**2\. Multi-Line Procurement**

- One procurement can draw from multiple budget lines

**3\. Multi-Year Projects**

- Budget split across financial years

**4\. Currency Handling**

- Optional multi-currency support

## 4.11 Integration Points

**Strategic Planning Module**

- Budget lines must link to:
    - Program
    - Sub-program
    - Indicator

**Requisition Module**

- Must reference budget line

**Procurement Module**

- Must validate budget before proceeding

## 4.12 Outputs

- Budget utilization reports
- Commitment reports
- Variance analysis
- Strategy vs spend tracking

# Section 5: Purchase Requisition Module

This is one of the most critical modules in the entire system. If this is weak, everything downstream becomes reactive and uncontrolled.

## 5.1 Purpose

To formally initiate procurement demand in a controlled, auditable, and structured manner such that:

- Every procurement originates from a legitimate, approved need
- Every request is aligned to:
    - Strategy
    - Budget
- Budget commitment begins at this stage
- Demand is standardized across the organization

## 5.2 Role in System Hierarchy

Strategic Plan  
↓  
Budget Allocation  
↓  
Purchase Requisition ← (STARTS HERE)  
↓  
Procurement Plan  
↓  
Tender → Award → Contract

## 5.3 Core Design Principles

**1\. Mandatory Entry Point**

- All procurement must originate from a requisition
- No bypass (except controlled emergency flow)

**2\. Budget Reservation Trigger**

- Requisition = **first financial commitment event**

**3\. Strategic Enforcement Point**

- Must link to:
    - Program
    - Sub-program
    - Output indicator
    - Performance target

**4\. Structured Demand**

- No vague descriptions
- Standardized item/service definitions

## 5.4 Core Entities

**1\. Purchase Requisition**

**Fields:**

- Requisition ID
- Entity
- Department
- Requesting User
- Date Created
- Status

**Strategic Fields (Mandatory):**

- Strategic Objective Code
- Program
- Sub-Program
- Output Indicator
- Performance Target

**Budget Fields:**

- Budget Line
- Available Budget (system derived)
- Requested Amount

**2\. Requisition Line Item**

(Child table)

**Fields:**

- Item / Service Description
- Quantity
- Unit of Measure
- Estimated Unit Cost
- Total Cost

**3\. Justification & Specification**

- Business justification
- Technical specifications
- Required delivery timeline

## 5.5 Workflow (Configurable with Guardrails)

**Standard Flow (Example):**

Draft → Submit → HOD Approval → Finance Validation → Procurement Acceptance

**States:**

1.  Draft
2.  Submitted
3.  Under Review
4.  Approved
5.  Rejected
6.  Converted to Plan

## 5.6 Functional Requirements

**FR-RQ-001: Create Requisition**

- Only authorized users can create
- Must include:
    - Strategic linkage
    - Budget line
    - Line items

**FR-RQ-002: Budget Validation (Hard Enforcement)**

On submission:

IF Available Budget ≥ Requested Amount  
THEN Reserve Budget  
ELSE  
BLOCK Submission

**FR-RQ-003: Strategic Validation**

System must block if:

- No strategic linkage provided
- Invalid mapping to program/sub-program

**FR-RQ-004: Approval Workflow**

- Configurable per entity
- Must include:
    - At least one approval step

**FR-RQ-005: Conversion to Procurement Plan**

- Approved requisitions become:
    - Plan items
- Must retain linkage

**FR-RQ-006: Budget Reservation**

On approval:

- Create budget ledger entry:
    - Type: Reservation
    - Amount: Requested amount

**FR-RQ-007: Modification Rules**

- Draft → editable
- Submitted → restricted
- Approved → locked

**FR-RQ-008: Cancellation**

- Cancelling requisition:
    - Releases reserved budget

## 5.7 Validation Rules

- Amount must be > 0
- Budget must exist and be active
- Strategic fields must be valid
- Line items must sum to total

## 5.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Create Requisition | Department User |
| Approve | HOD / Configured Roles |
| Budget Validation | Finance Role |
| Accept into Plan | Procurement Officer |

## 5.9 Audit Requirements

System must log:

- Creation
- Submission
- Approval/rejection
- Budget reservation
- Changes

## 5.10 Edge Cases

**1\. Partial Approval**

- Allow reduction of requested amount
- Adjust reservation accordingly

**2\. Multi-Department Requisition**

- Single requisition may include multiple departments (optional config)

**3\. Emergency Requisition**

- Can bypass standard workflow
- Must:
    - Require justification
    - Trigger audit flags

**4\. Requisition Expiry**

- If not processed within timeframe:
    - Auto-expire
    - Release budget

## 5.11 Outputs

- Approved requisition dataset
- Budget commitment record
- Input to procurement planning

## 5.12 Integration Points

**Strategic Module**

- Pulls:
    - Program
    - Indicators

**Budget Module**

- Reserves funds

**Procurement Planning**

- Converts to plan items

## 5.13 Implementation Mapping Note

Now we ground this in reality.

**Likely ERPNext Reuse**

- Some concepts align with:
    - Material Request (but insufficient as-is)
    - Budgeting structures (partial reuse)

**Gaps (Critical)**

ERPNext does NOT natively support:

- Strategic linkage hierarchy (Program → Indicator → Target)
- Hard budget reservation at requisition stage (in procurement context)
- Public procurement compliance workflows
- Multi-layer approval with committee structures

**Recommended Approach**

**1\. Create Custom DocType:**

- Purchase Requisition

**2\. Child Table:**

- Purchase Requisition Item

**3\. Extend:**

- Budget logic via custom service (not purely ERPNext standard budget)

**4\. Use Frappe Workflow Engine:**

- For approval chains

**5\. Custom Logic Required:**

- Budget reservation (server-side)
- Strategic validation
- Conversion to procurement plan

**Open Technical Questions (We’ll Resolve Later)**

- Should we reuse ERPNext “Material Request” or replace it entirely?
- How to integrate with ERPNext Budget vs custom commitment ledger?
- How to enforce entity isolation cleanly in multi-tenant setup?

# Section 6: Procurement Planning Module

Planning is **not an isolated spreadsheet exercise**. In KenTender, procurement planning is the controlled consolidation of approved demand into an executable procurement program.

## 6.1 Purpose

To transform approved and budget-backed requisitions into a structured procurement plan that:

- organizes procurement activities over a defined period
- enforces readiness before tendering
- aligns execution timelines to budget and strategic priorities
- provides an auditable bridge between demand and procurement action

## 6.2 Position in System Lifecycle

Strategic Planning  
↓  
Budget Allocation  
↓  
Purchase Requisition  
↓  
Procurement Planning  
↓  
Tender Preparation & Publishing  
↓  
Bid Management → Evaluation → Award → Contract

## 6.3 Core Design Principles

**1\. Planning is Derived, Not Invented**

Procurement plan items should primarily originate from approved requisitions, not freehand entries.

**2\. No Tender Outside Plan**

A tender cannot be created unless it is linked to an approved procurement plan item, except through a controlled emergency workflow.

**3\. Plan is a Scheduling and Structuring Layer**

The procurement plan does not replace requisitions or budgets. It consolidates them into a managed execution schedule.

**4\. Planning Must Preserve Traceability**

Every plan item must retain linkage to:

- originating requisition
- budget line
- strategic structure

**5\. Plans Are Versioned**

Approved plans are locked. Changes happen through formal revision.

## 6.4 Core Entities

**1\. Procurement Plan**

Represents the plan for an entity for a given planning period.

**Fields**

- Procurement Plan ID
- Entity
- Financial Year / Planning Period
- Plan Version
- Status
- Created By
- Created Date
- Submitted Date
- Approved Date
- Remarks

**2\. Procurement Plan Item**

Represents an individual procurement activity.

**Fields**

- Plan Item ID
- Parent Procurement Plan
- Origin Type
    - Requisition-derived
    - Manual strategic insertion
    - Revision-created
- Linked Requisition(s)
- Department
- Procurement Title
- Procurement Category
    - Goods
    - Works
    - Services
    - Consulting Services
- Procurement Method
- Estimated Cost
- Budget Line
- Strategic Objective Code
- Program
- Sub-Program
- Output Indicator
- Performance Target
- Planned Start Date
- Planned Tender Publish Date
- Planned Award Date
- Planned Contract Start Date
- Planned Completion Date
- Priority Level
- Status

## 3\. Plan Revision Record

Tracks approved changes to an already approved plan.

**Fields**

- Revision ID
- Plan Version From
- Plan Version To
- Revision Reason
- Requested By
- Approved By
- Revision Date

## 6.5 Workflow

**Procurement Plan Lifecycle**

1.  Draft
2.  Submitted
3.  Under Review
4.  Approved
5.  Active
6.  Revised
7.  Archived

**Typical Flow**

Draft → Submit → Review → Approve → Active  
↓  
Reject

Approved plans become active for execution. Any change after approval creates a revision pathway.

## 6.6 Functional Requirements

**FR-PP-001: Create Procurement Plan**

The system must allow authorized users to create a procurement plan for a specific entity and planning period.

Rules:

- only one active plan per entity per planning period unless multi-version mode is enabled
- plan must be associated with a valid budget period

**FR-PP-002: Pull Approved Requisitions into Plan**

The system must allow approved requisitions to be selected and converted into procurement plan items.

Rules:

- only approved requisitions may be pulled
- requisitions already fully planned cannot be duplicated unless split planning is allowed by configuration
- strategic and budget linkages must be preserved automatically

**FR-PP-003: Manual Plan Item Creation**

The system may allow manually created plan items only for authorized roles and only under controlled conditions.

Use cases:

- centrally planned procurements
- framework procurements
- statutory recurring procurements
- strategic procurements not initiated through department requisitions yet

Rules:

- manual entries must still include full strategic and budget linkage
- manual entries must be tagged as non-requisition-originated
- justification is mandatory

**FR-PP-004: Consolidation of Similar Demand**

The system may support consolidation of multiple approved requisitions into a single procurement plan item where appropriate.

Examples:

- multiple departments requesting the same office supplies
- recurring services aggregated into a single solicitation

Rules:

- consolidated item must retain references to all source requisitions
- total value must equal the sum of linked approved demand unless adjusted through approved planning logic
- audit trail must preserve source-level detail

**FR-PP-005: Procurement Method Suggestion**

The system must suggest or validate the procurement method based on:

- procurement category
- estimated cost
- jurisdiction rules
- entity-specific configurations where allowed

Rules:

- the Kenya compliance layer may enforce method thresholds and conditions
- a user may not select an invalid method

**FR-PP-006: Planning Timeline Definition**

Each plan item must include planned dates for major milestones.

Minimum milestones:

- planned procurement initiation date
- planned solicitation publication date
- planned award date
- planned contract start date
- planned completion date

Rules:

- dates must be sequentially valid
- dates must fall within the permissible planning horizon unless multi-year mode is enabled

**FR-PP-007: Submission for Approval**

The system must prevent submission of a procurement plan if:

- required fields are missing
- no plan items exist
- plan item budget links are invalid
- strategic linkages are invalid
- estimated values exceed reserved or allocated control rules

**FR-PP-008: Approval Workflow**

The plan approval workflow must be configurable by entity, with mandatory guardrails.

Possible approvers:

- Planning Officer
- Head of Procurement
- Planning Authority
- Finance Authority
- Accounting Officer where required

Rules:

- at least one formal approval step is required
- approval actions must be attributable to named users and roles

**FR-PP-009: Plan Locking**

Once approved, the plan becomes locked for normal editing.

Rules:

- direct edits to active plan items are prohibited
- changes require formal revision
- revision must produce a new plan version or revision log according to configuration

**FR-PP-010: Plan-to-Tender Control**

A tender record may only be created from an approved and active procurement plan item.

Rules:

- no orphan tenders
- one plan item may produce one or more tenders only if split procurement is allowed and properly justified
- one tender may aggregate multiple plan items only if permitted and auditable

**FR-PP-011: Plan Performance Monitoring**

The system must track execution status of each plan item.

Minimum statuses:

- Planned
- In Preparation
- Tender Published
- Under Evaluation
- Awarded
- Contracted
- In Execution
- Completed
- Cancelled

This enables plan versus actual monitoring.

## 6.7 Validation Rules

- every plan item must have valid budget linkage
- every plan item must have valid strategic linkage
- estimated cost must be greater than zero
- procurement method must be valid for the category and thresholds
- milestone dates must follow a logical sequence
- duplicate plan items should be flagged based on configurable anti-fragmentation rules
- a plan item cannot be activated if its source requisition is cancelled or invalidated

**6.8 Anti-Fragmentation Controls**

This is important and should be explicit.

The system must detect possible splitting of demand intended to avoid threshold controls.

**Detection rules may include:**

- same department
- same category
- similar item descriptions
- same budget line
- close time window
- aggregate value exceeding threshold while split items remain below threshold individually

**System behavior:**

- hard block or soft flag based on rule severity and configuration
- mandatory justification if proceeding under an approved exception path
- audit alert generation for oversight users

## 6.9 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Create procurement plan | Planning Officer / Procurement Officer |
| Add plan items | Planning Officer / Procurement Officer |
| Pull requisitions into plan | Planning Officer / Procurement Officer |
| Submit plan | Authorized planning role |
| Approve plan | Configured approvers |
| Revise approved plan | Restricted authorized roles |
| View all entity plans | Oversight / authorized entity roles |

## 6.10 Audit Requirements

The system must log:

- plan creation
- plan item addition
- linkage to source requisitions
- estimated value changes
- procurement method changes
- submission and approval actions
- revision actions
- plan-to-tender conversions

Each log must capture:

- actor
- role
- timestamp
- before value
- after value
- reason/comment where applicable

## 6.11 Edge Cases

**1\. Multi-Year Procurements**

A plan item may span multiple financial years.

Requirements:

- multi-year flag
- planned yearly budget linkage or phased funding references
- control to prevent tendering beyond available authorized funding structure

**2\. Centralized or Shared Procurement**

One entity may plan procurement for use by multiple departments or subordinate units.

Requirements:

- beneficiary entities/departments list
- cost distribution metadata
- visibility rules by participating unit

**3\. Requisition Consolidation with Value Change**

Planning review may adjust the consolidated procurement value.

Requirements:

- original source demand preserved
- delta justified and approved
- budget implications validated

**4\. Cancelled Plan Items**

Approved plan items may later be cancelled.

Requirements:

- cancellation reason mandatory
- linked downstream records checked before cancellation
- related reservations or planning markers reconciled

**5\. Emergency Procurement Outside Normal Planning**

Emergency items may bypass the standard planning sequence only through a controlled exception.

Requirements:

- emergency classification
- legal basis / justification
- separate approval path
- audit flag
- mandatory post-facto reporting

## 6.12 Outputs

The module must produce:

- approved procurement plan
- plan item register
- plan revision history
- plan vs execution dashboard
- anti-fragmentation alerts
- procurement pipeline forecast

## 6.13 Reporting Requirements

Minimum reports:

- annual procurement plan by entity
- procurement plan by department
- procurement plan by program / sub-program
- plan vs actual execution
- plan items by procurement method
- delayed plan items
- fragmented demand risk report
- budget-aligned procurement plan report

## 6.14 Integration Points

**With Strategic Planning Module**

Must inherit and validate:

- strategic objective code
- program
- sub-program
- output indicator
- performance target

**With Budget Module**

Must validate:

- budget line validity
- reserved / available budget posture
- reallocation effects where applicable

**With Requisition Module**

Must:

- pull approved requisitions
- preserve source references
- update requisition planning status

**With Tender Management Module**

Must:

- serve as mandatory upstream source for tender creation
- expose plan item metadata to tender setup

## 6.15 Kenya Compliance Overlay

For the Kenya implementation layer, the system should support rules such as:

- procurement must originate from an approved procurement plan except lawful exceptions
- procurement method selection must comply with regulatory thresholds and conditions
- annual planning and revision records must be auditable
- fragmentation controls must support oversight and audit use cases

These rules should be implemented through the compliance layer, not hardwired into the core in a way that prevents future jurisdictional reuse.

## 6.16 Implementation Mapping Note

**Likely Reuse Candidates**

- ERPNext may provide reusable structures for:
    - Company / Department
    - fiscal year handling
    - projects / cost centers in related contexts
    - standard workflow engine basics

**Likely Custom Requirements**

A custom Procurement Plan DocType will almost certainly be needed.

Likely custom DocTypes:

- Procurement Plan
- Procurement Plan Item
- Procurement Plan Revision

**Likely Extensions**

- linkage fields to strategic hierarchy
- linkage fields to budget line and requisition
- anti-fragmentation detection logic
- plan-to-tender conversion actions
- execution tracking statuses beyond standard ERPNext purchasing flow

**Technical Notes**

- standard ERPNext procurement docs are not sufficient for public-sector planning controls
- Frappe workflows can handle approvals, but revision/versioning may need custom logic
- reporting will likely require custom Script Reports / Query Reports and dashboard cards
- anti-fragmentation checks should likely run server-side on save/submit and via scheduled analytics jobs

**Open Technical Questions**

- whether plan execution status should be derived live from downstream records or persisted as synchronized status
- whether one tender can legally and operationally map to multiple plan items in the first release
- how far to reuse ERPNext purchasing objects versus building a distinct public procurement flow

# Section 7: Supplier Management Module

This is the next foundation block. If supplier management is weak, procurement becomes vulnerable, exclusionary, and hard to audit.

## 7.1 Purpose

To provide a controlled supplier lifecycle covering:

- supplier registration
- qualification and categorization
- verification and due diligence
- eligibility management
- participation readiness across procurement opportunities

The module must support public-sector fairness, transparency, inclusion, and compliance while maintaining high-quality supplier master data.

## 7.2 Design Principles

**1\. One Supplier, Many Opportunities**

A supplier should register once and participate across eligible procurements, subject to entity and category rules.

**2\. Eligibility Must Be Verifiable**

Registration alone does not equal eligibility. The system must distinguish:

- registered
- verified
- qualified
- suspended / debarred / inactive

**3\. Inclusion Must Be Explicitly Supported**

The module must support reserved and preference schemes, including AGPO-style categorization where applicable.

**4\. Supplier Data Is a Compliance Asset**

Supplier records are not just contacts. They are compliance, eligibility, and risk records.

## 7.3 Core Entities

**1\. Supplier Profile**

Primary legal and operational record for a vendor.

**Fields**

- Supplier ID
- Legal Name
- Trading Name
- Registration Number
- Tax Identification Number
- Entity Type
- Country
- Physical Address
- Postal Address
- Contact Person
- Email
- Phone
- Status

**2\. Supplier Category Assignment**

Defines supplier participation areas.

**Fields**

- Assignment ID
- Supplier
- Category
- Subcategory
- Effective Date
- Expiry Date
- Status

**3\. Supplier Compliance Record**

Tracks documentary and statutory compliance.

**Fields**

- Compliance Record ID
- Supplier
- Compliance Type
    - tax compliance
    - registration certificate
    - business permit
    - professional license
    - beneficial ownership declaration
    - AGPO certificate
    - other statutory document
- Document Reference
- Issue Date
- Expiry Date
- Verification Status

**4\. Supplier Verification Record**

Tracks due diligence and verification actions.

**Fields**

- Verification ID
- Supplier
- Verification Type
- Performed By
- Verification Date
- Result
- Notes

**5\. Supplier Eligibility Status**

Derived or explicit record showing procurement readiness.

Possible values:

- Draft
- Registered
- Pending Verification
- Verified
- Qualified
- Suspended
- Debarred
- Expired
- Inactive

**6\. Supplier Risk / Integrity Flags**

Tracks concerns requiring oversight.

Examples:

- duplicate identity indicators
- sanctions hit
- debarment match
- document mismatch
- conflict-of-interest declaration issue
- poor performance history

## 7.4 Supplier Lifecycle

Draft Registration → Submitted → Under Review → Verified → Qualified  
↓  
Rejected / Returned

Ongoing states:

- suspended
- debarred
- expired
- inactive

## 7.5 Functional Requirements

**FR-SM-001: Supplier Self-Registration**

The system must allow suppliers to self-register through a public-facing or supplier-facing portal.

Minimum requirements:

- legal identity details
- contact details
- category selections
- statutory documents
- declarations and consents

**FR-SM-002: Internal Supplier Creation**

Authorized users may create supplier records internally where policy permits.

Use cases:

- migration of legacy suppliers
- framework suppliers
- emergency circumstances with controlled onboarding

**FR-SM-003: Category-Based Registration**

The system must support supplier categorization by:

- procurement category
- sector
- specialization
- reserved group category where applicable

**FR-SM-004: Document Submission and Expiry Tracking**

The system must store and track validity periods for supplier compliance documents.

Rules:

- expired mandatory documents must affect eligibility
- renewal reminders should be generated before expiry
- version history of documents should be preserved

**FR-SM-005: Verification Workflow**

The system must support verification workflows for supplier data and compliance documents.

Possible verification actions:

- validate registration number
- validate tax compliance
- verify business license
- verify AGPO / reserved status
- verify bank details if applicable later
- verify beneficial ownership declarations

**FR-SM-006: Eligibility Determination**

The system must determine whether a supplier is eligible to participate in a procurement opportunity based on:

- active status
- valid category assignment
- valid mandatory compliance documents
- no suspension or debarment flag
- any opportunity-specific requirements

**FR-SM-007: Suspension and Debarment Handling**

Authorized roles must be able to suspend or mark suppliers as debarred based on lawful processes.

Rules:

- reason mandatory
- effective dates mandatory
- participation in new tenders must be blocked while status is active
- full audit trail required

**FR-SM-008: Supplier Profile Maintenance**

Suppliers must be able to update selected fields in their profiles, subject to review rules.

Rules:

- critical legal identity changes may require re-verification
- historical values should be retained

**FR-SM-009: Duplicate Detection**

The system must detect possible duplicate suppliers using:

- registration number
- tax number
- email / phone similarity
- legal name similarity
- beneficial ownership overlaps where data exists

**FR-SM-010: Participation Readiness Check**

Before bid submission, the system must validate that the supplier is eligible for that tender.

## 7.6 Validation Rules

- required identity fields must be complete
- registration number and tax identifier uniqueness must be enforced according to legal context
- mandatory documents must be valid and unexpired
- reserved category claims must have supporting evidence
- suppliers with active suspension or debarment cannot proceed to bid submission

## 7.7 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Self-register | Supplier user |
| Review supplier registration | Supplier Management Officer / Procurement role |
| Verify documents | Authorized verification roles |
| Approve qualification | Authorized procurement/compliance roles |
| Suspend / reactivate supplier | Restricted authority |
| View supplier risk flags | Oversight / authorized internal roles |

## 7.8 Audit Requirements

The system must log:

- registrations
- document uploads and replacements
- verification outcomes
- eligibility status changes
- suspension / debarment actions
- category changes
- supplier profile changes

## 7.9 Edge Cases

**1\. Expired Compliance During Active Tender**

System behavior must be defined for whether expiry after submission affects evaluation eligibility, according to jurisdiction rules.

**2\. Consortium / Joint Venture Participation**

The system should support linked supplier structures for joint bidding, with shared or member-specific compliance requirements.

**3\. Foreign Suppliers**

The system should support foreign supplier registration with alternate compliance requirements where allowed.

**4\. AGPO / Reserved Group Expiry**

If reserved status documentation expires, eligibility for reserved opportunities must be removed until renewed.

**7.10 Outputs**

- supplier master register
- verified supplier register
- category-qualified supplier lists
- suspended / debarred supplier list
- expiring compliance dashboard
- supplier inclusion and diversity reports

## 7.11 Integration Points

**With Tender Module**

- eligibility checks
- tender access control
- category qualification filtering

**With Evaluation Module**

- compliance status visibility at permitted stages
- supplier declarations and due diligence outputs

**With Reporting Module**

- participation rates
- category-based competition analytics
- inclusion metrics

## 7.12 Implementation Mapping Note (Frappe / ERPNext)

**Likely Reuse Candidates**

- ERPNext Supplier as a base master record may be reusable in part

**Likely Custom Extensions**

Standard ERPNext Supplier is not enough for public procurement.

Expected custom extensions / related DocTypes:

- supplier compliance documents
- supplier category assignments
- supplier verification records
- supplier risk flags
- reserved category / AGPO profile
- debarment / suspension records

**Recommended Direction**

- reuse ERPNext Supplier for core identity where practical
- extend through a custom app for procurement-specific compliance and eligibility logic
- do not rely on vanilla supplier status fields for legal eligibility states

**Open Technical Questions**

- whether supplier-facing portal should be built fully in Frappe portal/web forms or split into a separate frontend
- whether qualification should be continuous or tied to category-specific approval cycles
- how external verification APIs, if any, will be integrated in later phases

# Section 8: Tender Management Module

This module governs the creation, structuring, publication, and control of procurement opportunities.

## 8.1 Purpose

To define and manage procurement solicitations (tenders) such that:

- every tender is compliant, structured, and auditable
- suppliers receive clear, standardized requirements
- procurement methods are enforced correctly
- the process is transparent and controlled

## 8.2 Position in System Lifecycle

Procurement Plan  
↓  
Tender Creation  
↓  
Tender Publication  
↓  
Bid Submission  
↓  
Bid Opening → Evaluation → Award

## 8.3 Core Design Principles

**1\. No Orphan Tenders**

- Every tender must originate from an approved procurement plan item

**2\. Structured Tendering**

- No free-text-only tenders
- Must include:
    - requirements
    - criteria
    - timelines
    - documents

**3\. Method Enforcement**

- Procurement method must comply with:
    - thresholds
    - category
    - jurisdiction rules

**4\. Controlled Visibility**

- Suppliers only see what they are allowed to see, when they are allowed to see it

**5\. Immutable After Publication (with controlled amendments)**

- Published tenders cannot be silently changed

## 8.4 Core Entities

**1\. Tender**

**Fields:**

- Tender ID
- Title
- Description
- Procuring Entity
- Department
- Linked Procurement Plan Item
- Procurement Category
- Procurement Method
- Estimated Value
- Budget Line

**Strategic Fields:**

- Strategic Objective Code
- Program
- Sub-Program
- Output Indicator
- Performance Target

**2\. Tender Lot (Optional)**

Supports splitting into multiple components.

**Fields:**

- Lot ID
- Tender
- Lot Name
- Description
- Estimated Value

**3\. Tender Document Package**

- Instructions to bidders
- Technical specifications
- Terms of reference
- Conditions of contract
- Pricing forms

**4\. Tender Requirement Criteria**

**Types:**

- Mandatory requirements
- Technical evaluation criteria
- Financial evaluation criteria

**5\. Tender Timeline**

- Publication Date
- Clarification Deadline
- Submission Deadline
- Opening Date

**6\. Tender Amendment**

Tracks changes post-publication.

**Fields:**

- Amendment ID
- Tender
- Change Description
- Affected Fields
- New Submission Deadline (if applicable)
- Published Date

## 8.5 Tender Lifecycle

**States:**

1.  Draft
2.  Under Review
3.  Approved
4.  Published
5.  Closed (Submission ended)
6.  Opening Scheduled
7.  Opening Completed
8.  Under Evaluation
9.  Awarded
10. Cancelled

**Flow:**

Draft → Review → Approve → Publish → Close → Open → Evaluate → Award

## 8.6 Functional Requirements

**FR-TM-001: Create Tender**

- Must originate from a procurement plan item

System must auto-populate:

- budget linkage
- strategic linkage
- estimated value

**FR-TM-002: Define Tender Structure**

Tender must include:

- scope
- specifications
- requirements
- evaluation criteria
- timelines

**FR-TM-003: Procurement Method Validation**

System must validate:

- method allowed for value
- method allowed for category

**FR-TM-004: Tender Approval Workflow**

- Must be approved before publication
- Configurable approvers

**FR-TM-005: Publish Tender**

On publication:

- tender becomes visible to eligible suppliers
- submission window opens

**FR-TM-006: Supplier Eligibility Filtering**

System must restrict access based on:

- supplier category
- compliance status
- eligibility rules

**FR-TM-007: Clarifications Handling**

- Suppliers may submit clarification requests
- Responses must be:
    - recorded
    - visible to all eligible participants

**FR-TM-008: Tender Amendment**

Post-publication changes must:

- create amendment record
- notify all participants
- optionally extend deadlines

**FR-TM-009: Submission Deadline Enforcement**

System must:

- automatically close submissions at deadline
- block late submissions

**FR-TM-010: Tender Cancellation**

Allowed before or after publication with:

- mandatory justification
- notification to suppliers
- audit record

## 8.7 Validation Rules

- tender must link to approved plan item
- submission deadline must be after publication
- evaluation criteria must be defined before publication
- mandatory requirements must exist
- budget must still be valid

## 8.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Create tender | Procurement Officer |
| Approve tender | Head of Procurement / Committee |
| Publish tender | Authorized procurement role |
| Amend tender | Restricted roles |
| Cancel tender | Authorized roles |
| View tender | Suppliers / Public (based on stage) |

## 8.9 Audit Requirements

System must log:

- creation
- changes
- approvals
- publication
- amendments
- cancellations

## 8.10 Edge Cases

**1\. Re-Tendering**

- cancelled tender may be re-issued
- must link to original

**2\. Multi-Lot Tender**

- evaluation per lot
- award per lot

**3\. Framework Agreements**

- special tender type
- supports multiple awards

**4\. Restricted Tender**

- only invited suppliers can view/submit

## 8.11 Outputs

- published tender notice
- tender documents
- amendment history
- supplier participation records

## 8.12 Integration Points

**Procurement Planning**

- source of tender

**Supplier Management**

- eligibility filtering

**Bid Management**

- submission intake

## 8.13 Kenya Compliance Overlay

System must support:

- method thresholds
- public disclosure requirements
- controlled amendment processes
- audit-ready tender records

## 8.14 Implementation Mapping Note

**ERPNext Reuse**

- very limited direct reuse
- standard “Request for Quotation” is insufficient

**Custom Requirements**

Custom DocTypes required:

- Tender
- Tender Lot
- Tender Document
- Tender Amendment
- Tender Criteria

**Workflow**

- Frappe Workflow engine for:
    - draft → approval → publish

**Key Custom Logic**

- supplier eligibility filtering
- submission deadline enforcement
- amendment tracking
- plan linkage enforcement

**Likely Architecture**

- Tender module in custom app (kentender_procurement)
- Supplier portal integration required

**Open Questions**

- document storage strategy (Frappe vs external)
- handling large tender documents
- version control approach

# Section 9: Bid Management & Submission Module

## 9.1 Purpose

To securely receive, store, protect, and manage supplier bids such that:

- bids remain confidential until official opening
- submissions are tamper-proof
- deadlines are strictly enforced
- full auditability exists for every action
- fairness and integrity of the process are guaranteed

## 9.2 Position in Lifecycle

Tender Published  
↓  
Bid Submission Window Open  
↓  
Supplier Submits Bid  
↓  
Submission Deadline  
↓  
Bid Opening  
↓  
Evaluation

## 9.3 Core Design Principles

**1\. Confidentiality Before Opening**

- No user—including admins—can access bid contents before opening

**2\. Integrity & Non-Repudiation**

- Submitted bids cannot be altered
- Supplier actions must be attributable

**3\. Deadline Enforcement**

- Late submissions are impossible

**4\. Equal Treatment**

- All bidders operate under identical conditions

**5\. Full Audit Trail**

- Every submission event must be logged

## 9.4 Core Entities

**1\. Bid Submission**

**Fields:**

- Bid ID
- Tender
- Supplier
- Submission Timestamp
- Status

**2\. Bid Envelope Structure**

Supports structured submissions.

**Sections:**

- Technical Proposal
- Financial Proposal
- Mandatory Documents

**3\. Bid Document**

- Document ID
- Type
- File Reference
- Upload Timestamp

**4\. Bid Security Metadata**

- Encryption Status
- Hash Value (for integrity)
- Submission Token

## 9.5 Bid Lifecycle

**States:**

1.  Draft
2.  Submitted
3.  Locked
4.  Opened
5.  Under Evaluation
6.  Withdrawn (before deadline only)
7.  Disqualified

**Flow:**

Draft → Submit → Locked → Open → Evaluate

## 9.6 Functional Requirements

**FR-BM-001: Supplier Bid Creation**

- Only eligible suppliers can submit
- Supplier must be:
    - registered
    - compliant
    - qualified

**FR-BM-002: Bid Structure Enforcement**

System must enforce required sections:

- mandatory documents
- technical proposal
- financial proposal

**FR-BM-003: Secure Submission**

On submission:

- bid is:
    - encrypted (logical or system-controlled protection)
    - timestamped
    - hashed

**FR-BM-004: Submission Deadline Enforcement**

System must:

IF Current Time > Deadline  
THEN BLOCK submission

**FR-BM-005: Bid Locking**

After submission:

- bid becomes immutable
- no edits allowed

**FR-BM-006: Withdrawal (Before Deadline Only)**

- supplier may withdraw bid
- system must:
    - log withdrawal
    - allow resubmission before deadline

**FR-BM-007: Multi-Part Submission (Optional)**

- allow multiple uploads until submission
- final submission locks all parts

**FR-BM-008: Submission Receipt**

System must generate:

- digital receipt
- submission reference
- timestamp

## 9.7 Validation Rules

- supplier must be eligible
- all mandatory documents must be present
- file formats must be allowed
- submission must occur before deadline
- financial and technical sections must be complete

## 9.8 Security Requirements (Critical)

**1\. Access Control**

Before opening:

- NO internal user can access:
    - bid documents
    - financial values

**2\. Data Protection**

- bids must be:
    - encrypted at rest OR
    - protected via strict access controls

**3\. Integrity Verification**

- system must store:
    - file hash
- detect tampering

**4\. Audit Logging**

Log:

- upload
- submission
- withdrawal
- access attempts

## 9.9 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Submit bid | Supplier |
| Withdraw bid | Supplier (before deadline) |
| View bids | NONE (before opening) |
| Access after opening | Evaluation roles only |

## 9.10 Audit Requirements

System must log:

- submission timestamp
- supplier identity
- IP address (optional)
- document uploads
- withdrawal events
- access attempts

## 9.11 Edge Cases

**1\. Network Failure During Submission**

- allow retry until deadline
- partial submissions not accepted

**2\. Large File Uploads**

- support chunked uploads
- ensure integrity

**3\. Duplicate Submissions**

- only latest valid submission counts

**4\. Consortium Bids**

- support multiple suppliers per bid

## 9.12 Outputs

- bid register (locked before opening)
- submission audit logs
- receipt records

## 9.13 Integration Points

**Tender Module**

- defines submission structure

**Supplier Module**

- validates eligibility

**Evaluation Module**

- consumes opened bids

## 9.14 Kenya Compliance Overlay

System must support:

- strict confidentiality before opening
- formal opening procedures
- auditable submission records

## 9.15 Implementation Mapping Note (Frappe / ERPNext)

**ERPNext Limitations**

ERPNext does NOT support:

- secure bid handling
- sealed submissions
- procurement-grade confidentiality

This must be custom-built.

**Custom Components Required**

- Bid Submission DocType
- Bid Document storage layer
- secure submission service

**Security Design (Important)**

Options:

**Option 1 — Application-Level Protection**

- strict role access
- hidden documents

**Option 2 — Encryption Layer (Better)**

- encrypt bid documents
- decrypt only at opening

Recommended for high-integrity deployments

**Workflow**

- submission handled via portal
- locking enforced server-side
- opening event triggers access

**Technical Notes**

- use Frappe File DocType carefully
- consider external storage for large files
- ensure audit logs are immutable

**Open Questions**

- encryption strategy (must decide later)
- digital signature requirements
- legal admissibility requirements

# Section 10: Bid Opening Module

## 10.1 Purpose

To formally open submitted bids in a controlled, auditable, and legally compliant manner such that:

- no bid is accessed before the official opening
- all bids are opened fairly and simultaneously
- an official opening record is generated
- the process is transparent, traceable, and defensible

## 10.2 Position in Lifecycle

Bid Submission Closed  
↓  
Bid Opening Session Created  
↓  
Opening Event Executed  
↓  
Bids Become Visible  
↓  
Evaluation Begins

## 10.3 Core Design Principles

**1\. Controlled Access Moment**

- Bids transition from sealed → visible only during opening

**2\. Simultaneity**

- All bids are opened at once, not selectively

**3\. Transparency**

- Opening must produce:
    - a formal register
    - visible key details

**4\. Non-Repudiation**

- No one can claim:
    - a bid was added/removed
    - a bid was altered

**5\. Audit Integrity**

- Opening event must be fully logged

## 10.4 Core Entities

**1\. Bid Opening Session**

**Fields:**

- Opening Session ID
- Tender
- Scheduled Opening Date/Time
- Actual Opening Date/Time
- Location (Physical / Virtual)
- Status

**2\. Opening Committee**

- Committee ID
- Members
- Chairperson

**3\. Opening Record (Critical Output)**

This is the official record.

**Fields:**

- Record ID
- Tender
- Opening Session
- List of Bids Opened
- Summary of Each Bid:
    - Supplier Name
    - Bid Price (if applicable)
    - Bid Security presence
    - Submission timestamp

**4\. Opening Log**

- Action logs during opening
- System-generated

## 10.5 Opening Lifecycle

**States:**

1.  Scheduled
2.  Ready
3.  In Progress
4.  Completed
5.  Locked

**Flow:**

Scheduled → Ready → Open → Completed → Locked

## 10.6 Functional Requirements

**FR-BO-001: Schedule Opening Session**

- Automatically scheduled based on submission deadline
- Can be adjusted (with restrictions)

**FR-BO-002: Opening Preconditions**

System must block opening if:

- submission deadline not reached
- tender not in closed state
- required approvals not completed

**FR-BO-003: Controlled Opening Trigger**

Opening must require:

- authorized role
- explicit action (not automatic)

**FR-BO-004: Simultaneous Bid Access**

On opening:

- all valid bids become accessible
- system records:
    - opening timestamp
    - all bids included

**FR-BO-005: Opening Register Generation**

System must automatically generate:

- list of all submitted bids
- key attributes per bid

**FR-BO-006: Opening Record Finalization**

After opening:

- record becomes immutable
- digitally stored

**FR-BO-007: Late Bids Handling**

System must:

- exclude late submissions automatically
- log rejected attempts

**FR-BO-008: Opening Visibility**

System must define what becomes visible:

- supplier name
- submission timestamp
- bid price (configurable depending on method)

**FR-BO-009: Opening Committee Participation**

System must:

- record who attended
- record who initiated opening

## 10.7 Validation Rules

- opening cannot occur before deadline
- all bids must have valid submission status
- no partial opening allowed
- opening must include all valid bids

## 10.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Schedule opening | Procurement Officer |
| Initiate opening | Authorized committee role |
| View opening record | Authorized roles / public (partial) |

## 10.9 Audit Requirements (Critical)

System must log:

- opening trigger
- users present
- exact timestamp
- bids included
- system actions

## 10.10 Edge Cases

**1\. No Bids Submitted**

- opening still occurs
- record shows zero bids

**2\. Single Bid**

- still processed normally

**3\. System Failure During Opening**

- must support:
    - retry with integrity preserved
    - no duplication

**4\. Re-Opening (Not Allowed)**

- once opened → cannot revert

## 10.11 Outputs

- official bid opening register
- opening audit log
- bid list for evaluation

## 10.12 Integration Points

**Bid Module**

- source of submissions

**Evaluation Module**

- receives opened bids

**Transparency Portal**

- publishes opening summary (optional)

## 10.13 Kenya Compliance Overlay

System must support:

- formal opening procedures
- documented opening register
- audit-ready logs

## 10.14 Implementation Mapping Note (Frappe / ERPNext)

**ERPNext Gap**

No native concept of:

- bid opening session
- sealed → opened transition

**Custom Components Required**

- Bid Opening Session DocType
- Opening Record DocType
- Opening Committee DocType

**Key Logic**

- opening event triggers:
    - access unlock
    - register generation

**Workflow**

- scheduled → triggered manually
- locking after completion

**Technical Notes**

- ensure atomic transaction during opening
- no partial state allowed
- ensure concurrency safety

**Security Considerations**

- only authorized users can trigger
- ensure no pre-opening leaks

**Open Questions**

- whether opening should support:
    - public livestream integration
    - digital witness signatures

# Section 11: Evaluation Module

## 11.1 Purpose

To evaluate opened bids in a structured, transparent, and auditable manner such that:

- evaluation follows predefined criteria (no shifting goalposts)
- evaluators act independently but within controlled processes
- scoring is traceable and justifiable
- evaluation outputs are defensible under audit or legal challenge

## 11.2 Position in Lifecycle

Bid Opening Completed  
↓  
Evaluation Committee Activated  
↓  
Technical Evaluation  
↓  
Financial Evaluation  
↓  
Combined Scoring / Ranking  
↓  
Evaluation Report  
↓  
Award Recommendation

## 11.3 Core Design Principles

**1\. Criteria Must Be Locked Before Opening**

- No modification of evaluation criteria after tender publication

**2\. Separation of Evaluation Phases**

- Technical and financial evaluation must be clearly separated (where applicable)

**3\. Independent Scoring with Controlled Aggregation**

- Evaluators score individually
- System aggregates scores

**4\. No Pre-Opening Visibility**

- Evaluators cannot access bids before opening

**5\. Full Traceability**

- Every score, comment, and decision must be recorded

## 11.4 Core Entities

**1\. Evaluation Session**

**Fields:**

- Evaluation ID
- Tender
- Start Date
- End Date
- Status

**2\. Evaluation Committee**

- Committee ID
- Members
- Chairperson

**3\. Evaluation Criteria**

**Types:**

- Mandatory (Pass/Fail)
- Technical (Scored)
- Financial (Formula-based)

**4\. Evaluator Score Record**

**Fields:**

- Evaluator
- Bid
- Criteria
- Score
- Comments

**5\. Aggregated Evaluation Result**

- Bid
- Total Technical Score
- Total Financial Score
- Combined Score
- Ranking

**6\. Evaluation Report**

- Summary of process
- Scores
- Justifications
- Recommended award

## 11.5 Evaluation Lifecycle

**States:**

1.  Not Started
2.  In Progress
3.  Technical Completed
4.  Financial Completed
5.  Finalized
6.  Submitted

## 11.6 Functional Requirements

**FR-EV-001: Initialize Evaluation**

- Automatically triggered after opening
- Assign evaluation committee

**FR-EV-002: Criteria Enforcement**

System must:

- load criteria defined in tender
- prevent modification

**FR-EV-003: Mandatory Requirement Check**

- pass/fail stage
- disqualify non-compliant bids

**FR-EV-004: Technical Evaluation**

- evaluators score independently
- system records scores

**FR-EV-005: Financial Evaluation**

- based on predefined formulas
- system calculates automatically

**FR-EV-006: Score Aggregation**

System must:

- aggregate evaluator scores
- calculate final ranking

**FR-EV-007: Conflict of Interest Declaration**

Evaluators must:

- declare conflicts before accessing bids

**FR-EV-008: Evaluation Report Generation**

System must generate:

- full evaluation report
- audit-ready

**FR-EV-009: Recommendation Submission**

- evaluation committee submits recommendation
- moves to approval stage

## 11.7 Validation Rules

- criteria cannot be changed
- evaluators cannot edit others’ scores
- all required evaluations must be completed
- disqualified bids cannot proceed

## 11.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Perform evaluation | Committee Members |
| Submit report | Committee Chair |
| View results | Restricted roles |

## 11.9 Audit Requirements

System must log:

- scoring actions
- evaluator identity
- timestamps
- comments
- report generation

## 11.10 Edge Cases

**1\. Tie Scores**

- predefined tie-breaking rules

**2\. Evaluator Absence**

- replacement mechanism

**3\. Re-Evaluation**

- controlled restart with audit

**4\. Partial Completion**

- cannot finalize without all inputs

## 11.11 Outputs

- evaluation scores
- ranking
- evaluation report
- award recommendation

## 11.12 Integration Points

**Bid Module**

- input bids

**Tender Module**

- criteria

**Award Module**

- recommendation output

## 11.13 Kenya Compliance Overlay

System must support:

- formal evaluation committee structure
- documented evaluation process
- defensible scoring records

## 11.14 Implementation Mapping Note (Frappe / ERPNext)

**ERPNext Gap**

No native support for:

- structured evaluation scoring
- committee-based scoring
- multi-phase evaluation

**Custom Components Required**

- Evaluation Session
- Evaluation Criteria
- Evaluator Score
- Evaluation Report

**Workflow**

- controlled evaluation phases
- role-based access

**Key Logic**

- scoring engine
- aggregation logic
- disqualification handling

**Technical Notes**

- must prevent score tampering
- ensure data consistency

# Section 12: Award & Approval Module

## 12.1 Purpose

To review evaluation outcomes and formally approve (or reject) procurement awards such that:

- decisions are made by authorized bodies
- evaluation recommendations are scrutinized
- approvals are legally valid and auditable
- suppliers are formally notified of outcomes

## 12.2 Position in Lifecycle

Evaluation Completed  
↓  
Evaluation Report Submitted  
↓  
Tender Committee Review  
↓  
Approval / Rejection  
↓  
Accounting Officer Final Approval  
↓  
Award Notification  
↓  
Contract Creation

## 12.3 Core Design Principles

**1\. Evaluation ≠ Award**

- Evaluation recommends
- Approval decides

**2\. Separation of Authority**

- Evaluators cannot approve awards
- Final authority lies with designated roles

**3\. Structured Decision-Making**

- Decisions must be:
    - documented
    - justified
    - auditable

**4\. No Silent Overrides**

- Any deviation from evaluation must be:
    - explicitly recorded
    - justified

## 12.4 Core Entities

**1\. Award Decision Record**

**Fields:**

- Decision ID
- Tender
- Linked Evaluation Report
- Recommended Supplier
- Approved Supplier
- Decision Status
- Decision Date
- Decision Notes

**2\. Approval Workflow Record**

- Step ID
- Role
- User
- Action (Approve / Reject / Request Clarification)
- Timestamp
- Comments

**3\. Award Notification**

- Notification ID
- Tender
- Supplier
- Outcome (Awarded / Unsuccessful)
- Notification Date
- Message Content

**4\. Standstill Period Record**

- Start Date
- End Date
- Status

## 12.5 Lifecycle

**States:**

1.  Evaluation Submitted
2.  Under Review
3.  Approved
4.  Rejected
5.  Awarded
6.  Notified
7.  Closed

**Flow:**

Evaluation → Review → Approve → Notify → Contract

## 12.6 Functional Requirements

**FR-AA-001: Receive Evaluation Report**

- System must ingest evaluation output
- Lock evaluation data

**FR-AA-002: Review Evaluation Outcome**

- Authorized roles review:
    - scores
    - ranking
    - compliance

**FR-AA-003: Approval Workflow**

- Configurable multi-level approval

Possible roles:

- Tender Committee
- Head of Procurement
- Finance Authority
- Accounting Officer

**FR-AA-004: Decision Recording**

System must record:

- recommended supplier
- approved supplier
- justification

**FR-AA-005: Handling Deviations**

If approved supplier ≠ recommended supplier:

- system must:
    - require justification
    - flag for audit

**FR-AA-006: Final Approval**

- Accounting Officer must:
    - approve or reject award

**FR-AA-007: Award Notification**

System must:

- notify:
    - winning supplier
    - unsuccessful bidders

**FR-AA-008: Standstill Period**

- allow time for:
    - complaints
    - challenges

**FR-AA-009: Rejection Handling**

If rejected:

- return to:
    - evaluation OR
    - re-tender

## 12.7 Validation Rules

- evaluation must be complete
- approval workflow must be completed
- no award without final approval
- justification required for deviations

## 12.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Review evaluation | Tender Committee |
| Approve award | Accounting Officer |
| Record decision | Authorized roles |
| Notify suppliers | System / Procurement |

## 12.9 Audit Requirements

System must log:

- all approval actions
- decision changes
- deviations
- notifications sent

## 12.10 Edge Cases

**1\. No Responsive Bids**

- tender may be:
    - cancelled
    - re-issued

**2\. Tie Recommendation**

- predefined tie-breaking rules

**3\. Appeal Before Award Finalization**

- pause award

**4\. Partial Award**

- multiple suppliers selected

## 12.11 Outputs

- award decision record
- approval trail
- notification records

## 12.12 Integration Points

**Evaluation Module**

- input recommendation

**Contract Module**

- triggers contract creation

**Supplier Module**

- notification

## 12.13 Kenya Compliance Overlay

System must support:

- formal approval authorities
- documented award decisions
- supplier notification requirements
- complaint window handling

## 12.14 Implementation Mapping Note (Frappe / ERPNext)

**ERPNext Gap**

No native support for:

- committee-based approvals
- procurement award workflows

**Custom Components Required**

- Award Decision
- Approval Workflow
- Award Notification

**Workflow**

- multi-step approval via Frappe Workflow

**Key Logic**

- deviation tracking
- notification triggers

**Technical Notes**

- ensure immutability of evaluation data
- ensure clear state transitions

**Open Questions**

- standstill enforcement rules
- integration with legal dispute system

# Section 13: Contract Management Module

## 13.1 Purpose

To create, manage, and control procurement contracts such that:

- contracts are derived from approved awards
- terms are structured and enforceable
- execution is monitored against plan and performance targets
- variations are controlled and auditable
- full traceability exists from contract → budget → strategy

## 13.2 Position in Lifecycle

Award Approved  
↓  
Contract Creation  
↓  
Contract Signing  
↓  
Contract Execution  
↓  
Inspection & Acceptance  
↓  
Contract Closure

## 13.3 Core Design Principles

**1\. No Contract Without Award**

- Contracts must originate from approved award decisions

**2\. Structured Contracts**

- Not just documents
- Must include:
    - values
    - timelines
    - deliverables
    - milestones

**3\. Performance Linkage**

- Every contract must link back to:
    - output indicators
    - performance targets

**4\. Controlled Variations**

- Any change to contract must be:
    - approved
    - tracked
    - justified

**5\. Lifecycle Visibility**

- System must show:
    - status
    - progress
    - risks

## 13.4 Core Entities

**1\. Contract**

**Fields:**

- Contract ID
- Tender
- Award Decision
- Supplier
- Contract Title
- Contract Type
- Contract Value
- Currency
- Start Date
- End Date
- Status

**Strategic Fields:**

- Strategic Objective Code
- Program
- Sub-Program
- Output Indicator
- Performance Target

**2\. Contract Milestone**

**Fields:**

- Milestone ID
- Contract
- Description
- Due Date
- Value (optional)
- Status

**3\. Contract Deliverable**

- Deliverable ID
- Contract
- Description
- Expected Output

**4\. Contract Variation**

Tracks changes.

**Fields:**

- Variation ID
- Contract
- Type (Scope / Time / Cost)
- Description
- Value Change
- Date
- Approval Status

**5\. Contract Document**

- Contract file
- Signed agreements
- supporting documents

## 13.5 Contract Lifecycle

**States:**

1.  Draft
2.  Under Review
3.  Approved
4.  Signed
5.  Active
6.  Suspended
7.  Completed
8.  Terminated
9.  Closed

**Flow:**

Draft → Review → Approve → Sign → Active → Complete → Close

## 13.6 Functional Requirements

**FR-CM-001: Contract Creation**

- Automatically generated from:
    - award decision

**FR-CM-002: Contract Structuring**

Must include:

- contract value
- duration
- milestones
- deliverables

**FR-CM-003: Contract Approval**

- must go through approval workflow before signing

**FR-CM-004: Contract Signing**

- support:
    - digital or manual signing

**FR-CM-005: Contract Activation**

- becomes active after signing

**FR-CM-006: Milestone Tracking**

- system must track:
    - progress
    - completion

**FR-CM-007: Variation Management**

System must:

- allow controlled changes
- require approvals

**FR-CM-008: Budget Impact Tracking**

- contract must:
    - reflect committed funds
    - update budget ledger

**FR-CM-009: Contract Completion**

- based on:
    - milestone completion
    - final acceptance

## 13.7 Validation Rules

- contract must match award decision
- contract value must not exceed approved value
- variations must be approved
- dates must be valid

## 13.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Create contract | Procurement |
| Approve contract | Authorized roles |
| Manage execution | Contract Manager |
| Approve variations | Authorized roles |

**13.9 Audit Requirements**

System must log:

- contract creation
- approvals
- variations
- status changes

## 13.10 Edge Cases

**1\. Partial Delivery**

- track partial completion

**2\. Contract Termination**

- early termination with reason

**3\. Multi-Supplier Contracts**

- support multiple awards

**4\. Extension of Time**

- controlled variation

## 13.11 Outputs

- contract register
- milestone reports
- variation logs

## 13.12 Integration Points

**Award Module**

- source of contract

**Budget Module**

- financial tracking

**Inspection Module**

- delivery verification

## 13.13 Kenya Compliance Overlay

System must support:

- formal contract records
- variation controls
- performance tracking

## 13.14 Implementation Mapping Note

**ERPNext Reuse**

Partial reuse possible:

- Supplier
- basic contract constructs (limited)

**Custom Components Required**

- Contract
- Contract Milestone
- Contract Variation

**Workflow**

- approval + execution states

**Key Logic**

- variation tracking
- milestone tracking
- linkage to budget

**Technical Notes**

- ensure integration with budget commitments
- ensure document management

**Open Questions**

- integration with payment systems
- performance penalty handling

# Section 14: Inspection & Acceptance Module

## 14.1 Purpose

To verify and formally accept (or reject) delivered goods, works, or services such that:

- delivery is checked against contract terms
- quality and quantity are validated
- acceptance is documented and auditable
- only accepted deliverables proceed to downstream processes (e.g., payment systems)

## 14.2 Position in Lifecycle

Contract Active  
↓  
Supplier Delivers  
↓  
Inspection Conducted  
↓  
Acceptance / Rejection  
↓  
Completion / Further Action

## 14.3 Core Design Principles

**1\. No Acceptance Without Verification**

- All deliverables must be inspected before acceptance

**2\. Contract-Driven Validation**

- Inspection must be based on:
    - contract deliverables
    - specifications
    - milestones

**3\. Evidence-Based Acceptance**

- Acceptance must include:
    - findings
    - supporting documents
    - approvals

**4\. Separation of Duties**

- Inspectors must not be:
    - procurement officers
    - suppliers

**5\. Outcome Traceability**

- Acceptance must link to:
    - contract
    - milestone
    - performance target

## 14.4 Core Entities

**1\. Inspection Record**

**Fields:**

- Inspection ID
- Contract
- Related Milestone
- Inspection Date
- Location
- Inspecting Officer(s)
- Status

**2\. Inspection Item / Checklist**

- Item Description
- Expected Specification
- Observed Result
- Compliance Status (Pass/Fail/Partial)

**3\. Acceptance Record**

**Fields:**

- Acceptance ID
- Inspection Record
- Acceptance Status (Accepted / Rejected / Partial)
- Acceptance Date
- Approved By
- Remarks

**4\. Defect / Non-Conformance Record**

- Issue ID
- Description
- Severity
- Required Action
- Resolution Status

**5\. Supporting Documents**

- Photos
- Reports
- Delivery notes
- Certificates

## 14.5 Lifecycle

**States:**

1.  Pending Inspection
2.  Inspection In Progress
3.  Inspection Completed
4.  Accepted
5.  Rejected
6.  Partially Accepted
7.  Closed

**Flow:**

Pending → Inspect → Evaluate → Accept / Reject → Close

## 14.6 Functional Requirements

**FR-IA-001: Initiate Inspection**

- triggered by:
    - delivery event
    - milestone due

**FR-IA-002: Conduct Inspection**

System must allow:

- recording of findings
- checklist-based validation

**FR-IA-003: Capture Evidence**

- attach documents
- photos
- reports

**FR-IA-004: Record Non-Conformance**

- system must:
    - allow defect logging
    - track resolution

**FR-IA-005: Acceptance Decision**

System must support:

- full acceptance
- partial acceptance
- rejection

**FR-IA-006: Approval Workflow**

- acceptance must be approved by authorized role

**FR-IA-007: Feedback Loop to Contract**

- update:
    - milestone status
    - contract progress

**FR-IA-008: Link to Budget/Finance**

- accepted deliverables trigger:
    - downstream processes (e.g., payment eligibility)

## 14.7 Validation Rules

- inspection must link to contract
- cannot accept without inspection
- acceptance must be approved
- rejected items must have reason

## 14.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Conduct inspection | Inspection Officer |
| Approve acceptance | Authorized role |
| View records | Relevant stakeholders |

## 14.9 Audit Requirements

System must log:

- inspection actions
- acceptance decisions
- supporting evidence
- approvals

## 14.10 Edge Cases

**1\. Partial Delivery**

- partial acceptance allowed
- remaining tracked

**2\. Re-Inspection**

- required after corrections

**3\. Quality Failure**

- reject and escalate

**4\. Delayed Delivery**

- flag contract performance issue

## 14.11 Outputs

- inspection reports
- acceptance records
- defect logs
- contract performance updates

## 14.12 Integration Points

**Contract Module**

- source of deliverables

**Budget / Finance**

- triggers downstream processes

**Reporting Module**

- performance tracking

## 14.13 Kenya Compliance Overlay

System must support:

- formal inspection records
- documented acceptance decisions
- accountability of inspectors

## 14.14 Implementation Mapping Note

**ERPNext Reuse**

Partial reuse:

- stock receipt / delivery concepts (for goods only)

**Custom Components Required**

- Inspection Record
- Acceptance Record
- Defect Log

**Workflow**

- inspection → approval → closure

**Key Logic**

- checklist validation
- contract linkage
- acceptance control

**Technical Notes**

- support attachments
- ensure audit integrity

# Section 15: Complaints & Dispute Management Module

## 15.1 Purpose

To manage complaints, appeals, and disputes arising from procurement processes such that:

- suppliers and stakeholders can formally challenge decisions
- complaints are handled within defined timelines and procedures
- decisions are documented and auditable
- the procurement process can pause or proceed based on legal rules

## 15.2 Position in Lifecycle

Tender → Bid → Evaluation → Award  
↓  
Complaint Filed  
↓  
Review & Resolution  
↓  
Resume / Modify / Cancel Process

## 15.3 Core Design Principles

**1\. Right to Challenge**

- Suppliers must have a structured mechanism to raise complaints

**2\. Timeliness**

- Complaints must be submitted and resolved within defined timelines

**3\. Process Integrity**

- Complaints may:
    - pause procurement
    - trigger review

**4\. Independence**

- Complaint reviewers must be independent from the original decision-makers

**5\. Full Traceability**

- Every complaint must be:
    - logged
    - tracked
    - resolved with justification

## 15.4 Core Entities

**1\. Complaint Record**

**Fields:**

- Complaint ID
- Tender
- Related Stage (Tender / Evaluation / Award / Contract)
- Complainant (Supplier / Stakeholder)
- Submission Date
- Complaint Type
- Description
- Status

**2\. Complaint Category**

Examples:

- Tender specification issue
- Eligibility dispute
- Evaluation dispute
- Award dispute
- Contract performance dispute

**3\. Complaint Review Record**

- Reviewer(s)
- Review Date
- Findings
- Recommendation

**4\. Decision Record**

- Decision Outcome (Upheld / Rejected / Partially Upheld)
- Action Taken
- Decision Date
- Justification

**5\. Appeal Record (Optional Layer)**

- Appeal ID
- Linked Complaint
- Appeal Outcome

## 15.5 Lifecycle

**States:**

1.  Submitted
2.  Under Review
3.  Investigation
4.  Decision Made
5.  Closed
6.  Appealed

**Flow:**

Submit → Review → Investigate → Decide → Close

**15.6 Functional Requirements**

**FR-CD-001: Submit Complaint**

- Suppliers must be able to:
    - file complaints via portal
- Must include:
    - description
    - supporting documents

**FR-CD-002: Complaint Validation**

System must ensure:

- complaint is within allowed time window
- complaint relates to valid procurement

**FR-CD-003: Acknowledgment**

- system must:
    - generate receipt
    - notify complainant

**FR-CD-004: Assign Reviewers**

- assign independent reviewers
- enforce separation from original evaluators

**FR-CD-005: Investigation Process**

- reviewers can:
    - access relevant records
    - request additional information

**FR-CD-006: Decision Making**

- must produce:
    - outcome
    - justification

**FR-CD-007: Process Impact Handling**

System must support:

- pausing procurement
- modifying results
- cancelling procurement

**FR-CD-008: Appeal Handling**

- allow escalation
- track appeal outcomes

**FR-CD-009: Notifications**

System must notify:

- complainant
- affected suppliers
- internal stakeholders

## 15.7 Validation Rules

- complaint must be within allowed period
- must reference valid procurement stage
- cannot proceed without required information

## 15.8 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Submit complaint | Supplier |
| Review complaint | Assigned reviewers |
| Approve decision | Authorized authority |
| View complaints | Restricted roles |

## 15.9 Audit Requirements

System must log:

- complaint submission
- review actions
- decisions
- process changes

## 15.10 Edge Cases

**1\. Late Complaint**

- automatically rejected

**2\. Multiple Complaints on Same Tender**

- track separately but link

**3\. Complaint After Award**

- may affect contract

**4\. Frivolous Complaints**

- flag for monitoring

## 15.11 Outputs

- complaint register
- decision records
- appeal records

## 15.12 Integration Points

**Tender / Evaluation / Award Modules**

- source of complaint

**Workflow Engine**

- pause/resume process

**Reporting**

- complaint analytics

## 15.13 Kenya Compliance Overlay

System must support:

- formal complaint procedures
- timelines
- audit-ready records

## 15.14 Implementation Mapping Note

**ERPNext Gap**

No native:

- procurement dispute handling

**Custom Components Required**

- Complaint
- Complaint Review
- Appeal

**Workflow**

- complaint lifecycle states

**Key Logic**

- timeline enforcement
- process pause/resume

**Technical Notes**

- ensure secure access
- link to procurement records

**Open Questions**

- integration with external tribunals
- legal document handling

# Section 16: Audit, Compliance & Reporting Module

## 16.1 Purpose

To provide full visibility, traceability, and analytical insight across all procurement activities such that:

- every action is auditable
- compliance with rules and regulations is enforceable
- risks and irregularities can be detected
- decision-makers have real-time insight into procurement performance

## 16.2 Position in System

This module is **cross-cutting**—it spans all modules:

Strategy → Budget → Requisition → Planning → Tender → Bid → Evaluation → Award → Contract → Inspection  
↓  
Audit & Compliance Layer  
↓  
Reporting & Analytics

## 16.3 Core Design Principles

**1\. Everything is Auditable**

- no silent actions
- no hidden changes

**2\. Data is the Source of Truth**

- reports must derive from structured system data
- not manual inputs

**3\. Real-Time Oversight**

- audit is not post-mortem only
- system must support live monitoring

**4\. Risk-Based Monitoring**

- system must detect:
    - anomalies
    - patterns
    - violations

**5\. Transparency by Design**

- appropriate data must be publicly accessible

## 16.4 Core Components

**1\. Audit Trail Engine**

Captures every system action.

**Fields:**

- Audit ID
- Module
- Entity
- User
- Role
- Action Type
- Timestamp
- Before Value
- After Value
- Reference Document

**2\. Compliance Rules Engine**

Defines enforceable rules.

**Examples:**

- no tender without plan
- no award without evaluation
- no procurement without budget

**3\. Risk & Red Flag Engine**

Detects irregularities.

**Examples:**

- bid splitting (fragmentation)
- repeated awards to same supplier
- deviation from evaluation
- late-stage amendments
- abnormal pricing patterns

**4\. Reporting Engine**

Generates structured reports.

**5\. Analytics Dashboard**

Provides real-time insights.

## 16.5 Functional Requirements

**FR-AC-001: Audit Logging (System-Wide)**

System must log:

- all create/update/delete actions
- workflow transitions
- approvals
- financial movements

**FR-AC-002: Immutable Audit Records**

- audit logs must not be editable
- only append operations allowed

**FR-AC-003: Compliance Monitoring**

System must:

- validate rules continuously
- block violations
- log attempted violations

**FR-AC-004: Red Flag Detection**

System must detect:

- suspicious patterns
- threshold breaches
- anomalies

**FR-AC-005: Reporting**

System must provide:

**Operational Reports:**

- procurement plan vs actual
- budget utilization
- contract performance

**Compliance Reports:**

- rule violations
- audit trails
- complaint statistics

**Strategic Reports:**

- procurement vs strategic objectives
- performance outcomes

**FR-AC-006: Dashboard**

Provide dashboards for:

- executives
- procurement officers
- auditors

**FR-AC-007: Public Transparency Portal**

System must expose:

- published tenders
- awards
- contract summaries

**FR-AC-008: Data Export**

- allow export for:
    - audit
    - regulatory reporting

## 16.6 Validation Rules

- all actions must be logged
- audit records cannot be deleted
- compliance rules must be enforced

## 16.7 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| View audit logs | Auditors / Authorized roles |
| Configure rules | System Admin / Compliance Authority |
| View reports | Authorized users |
| View public data | Public |

## 16.8 Audit Requirements (Meta-Level)

System must audit:

- audit logs access
- report generation
- compliance rule changes

**16.9 Edge Cases**

**1\. High Volume Data**

- must support scalable logging

**2\. False Positives in Risk Detection**

- allow tuning of rules

**3\. Data Privacy**

- restrict sensitive data

**16.10 Outputs**

- audit logs
- compliance reports
- risk alerts
- dashboards

## 16.11 Integration Points

**All Modules**

- source of data

**External Systems**

- audit bodies
- regulatory systems

## 16.12 Kenya Compliance Overlay

System must support:

- audit readiness
- regulatory reporting
- transparency requirements

## 16.13 Implementation Mapping Note

**ERPNext Reuse**

- basic audit logs (limited)
- standard reports

**Custom Requirements**

- enhanced audit engine
- risk detection engine
- advanced dashboards

**Likely Components**

- Audit Log Extension
- Compliance Rule Engine
- Risk Detection Module
- Analytics Dashboard

**Technical Notes**

- use event hooks
- ensure performance

**Open Questions**

- AI-based anomaly detection?
- external BI integration?

# Section 17: System Administration & Configuration Module

## 17.1 Purpose

To enable controlled configuration and administration of the system such that:

- workflows can adapt to different entities
- roles and permissions are properly managed
- compliance rules remain enforced
- system behavior is configurable without compromising integrity

## 17.2 Position in System

This module is **global and foundational**:

System Administration  
↓  
Roles / Permissions / Workflows / Rules / Templates  
↓  
All Operational Modules

## 17.3 Core Design Principles

**1\. Configurable but Controlled**

- entities can configure workflows
- but cannot bypass compliance rules

**2\. Separation of Configuration Authority**

- system administrators ≠ procurement users

**3\. Governance First**

- changes must be:
    - logged
    - controlled
    - reversible where appropriate

**4\. Multi-Tenant Control**

- configurations can be:
    - global
    - entity-specific

## 17.4 Core Components

**1\. Role Management**

Defines roles and capabilities.

**Features:**

- create roles
- assign permissions
- define role hierarchies

**2\. User Management**

- create users
- assign roles
- manage access

**3\. Workflow Configuration Engine**

Allows defining workflows for:

- requisition
- planning
- tender
- evaluation
- approval

**4\. Compliance Rule Configuration**

Defines enforceable rules.

Examples:

- budget thresholds
- procurement methods
- approval levels

**5\. Template Management**

Templates for:

- tenders
- evaluation criteria
- contracts
- reports

**6\. Master Data Management**

Defines:

- procurement categories
- departments
- programs
- units of measure

**7\. Notification Configuration**

- email
- SMS
- in-system alerts

**8\. System Parameters**

Global settings such as:

- deadlines
- currency
- localization

## 17.5 Functional Requirements

**FR-SA-001: Role Definition**

- system must allow creation of roles
- roles must map to permissions

**FR-SA-002: User Assignment**

- assign users to roles
- support multi-role users

**FR-SA-003: Workflow Configuration**

- define steps
- assign roles
- define conditions

**FR-SA-004: Compliance Rule Setup**

- define thresholds
- enforce rules

**FR-SA-005: Template Management**

- create reusable templates
- enforce usage

**FR-SA-006: Notification Setup**

- configure triggers
- define recipients

**FR-SA-007: Configuration Audit**

- all changes must be logged

## 17.6 Validation Rules

- no conflicting roles (e.g., evaluator + approver)
- workflows must include approval steps
- compliance rules cannot be disabled

## 17.7 Permissions

|     |     |
| --- | --- |
| **Action** | **Role** |
| Configure system | System Administrator |
| Assign roles | Admin |
| Modify workflows | Admin |
| View configurations | Authorized roles |

## 17.8 Audit Requirements

System must log:

- configuration changes
- role changes
- workflow updates
- rule modifications

## 17.9 Edge Cases

**1\. Misconfiguration**

- system must validate configs before activation

**2\. Role Conflict**

- prevent conflicting assignments

**3\. Workflow Errors**

- detect incomplete workflows

## 17.10 Outputs

- configuration records
- audit logs
- workflow definitions

## 17.11 Integration Points

**All Modules**

- use configured roles and workflows

## 17.12 Kenya Compliance Overlay

System must support:

- enforcement of regulatory rules
- centralized oversight

## 17.13 Implementation Mapping Note

**ERPNext Reuse**

- roles & permissions
- workflow engine
- user management

**Custom Extensions**

- compliance rule engine
- advanced workflow logic
- conflict detection

**Technical Notes**

- use Frappe Role + Workflow system
- extend where needed

**Open Questions**

- how much config exposed to entities vs central authority

# Section 18: Non-Functional Requirements (NFRs)

## 18.1 Purpose

To define the operational, technical, and quality attributes required to ensure that KenTender:

- performs reliably under load
- secures sensitive procurement data
- scales across multiple entities
- remains available and resilient
- meets regulatory and audit expectations

## 18.2 Core Categories

We will define:

1.  Security
2.  Performance
3.  Availability & Reliability
4.  Scalability
5.  Data Integrity
6.  Usability
7.  Interoperability
8.  Compliance & Legal
9.  Maintainability
10. Observability

## 18.3 Security Requirements (Critical)

This is the highest priority area.

**18.3.1 Access Control**

- Role-Based Access Control (RBAC) must be enforced
- Least privilege principle must apply
- Entity-level data isolation required

**18.3.2 Authentication**

- Support secure login:
    - strong passwords
    - optional MFA for sensitive roles

**18.3.3 Data Protection**

- Sensitive data must be:
    - encrypted at rest (recommended)
    - encrypted in transit (mandatory – HTTPS/TLS)

**18.3.4 Bid Security (Critical Requirement)**

- bids must be:
    - inaccessible before opening
    - protected from unauthorized access

**18.3.5 Audit Security**

- audit logs must be:
    - immutable
    - tamper-resistant

**18.3.6 Session Management**

- session timeouts
- inactivity handling

**18.3.7 Data Access Logging**

- all sensitive data access must be logged

## 18.4 Performance Requirements

**18.4.1 Response Time**

- standard operations: < 2 seconds
- complex operations: < 5 seconds

**18.4.2 Concurrent Users**

- system must support:
    - thousands of concurrent users (national scale)

**18.4.3 File Handling**

- support large file uploads (tender docs, bids)
- optimized upload/download

## 18.5 Availability & Reliability

**18.5.1 Uptime**

- target: ≥ 99.5%

**18.5.2 Fault Tolerance**

- system must:
    - recover from failures
    - prevent data loss

**18.5.3 Backup & Recovery**

- regular backups
- disaster recovery plan

## 18.6 Scalability

**18.6.1 Horizontal Scalability**

- support scaling:
    - application layer
    - database layer

**18.6.2 Multi-Entity Support**

- system must support:
    - many procuring entities
- without performance degradation

## 18.7 Data Integrity

**18.7.1 Transaction Integrity**

- no partial transactions
- atomic operations required

**18.7.2 Referential Integrity**

- enforce relationships:
    - strategy → budget → procurement

**18.7.3 Version Control**

- plans, tenders, contracts must be versioned

## 18.8 Usability

**18.8.1 User Experience**

- intuitive workflows
- minimal training required

**18.8.2 Accessibility**

- support accessibility standards where possible

**18.8.3 Localization**

- support:
    - language
    - currency
    - formats

## 18.9 Interoperability

**18.9.1 External Integrations**

System must support integration with:

- financial systems (IFMIS)
- tax systems
- identity systems
- business registries

**18.9.2 API Support**

- expose APIs for:
    - data exchange
    - integrations

## 18.10 Compliance & Legal Requirements

**18.10.1 Data Retention**

- define retention policies
- ensure historical data availability

**18.10.2 Legal Admissibility**

- records must be:
    - timestamped
    - auditable

**18.10.3 Privacy**

- protect personal and sensitive data

**18.11 Maintainability**

**18.11.1 Modular Architecture**

- system must be modular

**18.11.2 Configurability**

- minimize hardcoding

**18.11.3 Upgradeability**

- support updates without breaking system

## 18.12 Observability

**18.12.1 Logging**

- system logs:
    - errors
    - events

**18.12.2 Monitoring**

- system health monitoring

**18.12.3 Alerting**

- alerts for:
    - failures
    - anomalies

**18.13 Edge Considerations**

**1\. Peak Load (Tender Deadlines)**

- system must handle:
    - high submission traffic

**2\. Large Document Handling**

- optimize storage and retrieval

**3\. Distributed Users**

- performance across regions

## 18.14 Implementation Mapping Note

**Strengths**

- Frappe provides:
    - RBAC
    - workflows
    - API framework

**Gaps / Enhancements Needed**

- high-scale optimization
- secure bid handling enhancements
- audit immutability strengthening

**Likely Enhancements**

- reverse proxy (NGINX)
- background workers
- caching layer
- external storage (S3-like)

**Open Questions**

- hosting strategy (cloud vs on-prem)
- multi-region deployment

# Section 19: Integration Architecture

## 19.1 Purpose

To define how KenTender integrates with external systems such that:

- data consistency is maintained
- duplication is minimized
- authoritative sources are respected
- workflows remain seamless across systems

## 19.2 Integration Principles

**1\. System of Record Discipline**

Each data domain must have a **single authoritative source**.

**2\. Loose Coupling**

- integrations should not tightly bind systems
- failures in external systems must not crash KenTender

**3\. Asynchronous Where Possible**

- avoid blocking operations
- use queues/events for reliability

**4\. Traceability**

- all integrations must be logged and auditable

**5\. Security First**

- all integrations must be:
    - authenticated
    - encrypted

## 19.3 Key External Systems

**1\. Financial System (IFMIS or Equivalent)**

**Role:**

- source of budget allocations
- source of payments (outside KenTender)

**Integration Scope:**

**Data Flow IN:**

- budget ceilings
- budget approvals
- expenditure records (optional)

**Data Flow OUT:**

- commitments (requisitions, awards)
- contract data

**Integration Type:**

- API or batch sync

**2\. Tax Authority System**

**Role:**

- validate supplier tax compliance

**Integration Scope:**

- verify:
    - tax registration
    - compliance status

**3\. Business Registry**

**Role:**

- verify supplier legal identity

**Integration Scope:**

- validate:
    - registration number
    - company status

**4\. Identity Management System**

**Role:**

- user authentication

**Integration Scope:**

- SSO (optional)
- identity verification

**5\. Notification Systems**

**Role:**

- communication

**Integration Scope:**

- email gateways
- SMS providers

**6\. Document Signing Systems (Optional)**

**Role:**

- digital contract signing

**7\. Public Transparency Portals**

**Role:**

- publish procurement data

## 19.4 Integration Patterns

**1\. API-Based Integration**

- REST APIs
- secure authentication

**2\. Event-Based Integration**

- publish events:
    - requisition approved
    - award approved
    - contract signed

**3\. Batch Integration**

- periodic sync for:
    - budgets
    - supplier data

**19.5 Data Exchange Models**

**1\. Budget Data**

- budget lines
- allocations
- consumption

**2\. Supplier Data**

- identity
- compliance

**3\. Procurement Data**

- tenders
- awards
- contracts

## 19.6 Error Handling

System must:

- log integration failures
- retry where applicable
- notify administrators

## 19.7 Security Requirements

- API authentication (tokens / OAuth)
- encrypted communication (HTTPS)
- access control per integration

## 19.8 Audit Requirements

System must log:

- all API calls
- data exchanged
- failures

## 19.9 Edge Cases

**1\. External System Downtime**

- system must:
    - continue operating
    - queue requests

**2\. Data Mismatch**

- detect inconsistencies
- flag for review

**3\. Delayed Sync**

- handle stale data

## 19.10 Outputs

- integration logs
- sync status reports
- error reports

## 19.11 Implementation Mapping Note

**Frappe Capabilities**

- REST API framework
- background jobs
- webhook support

**Required Enhancements**

- integration service layer
- retry mechanisms
- monitoring

**Likely Architecture**

- integration module (kentender_integrations)
- queue-based processing

**Open Questions**

- real-time vs batch for IFMIS
- national API standards