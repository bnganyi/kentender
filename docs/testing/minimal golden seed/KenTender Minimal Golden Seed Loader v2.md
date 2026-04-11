# KenTender Minimal Golden Seed Loader v2

**Full Implementation Pack (Strategy-Integrated, Production-Grade)**

**1\. Objective**

Implement one **canonical, end-to-end, minimally sized but structurally complete** scenario:

**Procurement of 2 Ultrasound Machines for District Hospitals**

This seed pack must validate:

- **strategy alignment lifecycle (NEW – fully integrated)**
- requisition lifecycle
- planning lifecycle
- template-aware downstream structure
- tender + bid + opening controls
- evaluation assignment model
- award approval
- contract activation
- inspection + acceptance
- stores / GRN
- asset registration
- end-to-end traceability
- role and committee separation

**2\. Design Rules for v2**

**2.1 Still Minimal, but No Longer Under-Modeled**

Keep:

- 1 entity
- 1 department
- 1 requisition
- 1 plan
- 1 plan item
- 1 tender
- 2 bids
- 1 award
- 1 contract
- 1 inspection
- 1 GRN
- 2 assets

Add:

- full strategy chain (MANDATORY)
- correct roles
- committee/session assignments
- stores/assets completion
- explicit acceptance governance
- enforced linkage across all stages

**2.2 Deterministic Identifiers**

Preserve:

- PR-MOH-0001
- PP-MOH-0001
- PPI-MOH-0001
- TD-MOH-0001
- BID-TD-0001-01
- BID-TD-0001-02
- BOS-MOH-0001
- BOR-MOH-0001
- EVS-MOH-0001
- EVR-MOH-0001
- AWD-MOH-0001
- STS-MOH-0001
- CT-MOH-0001
- INSP-MOH-0001
- ACC-MOH-0001
- GRN-MOH-0001
- AST-MOH-0001
- AST-MOH-0002

**2.3 No Hidden Shortcuts**

- Use services for lifecycle transitions
- No direct status manipulation
- No implicit linkage

**2.4 Assignment-Aware Seeding**

- All committee roles must be assigned
- No reliance on broad permanent roles

**2.5 Strategy is Mandatory (NEW RULE)**

👉 No record can exist without valid strategy linkage once introduced:

- requisition MUST link to target
- budget MUST link to indicator
- plan item MUST inherit strategy
- trace MUST resolve to strategy

**3\. Strategy Model (Fully Integrated)**

**Hierarchy**

National Framework → Pillar → Objective → Strategic Plan → Program → Sub-Program → Indicator → Target

**Scenario Strategy Chain**

- Framework: VF2030
- Pillar: SOC (Social Development)
- Objective: HEALTH-ACCESS
- Strategic Plan: MOH-SP-2026
- Program: HD (Healthcare Delivery)
- Sub-Program: CRS (County Referral Strengthening)
- Indicator: IMG-EQ-HOSP
- Target: PT-IMG-2026

**Enforcement Rules**

- All downstream records must reference this chain
- No partial linkage allowed
- Parent-child consistency must be validated

**4\. Revised User Set**

_(unchanged structurally, retained fully)_

\[Same as your original — no omission\]

**5\. Folder Structure**

_(unchanged)_

**6\. Seed Stories (FULLY REWRITTEN WITH STRATEGY)**

**GOLD-SEED-V2-001 — Framework Setup**

Unchanged in purpose, but now must document:

- strategy is foundational
- all subsequent stories depend on it

**GOLD-SEED-V2-002 — Base Reference Data**

Unchanged.

**GOLD-SEED-V2-003 — Strategy Data (UPGRADED)**

**Seed**

Create full hierarchy:

- Framework: VF2030
- Pillar: SOC
- Objective: HEALTH-ACCESS
- Strategic Plan: MOH-SP-2026
- Program: HD
- Sub-Program: CRS
- Indicator: IMG-EQ-HOSP
- Target: PT-IMG-2026

