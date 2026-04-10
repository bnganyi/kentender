# KenTender Workspace & UAT Matrix

**1\. Purpose**

This matrix defines:

- which workspaces each role should see
- what their default landing page should be
- what business actions they must access quickly
- which acceptance journeys each role participates in
- which seed data packs are required for their testing

This becomes the blueprint for:

- workspace implementation
- role-based menu design
- tester account setup
- UAT execution planning

**2\. Global UI Rules**

**Rule 1 — Default landing page**

Most internal users land on:

**My Work**

This must show:

- pending approvals
- assigned tasks
- active committee work
- recent records
- due/overdue actions

**Rule 2 — Role-specific workspaces**

Users should only see the workspaces relevant to their role.

**Rule 3 — Business labels**

Use business-facing names, not raw DocType labels.

**Rule 4 — Task-first shortcuts**

Every workspace should prioritize:

- new action
- pending action
- status queue
- exceptions/warnings

**3\. Workspace Definitions**

**WS-001 — My Work**

Purpose:

- universal task queue for internal users

Typical cards/shortcuts:

- Pending My Approval
- Assigned to Me
- Due Soon
- Overdue Actions
- Recent Documents
- Notifications

**WS-002 — Strategy & Planning**

Purpose:

- strategic structure management

Contents:

- National Frameworks
- Entity Strategic Plans
- Programs
- Sub Programs
- Indicators
- Targets
- Strategy Reports

**WS-003 — Budget Control**

Purpose:

- budget configuration, control, and review

Contents:

- Budget Control Periods
- Budgets
- Budget Lines
- Allocations
- Revisions
- Availability Summary
- Budget Reports

**WS-004 — Procurement Operations**

Purpose:

- operational flow from requisition to tender operations

Contents:

- New Requisition
- My Requisitions
- Requisition Approval Queue
- Procurement Plans
- Planning Queue
- Tenders
- Clarifications
- Amendments
- Bid Opening Sessions

**WS-005 — Evaluation & Award**

Purpose:

- evaluation workbench and award processing

Contents:

- Conflict Declarations
- My Assigned Evaluations
- Evaluation Sessions
- Evaluation Reports
- Award Decisions
- Standstill Tracking
- Notifications Status

**WS-006 — Contract & Delivery**

Purpose:

- contract execution and verification

Contents:

- Contracts
- Variations
- Milestones
- Deliverables
- Inspections
- Acceptance Records

**WS-007 — Governance & Complaints**

Purpose:

- governance meetings, deliberations, and disputes

Contents:

- Deliberation Sessions
- Agenda Items
- Resolutions
- Follow-up Actions
- Complaints
- Appeals

**WS-008 — Stores**

Purpose:

- post-acceptance goods custody and stock control

Contents:

- Procurement Goods Receipts
- Store Issues
- Reconciliation
- Balance Exceptions

**WS-009 — Assets**

Purpose:

- procured asset registration and custody

Contents:

- Procured Assets
- Handover Records
- Custody Assignments
- Asset Movements
- Disposal

**WS-010 — Audit & Oversight**

Purpose:

- oversight and compliance visibility

Contents:

- Audit Events
- Exceptions
- Deviations
- Risk Flags
- Complaint Impact Views
- Transparency Outputs

**WS-011 — Administration**

Purpose:

- admin-only configuration and master data

Contents:

- Procuring Entities
- Departments
- Funding Sources
- Procurement Categories
- Procurement Methods
- Numbering Policies
- Notification Templates
- Guard Rules
- Assignment Admin

**4\. Role-to-Workspace Matrix**

**R-001 Department User / Requisitioner**

**Default Workspace**

- **My Work**

**Visible Workspaces**

- My Work
- Procurement Operations

**Key shortcuts**

- New Requisition
- My Requisitions
- Returned Requisitions
- Department Request Status

**Must not see**

- Budget Control
- Evaluation & Award
- Audit & Oversight
- Governance admin records

**Acceptance journeys**

- AT-REQ-001
- AT-REQ-002 (returned requisition scenario later)

**Seed data packs**

- Scenario Pack 1

