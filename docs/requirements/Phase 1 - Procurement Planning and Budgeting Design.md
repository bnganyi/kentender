**Phase 1: Procurement Planning and Budgeting**.

I’m treating the donor/IFAD-style ideas as reference material only where they improve discipline, auditability, and controls, but I am **not** making donor workflows part of the core module. The core design is anchored on Kenyan public-sector procurement, compliance-first governance, strategic traceability, APP control, budget discipline, segregation of duties, and auditable progression into requisitions and later tendering.

**Phase 1 objective**

This module must produce a defensible **Annual Procurement Plan (APP)** that links every planned procurement to:

- the procuring entity and financial year,
- the approved budget,
- the responsible department,
- the national/corporate strategic objective it serves,
- the approved procurement method path,
- and the downstream execution chain from plan to requisition to tender to contract to payment.

The system should not behave like a lightweight planning spreadsheet. It should behave like a **public financial control and procurement governance module** with strong traceability, approval discipline, lock rules, and audit evidence. The uploaded requirements are explicit about strategic alignment, immutable logging, budget lifecycle tracking, SoD, hard/soft budget controls, and end-to-end traceability.

**1) What changes from the prototype**

The prototype direction appears to have the right bones: Procurement Plan, Procurement Plan Item, strategic references, budgeting link, and requisition dependency.

What needs to be strengthened for a real public-sector rollout is this:

1.  **APP as a controlled public-sector record**, not just a transaction form.  
    It needs version control, formal approval, locking, supplement handling, and controlled re-baselining.
2.  **Budget control must become lifecycle-based**.  
    Not just “has a budget line,” but planned, committed/encumbered, invoiced, paid, and released balances.
3.  **Strategic alignment must be mandatory and auditable**.  
    The architecture already points to National Development Plan → Corporate Strategic Plan → Strategic Objective → Procurement Plan Item. That should be enforced, not optional.
4.  **Method and threshold governance must be rules-driven**.  
    Planning should advise or restrict procurement methods based on value bands, category, special conditions, and approvals, with anti-split controls. The requirements explicitly call for configurable policies, thresholds, review levels, and bundling suggestions.
5.  **Segregation of duties must be explicit in workflow design**.  
    Planning, approval, procurement execution, and payment must not collapse into one user path.
6.  **Auditability must be first-class**.  
    Changes to amount, dates, methods, approvals, and overrides need preserved old/new values with user and timestamp.

That is the design target below.

**2) Public-sector design principles for this module**

These should govern the build:

**2.1 Compliance-first**

The module exists to reduce discretion, enforce governance guardrails, and make the APP reviewable by Accounting Officers, internal audit, PPRA-type oversight, and the Auditor General. That is directly aligned with the KenTender requirements.

**2.2 Strategy-to-spend traceability**

No APP line should exist without showing what public objective it serves. The architecture already defines this linkage.

**2.3 Budget realism before procurement initiation**

A plan line may be drafted before final approval, but no line should be approved into an executable APP without a valid budget reference and budget availability status. The requirements repeatedly call for budget checks, commitments, and hard/soft stop behavior.

**2.4 APP is the gate to requisitions**

Requisitions must reference an approved Procurement Plan Item. The architecture already states this and validates that a requisitioned item must exist in the APP.

**2.5 No silent overrides**

Any override of cost, quarter, budget allocation, method recommendation, or approval path must capture a reason and become audit-visible.

**2.6 Lock after approval**

Once the APP is approved and published/locked, edits should not be direct. Changes must go through supplementary plan or formal revision flow. The architecture already expects lock behavior for controlled records, and the planning requirements call for snapshots and re-baselining.

**3) Target module boundaries**

For **Phase 1 / Procurement Planning and Budgeting**, the module should include:

- strategic planning references needed for traceability,
- APP creation and approval,
- APP line planning and validation,
- budget linkage and commitment reservation logic,
- planning policy rules and threshold checks,
- procurement scheduling at quarter/month level,
- plan publication and locking,
- controlled revision/supplementary planning,
- reports and dashboards,
- handoff to requisitions.

