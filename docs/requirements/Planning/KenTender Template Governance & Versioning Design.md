# KenTender Template Governance & Versioning Design (v1)

This formalizes your decisions into something developers can actually implement without ambiguity.

**1\. Core Decisions (Locked)**

| **Topic** | **Decision** |
| --- | --- |
| Template configuration | Admin UI-driven |
| Versioning | Controlled versioning (system-managed) |
| Mid-year changes | Allowed via approval workflow |
| Matching strictness | Best-match resolution (with trace) |
| Overrides | Allowed with HoD approval |
| Audit | Mandatory for overrides + selection |

**2\. Template Model (Final Structure)**

**2.1 Procurement Template (Master)**

This is the logical template identity.

**Fields**

- template_code (stable identifier)
- template_name
- category (goods/works/services)
- description
- is_active

**2.2 Procurement Template Version (NEW — critical)**

👉 This is where real behavior lives.

**Fields**

- parent_template
- version_no (1, 2, 3…)
- is_active
- effective_from
- effective_to (nullable)
- approval_status (Draft / Pending / Approved / Deprecated)

**Matching criteria**

- procurement_method
- complexity_classification
- threshold_min
- threshold_max
- sector
- risk_level

**Output definitions**

- evaluation_template
- acceptance_template
- approval_template

**2.3 Key principle**

Templates are stable  
Versions carry behavior

**3\. Versioning Strategy (Your “decide for me” answer)**

**3.1 Version creation rules**

A new version must be created when:

- matching criteria changes
- downstream templates change
- regulatory requirement changes

**3.2 Version lifecycle**

Draft → Pending Approval → Approved → Active → Deprecated

**3.3 Activation rules**

- Only one version active per template per rule scope
- New version overrides old version **from effective date**

**3.4 Mid-year changes (your requirement)**

Allowed only if:

- new version is created
- approved via workflow
- has effective_from date

👉 Old plan items keep old version  
👉 New plan items use new version

**4\. Template Resolution Engine (Refined)**

**4.1 Matching approach (your “next best match”)**

You explicitly chose:

Not strict matching → best match

So we must formalize scoring.

**4.2 Matching scoring model**

Each candidate template version gets a score:

| **Criterion** | **Weight** |
| --- | --- |
| procurement_method | HIGH |
| category | HIGH |
| complexity | HIGH |
| threshold range | MED |
| sector match | MED |
| risk level | LOW |

**4.3 Selection logic**

Find all active template versions  
Filter by required criteria (method, category)  
Score candidates  
Pick highest score

**4.4 Mandatory requirement**

If match is not exact:

👉 System must log:

- “Best-match template selected”
- mismatch fields

**4.5 Example audit log**

Template Selected: TMP-OPEN-GOODS v3  
Match Type: Partial  
Mismatch:  
\- complexity: requested HIGH, matched MEDIUM  
\- sector: requested HEALTH, matched GENERIC

**5\. Override Mechanism (Your requirement)**

**5.1 When override is allowed**

Only when:

- user rejects system-selected template
- provides justification

**5.2 Override workflow**

Requested → Pending HoD Approval → Approved/Rejected

**5.3 Override fields**

On Plan Item:

- system_selected_template_version
- override_requested (bool)
- override_reason
- override_template_version
- override_status
- override_approved_by

**5.4 Enforcement rules**

- Cannot proceed to Plan Approval if override is pending
- Cannot activate plan with unapproved override
- Override must be approved by HoD (as you specified)

**6\. Audit Model (Important — your last point)**

**6.1 What must be audited**

**A. Template selection**

- selected version
- matching score
- mismatches

**B. Override**

- requested by
- reason
- approved/rejected by
- timestamp

**C. Version usage**

- which template version was used for:
    - plan item
    - tender
    - evaluation
    - acceptance

**6.2 Immutable record**

👉 Once plan is Active:

- template version becomes **locked**
- cannot change without formal revision process

**7\. Template Propagation (Critical)**

Once resolved at planning:

**Must propagate to:**

| **Stage** | **Uses Template** |
| --- | --- |
| Tender | structure + requirements |
| Evaluation | scoring + process |
| Award | approval workflow |
| Contract | conditions |
| Acceptance | inspection/approval flow |

**Rule**

Template chosen at planning is binding downstream

**8\. Revision Handling**

**If template changes after planning**

**Case A — Plan not Active**

- re-resolve template
- allow update

**Case B — Plan Active**

- require **Plan Revision Workflow**
- re-approval required

**9\. Edge Cases (Handled explicitly)**

**9.1 No matching template**

Options:

- block plan item
- OR require manual override (with HoD approval)

**9.2 Multiple equal matches**

- choose highest priority
- log ambiguity

**9.3 Template deprecated mid-process**

- existing plan items continue using old version
- new plan items use new version

**10\. UI Behavior (Important)**

**On Plan Item form**

Show:

- Selected Template (system)
- Match Quality (Exact / Partial)
- Mismatch details
- Override section (if used)

**Do NOT allow:**

- free editing of template field
- silent override

**11\. Developer Implementation Guidance**

**Must implement:**

- resolve_template(plan_item)
- score_template_match()
- apply_template(plan_item)
- request_template_override()
- approve_template_override()

**Must NOT allow:**

plan_item.procurement_template = "whatever"

**12\. What you just achieved**

With these decisions, your system now:

- supports real-world policy changes mid-year
- avoids rigid rule failures
- enforces governance through overrides
- keeps audit trace strong
- allows flexibility without chaos

**My honest assessment**

This is now a **serious system design**.

Most procurement systems fail exactly here:

- no versioning
- no traceability
- no controlled override

You’ve avoided that.

**Next step (important)**

Now that:

- planning model ✔
- template engine ✔
- governance ✔

👉 You should move to:

**Cursor Implementation Pack — Planning + Template Engine**

This will translate all this into:

- DocTypes
- services
- validation logic
- resolver + scoring engine
- override workflow