**R-002 Head of Department**

**Default Workspace**

- **My Work**

**Visible Workspaces**

- My Work
- Procurement Operations

**Key shortcuts**

- Pending Requisition Approvals
- Department Requisitions
- Returned for Clarification
- Approved Requests

**Acceptance journeys**

- AT-REQ-001

**Seed data packs**

- Scenario Pack 1

**R-003 Strategy Manager**

**Default Workspace**

- **Strategy & Planning**

**Visible Workspaces**

- My Work
- Strategy & Planning

**Key shortcuts**

- Entity Strategic Plans
- Programs
- Indicators
- Targets
- Active Strategy Reports

**Acceptance journeys**

- strategy administration journeys
- future AT-STRAT-001

**Seed data packs**

- strategy seed pack

**R-004 Planning Authority**

**Default Workspace**

- **Strategy & Planning**

**Visible Workspaces**

- My Work
- Strategy & Planning
- Procurement Operations

**Key shortcuts**

- Strategic Plans Under Review
- Programs
- Targets
- Procurement Plans Requiring Alignment Review

**Acceptance journeys**

- strategy approval
- planning consistency review

**Seed data packs**

- strategy seed pack
- Scenario Pack 2

**R-005 Budget Officer**

**Default Workspace**

- **Budget Control**

**Visible Workspaces**

- My Work
- Budget Control

**Key shortcuts**

- Budget Control Periods
- Budgets
- Budget Lines
- Revisions
- Availability View
- Budget Alerts

**Acceptance journeys**

- future AT-BUD-001
- requisition budget validation parts of AT-REQ-001

**Seed data packs**

- budget seed pack
- Scenario Pack 1

**R-006 Finance Approver**

**Default Workspace**

- **My Work**

**Visible Workspaces**

- My Work
- Budget Control
- Procurement Operations

**Key shortcuts**

- Pending Budget Reviews
- Pending Requisition Finance Checks
- Budget Exceptions
- Revisions Awaiting Approval

**Acceptance journeys**

- AT-REQ-001
- future AT-BUD-002

**Seed data packs**

- Scenario Pack 1
- budget seed pack

**R-007 Procurement Officer**

**Default Workspace**

- **Procurement Operations**

**Visible Workspaces**

- My Work
- Procurement Operations
- Contract & Delivery

**Key shortcuts**

- Planning Queue
- Draft Tenders
- Tenders Under Review
- Clarifications
- Amendments
- Scheduled Bid Openings
- Draft Contracts

**Acceptance journeys**

- AT-PLAN-001
- AT-TDR-001
- AT-OPEN-001
- AT-CON-001

**Seed data packs**

- Scenario Pack 2
- Scenario Pack 3
- Scenario Pack 4
- Scenario Pack 5

**R-008 Head of Procurement**

**Default Workspace**

- **Procurement Operations**

**Visible Workspaces**

- My Work
- Procurement Operations
- Evaluation & Award
- Contract & Delivery

**Key shortcuts**

- Tenders Awaiting Approval
- Opening Sessions
- Award Decisions Under Review
- Contract Drafts
- Variations

**Acceptance journeys**

- AT-TDR-001
- AT-AWD-001
- AT-CON-001

**Seed data packs**

- Scenario Packs 2, 3, 4, 5

**R-009 Opening Committee Chair**

**Default Workspace**

- **My Work**

**Visible Workspaces**

- My Work
- Procurement Operations

**Key shortcuts**

- My Opening Sessions
- Opening Preconditions
- Execute Opening
- Opening Registers

**Acceptance journeys**

- AT-OPEN-001

**Seed data packs**

- Scenario Pack 3

**R-010 Opening Committee Member**

**Default Workspace**

- **My Work**

**Visible Workspaces**

- My Work
- Procurement Operations

**Key shortcuts**

- Assigned Opening Sessions
- Opening Register View

**Acceptance journeys**

- AT-OPEN-001

**Seed data packs**

- Scenario Pack 3

**R-011 Evaluation Committee Member**

**Default Workspace**

- **My Work**

**Visible Workspaces**

