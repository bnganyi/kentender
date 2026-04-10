# Minimal Golden seed pack

Canonical dataset: **[Minimal Golden Testing Scenario.md](../../docs/testing/Minimal%20Golden%20Testing%20Scenario.md)**  
Loader implementation pack: **[KenTender Minimal Golden Scenario Seed Loader Implementation Pack.md](../../docs/testing/KenTender%20Minimal%20Golden%20Scenario%20Seed%20Loader%20Implementation%20Pack.md)**

## Files

| File | Purpose |
|------|---------|
| `minimal_golden_canonical.json` | Mirror of `kentender/kentender/uat/minimal_golden/data/minimal_golden_canonical.json` — **keep in sync** when editing. |

## Load order (implemented in Python)

1. **Cleanup (optional):** remove UAT-MVP rows via `kentender.uat.minimal_golden.cleanup.cleanup_mvp_uat_data` (default before seed).
2. Base reference — procuring entity, departments, funding source, category, method. For each department with ``hod_email_key``, the matching ``users.internal`` row is **created if missing** (role, password), and a **User Permission** on **Procuring Entity** is added for that HOD when ``grant_hod_entity_user_permission`` is true (default). Full user seed also grants entity permission to each internal user when ``grant_entity_user_permission`` is true (default).
3. Strategy — national framework → … → performance target.
4. Budget — control period, budget, main budget line.
5. Users — internal + supplier personas.
6. **Re-base-ref** — refresh department HOD links after users exist.
7. Purchase requisition — `PR-MOH-0001` approved with budget reservation (SP1).
8. Tender — `TD-MOH-0001` (manual origin), aligned with strategy/budget links.
9. **Bid Submission** — two rows (`future_business_ids` **bid_1** / **bid_2** → `BID-TD-0001-01`, `BID-TD-0001-02`) linked to the tender.
10. **Bid Receipt** — one row for **bid_1** (`bid_receipt` in JSON); sets **Latest Receipt** on that bid submission.

**Deferred:** Store (CMS) and Asset Category (MED-DIAG) — no KenTender DocTypes yet (see JSON `deferred_masters_note`).  
**Future:** remaining `future_business_ids` (opening session, award, contract, …) — verified only when DocTypes exist and loaders are added.

## Commands

**Step 1 (master data only):**

```bash
bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.seed_minimal_golden_base_ref_console
```

**Step 2 (strategy chain only — run step 1 before this):**

```bash
bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.seed_minimal_golden_strategy_console
```

From code, `seed_minimal_golden_strategy()` matches the console (strategy only). Pass `ensure_base_ref=True` if you want an idempotent shortcut that runs step 1 first in the same call.

**Step 3 (budget only — run steps 1–2 before this):**

```bash
bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.seed_minimal_golden_budget_console
```

From code, `seed_minimal_golden_budget()` matches the console. Pass `ensure_base_ref=True` and/or `ensure_strategy=True` for idempotent shortcuts.

**Step 4 (users + re-base-ref — run step 1 first; steps 2–3 recommended before PR / step 5):**

```bash
bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.seed_minimal_golden_users_console
```

Upserts all `users.internal` and `users.suppliers` from the canonical JSON (roles, passwords, Procuring Entity user permissions), then runs `load_base_ref` again to refresh department HOD links — same as the full seed pipeline before the purchase requisition.

From code, `seed_minimal_golden_users()` matches the console. Pass `ensure_base_ref=True` to run step 1 data load first in the same call.

**Step 5 (purchase requisition + budget reservation — run steps 1–4 first):**

```bash
bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.seed_minimal_golden_requisition_console
```

Creates the canonical approved **Purchase Requisition** (`PR-MOH-0001`) with budget reservation and the canonical **Tender** (`TD-MOH-0001`), matching the tail of the full seed. Requires **steps 1–4** (entity, strategy, budget, users). From code, `seed_minimal_golden_requisition()` matches the console. Pass `ensure_base_ref=True`, `ensure_strategy=True`, and/or `ensure_budget=True` for idempotent shortcuts that run earlier steps in the same call.

After step 5, **`verify_minimal_golden_console`** should pass for the golden dataset.

**Full chain (through approved PR):**

```bash
bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.seed_minimal_golden_console
```

Verify / reset:

```bash
bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.verify_minimal_golden_console
bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.reset_minimal_golden_console
```

Password: `users.default_password` in JSON, or env **`KENTENDER_MINIMAL_GOLDEN_PASSWORD`**.

## Implementation layout (in app)

Source: `kentender/kentender/uat/minimal_golden/` — `base_ref.py`, `strategy.py`, `budget.py`, `users.py`, `requisition.py`, `procurement_planning.py`, `tender.py`, `commands.py`, `verify.py`, `reset.py`, `cleanup.py`, `dataset.py`, `paths.py`.
