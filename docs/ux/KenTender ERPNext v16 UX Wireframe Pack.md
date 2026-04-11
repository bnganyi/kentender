# KenTender ERPNext v16 UX Wireframe Pack

**1\. Purpose of This Document**

This document defines the **full UI/UX structure for KenTender**, aligned to:

- ERPNext v16 workspace model
- template-driven procurement logic
- strict workflow enforcement
- role-based operational separation

It is intended to:

- guide **workspace configuration**
- guide **form layout design**
- guide **role visibility**
- ensure **consistency across modules**

**2\. System UX Model (Foundation)**

KenTender is:

👉 **Lifecycle-driven + Template-controlled + Queue-first**

**2.1 Lifecycle Backbone**

All UX aligns to:

Requisition → Planning → Tender → Submission → Evaluation → Award → Contract → Acceptance → GRN → Asset

**2.2 Control Layers (must be visible in UI)**

Every stage is governed by:

- Workflow State (where you are)
- Template (how process behaves)
- Constraints (what is allowed)
- Assignment (who can act)

**2.3 Mandatory UX Rule**

Every major screen MUST show:

Stage + Template + Constraints + Responsible Role

**3\. Information Architecture (Final)**

**3.1 Modules**

| **#** | **Module** | **Purpose** |
| --- | --- | --- |
| 1   | Requisitions | Demand capture & approval |
| 2   | Procurement Planning | Consolidation + process definition |
| 3   | Suppliers | Supplier lifecycle |
| 4   | Tendering | Tender creation & publication |
| 5   | Submissions & Opening | Bid intake & opening |
| 6   | Evaluation & Award | Evaluation + award |
| 7   | Contracts & Execution | Contract lifecycle |
| 8   | Acceptance, Stores & Assets | Delivery → GRN → Asset |
| 9   | Oversight & Audit | Monitoring & traceability |

**3.2 Navigation Rules**

- Users interact via **Workspaces only**
- No direct DocType navigation
- Workspaces are:
    - role-specific
    - queue-driven
- Smart buttons replace navigation

**4\. Global Workspace Pattern**

Each workspace MUST follow:

**4.1 Section Structure**

1.  **Quick Actions**
2.  **My Work Queue**
3.  **Monitoring / KPIs**
4.  **Linked Records / Drill-down**

**4.2 Queue Types**

- Pending My Action
- Assigned to Me
- Awaiting Others
- Blocked / Exceptions

**4.3 Visual Signals**

| **State** | **Meaning** |
| --- | --- |
| Red | Blocked |
| Yellow | Pending |
| Blue | Active |
| Green | Complete |

**5\. Workspace Definitions (Detailed)**

**🔵 5.1 Requisitions Workspace**

**Purpose**

Capture and approve procurement demand.

**Quick Actions**

- Create Requisition

**My Work Queue**

- Pending My Approval
- Returned for Correction

**Monitoring**

- Approved (Not Planned)
- Budget Blocked
- Fully Planned

**Key UX Additions**

**Planning Status Indicator**

Each requisition shows:

- Not Planned
- Partially Planned
- Fully Planned

**Budget Status Banner**

Budget Status: Reserved / Pending / Insufficient

**Smart Buttons**

- View Linked Plan Items
- View Budget Impact

**🔵 5.2 Procurement Planning Workspace (CRITICAL)**

**Purpose**

Transform requisitions into executable procurement actions.

**Quick Actions**

- Create Procurement Plan
- Add Plan Item

**My Work Queue**

- Draft Plan Items
- Pending Approval
- Pending Template Override

**Monitoring**

- Requisitions Ready for Planning
- Partially Planned Requisitions
- Active Plan Items

**Core UI Panels (NEW — critical)**

**🔹 Template Resolution Panel**

Displays:

- Procurement Method
- Selected Template (version)
- Match Quality:
    - Exact
    - Partial
- Override Status:
    - Not Requested
    - Pending
    - Approved

**🔹 Allocation Tracker**

| Requisition | Requested | Allocated | Remaining |

**🔹 Grouping / Splitting Display**

- “This plan item consolidates X requisitions”
- “This requisition is split across X plan items”

**🔹 Constraints Panel**

Shows:

- Eligibility rules
- Regulatory requirements
- Complexity classification

**Smart Buttons**

