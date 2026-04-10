# KenTender Permissions Cursor Implementation Pack

**Recommended delivery order**

Build in this order:

1.  PERM-001 — permission architecture conventions
2.  PERM-002 — role constants and permission registry
3.  PERM-003 — row-level scope helper framework
4.  PERM-004 — report access control framework
5.  PERM-005 — workflow action authorization framework
6.  PERM-006 — assignment-based access framework hardening
7.  PERM-007 — sensitivity and sealed-access enforcement
8.  PERM-008 — requisition permission implementation
9.  PERM-009 — planning permission implementation
10. PERM-010 — tender and bid permission implementation
11. PERM-011 — evaluation permission implementation
12. PERM-012 — award and contract permission implementation
13. PERM-013 — inspection / stores / assets permission implementation
14. PERM-014 — report and queue permission implementation
15. PERM-015 — permission test suite and verification fixtures

**Implementation rules for Cursor**

Before the stories, these are the rules Cursor must follow:

- Do **not** rely only on Role Permissions Manager.
- Do **not** put sensitive access rules only in client scripts.
- Do **not** encode business authorization only in reports.
- Do **not** assume System Manager should bypass all business controls.
- Keep permission logic in reusable backend services.
- Use:
    - DocType permissions for baseline access
    - service-layer authorization for actions
    - query helpers for row-level access
    - assignment checks for committee-controlled processes
    - protected file access for sealed/sensitive documents

**PERM-001 — Create permissions architecture note and implementation skeleton**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded security architecture task in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-001
- Title: Create permissions architecture note and implementation skeleton

Context:

- KenTender permissions are implementation-grade and must cover:
    - DocType baseline permissions
    - workflow action authorization
    - row-level filters
    - assignment-based access
    - sensitivity/sealed document access
- The workbook KenTender_Role_Access_Permissions_Workbook_Implementation_Grade.xlsx is the source design artifact.

Task:  
Create the permissions architecture skeleton in kentender_core.

Requirements:

1.  Add a developer-facing permissions architecture note covering:
    - the 5 permission layers
    - what belongs in Frappe Role Permissions Manager vs backend services
    - why report access and row-level filters are separate concerns
2.  Create internal package structure for permission-related code, such as:
    - permissions/
    - permissions/registry.py
    - permissions/scope.py
    - permissions/reports.py
    - permissions/actions.py
3.  Keep the structure clean and reusable by downstream apps.

Constraints:

- Do not implement all domain rules yet.
- Do not hardcode one-off fixes only.
- Keep this as the foundational skeleton.

Acceptance criteria:

- permission architecture note exists
- backend skeleton exists
- later stories have clear integration points

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  final package structure

**PERM-002 — Implement role constants and permission registry**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded permission metadata task in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-002
- Title: Implement role constants and permission registry

Context:

- KenTender needs a stable role vocabulary aligned to the implementation-grade permissions workbook.

Task:  
Implement a central role/permission registry.

Requirements:

1.  Define constants or registry structures for key roles including:
    - Department User
    - Head of Department
    - Finance Approver
    - Procurement Officer
    - Opening Chair
    - Evaluator
    - Evaluation Chair
    - Accounting Officer
    - Contract Manager
    - Inspection Officer
    - Storekeeper
    - Asset Officer
    - Supplier User
    - Auditor
    - System Administrator
2.  Add helper functions for role-family checks.
3.  Keep naming aligned with the permissions workbook and not with ad hoc variants.
4.  Add tests for representative role lookup/check behavior.

Constraints:

- Do not build every domain permission here.
- Keep this as registry/metadata support.

Acceptance criteria:

- role registry exists
- role helpers exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  roles registered

**PERM-003 — Implement row-level scope helper framework**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded row-level permission framework in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-003
- Title: Implement row-level scope helper framework

Context:

- KenTender row-level access depends on scope such as:
    - own
    - department
    - entity
    - assigned
    - supplier-owned
- Reports and list views must not rely on report-level access alone.

Task:  
Implement reusable row-level scope helper services.

Requirements:

