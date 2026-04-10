# KenTender Cursor Refactor Pack — Status Standardization

**Tracked checklist:** [STAT Implementation Tracker](STAT%20Implementation%20Tracker.md).

**Refactor objective**

Standardize status handling across all approval-controlled DocTypes so that:

- docstatus is used only for Frappe lifecycle
- workflow_state is the only authoritative business state
- status is derived and read-only, only if still needed
- duplicate fields like approval_status are removed or converted to derived read-only
- reports and permissions filter on workflow_state
- users cannot directly edit any approval-controlled state fields

**Delivery order**

Run these in order:

1.  STAT-001 — create status standard and field classification framework
2.  STAT-002 — audit current DocTypes for status field usage
3.  STAT-003 — implement shared workflow_state → status mapping helpers
4.  STAT-004 — enforce read-only protection for approval-controlled fields
5.  STAT-005 — refactor Purchase Requisition status model
6.  STAT-006 — refactor Procurement Plan and Plan Item status model
7.  STAT-007 — refactor Tender and Bid status model
8.  STAT-008 — refactor Evaluation and Award status model
9.  STAT-009 — refactor Contract and Acceptance status model
10. STAT-010 — refactor Stores / GRN / Assets status model
11. STAT-011 — update reports and filters to use workflow_state
12. STAT-012 — update forms/UI labels and visibility
13. STAT-013 — migration/patch plan for existing records
14. STAT-014 — regression test suite for status consistency

**Global refactor rules for Cursor**

These apply to all stories:

- do not use docstatus for business-stage meaning
- do not keep two editable fields that represent the same state
- do not leave report filters on deprecated status fields
- do not break existing routes silently; use migration-safe patches
- keep workflow_state authoritative
- keep status only if it provides distinct reporting value and is strictly derived
- remove approval_status unless there is a strong, documented reason to retain it as a derived summary

**STAT-001 — Create status standard and classification framework**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded refactor-foundation task in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-001
- Title: Create status standard and classification framework

Context:

- KenTender needs a single system-wide status model:
    - docstatus = Frappe lifecycle only
    - workflow_state = authoritative business state
    - status = optional derived summary only
- Many current DocTypes contain confusing or duplicated fields such as:
    - status
    - approval_status
    - workflow_state
- This refactor must standardize how these are interpreted.

Task:  
Create the status standard and field-classification framework.

Requirements:

1.  Add a developer-facing status standard note explaining:
    - the 3-layer model
    - one field = one meaning
    - no direct user mutation of approval-controlled fields
2.  Add a reusable classification pattern for fields:
    - lifecycle field
    - authoritative workflow field
    - derived summary field
    - deprecated/duplicate field
3.  Place this in a reusable core location.

Constraints:

- Do not refactor all DocTypes in this story.
- Keep this as the foundation for later status cleanup.

Acceptance criteria:

- status standard note exists
- classification framework exists
- later refactor stories have clear guidance

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  classification model summary

**STAT-002 — Audit current DocTypes for status field usage**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded audit/refactor-planning task in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-002
- Title: Audit current DocTypes for status field usage

Context:

- The system currently contains multiple status-like fields on many DocTypes.
- Before refactoring, we need a clear inventory of how they are used today.

Task:  
Audit approval-controlled and operational DocTypes for status field usage.

For each relevant DocType, identify:

- whether it has workflow_state
- whether it has status
- whether it has approval_status
- whether those fields are editable
- whether reports currently filter on them
- whether field meanings overlap/conflict

Priority DocTypes include:

- Purchase Requisition
- Procurement Plan
- Procurement Plan Item
- Tender
- Bid Submission
- Evaluation Session
- Evaluation Report
- Award Decision
- Contract
- Acceptance Record
- Goods Receipt Note
- Asset

Requirements:

1.  Produce a developer-facing audit artifact in the repo.
2.  Mark each field as:
    - keep authoritative
    - keep derived
    - deprecate/remove
    - investigate
3.  Keep the output concrete and implementation-oriented.

Constraints:

- Do not perform all refactors here.
- Do not hand-wave unclear field meanings; explicitly flag them.

Acceptance criteria:

- audit exists
- priority DocTypes are classified
- later refactor work is clearly informed

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  DocType audit summary

**STAT-003 — Implement shared workflow_state to status mapping helpers**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded shared-helper task in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-003
- Title: Implement shared workflow_state to status mapping helpers

Context:

- If status remains on certain DocTypes, it must be derived from workflow_state.
- This mapping must not be scattered across client scripts or ad hoc methods.

Task:  
Implement reusable helpers for deriving status from workflow_state.

Requirements:

1.  Provide a mapping framework that allows per-DocType workflow_state-to-status mapping.
2.  Keep the mapping readable and centrally defined.
3.  Add tests for representative mappings such as:
    - requisition
    - award
    - contract
4.  Ensure the framework supports cases where status may be intentionally omitted.

Constraints:

- Do not refactor all DocTypes here.
- Do not make status authoritative.

Acceptance criteria:

- shared mapping helper exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  supported mapping pattern

**STAT-004 — Enforce read-only protection for approval-controlled state fields**

**App:** kentender_core  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded state-safety refactor task in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-004
- Title: Enforce read-only protection for approval-controlled state fields

Context:

- Approval-controlled fields must not be directly editable by users.
- This includes:
    - workflow_state
    - status where derived
    - approval_status where still present temporarily
    - related route/current-step control fields

Task:  
Enforce read-only and backend-protected behavior for approval-controlled state fields.

Requirements:

1.  Build on the existing approval-controlled field protection mechanism.
2.  Ensure these fields cannot be directly mutated by normal saves/import-like casual flows.
3.  Keep workflow-service-authorized changes functioning.
4.  Add tests for blocked direct mutation and allowed engine-driven mutation.

Constraints:

- Do not depend only on form read-only settings.
- Keep this backend-enforced.

Acceptance criteria:

- state fields are protected
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  protection summary

**STAT-005 — Refactor Purchase Requisition status model**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded status refactor for Purchase Requisition in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-005
- Title: Refactor Purchase Requisition status model

Context:

- Purchase Requisition currently shows confusing overlapping state fields.
- Target standard:
    - docstatus = Draft/Submitted/Cancelled
    - workflow_state = authoritative business state
    - status = optional derived summary only
    - approval_status should be removed or converted to derived-only if absolutely needed

Task:  
Refactor the Purchase Requisition status model to the system standard.

Requirements:

1.  Identify and classify current requisition status-related fields.
2.  Make workflow_state the only authoritative business stage field.
3.  Convert status to derived-only if retained.
4.  Remove or deprecate approval_status unless a strong implementation need remains.
5.  Update service logic to use workflow_state as source of truth.
6.  Add tests confirming:
    - direct edits blocked
    - derived mapping works
    - workflow actions still function

Constraints:

- Do not silently preserve duplicate meaning in multiple editable fields.
- Keep migration-safe behavior for existing records.

Acceptance criteria:

- requisition status model is standardized
- duplicate semantic overlap is removed
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  final requisition field behavior summary

**STAT-006 — Refactor Procurement Plan and Plan Item status model**

**App:** kentender_procurement  
**Priority:** High

**Cursor prompt**

Writing

Implement status-model refactor for Procurement Plan and Procurement Plan Item.

Requirements:

- workflow_state becomes authoritative business state
- status becomes derived-only if retained
- remove/deprecate overlapping approval-style fields
- update services, validations, and tests accordingly
- document final field behavior

Constraints:

- preserve reporting needs without preserving semantic duplication

**STAT-007 — Refactor Tender and Bid status model**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement status-model refactor for Tender and Bid Submission.

Requirements:

1.  Tender:
    - workflow_state authoritative for business stage
    - status derived if retained
2.  Bid Submission:
    - use clear stage model such as Draft / Submitted / Opened / Withdrawn
    - avoid overlapping editable fields that duplicate sealing/submission meaning
3.  Update tender/bid services and tests accordingly.
4.  Ensure reports use authoritative state fields.

Constraints:

- do not weaken sealed-content rules
- keep state model clean and auditable

**STAT-008 — Refactor Evaluation and Award status model**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement status-model refactor for Evaluation Session, Evaluation Report, and Award Decision.

Requirements:

- workflow_state authoritative
- status derived only if retained
- remove/deprecate overlapping approval status fields
- keep report/award progression readable but non-duplicative
- update workflow engine integration and tests

Constraints:

- preserve SoD and approval audit behavior

**STAT-009 — Refactor Contract and Acceptance status model**

**App:** kentender_procurement  
**Priority:** Critical

**Cursor prompt**

Writing

Implement status-model refactor for Contract and Acceptance Record.

Requirements:

1.  Contract:
    - clean distinction between doc lifecycle, business stage, and optional summary
2.  Acceptance:
    - stable lifecycle states with authoritative workflow_state
    - no duplicate approval fields that drift
3.  Update dynamic workflow integration and tests

Constraints:

- preserve GRN eligibility side-effect logic
- do not create ambiguous “accepted vs approved vs completed” overlaps

**STAT-010 — Refactor Stores / GRN / Assets status model**

**App:** downstream ops apps  
**Priority:** High

