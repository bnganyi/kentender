# KenTender Planning and Template Cursor Implementation Pack

**Planning + Template Engine (v1)**

**Implementation Strategy (read this first)**

You are building **two tightly coupled systems**:

**1\. Planning Engine**

- Plan
- Plan Item
- Requisition allocation
- validation rules

**2\. Template Engine**

- Template + versioning
- resolution logic
- override workflow
- audit trail

**Critical rule**

Planning **must not work** without template resolution  
Templates **must not exist** without version control

**Delivery Order (STRICT)**

Do NOT reorder:

1.  PLAN-001 — Planning domain models
2.  PLAN-002 — Requisition allocation engine
3.  PLAN-003 — Template + Template Version models
4.  PLAN-004 — Template version workflow
5.  PLAN-005 — Template resolution engine
6.  PLAN-006 — Template scoring engine
7.  PLAN-007 — Template audit logging
8.  PLAN-008 — Template override workflow
9.  PLAN-009 — Plan Item validation service
10. PLAN-010 — Plan workflow integration
11. PLAN-011 — Plan activation + downstream locking
12. PLAN-012 — Tender creation from Plan Item
13. PLAN-013 — Planning reports + queues
14. PLAN-014 — Planning regression test suite

**PLAN-001 — Planning domain models**

**App:** kentender_procurement

**Cursor prompt**

Writing

You are implementing planning domain models in a modular Frappe-based system called KenTender.

Story:

- ID: PLAN-001
- Title: Planning domain models

Task:  
Implement the core planning DocTypes.

Models to create:

1.  Procurement Plan  
    Fields:

- plan_code
- entity
- planning_period_start
- planning_period_end
- workflow_state
- is_active

1.  Procurement Plan Item  
    Fields:

- parent_plan
- category
- sector
- procurement_method
- complexity_classification
- risk_level
- estimated_total_cost
- funding_source
- packaging_strategy
- planned_procurement_start
- planned_publication_date
- workflow_state

1.  Plan Item Requisition Link (child table)  
    Fields:

- parent_plan_item
- requisition_id
- requisition_line_id
- allocated_quantity

Requirements:

- keep fields clean and minimal but extensible
- do not implement full validation yet
- ensure naming and relationships are correct

Acceptance:

- models exist
- relations valid
- basic creation works

Output:

- files changed
- assumptions
- open questions

**PLAN-002 — Requisition allocation engine**

**App:** kentender_procurement

**Cursor prompt**

Writing

You are implementing requisition allocation logic.

Story:

- ID: PLAN-002
- Title: Requisition allocation engine

Task:  
Implement allocation tracking between requisitions and plan items.

Requirements:

1.  Track:
    - requested_quantity
    - allocated_quantity
    - remaining_quantity
2.  Enforce:  
    sum(allocated_quantity) ≤ requested_quantity
3.  Provide service:
    - allocate_requisition_quantity(plan_item, requisition_line, qty)
4.  Prevent:
    - over-allocation
    - duplicate allocation without explicit intention

Add tests for:

- full allocation
- partial allocation
- over-allocation rejection

Output:

- files changed
- assumptions
- edge cases

**PLAN-003 — Template + Template Version models**

**App:** kentender_core

**Cursor prompt**

Writing

You are implementing template models.

Story:

- ID: PLAN-003
- Title: Template + Template Version models

Task:  
Create:

1.  Procurement Template (master)  
    Fields:

- template_code
- template_name
- category
- is_active

1.  Procurement Template Version  
    Fields:

- parent_template
- version_no
- procurement_method
- complexity_classification
- threshold_min
- threshold_max
- sector
- risk_level
- evaluation_template
- acceptance_template
- approval_template
- effective_from
- effective_to
- approval_status

Requirements:

- version holds behavior
- template is identity only
- no resolution logic yet

Acceptance:

- models exist
- relations valid

Output:

- files changed
- assumptions

**PLAN-004 — Template version workflow**

**App:** kentender_core

**Cursor prompt**

Writing

Implement workflow for template version lifecycle.

Story:

- ID: PLAN-004

States:  
Draft → Pending Approval → Approved → Active → Deprecated

Requirements:

- only approved versions can be active
- only one active version per rule scope
- version activation respects effective dates
- integrate with workflow engine

Add tests:

- cannot activate unapproved version
- cannot have multiple active versions

Output:

- workflow config
- enforcement logic