1.  Support common checks/patterns such as:
    - current user owns record
    - current user is HOD for record department
    - current user is finance approver for entity
    - current user is assigned to session/case
    - supplier user can access own supplier records only
2.  Provide helpers suitable for:
    - query condition generation
    - explicit allow/deny checks
3.  Add tests for representative positive/negative scope cases.

Constraints:

- Do not hardcode only one DocType.
- Keep service reusable across procurement, governance, stores, and assets.

Acceptance criteria:

- row-level scope helpers exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  supported scope patterns

**PERM-004 — Implement report and queue access control framework**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded report security framework in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-004
- Title: Implement report and queue access control framework

Context:

- Report access in KenTender has two layers:
    1.  who can open the report
    2.  what rows they can see
- The implementation-grade workbook defines intended access such as:
    1.  HOD -> Pending Requisition Approvals
    2.  Finance -> budget-stage queues
    3.  Evaluator -> My Assigned Evaluations
    4.  Storekeeper -> goods receipt queues

Task:  
Implement a reusable report access control framework.

Requirements:

1.  Add a backend registry or mapping for report-to-role access.
2.  Provide a clean pattern for attaching row-level filters per report.
3.  Make the framework suitable for both Script Reports and Query Reports where practical.
4.  Add tests or verification hooks for representative reports:
    - Pending Requisition Approvals
    - Planning Queue
    - My Assigned Evaluations
    - Awards Pending Final Approval

Constraints:

- Do not embed every report directly into one huge file without structure.
- Do not rely only on workspace visibility for access control.

Acceptance criteria:

- report access framework exists
- representative report controls are defined
- tests/verification exist

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  reports covered

**PERM-005 — Implement workflow action authorization framework**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded workflow authorization framework in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-005
- Title: Implement workflow action authorization framework

Context:

- KenTender actions such as approve, publish, open, finalize, activate, accept must be server-authorized.
- DocType write permission is not sufficient.

Task:  
Implement reusable workflow action authorization helpers.

Requirements:

1.  Support patterns such as:
    - role allowed for action
    - role allowed only at specific workflow stage
    - assignment required
    - separation-of-duty conflict check
2.  Make helpers callable from service-layer actions in downstream apps.
3.  Add tests for representative allow/deny scenarios.

Constraints:

- Do not implement every domain action here.
- Keep this framework generic and reusable.

Acceptance criteria:

- workflow action authorization helpers exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  supported authorization patterns

**PERM-006 — Harden assignment-based access framework**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded assignment-based permission hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-006
- Title: Harden assignment-based access framework

Context:

- Sensitive functions in KenTender must use assignment-based access:
    - opening
    - evaluation
    - complaint review
    - inspection where assigned
- The core framework already exists in principle and now needs domain-ready hardening.

Task:  
Harden and extend assignment-based access support.

Requirements:

1.  Support active/inactive assignment states.
2.  Support committee role checks such as Chair, Member, Secretary, Observer.
3.  Support target-object assignment checks for sessions/cases.
4.  Add tests for representative assignment-based access control scenarios.

Constraints:

- Do not tie this only to evaluation.
- Keep it reusable across governance and procurement.

Acceptance criteria:

- assignment access framework is robust enough for domain integration
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  assignment patterns supported

**PERM-007 — Implement sensitivity and sealed-access enforcement layer**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded sensitive-access enforcement task in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-007
- Title: Implement sensitivity and sealed-access enforcement layer

Context:

- Sensitive and sealed records require stricter controls than ordinary role access.
- Examples:
    - pre-opening bid documents
    - confidential evaluation details
    - complaint evidence
    - protected contract or inspection evidence where applicable

Task:  
Implement reusable sealed/sensitive access enforcement helpers.

Requirements:

1.  Build on typed attachment and protected file access patterns.
2.  Support checks for:
    - sealed procurement content
    - confidential content
    - internal-only content
3.  Integrate allow/deny audit logging.
4.  Add tests for representative allow/deny cases.

Constraints:

- Do not implement all domain permission matrices here.
- Keep this layer reusable and backend-enforced.

Acceptance criteria:

- sensitivity enforcement layer exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  content classes supported

