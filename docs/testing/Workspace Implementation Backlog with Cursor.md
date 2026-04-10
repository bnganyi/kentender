# Workspace Implementation Backlog with Cursor-ready prompts

This is designed to let you start building the **tester-facing UI shell** in parallel with backend development, without waiting for the entire product to exist.

The key idea is:

- build the **navigation skeleton early**
- connect each workspace first to **safe placeholders, filtered lists, and queue views**
- deepen each workspace as the underlying modules mature

**KenTender Workspace Implementation Backlog**

**Epic group overview**

**EPIC-UI-001 — Global Workspace Framework**

Owns:

- My Work
- landing rules
- shared navigation conventions
- workspace shell

**EPIC-UI-002 — Domain Workspaces**

Owns:

- Strategy & Planning
- Budget Control
- Procurement Operations
- Evaluation & Award
- Contract & Delivery
- Governance & Complaints
- Stores
- Assets
- Audit & Oversight
- Administration

**EPIC-UI-003 — Role Routing and Menu Visibility**

Owns:

- default landing logic
- workspace visibility by role
- admin/tester-safe visibility model

**EPIC-UI-004 — Queue Views and Acceptance-Oriented Shortcuts**

Owns:

- filtered list shortcuts
- “pending my action” queues
- business-action-first navigation

**EPIC-UI-005 — UAT Support UI**

Owns:

- test data visibility helpers
- scenario markers
- seeded journey access patterns

**Wave UI-0: build order**

Build in this order:

1.  UI-STORY-001 — shared workspace conventions
2.  UI-STORY-002 — My Work workspace
3.  UI-STORY-003 — default landing routing
4.  UI-STORY-004 — role-to-workspace visibility framework
5.  UI-STORY-005 — Procurement Operations workspace
6.  UI-STORY-006 — Evaluation & Award workspace
7.  UI-STORY-007 — Contract & Delivery workspace
8.  UI-STORY-008 — Strategy & Planning workspace
9.  UI-STORY-009 — Budget Control workspace
10. UI-STORY-010 — Governance & Complaints workspace
11. UI-STORY-011 — Stores workspace
12. UI-STORY-012 — Assets workspace
13. UI-STORY-013 — Audit & Oversight workspace
14. UI-STORY-014 — Administration workspace
15. UI-STORY-015 — queue/report shortcut standardization

That gives you usable UI for early UAT.

**EPIC-UI-001 — Global Workspace Framework**

**UI-STORY-001 — Create shared workspace conventions and shell structure**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** Wave 0 foundation

**Objective**  
Create the shared framework for workspace definitions, naming, grouping, and reusable UI conventions.

**Scope**

- workspace naming conventions
- section naming conventions
- shortcut naming conventions
- standard icon/label placeholders
- README/developer notes for UI consistency

**Out of scope**

- no role routing yet
- no deep business pages
- no dashboard KPIs

**Acceptance criteria**

- consistent workspace naming standard exists
- developers have one place to follow UI conventions
- workspace structure is ready for implementation

**Cursor prompt**

Writing

You are implementing a bounded UI-structure task in a modular Frappe-based system called KenTender.

Story:

- ID: UI-STORY-001
- Epic: EPIC-UI-001
- Title: Create shared workspace conventions and shell structure

Context:

- App: kentender_core
- KenTender is a multi-app backend, but the UI must feel like one coherent product.
- UI must be role-centric and process-centric, not app-centric.
- Top-level workspace families are:
    - My Work
    - Strategy & Planning
    - Budget Control
    - Procurement Operations
    - Evaluation & Award
    - Contract & Delivery
    - Governance & Complaints
    - Stores
    - Assets
    - Audit & Oversight
    - Administration

Task:  
Create the shared workspace shell/convention layer for KenTender.

Requirements:

1.  Add developer-facing conventions for:
    - workspace names
    - section names
    - shortcut labels
    - queue labels
2.  Create a lightweight shell structure or placeholder definitions for the top-level workspace set.
3.  Keep the structure centralized in kentender_core.
4.  Add a short developer note explaining:
    - UI is role-centric, not app-centric
    - raw DocType exposure should be minimized for testers
    - business labels should be preferred over technical labels