- My Work
- Evaluation & Award

**Key shortcuts**

- Conflict Declaration
- My Assigned Evaluations
- Active Evaluation Stages
- Submitted Evaluations

**Must not see**

- unrelated evaluation sessions
- award final approval controls

**Acceptance journeys**

- AT-EVAL-001

**Seed data packs**

- Scenario Pack 4

**R-012 Evaluation Committee Chair**

**Default Workspace**

- **Evaluation & Award**

**Visible Workspaces**

- My Work
- Evaluation & Award

**Key shortcuts**

- Evaluation Sessions
- Stage Progress
- Incomplete Evaluator Records
- Generate Evaluation Report
- Submit Evaluation Report

**Acceptance journeys**

- AT-EVAL-001
- AT-AWD-001

**Seed data packs**

- Scenario Pack 4

**R-013 Accounting Officer**

**Default Workspace**

- **My Work**

**Visible Workspaces**

- My Work
- Evaluation & Award
- Contract & Delivery

**Key shortcuts**

- Awards Pending Final Approval
- Deviations Requiring Review
- Standstill Status
- Contract Readiness Queue

**Acceptance journeys**

- AT-AWD-001
- AT-CON-001

**Seed data packs**

- Scenario Pack 4
- Scenario Pack 5
- Scenario Pack 6

**R-014 Contract Manager**

**Default Workspace**

- **Contract & Delivery**

**Visible Workspaces**

- My Work
- Contract & Delivery

**Key shortcuts**

- Active Contracts
- Milestones Due
- Deliverables Pending Inspection
- Variation Requests
- Completion Progress

**Acceptance journeys**

- AT-CON-001
- AT-INSP-001

**Seed data packs**

- Scenario Pack 5

**R-015 Inspection Officer**

**Default Workspace**

- **Contract & Delivery**

**Visible Workspaces**

- My Work
- Contract & Delivery

**Key shortcuts**

- Scheduled Inspections
- My Inspection Tasks
- Inspections Awaiting Acceptance
- Reinspections Due

**Acceptance journeys**

- AT-INSP-001

**Seed data packs**

- Scenario Pack 5

**R-016 Complaint Review Chair**

**Default Workspace**

- **Governance & Complaints**

**Visible Workspaces**

- My Work
- Governance & Complaints
- Audit & Oversight

**Key shortcuts**

- Complaints Awaiting Admissibility
- Complaints Under Review
- Decision Drafts
- Complaint Holds
- Appeals

**Acceptance journeys**

- AT-CMP-001

**Seed data packs**

- Scenario Pack 6

**R-017 Complaint Review Member**

**Default Workspace**

- **My Work**

**Visible Workspaces**

- My Work
- Governance & Complaints

**Key shortcuts**

- Assigned Complaints
- Review Notes
- Complaint Evidence

**Acceptance journeys**

- AT-CMP-001

**Seed data packs**

- Scenario Pack 6

**R-018 Storekeeper**

**Default Workspace**

- **Stores**

**Visible Workspaces**

- My Work
- Stores

**Key shortcuts**

- Goods Pending Receipt
- Procurement Goods Receipts
- Store Issues
- Reconciliation Tasks

**Acceptance journeys**

- AT-STORES-001

**Seed data packs**

- Scenario Pack 7

**R-019 Asset Officer**

**Default Workspace**

- **Assets**

**Visible Workspaces**

- My Work
- Assets

**Key shortcuts**

- Pending Asset Registration
- Procured Assets
- Handover Records
- Custody Assignments
- Movements

**Acceptance journeys**

- AT-ASSET-001

**Seed data packs**

- Scenario Pack 7

**R-020 Auditor / Oversight User**

**Default Workspace**

- **Audit & Oversight**

**Visible Workspaces**

- Audit & Oversight
- Governance & Complaints
- Budget Control
- Evaluation & Award
- Contract & Delivery

**Key shortcuts**

- Audit Events
- Exceptions
- Award Deviations
- Complaint Outcomes
- Budget Exposure
- Contract Risk Views

**Acceptance journeys**

- audit verification across all major scenarios

