# KenTender Minimal Golden Scenario v2

**Full UAT Script Pack (Strategy-Integrated, Role-Driven, End-to-End)**

**1\. Purpose**

This UAT pack validates:

- full procurement lifecycle
- **strategy alignment (NEW – mandatory validation)**
- role-based access control
- workflow enforcement
- assignment-based permissions
- financial controls (reservation + commitment)
- stores and asset lifecycle
- end-to-end traceability (extended to strategy layer)

**2\. Scenario Reference**

**Scenario**

**Procurement of 2 Ultrasound Machines for District Hospitals**

**Core Records**

- PR-MOH-0001
- PP-MOH-0001
- PPI-MOH-0001
- TD-MOH-0001
- BID-TD-0001-01 / 02
- BOS-MOH-0001 / BOR-MOH-0001
- EVS-MOH-0001 / EVR-MOH-0001
- AWD-MOH-0001 / STS-MOH-0001
- CT-MOH-0001
- INSP-MOH-0001 / ACC-MOH-0001
- GRN-MOH-0001
- AST-MOH-0001 / AST-MOH-0002

**Strategy Reference (NEW)**

- Framework: VF2030
- Pillar: SOC
- Objective: HEALTH-ACCESS
- Strategic Plan: MOH-SP-2026
- Program: HD
- Sub-Program: CRS
- Indicator: IMG-EQ-HOSP
- Target: PT-IMG-2026

**3\. UAT Execution Principles**

**3.1 Always test as the role**

- log in as the actual user
- do NOT test as Administrator

**3.2 Validate BOTH**

- what user **can do**
- what user **cannot do**

**3.3 No skipping stages**

Follow lifecycle:

Requisition → Planning → Tender → Opening → Evaluation → Award → Contract → Acceptance → Stores → Assets

**3.4 Strategy validation is mandatory (NEW)**

Every stage must validate:

- presence of strategy linkage
- correctness of linkage
- consistency across records

**4\. UAT Scripts (By Role)**

**🔵 UAT-001 — Requisitioner**

**User**

requisitioner.test

**Steps**

1.  Open PR-MOH-0001
2.  Review requisition details

**Expected**

- sees amount = 9,000,000
- sees 2 items
- **sees strategy fields (NEW):**
    - Program: HD
    - Sub-Program: CRS
    - Indicator: IMG-EQ-HOSP
    - Target: PT-IMG-2026

**Must NOT**

- approve requisition
- edit approved requisition
- modify strategy linkage

**🟣 UAT-002 — Department Reviewer**

**Expected**

- sees requisition
- sees approval history
- **sees strategy context clearly displayed**

**Must NOT**

- alter strategy linkage
- create plan

**🟢 UAT-003 — Head of Department**

**Expected**

- sees requisition trace
- sees planning visibility
- **sees alignment to strategic objective**

**Must NOT**

- change strategy
- create tender

**🔵 UAT-004 — Procurement Planner**

**Steps**

1.  Open PP-MOH-0001
2.  Open PPI-MOH-0001

**Expected**

- sees linkage to PR
- sees method = ONT
- **strategy inherited correctly (NEW)**
- no mismatch between requisition and plan

**Must NOT**

- override strategy silently

**🟣 UAT-005 — Planning Authority**

**Expected**

- sees plan
- **validates strategy alignment explicitly**

**Must NOT**

- approve misaligned plan

**🔵 UAT-006 — Procurement Officer**

**Expected**

- sees tender
- sees criteria
- **sees strategy context (read-only)**

**Must NOT**

- modify strategy

**🟡 UAT-007 — Tender Committee**

**Expected**

- sees tender
- **sees program/target context**

**Must NOT**

- alter strategy
- access downstream execution

**🟠 UAT-008 — Opening Committee**

**Expected**

- sees opening data
- sees bids
- **strategy context visible but read-only**

**🔴 UAT-009 — Evaluator**

**Expected**

- sees assigned evaluation
- sees scoring
- **sees strategy context for evaluation justification**

**Must NOT**

- access unrelated tenders
- change strategy

**🟣 UAT-010 — Evaluation Chair & Secretary**

**Expected**

- sees evaluation report
- **report includes strategy context (NEW)**

**🟢 UAT-011 — Accounting Officer**

**Expected**

- sees award
- sees amount
- **sees strategy linkage**

**🔵 UAT-012 — Contract Manager**

**Expected**

- sees contract
- **strategy inherited from award/tender**

**🟠 UAT-013 — Inspector**

**Expected**

- sees inspection
- **can view originating strategy context**

**🔴 UAT-014 — Acceptance Committee**

**Expected**

- sees acceptance
- **trace to strategy available**

**🟢 UAT-015 — Storekeeper / Stores Supervisor**

**Expected**

- sees GRN
- **can trace to contract → strategy**

**🔵 UAT-016 — Asset Officer**

**Expected**

- sees assets
- **sees Program + Target (NEW requirement)**
- asset trace includes strategy

**🟣 UAT-017 — Supplier**

**Expected**

- sees own bid
- **does NOT see internal strategy details beyond what is exposed in tender**

**⚫ UAT-018 — Auditor**

**Steps**

1.  Open records
2.  Verify trace

**Expected**

- full read-only access
- **can trace from asset → strategy**

**🧭 UAT-019 — End-to-End Trace (UPDATED)**

**Steps**

Trace backward:

AST-MOH-0001  
→ GRN-MOH-0001  
→ CT-MOH-0001  
→ AWD-MOH-0001  
→ EVR-MOH-0001  
→ BOS-MOH-0001  
→ TD-MOH-0001  
→ PPI-MOH-0001  
→ PR-MOH-0001  
→ PT-IMG-2026  
→ IMG-EQ-HOSP  
→ CRS  
→ HD  
→ MOH-SP-2026

**Expected**

- full trace exists
- no broken links
- strategy chain intact

**5\. Critical Control Tests (UPDATED)**

**5.1 Sealed Bid**

Unchanged

**5.2 Assignment Enforcement**

Unchanged

**5.3 GRN Gating**

Unchanged

**5.4 Asset Gating**

Unchanged

**5.5 Strategy Integrity (NEW)**

Must FAIL if:

- requisition has no target
- plan item breaks strategy chain
- contract missing strategy
- asset cannot trace to target

**6\. Pass Criteria (UPDATED)**

Scenario passes ONLY if:

- all roles behave correctly
- no unauthorized access
- all stages linked
- financial flows correct
- stores and assets correct
- **strategy alignment preserved end-to-end (NEW)**

**Final Assessment**

**Before (your original UAT pack)**

- strong lifecycle validation
- good role coverage
- **no strategy validation**

**Now**

- lifecycle validated
- roles validated
- permissions validated
- **strategy validated end-to-end**
- **audit trace complete**

**Bottom Line**

Now your UAT pack tests:

👉 not just **“did we procure correctly?”**  
but also  
👉 **“did we procure the right thing for the right strategic reason?”**