Constraints:

- Do not implement all workspace contents yet.
- Do not add speculative dashboards.
- Keep this story focused on conventions and shell structure.

Acceptance criteria:

- workspace naming/convention structure exists
- developer note exists
- top-level workspace shell is ready for follow-on stories

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  how later workspace stories should extend this structure

**UI-STORY-002 — Implement “My Work” workspace**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** UI-STORY-001

**Objective**  
Create the universal landing workspace for most internal users.

**Scope**

- My Work workspace
- placeholder sections for:
    - Pending My Approval
    - Assigned to Me
    - Due Soon
    - Overdue
    - Recent Activity
    - Notifications

**Acceptance criteria**

- workspace exists
- visible sections/shortcuts are coherent
- can be extended safely later

**Cursor prompt**

Writing

You are implementing a bounded UI workspace feature in a modular Frappe-based system called KenTender.

Story:

- ID: UI-STORY-002
- Epic: EPIC-UI-001
- Title: Implement “My Work” workspace

Context:

- App: kentender_core
- “My Work” is the default landing workspace for most internal users.
- It should become the main operational queue surface for testers and users.

Task:  
Implement the My Work workspace.

Required sections/shortcuts:

- Pending My Approval
- Assigned to Me
- Due Soon
- Overdue Items
- Recent Activity
- Notifications

Requirements:

1.  Create the workspace in a clean, extendable way.
2.  Use business-friendly labels.
3.  Prefer queue/shortcut placeholders or filtered report hooks over raw DocType dumps.
4.  Make the structure easy to connect to future queues.

Constraints:

- Do not hardwire it to one module only.
- Do not expose unrelated admin objects.
- Keep visuals simple and functional.

Acceptance criteria:

- My Work workspace exists
- sections are coherent and role-neutral enough for internal use
- implementation is ready for later queue integrations

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  where future queue wiring should plug in

**UI-STORY-003 — Implement default landing routing rules**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** UI-STORY-002

**Objective**  
Route users to the correct default landing workspace based on persona/role.

**Acceptance criteria**

- internal operational users default to My Work
- specialist roles can default to specific workspaces
- behavior is easy to adjust later

**Cursor prompt**

Writing

You are implementing a bounded UI-routing feature in a modular Frappe-based system called KenTender.

Story:

- ID: UI-STORY-003
- Epic: EPIC-UI-001
- Title: Implement default landing routing rules

Context:

- App: kentender_core
- Default landing expectations:
    - most internal operational users -> My Work
    - strategy-focused users -> Strategy & Planning
    - budget-focused users -> Budget Control
    - oversight users -> Audit & Oversight
    - storekeepers -> Stores
    - asset officers -> Assets
    - admins -> Administration
- Supplier users should not use internal Desk landing logic.

Task:  
Implement a clean role-based default landing routing mechanism.

Requirements:

1.  Add a maintainable backend mechanism for resolving default workspace by role/persona.
2.  Keep routing logic centralized and understandable.
3.  Make it easy to expand later.
4.  Add tests or clear verification hooks for routing behavior.

Constraints:

- Do not entangle routing with supplier portal behavior.
- Do not hardcode brittle assumptions where a configuration pattern is simple.
- Keep this internal-user focused.

Acceptance criteria:

- default landing routing works for defined role families
- logic is maintainable
- tests/verification exist

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  supported role-to-default mappings

**UI-STORY-004 — Implement role-to-workspace visibility framework**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** UI-STORY-001, UI-STORY-003

**Objective**  
Control which workspaces each role sees.

**Cursor prompt**

Writing

You are implementing a bounded UI-visibility feature in a modular Frappe-based system called KenTender.

Story:

- ID: UI-STORY-004
- Epic: EPIC-UI-003
- Title: Implement role-to-workspace visibility framework

Context:

- App: kentender_core
- Users should only see workspaces relevant to their business role.
- Example:
    - requisitioner -> My Work, Procurement Operations
    - evaluator -> My Work, Evaluation & Award
    - auditor -> Audit & Oversight, Governance & Complaints, selected others
    - admin -> Administration and selected admin-safe views

Task:  
Implement a maintainable role-to-workspace visibility mechanism.