**Cursor prompt**

Writing

Implement status-model refactor for Goods Receipt Note and Asset.

Requirements:

- keep state fields minimal and non-overlapping
- use authoritative workflow/business state where applicable
- avoid separate editable fields that mean the same thing
- update services and tests accordingly

Constraints:

- keep stores/assets practical and not over-engineered

**STAT-011 — Update reports and filters to use workflow_state**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded report consistency refactor in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-011
- Title: Update reports and filters to use workflow_state

Context:

- Reports must not rely on deprecated or ambiguous status fields.
- workflow_state is now authoritative for business-stage filtering.

Task:  
Refactor key reports and queues to use authoritative state fields.

Minimum scope:

- My Requisitions
- Pending Requisition Approvals
- Planning Ready Requisitions
- Planning Queue
- Draft Tenders
- Published Tenders
- My Assigned Evaluations
- Awards Pending Final Approval
- Scheduled Inspections
- Goods Pending Receipt
- Pending Asset Registration

Requirements:

1.  Replace ambiguous status / approval_status filters with workflow_state where appropriate.
2.  Keep row-level access logic intact.
3.  Add tests or verification fixtures for representative report behavior.

Constraints:

- do not change report intent accidentally
- keep filters explicit and readable

**STAT-012 — Update forms and UI labels to match the standard**

**App:** cross-module  
**Priority:** High

**Cursor prompt**

Writing

You are implementing a bounded UI consistency refactor in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-012
- Title: Update forms and UI labels to match the standard

Context:

- Current forms show confusing overlapping status fields.
- The UI must reflect the standardized model clearly.

Task:  
Refactor forms and UI presentation for status fields.

Requirements:

1.  Show workflow_state as the primary visible business-stage field.
2.  Keep derived status hidden or secondary if retained.
3.  Do not present multiple editable dropdowns that represent the same meaning.
4.  Improve field labels where needed, for example:
    - Lifecycle (system)
    - Stage (business)
    - Overall Status (derived) only if truly needed
5.  Update representative forms first:
    - Purchase Requisition
    - Tender
    - Award
    - Contract
    - Acceptance

Constraints:

- do not rely only on UI hiding for logic correctness
- keep backend rules authoritative

**STAT-013 — Implement migration/patch plan for existing records**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded migration/refactor safety task in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-013
- Title: Implement migration/patch plan for existing records

Context:

- Existing records may contain overlapping or inconsistent status values.
- The status-standardization refactor must not leave old records in ambiguous states.

Task:  
Implement migration/patch support for status standardization.

Requirements:

1.  Add a patch or migration plan to:
    - backfill derived status from workflow_state where retained
    - identify or fix inconsistent state combinations
    - mark deprecated fields safely
2.  Add a developer-facing migration note.
3.  Add tests or verification for representative migration cases.

Constraints:

- do not silently discard important state history
- keep migration logic explicit and reviewable

**STAT-014 — Implement regression test suite for status consistency**

**App:** cross-module  
**Priority:** Critical

**Cursor prompt**

Writing

You are implementing a bounded regression test task in a modular Frappe-based system called KenTender.

Story:

- ID: STAT-014
- Title: Implement regression test suite for status consistency

Context:

- KenTender needs regression coverage to ensure the status model stays standardized over time.

Task:  
Implement a status-consistency regression suite.

Minimum coverage:

1.  workflow_state is authoritative for business stage
2.  derived status matches mapping where retained
3.  direct mutation of approval-controlled fields is blocked
4.  deprecated/duplicate fields are not driving business logic
5.  reports use authoritative state fields
6.  representative DocTypes remain functional:
    - Purchase Requisition
    - Tender
    - Award
    - Contract
    - Acceptance

Constraints:

- do not rely only on UI tests
- keep the suite focused on backend truth and report correctness

**Recommended first execution batch**

Start with this batch first:

1.  STAT-001
2.  STAT-002
3.  STAT-004
4.  STAT-005
5.  STAT-011
6.  STAT-012

That batch will:

- define the standard
- audit what exists
- stop direct mutation
- fix the most visible confusion on PR
- align reports
- clean up forms

**What developers should verify after each story**

After each run, check:

- Is workflow_state now the real source of truth?
- Is status only derived or removed?
- Is approval_status removed/deprecated where redundant?
- Are users blocked from direct state edits?
- Do reports still return correct business-stage records?
- Is the UI less confusing than before?

**Strong recommendation**

Do **Purchase Requisition first**, exactly as you noticed.  
It is the best canary for this refactor because it already visibly shows the confusion.

After PR is clean, developers will understand the pattern and can apply it consistently elsewhere.