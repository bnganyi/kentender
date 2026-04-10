# Cursor ticket pack for MVP auto-seeding

**UAT-MVP-001 — Create MVP seed folder structure**

**Objective**  
Create the repo structure for MVP seed loaders and reset utilities.

**Cursor prompt**

Writing

You are implementing a bounded UAT infrastructure task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-001
- Title: Create MVP seed folder structure

Context:

- KenTender needs deterministic seed data for MVP acceptance testing.
- For MVP, only baseline and scenario packs SP1-SP3 are required.

Task:  
Create a clear seed-data structure for MVP loaders and utilities.

Required structure:

- /uat/seed_packs/base_ref/
- /uat/seed_packs/base_strat/
- /uat/seed_packs/base_bud/
- /uat/seed_packs/sp1_requisition/
- /uat/seed_packs/sp2_planning/
- /uat/seed_packs/sp3_tender_bids/
- /uat/users/
- /uat/utils/

Requirements:

1.  Add README notes describing the purpose of each folder.
2.  Keep the structure deterministic and easy to extend later.
3.  Prepare it for command-driven loading.

Constraints:

- Do not implement all loaders yet.
- Keep this story about folder structure and conventions only.

Acceptance criteria:

- folder structure exists
- conventions are documented
- future seed stories have a clear place to live

At the end, provide:

1.  files/folders created
2.  assumptions made
3.  open questions
4.  recommended next commands to implement

**UAT-MVP-002 — Seed internal MVP test users**

**Objective**  
Create only the minimum internal users required for MVP.

**Users**

- requisitioner.test
- hod.test
- finance.test
- procurement.test
- evaluator.test
- accounting.test

**Cursor prompt**

Writing

You are implementing a bounded UAT user-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-002
- Title: Seed internal MVP test users

Context:

- MVP UAT only needs a lean internal user set.

Task:  
Implement deterministic seeded internal user creation for:

- requisitioner.test
- hod.test
- finance.test
- procurement.test
- evaluator.test
- accounting.test

Requirements:

1.  Create an idempotent loader for these users.
2.  Make the users clearly identifiable as UAT accounts.
3.  Add a lightweight verification output listing created or existing users.

Constraints:

- Do not create the full long-form UAT user catalogue yet.
- Do not assign every future role; only what MVP needs.
- Keep credentials handling consistent with repo policy.

Acceptance criteria:

- users can be loaded deterministically
- verification output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  how to run and verify the loader

**UAT-MVP-003 — Seed supplier MVP test users**

**Users**

- supplier.test
- optional second bidder: supplier2.test

**Cursor prompt**

Writing

You are implementing a bounded UAT supplier-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-003
- Title: Seed supplier MVP test users

Context:

- MVP UAT needs at least one supplier user for bid submission.
- A second supplier is recommended for competition and opening scenarios.

Task:  
Implement deterministic supplier test user creation for:

- supplier.test
- supplier2.test (recommended)

Requirements:

1.  Make user creation idempotent.
2.  Keep users clearly marked as UAT fixtures.
3.  Prepare them for later linkage to seeded supplier records.
4.  Provide verification output.

Constraints:

- Do not implement full supplier organization complexity unless minimally needed.
- Keep this story focused on user creation.

Acceptance criteria:

- supplier test users can be loaded
- verification exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  how to run and verify the loader

**UAT-MVP-004 — Assign MVP roles/personas**

**Cursor prompt**

Writing

You are implementing a bounded UAT persona-assignment task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-004
- Title: Assign MVP roles/personas

Context:

- MVP test users must map to the minimum viable role set for end-to-end testing.

Task:  
Assign appropriate roles/personas to the seeded MVP users.

Minimum intended mappings:

- requisitioner.test -> requisitioner role(s)
- hod.test -> HOD role(s)
- finance.test -> finance approver role(s)
- procurement.test -> procurement officer role(s)
- evaluator.test -> evaluator role(s)
- accounting.test -> accounting officer role(s)
- supplier.test -> supplier user/admin role(s)
- supplier2.test -> supplier user/admin role(s)

Requirements:

1.  Make assignment loading idempotent.
2.  Add verification output showing user -> assigned roles.
3.  Keep mapping aligned with the MVP test workbook.

Constraints:

- Do not assign unnecessary advanced roles.
- Do not add complaint/stores/assets personas yet.

Acceptance criteria:

- all MVP users receive appropriate roles
- mapping is verifiable

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  actual mappings applied

**UAT-MVP-005 — Implement BASE-REF loader**

**Seed minimum**

- 1 entity
- 2–3 departments
- funding source
- procurement category
- procurement method
- numbering policies
- essential document types

**Cursor prompt**

Writing

You are implementing a bounded baseline-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-005
- Title: Implement BASE-REF loader

Context:

- BASE-REF provides the minimum shared reference data for MVP UAT.

Task:  
Implement deterministic BASE-REF seeding.

Must include:

- one procuring entity
- a small set of departments/business units
- one or more funding sources
- procurement categories
- procurement methods
- minimal numbering policies
- essential document type registry records

Requirements:

1.  Use stable, human-readable UAT codes and names.
2.  Make the loader idempotent where practical.
3.  Output a summary of seeded reference records.

Constraints:

- Do not seed strategy or budget here.
- Keep the dataset minimal and clean.

Acceptance criteria:

- BASE-REF loads successfully
- records are recognizable and reusable
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  summary of seeded records

**UAT-MVP-006 — Implement BASE-STRAT loader**

**Seed minimum**

- 1 national framework
- 1 entity strategic plan
- 1 program
- 1 sub-program
- 1 indicator
- 1 target

**Cursor prompt**

Writing

You are implementing a bounded baseline-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-006
- Title: Implement BASE-STRAT loader

Context:

- BASE-STRAT provides the minimum strategic structure for MVP UAT.

Task:  
Implement deterministic BASE-STRAT seeding.

Must include:

- one national framework hierarchy
- one entity strategic plan
- one program
- one sub-program
- one output indicator
- one performance target

Requirements:

1.  Ensure all linkages are valid.
2.  Keep the dataset minimal but sufficient for requisition and planning.
3.  Output a summary of seeded strategic records.

Constraints:

- Do not create many variants.
- Keep it small and easy for testers to understand.

Acceptance criteria:

- BASE-STRAT loads successfully
- strategy linkages are valid
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  summary of seeded records

**UAT-MVP-007 — Implement BASE-BUD loader**

**Seed minimum**

- 1 control period
- 1 budget
- 2 budget lines
    - one with sufficient funds
    - one constrained

**Cursor prompt**

Writing

You are implementing a bounded baseline-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-007
- Title: Implement BASE-BUD loader

Context:

- BASE-BUD provides the minimum budget control context for MVP UAT.
- We need both positive and negative test conditions.

Task:  
Implement deterministic BASE-BUD seeding.

Must include:

- one open budget control period
- one active budget
- at least two budget lines:
    - one with healthy availability
    - one intentionally constrained for insufficient-funds tests

Requirements:

1.  Link budget lines correctly to seeded strategy hierarchy.
2.  Use stable UAT-friendly codes and labels.
3.  Output a summary of seeded budget records.

Constraints:

- Do not seed requisitions yet.
- Keep data small and practical.

Acceptance criteria:

- BASE-BUD loads successfully
- budget lines are valid and recognizable
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  summary of seeded records

**UAT-MVP-008 — Implement SP1 loader (Requisition)**

**Seed minimum**

- one draft-ready requisition scenario
- one returned requisition scenario
- one approved requisition scenario

**Cursor prompt**

Writing

You are implementing a bounded UAT scenario-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-008
- Title: Implement SP1 loader (Requisition)

Context:

- SP1 supports MVP requisition acceptance testing.

Task:  
Implement deterministic SP1 seeding.

Must include:

- one draft-ready requisition scenario
- one returned requisition scenario
- one approved requisition scenario

Requirements:

1.  Use seeded users from the MVP user pack.
2.  Use valid strategy and budget references from the base packs.
3.  Ensure scenarios align with:
    - create requisition
    - return for revision
    - approve and planning-ready state
4.  Output business IDs and current states.

Constraints:

- Do not seed procurement plans here.
- Keep the scenarios easy to understand.

Acceptance criteria:

- SP1 loads deterministically
- requisition states are correct for testing
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  seeded business IDs and statuses

**UAT-MVP-009 — Implement SP2 loader (Planning)**

**Seed minimum**

- approved requisitions
- one draft plan
- one active plan
- one plan item ready for tender

**Cursor prompt**

Writing

You are implementing a bounded UAT scenario-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-009
- Title: Implement SP2 loader (Planning)

