# Milestone auto-seeding (FRS 4.1 / 4.5)

When a **Contract** first moves to status **Active**, KenTender creates baseline **ERPNext `Task`** rows flagged as contract milestones (`is_contract_milestone = 1`), linked to the contract’s **Project**.

## Behaviour

- **Trigger**: `Contract` document hook `on_update` → `seed_contract_milestones_on_contract_activation`.
- **Runs when**: `doc.status == "Active"` and the previous saved state was **not** already Active (including first save as Active, where there is no prior version).
- **Skips when**:
  - `frappe.conf.kentender_skip_milestone_seeding` is truthy, or
  - `frappe.flags.in_import`, or
  - the contract has no `project`, or
  - at least one **Task** already exists with `contract` = this contract and `is_contract_milestone` = 1.

## Generated tasks

For each phase (default **3**, configurable):

- **Subject**: phase label + award context (prefers **Tender** → **Procurement Plan Item** → **Item** name/code; falls back to contract title).
- **Payment %**: split evenly across rows; the last row is adjusted so the total is **100%**.
- **Deliverables / acceptance criteria**: standard template strings referencing the phase and contract/tender requirements.
- **Expected dates**: if `Contract.start_date` and `end_date` are set, `exp_start_date` / `exp_end_date` are allocated in equal slices across the contract period.
- **Status**: `milestone_status = Pending`, task `status = Open`.

When the row count is **3**, phase names depend on `contract_type` (**Goods** / **Works** / **Services**). For other counts, subjects use `Phase 1 … Phase N`.

## Configuration (`site_config.json`)

| Key | Purpose |
|-----|---------|
| `kentender_milestone_seed_count` | Number of milestone tasks (default **3**, clamped **1–12**). |
| `kentender_skip_milestone_seeding` | If true, disables automatic seeding (manual API still available if you need it). |

Ensure CLM custom fields on **Task** exist (`ensure_clm_custom_fields`).

## Manual retry

Whitelisted method: **`kentender.kentender.api.seed_contract_milestones`**

- Caller must have **write** permission on the contract.
- Contract must be **Active**.
- Idempotent: if milestone tasks already exist for the contract, no new rows are created.

## Audit

Successful seeding logs **`KenTender Audit Event`** with action **`contract_milestones_seeded`** and details including created task names, tender, and project.