It should **not** yet include supplier, tendering, bid evaluation, or award workflows beyond reference linkage for future traceability. Those belong to later modules.

**4) Recommended module structure**

I would organize Phase 1 into **8 submodules** inside Procurement Planning and Budgeting.

**Module 1 — Strategic Planning & Policy Foundation**

Purpose: provide the public-policy alignment backbone and rule references for APP construction.

**Core DocTypes**

- **National Development Plan**
- **National Development Priority**
- **Corporate Strategic Plan**
- **Strategic Objective**
- **Procurement Policy Profile**
- **Procurement Threshold Rule**
- **Procurement Method Rule**
- **Budget Control Rule**
- **Approval Matrix Rule**

**Why this matters**

The architecture already defines the strategic hierarchy. What is missing is the policy layer as configurable master data rather than hidden custom scripts. The requirements explicitly say thresholds, methods, review levels, and budget checks should be configurable and versioned.

**Key fields**

For **Procurement Policy Profile**:

- entity
- financial_year
- effective_from / effective_to
- procurement regime
- approval basis
- hard_stop_budget_check yes/no
- soft_warn_threshold_percent
- anti_split_detection_window
- emergency_procurement_enabled
- status

For **Procurement Threshold Rule**:

- policy_profile
- category
- procurement_type
- minimum_amount
- maximum_amount
- recommended_method
- allowed_methods
- approval_level
- special_conditions
- active

For **Approval Matrix Rule**:

- entity
- category
- value_band
- department scope
- required approvers in sequence
- finance mandatory yes/no
- accounting_officer mandatory yes/no

**Design decision**

Do **not** hardcode method thresholds in Python. Put them in reference DocTypes and version them by policy profile. That matches the architecture’s “reference tables should never be hardcoded” rule.

**Module 2 — Annual Procurement Plan (APP) Header Management**

Purpose: create and govern the formal APP record for a procuring entity and financial year.

**Core DocType**

- **Procurement Plan** as the APP master.

**Strengthened APP fields**

Keep the architecture’s fields, but add the controls below:

Existing architecture-aligned fields:

- plan_name / APP number
- entity
- financial_year
- plan_type
- budget_reference
- budget_approval_date
- budget_approved_by
- status
- total_budget
- created_by_department
- remarks

Add:

- plan_version
- parent_plan_version
- revision_type: Original / Supplementary / Revision / Administrative Update
- revision_reason
- preparation_start_date
- submission_date
- approval_date
- published_date
- locked_on
- locked_by
- policy_profile
- total_planned_amount
- total_committed_amount
- total_actual_amount
- currency
- approval_memo_attachment
- publication_reference
- audit_pack_file

These additions are justified by the requirement for version control, update/upgrade distinction, publication logging, snapshots, and audit export.

**Workflow**

Recommended APP workflow:

- Draft
- Department Consolidation
- Procurement Review
- Finance Review
- Submitted for Approval
- Approved
- Published
- Locked
- Superseded
- Cancelled

**Key rules**

- One active **Original Annual APP** per entity per financial year.
- Supplementary APPs are separate records linked back to the base annual APP.
- Once status reaches **Published** or **Locked**, direct line edits are blocked.
- Any change after lock requires a **Revision** or **Supplementary Plan**.
- Total APP value recalculates from approved line totals only.

**Module 3 — Procurement Plan Item Management**

Purpose: manage each APP line as the atomic planning unit from which later procurement execution flows.

**Core DocType**

- **Procurement Plan Item**.  
    The architecture models it as a child table, but for a serious public-sector system I strongly recommend making it a **full transaction DocType** with child tables for allocations/history instead of only a child row. It can still render inside the APP form as a grid, but it should exist as a standalone document for auditability, workflow hooks, and downstream references.

**Base fields from the architecture**

- parent_plan
- procurement_reference
- strategic_plan
- strategic_objective
- national_priority
- description
- category
- estimated_cost
- procurement_method
- funding_source
- quarter
- responsible_department
- status

**Recommended additional fields**

