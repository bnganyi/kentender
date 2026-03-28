## Wave 0 Ticket Pack

**EPIC-CORE-001 — Repository and Multi-App Foundation**

**STORY-CORE-001 — Initialize multi-app KenTender workspace**

**App:** workspace / all apps  
**Priority:** Critical  
**Depends on:** none

**Objective**  
Create the modular Frappe app skeletons and repository structure for KenTender.

**Scope**

- initialize apps:
    - kentender_core
    - kentender_strategy
    - kentender_budget
    - kentender_procurement
    - kentender_governance
    - kentender_compliance
    - kentender_stores
    - kentender_assets
    - kentender_integrations
- standardize package layout
- add shared top-level docs folders:
    - docs/architecture
    - docs/delivery
    - docs/prompts
- ensure apps are installable

**Out of scope**

- no DocTypes yet
- no business logic
- no workflows

**Acceptance criteria**

- all apps exist and load
- package layout is consistent
- repository contains delivery/prompt docs folders
- no circular dependency setup introduced

**Tests**

- app import/install smoke checks
- basic module import checks

**Cursor prompt**

Writing

You are implementing a bounded platform foundation task in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-001
- Epic: EPIC-CORE-001
- Title: Initialize multi-app KenTender workspace

Context:

- KenTender is a modular public procurement platform.
- The solution uses multiple Frappe apps, not a monolith.
- The required app set is:
    - kentender_core
    - kentender_strategy
    - kentender_budget
    - kentender_procurement
    - kentender_governance
    - kentender_compliance
    - kentender_stores
    - kentender_assets
    - kentender_integrations

Task:  
Set up the repository/app structure for these apps and standardize the internal layout.

Requirements:

1.  Create or scaffold the listed apps if they do not already exist.
2.  Standardize app internal structure for future work, including sensible folders for:
    - doctype
    - services
    - api
    - tests
3.  Add top-level docs folders:
    - docs/architecture
    - docs/delivery
    - docs/prompts
4.  Ensure the apps are importable and ready for later installation/configuration.
5.  Add a short README or developer note summarizing the intended role of each app.

Constraints:

- Do not implement business DocTypes yet.
- Do not add speculative features.
- Keep the structure clean and minimal.
- Do not invent cross-app dependencies yet beyond comments or placeholders.

Acceptance criteria:

- all required apps exist
- layout is standardized
- docs folders exist
- import/install smoke readiness is in place

At the end, provide:

1.  files/folders created or modified
2.  assumptions made
3.  open questions
4.  any commands needed to verify setup

**STORY-CORE-002 — Set app dependency boundaries and shared config conventions**

**App:** all apps  
**Priority:** Critical  
**Depends on:** STORY-CORE-001

**Objective**  
Define dependency order and common conventions so later implementation does not drift.

**Scope**

- document allowed dependency direction
- add app-level notes/config placeholders
- define naming and service conventions
- establish no-circular-import policy

**Out of scope**

- no business services
- no DocTypes

**Acceptance criteria**

- dependency rules documented in repo
- app-level conventions visible to developers
- dependency direction matches architecture

**Tests**

- no runtime tests required beyond import sanity

**Cursor prompt**

Writing

You are implementing a bounded platform architecture task in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-002
- Epic: EPIC-CORE-001
- Title: Set app dependency boundaries and shared config conventions

Context:

- KenTender uses modular multi-app architecture.
- Dependency direction must be controlled.
- Core architectural direction:
    - kentender_core is the base dependency
    - kentender_strategy depends on kentender_core
    - kentender_budget depends on kentender_core and may reference strategy
    - kentender_procurement depends on core/strategy/budget
    - governance/compliance/integrations depend on core and interface with others cleanly
    - stores/assets are downstream extensions

Task:  
Create developer-facing dependency and configuration conventions in the codebase.

Requirements:

1.  Add a repository-level developer architecture note documenting allowed app dependency direction.
2.  Add lightweight per-app README or notes describing intended responsibility and forbidden coupling.
3.  Define shared naming conventions for:
    - DocTypes
    - service modules
    - tests
    - business IDs
