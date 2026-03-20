### KenTender

Public eProcurement System

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch master
bench install-app kentender
```

After install or upgrade, create/update ERPNext custom fields (Contract on PI, CLM fields on **Payment Entry**, etc.):

```bash
bench --site <yoursite> execute kentender.kentender.api.ensure_clm_custom_fields
```

**Retention (optional):** To skip auto-creating monthly informational `Retention Ledger` rows with type **Planned** during the daily reminder, set in `site_config.json`: `"kentender_skip_retention_planned_ledger": true`.

**External signatures (FRS 4.2):** Set `kentender_signature_verifier` and optionally `kentender_signature_strict` in `site_config.json`. See [docs/kentender_signature_adapter.md](docs/kentender_signature_adapter.md).

**Audit export:** `get_ken_tender_audit_event_report` and `download_ken_tender_audit_events_csv` — see [docs/kentender_audit_export.md](docs/kentender_audit_export.md).

**CIT / Inspection Committee:** `transition_cit_member`, `transition_inspection_committee_member` — see [docs/cit_icm_workflow.md](docs/cit_icm_workflow.md).

**Milestone seeding (FRS 4.5):** Baseline contract milestone `Task` rows are created on first **Active** transition. Optional: `kentender_milestone_seed_count`, `kentender_skip_milestone_seeding`. Manual: `seed_contract_milestones`. See [docs/milestone_seeding.md](docs/milestone_seeding.md).

**Governance Sessions MVP (Proceedings):** Draft proceedings (`Governance Session` + `Session Agenda Item`) are auto-created on first milestone completion and on contract handover completion. Includes `Locked` immutability and controlled transition APIs. See [docs/governance_sessions_mvp.md](docs/governance_sessions_mvp.md).

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/kentender
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
