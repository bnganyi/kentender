### Kentender Procurement

KenTender procurement module.

### KenTender architecture (STORY-CORE-002)

**Role:** Procurement / tendering lifecycle; sits on core, strategy, and budget.  
**Allowed upstream KenTender deps:** `kentender`, `kentender_strategy`, `kentender_budget`.  
**Do not** treat `kentender_stores` / `kentender_assets` as hard import dependencies (use explicit APIs if needed).  
Details: [App dependencies and boundaries](../docs/architecture/app-dependencies-and-boundaries.md).

### Wave 2 (procurement build)

Sprint tracker: [`docs/dev/WAVE 2 BACKLOG.md`](../docs/dev/WAVE%202%20BACKLOG.md). Full tickets and Cursor prompts: [`docs/prompts/Wave 2 Ticket Pack.md`](../docs/prompts/Wave%202%20Ticket%20Pack.md).

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch 
bench install-app kentender_procurement
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/kentender_procurement
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
