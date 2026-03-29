# Wave 1 Ticket Pack

**EPIC-STRAT-001 — National Framework Reference Model**

**STORY-STRAT-001 — Implement National Framework DocType**

**App:** kentender_strategy  
**Priority:** Critical  
**Depends on:** STORY-CORE-004, STORY-CORE-006

**Objective**  
Create the top-level imported national planning framework record.

**Scope**

- National Framework DocType
- lifecycle/status support
- import/reference-oriented fields
- immutability-ready structure

**Out of scope**

- import batch tooling
- pillars/objectives
- entity plans

**Acceptance criteria**

- DocType exists
- key code uniqueness works
- active reference lock behavior scaffolded
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-001
- Epic: EPIC-STRAT-001
- Title: Implement National Framework DocType

Context:

- App: kentender_strategy
- National frameworks are imported read-only reference structures used by entity strategic plans.
- Examples include national development plans, medium-term plans, CIDPs, sector plans.
- These records are centrally managed and should be treated as locked references once active.

Task:  
Implement the National Framework DocType.

Required fields:

- business_id
- framework_code
- framework_name
- framework_type
- version_label
- status
- start_date
- end_date
- source_reference
- source_document_url
- import_batch_id
- imported_at
- imported_by
- is_locked_reference
- description

Requirements:

1.  Create the DocType.
2.  Enforce uniqueness for framework_code plus version semantics as appropriate.
3.  Add date sanity validation.
4.  Add guard behavior so active locked references are not casually editable.
5.  Add tests for:
    - valid create
    - duplicate key rejection
    - invalid date range rejection
    - lock behavior for active references

Constraints:

- Do not implement import pipeline logic yet.
- Do not add entity plan logic here.
- Keep this as a centrally managed reference object.

Acceptance criteria:

- DocType exists and validates correctly
- active lock behavior is in place or scaffolded cleanly
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-STRAT-002 — Implement National Pillar and National Objective DocTypes**

**App:** kentender_strategy  
**Priority:** Critical  
**Depends on:** STORY-STRAT-001

**Objective**  
Build the imported national hierarchy beneath the framework.

**Scope**

- National Pillar
- National Objective
- parent/child validation
- derived framework consistency

**Acceptance criteria**

- hierarchy works
- codes validate uniquely in sensible scope
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-002
- Epic: EPIC-STRAT-001
- Title: Implement National Pillar and National Objective DocTypes

Context:

- App: kentender_strategy
- National hierarchy is:  
    National Framework -> National Pillar -> National Objective
- These are imported/managed reference records.

Task:  
Implement:

1.  National Pillar
2.  National Objective

Required fields:

For National Pillar:

- business_id
- national_framework
- pillar_code
- pillar_name
- description
- display_order
- status

For National Objective:

- business_id
- national_framework
- national_pillar
- objective_code
- objective_name
- description
- display_order
- status

Requirements:

1.  Create both DocTypes.
2.  Enforce parent-child consistency.
3.  Ensure National Objective.national_framework matches its selected pillar’s framework.
4.  Add uniqueness rules for pillar/objective codes in a reasonable scope.
5.  Add tests covering:
    - valid hierarchy creation
    - invalid pillar/framework mismatch blocked
    - duplicate code behavior
    - framework derivation consistency

Constraints:

- Do not build entity strategy logic here.
- Keep the hierarchy strict.
- Keep records reference-oriented and centrally managed.

Acceptance criteria:

- both DocTypes exist
- hierarchy validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-STRAT-003 — Implement national reference immutability rules**

**App:** kentender_strategy  
**Priority:** High  
**Depends on:** STORY-STRAT-001, STORY-STRAT-002, STORY-CORE-013

**Objective**  
Make active imported national reference data operationally read-only.

**Scope**

- lock/edit restrictions for active framework/pillar/objective
- controlled admin-safe patterns only

**Acceptance criteria**

