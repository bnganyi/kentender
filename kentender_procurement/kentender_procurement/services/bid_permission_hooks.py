# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Document-level permission hooks for Bid Submission (matrix §6.1 AS — Evaluator assignment)."""

from __future__ import annotations

import frappe

from kentender.permissions.registry import MATRIX_ROLE

EA = "Evaluator Assignment"
ES = "Evaluation Session"
_ACTIVE = "Active"


def bid_submission_has_permission(doc, ptype=None, user=None, debug=False) -> bool:
	"""Deny Evaluator desk access to bids unless actively assigned to an evaluation session for the tender.

	Frappe controller hooks may only deny; base DocPerm must still grant the Evaluator role.
	"""
	if not doc or not doc.get("name"):
		return True
	user = user or frappe.session.user
	if user == "Administrator":
		return True

	roles = frappe.get_roles(user)
	if MATRIX_ROLE.EVALUATOR.value not in roles:
		return True
	if ptype not in ("read", "write", "submit", "cancel", "print", "email"):
		return True

	tender = (doc.get("tender") or "").strip()
	if not tender:
		return True

	sessions = (
		frappe.get_all(ES, filters={"tender": tender}, pluck="name", limit=50) or []
	)
	for sn in sessions:
		if frappe.db.exists(
			EA,
			{
				"evaluation_session": sn,
				"evaluator_user": user,
				"assignment_status": _ACTIVE,
			},
		):
			return True
	return False
