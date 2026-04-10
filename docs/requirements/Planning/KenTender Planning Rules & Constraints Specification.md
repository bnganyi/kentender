# KenTender Planning Rules & Constraints Specification (v1)

This defines:

- how requisitions become plan items
- how planning decisions affect downstream stages
- how “invisible” fields (method, complexity, etc.) actually drive the system

**1\. Requisition → Plan Mapping (Grouping / Splitting)**

**1.1 Allowed relationships**

You must support **both directions**:

**A. One requisition → multiple plan items (split)**

Example:

- 100 ultrasound machines
- 60 now (urgent)
- 40 later

**B. Multiple requisitions → one plan item (grouping)**

Example:

- 10 hospitals requesting similar equipment
- consolidated national tender

**1.2 Partial quantity planning (THIS IS CRITICAL)**

You need an explicit tracking model.

**Required fields**

On **Requisition Line**:

- requested_quantity
- planned_quantity (aggregated from plan links)
- remaining_quantity

On **Plan Item Link Table**:

- requisition_id
- requisition_line_id
- allocated_quantity

**1.3 Rules**

**Rule 1 — Cannot over-plan**

sum(allocated_quantity) ≤ requested_quantity

**Rule 2 — Remaining quantity must be visible**

remaining_quantity = requested_quantity - allocated_quantity

**Rule 3 — Planning must be explicit**

You cannot silently assume:

“entire requisition is planned”

System must show:

- Fully planned
- Partially planned
- Not planned

**1.4 Effects of splitting**

When you split a requisition:

- you create **multiple procurement timelines**
- you may use **different procurement methods**
- you may assign **different priorities**

This is not just quantity — it’s **process divergence**

**1.5 Effects of grouping**

When you group:

- you unify:
    - procurement method
    - timeline
    - evaluation criteria
- you may increase:
    - contract value
    - complexity
    - approval thresholds

**2\. Procurement Method — Must Become a System Driver**

You’re absolutely right: right now it’s just a label.

That’s wrong.

👉 It must drive behavior across the system.

**2.1 Procurement Method is NOT informational**

It must control:

**A. Tender structure**

- Open Tender → public advert + full process
- RFQ → limited supplier invite
- Direct → no competition
- Framework → call-off rules

**B. Supplier eligibility**

- open → all eligible
- restricted → prequalified only
- direct → specific supplier

**C. Workflow differences**

Example:

| **Method** | **Opening** | **Evaluation** | **Approval** |
| --- | --- | --- | --- |
| Open | Formal opening session | Full scoring | Full approval |
| RFQ | Simplified opening | Simple evaluation | Faster approval |
| Direct | No opening | justification-based | high scrutiny |

**D. Document requirements**

- Open → full tender dossier
- RFQ → simplified
- Direct → justification memo

**E. Approval thresholds**

- Direct procurement → stricter approval
- Open tender → standard approval

**2.2 Enforcement rule**

❗ You must NOT allow tender creation without a method  
❗ You must NOT allow method change after tender publication

**3\. Template-Driven Procurement Processes (You were right — we hadn’t formalized this)**

This is where your system becomes powerful.

**3.1 What templates are**

Templates define:

- required documents
- workflow steps
- evaluation model
- approval path
- compliance requirements

**3.2 Planning must select a template**

Each Plan Item must resolve:

procurement_method + complexity + category → template

**3.3 Example templates**

**Template A — Open Tender (Standard Goods)**

- public advert
- technical + financial evaluation
- standard approval

**Template B — Open Tender (Complex Equipment)**

- technical compliance stage
- expert evaluation
- weighted scoring
- stricter acceptance

**Template C — RFQ**

- limited invite
- simplified evaluation

**Template D — Direct Procurement**

- justification
- approval-heavy
- no opening

**3.4 Where templates are used downstream**

Templates must drive:

- Tender creation
- Bid structure
- Evaluation scoring model
- Approval workflow
- Acceptance workflow

**3.5 Strong rule**

Planning must resolve the template, not procurement later

Otherwise:  
👉 procurement becomes inconsistent and manual

**4\. Complexity, Risk, and Special Requirements (You’re right — this was under-specified)**

These fields are NOT metadata.

They must drive system behavior.

**4.1 Complexity Classification**

**Example values**

- Low
- Medium
- High
- Specialized

**4.2 What complexity controls**

**A. Evaluation model**

- Low → simple price comparison
- High → technical scoring + weighting

**B. Approval workflow**

- High complexity → more approval steps

**C. Acceptance workflow**

This is key:

| **Complexity** | **Acceptance** |
| --- | --- |
| Low | Inspector only |
| Medium | Inspector + technical check |
| High | Inspector + expert + committee |
| Specialized | Lab/test + committee |

👉 This ties directly to your earlier observation

**4.3 Risk Level**

**Drives:**

- approval thresholds
- audit attention
- complaint sensitivity
- possible additional review steps

**4.4 Special Requirements**

**Examples:**

- regulatory approval required
- environmental clearance
- medical certification
- safety compliance

**Effects:**

- blocks tender publication if missing
- adds evaluation criteria
- affects acceptance requirements

**4.5 Eligibility Constraints**

**Drives:**

- supplier filtering
- prequalification rules
- participation rules

**4.6 Strategic Objective Link**

**Why this matters**

This is not just reporting.

It enables:

- policy alignment tracking
- audit justification
- prioritization logic

**5\. Updated Plan Item (Now Properly Defined)**

Your Plan Item must now include:

**Core fields**

- linked requisitions
- allocated quantities
- estimated value
- funding source

**Process drivers (NEW — critical)**

- procurement method
- **procurement template (resolved)**
- complexity classification
- risk level
- special requirements
- eligibility constraints

**Structure**

- packaging / lotting model

**Timeline**

- planned start
- planned publication

**6\. Enforcement Rules (Non-negotiable)**

**Rule 1 — Cannot create tender without Plan Item**

No bypass.

**Rule 2 — Cannot create Plan Item without requisition (unless strategic)**

Must be explicit if strategic.

**Rule 3 — Cannot exceed requisition quantity or budget**

**Rule 4 — Template must be resolved before tender creation**

**Rule 5 — Procurement method must drive template**

**Rule 6 — Complexity must influence:**

- evaluation
- acceptance
- approval

**7\. New Hard Questions (you must answer these before building)**

1.  Can one Plan Item produce multiple tenders?
2.  Can a Plan Item be re-opened after activation?
3.  Can procurement method be changed after plan approval?
4.  What happens if complexity classification changes later?
5.  Can you mix requisitions with different complexity levels into one Plan Item?
6.  What is the rule for grouping across departments?
7.  Who approves the plan — procurement only or external authority?
8.  How do you handle budget revisions after planning?
9.  Can templates be overridden manually?
10. How do you prevent misuse of “Direct Procurement”?

**My blunt assessment**

You’ve just uncovered the most important shift:

👉 Planning is not administrative  
👉 Planning is **process configuration for the entire downstream lifecycle**

If you get this wrong:

- evaluation breaks
- acceptance becomes inconsistent
- audit becomes weak
- procurement becomes manual

**Recommended next step**

Before implementation, you should now define:

**Planning Data Model + Template Resolution Design**

This will:

- formalize Plan Item fields
- define template selection logic
- lock how planning drives downstream modules