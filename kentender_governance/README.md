### Kentender Governance

KenTender governance module.

### KenTender architecture (STORY-CORE-002)

**Role:** Governance overlay; depends on core only among KenTender apps.  
**Allowed upstream KenTender deps:** `kentender`.  
**Do not** deep-import strategy, budget, or procurement internals—integrate via whitelisted `api` / documented contracts.  
Details: [App dependencies and boundaries](../docs/architecture/app-dependencies-and-boundaries.md).

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch 
bench install-app kentender_governance
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/kentender_governance
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
