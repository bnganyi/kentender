# KenTender UAT support (repository layout)

This tree holds **documentation and future loaders** for seeded scenarios. It complements in-app code under [`kentender/kentender/uat/`](../kentender/kentender/uat/) (import: `kentender.uat.bootstrap`).

**Workspace JSON location:** Frappe only syncs workspaces from the nested module package — see [`KenTender Workspace Conventions.md`](../docs/testing/KenTender%20Workspace%20Conventions.md).

## Folders

| Path | Purpose |
| --- | --- |
| `seed_packs/` | Scenario packs SP1–SP7, baseline fragments, [`mvp_canonical.json`](seed_packs/mvp_canonical.json), and [`minimal_golden/`](seed_packs/minimal_golden/README.md). |
| `journeys/` | AT script notes or exports (future). |
| `users/` | Optional user-fixture docs; see [users/README.md](users/README.md). |

## MVP auto-seed (through Purchase Requisition)

Deterministic **BASE-REF → BASE-STRAT → BASE-BUD → SP1** load for milestone testing (see `docs/testing/Cursor ticket pack for MVP auto-seeding.md`).

1. **`bench migrate`** on the site.
2. **Seed** (console; runs as Administrator):

   ```bash
   bench --site kentender.midas.com execute kentender.uat.mvp.commands.seed_uat_mvp_console
   ```

3. **Verify** (exits non-zero if checks fail):

   ```bash
   bench --site kentender.midas.com execute kentender.uat.mvp.commands.verify_uat_mvp_console
   ```

4. **Reset + re-seed** (deletes `UAT-MVP*` business data, then loads again):

   ```bash
   bench --site kentender.midas.com execute kentender.uat.mvp.commands.reset_uat_mvp_console
   ```

Password: `users.default_password` in the JSON (`k3nTender!golden`), or override with env **`KENTENDER_MINIMAL_GOLDEN_PASSWORD`** (same as minimal golden).

Bundled dataset path (for `bench` installs): `kentender/kentender/uat/mvp/data/mvp_canonical.json` (keep in sync with `uat/seed_packs/mvp_canonical.json` when editing).

## Minimal Golden Scenario (canonical MVP chain — SP1 implemented)

Single end-to-end workbook: [`docs/testing/Minimal Golden Testing Scenario.md`](../docs/testing/Minimal%20Golden%20Testing%20Scenario.md). Loader stories: [`KenTender Minimal Golden Scenario Seed Loader Implementation Pack.md`](../docs/testing/KenTender%20Minimal%20Golden%20Scenario%20Seed%20Loader%20Implementation%20Pack.md).

**Relationship to MVP:** `seed_minimal_golden` **by default** calls `cleanup_mvp_uat_data()` first so `UAT-MVP*` rows (including strategy, planning links, and PRs) are removed and do not collide with golden MOH data. To seed golden without touching MVP, call `seed_minimal_golden(cleanup_mvp=False)` from code (not the default console entrypoint).

1. **`bench migrate`** on the site.
2. **Optional — step-by-step seed** (each idempotent where noted):

   - Step 1 — master data: `seed_minimal_golden_base_ref_console`
   - Step 2 — strategy only (after step 1): `seed_minimal_golden_strategy_console`
   - Step 3 — budget only (after steps 1–2): `seed_minimal_golden_budget_console`
   - Step 4 — users + base_ref refresh (after step 1; steps 2–3 before PR): `seed_minimal_golden_users_console`
   - Step 5 — purchase requisition (after steps 1–4): `seed_minimal_golden_requisition_console`  
   See [`uat/seed_packs/minimal_golden/README.md`](seed_packs/minimal_golden/README.md).

3. **Full seed** (console; removes MVP UAT data then loads MOH → strategy → budget → users → `PR-MOH-0001` approved):

   ```bash
   bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.seed_minimal_golden_console
   ```

4. **Verify** (exits non-zero if checks fail):

   ```bash
   bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.verify_minimal_golden_console
   ```

