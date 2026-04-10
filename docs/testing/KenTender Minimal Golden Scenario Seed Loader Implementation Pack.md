# KenTender Minimal Golden Scenario Seed Loader Implementation Pack

**Objective**

Implement one **canonical MVP seed scenario**:

**Procurement of 2 Ultrasound Machines for District Hospitals**

This seed pack must create a complete linked chain from:

- strategy
- budget
- requisition
- planning
- tender
- bids
- opening
- evaluation
- award
- contract
- inspection
- GRN
- assets

**Implementation principles**

**1\. Deterministic IDs**

Use the exact business IDs from the workbook wherever practical:

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

**2\. Idempotent enough for QA/UAT**

Running loaders repeatedly should:

- reuse existing records when safe
- update only where explicitly intended
- avoid duplicate active scenario objects

**3\. Load in dependency order**

Always seed in this order:

1.  base reference
2.  strategy
3.  budget
4.  users
5.  scenario chain

**4\. No hidden shortcuts**

Do not bypass service logic unless absolutely necessary for fixture setup.  
Where business state matters, prefer services.

**Recommended folder structure**

/uat/  
/seed_packs/  
/minimal_golden/  
README.md  
00_base_ref.py  
01_strategy.py  
02_budget.py  
03_users.py  
04_requisition.py  
05_planning.py  
06_tender.py  
07_bids_opening.py  
08_evaluation.py  
09_award.py  
10_contract.py  
11_inspection.py  
12_stores_assets.py  
verify.py  
reset.py  
/utils/  
seed_helpers.py  
lookup_helpers.py

**Seed loader story breakdown**

**GOLD-SEED-001 — Create minimal golden seed framework**

**Objective**  
Create the folder structure, shared helpers, and command pattern for the minimal golden scenario.

**Cursor prompt**

Writing

You are implementing a bounded UAT seed infrastructure task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-001
- Title: Create minimal golden seed framework

Context:

- KenTender has a canonical MVP scenario called the Minimal Golden Scenario.
- It must be seeded deterministically for QA/UAT and demos.
- The scenario workbook defines the exact target objects and business IDs.

Task:  
Create the seed framework for the Minimal Golden Scenario.

Required structure:

- /uat/seed_packs/minimal_golden/
- shared helper location such as /uat/utils/
- README describing load order and purpose
- command-ready structure for:
    - base reference
    - strategy
    - budget
    - users
    - requisition
    - planning
    - tender
    - bids/opening
    - evaluation
    - award
    - contract
    - inspection
    - stores/assets
    - verify
    - reset

Requirements:

1.  Create deterministic structure and naming conventions.
2.  Add developer notes for:
    - exact business IDs should be preserved
    - load order must be respected
    - scenario is intended to be canonical
3.  Keep the framework lightweight and ready for follow-on stories.

Constraints:

- Do not implement all seed data in this story.
- Do not mix unrelated scenarios.
- Keep this focused on structure and conventions.

Acceptance criteria:

- seed framework folders/files exist
- README/conventions exist
- later seed stories have a clear place to live

At the end, provide:

1.  files/folders created
2.  assumptions made
3.  open questions
4.  recommended load sequence

**GOLD-SEED-002 — Implement base reference seed loader**

**Seeds**

- entity
- department
- funding source
- procurement category
- procurement method
- store
- asset category

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-002
- Title: Implement base reference seed loader

Context:

- This is the first seed stage for the Minimal Golden Scenario.
- The exact records to seed are defined in the workbook.

Task:  
Implement a deterministic base reference loader for the following records:

1.  Procuring Entity

- Code: MOH
- Name: Ministry of Health

1.  Department

- Code: CLIN-SERV
- Name: Clinical Services
- Entity: MOH

1.  Funding Source

- Code: EXCH-DEV
- Name: Exchequer Development Grant

1.  Procurement Category

- Code: MED-EQ
- Name: Medical Equipment

1.  Procurement Method

- Code: ONT
- Name: Open National Tender

1.  Store

- Code: CMS
- Name: Central Medical Store
- Entity: MOH

1.  Asset Category

