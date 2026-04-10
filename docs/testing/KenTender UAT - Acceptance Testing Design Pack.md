# KenTender UAT / Acceptance Testing Design Pack

This pack gives you a practical model for **UI-based acceptance testing in a multi-app Frappe system** without exposing the technical app boundaries to testers.

**1\. Acceptance Testing Principle**

Testers should validate **business journeys by role**, not backend modules.

So the UI should be organized around:

- who the tester is
- what work they need to do
- where they are in the procurement lifecycle

Not around:

- app names
- DocType names
- internal package structure

**Core rule**

**Code is app-centric. UI is role-centric and process-centric.**

**2\. Recommended UI Architecture for Testing**

Use kentender_core as the owner of:

- global Workspaces
- role landing pages
- menu grouping
- common dashboards
- “My Work” queues
- filtered list shortcuts

Each domain app still owns its DocTypes and logic, but testers should mostly enter the system through unified workspaces.

**3\. Recommended Top-Level Workspace Model**

These should be your primary user-facing workspace families.

**A. My Work**

For every logged-in internal user:

- Items awaiting my action
- Recently updated records
- Assigned committee work
- Pending approvals
- Notifications

This should be the default landing workspace for most users.

**B. Strategy & Planning**

Used by:

- Strategy Manager
- Planning Authority
- selected oversight testers

Contents:

- National Frameworks
- Entity Strategic Plans
- Programs
- Sub Programs
- Indicators
- Targets
- Planning reports

**C. Budget Control**

Used by:

- Budget Officer
- Finance Approver
- auditors

Contents:

- Budget Control Periods
- Budgets
- Budget Lines
- Allocations
- Revisions
- Availability view
- Budget ledger reports

**D. Procurement Operations**

Used by:

- Department users
- HOD
- Procurement officers

Contents:

- Requisitions
- Procurement Plans
- Tenders
- Clarifications
- Amendments
- Bid Opening Sessions

**E. Evaluation & Award**

Used by:

- evaluators
- evaluation chair
- tender committee
- accounting officer

Contents:

- Conflict declarations
- Assigned evaluations
- Evaluation sessions
- Award decisions
- Standstill monitoring
- Notifications status

**F. Contract & Delivery**

Used by:

- contract managers
- procurement officers
- inspectors

Contents:

- Contracts
- Variations
- Milestones
- Deliverables
- Inspections
- Acceptance records

**G. Governance & Complaints**

Used by:

- complaint reviewers
- governance officers
- oversight users

Contents:

- Deliberation sessions
- Agenda items
- Resolutions
- Follow-up actions
- Complaints
- Appeals

**H. Stores**

Used by:

- storekeepers
- inventory testers
- operations users

Contents:

- Goods receipts
- Store issues
- Reconciliation
- Balance exceptions

**I. Assets**

Used by:

- asset officers
- custodians
- auditors

Contents:

- Procured assets
- Handover records
- Custody assignments
- Asset movements
- Disposal

**J. Audit & Oversight**

Used by:

- auditors
- central compliance
- central oversight

Contents:

- Audit events
- Exceptions
- Red flags
- Deviations
- Complaint impacts
- Transparency outputs

**K. Administration**

Used by:

- admins only

Contents:

- Master data
- numbering policies
- templates
- workflow guard rules
- assignment admin
- notification config

**4\. Persona-Based Workspace Mapping**

This is the important part for UAT.

**Department User**

Primary workspaces:

- My Work
- Procurement Operations

Should see:

- Create Requisition
- My Requisitions
- Department request status

Should not see:

- budget ledger
- evaluation data
- award internals

**Head of Department**

Primary workspaces:

- My Work
- Procurement Operations

Should see:

- Pending requisition approvals
- Department requisitions
- returned items

**Budget Officer**

Primary workspaces:

- My Work
- Budget Control

Should see:

- Budget lines
- availability checks
- revisions
- budget warnings

**Procurement Officer**

Primary workspaces:

- My Work
- Procurement Operations
- Contract & Delivery

Should see:

- planning queue
- tenders in draft/review
- opening schedules
- contracts pending preparation

**Evaluation Committee Member**

Primary workspaces:

- My Work
- Evaluation & Award

Should see:

- conflict declaration
- assigned evaluations only
- stage-specific work queue

Should not see:

- unrelated evaluations
- award approval controls

**Evaluation Committee Chair**

Primary workspaces:

- My Work
- Evaluation & Award

Should see:

- evaluation progress tracking
- finalize report
- return/reopen controls where allowed

**Accounting Officer**

Primary workspaces:

- My Work
- Evaluation & Award
- Contract & Delivery

Should see:

- awards pending final approval
- decisions requiring authority
- contract approvals where applicable

**Inspection Officer**

Primary workspaces:

- My Work
- Contract & Delivery

