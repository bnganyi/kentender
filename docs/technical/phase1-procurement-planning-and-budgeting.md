# KenTender Phase 1: Procurement Planning and Budgeting (Technical Reference)

## Scope
Phase 1 is responsible for producing a defensible **Annual Procurement Plan (APP)** that:
- links every planned procurement line to strategic objectives,
- enforces budget discipline and commitment reservation rules,
- governs procurement method recommendations using policy/threshold data,
- prevents threshold circumvention via anti-split controls,
- and provides a controlled handoff into **Purchase Requisitions (PRs)** for downstream execution.

## Core DocTypes (current baseline)

Typical core records include:
- `Procurement Plan` (APP header / governance record)
- `Procurement Plan Item` (APP line / governance atomic unit)
- Policy/reference masters:
  - `Procurement Policy Profile`
  - `Procurement Threshold Rule`
  - `Approval Matrix`
  - `Spend Category`
  - `Funding Source`
- Budget/commitment:
  - `Budget Override Record` (gated exception logging)
  - Commitment integration is partially implemented and still being deepened
- Publication snapshots / audit packs:
  - `Published Plan Record` (immutable snapshot registry)

## Server-side Enforcement Points (where the gates live)
Current implementation maps rules to one (or more) of:
- DocType `validate` / `before_submit` / `on_submit` hooks
- Whitelisted APIs for controlled transitions (bench/UAT)
- Workflow transition guards (if implemented via ERPNext workflow)

### Contract with security: “No silent overrides”
For any override of:
- approved amounts,
- timing/quarter allocations,
- procurement method recommendation,
- approval routing level,
the system must:
1. require a reason,
2. write a durable audit evidence record,
3. and keep old/new values visible for reviewers.

## Strategic alignment enforcement
Current behavior:
- `Procurement Plan Item` must not be approved unless strategic references are valid.
- Each line must map to the strategic objective hierarchy required by architecture.

Implementation evidence:
- `_phase1_validate_item_before_first_approval` enforces strategic gating at plan-item approval path
- missing/invalid strategic linkage blocks progression

## APP versioning / locking / publication
Current behavior:
- Draft vs Submitted vs Approved vs Published vs Locked vs Superseded are governed states.
- After Accounting Officer approval (or the configured lock point):
  - direct edits are blocked,
  - changes must go through revision/supplementary records,
  - and an immutable publication snapshot is generated.

Implementation evidence:
- Header hooks in `kentender/hooks.py`:
  - `phase1_procurement_plan_before_insert`
  - `phase1_procurement_plan_validate`
  - `phase1_procurement_plan_on_submit`
  - `phase1_procurement_plan_on_update_after_submit`
- Controlled transition API:
  - `phase1_transition_procurement_plan_status`
- Active workflow records:
  - `Procurement Plan Workflow`
  - `Procurement Plan Revision Workflow`
- Snapshot and lock side effects:
  - `_phase1_create_published_snapshot`
  - `_phase1_lock_procurement_plan`
- Revision publish orchestration:
  - `phase1_publish_procurement_plan_revision` (controlled publish service)
  - `phase1_procurement_plan_revision_validate` (revision governance checks)
  - `_phase1_apply_revision_publish_side_effects` (parent APP supersede + metadata stamping + audit event)

## Procurement Plan Item governance
Current behavior (line-level):
- On transition to “Under Review”, the approval chain must be generated from the approval matrix rule set.
- Only authorized roles can progress approvals.
- Status changes must be controlled (no manual status edits after submit).

Implementation evidence:
- `generate_approval_chain` builds level approvals from `Approval Matrix`
- `approve_plan_item` / `reject_plan_item` enforce controlled progression
- manual post-submit status mutation is blocked outside controlled paths

## Budget lifecycle and commitment discipline
Current behavior:
- Budget availability must be checked before approving lines into executable APP.
- When Purchase Requisitions (PRs) are generated, commitment/encumbrance must be reserved.
- Plan totals must reflect line-level states and lifecycle amounts.

Current gap:
- ERPNext budget/GL encumbrance integration remains partial and is a next hardening step

## Threshold & method advisory engine (+ anti-split)
Current behavior:
- procurement method is recommended from policy/threshold rules based on:
  - estimated value,
  - procurement type,
  - category,
  - emergency/framework flags.
- anti-split controls block plans that attempt to avoid threshold approvals by fragmenting similar lines within a configured window.

Implementation evidence:
- `_phase1_recommend_procurement_method_for_item` applies threshold guidance
- threshold ambiguity hard-stop: approval is blocked when more than one active threshold rule matches a line
- threshold allowed-method enforcement: selected method must be present in matched rule `allowed_methods` (when configured)
- policy-profile gate for non-competitive methods: `Direct Procurement` / `Restricted Tender` require justification when profile flag is enabled
- method override reason is mandatory when deviating from recommendation
- anti-split block is enforced at plan-item approval gate, with risk scoring (`risk_score`, `risk_level`) for reviewer visibility
- override evidence is deduplicated via `_phase1_upsert_budget_override_record` to prevent duplicate `Budget Override Record` rows on repeated approval actions

## Handoff to requisitions (Wave 1 bridge)
Current behavior:
- Purchase Requisitions (PRs) must reference an approved `Procurement Plan Item`.
- a PR cannot progress if its plan item is not in an executable/approved state.

Current gap:
- full requisition-to-commitment bridge in live `kentender` app remains partial

## Reporting / dashboards
Current status:
- APP totals by stage (Draft/Submitted/Approved/Published/Locked)
- budget lifecycle counters (planned vs committed vs actual where applicable)
- threshold advisory coverage and “override incidents”
- anti-split detection summary

Implemented service layer:
- `phase1_get_reporting_snapshot(company, fiscal_year)`:
  - returns aggregate APP status counts and totals,
  - plan-item budget/risk distributions,
  - override incident totals by type,
  - PR readiness and linked-tender rollups,
  - handoff row view (`Requisition Tender Handoff`).
- `phase1_download_reporting_snapshot_csv(company, fiscal_year)`:
  - exports handoff snapshot rows as CSV for downstream reporting tools.

Current gap:
- Desk-native chart widgets and packaged evidence-export bundles are still pending.

## Whitelisted bench APIs (current baseline)
Stable UAT/service entrypoints currently include:
- `phase1_transition_procurement_plan_status` (controlled APP header transitions)
- `approve_plan_item` / `reject_plan_item` (controlled plan-item progression)
- `phase1_get_reporting_snapshot` / `phase1_download_reporting_snapshot_csv` (reporting + export APIs)

## Audit evidence
Current behavior:
- controlled transitions write:
  - workflow comments
  - append-only audit event entries (or immutable record snapshots)
  - old/new values for sensitive updates