**PLAN-005 — Template resolution engine**

**App:** kentender_core

**Cursor prompt**

Writing

Implement template resolution engine.

Story:

- ID: PLAN-005

Task:  
Create service:

- resolve_template(plan_item)

Requirements:

1.  fetch candidate template versions
2.  filter by:
    - procurement_method
    - category
3.  return candidates for scoring
4.  fail if none found

No scoring yet.

Output:

- resolver skeleton
- tests

**PLAN-006 — Template scoring engine**

**App:** kentender_core

**Cursor prompt**

Writing

Implement template scoring.

Story:

- ID: PLAN-006

Task:  
Score template candidates.

Weights:

- method (high)
- category (high)
- complexity (high)
- threshold (medium)
- sector (medium)
- risk (low)

Requirements:

- return best match
- flag mismatches
- return match_quality (Exact / Partial)

Output:

- scoring function
- test cases

**PLAN-007 — Template audit logging**

**App:** kentender_core

**Cursor prompt**

Writing

Implement template selection audit.

Story:

- ID: PLAN-007

Task:  
Log:

- selected template version
- score
- mismatches

Model:  
Template Selection Log:

- object_type
- object_id
- template_version
- match_quality
- mismatch_details

Requirements:

- auto-create on resolution
- immutable

Output:

- model + logging service

**PLAN-008 — Template override workflow**

**App:** kentender_procurement

**Cursor prompt**

Writing

Implement template override workflow.

Story:

- ID: PLAN-008

Task:  
Allow override with Head of Procurement approval.

Fields on Plan Item:

- system_selected_template
- override_requested
- override_reason
- override_template
- override_status
- override_approved_by

Workflow:  
Requested → Pending Head of Procurement → Approved/Rejected

Rules:

- cannot proceed if pending
- must log override

Output:

- override workflow
- validation logic

**PLAN-009 — Plan Item validation service**

**App:** kentender_procurement

**Cursor prompt**

Writing

Implement plan item validation.

Story:

- ID: PLAN-009

Validate:

- quantity constraints
- template resolved
- no orphan items
- no invalid grouping
- budget consistency

Block submission if invalid.

Output:

- validation service

**PLAN-010 — Plan workflow integration**

**App:** kentender_procurement

**Cursor prompt**

Writing

Integrate plan with workflow engine.

Story:

- ID: PLAN-010

States:  
Draft → Submitted → Approved → Active

Rules:

- submission validates items
- approval locks structure
- activation enables tender creation

Output:

- workflow config
- services

**PLAN-011 — Plan activation + downstream locking**

**App:** kentender_procurement

**Cursor prompt**

Writing

Implement plan activation effects.

Story:

- ID: PLAN-011

On activation:

- lock template selection
- lock method
- mark items as tenderable

Prevent:

- structural edits post-activation

Output:

- activation service

**PLAN-012 — Tender creation from Plan Item**

**App:** kentender_procurement

**Cursor prompt**

Writing

Implement tender creation from plan item.

Story:

- ID: PLAN-012

Requirements:

- must use plan item
- must inherit:
    - method
    - templates
    - structure

Block:

- manual tender creation without plan item

Output:

- creation service

**PLAN-013 — Planning reports + queues**

**App:** kentender_procurement

**Cursor prompt**

Writing

Implement planning reports.

Story:

- ID: PLAN-013

Reports:

- Planning Ready Requisitions
- Draft Plans
- Plan Items Pending Approval
- Active Plan Items

Use workflow_state filters.

Output:

- reports

**PLAN-014 — Planning regression test suite**

**App:** cross-module

**Cursor prompt**

Writing

Implement planning regression tests.

Story:

- ID: PLAN-014

Test:

- allocation logic
- template resolution
- override workflow
- plan validation
- activation rules
- tender creation

Output:

- test suite

**What to review after each step**

- Is planning still traceable to requisitions?
- Is template resolution mandatory and auditable?
- Can users bypass planning? (must be NO)
- Are overrides controlled?
- Does activation lock behavior correctly?

**My blunt advice**

Start with:

👉 PLAN-002 (allocation)  
👉 PLAN-006 (scoring)  
👉 PLAN-008 (override)

These are your highest-risk areas.

**Next logical phase after this**

Once planning is stable:

👉 **Tender + Evaluation Implementation Pack (template-driven)**

That’s where your template decisions really get tested.