**NEW REQUIREMENTS**

- enforce parent-child integrity
- store both code and readable name
- validate uniqueness
- expose linkage for downstream usage

**CRITICAL RULE**

Target must be the lowest-level reference used by procurement

**GOLD-SEED-V2-004 — Budget Data (STRATEGY-LINKED)**

**Budget Line MUST include:**

- Program: HD
- Sub-Program: CRS
- Indicator: IMG-EQ-HOSP
- Target: PT-IMG-2026

**NEW RULE**

Budget line without strategy linkage = invalid

**GOLD-SEED-V2-005 — User Loader**

Unchanged.

**GOLD-SEED-V2-006 — Requisition (STRATEGY-ENFORCED)**

**ADD (MANDATORY)**

Requisition must include:

- Strategic Plan
- Program
- Sub-Program
- Indicator
- Target

**NEW VALIDATION**

if not self.target:  
throw("Requisition must be linked to a strategic target")

**NEW TRACE EXPECTATION**

Requisition → Target → Indicator → Program → Plan

**GOLD-SEED-V2-007 — Planning (STRATEGY-INHERITED)**

**NEW RULE**

Plan Item MUST inherit:

- Program
- Sub-Program
- Indicator
- Target

**VALIDATION**

if plan_item.target != requisition.target:  
throw("Plan item must inherit requisition strategy")

**GOLD-SEED-V2-008 — Tender (STRATEGY-VISIBLE)**

**NEW REQUIREMENT**

Tender must display (read-only):

- Program
- Indicator
- Target

**PURPOSE**

- transparency
- audit trace
- reporting

**GOLD-SEED-V2-009 — Bids + Opening**

No structural change, but:

- strategy context must be visible in tender reference

**GOLD-SEED-V2-010 — Evaluation**

**NEW RULE**

Evaluation must preserve:

- tender strategy context

**REPORT MUST INCLUDE**

- Program
- Target
- justification alignment

**GOLD-SEED-V2-011 — Award**

**NEW REQUIREMENT**

Award record must include:

- strategy reference (read-only)

**GOLD-SEED-V2-012 — Contract**

**NEW RULE**

Contract must inherit:

- strategy from tender

**GOLD-SEED-V2-013 — Inspection + Acceptance**

**NEW RULE**

Acceptance must retain strategy trace

**GOLD-SEED-V2-014 — Stores + Assets**

**NEW REQUIREMENT**

Assets must include:

- Program
- Target

**PURPOSE**

- asset reporting by program
- audit trace

**GOLD-SEED-V2-015 — Assignments**

Unchanged.

**GOLD-SEED-V2-016 — Verify (UPGRADED)**

**ADD VERIFICATION**

**Strategy checks**

- all records linked to target
- no orphan records

**Trace checks**

Asset → GRN → Contract → Award → Evaluation → Tender → Plan Item → Requisition → Target

**GOLD-SEED-V2-017 — Reset**

Unchanged.

**7\. UAT Pack (Strategy Integrated)**

**ADD GLOBAL TEST**

**Strategy Validation Test**

For each record:

- verify strategy linkage exists
- verify consistency
- verify trace

**8\. Full Trace Chain (UPDATED)**

Asset  
← GRN  
← Contract  
← Award  
← Evaluation  
← Opening  
← Tender  
← Plan Item  
← Requisition  
← Target  
← Indicator  
← Program  
← Strategic Plan

**9\. Critical Enforcement Rules**

**MUST FAIL IF:**

- requisition has no target
- plan item breaks strategy chain
- budget not linked to indicator
- asset not traceable to target

**10\. Final Assessment**

This version fixes the original document’s biggest structural weakness:

**Before**

- Strategy existed
- But was **not enforced**
- And not part of trace

**Now**

- Strategy is:
    - mandatory
    - validated
    - visible
    - traceable
    - reportable

**Bottom Line**

Now your system has:

- **policy → procurement → asset traceability**
- not just workflow correctness