- Code: MED-DIAG
- Name: Medical Diagnostic Equipment

Requirements:

1.  Make the loader deterministic and idempotent where practical.
2.  Use exact codes/names from the scenario workbook.
3.  Print or return a summary of created/found records.

Constraints:

- Do not seed strategy or budget here.
- Do not invent extra reference records unless required for integrity.
- Keep the dataset minimal.

Acceptance criteria:

- all required reference records are seeded
- repeated load does not create uncontrolled duplicates
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  summary of seeded records

**GOLD-SEED-003 — Implement strategy seed loader**

**Seeds**

- framework
- pillar
- objective
- entity strategic plan
- program
- sub-program
- indicator
- target

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-003
- Title: Implement strategy seed loader

Context:

- This is the strategy layer for the Minimal Golden Scenario.
- The records must be seeded exactly as defined.

Task:  
Implement a deterministic strategy seed loader for:

1.  National Framework

- Code: VF2030
- Name: Vision 2030

1.  National Pillar

- Code: SOC
- Name: Social Development
- Framework: VF2030

1.  National Objective

- Code: HEALTH-ACCESS
- Name: Improve access to healthcare services
- Pillar: SOC

1.  Entity Strategic Plan

- Code: MOH-SP-2026
- Name: MOH Strategic Plan 2026–2030
- Entity: MOH

1.  Program

- Code: HD
- Name: Healthcare Delivery
- Strategic Plan: MOH-SP-2026
- National Objective: HEALTH-ACCESS

1.  Sub-Program

- Code: CRS
- Name: County Referral Strengthening
- Program: HD

1.  Output Indicator

- Code: IMG-EQ-HOSP
- Name: Number of hospitals equipped with imaging equipment
- Sub-Program: CRS

1.  Performance Target

- Code: PT-IMG-2026
- Name: Equip 2 district hospitals with ultrasound machines
- Indicator: IMG-EQ-HOSP
- Target Value: 2

Requirements:

1.  Preserve exact linkage hierarchy.
2.  Keep the loader deterministic and idempotent where practical.
3.  Output a summary of created/found records.

Constraints:

- Do not create extra strategy branches.
- Keep this scenario minimal and canonical.

Acceptance criteria:

- all strategy records are seeded and correctly linked
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  summary of seeded records

**GOLD-SEED-004 — Implement budget seed loader**

**Seeds**

- control period
- budget
- budget line
- reservation entry
- commitment entry placeholder or actual post depending approach

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-004
- Title: Implement budget seed loader

Context:

- This is the budget layer for the Minimal Golden Scenario.
- The scenario budget state is intentionally simple and must be reproducible.

Task:  
Implement deterministic budget seeding for:

1.  Budget Control Period

- Code: BCP-2026
- Fiscal Year: FY2026/27
- Entity: MOH

1.  Budget

- Code: BUD-MOH-2026-V1
- Name: MOH Budget FY2026/27 v1
- Control Period: BCP-2026

1.  Budget Line

- Code: BL-MOH-IMG-001
- Name: Diagnostic Imaging Equipment
- Budget: BUD-MOH-2026-V1
- Entity: MOH
- Department: CLIN-SERV
- Funding Source: EXCH-DEV
- Program: HD
- Sub-Program: CRS
- Indicator: IMG-EQ-HOSP
- Target: PT-IMG-2026
- Allocated Amount: 12,000,000

Also support the scenario budget movements:

- Reservation from PR-MOH-0001 = 9,000,000
- Commitment from CT-MOH-0001 = 8,700,000

Requirements:

1.  Seed the structural budget records first.
2.  Use budget services where practical for ledger movements.
3.  If scenario stage loading order requires it, allow reservation/commitment entries to be seeded in later stages rather than here, but document clearly.
4.  Output a summary of seeded records and current balances.

Constraints:

- Do not fake totals without traceable ledger semantics.
- Keep the model aligned with the budget service design.

Acceptance criteria:

- budget structural records are seeded
- ledger-compatible scenario state is supported
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  summary of seeded records and balance state

**GOLD-SEED-005 — Implement minimal golden user loader**

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-005
- Title: Implement minimal golden user loader