- procurement_title
- detailed_description/specification_summary
- item_group / spend_category / subcategory / item_class
- procurement_type: Goods / Works / Non-Consulting Services / Consulting Services / Asset Disposal
- estimated_cost_base
- approved_planned_cost
- quantity_estimate
- unit_of_measure
- budget_head
- cost_center
- programme/project
- source_of_funds
- multi-fund_flag
- delivery_location
- intended_procurement_method
- system_recommended_method
- method_override_reason
- procurement_rationale
- aggregation_group
- anti_split_group
- priority_level
- planned_initiation_quarter
- planned_advertisement_date
- planned_contract_award_date
- planned_contract_start
- planned_contract_end
- procurement_lead_time_days
- risk_score
- risk_level
- emergency_flag
- framework_flag
- recurring_flag
- reserved_budget_amount
- commitment_status
- downstream_requisition_count
- downstream_tender_reference
- line_status

These additions are driven by the requirements for category hierarchy, risk scoring, bundling suggestions, TCO optionality, lifecycle budget tracking, and traceability into later modules.

**Child tables under Procurement Plan Item**

- **Plan Item Budget Allocation**
- **Plan Item Milestone**
- **Plan Item Change Log**
- **Plan Item Compliance Check**
- **Plan Item Attachment**
- **Plan Item Justification**

**Key validations**

- Must link to an approved APP in editable state.
- Must link to at least one strategic objective.
- Must have a valid budget head.
- Estimated cost must be > 0.
- Quarter or planned initiation period required.
- Intended method required.
- If intended method differs from rules-based recommendation, override reason required.
- If high value / direct procurement / emergency / single source style case, justification mandatory.
- If similar lines exist in same entity and year, system flags potential fragmentation or aggregation opportunity.

**Module 4 — Budget Linkage & Commitment Control**

Purpose: turn the APP into a real financial control instrument rather than a planning wish list.

**Core design**

Use ERPNext budget structures where possible, but add procurement-aware controls:

- APP line links to **Budget head / GL / Cost Center / Project**.
- Approval of APP line can create a **planning reservation**.
- Approval of downstream requisition creates a **commitment/encumbrance**.
- PO/contract reduces available commitment balance.
- Invoice/payment converts commitment to actual.
- cancellation/reduction releases unused amount.

**Recommended DocTypes**

- **Budget Control Snapshot**
- **Procurement Commitment**
- **Budget Override Record**
- **Fund Allocation Detail**

**Budget statuses**

Per APP line:

- Unchecked
- Budget Available
- Budget Warning
- Budget Blocked
- Reserved
- Committed
- Partially Utilized
- Fully Utilized
- Released

**Required controls**

- Hard stop or soft warning based on rule profile.
- Commitment visibility before approval.
- Multi-fund allocation with auditable proration.
- Store exchange rate if foreign currency is ever allowed later.
- Show available balance, current commitments, and projected remaining balance during approval.

**Important implementation choice**

For public-sector mode, **do not create encumbrance merely because a planner typed a draft line**.  
Use this sequence instead:

- APP line approval = optional planning reservation
- Requisition approval = formal commitment trigger
- PO/contract = commitment consumption
- invoice/payment = actual posting

That gives better financial discipline and avoids over-reserving draft plans while still respecting the requirement for commitment control.

**Module 5 — Planning Governance, Thresholds, and Compliance Controls**

Purpose: embed the public-sector rule engine inside planning.

**Controls to implement**

1.  **Method recommendation engine**  
    Based on category + estimated value + policy profile + special condition.
2.  **Approval routing engine**  
    Based on amount, department, category, and whether special approvals are needed.
3.  **Anti-split / anti-fragmentation engine**  
    Detect similar descriptions, same category, same budget head, same department, close planning windows, and near-threshold values. The requirements explicitly call for bundling and aggregation suggestions.
4.  **Risk scoring**  
    Inputs can include value, method, urgency, repeat procurement, supplier concentration risk later, and strategic criticality. The requirements explicitly call for configurable procurement risk scoring.
5.  **Exception register**  
    High-risk, emergency, direct procurement, budget override, and method override lines should enter an exception queue.

**Recommended supporting DocTypes**

