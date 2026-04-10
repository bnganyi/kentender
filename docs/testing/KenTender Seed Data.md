# KenTender Seed Data & Acceptance Journey Pack

This pack defines:

- seeded test users
- scenario data packs
- reset strategy
- acceptance journey scripts
- evidence expectations
- execution order

The goal is simple:

Any tester should be able to log in, follow a known script, and verify a business flow without needing developers to prepare the environment manually.

**1\. UAT Operating Principles**

**1\. Stable personas**

Every acceptance test must be run with a defined seeded user.

**2\. Stable scenarios**

Every acceptance test must depend on a named scenario pack, not ad hoc records.

**3\. Resettable state**

The environment must be restorable to a known baseline.

**4\. Journey-based testing**

Testers validate business outcomes, not internal tables.

**5\. Evidence capture**

Every completed UAT run must leave evidence:

- screenshots
- business IDs
- visible status changes
- notifications
- audit evidence where relevant

**2\. Seeded User Pack**

These users should exist in QA/UAT.

**Internal users**

**requisitioner.test**

Role set:

- Department User / Requisitioner

Purpose:

- create and submit requisitions

Default workspace:

- My Work

**hod.test**

Role set:

- Head of Department

Purpose:

- approve or return requisitions

Default workspace:

- My Work

**strategy.test**

Role set:

- Strategy Manager

Purpose:

- manage entity strategic structures

Default workspace:

- Strategy & Planning

**planningauthority.test**

Role set:

- Planning Authority

Purpose:

- review strategic and planning structures

Default workspace:

- Strategy & Planning

**budgetofficer.test**

Role set:

- Budget Officer

Purpose:

- maintain budgets and validate budget lines

Default workspace:

- Budget Control

**financeapprover.test**

Role set:

- Finance Approver

Purpose:

- finance checks, budget review, approvals

Default workspace:

- My Work

**procurement.test**

Role set:

- Procurement Officer

Purpose:

- planning, tender prep, contract prep

Default workspace:

- Procurement Operations

**headofprocurement.test**

Role set:

- Head of Procurement

Purpose:

- tender approvals, award reviews, contract reviews

Default workspace:

- Procurement Operations

**openingchair.test**

Role set:

- Opening Committee Chair

Purpose:

- execute opening

Default workspace:

- My Work

**openingmember.test**

Role set:

- Opening Committee Member

Purpose:

- participate in opening

Default workspace:

- My Work

**evaluator1.test**

Role set:

- Evaluation Committee Member

Purpose:

- score assigned bids

Default workspace:

- My Work

**evaluator2.test**

Role set:

- Evaluation Committee Member

Purpose:

- second evaluator for variance/aggregation testing

Default workspace:

- My Work

**evaluationchair.test**

Role set:

- Evaluation Committee Chair

Purpose:

- manage evaluation session and report submission

Default workspace:

- Evaluation & Award

**accountingofficer.test**

Role set:

- Accounting Officer

Purpose:

- final award approval

Default workspace:

- My Work

**contractmanager.test**

Role set:

- Contract Manager

Purpose:

- manage active contracts and milestones

Default workspace:

- Contract & Delivery

**inspector.test**

Role set:

- Inspection Officer

Purpose:

- perform inspections and record evidence

Default workspace:

- Contract & Delivery

**complaintschair.test**

Role set:

- Complaint Review Chair

Purpose:

- admissibility and complaint decisions

Default workspace:

- Governance & Complaints

**complaintsmember.test**

Role set:

- Complaint Review Member

Purpose:

- complaint review participation

Default workspace:

- My Work

**storekeeper.test**

Role set:

- Storekeeper

Purpose:

- goods receipt and issue

Default workspace:

- Stores

**assetofficer.test**

Role set:

- Asset Officer

Purpose:

- register and assign assets

Default workspace:

- Assets

**auditor.test**

Role set:

- Auditor / Oversight User

Purpose:

- verify audit and oversight behavior

Default workspace:

- Audit & Oversight

**sysadmin.test**

Role set:

- System Administrator

Purpose:

- admin-only configuration checks

Default workspace:

- Administration

This user must not be used for ordinary business UAT.

**Supplier users**