- active references cannot be casually edited
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded governance-control feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-003
- Epic: EPIC-STRAT-001
- Title: Implement national reference immutability rules

Context:

- App: kentender_strategy
- Active national framework reference records must behave as read-only references in normal operation.

Task:  
Implement immutability rules for:

- National Framework
- National Pillar
- National Objective

Requirements:

1.  Once a reference record is active and marked locked, normal edits should be blocked.
2.  Allow only tightly controlled changes if needed for system integrity, with clear code structure.
3.  Add tests demonstrating edit-block behavior on active locked records.

Constraints:

- Do not build a full revision/import replacement workflow yet.
- Do not weaken immutability for convenience.

Acceptance criteria:

- active locked records cannot be casually edited
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-STRAT-002 — Entity Strategic Planning Model**

**STORY-STRAT-004 — Implement Entity Strategic Plan DocType**

**App:** kentender_strategy  
**Priority:** Critical  
**Depends on:** STORY-STRAT-001, STORY-CORE-004, STORY-CORE-007

**Objective**  
Create the versioned entity strategy anchor.

**Scope**

- Entity Strategic Plan
- versioned/supersession-ready fields
- primary national framework linkage
- basic workflow-ready status model

**Acceptance criteria**

- DocType exists
- one current active version pattern supported
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-004
- Epic: EPIC-STRAT-002
- Title: Implement Entity Strategic Plan DocType

Context:

- App: kentender_strategy
- Entity Strategic Plan is the anchor for entity-level strategy and must be versioned and controlled.
- It links an entity to a primary national framework for a defined period.

Task:  
Implement the Entity Strategic Plan DocType.

Required fields:

- business_id
- plan_title
- procuring_entity
- plan_period_label
- version_no
- status
- start_date
- end_date
- primary_national_framework
- primary_alignment_basis
- is_current_active_version
- supersedes_plan
- superseded_by_plan
- revision_reason
- approval_status
- workflow_state
- strategy_manager
- planning_authority_owner
- remarks

Requirements:

1.  Create the DocType.
2.  Enforce valid date ranges.
3.  Enforce entity linkage.
4.  Support versioning/supersession fields cleanly.
5.  Add tests for:
    - valid create
    - invalid dates blocked
    - supersession fields behave consistently
    - active-version semantics scaffolded sensibly

Constraints:

- Do not implement full approval workflow engine here.
- Do not implement all downstream child structures yet.
- Keep this as a controlled document model.

Acceptance criteria:

- DocType exists
- versioned design is correctly scaffolded
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-STRAT-005 — Implement Program and Sub Program DocTypes**

**App:** kentender_strategy  
**Priority:** Critical  
**Depends on:** STORY-STRAT-004, STORY-STRAT-002

**Objective**  
Build entity-level strategic hierarchy under the plan.

**Scope**

- Program
- Sub Program
- hierarchy validation
- national objective mapping at program level

**Acceptance criteria**

- programs link to plan and national objective
- sub-programs link to program
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-005
- Epic: EPIC-STRAT-002
- Title: Implement Program and Sub Program DocTypes

Context:

- App: kentender_strategy
- Entity-level strategic hierarchy is:  
    Entity Strategic Plan -> Program -> Sub Program
- Program must map to a National Objective.

Task:  
Implement:

1.  Program
2.  Sub Program

Required fields:

For Program:

- business_id
- entity_strategic_plan
- procuring_entity
- program_code
- program_name
- description
- national_objective
- responsible_department
- priority_level
- status

For Sub Program:

- business_id
- entity_strategic_plan
- program
- sub_program_code
- sub_program_name
- description
- responsible_department
- status

Requirements:

1.  Create both DocTypes.
2.  Enforce:
    - program belongs to one entity strategic plan
    - program maps to one national objective
    - sub-program belongs to one program
    - entity/plan derivation stays consistent
3.  Add tests for valid hierarchy creation and mismatch blocking.

Constraints:

- Do not implement indicators/targets here.
- Do not loosen hierarchy rules.
- Keep editability compatible with parent-plan control later.