Requirements:

1.  Support workspace visibility by role family.
2.  Keep logic centralized and easy to extend.
3.  Avoid exposing irrelevant workspaces by default.
4.  Add tests or verification coverage for representative role cases.

Constraints:

- Do not solve all menu-item permissions here.
- Do not expose supplier portal through this internal framework.
- Keep logic clean and backend-driven.

Acceptance criteria:

- workspace visibility can be controlled by role
- representative cases work
- verification/tests exist

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  representative visibility mappings

**EPIC-UI-002 — Domain Workspaces**

**UI-STORY-005 — Implement Procurement Operations workspace**

**App:** kentender_core with links into kentender_procurement  
**Priority:** Critical  
**Depends on:** UI-STORY-001, UI-STORY-004

**Objective**  
Provide the main tester-facing workspace for requisition, planning, tendering, and opening operations.

**Required shortcuts**

- New Requisition
- My Requisitions
- Pending Requisition Approvals
- Planning Queue
- Procurement Plans
- Draft Tenders
- Published Tenders
- Bid Opening Sessions

**Cursor prompt**

Writing

You are implementing a bounded UI workspace feature in a modular Frappe-based system called KenTender.

Story:

- ID: UI-STORY-005
- Epic: EPIC-UI-002
- Title: Implement Procurement Operations workspace

Context:

- Primary user groups:
    - requisitioners
    - HODs
    - procurement officers
    - heads of procurement
- This workspace should support early UAT for requisition through opening flow.

Task:  
Implement the Procurement Operations workspace.

Required shortcuts/sections:

- New Requisition
- My Requisitions
- Pending Requisition Approvals
- Planning Queue
- Procurement Plans
- Draft Tenders
- Published Tenders
- Bid Opening Sessions

Requirements:

1.  Use business-friendly labels.
2.  Prefer filtered list/report shortcuts and action-first navigation.
3.  Keep the structure ready for staged backend maturation.
4.  Avoid showing raw admin/master data clutter.

Constraints:

- Do not overbuild dashboards yet.
- Do not expose unrelated modules.
- Keep it useful even if some linked modules are still placeholders.

Acceptance criteria:

- Procurement Operations workspace exists
- shortcuts reflect the approved business flow
- ready for early UAT use

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  placeholder vs fully wired shortcuts

**UI-STORY-006 — Implement Evaluation & Award workspace**

**App:** kentender_core with links into procurement decision modules  
**Priority:** Critical  
**Depends on:** UI-STORY-004

**Required shortcuts**

- Conflict Declaration
- My Assigned Evaluations
- Evaluation Sessions
- Evaluation Reports
- Award Decisions
- Standstill Tracking
- Notification Status

**Cursor prompt**

Writing

You are implementing a bounded UI workspace feature in a modular Frappe-based system called KenTender.

Story:

- ID: UI-STORY-006
- Epic: EPIC-UI-002
- Title: Implement Evaluation & Award workspace

Context:

- Primary user groups:
    - evaluators
    - evaluation chair
    - procurement review roles
    - accounting officer
- This workspace must support controlled decision-stage UAT.

Task:  
Implement the Evaluation & Award workspace.

Required shortcuts/sections:

- Conflict Declaration
- My Assigned Evaluations
- Evaluation Sessions
- Evaluation Reports
- Award Decisions
- Standstill Tracking
- Notification Status

Requirements:

1.  Keep the workspace role-aware and decision-stage focused.
2.  Use business labels, not raw internal names where avoidable.
3.  Keep unrelated procurement execution links out unless necessary.

Constraints:

- Do not expose unrelated evaluations broadly.
- Do not add award approval logic here; only workspace/navigation.
- Keep it extendable for later queues and cards.

Acceptance criteria:

- Evaluation & Award workspace exists
- shortcuts align with approved user journeys
- ready for evaluator/award UAT

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  placeholder vs fully wired shortcuts

**UI-STORY-007 — Implement Contract & Delivery workspace**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** UI-STORY-004

**Required shortcuts**

- Contracts
- Variations
- Milestones
- Deliverables
- Scheduled Inspections
- Acceptance Records

**Cursor prompt**

Writing

