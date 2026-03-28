### KenTender (monorepo)

End-to-end public eProcurement system. This repository contains **nine** Frappe apps under one tree, plus shared product documentation.

| Directory | Frappe `app_name` |
| --------- | ------------------ |
| [`kentender/`](kentender/) | `kentender` (Wave 0 **kentender_core** role) |
| [`kentender_strategy/`](kentender_strategy/) | `kentender_strategy` |
| [`kentender_budget/`](kentender_budget/) | `kentender_budget` |
| [`kentender_procurement/`](kentender_procurement/) | `kentender_procurement` |
| [`kentender_governance/`](kentender_governance/) | `kentender_governance` |
| [`kentender_compliance/`](kentender_compliance/) | `kentender_compliance` |
| [`kentender_stores/`](kentender_stores/) | `kentender_stores` |
| [`kentender_assets/`](kentender_assets/) | `kentender_assets` |
| [`kentender_integrations/`](kentender_integrations/) | `kentender_integrations` |

See [`docs/architecture/README.md`](docs/architecture/README.md) for naming vs the Wave 0 ticket and bench layout. **App dependency DAG, `required_apps` matrix, and naming conventions:** [`docs/architecture/app-dependencies-and-boundaries.md`](docs/architecture/app-dependencies-and-boundaries.md). **Package layout (services, api, tests, utils):** [`docs/architecture/application-package-layout.md`](docs/architecture/application-package-layout.md).

### Local bench layout

Clone or place this repo **anywhere** (common choice: `frappe-bench/apps/kentender_platform`). For each app, point bench at the **inner app folder** (the one that contains that app’s `pyproject.toml`):

```bash
cd $PATH_TO_YOUR_BENCH

# Example: symlinks (typical when the repo lives under apps/)
ln -sfn kentender_platform/kentender apps/kentender
ln -sfn kentender_platform/kentender_strategy apps/kentender_strategy
# … repeat for each app, or script from kentender_platform/scripts/link_apps.sh

bench setup requirements --dev
bench --site your.site install-app kentender   # per site, as needed
```

Alternatively use `bench get-app <app_name> $PATH_TO_REPO/<app_name>` for each app (bench will materialize under `apps/<app_name>`).

### CI / GitHub clone

CI checks out the monorepo root and runs `bench get-app kentender $GITHUB_WORKSPACE/kentender`. Other apps can be added to the workflow with the same pattern when they have tests.

### Contributing

Install pre-commit from the **repository root** (not inside a single app folder):

```bash
cd kentender_platform   # repo root containing docs/ and kentender/
pre-commit install
```

### CI

- **Server tests:** GitHub Actions installs `kentender` from `kentender/` and runs `bench run-tests --app kentender`.
- **Linters:** Semgrep and pip-audit on pull requests.

### License

mit
