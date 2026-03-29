# KenTender Master Epic Map

**Wave 0 — detailed tickets, acceptance criteria, and recommended Cursor execution order:** see [`Wave 0 Ticket Pack.md`](Wave%200%20Ticket%20Pack.md) and the thin tracker [`WAVE 0 BACKLOG.md`](WAVE%200%20BACKLOG.md). **Wave 1** is closed: [`WAVE 1 BACKLOG.md`](Wave%201%20BACKLOG.md). **Wave 2 (procurement):** [`WAVE 2 BACKLOG.md`](Wave%202%20BACKLOG.md), [`docs/prompts/Wave 2 Ticket Pack.md`](../prompts/Wave%202%20Ticket%20Pack.md). This document remains the high-level epic/story index and wave breakdown.

Below is a **Master Epic Map** and a **Wave 0 / Wave 1 / Wave 2** story index designed specifically for Cursor-driven implementation.

This is the point where the project becomes executable.

# 1\. Delivery model

We will use this hierarchy:

- **Epic** = a major functional deliverable
- **Story** = a bounded engineering unit
- **Cursor Prompt** = one implementation instruction set per story

For now, we’ll fully define:

- **Wave 0 — Platform Foundation**
- **Wave 1 — Strategy + Budget Backbone**
- **Wave 2 — Procurement Demand and Planning** (requisition → plan → tender gate; see §2 and [`WAVE 2 BACKLOG.md`](Wave%202%20BACKLOG.md))

That is enough to start building without architectural drift.

# 2\. Master Epic Map

**Wave 0 — Platform Foundation**

**EPIC-CORE-001 — Repository and Multi-App Foundation**

App(s):

- all apps scaffolded  
    Priority:
- Critical  
    Depends on:
- none  
    Outcome:
- modular app structure, shared conventions, installability

**EPIC-CORE-002 — Shared Master Data and Entity Model**

App:

- kentender_core  
    Priority:
- Critical  
    Depends on:
- EPIC-CORE-001  
    Outcome:
- procuring entities, departments, funding sources, procurement categories/methods, reference policies

**EPIC-CORE-003 — Shared Security, Scope, and Permission Framework**

App:

- kentender_core  
    Priority:
- Critical  
    Depends on:
- EPIC-CORE-001, EPIC-CORE-002  
    Outcome:
- entity scoping, assignment-based access helpers, permission utilities

**EPIC-CORE-004 — Workflow Guard and Business Action Framework**

App:

- kentender_core  
    Priority:
- Critical  
    Depends on:
- EPIC-CORE-001, EPIC-CORE-003  
    Outcome:
- server-side guarded actions, conflict-of-duty enforcement hooks

**EPIC-CORE-005 — Audit Event and Exception Framework**

App:

- kentender_core, kentender_compliance  
    Priority:
- Critical  
    Depends on:
- EPIC-CORE-001  
    Outcome:
- event-based audit infrastructure, exception records

**EPIC-CORE-006 — Typed Document and File Control Framework**

App:

- kentender_core  
    Priority:
- High  
    Depends on:
- EPIC-CORE-001  
    Outcome:
- typed attachments, sensitivity classes, protected file patterns

**EPIC-CORE-007 — Notification Framework**

App:

- kentender_core, kentender_integrations  
    Priority:
- Medium  
    Depends on:
- EPIC-CORE-001  
    Outcome:
- template-driven internal/external notifications

**Wave 1 — Strategic and Budget Backbone**

**EPIC-STRAT-001 — National Framework Reference Model**

App:

- kentender_strategy  
    Priority:
- Critical  
    Depends on:
- EPIC-CORE-002  
    Outcome:
- national frameworks, pillars, objectives

**EPIC-STRAT-002 — Entity Strategic Planning Model**

App:

- kentender_strategy  
    Priority:
- Critical  
    Depends on:
- EPIC-STRAT-001  
    Outcome:
- entity strategic plans, programs, sub-programs

**EPIC-STRAT-003 — Indicators, Targets, and Strategic Validation Services**

App:

- kentender_strategy  
    Priority:
- Critical  
    Depends on:
- EPIC-STRAT-002  
    Outcome:
- output indicators, performance targets, validation service layer

**EPIC-BUD-001 — Budget Control Period and Budget Header Model**

App:

- kentender_budget  
    Priority:
- Critical  
    Depends on:
- EPIC-CORE-002, EPIC-STRAT-003  
    Outcome:
- budget periods, budget versions

**EPIC-BUD-002 — Budget Line Model and Strategic/Budget Linkage**

App:

- kentender_budget  
    Priority:
- Critical  
    Depends on:
- EPIC-BUD-001, EPIC-STRAT-003  
    Outcome:
- budget lines with strategic references