You are implementing a bounded UI workspace feature in a modular Frappe-based system called KenTender.

Story:

- ID: UI-STORY-007
- Epic: EPIC-UI-002
- Title: Implement Contract & Delivery workspace

Context:

- Primary user groups:
    - procurement officers
    - contract managers
    - inspectors
- This workspace supports contract lifecycle and verification UAT.

Task:  
Implement the Contract & Delivery workspace.

Required shortcuts/sections:

- Contracts
- Variations
- Milestones
- Deliverables
- Scheduled Inspections
- Acceptance Records

Requirements:

1.  Organize the workspace around active contractual work, not raw data maintenance.
2.  Keep the structure ready for inspection-heavy workflows later.
3.  Use business-friendly shortcut naming.

Constraints:

- Do not implement KPI dashboards yet.
- Do not expose stores/assets here beyond future handoff awareness.
- Keep this workspace focused on contract execution and verification.

Acceptance criteria:

- Contract & Delivery workspace exists
- shortcuts support AT-CON-001 and AT-INSP-001 style journeys
- implementation is extendable

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  placeholder vs fully wired shortcuts

**UI-STORY-008 — Implement Strategy & Planning workspace**

**App:** kentender_core  
**Priority:** High  
**Depends on:** UI-STORY-004

**Cursor prompt**

Writing

Implement the Strategy & Planning workspace in KenTender.

Required shortcuts/sections:

- National Frameworks
- Entity Strategic Plans
- Programs
- Sub Programs
- Indicators
- Targets
- Strategy Reports

Requirements:

- centralize workspace in kentender_core
- use business-friendly labels
- keep strategy-specific navigation coherent
- avoid unrelated operational procurement clutter

Constraints:

- no dashboard overbuild
- no role routing changes in this story

**UI-STORY-009 — Implement Budget Control workspace**

**App:** kentender_core  
**Priority:** High  
**Depends on:** UI-STORY-004

**Cursor prompt**

Writing

Implement the Budget Control workspace in KenTender.

Required shortcuts/sections:

- Budget Control Periods
- Budgets
- Budget Lines
- Allocations
- Revisions
- Availability Summary
- Budget Reports

Requirements:

- organize around budget operations and review
- keep labels business-friendly
- prepare for UAT budget validation and review journeys

Constraints:

- do not expose raw ledger internals as primary shortcuts yet
- no heavy dashboards yet

**UI-STORY-010 — Implement Governance & Complaints workspace**

**App:** kentender_core  
**Priority:** High  
**Depends on:** UI-STORY-004

**Cursor prompt**

Writing

Implement the Governance & Complaints workspace in KenTender.

Required shortcuts/sections:

- Deliberation Sessions
- Agenda Items
- Resolutions
- Follow-up Actions
- Complaints
- Appeals

Requirements:

- support governance and complaint reviewers
- use business-friendly labels
- keep the workspace complaint-action and deliberation oriented

Constraints:

- do not expose unrelated procurement transaction maintenance here
- no public-facing complaint views

**UI-STORY-011 — Implement Stores workspace**

**App:** kentender_core  
**Priority:** Medium  
**Depends on:** UI-STORY-004

**Cursor prompt**

Writing

Implement the Stores workspace in KenTender.

Required shortcuts/sections:

- Goods Pending Receipt
- Procurement Goods Receipts
- Store Issues
- Reconciliation Tasks
- Balance Exceptions

Requirements:

- organize around storekeeper task flow
- support post-acceptance goods custody UAT
- keep business labels clear

Constraints:

- no asset management shortcuts here
- no unrelated procurement upstream clutter

**UI-STORY-012 — Implement Assets workspace**

**App:** kentender_core  
**Priority:** Medium  
**Depends on:** UI-STORY-004

**Cursor prompt**

Writing

Implement the Assets workspace in KenTender.

Required shortcuts/sections:

- Pending Asset Registration
- Procured Assets
- Handover Records
- Custody Assignments
- Asset Movements
- Disposal

Requirements:

- organize around asset officer workflow
- support source-procurement traceability use cases
- use business labels

Constraints:

- no stores duplication
- no unnecessary depreciation/accounting UI in this story

**UI-STORY-013 — Implement Audit & Oversight workspace**