Context:

- The Minimal Golden Scenario uses a small fixed user set.

Task:  
Implement deterministic user loading for:

Internal:

- requisitioner.test
- hod.test
- finance.test
- procurement.test
- openingchair.test
- evaluator.test
- evaluationchair.test
- accounting.test
- contractmanager.test
- inspector.test
- storekeeper.test
- assetofficer.test

Suppliers:

- supplier1.test -> MedEquip Africa Ltd
- supplier2.test -> Afya Diagnostics Ltd

Requirements:

1.  Create users deterministically and idempotently where practical.
2.  Assign the minimum necessary roles/personas for the scenario.
3.  Keep supplier naming and organization linkage clear.
4.  Output a user summary.

Constraints:

- Do not add the full long-form UAT user pack here.
- Keep this strictly scenario-focused.

Acceptance criteria:

- all users are seeded
- user-role mapping is usable for the scenario
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  summary of user-role mappings

**GOLD-SEED-006 — Implement requisition seed loader**

**Target records**

- PR-MOH-0001
- requisition item
- reservation entry for 9,000,000

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-006
- Title: Implement requisition seed loader

Context:

- This creates SP1 for the Minimal Golden Scenario.

Task:  
Seed the requisition stage exactly as follows:

Purchase Requisition:

- Business ID: PR-MOH-0001
- Title: Procurement of 2 Ultrasound Machines
- Entity: MOH
- Department: CLIN-SERV
- Requested By: requisitioner.test
- Budget Line: BL-MOH-IMG-001
- Program: HD
- Sub-Program: CRS
- Indicator: IMG-EQ-HOSP
- Target: PT-IMG-2026
- Requested Amount: 9,000,000
- Status at seed: Approved

Requisition Item:

- Description: Portable Ultrasound Machine
- Quantity: 2
- Estimated Unit Cost: 4,500,000
- Line Total: 9,000,000

Also seed the budget reservation state:

- Reservation amount: 9,000,000
- Source: PR-MOH-0001

Requirements:

1.  Prefer service-driven approval/reservation paths where practical.
2.  Preserve exact business ID.
3.  Ensure the requisition ends in Approved state and is planning-ready.
4.  Output the requisition ID and reservation confirmation.

Constraints:

- Do not seed planning records here.
- Do not silently fake approval history if approval record models already exist; seed them properly where supported.

Acceptance criteria:

- PR-MOH-0001 exists in Approved state
- reservation exists and is traceable
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  requisition and reservation summary

**GOLD-SEED-007 — Implement planning seed loader**

**Target records**

- PP-MOH-0001
- PPI-MOH-0001
- requisition planning link

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-007
- Title: Implement planning seed loader

Context:

- This creates SP2 for the Minimal Golden Scenario.

Task:  
Seed the planning stage exactly as follows:

Procurement Plan:

- Business ID: PP-MOH-0001
- Title: MOH Procurement Plan FY2026/27
- Status at seed: Active

Procurement Plan Item:

- Business ID: PPI-MOH-0001
- Title: Procurement of 2 Ultrasound Machines
- Source Requisition: PR-MOH-0001
- Method: ONT
- Estimated Amount: 9,000,000
- Planned Publication Date: 2026-07-15
- Planned Submission Deadline: 2026-08-01
- Planned Award Date: 2026-08-15
- Status at seed: Approved / Ready for Tender

Requisition Planning Link:

- Requisition: PR-MOH-0001
- Plan Item: PPI-MOH-0001
- Linked Amount: 9,000,000
- Status: Active

Requirements:

1.  Preserve exact business IDs.
2.  Keep full traceability between requisition and plan item.
3.  Prefer planning service methods if available and practical.
4.  Output plan and plan item summary.

Constraints:

- Do not seed tender here.
- Do not create unrelated plan items.

Acceptance criteria:

- PP-MOH-0001 and PPI-MOH-0001 exist
- link to PR-MOH-0001 is explicit
- plan item is ready for tender
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  planning summary

**GOLD-SEED-008 — Implement tender seed loader**

