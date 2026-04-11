# UAT user fixtures (reference)

Runtime seeding uses:

- **Minimal golden (canonical desk + portal test users):** `kentender.uat.minimal_golden.commands` / `seed_minimal_golden_*` (see [../README.md](../README.md)). Emails and roles are defined in `minimal_golden_canonical.json`.
- **MVP pack (through PR, optional):** `kentender.uat.mvp.commands.seed_uat_mvp` — reuses the **same** emails as minimal golden; business data uses `UAT-MVP*` identifiers in [`../seed_packs/mvp_canonical.json`](../seed_packs/mvp_canonical.json).

Matrix **Role** documents (Excel Role Catalogue) are ensured on migrate via `kentender.uat.bootstrap.ensure_uat_roles` / `after_migrate`.