4.  Document a no-circular-import rule and service-layer interaction rule.
5.  Keep this implementation lightweight and non-invasive.

Constraints:

- Do not implement actual business logic.
- Do not add fake runtime dependency enforcement unless simple and safe.
- Do not change app roles or boundaries from the approved architecture.

Acceptance criteria:

- dependency rules are documented in-repo
- app responsibilities are clear
- naming/service conventions are documented

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  how developers should use the conventions

**STORY-CORE-003 — Create common service module structure across apps**

**App:** all apps  
**Priority:** Critical  
**Depends on:** STORY-CORE-001, STORY-CORE-002

**Objective**  
Create a predictable code organization pattern for Cursor and human developers.

**Scope**

- standard service package layout
- API package layout
- tests layout
- placeholders for hooks/utilities where appropriate

**Acceptance criteria**

- each app has consistent internal structure
- service modules are discoverable and ready for use

**Cursor prompt**

Writing

You are implementing a bounded engineering-structure task in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-003
- Epic: EPIC-CORE-001
- Title: Create common service module structure across apps

Task:  
Standardize internal code structure across all KenTender apps for future implementation.

Requirements:

1.  For each app, ensure sensible package structure exists for:
    - doctype
    - services
    - api
    - tests
    - optional utils where needed
2.  Add minimal package init files as necessary.
3.  Add a short developer note describing where business logic belongs:
    - DocType definitions/controllers for thin model behavior
    - service modules for business actions
    - tests for unit/integration coverage
4.  Keep the setup lightweight and ready for future stories.

Constraints:

- Do not add speculative business modules.
- Do not duplicate patterns differently per app.
- Keep business logic out of this story.

Acceptance criteria:

- app internals are structured consistently
- service-layer organization is obvious
- developers can implement future stories in a predictable place

At the end, provide:

1.  files/folders created or modified
2.  assumptions made
3.  open questions
4.  final recommended folder pattern

**EPIC-CORE-002 — Shared Master Data and Entity Model**

**STORY-CORE-004 — Implement Procuring Entity DocType**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-001

**Objective**  
Implement the top-level operational scope object.

**Scope**

- Procuring Entity DocType
- validation:
    - unique entity_code
    - no self-parent
    - no circular parent chain

**Acceptance criteria**

- entity records can be created
- hierarchy validation works
- code uniqueness enforced

**Tests**

- valid create
- duplicate code blocked
- self-parent blocked
- circular reference blocked

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-004
- Epic: EPIC-CORE-002
- Title: Implement Procuring Entity DocType

Context:

- App: kentender_core
- Procuring Entity is the top operational scope for most transactional records.
- This object will be referenced by strategy, budget, procurement, governance, stores, and assets modules.

Task:  
Implement the Procuring Entity DocType and supporting validation logic.

Required fields:

- entity_code
- entity_name
- entity_type
- parent_entity
- active
- company_link (optional)
- default_currency
- country
- central_reporting_scope
- allow_entity_level_workflows
- allow_entity_level_master_data_extensions

Requirements:

1.  Create the DocType.
2.  Enforce unique entity_code.
3.  Prevent self-parenting.
4.  Prevent circular parent hierarchy.
5.  Add tests for valid create, duplicate code, self-parent, and circular hierarchy.
6.  Keep business logic server-side.

Constraints:

- Do not implement departments here.
- Do not add unrelated fields unless needed for Frappe integrity.
- Keep UI customization minimal.

Acceptance criteria:

- DocType exists and is usable
- validations work
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-005 — Implement Department / Business Unit DocType**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-004

**Objective**  
Implement department/unit scoping under a procuring entity.

**Scope**

- Department / Business Unit DocType
- link to Procuring Entity
- optional hierarchy
- HOD linkage
- validation

**Acceptance criteria**

- department belongs to entity
- unique code per entity
- optional parent hierarchy works