**Target records**

- TD-MOH-0001
- tender criteria
- published state

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-008
- Title: Implement tender seed loader

Context:

- This creates SP3 tender state for the Minimal Golden Scenario.

Task:  
Seed the tender stage exactly as follows:

Tender:

- Business ID: TD-MOH-0001
- Title: Supply and Delivery of 2 Ultrasound Machines
- Source Plan Item: PPI-MOH-0001
- Method: ONT
- Estimated Amount: 9,000,000
- Publication Date: 2026-07-15
- Submission Deadline: 2026-08-01 10:00
- Opening Time: 2026-08-01 10:30
- Status at seed: Published

Tender Criteria:

1.  Tax compliance certificate — Mandatory
2.  Manufacturer authorization — Mandatory
3.  Technical compliance — Score / 70
4.  Financial quote — Score / 30

Requirements:

1.  Preserve exact tender business ID.
2.  Keep tender linked to PPI-MOH-0001.
3.  Use publish service if practical so publication state is consistent.
4.  Output tender and criteria summary.

Constraints:

- Do not seed bids here.
- Do not introduce lots or advanced tender structures for this scenario.

Acceptance criteria:

- TD-MOH-0001 exists in Published state
- required criteria exist
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tender summary

**GOLD-SEED-009 — Implement bids and opening seed loader**

**Target records**

- BID-TD-0001-01
- BID-TD-0001-02
- BOS-MOH-0001
- BOR-MOH-0001

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-009
- Title: Implement bids and opening seed loader

Context:

- This completes SP3 for the Minimal Golden Scenario.

Task:  
Seed bids and opening exactly as follows:

Bid 1:

- Business ID: BID-TD-0001-01
- Supplier: MedEquip Africa Ltd
- User: supplier1.test
- Quoted Amount: 8,700,000
- Status at seed: Submitted / Locked

Bid 2:

- Business ID: BID-TD-0001-02
- Supplier: Afya Diagnostics Ltd
- User: supplier2.test
- Quoted Amount: 8,900,000
- Status at seed: Submitted / Locked

Opening Session:

- Business ID: BOS-MOH-0001
- Tender: TD-MOH-0001
- Chair: openingchair.test
- Status at seed: Completed

Opening Register:

- Business ID: BOR-MOH-0001
- Includes both bids
- Status: Locked

Requirements:

1.  Preserve exact business IDs.
2.  Prefer real submission/opening services where practical.
3.  Ensure bids are sealed/locked before opening and opened afterward in a traceable way.
4.  Output summary of bids, opening session, and register.

Constraints:

- Do not seed evaluation here.
- Keep the scenario minimal and deterministic.

Acceptance criteria:

- both bids exist with expected quoted amounts
- BOS-MOH-0001 and BOR-MOH-0001 exist
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  bids/opening summary

**GOLD-SEED-010 — Implement evaluation seed loader**

**Target records**

- EVS-MOH-0001
- EVR-MOH-0001
- evaluation scores
- recommended supplier1

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-010
- Title: Implement evaluation seed loader

Context:

- This creates SP4 for the Minimal Golden Scenario.

Task:  
Seed evaluation exactly as follows:

Evaluation Session:

- Business ID: EVS-MOH-0001
- Tender: TD-MOH-0001
- Status at seed: Completed

Conflict Declaration:

- Evaluator: evaluator.test
- Status: Declared No Conflict

Evaluation results:  
Bid 1:

- Technical Score: 88
- Financial Score: 30
- Combined Score: 91.6

Bid 2:

- Technical Score: 84
- Financial Score: 29.3
- Combined Score: 87.3

Evaluation Report:

- Business ID: EVR-MOH-0001
- Recommended Bid: BID-TD-0001-01
- Recommended Supplier: MedEquip Africa Ltd
- Recommended Amount: 8,700,000
- Status at seed: Submitted

Requirements:

1.  Preserve exact business IDs.
2.  Keep recommendation consistent with scores.
3.  Prefer evaluation service flows where practical.
4.  Output evaluation summary.

Constraints:

- Do not seed award here.
- Keep evaluator set minimal.