Should see:

- scheduled inspections
- active contract inspections
- pending acceptance tasks

**Complaint Reviewer**

Primary workspaces:

- My Work
- Governance & Complaints

Should see:

- assigned complaints
- evidence
- review actions
- hold status

**Storekeeper**

Primary workspaces:

- My Work
- Stores

Should see:

- accepted goods pending receipt
- store receipts
- issues
- reconciliations

**Asset Officer**

Primary workspaces:

- My Work
- Assets

Should see:

- pending asset registrations
- handovers
- active custody records

**Auditor / Oversight**

Primary workspaces:

- Audit & Oversight
- Governance & Complaints
- Budget Control
- Evaluation & Award

Should see:

- audit events
- deviations
- exceptions
- complaint outcomes
- budget exposure summaries

**Supplier User**

This should be a separate supplier-facing experience.

Primary views:

- Eligible Tenders
- My Bids
- My Notifications
- My Complaints
- Contracts for signature

Do not expose Desk-style internal workspaces to suppliers.

**5\. Menu Design Rules**

**Rule 1**

Menus should use **business labels**, not raw DocType names.

Examples:

- “My Requisitions” instead of Purchase Requisition
- “Award Decisions” instead of Award Decision
- “Inspection Tasks” instead of Inspection Record

**Rule 2**

Put “create” and “work queue” links first.

Example for Procurement Operations:

- New Requisition
- Requisitions Awaiting Approval
- Planning Queue
- Draft Tenders
- Published Tenders
- Opening Sessions

**Rule 3**

Hide irrelevant menus by role.  
Do not overwhelm testers with everything.

**6\. Acceptance Test Environment Model**

You should have at least these environments:

**DEV**

For developers only.

**QA**

For controlled feature verification.

**UAT**

For role-based acceptance testing by testers and business users.

**Optional Demo/UAT Reset**

A resettable site with seeded scenarios.

**Recommendation**

For UAT, maintain:

- stable seed data
- stable test users
- repeatable scenario states

Without that, testers will burn time rebuilding context.

**7\. Seeded Test Personas**

Create dedicated users with stable credentials and fixed roles.

Example set:

- requisitioner.test
- hod.test
- budgetofficer.test
- procurement.test
- evaluator1.test
- evaluator2.test
- evaluationchair.test
- accountingofficer.test
- inspector.test
- complaintschair.test
- storekeeper.test
- assetofficer.test
- auditor.test
- supplieradmin1.test

Each user should land in the correct workspace with realistic permissions.

**8\. Seeded Acceptance Scenarios**

This is critical.

Build reusable UAT data packs.

**Scenario Pack 1 — Requisition Flow**

Contains:

- active strategic plan
- budget line
- department user
- draft-ready requisition context

Purpose:

- test requisition creation, approval, and planning readiness

**Scenario Pack 2 — Planning and Tender Flow**

Contains:

- approved requisitions
- procurement plan
- plan item ready for tender
- procurement officer user

Purpose:

- test plan consolidation, tender creation, approval, publication

**Scenario Pack 3 — Bid Submission and Opening**

Contains:

- published tender
- eligible suppliers
- submitted bids
- opening committee users

Purpose:

- test supplier portal, bid sealing, opening session, register generation

**Scenario Pack 4 — Evaluation and Award**

Contains:

- opened bids
- evaluator assignments
- stage-ready criteria
- award decision draft path

Purpose:

- test scoring, aggregation, report submission, final approval

**Scenario Pack 5 — Contract and Inspection**

Contains:

- approved award
- draft/signed contract
- milestone and deliverable setup
- inspection template

Purpose:

- test contract lifecycle, inspection, parameter testing, acceptance

**Scenario Pack 6 — Complaint and Hold**

Contains:

- award in standstill
- complaint filed
- review panel assigned

Purpose:

- test complaint review, hold application, decision and release

**Scenario Pack 7 — Stores and Assets**

Contains:

- accepted goods
- store receipt-ready records
- assetizable items

Purpose:

- test goods receipt, issuance, reconciliation, asset registration

**9\. Acceptance Journey Catalog**

Your testers should run named journeys.

**AT-REQ-001 — Submit and Approve Requisition**

Persona:

- Department User, HOD, Finance, Procurement

Expected result:

- requisition created
- approved
- budget reserved
- planning queue updated

**AT-PLAN-001 — Convert Approved Demand into Procurement Plan**

Persona:

- Procurement Officer

Expected result:

- approved requisitions pulled into plan
- sources linked
- anti-fragmentation checks visible

**AT-TDR-001 — Publish Tender**

Persona:

- Procurement Officer, Approver

Expected result:

- tender approved
- publication readiness checks pass
- supplier-visible notice available

**AT-BID-001 — Submit Bid and Receive Receipt**

Persona:

