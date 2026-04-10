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

Password: `users.default_password` in the JSON, or override with env **`KENTENDER_UAT_MVP_PASSWORD`**.

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

## Purchase Requisition phase (Wave 2) — end-to-end without System Manager

UI testers can run **reference masters → strategy chain → budget → PR submit/approve** using only the seeded **KT UAT** personas (after `bench migrate` and one console seed).

1. Run **`bench migrate`** so Workspace docs and DocType permission JSON sync.
2. Roles **`KT UAT *`** are created automatically on migrate (`after_migrate`).
3. Create desk users (once per site):

   ```bash
   bench --site kentender.midas.com execute kentender.uat.bootstrap.seed_pr_uat_users_console
   ```

4. Log in with (default password in [`kentender/uat/bootstrap.py`](../kentender/kentender/uat/bootstrap.py) — **`DEFAULT_PASSWORD`**; change on shared environments):

   | User | Role | Default workspace |
   | --- | --- | --- |
   | `strategy.uat@ken-tender.test` | KT UAT Strategy Manager | KenTender Strategy |
   | `budgetofficer.uat@ken-tender.test` | KT UAT Budget Officer | KenTender Budget |
   | `requisitioner.uat@ken-tender.test` | KT UAT Requisitioner | KenTender My Work |
   | `hod.uat@ken-tender.test` | KT UAT HOD | KenTender Approvals |
   | `financeapprover.uat@ken-tender.test` | KT UAT Finance Approver | KenTender Approvals |
   | `procurement.uat@ken-tender.test` | KT UAT Procurement Officer | KenTender Procurement |

5. **Suggested journey order (through approved / planning-ready PR):**

   1. **Strategy Manager** — **KenTender Strategy**: procuring entity, department, funding source, category, method (or use **KenTender Procurement** / masters as applicable); national framework → pillars/objectives → entity strategic plan → programs/sub-programs → outputs/targets as required by your test case. If national reference rows are **locked** when Active, create or use **Draft** records per DocType rules.
   2. **Budget Officer** — **KenTender Budget**: budget control period → budget → budget lines (amounts your PR will consume).
   3. **Requisitioner** — **KenTender My Work**: new **Purchase Requisition**, set strategy/budget links, add lines, save/submit per workflow.
   4. **HOD** → **Finance Approver** — **KenTender Approvals** (**Pending Requisition Approvals**). **Procurement Officer** — **KenTender Procurement** for **Planning Ready Requisitions** and related ops.

6. All six personas can open **KenTender My Work**. **KenTender Procurement** is for procurement/strategy/budget/auditor-style desk roles (not the pure requisitioner). **KenTender Approvals** is for HOD and finance approvers. Strategy and Budget workspaces stay visible to the broader UAT role set for cross-checking.

7. Full scripted IDs and SP1 loaders remain in [`KenTender Seed Data.md`](../docs/testing/KenTender%20Seed%20Data.md); this slice provides **navigation, roles, permissions for strategy/budget masters, and users** so Link fields on PR resolve for non–System Manager testers.