**supplieradmin1.test**

Role set:

- Supplier Admin

Purpose:

- bid submission, complaint filing, signing workflow

Default experience:

- Supplier Portal

**supplieruser1.test**

Role set:

- Supplier User

Purpose:

- supporting bid operations

Default experience:

- Supplier Portal

**supplieradmin2.test**

Role set:

- Supplier Admin

Purpose:

- second bidder for competition scenarios

Default experience:

- Supplier Portal

**3\. Core Seed Data Pack Structure**

Each scenario pack should be loadable independently or cumulatively.

Naming convention:

- SP1
- SP2
- SP3
- etc.

Each pack should include:

- master data prerequisites
- user-role assumptions
- transactional seed records
- expected starting state
- reset notes

**4\. Scenario Pack Definitions**

**SP1 — Requisition Flow Pack**

**Purpose**

Supports requisition creation, approval, and reservation testing.

**Includes**

- 1 procuring entity
- 3 departments
- active strategic plan
- one program
- one sub-program
- one indicator
- one performance target
- open budget control period
- active budget
- 2 active budget lines
- requisitioner, HOD, finance approver, procurement officer users
- one draft requisition template scenario
- one returned requisition scenario
- one already approved requisition scenario

**Starting states**

- active strategy and budget are valid
- one budget line has enough balance
- one budget line is intentionally near exhaustion for negative testing

**Used by**

- AT-REQ-001
- AT-REQ-002
- budget validation checks

**SP2 — Planning and Tender Preparation Pack**

**Purpose**

Supports plan creation, consolidation, anti-fragmentation, and tender draft creation.

**Includes**

- everything from SP1 as needed
- 3 approved requisitions:
    - two similar requisitions for consolidation
    - one separate requisition
- one draft procurement plan
- one active procurement plan
- one fragmentation alert example
- one manual strategic entry example (if enabled for UAT)

**Starting states**

- requisitions are planning-eligible
- one plan item is ready for tender creation
- one alert is unresolved for warning/block testing

**Used by**

- AT-PLAN-001
- AT-TDR-001 setup path

**SP3 — Published Tender and Bid Submission Pack**

**Purpose**

Supports supplier-facing tender access, bid submission, and opening preparation.

**Includes**

- one published tender
- optional tender lots if multi-lot testing is desired
- criteria
- tender documents
- visibility rules
- at least 2 eligible suppliers
- one supplier with no submission yet
- one draft bid scenario
- one submitted bid scenario
- one withdrawn/superseded bid scenario
- one scheduled opening session

**Starting states**

- submission window open
- clarification window optionally open
- at least one bid ready for opening
- opening session not yet executed

**Used by**

- AT-BID-001
- AT-OPEN-001

**SP4 — Evaluation and Award Pack**

**Purpose**

Supports evaluator workflows, aggregation, report generation, and award approval.

**Includes**

- one tender with opening completed
- opening register
- at least 2 opened bids
- evaluator assignments
- conflict declaration pending state
- one evaluation stage in progress
- one completed technical stage variant if needed
- one draft evaluation report
- one draft award decision

**Starting states**

- evaluator users can access assigned session only
- no final award approval yet
- standstill not yet initialized

**Used by**

- AT-EVAL-001
- AT-AWD-001

**SP5 — Contract and Inspection Pack**

**Purpose**

Supports contract creation, signing, activation, inspection, and acceptance.

**Includes**

- one approved award ready for contract
- one draft contract
- one approved contract pending signature
- one signed/active contract
- milestones and deliverables
- at least one inspection method template
- one scheduled inspection
- one inspection requiring parameter-based testing
- one non-conformance scenario
- one partial acceptance scenario

**Starting states**

- one contract ready for signature testing
- one active contract ready for inspection testing
- one variation-ready contract if needed later

**Used by**

- AT-CON-001
- AT-INSP-001

**SP6 — Complaint and Hold Pack**

**Purpose**

Supports complaint submission, hold application, review, decision, and release.

**Includes**

- one award decision in standstill
- one supplier able to file complaint
- one complaint draft
- one submitted complaint awaiting admissibility
- one complaint with hold already applied
- review panel assignments
- one appeal-ready complaint decision if needed

