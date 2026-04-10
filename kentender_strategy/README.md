### Kentender Strategy

KenTender strategy module.

### KenTender architecture (STORY-CORE-002)

**Role:** Strategy layer (plans and policies upstream of budget and procurement).  
**Allowed upstream KenTender deps:** `kentender` only.  
**Do not** import `kentender_budget`, `kentender_procurement`, or internal modules of governance/compliance/stores/assets/integrations.  
Details: [App dependencies and boundaries](../docs/architecture/app-dependencies-and-boundaries.md).

### Dev/UAT: purge all strategy data

**System Manager only.** Deletes every document in the core strategy DocTypes (national framework through performance target, including revision records) and clears strategy link fields on **Purchase Requisition** and **Budget Line**. Does not remove entities, budgets, or PR headers.

```bash
bench --site kentender.midas.com execute kentender_strategy.services.purge_all_strategy_data.purge_all_strategy_data_console
```

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch 
bench install-app kentender_strategy
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/kentender_strategy
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