Acceptance criteria:

- hierarchy works
- validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-STRAT-006 — Implement strategic revision model**

**App:** kentender_strategy  
**Priority:** High  
**Depends on:** STORY-STRAT-004, STORY-STRAT-005, STORY-CORE-016

**Objective**  
Introduce explicit revision tracking for strategic plan changes.

**Scope**

- Strategic Revision Record
- supersession-friendly revision references

**Acceptance criteria**

- revision object exists
- old/new plan linkage works
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded revision-tracking feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-006
- Epic: EPIC-STRAT-002
- Title: Implement strategic revision model

Context:

- App: kentender_strategy
- Active strategic structures must not be silently overwritten.
- Revisions should preserve old/new plan linkage and audit traceability.

Task:  
Implement a Strategic Revision Record DocType and related linkage logic.

Suggested fields:

- revision_id or business_id
- entity_strategic_plan_old
- entity_strategic_plan_new
- revision_reason
- requested_by
- approved_by
- effective_date
- impact_summary

Requirements:

1.  Create the DocType.
2.  Ensure old/new plan linkage is clear and consistent.
3.  Add tests for revision record creation and linkage integrity.

Constraints:

- Do not implement a full revision workflow engine yet.
- Do not mutate active plans silently.

Acceptance criteria:

- revision record exists
- plan linkage works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-STRAT-003 — Indicators, Targets, and Strategic Validation Services**

**STORY-STRAT-007 — Implement Output Indicator DocType**

**App:** kentender_strategy  
**Priority:** Critical  
**Depends on:** STORY-STRAT-005

**Objective**  
Create measurable output indicator records under sub-programs.

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-007
- Epic: EPIC-STRAT-003
- Title: Implement Output Indicator DocType

Context:

- App: kentender_strategy
- Output indicators sit under sub-programs and are later referenced by budget and procurement.

Task:  
Implement the Output Indicator DocType.

Required fields:

- business_id
- indicator_code
- indicator_name
- entity_strategic_plan
- program
- sub_program
- unit_of_measure
- indicator_type
- baseline_value
- baseline_date
- measurement_notes
- responsible_department
- status

Requirements:

1.  Create the DocType.
2.  Enforce that the indicator belongs to one sub-program.
3.  Keep derived hierarchy consistency with plan/program.
4.  Add tests for valid creation and mismatch blocking.

Constraints:

- Do not implement targets here.
- Keep measurement fields simple but structured.

Acceptance criteria:

- DocType exists
- hierarchy validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-STRAT-008 — Implement Performance Target DocType**

**App:** kentender_strategy  
**Priority:** Critical  
**Depends on:** STORY-STRAT-007

**Objective**  
Create time-bound targets under indicators.

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-008
- Epic: EPIC-STRAT-003
- Title: Implement Performance Target DocType

Context:

- App: kentender_strategy
- Performance targets are time-bound operational targets tied to output indicators.

Task:  
Implement the Performance Target DocType.

Required fields:

- business_id
- target_title
- entity_strategic_plan
- program
- sub_program
- output_indicator
- target_period_type
- period_start_date
- period_end_date
- period_label
- target_value_numeric
- target_value_text
- target_value_percent
- target_measurement_type
- achievement_rule_notes
- responsible_department
- status

Requirements:

1.  Create the DocType.
2.  Derive and validate hierarchy from output_indicator.
3.  Validate target period dates.
4.  Add basic target value compatibility checks.
5.  Add tests for valid create and invalid date/hierarchy scenarios.

Constraints:

- Do not overengineer composite formula targets yet.
- Keep first-release target typing practical.

Acceptance criteria:

- DocType exists
- date and hierarchy validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-STRAT-009 — Implement strategic linkage validation services**

**App:** kentender_strategy  
**Priority:** Critical  
**Depends on:** STORY-STRAT-005, STORY-STRAT-007, STORY-STRAT-008