**EPIC-BUD-003 — Budget Ledger and Availability Engine**

App:

- kentender_budget  
    Priority:
- Critical  
    Depends on:
- EPIC-BUD-002, EPIC-CORE-005  
    Outcome:
- reservation, commitment, release, availability calculation

**EPIC-BUD-004 — Budget Revision and Allocation Framework**

App:

- kentender_budget  
    Priority:
- High  
    Depends on:
- EPIC-BUD-002, EPIC-BUD-003  
    Outcome:
- budget revision workflow, line-level adjustments

**EPIC-BUD-005 — Budget Validation APIs for Downstream Modules**

App:

- kentender_budget  
    Priority:
- Critical  
    Depends on:
- EPIC-BUD-003  
    Outcome:
- service interface for requisition/planning/contract variation use

**Wave 2 — Procurement Demand and Planning**

**EPIC-PROC-001 — Purchase Requisition**

App:

- kentender_procurement  
    Priority:
- Critical  
    Depends on:
- EPIC-BUD-005, EPIC-STRAT-003, EPIC-CORE-003 / EPIC-CORE-004 (guards, actions)  
    Outcome:
- internal demand record, items, approvals, amendments, planning linkage, budget reservation on approval

**EPIC-PROC-002 — Procurement Plan**

App:

- kentender_procurement  
    Priority:
- Critical  
    Depends on:
- EPIC-PROC-001 (requisition + planning link), EPIC-BUD-001–005  
    Outcome:
- plan header/items, consolidation, fragmentation controls, revisions, tender eligibility gate

**Tracking:** [`WAVE 2 BACKLOG.md`](Wave%202%20BACKLOG.md) (steps **1–22**). **Prompts:** [`docs/prompts/Wave 2 Ticket Pack.md`](../prompts/Wave%202%20Ticket%20Pack.md).

# 3\. Story breakdown — Wave 0

**EPIC-CORE-001 — Repository and Multi-App Foundation**

**STORY-CORE-001**

Title:  
Initialize multi-app KenTender workspace  
Outcome:

- app skeletons created
- install order documented
- shared Python package conventions established

**STORY-CORE-002**

Title:  
Set app dependency boundaries and shared config conventions  
Outcome:

- dependency map reflected in app metadata
- no circular dependencies
- common naming conventions documented in code comments/README

**STORY-CORE-003**

Title:  
Create common service module structure across apps  
Outcome:

- /services, /doctype, /api, /tests layout standardized

**EPIC-CORE-002 — Shared Master Data and Entity Model**

**STORY-CORE-004**

Title:  
Implement Procuring Entity DocType  
Outcome:

- entity scope model exists

**STORY-CORE-005**

Title:  
Implement Department / Business Unit DocType  
Outcome:

- departments linked to entities

**STORY-CORE-006**

Title:  
Implement shared master data DocTypes  
Scope:

- Funding Source
- Procurement Category
- Procurement Method
- Reference Number Policy
- Document Type Registry

**STORY-CORE-007**

Title:  
Implement naming/number generation service  
Outcome:

- reusable business_id generator pattern

**EPIC-CORE-003 — Shared Security, Scope, and Permission Framework**

**STORY-CORE-008**

Title:  
Implement entity scope utility layer  
Outcome:

- reusable scoping helpers for entity-bound DocTypes

**STORY-CORE-009**

Title:  
Implement assignment-based access helper framework  
Outcome:

- committee/case assignment utilities

**STORY-CORE-010**

Title:  
Implement permission query helper framework  
Outcome:

- common filters for entity/self/assignment scope

**STORY-CORE-011**

Title:  
Implement separation-of-duty conflict rule DocType and service  
Outcome:

- rules can be stored and evaluated centrally

**EPIC-CORE-004 — Workflow Guard and Business Action Framework**

**STORY-CORE-012**

Title:  
Implement Workflow Guard Rule DocType  
Outcome:

- guard rules configurable

**STORY-CORE-013**

Title:  
Implement shared workflow guard service  
Outcome:

- pre-submit, pre-approve, pre-transition checks

**STORY-CORE-014**

Title:  
Implement controlled business action pattern  
Outcome:

- pattern for service actions like publish_\*, approve_\*, open_\*

**EPIC-CORE-005 — Audit Event and Exception Framework**

**STORY-CORE-015**

Title:  
Implement Exception Record DocType  
Outcome:

- controlled override object exists

**STORY-CORE-016**

Title:  
Implement audit event service and event schema  
Outcome:

- app-wide event logger

**STORY-CORE-017**

Title:  
Implement access-denied and sensitive-access audit hooks  
Outcome:

- sensitive access attempts logged

**EPIC-CORE-006 — Typed Document and File Control Framework**

**STORY-CORE-018**

Title:  
Implement shared typed attachment model  
Outcome:

- typed document metadata linked to business records

**STORY-CORE-019**

Title:  
Implement sensitivity classification handling  
Outcome:

- Public/Internal/Confidential/Sealed Procurement behaviors defined in code

**STORY-CORE-020**

Title:  
Implement protected file access service for sensitive documents  
Outcome:

- no generic direct exposure for sealed docs

**EPIC-CORE-007 — Notification Framework**

**STORY-CORE-021**

Title:  
Implement Notification Template DocType  
Outcome:

- template-driven notifications possible

**STORY-CORE-022**

Title:  
Implement notification dispatch service abstraction  
Outcome:

- internal API ready for in-app/email/SMS later

# 4\. Story breakdown — Wave 1

**Tracking and prompts:** Sprint status and step order live in [`WAVE 1 BACKLOG.md`](Wave%201%20BACKLOG.md). Full objectives, acceptance criteria, and Cursor prompts are in [`docs/prompts/Wave 1 Ticket Pack.md`](../prompts/Wave%201%20Ticket%20Pack.md). **Important:** implementation order is **not** strictly numeric for strategy — **STORY-STRAT-006** runs **after** **STORY-STRAT-007**, **008**, and **009** (see backlog step list).

**Wave 1 status:** Closed (2026-03-28); all **26** backlog stories are **Done** in [`WAVE 1 BACKLOG.md`](Wave%201%20BACKLOG.md).

**Wave 2 — procurement**

Sprint tracker: [`WAVE 2 BACKLOG.md`](Wave%202%20BACKLOG.md). Full tickets and Cursor prompts: [`docs/prompts/Wave 2 Ticket Pack.md`](../prompts/Wave%202%20Ticket%20Pack.md). Execute **PROC-STORY-001** through **PROC-STORY-022** in the order listed in the pack (requisition **1–10**, then plan **11–22**).

**EPIC-STRAT-001 — National Framework Reference Model**

**STORY-STRAT-001**

Title:  
Implement National Framework DocType  
Outcome:

- read-only imported framework base object

**STORY-STRAT-002**

Title:  
Implement National Pillar and National Objective DocTypes  
Outcome:

- hierarchical national references

**STORY-STRAT-003**

Title:  
Implement national reference immutability rules  
Outcome:

- active imported reference records protected from casual edits

**EPIC-STRAT-002 — Entity Strategic Planning Model**

**STORY-STRAT-004**

Title:  
Implement Entity Strategic Plan DocType  
Outcome:

- versioned strategic plan object

**STORY-STRAT-005**

Title:  
Implement Program and Sub Program DocTypes  
Outcome:

- entity-level strategic hierarchy under plan

**STORY-STRAT-006**

Title:  
Implement strategic revision model  
Scope:

- Strategic Revision Record
- active version/supersession logic

**EPIC-STRAT-003 — Indicators, Targets, and Strategic Validation Services**

**STORY-STRAT-007**

Title:  
Implement Output Indicator DocType  
Outcome:

- measurable indicator object

**STORY-STRAT-008**

Title:  
Implement Performance Target DocType  
Outcome:

- time-bound targets linked to indicators

**STORY-STRAT-009**

Title:  
Implement strategic linkage validation services  
Scope:

- validate program/sub-program/indicator/target/entity alignment  
    Outcome:
- downstream modules can call strategy services safely

**STORY-STRAT-010**

Title:  
Implement strategy query helpers and reports  
Outcome:

- active hierarchy lookup and basic reports

**EPIC-BUD-001 — Budget Control Period and Budget Header Model**

**STORY-BUD-001**

Title:  
Implement Budget Control Period DocType  
Outcome:

- entity fiscal control window exists

**STORY-BUD-002**

Title:  
Implement Budget DocType  
Outcome:

- versioned budget header model exists

**STORY-BUD-003**

Title:  
Implement budget version/supersession logic  
Outcome:

- active budget version control

**EPIC-BUD-002 — Budget Line Model and Strategic/Budget Linkage**

**STORY-BUD-004**

Title:  
Implement Budget Line DocType  
Outcome:

- primary budget control unit exists

**STORY-BUD-005**

Title:  
Implement budget line validation against strategy and entity scope  
Outcome:

- invalid cross-entity/cross-strategy links blocked

**STORY-BUD-006**

Title:  
Implement budget line derived totals fields and recalculation hooks  
Outcome:

- convenience totals maintained safely

**EPIC-BUD-003 — Budget Ledger and Availability Engine**

**STORY-BUD-007**

Title:  
Implement Budget Ledger Entry DocType  
Outcome:

- append-only control ledger exists

**STORY-BUD-008**

Title:  
Implement ledger posting service  
Scope:

- reserve
- release reservation
- commit
- release commitment  
    Outcome:
- no direct downstream ledger writes needed

**STORY-BUD-009**

Title:  
Implement availability calculation service  
Outcome:

- authoritative allocated/reserved/committed/available computation

**STORY-BUD-010**

Title:  
Implement idempotency and concurrency protection for budget actions  
Outcome:

- double reservation/double commit risk reduced

**EPIC-BUD-004 — Budget Revision and Allocation Framework**

**STORY-BUD-011**

Title:  
Implement Budget Allocation DocType  
Outcome:

- auditable allocation transactions exist

**STORY-BUD-012**

Title:  
Implement Budget Revision and Budget Revision Line DocTypes  
Outcome:

- controlled revision framework exists

**STORY-BUD-013**

Title:  
Implement budget revision apply service  
Outcome:

- revision application updates control state safely

**EPIC-BUD-005 — Budget Validation APIs for Downstream Modules**

**STORY-BUD-014**

Title:  
Implement downstream validation APIs  
Scope:

- validate budget line
- get availability
- validate funds or raise

**STORY-BUD-015**

Title:  
Implement budget audit event integration  
Outcome:

- all critical budget actions emit audit events

**STORY-BUD-016**

Title:  
Implement budget unit/integration tests  
Outcome:

- core ledger logic covered before requisition build starts

# 5\. Recommended first Cursor execution order

Do not start all stories at once. Use this order:

1.  STORY-CORE-001
2.  STORY-CORE-002
3.  STORY-CORE-003
4.  STORY-CORE-004
5.  STORY-CORE-005
6.  STORY-CORE-006
7.  STORY-CORE-007
8.  STORY-CORE-015
9.  STORY-CORE-016
10. STORY-CORE-018
11. STORY-CORE-019
12. STORY-CORE-008
13. STORY-CORE-009
14. STORY-CORE-010
15. STORY-CORE-011
16. STORY-CORE-012
17. STORY-CORE-013
18. STORY-CORE-014

Then move to strategy:

1.  STORY-STRAT-001
2.  STORY-STRAT-002
3.  STORY-STRAT-003
4.  STORY-STRAT-004
5.  STORY-STRAT-005
6.  STORY-STRAT-007
7.  STORY-STRAT-008
8.  STORY-STRAT-009
9.  STORY-STRAT-006
10. STORY-STRAT-010

Then budget:

1.  STORY-BUD-001
2.  STORY-BUD-002
3.  STORY-BUD-003
4.  STORY-BUD-004
5.  STORY-BUD-005
6.  STORY-BUD-007
7.  STORY-BUD-008
8.  STORY-BUD-009
9.  STORY-BUD-010
10. STORY-BUD-011
11. STORY-BUD-012
12. STORY-BUD-013
13. STORY-BUD-014
14. STORY-BUD-015
15. STORY-BUD-016

Then procurement (Wave 2 — [`WAVE 2 BACKLOG.md`](Wave%202%20BACKLOG.md)):

1.  PROC-STORY-001
2.  PROC-STORY-002
3.  PROC-STORY-003
4.  PROC-STORY-004
5.  PROC-STORY-005
6.  PROC-STORY-006
7.  PROC-STORY-007
8.  PROC-STORY-008
9.  PROC-STORY-009
10. PROC-STORY-010
11. PROC-STORY-011
12. PROC-STORY-012
13. PROC-STORY-013
14. PROC-STORY-014
15. PROC-STORY-015
16. PROC-STORY-016
17. PROC-STORY-017
18. PROC-STORY-018
19. PROC-STORY-019
20. PROC-STORY-020
21. PROC-STORY-021
22. PROC-STORY-022

That gives you a clean path from platform through strategy, budget, requisition, and tender-ready procurement plan items.

# 6\. Ticket template for your backlog tool

Use this structure for every story ticket.

**Ticket Header**

- Story ID
- Epic ID
- Title
- App
- Priority
- Dependencies

**Objective**

One short paragraph.

**Scope**

List exact items to build.

**Out of Scope**

List what must not be touched.

**Architecture Constraints**

Examples:

- no direct writes to ledger outside service layer
- use entity scoping helpers
- use audit service for all critical actions
- use server-side business actions for state changes

**Acceptance Criteria**

Bullet-point, testable.

**Required Tests**

List explicit tests.

**Cursor Prompt**

Paste the execution prompt here.

# 7\. Cursor prompt pack structure

For each story, use this pattern:

**A. Context**

What app and story this is.

**B. Design truth**

Summarize the non-negotiable rules from our design.

**C. Exact deliverables**

DocTypes, services, tests, reports.

**D. Constraints**

What Cursor must not do.

**E. Acceptance criteria**

Concrete outputs.

**F. Review checklist**

Ask Cursor to report:

- files created/modified
- assumptions made
- open questions
- tests added