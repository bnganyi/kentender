# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""KenTender reusable workflow / approval engine (WF-001).

See ``docs/workflow/Workflow Engine Architecture.md`` in the repository.
"""

from kentender.workflow_engine.safeguards import (
	document_validate_approval_controlled_fields,
	register_approval_controlled_fields,
	workflow_mutation_context,
)

# Default registration for shipped approval-controlled DocTypes (STAT-004/005).
# Authoritative stage is workflow_state only; derived status is enforced in DocType validate.
register_approval_controlled_fields(
	"Purchase Requisition",
	("workflow_state",),
)

import kentender.status_model.derived_status  # noqa: F401 — STAT-003 mapper registration

__all__ = [
	"document_validate_approval_controlled_fields",
	"register_approval_controlled_fields",
	"workflow_mutation_context",
]