**Objective**  
Create reusable strategy validation APIs for downstream modules.

**Scope**

- validate program
- validate sub-program
- validate indicator
- validate target
- validate full linkage set

**Acceptance criteria**

- service layer exists
- validations usable by budget/procurement later
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded shared-service feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-009
- Epic: EPIC-STRAT-003
- Title: Implement strategic linkage validation services

Context:

- App: kentender_strategy
- Downstream modules must not reimplement strategy validation logic.
- Budget and procurement modules will call strategy services to validate hierarchy integrity.

Task:  
Implement reusable strategy validation services.

Required service methods:

- validate_program(program_id, entity)
- validate_sub_program(sub_program_id, entity)
- validate_indicator(indicator_id, entity)
- validate_target(target_id, entity, as_of_date=None)
- validate_strategic_linkage_set(program, sub_program, output_indicator, performance_target, entity)

Requirements:

1.  Create service modules under kentender_strategy/services/.
2.  Ensure hierarchy and entity consistency checks are enforced.
3.  Return structured results or raise consistent exceptions as appropriate.
4.  Add tests for valid and invalid linkage combinations.

Constraints:

- Do not add budget or procurement logic here.
- Keep service signatures reusable and stable.
- Do not duplicate hierarchy logic in multiple places.

Acceptance criteria:

- service layer exists
- hierarchy validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-STRAT-010 — Implement strategy query helpers and reports**

**App:** kentender_strategy  
**Priority:** Medium  
**Depends on:** STORY-STRAT-009

**Objective**  
Provide query helpers and baseline reports for active strategy structures.

**Cursor prompt**

Writing

You are implementing a bounded support feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-STRAT-010
- Epic: EPIC-STRAT-003
- Title: Implement strategy query helpers and reports

Context:

- App: kentender_strategy
- Downstream modules and admins need efficient lookup of active strategy structures.

Task:  
Implement:

1.  query helpers for active strategy lookup
2.  a minimal first-pass reporting layer for strategy records

Suggested report/use cases:

- active strategic plans by entity
- programs by national objective
- indicators and targets by entity

Requirements:

- keep implementation lightweight and useful
- add tests for query helper behavior where practical

Constraints:

- do not build full dashboard layer
- do not add procurement/budget joins yet

Acceptance criteria:

- query helpers exist
- baseline reports or report scaffolds exist
- tests/examples are provided where practical

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-BUD-001 — Budget Control Period and Budget Header Model**

**STORY-BUD-001 — Implement Budget Control Period DocType**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORY-CORE-004, STORY-CORE-006

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-001
- Epic: EPIC-BUD-001
- Title: Implement Budget Control Period DocType

Context:

- App: kentender_budget
- Budget Control Period defines the active budgeting/control window for an entity, usually aligned with a fiscal year.

Task:  
Implement Budget Control Period.

Required fields:

- business_id
- procuring_entity
- fiscal_year
- period_label
- start_date
- end_date
- status
- allow_multi_year_commitments
- budget_source_type
- remarks

Requirements:

1.  Create the DocType.
2.  Enforce one active/open period per entity per fiscal year.
3.  Validate date sanity.
4.  Add tests for valid create and duplicate-open-period blocking.

Constraints:

- Do not implement budget header/lines here.
- Keep this as a clean control-period object.

Acceptance criteria:

- DocType exists
- uniqueness and date rules work
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-002 — Implement Budget DocType**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORY-BUD-001, STORY-CORE-007

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-002
- Epic: EPIC-BUD-001
- Title: Implement Budget DocType

Context:

- App: kentender_budget
- Budget is a versioned control document for an entity and control period.

Task:  
Implement the Budget DocType.

Required fields:

- business_id
- budget_title
- procuring_entity
- budget_control_period
- version_no
- status
- source_reference
- source_budget_system
- approval_status
- workflow_state
- is_current_active_version
- supersedes_budget
- superseded_by_budget
- revision_reason
- total_allocated_amount
- currency