**Cursor prompt**

Writing

You are implementing a bounded feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-005
- Epic: EPIC-CORE-002
- Title: Implement Department / Business Unit DocType

Context:

- App: kentender_core
- Departments/business units are entity-scoped and used heavily in requisitions, budgets, workflows, and reporting.

Task:  
Implement the Department / Business Unit DocType.

Required fields:

- department_code
- department_name
- procuring_entity
- parent_department
- hod_user
- active
- budget_scope_type

Requirements:

1.  Create the DocType.
2.  Enforce that every department belongs to a procuring entity.
3.  Enforce uniqueness of department_code within an entity.
4.  Prevent invalid self-parent or circular department hierarchy.
5.  Add tests for valid create and hierarchy validation.

Constraints:

- Do not build role assignment logic beyond linking HOD user.
- Do not add requisition or budget logic here.
- Keep scope entity-centric.

Acceptance criteria:

- entity-scoped departments exist
- code uniqueness per entity works
- hierarchy validation works
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-006 — Implement shared master data DocTypes**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-004

**Objective**  
Implement core master/reference data used everywhere.

**Scope**

- Funding Source
- Procurement Category
- Procurement Method
- Reference Number Policy
- Document Type Registry

**Acceptance criteria**

- DocTypes exist
- core validation in place
- suitable indexing/uniqueness rules
- basic tests

**Cursor prompt**

Writing

You are implementing a bounded master-data feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-006
- Epic: EPIC-CORE-002
- Title: Implement shared master data DocTypes

Context:

- App: kentender_core
- These DocTypes will be reused across most modules.

Task:  
Implement these DocTypes:

1.  Funding Source
2.  Procurement Category
3.  Procurement Method
4.  Reference Number Policy
5.  Document Type Registry

Use the approved architecture and keep the definitions backend-clean.

Minimum fields to support:

- Funding Source:
    - funding_source_code
    - funding_source_name
    - funding_source_type
    - external_reference
    - active
    - entity_scope_type
- Procurement Category:
    - category_code
    - category_name
    - parent_category
    - category_type
    - active
- Procurement Method:
    - method_code
    - method_name
    - category_applicability
    - requires_publication
    - requires_invitation_only
    - allows_lotting
    - allows_framework
    - active
- Reference Number Policy:
    - policy_code
    - target_doctype
    - entity_scoped
    - fiscal_year_scoped
    - pattern
    - active
- Document Type Registry:
    - document_type_code
    - document_type_name
    - module_scope
    - sensitivity_class
    - required_for_processes
    - active

Requirements:

1.  Create the DocTypes.
2.  Add sensible uniqueness validation on key codes.
3.  Support hierarchy where applicable (parent_category).
4.  Add basic tests for valid creation and duplicate-code blocking.

Constraints:

- Do not implement business logic of downstream modules.
- Do not overengineer rule evaluation here.
- Keep these as reusable master/reference records.

Acceptance criteria:

- all five DocTypes exist and validate correctly
- duplicate key codes are blocked
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-007 — Implement naming/number generation service**

**App:** kentender_core  
**Priority:** High  
**Depends on:** STORY-CORE-006

**Objective**  
Create reusable business ID generation based on policy.

**Scope**

- numbering service
- consume Reference Number Policy
- support entity/fiscal-year scoped sequences

**Acceptance criteria**

- service generates IDs for sample doctypes
- respects policy pattern
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded shared-service feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-007
- Epic: EPIC-CORE-002
- Title: Implement naming/number generation service

Context:

- App: kentender_core
- KenTender uses human-readable business_id values driven by Reference Number Policy.
- Business IDs may be entity-scoped and/or fiscal-year-scoped.

Task:  
Implement a reusable numbering service that can generate business_id values for major business records.

Requirements:

1.  Create a service module for business ID generation.
2.  Use Reference Number Policy as the source of pattern rules.
3.  Support at minimum:
    - entity-scoped numbering
    - fiscal-year-scoped numbering
    - sequence padding where applicable
