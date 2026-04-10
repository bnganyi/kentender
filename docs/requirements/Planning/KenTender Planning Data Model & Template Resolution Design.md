# KenTender Planning Data Model + Template Resolution Design (v1)

**1\. Design Objective**

Planning must:

- transform approved requisitions into executable procurement units
- configure the **entire downstream lifecycle** (tender → evaluation → award → contract → acceptance)
- enforce consistency and prevent ad hoc procurement behavior

👉 A Plan Item is not just data — it is a **process configuration object**

**2\. Core Entities**

**2.1 Procurement Plan (Procurement Plan)**

**Purpose**

- Container for a planning period (annual, quarterly, special)

**Key fields**

- plan_code
- entity
- planning_period_start
- planning_period_end
- status (workflow-driven)
- is_active

**2.2 Procurement Plan Item (Procurement Plan Item)**

**Purpose**

👉 This is the **most important object in planning**

It defines:

- WHAT will be procured
- HOW it will be procured
- HOW the entire downstream process behaves

**3\. Procurement Plan Item — Full Field Model**

**3.1 Source linkage**

- linked_requisitions (child table)
    - requisition_id
    - requisition_line_id
    - allocated_quantity

**3.2 Demand tracking (mandatory)**

- total_requested_quantity
- total_allocated_quantity
- remaining_quantity

**3.3 Financials**

- estimated_unit_cost
- estimated_total_cost
- currency
- funding_source
- budget_line

**3.4 Procurement drivers (CRITICAL)**

These fields **drive everything downstream**:

- procurement_method
- complexity_classification
- risk_level
- category (goods / works / services)
- sector (health, infrastructure, etc.)
- requires_professional_opinion (bool)
- requires_committee (bool)

**3.5 Template resolution output**

- procurement_template (resolved, not user-entered)
- evaluation_template
- acceptance_template
- approval_template

👉 These should be system-derived

**3.6 Structural configuration**

- packaging_strategy
    - single lot
    - multi-lot
    - framework
- number_of_lots

**3.7 Timeline**

- planned_procurement_start
- planned_publication_date
- planned_award_date
- planned_contract_start

**3.8 Constraints / compliance**

- eligibility_constraints
- special_requirements
- regulatory_flags

**3.9 Strategic context**

- strategic_objective
- priority_level

**3.10 State**

- workflow_state (authoritative)
- status (derived, optional)

**4\. Supporting Entities**

**4.1 Plan Item Requisition Link (child table)**

Tracks partial allocation.

Fields:

- requisition_id
- requisition_line_id
- allocated_quantity

**4.2 Procurement Template**

Defines the process blueprint.

Fields:

- template_code
- template_name
- procurement_method
- complexity_classification
- category
- evaluation_template
- acceptance_template
- approval_template

**4.3 Evaluation Template**

Defines:

- scoring model
- weighting
- stages

**4.4 Acceptance Template**

Defines:

- acceptance workflow
- whether:
    - inspector only
    - expert required
    - committee required
    - lab testing required

**4.5 Approval Template**

Defines:

- approval chain
- thresholds
- actors

**5\. Template Resolution Engine**

This is the heart of the system.

**5.1 When it runs**

Template resolution must occur:

👉 when Plan Item is created or updated  
👉 before Plan Item approval  
👉 before Tender creation

**5.2 Inputs**

From Plan Item:

- procurement_method
- complexity_classification
- category
- estimated_total_cost
- risk_level
- special flags

**5.3 Resolution logic (deterministic)**

SELECT template  
WHERE  
method = procurement_method  
AND category = category  
AND complexity = complexity_classification  
AND threshold_min <= estimated_total_cost <= threshold_max  
AND (sector match OR generic)  
AND active = true  
ORDER BY priority DESC  
LIMIT 1

**5.4 Output**

System sets:

- procurement_template
- evaluation_template
- acceptance_template
- approval_template

**5.5 Failure condition**

If no template found:

❌ Plan Item cannot be approved  
❌ Tender cannot be created

**6\. Planning Workflow**

Draft → Submitted → Approved → Active

**6.1 Draft**

- procurement defines plan items
- grouping / splitting happens here
- template resolution must already work

**6.2 Submitted**

- validation phase
- system checks:
    - quantity constraints
    - budget consistency
    - template resolution

**6.3 Approved**

- governance approval
- plan locked for structural changes

**6.4 Active**

👉 This is the critical transition

Effects:

- plan items become tenderable
- procurement can generate tenders
- downstream templates become binding

**7\. Enforcement Rules**

**7.1 Quantity enforcement**

sum(allocated_quantity) ≤ requested_quantity

**7.2 No orphan plan items**

Must:

- link to requisition  
    OR
- be explicitly marked strategic

**7.3 Template must exist**

Cannot proceed without template resolution

**7.4 No tender without plan item**

Absolute rule

**7.5 No method change after activation**

**7.6 Complexity must propagate**

Must affect:

- evaluation
- acceptance
- approval

**8\. Downstream Impact (VERY IMPORTANT)**

**Planning controls:**

**Tender**

- structure
- method
- visibility

**Evaluation**

- scoring model
- stages
- roles

**Award**

- approval thresholds

**Contract**

- structure and obligations

**Acceptance**

- workflow complexity (your earlier point)

**9\. Edge Case Handling**

**Case 1 — Mixed complexity grouping**

👉 DO NOT allow silently

Options:

- block grouping
- or escalate to highest complexity

**Case 2 — Budget change after planning**

- require re-validation
- may require re-approval

**Case 3 — Partial planning**

- track remaining quantity
- allow future plan items

**Case 4 — Template change**

- allowed only before activation
- after activation → controlled revision only

**10\. Developer Implementation Notes**

**Must implement services:**

- create_plan_item_from_requisition()
- allocate_requisition_quantity()
- resolve_procurement_template()
- validate_plan_item()
- submit_plan()
- approve_plan()
- activate_plan()

**Must NOT allow:**

plan_item.procurement_template = "manual"  
plan_item.save()

Templates must be resolved, not manually set.

**11\. What this design solves**

- eliminates manual procurement variation
- ensures consistency across tenders
- ties planning directly to execution
- enforces auditability
- supports complex real-world procurement cases

**12\. What you should challenge next (important)**

Before building:

1.  Should templates be configurable by admin UI or code-controlled?
2.  How do you version templates?
3.  Can templates change mid-year?
4.  How strict should template matching be?
5.  Should overrides be allowed? If yes, who approves?
6.  How do you audit template selection decisions?

**My blunt conclusion**

This is the moment your system transitions from:

👉 “record-keeping system”  
to  
👉 “policy-enforcing procurement platform”

If you implement this properly:

- procurement becomes consistent
- audit becomes strong
- downstream modules become predictable

If you don’t:

- planning becomes a spreadsheet clone
- everything downstream becomes manual

**Next best step**

You now need:

👉 **Cursor Implementation Pack for Planning + Template Engine**

This will translate this into:

- DocTypes
- services
- validation logic
- resolver engine