**Seed data packs**

- all scenario packs

**R-021 System Administrator**

**Default Workspace**

- **Administration**

**Visible Workspaces**

- Administration
- Audit & Oversight
- selected operational views only where needed

**Key shortcuts**

- Master Data
- Role/Assignment Admin
- Numbering Policies
- Notification Templates
- Guard Rules

**Must not be used as general business actor for UAT**

Keep admin testing separate from business-flow testing.

**R-022 Supplier Admin / Supplier User**

**Default Experience**

- **Supplier Portal Home**, not internal Desk

**Visible areas**

- Eligible Tenders
- My Bids
- My Notifications
- My Complaints
- Contracts for Signature

**Acceptance journeys**

- AT-BID-001
- AT-CMP-001
- supplier side of AT-CON-001

**Seed data packs**

- Scenario Pack 3
- Scenario Pack 6
- Scenario Pack 5 where signing is included

**5\. Role-to-Acceptance Journey Matrix**

| **Role** | **AT-REQ-001** | **AT-PLAN-001** | **AT-TDR-001** | **AT-BID-001** | **AT-OPEN-001** | **AT-EVAL-001** | **AT-AWD-001** | **AT-CON-001** | **AT-INSP-001** | **AT-CMP-001** | **AT-STORES-001** | **AT-ASSET-001** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Department User | ✓   |     |     |     |     |     |     |     |     |     |     |     |
| HOD | ✓   |     |     |     |     |     |     |     |     |     |     |     |
| Budget Officer | ✓   | ✓   |     |     |     |     |     |     |     |     |     |     |
| Finance Approver | ✓   | ✓   |     |     |     |     |     |     |     |     |     |     |
| Procurement Officer |     | ✓   | ✓   |     | ✓   |     | ✓   | ✓   |     |     |     |     |
| Head of Procurement |     | ✓   | ✓   |     | ✓   |     | ✓   | ✓   |     |     |     |     |
| Supplier User |     |     | view | ✓   |     |     | notification | sign |     | ✓   |     |     |
| Opening Chair |     |     |     |     | ✓   |     |     |     |     |     |     |     |
| Opening Member |     |     |     |     | ✓   |     |     |     |     |     |     |     |
| Evaluator |     |     |     |     |     | ✓   |     |     |     |     |     |     |
| Evaluation Chair |     |     |     |     |     | ✓   | ✓   |     |     |     |     |     |
| Accounting Officer |     |     |     |     |     |     | ✓   | ✓   |     |     |     |     |
| Contract Manager |     |     |     |     |     |     |     | ✓   | ✓   |     |     |     |
| Inspector |     |     |     |     |     |     |     |     | ✓   |     |     |     |
| Complaint Reviewer |     |     |     |     |     |     |     |     |     | ✓   |     |     |
| Storekeeper |     |     |     |     |     |     |     |     |     |     | ✓   |     |
| Asset Officer |     |     |     |     |     |     |     |     |     |     |     | ✓   |
| Auditor | verify | verify | verify | verify | verify | verify | verify | verify | verify | verify | verify | verify |

**6\. Role-to-Seed-Pack Matrix**

| **Role** | **SP1 Requisition** | **SP2 Planning/Tender** | **SP3 Bid/Opening** | **SP4 Eval/Award** | **SP5 Contract/Inspection** | **SP6 Complaint/Hold** | **SP7 Stores/Assets** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Department User | ✓   |     |     |     |     |     |     |
| HOD | ✓   |     |     |     |     |     |     |
| Budget Officer | ✓   | ✓   |     |     |     |     |     |
| Finance Approver | ✓   | ✓   |     |     |     |     |     |
| Procurement Officer |     | ✓   | ✓   | ✓   | ✓   |     |     |
| Head of Procurement |     | ✓   | ✓   | ✓   | ✓   |     |     |
| Supplier User |     | ✓   | ✓   |     | ✓   | ✓   |     |
| Opening Chair/Member |     |     | ✓   |     |     |     |     |
| Evaluator / Chair |     |     |     | ✓   |     |     |     |
| Accounting Officer |     |     |     | ✓   | ✓   | ✓   |     |
| Contract Manager |     |     |     |     | ✓   |     |     |
| Inspector |     |     |     |     | ✓   |     |     |
| Complaint Reviewer |     |     |     | ✓   | ✓   | ✓   |     |
| Storekeeper |     |     |     |     | ✓   |     | ✓   |
| Asset Officer |     |     |     |     | ✓   |     | ✓   |
| Auditor | ✓   | ✓   | ✓   | ✓   | ✓   | ✓   | ✓   |