4.  Make the service easy for downstream modules to call later.
5.  Add tests demonstrating generation for at least two sample policy scenarios.

Constraints:

- Do not wire this into every DocType yet.
- Do not hardcode all future document patterns.
- Keep the service clean and reusable.

Acceptance criteria:

- numbering service exists
- policy-driven IDs can be generated
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-CORE-005 — Audit Event and Exception Framework**

**STORY-CORE-015 — Implement Exception Record DocType**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-001

**Objective**  
Create formal override/exception object used across modules.

**Acceptance criteria**

- exception record exists
- lifecycle/status fields present
- can link to arbitrary business records

**Cursor prompt**

Writing

You are implementing a bounded governance-control feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-015
- Epic: EPIC-CORE-005
- Title: Implement Exception Record DocType

Context:

- App: kentender_core
- Exception records are used for lawful override paths such as emergency procurement, controlled access override, or rule bypass with approval.
- Exceptions are first-class governance records.

Task:  
Implement the Exception Record DocType.

Required fields:

- exception_id or business_id
- exception_type
- related_doctype
- related_docname
- procuring_entity
- triggered_by
- justification
- approval_status
- approved_by
- effective_period
- severity

Requirements:

1.  Create the DocType with a sensible status model.
2.  Ensure it can link to arbitrary business objects by doctype/docname.
3.  Add basic validation for required justification and valid scope.
4.  Add tests for creation and basic linkage integrity.

Constraints:

- Do not implement all exception workflows yet.
- Keep this as a reusable governance object.
- Do not hardwire it to only one module.

Acceptance criteria:

- Exception Record exists and is reusable
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-016 — Implement audit event service and event schema**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-001

**Objective**  
Create event-based audit service for later modules.

**Scope**

- audit event schema/model
- reusable logging service
- append-only behavior

**Acceptance criteria**

- service can log events with standard payload
- event records immutable enough for first pass
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded platform-audit feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-016
- Epic: EPIC-CORE-005
- Title: Implement audit event service and event schema

Context:

- App: kentender_core
- KenTender uses event-based audit, not just field-version history.
- Audit events must support high-risk business actions later.

Task:  
Implement a reusable audit event model and service.

Requirements:

1.  Create an audit event DocType or equivalent structured model for event logging.
2.  Support at minimum these fields:
    - event_type
    - module
    - doctype
    - docname
    - business_id
    - actor
    - actor_role
    - procuring_entity
    - old_state
    - new_state
    - changed_fields_summary
    - reason/comment
    - event_hash
    - event_datetime
3.  Implement a reusable service method to log events.
4.  Keep audit records append-only in design.
5.  Add tests showing event creation and expected payload behavior.

Constraints:

- Do not build every audit integration yet.
- Do not depend on client-side calls.
- Keep service usable by all apps later.

Acceptance criteria:

- audit service exists
- structured events can be logged
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-017 — Implement access-denied and sensitive-access audit hooks**

**App:** kentender_core  
**Priority:** High  
**Depends on:** STORY-CORE-016

**Objective**  
Prepare logging for denied or sensitive access attempts.

**Acceptance criteria**

- helper/service exists
- can log denied access and sensitive access events
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded security-audit feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-017
- Epic: EPIC-CORE-005
- Title: Implement access-denied and sensitive-access audit hooks

Context:

- App: kentender_core
- Sealed bids, restricted evaluation data, and sensitive complaint/contract records require access-event logging.
- Denied access can itself be an audit-critical event.

Task:  
Implement reusable helpers for logging:

1.  denied access attempts
2.  allowed sensitive access events

Requirements:

1.  Build on the shared audit event service.
2.  Provide helper methods usable later by protected file access and permission services.
3.  Add tests demonstrating:
    - denied access logging
    - sensitive access logging

Constraints:

- Do not implement all permission checks in this story.
- Keep the implementation as a reusable audit helper layer.

Acceptance criteria:

- helpers exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-CORE-006 — Typed Document and File Control Framework**

**STORY-CORE-018 — Implement shared typed attachment model**

**App:** kentender_core  
**Priority:** High  
**Depends on:** STORY-CORE-006

**Objective**  
Create typed document attachment record for critical files.

**Acceptance criteria**

- attachment model exists
- links to owning doctype/docname
- stores sensitivity and document type metadata
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded document-control feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-018
- Epic: EPIC-CORE-006
- Title: Implement shared typed attachment model

Context:

- App: kentender_core
- KenTender does not rely on raw generic file attachment alone for critical procurement documents.
- Critical files need typed metadata and access semantics.

Task:  
Implement a shared typed attachment model.

Requirements:

1.  Create a reusable DocType for typed attachments linked to arbitrary business records.
2.  Support fields such as:
    - document_type
    - file
    - sensitivity_class
    - owning_doctype
    - owning_docname
    - uploaded_by
    - uploaded_at
    - file_hash
    - public_disclosure_eligibility
    - sealed_until_event (optional)
3.  Add validation for required owning record linkage.
4.  Add tests for valid attachment creation.

Constraints:

- Do not implement every document-specific workflow yet.
- Do not expose sensitive files directly.
- Keep this reusable across modules.

Acceptance criteria:

- typed attachment model exists
- metadata is captured
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-019 — Implement sensitivity classification handling**

**App:** kentender_core  
**Priority:** High  
**Depends on:** STORY-CORE-018

**Objective**  
Provide reusable sensitivity behavior primitives.

**Acceptance criteria**

- helper utilities exist for Public/Internal/Confidential/Sealed Procurement
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded document-security feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-019
- Epic: EPIC-CORE-006
- Title: Implement sensitivity classification handling

Context:

- App: kentender_core
- Sensitivity classes include:
    - Public
    - Internal
    - Confidential
    - Sealed Procurement
- Many later modules depend on this behavior.

Task:  
Implement reusable sensitivity classification helpers/utilities.

Requirements:

1.  Create shared constants/enums/utilities for sensitivity classes.
2.  Provide helper methods for checking whether content is:
    - publicly disclosable
    - sensitive
    - sealed
3.  Integrate this cleanly with the typed attachment model where useful.
4.  Add tests for classification behavior.

Constraints:

- Do not implement full permission enforcement here.
- Do not hardcode module-specific rules.
- Keep this as reusable infrastructure.

Acceptance criteria:

- sensitivity utilities exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-020 — Implement protected file access service for sensitive documents**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-018, STORY-CORE-019, STORY-CORE-017

**Objective**  
Create service pattern for protected retrieval of sensitive files.

**Acceptance criteria**

- protected access service exists
- supports deny/allow logging hooks
- no generic raw retrieval pattern baked in
- tests pass

**Cursor prompt**

Writing

You are implementing a bounded sensitive-file access feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-020
- Epic: EPIC-CORE-006
- Title: Implement protected file access service for sensitive documents

Context:

- App: kentender_core
- Sealed procurement and confidential files must not rely on raw generic file access.
- Access must be permission-checked and auditable.

Task:  
Implement a protected file access service pattern for typed attachments.

Requirements:

1.  Create a service function or module that resolves access to a typed attachment only after permission/sensitivity checks.
2.  Integrate with sensitive-access and denied-access audit helpers.
3.  Structure the service so later modules can plug in their own permission logic.
4.  Add tests for:
    - allowed access path
    - denied access path
    - audit hook execution

Constraints:

- Do not implement final bid-specific permission rules in this story.
- Do not expose direct unaudited file reads.
- Keep the service generic and reusable.

Acceptance criteria:

- protected access service exists
- allow/deny hooks work
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-CORE-003 — Shared Security, Scope, and Permission Framework**

**STORY-CORE-008 — Implement entity scope utility layer**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-004, STORY-CORE-005

**Objective**  
Provide reusable entity scoping helpers.

**Cursor prompt**

Writing