Requirements:

1.  Create the DocType.
2.  Support versioning/supersession fields.
3.  Validate entity and control-period consistency.
4.  Add tests for valid create and version linkage behavior.

Constraints:

- Do not implement budget lines here.
- Do not implement revision engine yet.
- Keep this as a controlled header object.

Acceptance criteria:

- DocType exists
- version/supersession model works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-003 — Implement budget version/supersession logic**

**App:** kentender_budget  
**Priority:** High  
**Depends on:** STORY-BUD-002

**Cursor prompt**

Writing

You are implementing a bounded version-control feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-003
- Epic: EPIC-BUD-001
- Title: Implement budget version/supersession logic

Context:

- App: kentender_budget
- Only one current active budget version should exist per entity/control period.

Task:  
Implement budget version/supersession validation and helper logic.

Requirements:

1.  Enforce sensible active-version behavior.
2.  Prevent inconsistent supersession chains.
3.  Add tests for:
    - valid supersession
    - invalid multiple-current-active version scenarios
    - inconsistent old/new links blocked

Constraints:

- Do not implement full revision DocType here.
- Keep logic focused on version integrity.

Acceptance criteria:

- version control works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-BUD-002 — Budget Line Model and Strategic/Budget Linkage**

**STORY-BUD-004 — Implement Budget Line DocType**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORY-BUD-002, STORY-STRAT-009

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-004
- Epic: EPIC-BUD-002
- Title: Implement Budget Line DocType

Context:

- App: kentender_budget
- Budget Line is the primary procurement control unit.
- It links budget control to strategic hierarchy and funding source.

Task:  
Implement the Budget Line DocType.

Required fields:

- business_id
- budget
- procuring_entity
- budget_control_period
- fiscal_year
- status
- department
- responsible_department
- funding_source
- entity_strategic_plan
- program
- sub_program
- output_indicator
- performance_target
- procurement_category
- budget_line_type
- cost_center
- project
- allocated_amount
- reserved_amount
- committed_amount
- released_amount
- consumed_actual_amount
- available_amount
- external_budget_code
- external_reference_name
- allow_partial_reservation
- hard_stop_enforced
- allow_cross_department_use
- is_multi_year_line

Requirements:

1.  Create the DocType.
2.  Keep derived total fields present but non-authoritative.
3.  Validate entity and strategy linkage structure.
4.  Add tests for valid creation and invalid linkage combinations.

Constraints:

- Do not implement ledger posting here.
- Do not manually compute final balances from UI logic.
- Keep budget line as control unit, not transaction log.

Acceptance criteria:

- DocType exists
- structural validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-005 — Implement budget line validation against strategy and entity scope**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORY-BUD-004, STORY-STRAT-009, STORY-CORE-008

**Cursor prompt**

Writing

You are implementing a bounded validation feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-005
- Epic: EPIC-BUD-002
- Title: Implement budget line validation against strategy and entity scope

Context:

- App: kentender_budget
- Budget lines must align with valid strategy structures and entity scope.

Task:  
Implement backend validation logic for Budget Line using shared strategy and scope services.

Requirements:

1.  Use strategy validation services rather than reimplementing hierarchy logic.
2.  Ensure budget line entity matches strategy entity.
3.  Block invalid cross-entity or broken hierarchy combinations.
4.  Add tests for valid and invalid combinations.

Constraints:

- Do not implement ledger logic here.
- Do not duplicate strategy service logic.
- Keep validation server-side.

Acceptance criteria:

- validation layer works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-006 — Implement budget line derived totals fields and recalculation hooks**

**App:** kentender_budget  
**Priority:** Medium  
**Depends on:** STORY-BUD-004

**Cursor prompt**

Writing

You are implementing a bounded support feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-006
- Epic: EPIC-BUD-002
- Title: Implement budget line derived totals fields and recalculation hooks

Context:

- App: kentender_budget
- Budget line totals such as reserved/committed/available are convenience fields.
- The ledger will remain authoritative.

Task:  
Implement safe derived-total recalculation support for Budget Line.

Requirements:

1.  Add backend recalculation helpers/hooks for denormalized totals.
2.  Keep these fields read-only from the business-user perspective.
3.  Make it clear in code that ledger is authoritative.
4.  Add tests for recalculation behavior using mocked/simple ledger data patterns where needed.

Constraints:

- Do not implement full ledger service here.
- Do not make denormalized totals the source of truth.

Acceptance criteria:

- recalculation helpers exist
- totals are protected from manual misuse
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-BUD-003 — Budget Ledger and Availability Engine**

**STORY-BUD-007 — Implement Budget Ledger Entry DocType**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORY-BUD-004, STORY-CORE-016

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-007
- Epic: EPIC-BUD-003
- Title: Implement Budget Ledger Entry DocType

Context:

- App: kentender_budget
- Budget Ledger Entry is append-only and authoritative for procurement control movements.

Task:  
Implement the Budget Ledger Entry DocType.

Required fields:

- budget_line
- budget
- procuring_entity
- fiscal_year
- entry_type
- entry_direction
- amount
- posting_datetime
- status
- source_doctype
- source_docname
- source_business_id
- source_action
- related_requisition
- related_procurement_plan_item
- related_tender
- related_award_decision
- related_contract
- remarks
- created_by_user
- approved_by_user
- reversal_of_entry
- event_hash

Requirements:

1.  Create the DocType.
2.  Keep it append-only by design for posted entries.
3.  Add validation for required source context and positive amount handling.
4.  Add tests for valid posted entry creation and no destructive mutation behavior.

Constraints:

- Do not implement service posting methods in this story.
- Do not allow generic casual editing of posted entries.

Acceptance criteria:

- DocType exists
- append-only intent is clear in code
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-008 — Implement ledger posting service**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORY-BUD-007, STORY-CORE-016

**Cursor prompt**

Writing

You are implementing a bounded shared-service feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-008
- Epic: EPIC-BUD-003
- Title: Implement ledger posting service

Context:

- App: kentender_budget
- Budget Line is the procurement control unit.
- Budget Ledger Entry is append-only and authoritative.
- All budget mutations must go through service methods.

Task:  
Implement ledger posting service methods:

- reserve_budget
- release_reservation
- commit_budget
- release_commitment

Requirements:

1.  Create service module(s) under kentender_budget/services/.
2.  Each method must:
    - validate budget line
    - create append-only posted ledger entries
    - never destructively edit prior posted entries
    - emit audit events
3.  Support source context:
    - amount
    - source_doctype
    - source_docname
    - metadata/context
4.  Add tests for:
    - successful reservation
    - reservation blocked when insufficient funds
    - release reservation
    - commitment creation
    - commitment release
    - no destructive mutation

Constraints:

- Do not implement requisition/planning logic here.
- Do not place posting logic in DocType controller methods.
- Keep service layer reusable and authoritative.

Acceptance criteria:

- service methods exist
- ledger posting works
- insufficient funds block as expected
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-009 — Implement availability calculation service**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORY-BUD-007, STORY-BUD-008

**Cursor prompt**

Writing

You are implementing a bounded calculation-service feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-009
- Epic: EPIC-BUD-003
- Title: Implement availability calculation service

Context:

- App: kentender_budget
- Availability must be derived from budget control movements, not hand-edited totals.
- First-release procurement control availability should focus on allocation/reservation/commitment semantics.

Task:  
Implement availability calculation service.

Required service methods:

- get_budget_availability(budget_line_id, as_of_datetime=None)
- any internal helpers needed for balance breakdown

Required outputs:

- allocated
- reserved
- committed
- released
- available

Requirements:

1.  Compute values from authoritative ledger semantics.
2.  Keep design compatible with append-only entries.
3.  Add tests for:
    - empty/initial state
    - reservation effect
    - release effect
    - commitment effect
    - mixed sequence result