Acceptance criteria:

- EVS-MOH-0001 and EVR-MOH-0001 exist
- recommendation matches expected scoring outcome
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  evaluation summary

**GOLD-SEED-011 — Implement award seed loader**

**Target records**

- AWD-MOH-0001
- STS-MOH-0001

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-011
- Title: Implement award seed loader

Context:

- This creates SP5 for the Minimal Golden Scenario.

Task:  
Seed award exactly as follows:

Award Decision:

- Business ID: AWD-MOH-0001
- Tender: TD-MOH-0001
- Recommended Supplier: MedEquip Africa Ltd
- Approved Supplier: MedEquip Africa Ltd
- Approved Amount: 8,700,000
- Status at seed: Final Approved

Award Notifications:

- successful notice sent to supplier1.test
- unsuccessful notice sent to supplier2.test

Standstill Period:

- Business ID: STS-MOH-0001
- Status at seed: Completed

Requirements:

1.  Preserve exact business IDs.
2.  Keep award aligned with evaluation recommendation.
3.  Prefer award approval and standstill services where practical.
4.  Output award summary.

Constraints:

- Do not seed contract here.
- Keep no-deviation case only.

Acceptance criteria:

- AWD-MOH-0001 exists in Final Approved state
- STS-MOH-0001 exists in Completed state
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  award summary

**GOLD-SEED-012 — Implement contract seed loader**

**Target records**

- CT-MOH-0001
- commitment entry 8,700,000

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-012
- Title: Implement contract seed loader

Context:

- This creates SP6 contract state for the Minimal Golden Scenario.

Task:  
Seed contract exactly as follows:

Contract:

- Business ID: CT-MOH-0001
- Award: AWD-MOH-0001
- Supplier: MedEquip Africa Ltd
- Value: 8,700,000
- Status at seed: Active

Budget movement:

- Commitment amount: 8,700,000
- Source: CT-MOH-0001

Requirements:

1.  Preserve exact contract business ID.
2.  Prefer create/approve/sign/activate service flow where practical.
3.  Ensure commitment is visible and traceable through the budget layer.
4.  Output contract and commitment summary.

Constraints:

- Do not seed inspection here.
- Do not create variations or partial states.

Acceptance criteria:

- CT-MOH-0001 exists in Active state
- commitment exists and is traceable
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  contract summary

**GOLD-SEED-013 — Implement inspection and acceptance seed loader**

**Target records**

- INSP-MOH-0001
- ACC-MOH-0001

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-013
- Title: Implement inspection and acceptance seed loader

Context:

- This completes SP6 for the Minimal Golden Scenario.

Task:  
Seed inspection and acceptance exactly as follows:

Inspection Record:

- Business ID: INSP-MOH-0001
- Contract: CT-MOH-0001
- Method: Mixed
- Status at seed: Completed

Inspection Result:

- Machine 1: Pass
- Machine 2: Pass

Acceptance Record:

- Business ID: ACC-MOH-0001
- Decision: Accepted
- Status at seed: Accepted

Requirements:

1.  Preserve exact business IDs.
2.  Keep acceptance consistent with passing inspection results.
3.  Prefer service paths where practical.
4.  Output inspection and acceptance summary.

Constraints:

- Do not seed GRN here.
- Keep no-failure happy path only.

Acceptance criteria:

- INSP-MOH-0001 and ACC-MOH-0001 exist
- acceptance is consistent with inspection result
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  inspection summary

**GOLD-SEED-014 — Implement stores and assets seed loader**

**Target records**

- GRN-MOH-0001
- AST-MOH-0001
- AST-MOH-0002

**Cursor prompt**

Writing

You are implementing a bounded seed-loader task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-014
- Title: Implement stores and assets seed loader

Context:

- This completes SP7 for the Minimal Golden Scenario.

Task:  
Seed stores and assets exactly as follows:

Goods Receipt Note:

- Business ID: GRN-MOH-0001
- Contract: CT-MOH-0001
- Store: CMS
- Quantity Received: 2
- Status at seed: Posted

Store Ledger:

- Receipt of 2 units into CMS