- **Procurement Risk Rule**
- **Method Advisory Result**
- **Aggregation Suggestion**
- **Exception Register Entry**
- **Conflict of Interest Declaration**  
    The source mentions COI declarations as mandatory for procurement staff and evaluation actors. Even though evaluation is later, the master declaration model should start here.

**Hard validations**

- Direct/special method line cannot move to approval without justification.
- Budget override cannot proceed without approving officer and written reason.
- Emergency flag requires post-facto review route.
- High-risk line requires compliance checklist completion before execution handoff.

**Module 6 — Schedule & Procurement Calendar Management**

Purpose: make the APP operational by showing when procurement events are expected to happen during the year.

For public-sector mode, keep this lighter than the donor-style milestone engine, but do not throw it away completely.

**Recommended approach**

Use:

- quarter-level planning as mandatory,
- month-level planning as optional,
- milestone dates for key phases where needed:
    - requisition target date
    - tender issue date
    - evaluation completion target
    - award target
    - contract start target
    - delivery completion target

The ERPNext planning document includes a richer milestone/time-estimation engine. For public-sector mode, borrow the useful part: configurable milestone templates and change logging, but avoid making the IFAD Plan/Actual grid the center of the design.

**Supporting DocTypes**

- **Procurement Milestone Template**
- **Plan Item Milestone**
- **Planning Calendar View**

**Rule**

Milestone dates can be manually adjusted, but every change is logged. That aligns with the requirement for manual override tracking.

**Module 7 — APP Revision, Supplementary Planning, and Publication**

Purpose: control the life of the APP after first approval.

**Core states**

- Original APP
- Supplementary APP
- Formal Revision
- Administrative Update
- Superseded Archive

**Why this matters**

The requirements explicitly call for versioning, snapshots, re-baselining, publication logs, and audit export.

**Recommended rules**

- Approved APP becomes read-only except through revision flow.
- Administrative updates can change non-financial metadata only.
- Financial, scope, timing, or method changes require revision or supplementary APP.
- Each revision creates a snapshot of old and new values.
- A published PDF/audit pack is stored and cannot be overwritten.

**Supporting DocTypes**

- **Procurement Plan Revision**
- **Procurement Plan Snapshot**
- **Published Plan Record**
- **Revision Approval Record**

**Outputs**

- APP print/export PDF
- line-level revision delta report
- budget variance between versions
- newly added / removed items report

**Module 8 — Reporting, Dashboards, and Audit**

Purpose: make the module usable by management, oversight, and auditors.

**Operational dashboards**

- APP coverage by department
- approved vs draft APP value
- APP by category
- APP by quarter
- APP by budget head
- high-risk planned procurements
- method exception counts
- fragmentation alerts
- budget warning/block counts

**Strategic dashboards**

- spend planned by national priority
- spend planned by strategic objective
- entity-level APP alignment coverage
- recurring procurement concentration by category

**Audit reports**

- APP approval trail
- line change log
- budget override report
- method override report
- supplementary plan register
- plan-to-requisition traceability
- complete procurement audit pack export capability  
    The requirements explicitly call for one-click export of audit packs and immutable logs.

**5) Recommended final DocType map for Phase 1**

**Master / reference DocTypes**

- National Development Plan
- National Development Priority
- Corporate Strategic Plan
- Strategic Objective
- Procurement Policy Profile
- Procurement Threshold Rule
- Procurement Method Rule
- Budget Control Rule
- Approval Matrix Rule
- Procurement Risk Rule
- Spend Category
- Funding Source
- Budget Head Mapping
- Procurement Milestone Template

**Transaction DocTypes**

- Procurement Plan
- Procurement Plan Item
- Procurement Plan Revision
- Procurement Commitment
- Budget Override Record
- Exception Register Entry
- Published Plan Record
- Procurement Plan Snapshot
- Purchase Requisition  
    The requisition remains downstream but is part of the handoff boundary.

**Child tables**

- Plan Item Budget Allocation
- Plan Item Milestone
- Plan Item Compliance Check
- Plan Item Attachment
- Plan Item Justification
- Plan Item Change Log

**6) Workflow design**

**6.1 Procurement Plan workflow**

Draft → Department Consolidation → Procurement Review → Finance Review → Submitted for Approval → Approved → Published → Locked

