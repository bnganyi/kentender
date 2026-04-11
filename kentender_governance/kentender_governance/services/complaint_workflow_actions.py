# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-015: Complaint + :mod:`kentender.workflow_engine` (routes, ``apply_step_decision``).

Uses only ``kentender`` APIs (no procurement service imports). Hold/lock rules in
:mod:`complaint_hold_services` remain authoritative.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document

from kentender.workflow_engine.execution import apply_step_decision
from kentender.workflow_engine.routes import get_active_route_instance, get_or_create_active_route

C = "Complaint"


def attach_route_after_intake(complaint_name: str) -> str | None:
	"""If a matching **KenTender Workflow Policy** exists, create an Active route instance."""
	name = (complaint_name or "").strip()
	if not name:
		return None
	return get_or_create_active_route(C, name)


def apply_route_decision_after_admissibility_review(
	doc: Document,
	*,
	admissibility_outcome: str,
	actor_user: str,
	comments: str | None,
	previous_state: dict[str, Any],
	new_state: dict[str, Any],
) -> None:
	"""After ``review_complaint_admissibility`` saves, complete the current route step if a route exists."""
	rid = get_active_route_instance(C, doc.name)
	if not rid:
		return
	out = (admissibility_outcome or "").strip()
	if out == "Inadmissible":
		decision = "Reject"
	elif out == "Deferred":
		decision = "Return"
	else:
		decision = "Approve"
	u = (actor_user or "").strip() or frappe.session.user
	apply_step_decision(
		rid,
		decision,
		user=u,
		comments=comments,
		reference_doctype=C,
		reference_docname=doc.name,
		previous_state=previous_state,
		new_state=new_state,
		log_action="admissibility_review",
		hook_action="admissibility_review",
	)