**Starting states**

- contract creation blocked by hold in at least one scenario
- complaint review workspace populated

**Used by**

- AT-CMP-001

**SP7 — Stores and Assets Pack**

**Purpose**

Supports goods receipt, stores issue, reconciliation, and asset registration.

**Includes**

- one accepted goods-type contract output
- one acceptance record eligible for stores receipt
- one procurement goods receipt draft
- one posted goods receipt
- one issue-ready stock line
- one reconciliation scenario with variance
- one assetizable accepted item
- one unregistered asset candidate
- one registered procured asset

**Starting states**

- some goods still in store
- one asset pending handover
- one stock variance open for reconciliation testing

**Used by**

- AT-STORES-001
- AT-ASSET-001

**5\. Seed Pack Dependency Order**

Use this load order:

1.  **BASE-REF**
    - core master data
    - entities
    - departments
    - users
    - roles
    - numbering rules
    - procurement categories/methods
    - document types
2.  **BASE-STRAT**
    - national frameworks
    - strategic plans
    - programs
    - indicators
    - targets
3.  **BASE-BUD**
    - periods
    - budgets
    - budget lines

Then scenario packs:  
4\. SP1  
5\. SP2  
6\. SP3  
7\. SP4  
8\. SP5  
9\. SP6  
10\. SP7

This matters because UAT data becomes unstable if loaded in the wrong order.

**6\. Reset Strategy**

You need three reset modes.

**Reset Mode A — Full Baseline Reset**

Restores:

- BASE-REF
- BASE-STRAT
- BASE-BUD
- no transactional scenarios

Use when:

- starting clean

**Reset Mode B — Scenario Reset**

Restores:

- baseline packs
- one selected scenario pack only

Examples:

- reset to SP3 only
- reset to SP5 only

Use when:

- focused UAT on one business flow

**Reset Mode C — Full End-to-End Reset**

Restores:

- baseline packs
- SP1 through SP7 in linked sequence

Use when:

- performing integrated UAT
- demos
- regression across lifecycle

**7\. Acceptance Journey Register**

Below is the first clean set of business UAT scripts.

**AT-REQ-001 — Submit and Approve Requisition**

**Personas**

- requisitioner.test
- hod.test
- financeapprover.test
- procurement.test

**Seed pack**

- SP1

**Preconditions**

- active strategic linkage exists
- active budget line with sufficient balance exists

**Steps**

1.  Log in as requisitioner.test
2.  Open **My Work**
3.  Click **New Requisition**
4.  Enter title, type, strategy linkage, budget line, justification
5.  Add at least one line item
6.  Submit
7.  Log out and log in as hod.test
8.  Open **Pending Requisition Approvals**
9.  Review and approve
10. Log in as financeapprover.test
11. Review and approve/validate
12. Log in as procurement.test
13. Confirm requisition appears in planning-ready queue

**Expected results**

- requisition gets business ID
- workflow states move correctly
- budget reservation created on final approval
- planning queue updated
- audit events exist

**Evidence**

- screenshots of each state
- requisition business ID
- budget reservation confirmation
- audit event screenshot

**AT-REQ-002 — Returned Requisition Flow**

**Personas**

- requisitioner.test
- hod.test

**Seed pack**

- SP1

**Steps**

1.  Log in as hod.test
2.  Open a requisition pending approval
3.  Return for revision with comments
4.  Log in as requisitioner.test
5.  Confirm returned item appears in My Work
6.  Edit allowed fields
7.  Resubmit

**Expected results**

- return history preserved
- requisition becomes editable only through return path
- resubmission works
- previous history remains visible

**AT-PLAN-001 — Create Procurement Plan from Approved Demand**

**Personas**

- procurement.test

**Seed pack**

- SP2

**Steps**

1.  Log in as procurement.test
2.  Open **Planning Queue**
3.  Create or open draft procurement plan
4.  Add approved requisitions into plan
5.  Consolidate two similar requisitions into one plan item
6.  Save and review source links
7.  Submit plan for approval

**Expected results**

- requisition sources are linked explicitly
- consolidated item total reconciles
- fragmentation warnings appear where expected
- plan gets business ID and workflow status