5. **Reset + re-seed** (deletes golden business rows, optionally clears MVP again, then loads golden):

   ```bash
   bench --site kentender.midas.com execute kentender.uat.minimal_golden.commands.reset_minimal_golden_console
   ```

Password: `users.default_password` in JSON, or env **`KENTENDER_MINIMAL_GOLDEN_PASSWORD`**.

Bundled dataset: `kentender/kentender/uat/minimal_golden/data/minimal_golden_canonical.json` — keep in sync with `uat/seed_packs/minimal_golden/minimal_golden_canonical.json`.

**Matrix ↔ xlsx ↔ golden seed check** (Role Catalogue vs `MATRIX_ROLE` vs which roles have a golden test user):

```bash
bench --site kentender.midas.com execute kentender.uat.verify_matrix_alignment.verify_matrix_alignment_console
```

See [`docs/security/Implementation_Audit_vs_Permissions_Matrix_xlsx.md`](../docs/security/Implementation_Audit_vs_Permissions_Matrix_xlsx.md).

## Purchase Requisition phase (Wave 2) — end-to-end without System Manager

Matrix **Role** documents are created on every migrate (`after_migrate`). Desk and portal **users** come only from the **minimal golden** seed (see above): e.g. `requisitioner.test@ken-tender.test`, `strategyadmin.test@ken-tender.test`, `strategyreviewer.test@ken-tender.test`, `hod.test@ken-tender.test`, `finance.test@ken-tender.test`, and the rest of `minimal_golden_canonical.json` — not from a separate PR-phase UAT user list.

**Suggested journey order (through approved / planning-ready PR):**

1. **Procurement / strategy roles** — **KenTender Strategy** or **KenTender Procurement**: procuring entity, department, funding source, category, method; national framework → pillars/objectives → entity strategic plan → programs/sub-programs → outputs/targets as required. If national reference rows are **locked** when Active, create or use **Draft** records per DocType rules.
2. **Budget** — **KenTender Budget**: budget control period → budget → budget lines (amounts your PR will consume).
3. **Requisitioner** — **KenTender My Work**: new **Purchase Requisition**, set strategy/budget links, add lines, save/submit per workflow.
4. **HOD** → **Finance** — **KenTender Approvals** (**Pending Requisition Approvals**). **Procurement Officer** — **KenTender Procurement** for **Planning Ready Requisitions** and related ops.

For scripted **UAT-MVP** business IDs (separate entity `UAT-MVP-PE`), run `kentender.uat.mvp.commands.seed_uat_mvp` — it upserts the **same** golden test emails against that dataset.

Full scripted IDs and SP1 loaders remain in [`KenTender Seed Data.md`](../docs/testing/KenTender%20Seed%20Data.md).

## Obsolete seed users (one-off cleanup)

Sites that previously ran the old PR-phase desk seed or MVP with `*.uat-mvp@ken-tender.test` can remove those **User** rows without touching minimal golden accounts:

```bash
bench --site kentender.midas.com execute kentender.uat.wipe_test_data.purge_legacy_uat_seed_users_console
```

Implementation: [`kentender.uat.wipe_test_data`](../kentender/kentender/uat/wipe_test_data.py) (`LEGACY_SEED_USER_EMAILS`).

## Pytest / bench test fixture users (`_kt_*@test.local`)

Automated tests create System Users with emails like `_kt_pr04_approver@test.local`. TearDown now deletes them; for sites that already have leftovers:

```bash
bench --site kentender.midas.com execute kentender.uat.wipe_test_data.purge_kt_test_local_users_console
```

Helpers: [`kentender.uat.kt_test_local_users`](../kentender/kentender/uat/kt_test_local_users.py).

## Obsolete `KT UAT *` Frappe Roles

Historical Role documents used a `KT UAT …` prefix before the matrix moved to plain names (`Requisitioner`, etc.). To remove those rows (and disposable test roles like `KT PQ Test Role`) from the site:

```bash
bench --site kentender.midas.com execute kentender.uat.wipe_test_data.purge_legacy_kt_roles_console
```

Implementation: [`kentender.uat.legacy_kt_roles`](../kentender/kentender/uat/legacy_kt_roles.py).