- Resolve Template
- Request Override
- View Allocation
- Create Tender (only when Active)

**🟥 5.3 Tendering Workspace**

**Purpose**

Create and publish tenders from approved plan items.

**Quick Actions**

- Create Tender (from Plan Item ONLY)

**My Work Queue**

- Draft Tenders
- Pending Publication

**Monitoring**

- Published Tenders
- Closing Soon
- Closed

**Core UI Additions**

**🔹 Template Context Header**

Method: Open Tender  
Template: Complex Goods v3  
Evaluation Model: Weighted Technical + Financial

**🔹 Derived Constraints Panel**

Shows:

- Complexity
- Special requirements
- Eligibility constraints

**Restrictions**

❌ No manual method selection  
❌ No manual evaluation structure

**🟪 5.4 Submissions & Opening Workspace**

**Purpose**

Handle bid submissions and controlled opening.

**My Work Queue**

- Closing Today
- Ready for Opening

**Monitoring**

- Submitted Bids
- Late Submissions

**Core UI Additions**

**🔹 Sealed Bid Indicator**

Bid content sealed until official opening

**🔹 Opening Control Panel**

- Opening Session Status
- Opening Chair

**🟫 5.5 Evaluation & Award Workspace**

**Purpose**

Evaluate bids and determine award.

**My Work Queue**

- Assigned Evaluations
- Pending Submission

**Monitoring**

- Evaluation in Progress
- Reports Pending Approval

**Core UI Additions**

**🔹 Template-Driven Evaluation Panel**

Shows:

- Criteria
- Weighting
- Evaluation stages

**🔹 “Why this process?” Panel**

Complexity: HIGH  
Template: Complex Goods  
Evaluation Model: Multi-stage

**🔹 Assignment Panel**

- Assigned Role
- Assigned Lot

**🟤 5.6 Contracts & Execution Workspace**

**Purpose**

Manage contract lifecycle.

**My Work Queue**

- Contracts Pending Signature
- Contracts Ready for Activation

**Monitoring**

- Active Contracts
- Expiring Contracts

**Core UI Additions**

**🔹 Standstill Panel**

Shows:

- Standstill status
- Remaining days

**🔹 Readiness Panel**

- Approval status
- Compliance checks

**🟠 5.7 Acceptance, Stores & Assets Workspace**

**Purpose**

Handle delivery, inspection, GRN, and asset lifecycle.

**Sub-workspaces**

**A. Acceptance & Inspection**

**Users**

- Inspector
- Technical Committee

**Queues**

- Pending Inspection
- Pending Technical Review

**Dynamic Workflow Display**

Inspection → Technical Review → Committee → Acceptance

**B. Stores (GRN)**

**Users**

- Storekeeper

**Queues**

- Goods Pending Receipt
- GRN Pending Posting

**C. Assets**

**Users**

- Asset Officer

**Queues**

- Pending Registration
- Active Assets

**⚫ 5.8 Oversight & Audit Workspace**

**Purpose**

Provide monitoring and traceability.

**Dashboards**

- Procurement Pipeline
- Template Usage
- Override Frequency

**Tools**

- Trace Explorer
- Integrity Checker

**6\. Form Design Pattern (MANDATORY)**

**6.1 Header**

Must include:

- Document ID
- Workflow State
- Template + Version
- Owner

**6.2 Context Banner**

Stage: Evaluation  
Template: Goods v2  
Match: Partial  
Override: Approved

**6.3 “Why Blocked” Panel**

Cannot proceed:  
\- Awaiting Finance Approval

**6.4 Template Lineage**

Plan → Template → Evaluation → Acceptance

**7\. Smart Button Rules**

Buttons appear ONLY if:

- user has permission
- workflow allows action
- prerequisites are met

**8\. Role Coverage (Updated)**

| **Role** | **Primary Workspace** |
| --- | --- |
| Procurement Officer | Planning, Tender |
| Evaluator | Evaluation |
| Inspector | Acceptance |
| Storekeeper | Stores |
| Asset Officer | Assets |
| Contract Manager | Contracts |

**9\. What Has Been Removed (Obsolete)**

- manual process configuration
- free-form evaluation setup
- duplicated identifiers
- hidden workflow logic

**10\. Final UX Principle**

The system defines the process.  
The UI must make that process visible and actionable.