You are implementing a bounded access-scope feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-008
- Epic: EPIC-CORE-003
- Title: Implement entity scope utility layer

Context:

- App: kentender_core
- Most transactional records are scoped by procuring_entity.
- Cross-entity visibility must be controlled centrally.

Task:  
Implement reusable entity scope helper utilities.

Requirements:

1.  Create utility/service functions for common entity-scope checks.
2.  Support patterns such as:
    - record belongs to entity
    - user has access to entity
    - cross-entity access check for central roles
3.  Add tests for common positive/negative scope scenarios.

Constraints:

- Do not implement every final user-role assignment model here.
- Keep logic reusable and backend-oriented.

Acceptance criteria:

- entity scope helpers exist
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-009 — Implement assignment-based access helper framework**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-003

**Objective**  
Provide infrastructure for committee/case assignments.

**Cursor prompt**

Writing

You are implementing a bounded assignment-access feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-009
- Epic: EPIC-CORE-003
- Title: Implement assignment-based access helper framework

Context:

- App: kentender_core
- High-sensitivity access for opening, evaluation, and complaint review is assignment-based, not role-only.

Task:  
Implement a reusable assignment-based access helper framework.

Requirements:

1.  Create a generic assignment model or helper pattern suitable for:
    - committee assignment
    - case/session assignment
2.  Support checks like:
    - user assigned to target object
    - assignment active/inactive
    - role within assignment
3.  Add tests for assignment-based allow/deny behavior.

Constraints:

- Do not implement full evaluation/opening modules here.
- Keep the framework generic enough for later reuse.

Acceptance criteria:

- assignment helper framework exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-010 — Implement permission query helper framework**

**App:** kentender_core  
**Priority:** High  
**Depends on:** STORY-CORE-008, STORY-CORE-009

**Objective**  
Provide reusable query filter helpers for scope-aware access.

**Cursor prompt**

Writing

You are implementing a bounded permission-helper feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-010
- Epic: EPIC-CORE-003
- Title: Implement permission query helper framework

Context:

- App: kentender_core
- Later modules will need reusable query filtering for:
    - entity scope
    - self-owned records
    - assignment-based visibility

Task:  
Implement reusable permission query helper utilities.

Requirements:

1.  Create helper functions/patterns for common permission query filtering.
2.  Cover at minimum:
    - entity-scoped filtering
    - self-owned filtering
    - assignment-based filtering hooks/placeholders
3.  Add tests or usage examples where appropriate.

Constraints:

- Do not wire every future DocType yet.
- Keep framework generic.
- Avoid hardcoding business-module-specific conditions.

Acceptance criteria:

- query helper framework exists
- tests/examples validate usage

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**STORY-CORE-011 — Implement separation-of-duty conflict rule DocType and service**

**App:** kentender_core  
**Priority:** Critical  
**Depends on:** STORY-CORE-006, STORY-CORE-003

**Objective**  
Create central conflict-of-duty rule storage and evaluation.

**Cursor prompt**

Writing

You are implementing a bounded governance-control feature in a Frappe-based modular system called KenTender.

Story:

- ID: STORY-CORE-011
- Epic: EPIC-CORE-003
- Title: Implement separation-of-duty conflict rule DocType and service

Context:

- App: kentender_core
- KenTender centrally enforces conflicts such as:
    - requisitioner cannot approve own requisition
    - evaluator cannot approve award on same tender
    - procurement officer cannot evaluate same tender
- These rules must be reusable across modules.

Task:  
Implement:

1.  Separation of Duty Conflict Rule DocType
2.  a reusable evaluation service for checking conflicts

Required fields for rule model:

- rule_code
- source_doctype
- source_action
- source_role
- target_doctype
- target_action
- target_role
- scope_type
- severity
- exception_policy
- active

Requirements:

1.  Create the DocType.
2.  Create a service that can evaluate whether a proposed action conflicts with existing participation.
3.  Add tests for a few representative conflict checks.

Constraints:

- Do not tightly couple this to only one module.
- Keep it generic and reusable.
- Do not implement every future action integration yet.

Acceptance criteria:

- rule model exists
- evaluation service exists
- tests pass

At the end, provide:

1.  files created/modified
2.  assumptions made
3.  open questions
4.  tests added

**EPIC-CORE-004 — Workflow Guard and Business Action Framework**

**STORY-CORE-012 — Implement Workflow Guard Rule DocType**

**STORY-CORE-013 — Implement shared workflow guard service**

**STORY-CORE-014 — Implement controlled business action pattern**

To keep this usable, I’m bundling their prompts in a shorter form here. If you want, I can expand each exactly like the others.

**STORY-CORE-012 prompt**

Writing

Implement Workflow Guard Rule in kentender_core.

Fields:

- rule_code
- rule_name
- applies_to_doctype
- event_name
- rule_type
- severity
- active
- exception_policy
- evaluation_order

Requirements:

- create DocType
- add uniqueness/ordering validation
- keep generic for many modules
- add tests

Constraints:

- no module-specific business rules hardcoded
- keep as metadata for guard engine

**STORY-CORE-013 prompt**

Writing

Implement shared workflow guard service in kentender_core.

Requirements:

- support pre-create, pre-submit, pre-approve, pre-transition guard execution pattern
- accept target doctype/docname/context/action
- return structured pass/fail/blocking issues
- integrate cleanly with Workflow Guard Rule metadata where sensible
- add tests

Constraints:

- do not hardwire future procurement rules here
- keep engine generic and reusable

**STORY-CORE-014 prompt**

Writing

Implement controlled business action pattern in kentender_core.

Requirements:

- define a reusable service/action convention for critical actions like:
    - submit
    - approve
    - publish
    - open
    - finalize
    - close
- pattern must enforce:
    - permission checks
    - workflow guards
    - audit event creation
- add base utilities/tests

Constraints:

- do not implement tender/requisition-specific actions yet
- create framework only

**EPIC-CORE-007 — Notification Framework**

**STORY-CORE-021 — Implement Notification Template DocType**

**STORY-CORE-022 — Implement notification dispatch service abstraction**

**STORY-CORE-021 prompt**

Writing

Implement Notification Template in kentender_core.

Fields:

- template_code
- template_name
- channel
- event_name
- subject_template
- body_template
- active
- scope_type

Requirements:

- create DocType
- support reusable templating foundation
- add tests for create/duplicate-code behavior

**STORY-CORE-022 prompt**

Writing

Implement notification dispatch abstraction in kentender_core.

Requirements:

- create reusable notification service interface for:
    - in-system
    - email
    - SMS
- support template rendering input
- return delivery result structure
- keep integrations pluggable
- add tests or mock-based checks

Constraints:

- do not wire real gateways yet

**Recommended execution plan for you in Cursor**

Run these in order:

1.  STORY-CORE-001
2.  STORY-CORE-002
3.  STORY-CORE-003
4.  STORY-CORE-004
5.  STORY-CORE-005
6.  STORY-CORE-006
7.  STORY-CORE-007
8.  STORY-CORE-015
9.  STORY-CORE-016
10. STORY-CORE-017
11. STORY-CORE-018
12. STORY-CORE-019
13. STORY-CORE-020
14. STORY-CORE-008
15. STORY-CORE-009
16. STORY-CORE-010
17. STORY-CORE-011
18. STORY-CORE-012
19. STORY-CORE-013
20. STORY-CORE-014
21. STORY-CORE-021
22. STORY-CORE-022

That will give you a proper foundation before strategy and budget.

**Best review pattern after each Cursor run**

For every story, review these 6 things:

1.  Did Cursor stay inside scope?
2.  Did it put business logic in services, not only DocType controllers?
3.  Did it add tests?
4.  Did it accidentally introduce tighter coupling than intended?
5.  Did it invent fields or shortcuts not in the design?
6.  Did it leave open questions you need to resolve before the next story?