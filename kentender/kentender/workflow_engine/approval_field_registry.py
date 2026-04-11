# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-002: central registration of approval-controlled fields per DocType.

Authoritative stage is ``workflow_state``; derived ``status`` / legacy ``approval_status``
are set in DocType ``validate`` via :mod:`kentender.status_model.derived_status` where
registered — protect ``workflow_state`` so services must use
:func:`kentender.workflow_engine.safeguards.workflow_mutation_context`.
"""

from __future__ import annotations

from kentender.workflow_engine.safeguards import register_approval_controlled_fields


def register_default_ken_tender_approval_fields() -> None:
	"""Register shipped KenTender DocTypes that use engine-driven workflow stages."""
	register_approval_controlled_fields(
		"Purchase Requisition",
		("workflow_state",),
	)
	register_approval_controlled_fields(
		"Tender",
		("workflow_state",),
	)
	register_approval_controlled_fields(
		"Procurement Plan",
		("workflow_state",),
	)
	register_approval_controlled_fields(
		"Award Decision",
		("workflow_state",),
	)
	register_approval_controlled_fields(
		"Procurement Contract",
		("workflow_state",),
	)
	register_approval_controlled_fields(
		"Acceptance Record",
		("workflow_state",),
	)
	register_approval_controlled_fields(
		"Complaint",
		("workflow_state",),
	)
