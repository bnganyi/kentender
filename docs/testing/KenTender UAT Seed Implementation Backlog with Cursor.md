# KenTender UAT Seed Implementation Backlog with Cursor-ready Prompts

This backlog covers:

- seeded test users
- persona-role assignment
- baseline reference fixtures
- scenario pack loaders
- reset commands
- fixture conventions
- UAT metadata helpers

This should be built in parallel with Wave 2 backend work.

**Epic overview**

**EPIC-UAT-001 — Test User and Persona Foundation**

Owns:

- seeded user accounts
- role mappings
- default workspace profile setup
- supplier test users

**EPIC-UAT-002 — Baseline Reference Seed Packs**

Owns:

- base reference data
- base strategy data
- base budget data
- deterministic fixture conventions

**EPIC-UAT-003 — Scenario Pack Loaders**

Owns:

- SP1 through SP7 loaders
- linked business scenario fixtures
- known starting states

**EPIC-UAT-004 — Reset and Reload Commands**

Owns:

- baseline reset
- per-scenario reset
- full end-to-end reset

**EPIC-UAT-005 — UAT Metadata and Testability Helpers**

Owns:

- scenario markers
- known test record labels
- UAT notes
- convenience identification/reporting helpers

**Recommended build order**

1.  UAT-STORY-001 — fixture folder structure and conventions
2.  UAT-STORY-002 — seeded internal users
3.  UAT-STORY-003 — seeded supplier users
4.  UAT-STORY-004 — role/persona assignment loader
5.  UAT-STORY-005 — BASE-REF loader
6.  UAT-STORY-006 — BASE-STRAT loader
7.  UAT-STORY-007 — BASE-BUD loader
8.  UAT-STORY-008 — SP1 loader
9.  UAT-STORY-009 — SP2 loader
10. UAT-STORY-010 — SP3 loader
11. UAT-STORY-011 — SP4 loader
12. UAT-STORY-012 — SP5 loader
13. UAT-STORY-013 — SP6 loader
14. UAT-STORY-014 — SP7 loader
15. UAT-STORY-015 — reset command framework
16. UAT-STORY-016 — baseline reset commands
17. UAT-STORY-017 — scenario reset commands
18. UAT-STORY-018 — full E2E reset command
19. UAT-STORY-019 — UAT metadata helpers
20. UAT-STORY-020 — seed verification report command

**EPIC-UAT-001 — Test User and Persona Foundation**

**UAT-STORY-001 — Create UAT fixture folder structure and conventions**

**App:** kentender_core or repo-level support area  
**Priority:** Critical  
**Depends on:** workspace foundation only

**Objective**  
Create a standard structure for UAT fixtures, loaders, and scenario documentation.

**Scope**

- /uat/seed_packs/
- /uat/users/
- /uat/journeys/
- README conventions
- deterministic naming rules

**Acceptance criteria**

- UAT structure exists
- naming conventions documented
- easy for developers to extend

**Cursor prompt**

Writing

You are implementing a bounded UAT infrastructure task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-001
- Epic: EPIC-UAT-001
- Title: Create UAT fixture folder structure and conventions

Context:

- KenTender requires repeatable UI-based acceptance testing.
- UAT must rely on deterministic seed packs and known test users.
- Recommended structure includes:
    - /uat/seed_packs/
    - /uat/users/
    - /uat/journeys/

Task:  
Create the UAT folder structure and developer conventions.

Requirements:

1.  Add a clear UAT support structure in the repository.
2.  Add README/developer notes covering:
    - seed pack naming
    - user fixture naming
    - scenario pack naming
    - reset strategy naming
3.  Make the structure easy to extend for SP1–SP7 and future packs.

Constraints:

- Do not implement all loaders yet.
- Keep structure simple and deterministic.
- Do not bury UAT conventions across many files.

Acceptance criteria:

- UAT folder structure exists
- conventions are documented
- future stories have a clear place to live

At the end, provide:

1.  files/folders created
2.  assumptions made
3.  open questions
4.  recommended future file placement

**UAT-STORY-002 — Implement seeded internal test users**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** UAT-STORY-001

**Objective**  
Create deterministic internal test users for all core personas.

**Users**

- requisitioner.test
- hod.test
- strategy.test
- planningauthority.test
- budgetofficer.test
- financeapprover.test
- procurement.test
- headofprocurement.test
- openingchair.test
- openingmember.test
- evaluator1.test
- evaluator2.test
- evaluationchair.test
- accountingofficer.test
- contractmanager.test
- inspector.test
- complaintschair.test
- complaintsmember.test
- storekeeper.test
- assetofficer.test
- auditor.test
- sysadmin.test