Constraints:

- Do not use manually edited totals as source of truth.
- Keep actual expenditure sync out of first-pass availability unless explicitly modeled.

Acceptance criteria:

- availability service exists
- balance calculations are correct
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-010 — Implement idempotency and concurrency protection for budget actions**

**App:** kentender_budget  
**Priority:** High  
**Depends on:** STORY-BUD-008, STORY-BUD-009

**Cursor prompt**

Writing

You are implementing a bounded reliability feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-010
- Epic: EPIC-BUD-003
- Title: Implement idempotency and concurrency protection for budget actions

Context:

- App: kentender_budget
- Budget reservation/commitment actions are high-risk and must avoid double-posting under retries or concurrent operations.

Task:  
Implement practical idempotency and concurrency protection patterns for budget service actions.

Requirements:

1.  Add a reasonable idempotency strategy for repeated identical requests where practical.
2.  Add concurrency-safe validation/posting flow as far as possible within Frappe constraints.
3.  Add tests or simulated cases for duplicate reservation prevention.

Constraints:

- Do not overengineer distributed locking.
- Keep solution practical and explicit.
- Do not weaken correctness for convenience.

Acceptance criteria:

- duplicate-posting risk is materially reduced
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-BUD-004 — Budget Revision and Allocation Framework**

**STORY-BUD-011 — Implement Budget Allocation DocType**

**App:** kentender_budget  
**Priority:** High  
**Depends on:** STORY-BUD-004

**Cursor prompt**

Writing

You are implementing a bounded transaction-model feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-011
- Epic: EPIC-BUD-004
- Title: Implement Budget Allocation DocType

Context:

- App: kentender_budget
- Budget allocations are auditable transactions that affect control-state amounts.

Task:  
Implement Budget Allocation.

Required fields:

- business_id
- budget_line
- allocation_date
- allocation_amount
- allocation_type
- allocation_reference
- remarks
- status

Requirements:

1.  Create the DocType.
2.  Keep it suitable for auditable allocation events.
3.  Add basic validation for amount and linkage.
4.  Add tests.

Constraints:

- Do not apply allocation effects automatically via ad hoc client logic.
- Keep this as a transactional object, not a child-table shortcut.

Acceptance criteria:

- DocType exists
- validations work
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-012 — Implement Budget Revision and Budget Revision Line DocTypes**

**App:** kentender_budget  
**Priority:** High  
**Depends on:** STORY-BUD-011, STORY-BUD-004

**Cursor prompt**

Writing

You are implementing a bounded revision-model feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-012
- Epic: EPIC-BUD-004
- Title: Implement Budget Revision and Budget Revision Line DocTypes

Context:

- App: kentender_budget
- Budget revisions are formal controlled changes and must preserve before/after context.

Task:  
Implement:

1.  Budget Revision
2.  Budget Revision Line

Suggested fields:

- Budget Revision:
    - business_id
    - budget
    - revision_type
    - revision_reason
    - requested_by
    - approved_by
    - effective_date
    - status
- Budget Revision Line:
    - source_budget_line
    - target_budget_line
    - change_type
    - change_amount
    - remarks

Requirements:

1.  Create the DocTypes.
2.  Add validation for basic consistency.
3.  Add tests for valid create and invalid amount/linking patterns.

Constraints:

- Do not implement full apply logic here.
- Keep records auditable and explicit.

Acceptance criteria:

- revision DocTypes exist
- validations work
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-013 — Implement budget revision apply service**

**App:** kentender_budget  
**Priority:** High  
**Depends on:** STORY-BUD-012, STORY-BUD-008, STORY-BUD-009

**Cursor prompt**

Writing

You are implementing a bounded service-action feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-013
- Epic: EPIC-BUD-004
- Title: Implement budget revision apply service

Context:

- App: kentender_budget
- Budget revisions must be applied through controlled logic, not manual edits.

