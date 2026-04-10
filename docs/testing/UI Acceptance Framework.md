# UI Acceptance Framework

**Use one product UI, not one app UI per app**

Testers should experience **KenTender as one coherent system**, even though engineering is split across apps.

So:

- apps stay modular in code
- UI is unified through **Workspaces, role-based menus, dashboards, and guided flows**

Do **not** expose raw technical app boundaries to testers unless they are admin testers.

**Recommended approach**

**1\. Build a unified KenTender navigation layer in kentender_core**

Create central UI structure from kentender_core:

- top-level Workspaces
- grouped menus
- role-based shortcuts
- common dashboards
- tester-friendly route names

This avoids each app exposing disconnected modules.

**Suggested top-level workspaces**

- **Strategy & Planning**
- **Budget Control**
- **Procurement Operations**
- **Evaluation & Award**
- **Contract & Delivery**
- **Governance & Complaints**
- **Stores**
- **Assets**
- **Administration**
- **Audit & Oversight**

That gives testers a stable mental model.

**2\. Use role-based workspaces, not one giant workspace**

Each tester persona should have a realistic UI.

Examples:

**Department User workspace**

- My Requisitions
- Create Requisition
- Requisition Status
- My Department Demand

**Head of Department workspace**

- Pending Requisition Approvals
- Department Requests
- Approval Actions

**Procurement Officer workspace**

- Planning Queue
- Draft Tenders
- Tenders for Review
- Opening Sessions
- Contract Drafts

**Evaluator workspace**

- My Assigned Evaluations
- Conflict Declarations
- Active Evaluation Stages

**Accounting Officer workspace**

- Awards Pending Final Approval
- Contract Approvals
- Exceptions Requiring Decision

**Inspector workspace**

- Scheduled Inspections
- My Inspection Tasks
- Pending Acceptance Decisions

**Auditor/Oversight workspace**

- Audit Events
- Deviations
- Complaints
- Risk Flags

**Supplier portal workspace**

- Eligible Tenders
- My Bids
- My Complaints
- Notifications
- Contracts for Signature

This is much better than asking testers to search DocTypes manually.

**3\. Define “testable business journeys” and map them to UI routes**

Your testers should test **journeys**, not isolated forms.

Examples:

**Journey A — requisition to approval**

1.  Department user opens Requisition workspace
2.  Creates requisition
3.  Submits
4.  HOD sees it in approval queue
5.  Finance validates
6.  Procurement sees it in planning queue

**Journey B — tender to bid to opening**

1.  Procurement creates tender from plan item
2.  Approver reviews and publishes
3.  Supplier sees tender in portal
4.  Supplier submits bid
5.  Procurement schedules opening
6.  Opening committee opens bids

**Journey C — evaluation to award**

1.  Evaluator declares no conflict
2.  Completes scoring
3.  Chair finalizes report
4.  Award reviewers approve
5.  Accounting Officer final-approves
6.  Notifications sent

**Journey D — contract to inspection**

1.  Contract created from award
2.  Signed and activated
3.  Inspection created
4.  Inspector records checklist/parameter results
5.  Acceptance decision made

These journeys should become your acceptance-test scripts.

**Best UI design rule for testers**

**Never make testers rely on raw DocType lists**

Instead provide:

- workspace shortcuts
- filtered list views
- dashboard cards
- clear action buttons
- status indicators
- assigned work queues

Testers should not have to know:

- internal DocType names
- backend module boundaries
- parent-child technical structure

They should know:

- “Pending Tender Reviews”
- “My Assigned Evaluations”
- “Contracts Pending Signature”

**Recommended menu/workspace ownership in your multi-app setup**

**kentender_core**

Own this:

- global Workspaces
- navigation
- shared dashboards
- common reports menu
- role-based landing pages
- global search conventions

**other apps**

Own:

- underlying DocTypes
- backend logic
- app-specific pages/reports/components

This keeps UI coherent even while code stays modular.

**Acceptance testing structure you should implement**

**1\. Demo/Test Data Packs**

Create seeded datasets for each workflow.

You need at least:

**Dataset 1 — basic procurement**

- one entity
- departments
- strategy hierarchy
- budget lines
- one supplier
- one requisition-ready scenario

**Dataset 2 — competitive tender**

- published tender
- eligible suppliers
- bids submitted
- opening session pending

**Dataset 3 — evaluation/award**

