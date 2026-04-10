# KenTender workflow engine architecture (WF-001)

Developer map tying [Approval Workflow Specification v2](KenTender%20Approval%20Workflow%20Specification%20v2.md) §2 to code under **`kentender.workflow_engine`**.

## Stable lifecycle vs dynamic route

- **Lifecycle (Layer A):** DocType-level states (e.g. Draft → Pending → Approved) are **stable** across records of that type.
- **Policy + route (Layers B–C):** Which approvers and steps apply is **dynamic**, driven by **KenTender Workflow Policy** → **KenTender Approval Route Template** → **KenTender Approval Route Instance** (+ step children).
- **Action authorization (Layer D):** Who may act on the current step is enforced in services (`workflow_engine.actions`, controlled-action gates, SoD, assignment).

## Package layout (`kentender.workflow_engine`)

| Module | Responsibility |
|--------|----------------|
| `safeguards` | WF-002: registry of approval-controlled fields per DocType; `workflow_mutation_context()` for authorized saves; `validate` hook target |
| `policies` | WF-004/009: policy helpers; SoD delegation |
| `routes` | WF-005/006/007: template/instance helpers; `resolve_route_for_object` |
| `actions` | WF-008: submit/approve/reject/return execution; emits **KenTender Approval Action** rows |
| `hooks` | WF-010: ordered post-transition side-effect hooks |

## Integration for domain apps

1. Register approval-controlled fields with `register_approval_controlled_fields(doctype, fields)`.
2. Wrap any service that mutates those fields in `with workflow_mutation_context():`.
3. Resolve routes before first submit; run transitions through `workflow_engine.actions` (or adapters that call the same primitives).
4. Do **not** change `workflow_state` from client scripts or random server code outside the context manager.

## Related

- [Cursor Workflow Implementation Pack v2](KenTender%20Cursor%20Workflow%20Implementation%20Pack%20v2.md)  
- [WF Implementation Tracker](WF%20Implementation%20Tracker.md)
