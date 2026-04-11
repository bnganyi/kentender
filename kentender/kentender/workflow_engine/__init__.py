# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""KenTender reusable workflow / approval engine (WF-001).

See ``docs/workflow/Workflow Engine Architecture.md`` in the repository.
"""

from kentender.workflow_engine.approval_field_registry import register_default_ken_tender_approval_fields
from kentender.workflow_engine.safeguards import (
	document_validate_approval_controlled_fields,
	register_approval_controlled_fields,
	workflow_mutation_context,
)

# WF-002: shipped DocTypes (STAT-004/005; Tender / Plan stages).
register_default_ken_tender_approval_fields()

import kentender.status_model.derived_status  # noqa: F401 — STAT-003 mapper registration

__all__ = [
	"document_validate_approval_controlled_fields",
	"register_approval_controlled_fields",
	"workflow_mutation_context",
]