- opened bids
- evaluator assignments
- report-ready evaluation scenario

**Dataset 4 — contract/inspection**

- active contract
- milestones
- deliverables
- inspection templates/results

**Dataset 5 — complaints**

- award with standstill
- complaint filed
- hold applied

Without seeded data, testers waste time creating setup data instead of validating UI behavior.

**2\. Persona-based test users**

Create fixed test users such as:

- requisitioner.test
- hod.test
- finance.test
- procurement.test
- evaluator1.test
- evaluator2.test
- accountingofficer.test
- inspector.test
- auditor.test
- supplieradmin.test

Each should land on the right workspace automatically.

This is one of the most important things you can do for acceptance testing.

**3\. Stable acceptance environments**

Use at least:

- **Dev** for developers
- **QA/UAT** for tester acceptance
- **Demo/UAT seed reset path**

Testers need repeatable state. So build:

- data reset scripts
- fixture loaders
- known test scenarios

Otherwise acceptance testing becomes unreliable.

**How to organize workspaces and menus**

**Recommended workspace grouping**

**Strategy & Planning**

- National Frameworks
- Entity Strategic Plans
- Programs
- Sub Programs
- Indicators
- Targets

**Budget Control**

- Budget Periods
- Budgets
- Budget Lines
- Allocations
- Revisions
- Availability Reports

**Procurement Operations**

- Requisitions
- Procurement Plans
- Tenders
- Clarifications
- Amendments
- Bid Opening Sessions

**Evaluation & Award**

- Evaluation Sessions
- Assigned Evaluations
- Award Decisions
- Standstill Monitoring

**Contract & Delivery**

- Contracts
- Variations
- Inspections
- Acceptance Records

**Governance & Complaints**

- Deliberation Sessions
- Resolutions
- Complaints
- Appeals
- Follow-up Actions

**Stores**

- Goods Receipts
- Store Issues
- Reconciliation

**Assets**

- Procured Assets
- Handovers
- Custody
- Movements
- Disposal

**Audit & Oversight**

- Audit Events
- Exceptions
- Risk Flags
- Compliance Reports
- Transparency Outputs

**Administration**

- Master Data
- Numbering Policies
- Notification Templates
- Guard Rules
- Role/Assignment Admin

**How testers should execute acceptance tests**

**Use business scripts, not technical scripts**

Each acceptance test should have:

- **Title**
- **Persona**
- **Preconditions**
- **Steps**
- **Expected results**
- **Evidence to capture**

Example:

**AT-REQ-001 — Department requisition submission**

**Persona:** Department User  
**Preconditions:** Budget line and active target exist  
**Steps:**

1.  Open “My Requisitions”
2.  Click “New Requisition”
3.  Fill required fields
4.  Add item
5.  Submit  
    **Expected results:**

- requisition saved with business ID
- status changes to Submitted
- HOD sees item in approval queue
- audit event exists

This is much better than “test Purchase Requisition DocType.”

**Practical Frappe implementation guidance**

**1\. Create custom Workspaces early**

Do this earlier than many teams do.

For each major persona, provide:

- shortcuts
- filtered reports
- charts/cards later
- “My Work” lists

**2\. Use list view filters as work queues**

Examples:

- Pending my approval
- Assigned to me
- Ready for publication
- Awaiting opening
- Awaiting signature

**3\. Use clear route labels**

Avoid exposing ugly technical labels when a business label is better.

Example:

- “Award Decisions” not Award Decision
- “My Evaluations” not Evaluation Session

**4\. Add lightweight dashboard indicators**

Examples:

- Open requisitions
- Budget warnings
- Tenders closing soon
- Pending inspections
- Complaints on hold

These help testers confirm workflow state quickly.

**Critical rule for multi-app UI**

**The UI should be role-centric, not app-centric**

Bad:

- core
- strategy
- budget
- procurement
- governance
- stores
- assets

Good:

- My Work
- Planning
- Budget
- Procurement
- Evaluation
- Contracts
- Oversight

The codebase can stay app-centric. The UI should not.

**My recommendation for your project**

Do these 5 things before broad tester involvement:

1.  Define tester personas and seed users
2.  Build unified role-based workspaces in kentender_core
3.  Create scenario seed data packs
4.  Write acceptance journeys by business flow
5.  Add resettable QA/UAT environments

That will make UI acceptance testing efficient instead of chaotic.