Task:  
Implement apply_budget_revision(revision_id).

Requirements:

1.  Validate the revision before application.
2.  Prevent revisions that reduce below active exposure where appropriate.
3.  Apply effects through controlled ledger/allocation-aware logic.
4.  Emit audit events.
5.  Add tests for:
    - successful apply
    - invalid apply blocked
    - exposure conflict blocked

Constraints:

- Do not bypass ledger semantics.
- Do not directly mutate control totals without service logic.

Acceptance criteria:

- apply service exists
- invalid revisions are blocked
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-BUD-005 — Budget Validation APIs for Downstream Modules**

**STORY-BUD-014 — Implement downstream validation APIs**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORY-BUD-009

**Cursor prompt**

Writing

You are implementing a bounded shared-service feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-014
- Epic: EPIC-BUD-005
- Title: Implement downstream validation APIs

Context:

- App: kentender_budget
- Downstream modules like requisition, planning, and contract variation must consume budget services rather than reimplement budget logic.

Task:  
Implement downstream-facing validation APIs:

- validate_budget_line(budget_line_id, entity, as_of_date=None)
- get_budget_availability(budget_line_id, as_of_datetime=None)
- validate_funds_or_raise(budget_line_id, amount, stage, entity)

Requirements:

1.  Expose clean service methods.
2.  Use existing budget line and availability logic.
3.  Raise or return structured errors consistently.
4.  Add tests for valid and invalid use cases.

Constraints:

- Do not implement requisition/planning modules here.
- Keep interfaces stable and reusable.

Acceptance criteria:

- service methods exist
- validation behavior is correct
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-015 — Implement budget audit event integration**

**App:** kentender_budget  
**Priority:** High  
**Depends on:** STORY-BUD-008, STORY-BUD-013, STORY-CORE-016

**Cursor prompt**

Writing

You are implementing a bounded audit-integration feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-015
- Epic: EPIC-BUD-005
- Title: Implement budget audit event integration

Context:

- App: kentender_budget
- Budget actions are high-risk and must emit audit events consistently.

Task:  
Integrate budget actions with the shared audit service.

Requirements:

1.  Ensure major budget service actions emit audit events:
    - reservation
    - reservation release
    - commitment
    - commitment release
    - revision application
2.  Add tests or assertions validating audit calls where practical.

Constraints:

- Do not redesign the audit service.
- Keep this integration-layer focused.

Acceptance criteria:

- budget actions emit audit events
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-BUD-016 — Implement budget unit/integration tests**

**App:** kentender_budget  
**Priority:** Critical  
**Depends on:** STORIES BUD-001 through BUD-015

**Cursor prompt**

Writing

You are implementing a bounded test-hardening task in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-BUD-016
- Epic: EPIC-BUD-005
- Title: Implement budget unit/integration tests

Context:

- App: kentender_budget
- Budget control is one of the highest-risk parts of the platform.
- It must be hardened with focused test coverage before requisition development begins.

Task:  
Add a strong first-pass test suite for the budget module.

Coverage should include:

- budget control period rules
- budget header version integrity
- budget line linkage validation
- ledger posting semantics
- availability calculation
- revision apply behavior
- downstream validation API behavior

Requirements:

1.  Organize tests clearly.
2.  Cover both happy path and blocking scenarios.
3.  Keep the test suite maintainable and readable.

Constraints:

- Do not broaden into requisition tests yet.
- Focus on budget module correctness.

Acceptance criteria:

- meaningful budget test suite exists
- critical paths are covered
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**Recommended Wave 1 execution order**

Run these in this order:

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
6.  STORY-BUD-006
7.  STORY-BUD-007
8.  STORY-BUD-008
9.  STORY-BUD-009
10. STORY-BUD-010
11. STORY-BUD-011
12. STORY-BUD-012
13. STORY-BUD-013
14. STORY-BUD-014
15. STORY-BUD-015
16. STORY-BUD-016