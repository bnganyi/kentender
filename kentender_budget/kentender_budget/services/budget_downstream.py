# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Downstream validation API for procurement modules (BUD-014).

Stable entry points for requisition/planning/contract callers. Delegates to ledger-backed
availability where appropriate.
"""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe import _
from frappe.utils import flt, get_datetime

from kentender_budget.services.budget_availability import (
	BudgetAvailability,
	availability_headroom,
	get_budget_availability as _get_availability,
)

BL = "Budget Line"


def get_budget_availability(
	budget_line_id: str,
	as_of_datetime: datetime | str | None = None,
) -> BudgetAvailability:
	return _get_availability(budget_line_id, as_of_datetime=as_of_datetime)


def validate_budget_line(
	budget_line_id: str,
	entity: str,
	as_of_date: datetime | str | None = None,
) -> None:
	"""Ensure the line exists, belongs to *entity*, and is usable.

	:param as_of_date: Reserved for future as-of checks; passed to availability when set.
	"""
	ent = (entity or "").strip()
	if not ent:
		frappe.throw(_("Procuring Entity is required."), frappe.ValidationError)
	if not budget_line_id or not frappe.db.exists(BL, budget_line_id):
		frappe.throw(_("Budget Line not found."), frappe.DoesNotExistError)
	line = frappe.get_doc(BL, budget_line_id)
	if (line.status or "").strip() == "Cancelled":
		frappe.throw(_("Budget Line is cancelled."), frappe.ValidationError, title=_("Invalid line"))
	if (line.procuring_entity or "").strip() != ent:
		frappe.throw(
			_("Budget Line does not belong to Procuring Entity {0}.").format(frappe.bold(ent)),
			frappe.ValidationError,
			title=_("Entity mismatch"),
		)
	if as_of_date is not None:
		_get_availability(budget_line_id, as_of_datetime=get_datetime(as_of_date))


def validate_funds_or_raise(
	budget_line_id: str,
	amount: float,
	stage: str,
	entity: str,
) -> None:
	"""Raise ``ValidationError`` if *amount* cannot be satisfied for *stage*.

	*stage* (case-insensitive):

	- ``reserve`` — uncommitted headroom must cover *amount*.
	- ``commit_from_reserved`` — reserved balance must cover *amount*.
	- ``commit_from_available`` — same as reserve (commit without prior reservation).
	"""
	validate_budget_line(budget_line_id, entity)
	amt = flt(amount)
	if amt <= 0:
		frappe.throw(_("Amount must be positive."), frappe.ValidationError)
	st = (stage or "").strip().lower().replace(" ", "_")
	if st == "reserve":
		if availability_headroom(budget_line_id) + 1e-9 < amt:
			frappe.throw(
				_("Insufficient budget availability to reserve {0}.").format(amt),
				frappe.ValidationError,
				title=_("Insufficient funds"),
			)
	elif st in ("commit", "commit_from_reserved"):
		av = _get_availability(budget_line_id)
		if flt(av.reserved) + 1e-9 < amt:
			frappe.throw(
				_("Insufficient reserved balance to commit {0}.").format(amt),
				frappe.ValidationError,
				title=_("Insufficient reservation"),
			)
	elif st == "commit_from_available":
		if availability_headroom(budget_line_id) + 1e-9 < amt:
			frappe.throw(
				_("Insufficient budget availability to commit {0}.").format(amt),
				frappe.ValidationError,
				title=_("Insufficient funds"),
			)
	else:
		frappe.throw(
			_("Unknown validation stage: {0}.").format(stage),
			frappe.ValidationError,
			title=_("Invalid stage"),
		)