Context:

- SP2 supports MVP procurement planning and tender preparation testing.

Task:  
Implement deterministic SP2 seeding.

Must include:

- approved requisitions suitable for planning
- one draft procurement plan
- one active procurement plan
- at least one plan item ready for tender creation

Requirements:

1.  Keep the dataset small and aligned with MVP testing.
2.  Preserve traceability from requisitions to plan items.
3.  Output key business IDs and states.

Constraints:

- Do not publish tenders here.
- Do not seed fragmentation complexity unless it is simple and useful.

Acceptance criteria:

- SP2 loads successfully
- plan state is clear for testing
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  seeded business IDs and statuses

**UAT-MVP-010 — Implement SP3 loader (Tender, bids, opening-ready)**

**Seed minimum**

- one published tender
- one or two bids
- one scheduled opening session

**Cursor prompt**

Writing

You are implementing a bounded UAT scenario-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-010
- Title: Implement SP3 loader (Tender, bids, opening-ready)

Context:

- SP3 supports MVP tender publication, bid submission, and opening preparation testing.

Task:  
Implement deterministic SP3 seeding.

Must include:

- one published tender
- required criteria and documents sufficient for MVP testing
- at least one submitted bid
- ideally a second bid for opening/evaluation realism
- one scheduled opening session

Requirements:

1.  Use seeded supplier users.
2.  Keep scenario state suitable for:
    - bid submission tests
    - opening readiness tests
3.  Output key tender, bid, and opening session IDs.

Constraints:

- Do not seed full evaluation or contract artifacts here.
- Keep the dataset small and repeatable.

Acceptance criteria:

- SP3 loads successfully
- published tender and bid states are clear
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  seeded business IDs and statuses

**UAT-MVP-011 — Implement reset_uat_mvp command**

**Purpose**

One command to get a clean MVP UAT state.

**Cursor prompt**

Writing

You are implementing a bounded UAT operations feature in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-011
- Title: Implement reset_uat_mvp command

Context:

- MVP testers need one reliable reset command.
- It should restore the minimum end-to-end UAT dataset.

Task:  
Implement reset_uat_mvp.

Expected behavior:

1.  Load or restore:
    - BASE-REF
    - BASE-STRAT
    - BASE-BUD
    - SP1
    - SP2
    - SP3
2.  Respect dependency order.
3.  Print a useful final summary of key users and business IDs.

Requirements:

- deterministic
- documented
- repeatable for QA/UAT

Constraints:

- Do not include SP4-SP7.
- Do not create hidden extra records outside the defined packs.

Acceptance criteria:

- reset_uat_mvp produces a known MVP UAT state
- summary output is useful to testers and developers

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  sample output structure

**UAT-MVP-012 — Implement verify_uat_mvp command**

**Purpose**

Quick check after reset/load.

**Cursor prompt**

Writing

You are implementing a bounded UAT verification feature in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-MVP-012
- Title: Implement verify_uat_mvp command

Context:

- After loading MVP UAT data, testers and developers need a fast verification command.

Task:  
Implement verify_uat_mvp.

The verification output should summarize:

- seeded internal users
- seeded supplier users
- baseline packs loaded
- key requisition IDs
- key procurement plan IDs
- key tender and bid IDs
- opening session ID

Requirements:

1.  Keep output readable and concise.
2.  Make it easy to spot missing or broken seed state.
3.  Document how to run it.

Constraints:

- Do not build a full dashboard.
- Keep this command/report focused on MVP UAT verification.

Acceptance criteria:

- command exists
- output is useful and deterministic

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  sample output structure

**Recommended implementation order**

Run these in Cursor in this exact order:

1.  UAT-MVP-001
2.  UAT-MVP-002
3.  UAT-MVP-003
4.  UAT-MVP-004
5.  UAT-MVP-005
6.  UAT-MVP-006
7.  UAT-MVP-007
8.  UAT-MVP-008
9.  UAT-MVP-009
10. UAT-MVP-010
11. UAT-MVP-011
12. UAT-MVP-012

**Review checklist for each seed story**

After each Cursor run, check:

- Is the loader deterministic?
- Is it idempotent enough for repeated QA/UAT use?
- Are the records clearly recognizable?
- Does it stay within MVP scope?
- Does it print enough verification info?
- Does it avoid seeding future-phase complexity?