**PERM-008 — Implement requisition permissions and report fixes**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded domain permission task in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-008
- Title: Implement requisition permissions and report fixes

Context:

- The permissions workbook defines requisition access patterns such as:
    - Department User -> own/department requisitions
    - HOD -> Pending Requisition Approvals
    - Finance -> finance-stage requisition queue
    - Procurement -> planning-ready requisitions
- A current observed issue is that HOD cannot access the Pending Requisition Approvals report correctly.

Task:  
Implement requisition permission behavior and fix representative report access.

Requirements:

1.  Enforce row-level requisition access for:
    - Department User
    - HOD
    - Finance Approver
    - Procurement Officer
    - Auditor
2.  Fix report access and row filters for at least:
    - My Requisitions
    - Pending Requisition Approvals
    - Planning Ready Requisitions
3.  Ensure HOD sees only records where:
    - hod_user = current user
    - and workflow state is the HOD approval stage
4.  Ensure finance sees only finance-routed requisitions.
5.  Add tests for representative positive/negative access cases.

Constraints:

- Do not rely only on report role assignment.
- Keep row filters backend-driven and testable.

Acceptance criteria:

- HOD report issue is fixed
- requisition access follows workbook intent
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  reports and rules implemented

**PERM-009 — Implement planning permissions**

**App:** kentender_procurement  
**Priority:** High

**Cursor prompt**

Writing

Implement planning permissions in kentender_procurement.

Requirements:

- Procurement Officer owns create/edit/approve planning operations
- HOD and Finance have read-only access only where workbook indicates
- Auditors can read
- Add row-level access and report control for:
    - Planning Queue
    - Draft Procurement Plans
    - Active Procurement Plans
- Add tests for representative access scenarios

Constraints:

- keep implementation aligned to the workbook
- do not broaden planning edit rights casually

**PERM-010 — Implement tender and bid permissions**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement tender and bid permissions in kentender_procurement.

Requirements:

1.  Tender access:
    - Procurement owns draft/review/publish actions
    - Supplier sees published tenders only where eligible
    - Auditor can read
2.  Bid access:
    - Supplier can create/edit/submit only own bid before deadline
    - Internal users must not see sealed content pre-opening unless explicitly allowed
    - Opening Chair gets controlled opening access
3.  Reports/queues to cover:
    - Draft Tenders
    - Published Tenders
    - Bids Awaiting Opening
4.  Add tests for representative allow/deny cases:
    - supplier own bid access
    - denied access to other supplier bid
    - denied pre-opening internal access
    - opening-role controlled access

Constraints:

- use sensitivity/sealed-access helpers
- keep publication and submission rules server-side

**PERM-011 — Implement evaluation permissions**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement evaluation permissions in kentender_procurement.

Requirements:

1.  Evaluator access must be assignment-based.
2.  Conflict declaration must be required before scoring access.
3.  Evaluation Chair can finalize/report but ordinary evaluators cannot.
4.  Accounting Officer can read downstream award-relevant outputs but not edit scoring.
5.  Reports/queues to cover:
    - My Assigned Evaluations
    - Conflict Declarations Pending
    - Evaluation Sessions In Progress
6.  Add tests for:
    - assigned evaluator allow
    - unassigned evaluator deny
    - conflicted evaluator deny
    - chair-specific allow
    - evaluator cannot approve award

Constraints:

- keep peer visibility rules conservative unless clearly specified
- use assignment and workflow authorization helpers

**PERM-012 — Implement award and contract permissions**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement award and contract permissions in kentender_procurement.

Requirements:

1.  Award:
    - Procurement can prepare/manage draft stages as allowed
    - Accounting Officer performs final approval
    - Evaluators cannot approve award
    - deviation handling must remain controlled
2.  Contract:
    - Procurement / Contract Manager roles according to workbook
    - contract activation only through authorized service path
3.  Reports/queues to cover:
    - Awards Pending Approval
    - Awards Pending Final Approval
    - Standstill Active Awards
    - Contracts Pending Signature
    - Active Contracts
4.  Add tests for representative allow/deny cases.

Constraints:

- keep contract readiness, standstill, and hold-sensitive logic intact
- do not bypass service-layer authorization

**PERM-013 — Implement inspection / stores / assets permissions**

**App:** kentender_procurement and downstream ops apps  
**Priority:** High

**Cursor prompt**

Writing

Implement inspection, stores, and assets permissions.

Requirements:

1.  Inspection:
    - Inspector role owns inspection execution and acceptance actions
    - Contract Manager has read or limited related access as defined
2.  Stores:
    - Storekeeper owns GRN, stock movement, and store issue for scoped store access
3.  Assets:
    - Asset Officer owns asset registration and assignment lifecycle actions
4.  Reports/queues to cover:
    - Scheduled Inspections
    - Inspections Awaiting Acceptance
    - Goods Pending Receipt
    - Procurement Goods Receipts
    - Pending Asset Registration
    - Procured Assets
5.  Add row-level store and asset access where applicable.
6.  Add tests for representative role-scope cases.

Constraints:

- do not give operational edit rights to unrelated users
- use row-level scoping for store-specific data

**PERM-014 — Implement report and queue permissions from workbook**

**App:** kentender_core plus domain reports  
**Priority:** Critical

**Cursor prompt**

Writing

Implement report and queue permissions from the implementation-grade permissions workbook.

Requirements:

1.  Review all current key reports/queues and align them with the workbook.
2.  For each report, implement:
    - open-access role list
    - backend row-level filter logic
    - sensitivity handling if needed
3.  Cover at minimum:
    - My Requisitions
    - Pending Requisition Approvals
    - Planning Queue
    - Draft Tenders
    - Published Tenders
    - My Assigned Evaluations
    - Awards Pending Final Approval
    - Scheduled Inspections
    - Goods Pending Receipt
    - Pending Asset Registration
4.  Add verification tests or fixtures for role-specific report behavior.

Constraints:

- do not solve with workspace visibility only
- keep report access testable and explicit

**PERM-015 — Implement permission verification test suite**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded permission verification task in a modular Frappe-based system called KenTender.

Story:

- ID: PERM-015
- Title: Implement permission verification test suite

Context:

- KenTender now has implementation-grade permission rules and needs robust verification coverage.

Task:  
Add a permission-focused test suite covering:

1.  DocType baseline access
2.  workflow action authorization
3.  report open-access
4.  row-level filtering
5.  assignment-based access
6.  sensitivity/sealed-access behavior

Minimum representative scenarios:

- HOD can access Pending Requisition Approvals
- HOD cannot see another HOD’s records
- supplier can access own bid only
- evaluator can access assigned evaluation only after valid conflict declaration
- evaluator cannot approve award
- contract cannot be activated by unauthorized role
- storekeeper can access own store GRN queue only
- asset officer can access pending asset registration queue
- denied sealed bid access is logged

Requirements:

- organize tests clearly
- keep fixtures maintainable
- ensure the suite is useful for regression

Constraints:

- do not create brittle UI-only tests for everything
- focus on backend-enforced permission correctness

**Suggested execution order**

Run in this order:

1.  PERM-001
2.  PERM-002
3.  PERM-003
4.  PERM-004
5.  PERM-005
6.  PERM-006
7.  PERM-007
8.  PERM-008
9.  PERM-009
10. PERM-010
11. PERM-011
12. PERM-012
13. PERM-013
14. PERM-014
15. PERM-015

**What developers should verify after each story**

After every Cursor run, check:

- Did it follow the workbook rather than invent simpler rules?
- Is the rule enforced server-side?
- Does the report open for the right role?
- Does the row filter prevent cross-scope leakage?
- Are workflow actions blocked correctly?
- Are denied sensitive-access attempts auditable?

**Strong recommendation**

Start immediately with:

- PERM-008
- PERM-014
- PERM-015

Because your visible pain right now is **report access and broken real-world role behavior**, especially:

- HOD queue access
- finance-stage queue access
- report open vs row visibility mismatch

The next best artifact after this is a **permission defect triage checklist** you can use against the current build to systematically find what is broken before developers start patching randomly.

Top of Form

Bottom of Form