# KenTender System Hardening Pack

**Production-Readiness Implementation Pack v1**

**What this pack must achieve**

By the end of this pack, KenTender should be hardened for:

- concurrency and transaction safety
- audit-grade traceability
- permission edge cases
- sealed/sensitive data control
- performance on core queues and reports
- configuration safety
- operational support and debugging
- UAT stabilization and regression control

**Execution order**

Run in this order:

1.  HARD-001 — transaction boundary and concurrency review
2.  HARD-002 — optimistic/defensive locking for critical actions
3.  HARD-003 — audit completeness enforcement
4.  HARD-004 — state transition integrity enforcement
5.  HARD-005 — permission edge-case hardening
6.  HARD-006 — sealed/sensitive document access hardening
7.  HARD-007 — report/query performance hardening
8.  HARD-008 — workflow/report observability and diagnostics
9.  HARD-009 — template/configuration governance hardening
10. HARD-010 — migration and patch safety framework
11. HARD-011 — end-to-end consistency checker
12. HARD-012 — UAT stabilization toolkit
13. HARD-013 — production readiness checklist and gates
14. HARD-014 — regression and chaos-style failure test suite

**Global hardening rules**

These apply across all stories:

- no critical action should depend only on UI checks
- no critical transition should happen without a service boundary
- no critical service should silently partially succeed
- every approval/state change must be auditable
- every queue/report must remain correct under row-level filtering
- every cross-module link must be verifiable
- every override path must be explicit and logged

**HARD-001 — Transaction boundary and concurrency review**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-001
- Title: Transaction boundary and concurrency review

Context:

- KenTender has critical actions that can be triggered concurrently or retried, including:
    - requisition approval
    - budget reservation
    - tender publication
    - bid submission
    - bid opening
    - evaluation submission
    - award approval
    - contract activation
    - acceptance decision
    - GRN posting
    - asset creation
- These actions must have clear transaction boundaries and failure behavior.

Task:  
Perform a transaction/concurrency hardening review and implement safeguards where missing.

Requirements:

1.  Identify critical services with race-condition risk.
2.  Document expected transaction boundaries for each.
3.  Add defensive handling where practical to prevent duplicate or conflicting completion.
4.  Produce a developer-facing review note.

Constraints:

- Do not hand-wave concurrency risk.
- Be concrete about where duplicate execution would be dangerous.

Acceptance criteria:

- critical services reviewed
- transaction boundary note exists
- representative safeguards added

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  high-risk actions identified

**HARD-002 — Optimistic/defensive locking for critical actions**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded concurrency hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-002
- Title: Optimistic/defensive locking for critical actions

Context:

- Critical actions such as opening bids, final-approving awards, activating contracts, and posting GRNs must not be processed twice or in conflicting ways.

Task:  
Implement optimistic/defensive locking patterns for critical actions.

Requirements:

1.  Protect representative high-risk services such as:
    - execute_bid_opening(...)
    - final_approve_award(...)
    - activate_contract(...)
    - post_grn(...)
2.  Prevent duplicate completion where retry/double-click/concurrent execution occurs.
3.  Return clear error or no-op semantics where appropriate.
4.  Add tests for representative duplicate execution attempts.

Constraints:

- Do not rely on frontend button disabling.
- Keep behavior explicit and auditable.

Acceptance criteria:

- duplicate critical execution is prevented
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  locking approach summary

**HARD-003 — Audit completeness enforcement**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded audit hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-003
- Title: Audit completeness enforcement

Context:

- KenTender must be audit-grade.
- Every material transition must leave enough trace to reconstruct what happened.

Task:  
Implement audit completeness enforcement.

Requirements:

1.  Identify material actions that must produce audit records/events.
2.  Add checks or helper utilities to ensure actions do not complete silently without audit creation.
3.  Cover at minimum:
    - approval actions
    - tender publication
    - bid submission
    - opening
    - evaluation submission
    - award approval
    - contract activation
    - acceptance decision
    - GRN posting
    - asset creation from GRN
4.  Add tests or verification helpers.

Constraints:

- Do not rely on developers remembering manually.
- Keep this enforceable.

Acceptance criteria:

- audit completeness helper/pattern exists
- representative flows are covered
- tests/verification pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  audited actions covered

**HARD-004 — State transition integrity enforcement**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded state integrity hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-004
- Title: State transition integrity enforcement

Context:

- Approval-controlled and workflow-controlled objects must not move into invalid states or skip required stages.

Task:  
Implement stricter state transition integrity enforcement.

Requirements:

1.  Ensure transitions are validated against allowed-from/allowed-to rules.
2.  Block skipped-stage transitions.
3.  Block direct mutation patterns that attempt to bypass service logic.
4.  Add representative tests across:
    - requisition
    - award
    - contract
    - acceptance

Constraints:

- Keep workflow engine authoritative.
- Do not let migration logic accidentally bypass runtime rules without explicit override mode.

Acceptance criteria:

- invalid transitions are blocked
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  integrity rules summary