**Workflow rules**

- Department consolidation can only be edited by department planning users and procurement planners.
- Finance Review cannot be skipped when line items have budget implications.
- Approval requires all mandatory checks to pass.
- Publish creates snapshot and printable record.
- Locked blocks direct edits.

**6.2 Procurement Plan Item lifecycle**

Draft → Validated → Under Review → Approved in APP → Reserved → Requisitioned → In Procurement Process → Contracted → Closed / Cancelled

This lifecycle gives traceability beyond planning and supports later modules. It also aligns with the requirement for end-to-end traceability.

**6.3 Revision workflow**

Draft Revision → Review → Approved Revision → Published Revision → Supersede Prior Version

**7) Roles and permissions**

The architecture already proposes role-based workspaces and identifies Planning Authority, Procurement Officer, Department Officer, Finance Officer, Accounting Officer, and Auditor. Build on that.

**Recommended roles**

- **Planning Authority**
- **Procurement Planner**
- **Procurement Manager / Head of Procurement**
- **Department Planning Officer**
- **Finance/Budget Officer**
- **Accounting Officer**
- **Internal Auditor**
- **System Administrator**
- **Read-Only Oversight User**

**Permission model**

**Planning Authority**

- manage National Development Plan, priorities, strategy masters

**Procurement Planner**

- create/edit APP and APP lines before final approval
- cannot approve own final APP

**Department Planning Officer**

- submit departmental planning requirements
- view only own department’s draft lines unless wider rights granted

**Finance/Budget Officer**

- validate budget availability
- approve or reject overrides within authority
- cannot alter strategic references

**Head of Procurement**

- review method alignment, aggregation, compliance, and final planning readiness

**Accounting Officer**

- final approval of APP / supplementary APP
- approve exceptional overrides above threshold

**Internal Auditor**

- view logs, revisions, overrides, and audit packs
- no transactional edit rights

**System Administrator**

- configuration only, not substantive approval actor by default

This directly supports SoD, which the requirements treat as mandatory.

**8) Business rules that must be implemented**

**8.1 Mandatory strategic linkage**

Each APP line must link to:

- Corporate Strategic Plan
- Strategic Objective
- National Priority  
    If the entity is using the full chain, the system should derive the higher-level references automatically from the selected objective to prevent mismatches.

**8.2 Mandatory budget linkage**

No APP item can be approved without:

- budget head,
- cost center or project where applicable,
- confirmed budget status.

**8.3 Method advisory**

The system should recommend a procurement method from policy tables and flag deviations. It should not be fully open-text.

**8.4 Anti-split control**

If multiple similar lines in the same period and entity appear designed to avoid thresholds, block auto-approval and raise an exception. The source requirements call for demand aggregation and bundling suggestions; in a public-sector implementation, that should become a control, not just advice.

**8.5 Budget hard/soft stops**

This must be configurable by policy profile.

**8.6 Override governance**

Any override must record:

- overridden field
- old value
- new value
- reason
- approving user
- date/time

**8.7 Locking**

No editing after publish/lock except revision flow.

**8.8 Requisition gate**

A requisition must reference an approved APP item and cannot exceed its approved available amount without approved variation logic. The architecture already requires a plan item reference for requisitions.

**9) UI / workspace design**

The architecture already proposes workspaces by role. For this module, I’d implement four main workspaces first.

**9.1 Strategic Planning Workspace**

For Planning Authority.

- National plan
- corporate plan
- strategic objective registry
- alignment analytics

**9.2 Procurement Planning Workspace**

For Procurement Planner / Head of Procurement.

- APP list
- APP builder
- line validation queue
- aggregation alerts
- exception queue
- publication panel

**9.3 Budget Control Workspace**

For Finance.

- budget validation queue
- blocked/warning items
- commitment summary
- override approvals
- plan vs budget variance

**9.4 Executive / Audit Workspace**

For Accounting Officer / Auditor.

- pending APP approvals
- exception approvals
- supplementary APP register
- audit logs
- downloadable audit packs

**Important UX decision**

Do not make APP creation depend on users editing giant spreadsheets.  
Use:

- a strong line-item form for disciplined entry,
- a grid view for bulk review,
- and dashboards for validation.  
    The spreadsheet-like donor-style interface is useful as reference, but for public-sector core operations it should be secondary, not primary.

**10) ERPNext implementation approach**

The requirements explicitly say to use/extend ERPNext objects such as Budget, Supplier, Purchase Order, Purchase Invoice, Project, and GL entries, while introducing procurement-specific DocTypes.

**Recommended implementation approach**

- Keep KenTender as a **custom app layer**.
- Use ERPNext standard masters where practical:
    - Company
    - Fiscal Year
    - Cost Center
    - Project
    - Account / GL
    - Department
    - User
- Add custom procurement DocTypes for APP control rather than overloading Purchase Order or Material Request too early.
- Link downstream ERPNext purchasing/accounting docs back to procurement_plan_item.

**Important design call**

**Purchase Requisition** should remain a KenTender DocType, not just a renamed standard stock/purchase request, because public procurement approval requirements and APP traceability are stronger than standard private-sector purchasing flows. This is consistent with the architecture’s separate Requisition layer.

**11) Acceptance criteria for Phase 1**

A good Phase 1 implementation should pass at least these tests:

**Governance**

- User cannot approve and finalize their own APP when SoD rules prohibit it.

**Strategy linkage**

- Every approved APP line can be traced to a strategic objective and national priority.

**Budget control**

- A line with insufficient budget is either blocked or warning-routed based on policy settings.

**Anti-split**

- Three near-identical lines under the same department and budget head trigger an aggregation/fragmentation alert.

**Audit**

- Method, value, quarter, or budget overrides are fully logged with old/new values and approver identity.

**Lifecycle**

- Approved APP line can be selected on a requisition, and requisition cannot proceed without valid APP linkage.

**Locking**

- Once an APP is published/locked, user cannot edit it directly; they must create a revision or supplementary plan.

**Purchase Requisition**

- Purchase Requisition cannot be submitted without a valid linked Procurement Plan Item.

**12) MVP vs later enhancement**

**Must be in Phase 1**

- strategic alignment masters
- Procurement Policy Profile and threshold rules
- APP header + line item management
- budget linkage and validation
- approval workflow with SoD
- anti-split alerts
- method recommendation + override control
- revision/supplementary APP logic
- reporting and audit logs
- requisition handoff gate

**Can wait a bit**

- advanced risk scoring model
- sophisticated calendar simulation
- complex multi-fund proration automation
- full audit-pack bundle generation
- predictive analytics
- complex milestone engine modeled after donor templates

**13) Recommended final design stance**

For the public-sector Kentender build, I recommend this exact stance:

- Keep **Procurement Plan** as the formal APP master.
- Upgrade **Procurement Plan Item** into a first-class record, not just a passive child row.
- Add a configurable **policy/rules layer**.
- Add strong **budget control and commitment visibility**.
- Make **strategic linkage mandatory**.
- Make **requisition creation impossible without APP linkage**.
- Treat **revision and supplementary planning** as first-class workflows.
- Prioritize **auditability, SoD, and anti-fragmentation** over convenience features.

**14\. Recommended build sequence**

**Sprint 1**

- strategic masters
- Procurement Policy Profile
- threshold and approval rules
- Procurement Plan header

**Sprint 2**

- Procurement Plan Item standalone DocType
- validation engine
- strategy auto-linking
- budget checks

**Sprint 3**

- APP workflow
- role permissions
- exception register
- anti-split logic

**Sprint 4**

- publish/lock
- revision/snapshot
- commitment records
- audit logs and reports

**Sprint 5**

- requisition handoff integration
- dashboards
- hardening and UAT

**15\. Final recommendation**

The strongest move now is to treat this as the **authoritative Phase 1 design baseline**:

- APP is the formal public-sector control document
- APP Item is a first-class transactional record
- strategy, budget, and policy linkage are mandatory
- post-approval changes happen only through controlled revision
- requisitions are gated by approved APP items
- overrides and exceptions are never silent

That will keep KenTender squarely in the public-sector lane and stop the build from drifting into a generic purchasing app.