**Cursor prompt**

Writing

You are implementing a bounded UAT user-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-002
- Epic: EPIC-UAT-001
- Title: Implement seeded internal test users

Context:

- KenTender UAT requires deterministic internal persona users.
- These users should be easy to load repeatedly and recognize clearly.

Task:  
Implement seeded internal test user creation/loading support for these users:

- requisitioner.test
- hod.test
- strategy.test
- planningauthority.test
- budgetofficer.test
- financeapprover.test
- procurement.test
- headofprocurement.test
- openingchair.test
- openingmember.test
- evaluator1.test
- evaluator2.test
- evaluationchair.test
- accountingofficer.test
- contractmanager.test
- inspector.test
- complaintschair.test
- complaintsmember.test
- storekeeper.test
- assetofficer.test
- auditor.test
- sysadmin.test

Requirements:

1.  Create a deterministic fixture/loader for internal test users.
2.  Use clear metadata or comments so each user’s intended persona is obvious.
3.  Keep user creation idempotent where practical.
4.  Add a verification mechanism or simple report output showing loaded users.

Constraints:

- Do not assign final business roles in this story unless needed for integrity; that can be separated if cleaner.
- Do not mix supplier users here.
- Keep passwords/credentials handling consistent with repo policy.

Acceptance criteria:

- internal test users can be loaded deterministically
- implementation is reusable
- verification output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  how to run/verify the user load

**UAT-STORY-003 — Implement seeded supplier test users**

**App:** kentender_core or supplier-facing app support  
**Priority:** Critical  
**Depends on:** UAT-STORY-001

**Users**

- supplieradmin1.test
- supplieruser1.test
- supplieradmin2.test

**Cursor prompt**

Writing

You are implementing a bounded UAT supplier-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-003
- Epic: EPIC-UAT-001
- Title: Implement seeded supplier test users

Context:

- Supplier UAT requires deterministic supplier-side accounts.
- At minimum we need:
    - supplieradmin1.test
    - supplieruser1.test
    - supplieradmin2.test

Task:  
Implement deterministic seeded supplier test user creation/loading support.

Requirements:

1.  Create supplier-side test users in a repeatable way.
2.  Keep them clearly identifiable as UAT accounts.
3.  Prepare the structure so they can later be linked to seeded supplier organizations.
4.  Add verification output or a check command.

Constraints:

- Do not implement all supplier organization data here unless needed minimally.
- Keep this story focused on user fixture creation.

Acceptance criteria:

- supplier test users can be loaded
- implementation is deterministic
- verification exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  how to run/verify the user load

**UAT-STORY-004 — Implement role/persona assignment loader**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** UAT-STORY-002, UAT-STORY-003, role framework

**Objective**  
Assign the correct UAT personas to the seeded users.

**Cursor prompt**

Writing

You are implementing a bounded UAT persona-assignment task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-004
- Epic: EPIC-UAT-001
- Title: Implement role/persona assignment loader

Context:

- Seeded users must reflect realistic UAT personas.
- This story should assign intended roles/persona mappings to the seeded users.

Task:  
Implement a deterministic role/persona assignment loader for the seeded UAT users.

Requirements:

1.  Map each seeded user to the appropriate role set as defined in the UAT design.
2.  Keep the implementation idempotent.
3.  Make assignments easy to inspect and update later.
4.  Provide verification output showing user -> role mappings.

Constraints:

- Do not implement all business object assignments here.
- Keep persona mapping aligned with the approved UAT matrix.
- Avoid hidden side effects outside role assignment.

Acceptance criteria:

- UAT users receive intended role sets
- mappings are verifiable
- loader is repeatable

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  role mappings applied

**EPIC-UAT-002 — Baseline Reference Seed Packs**

**UAT-STORY-005 — Implement BASE-REF loader**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** core master data stories complete

**Scope**

- procuring entities
- departments
- funding sources
- procurement categories
- procurement methods
- numbering policies
- document type registry essentials

**Cursor prompt**

Writing

You are implementing a bounded UAT baseline-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-005
- Epic: EPIC-UAT-002
- Title: Implement BASE-REF loader

Context:

- BASE-REF is the foundational UAT reference pack.
- It should seed deterministic master/reference data needed by later scenario packs.

Task:  
Implement the BASE-REF loader.

Must seed:

- at least one procuring entity
- several departments/business units
- funding sources
- procurement categories
- procurement methods
- numbering/reference policies
- essential document types