**7\. Workspace Shortcut Blueprint**

**My Work**

Required standard shortcuts:

- Pending My Approval
- Assigned to Me
- Due This Week
- Overdue Items
- Recent Activity
- Notifications

**Procurement Operations**

Required shortcuts:

- New Requisition
- My Requisitions
- Pending Requisition Approvals
- Planning Queue
- Draft Tenders
- Published Tenders
- Bid Opening Sessions

**Evaluation & Award**

Required shortcuts:

- Conflict Declaration
- My Assigned Evaluations
- Evaluation Sessions
- Award Decisions Pending Approval
- Standstill Tracker

**Contract & Delivery**

Required shortcuts:

- Active Contracts
- Milestones Due
- Scheduled Inspections
- Pending Acceptance
- Variations Awaiting Review

**Governance & Complaints**

Required shortcuts:

- Deliberation Sessions
- Complaints Awaiting Admissibility
- Complaints Under Review
- Appeals
- Follow-up Actions

**Stores**

Required shortcuts:

- Goods Pending Receipt
- Procurement Goods Receipts
- Issues
- Reconciliation Tasks

**Assets**

Required shortcuts:

- Pending Asset Registration
- Active Assets
- Handovers
- Custody Assignments
- Movements

**Audit & Oversight**

Required shortcuts:

- Audit Events
- Exceptions
- Deviations
- Complaint Impact
- Budget Alerts
- Contract Risk Views

**8\. Default Landing Rules**

Recommended default landing pages:

- Internal operational users → **My Work**
- Strategy-only users → **Strategy & Planning**
- Budget-only users → **Budget Control**
- Oversight users → **Audit & Oversight**
- Storekeepers → **Stores**
- Asset officers → **Assets**
- Admins → **Administration**
- Suppliers → **Supplier Portal Home**

That keeps navigation intuitive.

**9\. UAT Environment Requirements**

For this matrix to work in practice, UAT needs:

**Fixed users**

Use consistent seeded users mapped to roles.

**Fixed data packs**

Resettable scenario packs.

**Predictable homepages**

Role-based workspace routing.

**Reset capability**

Be able to restore:

- SP1 only
- SP1+SP2
- full E2E flow packs
- complaint hold scenario
- stores/assets scenario

Without resettable packs, testers will corrupt each other’s scenarios.

**10\. Recommended Implementation Order for UI/UAT Setup**

Do not wait until all modules are done.

**Step 1**

Implement:

- My Work
- Procurement Operations
- Evaluation & Award
- Contract & Delivery

These are enough to start meaningful UAT on the core lifecycle.

**Step 2**

Add:

- Strategy & Planning
- Budget Control
- Governance & Complaints

**Step 3**

Add:

- Stores
- Assets
- Audit & Oversight

**Step 4**

Polish:

- dashboard cards
- KPIs
- status counters
- warnings
- timeline widgets

This sequence matches delivery maturity.

**11\. What developers should do with this matrix**

Use it to build:

- workspace JSON/config
- menu visibility rules
- role landing logic
- filtered list views
- queue reports
- test user setup scripts
- seed data scripts

Use it to avoid:

- exposing raw DocType clutter
- inconsistent menus
- forcing testers to use global search for everything

**12\. Recommendation**

You now have enough to operationalize tester-facing UI planning.

The next best artifact is:

**KenTender Seed Data & Acceptance Journey Pack**

with:

- detailed seed pack definitions
- user accounts per persona
- reset strategy
- full UAT scripts for each AT journey

That would let you move from architecture into repeatable business testing.