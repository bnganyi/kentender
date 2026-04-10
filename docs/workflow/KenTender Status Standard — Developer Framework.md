# KenTender status standard — developer framework (STAT-001)

This note is the **developer-facing** companion to [KenTender Standard Status Model (System-Wide)](KenTender%20Standard%20Status%20Model%20%28System-Wide%29.md). It defines how we classify fields and where code lives.

## Three layers (normative)

| Layer | Field | Who sets it | Use in business logic |
|-------|--------|-------------|------------------------|
| 1 | `docstatus` | Frappe submit/cancel | Never encode procurement stage |
| 2 | `workflow_state` | Workflow services only (`workflow_mutation_context`) | **Authoritative** stage, permissions, queues, reports |
| 3 | `status` (optional) | Derived in `validate` or service from `workflow_state` | Reporting / dashboards only |

## One field = one meaning

If two columns express the same stage, **one is deprecated**: hide from UI, stop writing independently, migrate to a single source (`workflow_state`).

## Field classification (use in audits and code review)

| Class | Meaning | Typical examples | Desk |
|-------|---------|------------------|------|
| **A — Lifecycle** | Frappe document lifecycle | `docstatus` | System |
| **B — Authoritative workflow** | Current business stage | `workflow_state` | Read-only; services only |
| **C — Derived summary** | Computed from B | `status` when kept | Read-only; never user-edited |
| **D — Deprecated / duplicate** | Same meaning as B or C | Legacy `approval_status` | Hidden; mirror or remove |

**Rule:** Business rules and `get_all` filters for **stage** use **B**, not C or `docstatus`.

## Code map

- **Registry & derivation:** `kentender.status_model.derived_status` — `register_doctype_summary_mapping`, `derive_summary_status`, `apply_registered_summary_fields`.
- **Mutation guard:** `kentender.workflow_engine.safeguards` — `register_approval_controlled_fields` lists **B** fields only; `workflow_mutation_context` for service writes.
- **Per-DocType `validate`:** Call `apply_registered_summary_fields(doc)` when a mapping is registered (after `workflow_state` is final for this save).

## Open extensions

When adding a new approval DocType:

1. Register **B** fields with `register_approval_controlled_fields`.
2. Either register a **C** mapping or omit `status`.
3. Mark **D** fields hidden and stop independent writes.
4. Add a row to [STAT Implementation Tracker](STAT%20Implementation%20Tracker.md) (STAT-001–014 execution checklist).