**AT-TDR-001 — Create and Publish Tender**

**Personas**

- procurement.test
- headofprocurement.test

**Seed pack**

- SP2 or SP3 setup

**Steps**

1.  Log in as procurement.test
2.  Open approved active plan item
3.  Trigger **Create Tender**
4.  Add criteria and documents
5.  Save draft
6.  Submit for review
7.  Log in as headofprocurement.test
8.  Review and approve
9.  Publish tender

**Expected results**

- tender created from plan item, not orphaned
- publication readiness checks pass
- publication timestamp set
- supplier-visible notice appears
- audit event exists

**AT-BID-001 — Supplier Bid Submission**

**Personas**

- supplieradmin1.test

**Seed pack**

- SP3

**Steps**

1.  Log in to supplier portal as supplieradmin1.test
2.  Open eligible tender
3.  Start draft bid
4.  Upload required documents
5.  Run validation
6.  Submit final bid

**Expected results**

- bid moves from draft to submitted/locked
- receipt generated
- bid no longer editable
- supplier sees confirmation and receipt number

**Evidence**

- receipt number
- screenshot of submitted status
- document count/checklist

**AT-OPEN-001 — Execute Bid Opening**

**Personas**

- openingchair.test
- openingmember.test
- procurement.test

**Seed pack**

- SP3

**Steps**

1.  Log in as openingchair.test
2.  Open assigned opening session
3.  Review preconditions
4.  Record attendance
5.  Execute opening
6.  Review generated register

**Expected results**

- candidate bid set resolved
- bids move from sealed to opened through controlled action
- register generated and locked
- tender status updated
- audit events created

**AT-EVAL-001 — Evaluate and Submit Report**

**Personas**

- evaluator1.test
- evaluator2.test
- evaluationchair.test

**Seed pack**

- SP4

**Steps**

1.  Log in as evaluator1.test
2.  Submit conflict declaration
3.  Open assigned evaluation session
4.  Score one bid and submit
5.  Repeat as evaluator2.test
6.  Log in as evaluationchair.test
7.  Review stage completion
8.  Generate evaluation report
9.  Submit report

**Expected results**

- only assigned evaluators can access session
- peer access rules behave correctly
- score records lock on submit
- report generated and submitted
- recommendation available for award stage

**AT-AWD-001 — Award Approval and Standstill**

**Personas**

- headofprocurement.test
- accountingofficer.test

**Seed pack**

- SP4

**Steps**

1.  Log in as headofprocurement.test
2.  Open draft award decision
3.  Review evaluation recommendation
4.  Submit/approve intermediate step
5.  Log in as accountingofficer.test
6.  Final approve award
7.  Trigger notifications
8.  Verify standstill initialized if applicable

**Expected results**

- final approval is separate from evaluation roles
- notifications generated
- standstill record created where required
- award becomes ready/not ready for contract depending standstill/hold state

**AT-CON-001 — Contract Creation, Signing, Activation**

**Personas**

- procurement.test
- supplieradmin1.test
- contractmanager.test

**Seed pack**

- SP5

**Steps**

1.  Log in as procurement.test
2.  Create contract from award
3.  Submit/approve contract draft
4.  Send for signature
5.  Log in as supplieradmin1.test
6.  Complete supplier-side signing action if supported
7.  Return to internal user
8.  Record signature completion
9.  Activate contract
10. Log in as contractmanager.test
11. Confirm milestones/deliverables visible

**Expected results**

- contract originates from award
- signed and active are separate states
- activation blocked until signing complete
- active contract exposes milestone/deliverable structure

**AT-INSP-001 — Parameter-Based Inspection and Acceptance**

**Personas**

- inspector.test
- contractmanager.test

**Seed pack**

- SP5

**Steps**

1.  Log in as inspector.test
2.  Open scheduled inspection
3.  Apply inspection template
4.  Record checklist results
5.  Record parameter test results
6.  Upload evidence
7.  Complete inspection
8.  Submit acceptance decision
9.  Log in as contractmanager.test
10. Confirm contract progress updated

**Expected results**

- parameter-based results evaluated against tolerance
- non-conformance created for failed parameters if applicable
- acceptance blocked or partial as rules require
- contract progress updates from accepted outcome