- Supplier User

Expected result:

- bid drafted
- validation runs
- final submit locks bid
- receipt issued

**AT-OPEN-001 — Execute Bid Opening**

Persona:

- Opening Committee Chair

Expected result:

- preconditions pass
- bids opened atomically
- register generated and locked

**AT-EVAL-001 — Evaluate and Submit Report**

Persona:

- Evaluator, Chair

Expected result:

- conflict declaration completed
- scoring submitted
- report generated and submitted

**AT-AWD-001 — Final Award Approval**

Persona:

- Tender Reviewer, Accounting Officer

Expected result:

- award approved
- notifications generated
- standstill initialized if required

**AT-CON-001 — Sign and Activate Contract**

Persona:

- Procurement Officer, Supplier, Contract Authority

Expected result:

- contract created
- signed
- activated
- budget commitment reference preserved

**AT-INSP-001 — Parameter-Based Inspection**

Persona:

- Inspector

Expected result:

- inspection template applied
- parameter results entered
- tolerance evaluated
- acceptance decision controlled by results

**AT-CMP-001 — Complaint Creates Award Hold**

Persona:

- Supplier, Complaint Reviewer

Expected result:

- complaint filed
- admissibility reviewed
- hold applied to award progression

**AT-STORES-001 — Receive Accepted Goods into Stores**

Persona:

- Storekeeper

Expected result:

- goods receipt created from acceptance
- stock visible
- traceable to contract and acceptance

**AT-ASSET-001 — Register Procured Asset**

Persona:

- Asset Officer

Expected result:

- asset created from accepted/store-linked procurement
- custody assigned
- source traceability preserved

**10\. UAT Script Template**

Use this format for every test.

**Test ID**

AT-REQ-001

**Title**

Submit and approve requisition

**Persona**

Department User / HOD / Finance / Procurement Officer

**Preconditions**

- active strategy exists
- active budget line exists
- users and permissions seeded

**Steps**

1.  Log in as department user
2.  Open My Work
3.  Click New Requisition
4.  Complete form
5.  Submit
6.  Log in as HOD
7.  Approve
8.  Log in as finance reviewer
9.  Validate
10. Confirm procurement queue entry

**Expected Results**

- business ID generated
- status changes correctly
- approval trail visible
- budget reservation created
- audit event exists

**Evidence to Capture**

- screenshots
- record IDs
- audit trail snapshot
- notification evidence if applicable

**11\. Workspace Build Strategy for Developers**

Implement workspaces in phases.

**Phase A — Minimal role workspaces**

Build first:

- My Work
- Strategy & Planning
- Budget Control
- Procurement Operations
- Evaluation & Award
- Contract & Delivery

**Phase B — Governance and downstream**

Then add:

- Governance & Complaints
- Stores
- Assets
- Audit & Oversight

**Phase C — Dashboards and polish**

Then add:

- charts
- KPIs
- warning cards
- timeline widgets

This keeps UAT usable early without waiting for polished analytics.

**12\. Practical Frappe Recommendations**

**Use Workspace shortcuts aggressively**

Examples:

- New Requisition
- My Pending Approvals
- Draft Tenders
- Assigned Evaluations
- Pending Inspections

**Use filtered list views as work queues**

Examples:

- workflow_state = Pending My Approval
- assigned_to = current user
- status = Draft and entity = current entity

**Add route-friendly pages for complex workflows**

Especially for:

- evaluation workbench
- opening session view
- inspection parameter testing
- complaint review workspace

**Do not rely only on generic DocType forms**

For high-complexity areas, build guided pages or action-centric views.

**13\. Best ownership model in the multi-app structure**

**kentender_core owns**

- top-level workspaces
- landing pages
- role-based navigation
- “My Work” framework
- shared UI conventions

**domain apps own**

- DocTypes
- backend logic
- specialized reports/pages
- domain-specific dashboards

That keeps UI unified and code modular.

**14\. Recommended Next Engineering Deliverables**

Before large-scale UAT, I recommend creating these artifacts:

**A. Workspace & Menu Matrix**

A table mapping:

- role
- default workspace
- visible workspaces
- key shortcuts
- prohibited menus

**B. UAT Persona Matrix**

A table mapping:

- persona
- user account
- roles
- test journeys
- seed data packs required

**C. Acceptance Journey Register**

A catalog of all AT scripts with IDs and dependencies

**D. Seed Data Pack Design**

A document defining:

- what records to seed
- in what order
- for which journey

**15\. My recommendation**

The best next move is not more architecture. It is to operationalize this for your team.

So the next artifact I should generate is a **KenTender Workspace & UAT Matrix** with:

- role-by-role workspace mapping
- menu grouping
- default landing pages
- acceptance journey mapping
- seed data scenario mapping

That will give developers and testers a concrete UI testing blueprint.