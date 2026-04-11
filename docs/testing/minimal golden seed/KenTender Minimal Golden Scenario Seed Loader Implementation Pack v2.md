# KenTender Minimal Golden Scenario Seed Loader Implementation Pack v2

**1\. Objective**

Implement one **canonical, end-to-end, minimally sized but structurally complete** seed scenario:

**Procurement of 2 Ultrasound Machines for District Hospitals**

This seed pack must create a complete, validated, and enforceable chain across:

- strategy
- budget
- requisition
- planning
- templates
- tender
- bids
- opening
- evaluation
- award
- contract
- inspection
- acceptance
- GRN
- store ledger
- assets
- session assignments
- full traceability
- full validation

This scenario is the system’s:

- default development seed
- QA/UAT reset baseline
- demo baseline
- audit baseline

**2\. Implementation Principles**

**2.1 Deterministic IDs**

Use the exact identifiers:

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

**2.2 Idempotency**

Repeated runs must:

- reuse existing records
- not duplicate scenario artifacts
- not duplicate assignments or ledgers
- preserve final system state

**2.3 Strict Load Order**

1.  base reference
2.  strategy
3.  templates
4.  budget
5.  users
6.  requisition
7.  planning
8.  tender
9.  bids + opening
10. evaluation
11. award
12. contract
13. inspection + acceptance
14. stores + assets
15. assignments
16. verify

**2.4 Service-Driven State**

All transitions must use services for:

- approvals
- publication
- opening
- evaluation completion
- award approval
- contract activation
- acceptance
- GRN posting

**2.5 Strategy Is Mandatory**

Every transactional record must link to:

- Program
- Sub-Program
- Indicator
- Target

No exceptions.

**2.6 Templates Drive Behavior**

All downstream processes must follow:

- procurement template
- evaluation template
- acceptance template

**2.7 Assignments Control Access**

Committee roles must be:

- explicitly assigned
- enforced via access control

**3\. Canonical Scenario Definition**

**Title**

**Procurement of 2 Ultrasound Machines for District Hospitals**

**Scope**

- 1 entity
- 1 department
- 1 funding source
- 1 procurement category
- 1 procurement method
- 1 store
- 1 asset category
- 1 strategy chain
- 1 budget line
- 1 requisition
- 1 plan
- 1 plan item
- 1 tender
- 2 bids
- 1 opening session
- 1 evaluation
- 1 award
- 1 contract
- 1 inspection
- 1 acceptance
- 1 GRN
- 2 assets

**4\. Strategy Model**

**Hierarchy**

Framework → Pillar → Objective → Strategic Plan → Program → Sub-Program → Indicator → Target

**Scenario Chain**

- VF2030
- SOC
- HEALTH-ACCESS
- MOH-SP-2026
- HD
- CRS
- IMG-EQ-HOSP
- PT-IMG-2026

**Enforcement Rules**

- target must belong to indicator
- indicator must belong to sub-program
- sub-program must belong to program
- all downstream records must use same chain

**5\. Template Model**

**Templates Seeded**

**Procurement Template**

- Code: ONT_STANDARD

**Evaluation Template**

- Code: QCBS_SIMPLE

**Acceptance Template**

- Code: GOODS_SIMPLE

**Enforcement**

- plan item selects templates
- tender must use procurement template
- evaluation must use evaluation template
- acceptance must follow acceptance template

**6\. Users**

**Internal Users**

(requisitioner, planner, procurement, evaluator, accounting, contract, inspector, stores, asset, auditor)

**Suppliers**

- supplier1.test
- supplier2.test

**Rule**

Permanent roles ≠ session access

**7\. Folder Structure**

/uat/seed_packs/minimal_golden_v2/  
00_base_ref.py  
01_strategy.py  
02_templates.py  
03_budget.py  
04_users.py  
05_requisition.py  
06_planning.py  
07_tender.py  
08_bids_opening.py  
09_evaluation.py  
10_award.py  
11_contract.py  
12_inspection_acceptance.py  
13_stores_assets.py  
14_assignments.py  
verify.py  
reset.py

**8\. Seed Execution Specification**

**8.1 Base Reference**

Seed:

- MOH
- CLIN-SERV
- EXCH-DEV
- MED-EQ
- ONT
- CMS
- MED-DIAG

**8.2 Strategy**

Seed full hierarchy with strict linkage.

**8.3 Templates**

Seed:

- ONT_STANDARD
- QCBS_SIMPLE
- GOODS_SIMPLE

**8.4 Budget**

Seed:

- BCP-2026
- BUD-MOH-2026-V1
- BL-MOH-IMG-001

Include:

- allocated: 12,000,000

**8.5 Users**

Create all users with roles.

**8.6 Requisition**

PR-MOH-0001

Include:

- strategy fields
- amount: 9,000,000
- status: Approved

Create reservation: 9,000,000

**8.7 Planning**

PP-MOH-0001  
PPI-MOH-0001

Include:

- inherited strategy
- template selection
- approved state

**8.8 Tender**

TD-MOH-0001

Include:

- link to plan
- template
- criteria
- published state

**8.9 Bids + Opening**

2 bids  
Opening session completed

**8.10 Evaluation**

EVS-MOH-0001  
EVR-MOH-0001

Include:

- scoring
- recommendation

**8.11 Award**

AWD-MOH-0001  
STS-MOH-0001

**8.12 Contract**

CT-MOH-0001

Create commitment: 8,700,000

**8.13 Inspection + Acceptance**

INSP-MOH-0001  
ACC-MOH-0001

**8.14 Stores + Assets**

GRN-MOH-0001

Assets:

- AST-MOH-0001
- AST-MOH-0002

**8.15 Assignments**

Assign:

- tender committee
- opening committee
- evaluation committee
- acceptance committee

**9\. Validation Rules**

**9.1 Strategy Consistency**

assert plan.target == requisition.target  
assert tender.target == plan.target  
assert contract.target == tender.target  
assert asset.target == contract.target

**9.2 Financial Integrity**

assert reservation <= allocated  
assert commitment <= reservation

**9.3 Workflow States**

All records must be in correct final states.

**9.4 Quantity Consistency**

assert grn.qty == 2  
assert assets.count == 2

**9.5 Supplier Consistency**

assert contract.supplier == award.supplier

**9.6 Template Consistency**

assert tender.template == plan.template

**10\. Process Gating Rules**

- no tender without approved plan
- no opening before deadline
- no evaluation before opening
- no award before evaluation
- no contract before award
- no GRN before acceptance
- no asset before GRN

**11\. Data Locking**

After approval:

- key fields immutable

**12\. Assignment Enforcement**

Users must only access assigned sessions.

**13\. Trace Chain**

Asset  
→ GRN  
→ Contract  
→ Award  
→ Evaluation  
→ Opening  
→ Tender  
→ Plan Item  
→ Requisition  
→ Target  
→ Indicator  
→ Program  
→ Strategic Plan

**14\. Verification Command**

Must check:

- all records exist
- workflow states correct
- financial balances correct
- assignments exist
- strategy chain intact
- templates applied
- full trace valid

**15\. Reset Command**

Rebuild full scenario deterministically.

**16\. Acceptance Criteria**

System is valid only if:

- no missing links
- no invalid states
- no financial inconsistencies
- no unauthorized access
- full trace exists

**Final Statement**

This document now defines a **complete, enforceable, auditable, production-grade seed scenario**.

It ensures:

- strategy-driven procurement
- template-driven execution
- controlled workflows
- financial integrity
- role enforcement
- full lifecycle traceability