**HARD-005 — Permission edge-case hardening**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded permission hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-005
- Title: Permission edge-case hardening

Context:

- Baseline permissions already exist, but edge cases remain dangerous:
    - role has report access but no row-level scope
    - user can open object through alternate route
    - assignment exists but is inactive
    - approval buttons hidden but backend still callable
    - mixed role users gain unintended privilege
    - broad admin-style access leaks into business workflows

Task:  
Harden permission edge cases.

Requirements:

1.  Review and tighten representative cases across:
    - requisition approvals
    - tender/bid access
    - evaluation assignment access
    - award approval
    - stores/assets scoped access
2.  Add backend tests for mixed-role and alternate-route cases.
3.  Document key edge-case patterns.

Constraints:

- Do not solve issues by broadening access.
- Keep the workbook as the source of intended behavior.

Acceptance criteria:

- representative edge cases are hardened
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  edge cases covered

**HARD-006 — Sealed/sensitive document access hardening**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded sensitive-data hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-006
- Title: Sealed/sensitive document access hardening

Context:

- KenTender handles sealed bids, sensitive evaluation materials, complaint evidence, and controlled contract/inspection evidence.

Task:  
Harden document/file access for sensitive content.

Requirements:

1.  Verify that sensitive content is only served through protected access paths.
2.  Remove or block raw/generic file access patterns where they bypass policy.
3.  Enforce sealed-bid restrictions pre-opening.
4.  Enforce assignment/sensitivity restrictions for evaluation and complaint evidence where applicable.
5.  Add tests for representative allow/deny and attempted bypass cases.

Constraints:

- Do not rely on UI hiding.
- Keep access backend-controlled and logged.

Acceptance criteria:

- sensitive file access is hardened
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  protected content classes covered

**HARD-007 — Report/query performance hardening**

**App:** cross-module  
**Priority:** High

**Cursor prompt**

Writing

You are implementing a bounded performance hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-007
- Title: Report/query performance hardening

Context:

- KenTender uses queue/report heavy workflows with row-level filtering and joins across procurement stages.
- Poor performance here will destroy usability.

Task:  
Harden performance of key reports/queries.

Minimum scope:

- Pending Requisition Approvals
- Planning Ready Requisitions
- Draft/Published Tenders
- My Assigned Evaluations
- Awards Pending Final Approval
- Goods Pending Receipt
- Pending Asset Registration

Requirements:

1.  Review query patterns for unnecessary joins or missing indexes.
2.  Add or recommend indexes where justified.
3.  Ensure row-level filtering does not make reports unusably slow.
4.  Add lightweight diagnostics/benchmarks for representative reports.

Constraints:

- Keep correctness first, then optimize.
- Do not weaken permission filters for speed.

Acceptance criteria:

- key reports reviewed
- representative improvements made
- diagnostics/notes provided

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  performance findings summary

**HARD-008 — Workflow/report observability and diagnostics**

**App:** kentender_core  
**Priority:** High

**Cursor prompt**

Writing

You are implementing a bounded operability hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-008
- Title: Workflow/report observability and diagnostics

Context:

- When workflows or permissions fail, developers and support staff need structured diagnostics instead of guesswork.

Task:  
Implement observability/diagnostic support for workflow and report issues.

Requirements:

1.  Add structured diagnostic output or helper tools for:
    - why a workflow action was denied
    - why a report row was filtered out
    - why a route/template was selected
2.  Keep outputs admin/developer-facing, not exposed broadly to end users.
3.  Add representative verification tests or examples.

Constraints:

- Do not leak sensitive internals to ordinary users.
- Keep diagnostics explainable and actionable.

Acceptance criteria:

- diagnostic support exists
- representative cases are covered

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  diagnostics supported

**HARD-009 — Template/configuration governance hardening**

**App:** kentender_core  
**Priority:** High

**Cursor prompt**

Writing

You are implementing a bounded configuration hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-009
- Title: Template/configuration governance hardening

Context:

- Planning and downstream process control now rely heavily on admin-configured templates and versions.
- Bad configuration can break the system as badly as bad code.

Task:  
Harden template/configuration governance.

Requirements:

1.  Add validation to prevent invalid template/version configurations.
2.  Detect overlapping or ambiguous active template version scopes where possible.
3.  Strengthen version approval/activation safeguards.
4.  Improve auditability of:
    - template selection
    - template overrides
    - version activation/deprecation
5.  Add tests for representative bad configurations.

Constraints:

- Keep admin UI-driven configuration, as decided.
- Do not force all logic back into code.

Acceptance criteria:

- configuration integrity is hardened
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  governance rules summary

**HARD-010 — Migration and patch safety framework**

**App:** cross-module  
**Priority:** High

**Cursor prompt**

Writing

You are implementing a bounded migration safety hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-010
- Title: Migration and patch safety framework

Context:

- KenTender will undergo schema and behavior changes over time.
- Migrations must not silently corrupt workflow states, permissions, or trace chains.

Task:  
Implement migration/patch safety patterns.

Requirements:

1.  Add developer-facing migration safety guidance.
2.  Create representative patch helpers/checks for:
    - status refactors
    - workflow data backfills
    - template version activation changes
3.  Add verification patterns for post-patch consistency checks.

Constraints:

- Do not assume migrations are always perfect.
- Keep recovery/review in mind.

Acceptance criteria:

- migration safety note exists
- representative helpers/checks exist

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  migration safeguards summary

**HARD-011 — End-to-end consistency checker**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded consistency-validation task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-011
- Title: End-to-end consistency checker

Context:

- KenTender is a linked-lifecycle system.
- Data may look fine locally while the end-to-end chain is broken.

Task:  
Implement an end-to-end consistency checker.

Requirements:

1.  Check representative chain integrity:  
    Requisition → Plan → Tender → Bid → Evaluation → Award → Contract → Acceptance → GRN → Asset
2.  Detect representative anomalies such as:
    - orphan downstream records
    - missing upstream links
    - inconsistent template propagation
    - GRN without acceptance
    - contract without approved award
3.  Provide a readable summary of failures.

Constraints:

- Keep checker useful for QA/UAT and admin diagnostics.
- Do not require UI to run.

Acceptance criteria:

- consistency checker exists
- representative anomalies are detected

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  anomalies checked

**HARD-012 — UAT stabilization toolkit**

**App:** cross-module  
**Priority:** High

**Cursor prompt**

Writing

You are implementing a bounded UAT hardening task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-012
- Title: UAT stabilization toolkit

Context:

- UAT fails when environments drift, seed data becomes inconsistent, or testers cannot verify expected states easily.

Task:  
Implement a UAT stabilization toolkit.

Requirements:

1.  Build on existing seed/reset/verify commands.
2.  Add concise verification summaries for the minimal golden scenario and key permission/workflow states.
3.  Add support for quickly checking:
    - key business IDs exist
    - reports open for expected roles
    - workflow states are correct
    - trace chain is intact
4.  Keep this tool practical for testers and developers.

Constraints:

- Do not build a heavy dashboard.
- Keep command-line or admin-tool oriented.

Acceptance criteria:

- toolkit exists
- representative checks are easy to run

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  checks supported

**HARD-013 — Production readiness checklist and release gates**

**App:** cross-module  
**Priority:** High

**Cursor prompt**

Writing

You are implementing a bounded production-readiness governance task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-013
- Title: Production readiness checklist and release gates

Context:

- KenTender needs explicit go-live gates, not vague confidence.

Task:  
Create a production-readiness checklist and release gates artifact.

Requirements:

1.  Cover at minimum:
    - workflow integrity
    - permissions
    - report correctness
    - audit completeness
    - seed/reset/verify reliability
    - migration safety
    - performance of key reports
    - backup/recovery expectations
2.  Make it developer/tester/release-manager usable.
3.  Keep it concrete, not aspirational.

Constraints:

- Do not treat “tests pass” as the only release gate.
- Keep the checklist short enough to be used.

Acceptance criteria:

- production readiness artifact exists
- release gates are explicit

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  release gates summary

**HARD-014 — Regression and chaos-style failure test suite**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded failure-hardening test task in a modular Frappe-based system called KenTender.

Story:

- ID: HARD-014
- Title: Regression and chaos-style failure test suite

Context:

- Production systems fail in ugly ways, including retries, partial crashes, permission drift, and configuration mistakes.

Task:  
Implement a regression/failure-oriented hardening test suite.

Minimum coverage:

1.  duplicate critical action attempts
2.  partial failure during side-effect-heavy transitions
3.  permission bypass attempts
4.  sealed document access bypass attempts
5.  bad template configuration detection
6.  consistency checker detecting anomalies
7.  report behavior under incorrect/missing scope conditions
8.  post-migration consistency verification

Constraints:

- keep tests practical and maintainable
- focus on backend robustness more than UI cosmetics

Acceptance criteria:

- hardening/failure test suite exists
- representative failure modes are covered

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  failure scenarios covered

**Recommended first batch**

Start with this batch first:

1.  HARD-003
2.  HARD-004
3.  HARD-005
4.  HARD-011
5.  HARD-012

That gives you the highest near-term value:

- audit certainty
- transition integrity
- permission hardening
- end-to-end validation
- UAT stability

**What to review after each story**

After each Cursor run, ask:

- Can this still be bypassed by a direct save?
- Can a user still see data they should not?
- Can a material action complete without audit?
- Can a downstream record exist without a valid upstream chain?
- Can testers verify this without guessing?

If the answer is yes to any of those, hardening is not done.

**Final blunt assessment**

At this stage, feature work is no longer the main risk.

The main risk is **false confidence**:

- the system appears complete
- but edge cases break trust, compliance, or traceability

This hardening pack is what turns KenTender from:

- “architecturally strong”  
    into
- **operationally trustworthy**

**Best next move**

You now have the full build path.

The most useful next artifact is a **Master Delivery Roadmap** that organizes everything we built into:

- architecture streams
- implementation waves
- dependency order
- UAT milestones
- release gates

That would give you one master execution view instead of many separate packs.