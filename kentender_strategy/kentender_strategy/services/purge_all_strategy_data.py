# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Remove all KenTender strategy-layer documents and clear strategy links on PR / Budget Line.

Use on dev/UAT only. Does not delete procuring entities, budgets, or requisitions — only unlinks strategy fields.
"""

from __future__ import annotations

from typing import Any

import frappe

PR = "Purchase Requisition"
BL = "Budget Line"

_STRATEGY_FIELDS_PR = (
	"entity_strategic_plan",
	"program",
	"sub_program",
	"output_indicator",
	"performance_target",
	"national_objective",
)

_STRATEGY_FIELDS_BL = (
	"entity_strategic_plan",
	"program",
	"sub_program",
	"output_indicator",
	"performance_target",
)

_DELETE_ORDER = (
	"Strategic Revision Record",
	"Performance Target",
	"Output Indicator",
	"Strategic Sub Program",
	"Strategic Program",
	"Entity Strategic Plan",
	"National Objective",
	"National Pillar",
	"National Framework",
)


def _clear_strategy_links_on_purchase_requisitions() -> None:
	set_clause = ", ".join(f"`{f}`=NULL" for f in _STRATEGY_FIELDS_PR)
	frappe.db.sql(f"UPDATE `tab{PR}` SET {set_clause}")


def _clear_strategy_links_on_budget_lines() -> None:
	set_clause = ", ".join(f"`{f}`=NULL" for f in _STRATEGY_FIELDS_BL)
	frappe.db.sql(f"UPDATE `tab{BL}` SET {set_clause}")


def _clear_entity_strategic_plan_self_refs() -> None:
	"""Break supersedes links so ESP rows can be deleted individually."""
	if not frappe.db.has_table("tabEntity Strategic Plan"):
		return
	frappe.db.sql(
		"""
		UPDATE `tabEntity Strategic Plan`
		SET supersedes_plan=NULL, superseded_by_plan=NULL
		"""
	)


def _delete_all_in_doctype(doctype: str) -> int:
	names = frappe.get_all(doctype, pluck="name") or []
	count = 0
	for name in names:
		try:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			count += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"purge_strategy:{doctype}:{name}")
			raise
	return count


def purge_all_strategy_data(*, commit: bool = True) -> dict[str, Any]:
	"""Delete every document in kentender_strategy core doctypes; clear PR/BL strategy links first.

	:param commit: When False (e.g. unit tests), caller controls transaction boundaries.
	"""
	frappe.only_for("System Manager")

	_clear_strategy_links_on_purchase_requisitions()
	_clear_strategy_links_on_budget_lines()
	summary: dict[str, Any] = {
		"purchase_requisition_strategy_links_cleared": True,
		"budget_line_strategy_links_cleared": True,
		"deleted_by_doctype": {},
	}

	_clear_entity_strategic_plan_self_refs()

	for dt in _DELETE_ORDER:
		if not frappe.db.exists("DocType", dt):
			continue
		summary["deleted_by_doctype"][dt] = _delete_all_in_doctype(dt)

	if commit:
		frappe.db.commit()
	return summary


def purge_all_strategy_data_console() -> None:
	import json

	out = purge_all_strategy_data(commit=True)
	print(json.dumps(out, indent=2, default=str))