Requirements:

1.  Make the loader deterministic and idempotent where practical.
2.  Use recognizable UAT-friendly names/codes.
3.  Output a summary of what was created/verified.

Constraints:

- Do not seed strategy or budget data here.
- Keep the baseline practical, not huge.
- Do not create ad hoc inconsistent codes.

Acceptance criteria:

- BASE-REF can be loaded repeatedly
- reference records exist in known form
- output/verification exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  seeded reference records summary

**UAT-STORY-006 — Implement BASE-STRAT loader**

**App:** kentender_strategy  
**Priority:** Critical  
**Depends on:** strategy module baseline complete, BASE-REF

**Scope**

- national framework
- entity strategic plan
- program
- sub-program
- indicator
- target

**Cursor prompt**

Writing

You are implementing a bounded UAT baseline-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-006
- Epic: EPIC-UAT-002
- Title: Implement BASE-STRAT loader

Context:

- BASE-STRAT seeds deterministic strategic hierarchy for later UAT journeys.

Task:  
Implement the BASE-STRAT loader.

Must seed:

- one national framework hierarchy
- one entity strategic plan
- one or more programs
- one or more sub-programs
- at least one output indicator
- at least one performance target

Requirements:

1.  Seed data must align correctly with BASE-REF entity/department context.
2.  Use stable, recognizable UAT labels/codes.
3.  Output a summary of seeded strategic context.

Constraints:

- Do not create large amounts of unnecessary strategy data.
- Keep the dataset small but sufficient for requisition and budget scenarios.

Acceptance criteria:

- BASE-STRAT loads deterministically
- strategic linkage is valid
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  seeded strategy summary

**UAT-STORY-007 — Implement BASE-BUD loader**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** budget baseline complete, BASE-REF, BASE-STRAT

**Scope**

- budget control period
- budget
- budget lines
- one healthy budget line
- one constrained budget line for negative tests

**Cursor prompt**

Writing

You are implementing a bounded UAT baseline-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-007
- Epic: EPIC-UAT-002
- Title: Implement BASE-BUD loader

Context:

- BASE-BUD seeds deterministic budget control data for UAT.
- We need both positive and negative test conditions.

Task:  
Implement the BASE-BUD loader.

Must seed:

- one open budget control period
- one active budget
- at least two budget lines:
    - one with sufficient availability
    - one intentionally constrained for insufficient-funds testing

Requirements:

1.  Budget lines must link validly to BASE-STRAT hierarchy.
2.  Use stable UAT-friendly codes and labels.
3.  Output a summary of seeded budget state.

Constraints:

- Do not seed requisitions or downstream procurement objects here.
- Keep the data minimal but sufficient for SP1 and later packs.

Acceptance criteria:

- BASE-BUD loads deterministically
- budget lines are valid and usable
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  seeded budget summary

**EPIC-UAT-003 — Scenario Pack Loaders**

**UAT-STORY-008 — Implement SP1 loader (Requisition Flow Pack)**

**Cursor prompt**

Writing

You are implementing a bounded UAT scenario-fixture task in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-008
- Epic: EPIC-UAT-003
- Title: Implement SP1 loader (Requisition Flow Pack)

Context:

- SP1 supports requisition flow acceptance testing.
- It depends on BASE-REF, BASE-STRAT, and BASE-BUD.

Task:  
Implement SP1 scenario loader.

Must seed:

- one draft-ready requisition scenario
- one returned requisition scenario
- one approved requisition scenario
- proper user/persona context for requisitioner, HOD, finance approver, and procurement officer

Requirements:

1.  Use realistic but deterministic values.
2.  Ensure records are in known states for AT-REQ-001 and AT-REQ-002.
3.  Provide output showing the key record IDs/business IDs.

Constraints:

- Do not seed planning/tender records here.
- Keep scenario state clear and minimal.

Acceptance criteria:

- SP1 loads deterministically
- requisition scenarios are in correct known states
- summary output exists

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  seeded scenario summary

**UAT-STORY-009 — Implement SP2 loader (Planning and Tender Preparation Pack)**

**Cursor prompt**

Writing

Implement SP2 scenario loader for KenTender.

Purpose:

- support procurement planning and tender preparation UAT

Must seed:

- approved requisitions suitable for planning
- one draft procurement plan
- one active procurement plan
- at least one consolidation scenario
- at least one fragmentation warning scenario
- one plan item ready for tender creation

Requirements:

- deterministic, small dataset
- summary output of key business IDs
- aligned with BASE packs and SP1 where needed

Constraints:

- do not publish tenders here unless clearly part of scenario design

**UAT-STORY-010 — Implement SP3 loader (Published Tender and Bid Submission Pack)**

**Cursor prompt**

Writing

Implement SP3 scenario loader for KenTender.

Purpose:

- support published tender, supplier bid submission, and opening preparation UAT

Must seed:

- one published tender
- criteria and tender documents
- visibility rules
- at least two eligible supplier organizations/users
- one draft bid scenario
- one submitted bid scenario
- one withdrawn or superseded submission scenario
- one scheduled opening session

Requirements:

- deterministic and repeatable
- summary output includes tender ID and bid IDs
- suitable for AT-BID-001 and AT-OPEN-001

Constraints:

- do not seed evaluation results here

**UAT-STORY-011 — Implement SP4 loader (Evaluation and Award Pack)**

**Cursor prompt**

Writing

Implement SP4 scenario loader for KenTender.

Purpose:

- support evaluation and award UAT

Must seed:

- one tender with opening completed
- opening register
- at least two opened bids
- evaluator assignments
- conflict declaration pending state
- one evaluation stage in progress
- one draft evaluation report
- one draft award decision

Requirements:

- deterministic and role-aware
- suitable for AT-EVAL-001 and AT-AWD-001
- summary output includes evaluation and award references

Constraints:

- do not seed contract objects here

**UAT-STORY-012 — Implement SP5 loader (Contract and Inspection Pack)**

**Cursor prompt**

Writing

Implement SP5 scenario loader for KenTender.

Purpose:

- support contract, signing, activation, inspection, and acceptance UAT

Must seed:

- one approved award ready for contract
- one draft contract
- one approved contract pending signature
- one signed/active contract
- milestones and deliverables
- at least one inspection method template
- one scheduled inspection
- one parameter-based inspection scenario
- one non-conformance or partial acceptance scenario

Requirements:

- deterministic and suitable for AT-CON-001 and AT-INSP-001
- summary output includes contract and inspection IDs

Constraints:

- do not seed complaint holds here

**UAT-STORY-013 — Implement SP6 loader (Complaint and Hold Pack)**

**Cursor prompt**

Writing

Implement SP6 scenario loader for KenTender.

Purpose:

- support complaint submission, hold application, review, and decision UAT

Must seed:

- one award in standstill or hold-sensitive state
- one supplier able to file complaint
- one complaint draft or submitted scenario
- one complaint awaiting admissibility
- one complaint with hold already applied
- review panel assignments

Requirements:

- deterministic
- suitable for AT-CMP-001
- summary output includes complaint and affected award references

Constraints:

- do not broaden into unrelated procurement setup beyond what is required

**UAT-STORY-014 — Implement SP7 loader (Stores and Assets Pack)**

**Cursor prompt**

Writing

Implement SP7 scenario loader for KenTender.

Purpose:

- support stores and asset UAT

Must seed:

- one accepted goods-type output eligible for stores receipt
- one procurement goods receipt draft
- one posted goods receipt
- one issue-ready stock line
- one reconciliation variance scenario
- one assetizable accepted item
- one pending asset registration candidate
- one already registered procured asset

Requirements:

- deterministic and suitable for AT-STORES-001 and AT-ASSET-001
- summary output includes receipt and asset references

Constraints:

- do not seed excessive inventory complexity

**EPIC-UAT-004 — Reset and Reload Commands**

**UAT-STORY-015 — Implement reset command framework**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** UAT-STORY-001 through 014 structure

**Cursor prompt**

Writing

You are implementing a bounded UAT operations feature in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-015
- Epic: EPIC-UAT-004
- Title: Implement reset command framework

Context:

- KenTender UAT requires deterministic resets.
- We need a clear command pattern for loading and resetting baseline/scenario packs.

Task:  
Implement a command/framework pattern for UAT seed loading and reset operations.

Requirements:

1.  Provide a consistent command naming pattern for:
    - baseline load
    - scenario load
    - reset operations
2.  Make it easy to add new scenario loaders.
3.  Add developer-facing usage notes.

Constraints:

- Do not hardcode one giant all-in-one script only.
- Keep it modular and maintainable.
- Avoid destructive ambiguity.

Acceptance criteria:

- command framework exists
- future reset/load commands have a clear structure

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  example commands supported

**UAT-STORY-016 — Implement baseline reset commands**

**Cursor prompt**

Writing

Implement baseline reset commands for KenTender UAT.

Required commands:

- reset to BASE-REF
- reset to BASE-REF + BASE-STRAT
- reset to full baseline (BASE-REF + BASE-STRAT + BASE-BUD)

Requirements:

- deterministic
- clearly documented
- safe enough for UAT use
- provide summary output after execution

**UAT-STORY-017 — Implement scenario reset commands**

**Cursor prompt**

Writing

Implement scenario reset commands for KenTender UAT.

Required examples:

- reset to SP1
- reset to SP3
- reset to SP5
- reset to SP6

Requirements:

- each command should ensure prerequisite base packs are loaded
- output should summarize loaded scenario state
- implementation should be deterministic and repeatable

**UAT-STORY-018 — Implement full E2E reset command**

**Cursor prompt**

Writing

Implement a full end-to-end UAT reset command for KenTender.

Purpose:

- load baseline plus SP1 through SP7 in a coherent order

Requirements:

- respect dependency order
- provide a final summary of key seeded records
- keep the command deterministic
- document intended use for integrated UAT and demos

Constraints:

- do not create hidden state or ad hoc records outside the defined loaders

**EPIC-UAT-005 — UAT Metadata and Testability Helpers**

**UAT-STORY-019 — Implement UAT metadata helpers**

**App:** kentender_core  
**Priority:** Medium  
**Depends on:** seeded scenarios

**Objective**  
Make seeded records easy to identify in UI and troubleshooting.

**Scope**

- scenario tags
- predictable naming prefixes
- optional UAT note fields/helpers

**Cursor prompt**

Writing

You are implementing a bounded UAT usability feature in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-019
- Epic: EPIC-UAT-005
- Title: Implement UAT metadata helpers

Context:

- Testers and developers need to quickly identify seeded UAT records.
- Known business IDs, prefixes, or tags improve debugging and acceptance execution.

Task:  
Implement lightweight UAT metadata/testability helpers.

Requirements:

1.  Add a clean way to identify seeded UAT records, such as:
    - naming prefixes
    - scenario tags
    - metadata helpers
2.  Keep the approach lightweight and non-invasive.
3.  Make it useful in list views, debugging, and UAT support.

Constraints:

- Do not pollute production logic with heavy UAT-only fields unless optional and safe.
- Keep the implementation maintainable.

Acceptance criteria:

- seeded records are easier to identify
- approach is documented

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  how UAT records are identified

**UAT-STORY-020 — Implement seed verification report command**

**App:** kentender_core  
**Priority:** High  
**Depends on:** all major loaders

**Objective**  
Provide a quick way to verify that UAT users and scenarios are loaded correctly.

**Cursor prompt**

Writing

You are implementing a bounded UAT verification feature in a modular Frappe-based system called KenTender.

Story:

- ID: UAT-STORY-020
- Epic: EPIC-UAT-005
- Title: Implement seed verification report command

Context:

- After loading seed packs, testers and developers need a fast verification view.
- This should confirm key users, scenario packs, and major seeded business objects.

Task:  
Implement a seed verification report or command.

Requirements:

1.  Summarize:
    - seeded UAT users
    - loaded baseline packs
    - loaded scenario packs
    - key reference business IDs
2.  Make the output readable for developers and testers.
3.  Keep it deterministic and easy to run after reset/load operations.

Constraints:

- Do not build a full dashboard here.
- Keep it command/report oriented.

Acceptance criteria:

- verification command/report exists
- gives a useful summary of UAT state

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  sample output structure

**Recommended implementation order**

Use this order:

1.  UAT-STORY-001
2.  UAT-STORY-002
3.  UAT-STORY-003
4.  UAT-STORY-004
5.  UAT-STORY-005
6.  UAT-STORY-006
7.  UAT-STORY-007
8.  UAT-STORY-015
9.  UAT-STORY-016
10. UAT-STORY-008
11. UAT-STORY-009
12. UAT-STORY-010
13. UAT-STORY-011
14. UAT-STORY-012
15. UAT-STORY-013
16. UAT-STORY-014
17. UAT-STORY-017
18. UAT-STORY-018
19. UAT-STORY-019
20. UAT-STORY-020

That order gives you a usable UAT engine early, then fills in scenarios.

**Review checklist after each Cursor run**

For every UAT story, verify:

1.  Is the data deterministic?
2.  Is the loader idempotent enough for repeated QA/UAT use?
3.  Did it avoid mixing unrelated scenarios?
4.  Did it output enough verification information?
5.  Are business IDs/test labels recognizable?
6.  Will testers know where to start after loading it?