Assets:

1.  AST-MOH-0001

- Name: Ultrasound Machine Unit 1
- Source Contract: CT-MOH-0001
- Source GRN: GRN-MOH-0001
- Assigned To: District Hospital A
- Status: Assigned

1.  AST-MOH-0002

- Name: Ultrasound Machine Unit 2
- Source Contract: CT-MOH-0001
- Source GRN: GRN-MOH-0001
- Assigned To: District Hospital B
- Status: Assigned

Requirements:

1.  Preserve exact business IDs.
2.  Ensure GRN is linked to accepted delivery.
3.  Ensure assets are linked to GRN and contract.
4.  Output GRN and asset summary.

Constraints:

- Do not add disposal/maintenance/transfer complexity.
- Keep this minimal and traceable.

Acceptance criteria:

- GRN-MOH-0001 exists in Posted state
- store receipt exists
- AST-MOH-0001 and AST-MOH-0002 exist and are assigned
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  stores/assets summary

**GOLD-SEED-015 — Implement verify_minimal_golden command**

**Cursor prompt**

Writing

You are implementing a bounded verification task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-015
- Title: Implement verify_minimal_golden command

Context:

- Developers and testers need a quick way to verify the Minimal Golden Scenario is loaded correctly.

Task:  
Implement verify_minimal_golden.

The output should summarize:

- master data seeded
- strategy chain seeded
- budget seeded
- users seeded
- scenario business IDs present:
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

Also verify:

- requisition reservation exists
- contract commitment exists
- asset trace chain is intact at least to contract and GRN

Requirements:

1.  Make output concise and readable.
2.  Make missing records obvious.
3.  Document how to run it.

Constraints:

- Do not build a dashboard.
- Keep this command/report oriented.

Acceptance criteria:

- command exists
- output is useful to testers and developers

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  sample output structure

**GOLD-SEED-016 — Implement reset_minimal_golden command**

**Cursor prompt**

Writing

You are implementing a bounded reset task in a modular Frappe-based system called KenTender.

Story:

- ID: GOLD-SEED-016
- Title: Implement reset_minimal_golden command

Context:

- Testers need one reliable way to restore the exact Minimal Golden Scenario.

Task:  
Implement reset_minimal_golden.

Expected behavior:

1.  Load or restore in this order:
    - base reference
    - strategy
    - budget
    - users
    - requisition
    - planning
    - tender
    - bids/opening
    - evaluation
    - award
    - contract
    - inspection/acceptance
    - stores/assets
2.  Respect dependency order.
3.  Print a final summary of all major business IDs and scenario state.

Requirements:

- deterministic
- documented
- suitable for QA/UAT repetition

Constraints:

- do not load unrelated negative scenarios
- do not create hidden extra data beyond the golden scenario unless technically required and documented

Acceptance criteria:

- reset command restores the exact golden scenario
- summary output is useful
- command is repeatable

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  sample output structure

**Recommended implementation order**

Run in this order:

1.  GOLD-SEED-001
2.  GOLD-SEED-002
3.  GOLD-SEED-003
4.  GOLD-SEED-004
5.  GOLD-SEED-005
6.  GOLD-SEED-006
7.  GOLD-SEED-007
8.  GOLD-SEED-008
9.  GOLD-SEED-009
10. GOLD-SEED-010
11. GOLD-SEED-011
12. GOLD-SEED-012
13. GOLD-SEED-013
14. GOLD-SEED-014
15. GOLD-SEED-015
16. GOLD-SEED-016

**Review checklist after each Cursor run**

Check these every time:

**Structural**

- Did it preserve the exact IDs?
- Did it create only the intended records?
- Did it respect load order?

**Integrity**

- Are the links correct?
- Are states exactly as defined?
- Are ledger movements traceable?

**Reusability**

- Is the loader idempotent enough?
- Is output readable?
- Is behavior documented?

**Strong recommendation**

Use this Minimal Golden Scenario as:

- your **default dev seed**
- your **default QA reset**
- your **demo baseline**
- your **first audit walk-through dataset**

Then build every new scenario as a deviation from this baseline.