**App:** kentender_core  
**Priority:** High  
**Depends on:** UI-STORY-004

**Cursor prompt**

Writing

Implement the Audit & Oversight workspace in KenTender.

Required shortcuts/sections:

- Audit Events
- Exceptions
- Deviations
- Risk Flags
- Complaint Impact Views
- Transparency Outputs

Requirements:

- target auditors and oversight users
- keep the workspace read-heavy and review-oriented
- use controlled business labels

Constraints:

- no raw admin clutter
- do not expose sealed/private content casually

**UI-STORY-014 — Implement Administration workspace**

**App:** kentender_core  
**Priority:** Medium  
**Depends on:** UI-STORY-004

**Cursor prompt**

Writing

Implement the Administration workspace in KenTender.

Required shortcuts/sections:

- Procuring Entities
- Departments
- Funding Sources
- Procurement Categories
- Procurement Methods
- Numbering Policies
- Notification Templates
- Guard Rules
- Assignment Admin

Requirements:

- admin-only orientation
- keep this separate from operational user workspaces
- clear business/admin labels

Constraints:

- do not use this workspace as the default for normal users
- do not mix business work queues here

**EPIC-UI-004 — Queue Views and Acceptance-Oriented Shortcuts**

**UI-STORY-015 — Standardize queue/report shortcut patterns**

**App:** kentender_core  
**Priority:** High  
**Depends on:** UI-STORY-002 through UI-STORY-014

**Objective**  
Make workspace shortcuts consistent and UAT-friendly.

**Scope**

- queue naming conventions
- filtered-list/report shortcut conventions
- action-first patterns

**Cursor prompt**

Writing

You are implementing a bounded UI-consistency feature in a modular Frappe-based system called KenTender.

Story:

- ID: UI-STORY-015
- Epic: EPIC-UI-004
- Title: Standardize queue/report shortcut patterns

Context:

- KenTender workspaces should emphasize task queues and acceptance-friendly navigation.
- Testers should not have to search raw DocTypes or guess where pending work is.

Task:  
Standardize queue and report shortcut patterns across implemented workspaces.

Requirements:

1.  Define and apply consistent naming patterns such as:
    - Pending My Approval
    - Assigned to Me
    - Draft ...
    - Published ...
    - Awaiting ...
    - Ready for ...
2.  Prefer filtered list/report shortcuts over raw module dumps.
3.  Align shortcut labels with acceptance journeys.

Constraints:

- Do not redesign all business logic.
- Keep this a UI/navigation consistency story.
- Avoid unrelated visual polish work.

Acceptance criteria:

- shortcut naming is consistent
- workspaces feel task-oriented
- implementation is clearer for testers

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  final naming pattern applied

**Recommended role-to-workspace initial visibility map for implementation**

This is the minimum viable visibility setup developers should target first:

**Requisitioner**

- My Work
- Procurement Operations

**HOD**

- My Work
- Procurement Operations

**Budget Officer**

- My Work
- Budget Control

**Finance Approver**

- My Work
- Budget Control
- Procurement Operations

**Procurement Officer**

- My Work
- Procurement Operations
- Contract & Delivery

**Head of Procurement**

- My Work
- Procurement Operations
- Evaluation & Award
- Contract & Delivery

**Evaluator**

- My Work
- Evaluation & Award

**Evaluation Chair**

- My Work
- Evaluation & Award

**Accounting Officer**

- My Work
- Evaluation & Award
- Contract & Delivery

**Contract Manager**

- My Work
- Contract & Delivery

**Inspector**

- My Work
- Contract & Delivery

**Complaint Reviewer**

- My Work
- Governance & Complaints

**Storekeeper**

- My Work
- Stores

**Asset Officer**

- My Work
- Assets

**Auditor**

- Audit & Oversight
- Governance & Complaints
- selected read-only other workspaces as needed

**System Admin**

- Administration
- selected Audit & Oversight

**What this gives you**

With this backlog, your team can build:

- a unified UI shell in kentender_core
- role-based landing pages
- workspace-driven tester navigation
- UAT-friendly shortcut structure

before every deep module is fully mature.

That is exactly what you want for UI acceptance testing.