**AT-CMP-001 — Complaint Submission and Award Hold**

**Personas**

- supplieradmin1.test
- complaintschair.test
- complaintsmember.test

**Seed pack**

- SP6

**Steps**

1.  Log in as supplieradmin1.test
2.  File complaint against award
3.  Upload evidence
4.  Log in as complaintschair.test
5.  Perform admissibility review
6.  Apply hold if complaint affects award/contract progression
7.  Assign review panel
8.  Log in as complaintsmember.test
9.  Add review notes
10. Chair issues decision
11. Verify hold release or continued enforcement based on decision

**Expected results**

- complaint recorded with business ID
- hold applied explicitly
- review records stored
- decision results in controlled actions
- award/contract readiness reflects complaint status

**AT-STORES-001 — Receive Accepted Goods into Stores**

**Personas**

- storekeeper.test

**Seed pack**

- SP7

**Steps**

1.  Log in as storekeeper.test
2.  Open accepted goods pending receipt
3.  Create procurement goods receipt
4.  Record receipt quantities and locations
5.  Post receipt
6.  Create store issue for part of received quantity

**Expected results**

- goods receipt linked to acceptance and contract
- stock traceability preserved
- issue reduces available store balance correctly

**AT-ASSET-001 — Register Procured Asset and Assign Custody**

**Personas**

- assetofficer.test

**Seed pack**

- SP7

**Steps**

1.  Log in as assetofficer.test
2.  Open pending asset registration candidate
3.  Register procured asset
4.  Generate/record asset tag
5.  Assign custodian and location
6.  Create handover record

**Expected results**

- asset linked back to acceptance/contract/stores source
- asset tag unique
- custody assignment active
- movement/handover history preserved

**8\. Evidence Capture Standard**

For every acceptance run, collect:

- Test ID
- Tester name
- Date/time
- User account used
- Seed pack used
- Business IDs created/modified
- Screenshots for critical transitions
- Pass/Fail
- Defects found
- Notes

Recommended screenshot checkpoints:

- form submission success
- approval queue state
- publication state
- receipt state
- opening register
- report submission
- final award approval
- contract activation
- acceptance decision
- complaint hold status

**9\. Defect Logging Guidance**

Each failed UAT should log:

- Journey ID
- Step number
- Expected result
- Actual result
- Severity
- Screenshot
- Business ID / record route
- Reproducibility
- Role/user used
- Seed pack used

This is important because many issues in this system will be:

- role visibility bugs
- workflow transition bugs
- state lock bugs
- service action side-effect bugs

**10\. Seed Data Build Guidance for Developers**

Developers should implement seed packs as:

- scripted fixtures
- idempotent setup commands where possible
- resettable loaders

Recommended structure:

/uat/  
/seed_packs/  
base_ref/  
base_strat/  
base_bud/  
sp1_requisition/  
sp2_planning_tender/  
sp3_bid_opening/  
sp4_eval_award/  
sp5_contract_inspection/  
sp6_complaint_hold/  
sp7_stores_assets/  
/users/  
/journeys/

Each seed pack should include:

- README
- dependencies
- loaded records summary
- known business IDs or prefixes

**11\. Reset Command Strategy**

Recommend implementing management scripts or bench commands like:

- load_uat_base_ref
- load_uat_base_strat
- load_uat_base_bud
- load_uat_sp1
- load_uat_sp2
- ...
- reset_uat_to_baseline
- reset_uat_to_sp3
- reset_uat_full_e2e

These should be deterministic.

**12\. Recommended Next Engineering Artifacts**

You now have enough to direct both UX and UAT.

The next most useful artifacts would be:

**Option A — Workspace implementation backlog**

Ticket pack for:

- workspace JSON/config
- role landing rules
- queue views
- filtered reports

**Option B — UAT seed implementation backlog**

Ticket pack for:

- test users
- seed loaders
- reset commands
- scenario fixtures

**Option C — Wave 2 engineering pack**

Ticket pack for:

- Purchase Requisition
- Procurement Plan

**My recommendation**

Do **A and B before broad UAT**, but do **Wave 2 in parallel** for development.