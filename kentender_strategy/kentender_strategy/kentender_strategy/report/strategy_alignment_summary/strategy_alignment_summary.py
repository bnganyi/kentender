# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""KPI-style counts for Strategy & Alignment workspace (Minimal Golden v2 / UX spec)."""

import frappe
from frappe import _


def execute(filters=None):
	columns = [_("Metric") + ":Data:280", _("Value") + ":Int:120"]
	data = [
		[_("National frameworks (Active)"), _count("National Framework", {"status": "Active"})],
		[_("National pillars (Active)"), _count("National Pillar", {"status": "Active"})],
		[_("Entity strategic plans (Active)"), _count("Entity Strategic Plan", {"status": "Active"})],
		[_("Strategic programs (Active)"), _count("Strategic Program", {"status": "Active"})],
		[_("Performance targets (Active)"), _count("Performance Target", {"status": "Active"})],
		[_("Purchase requisitions with target"), _pr_with_target()],
		[_("Procurement plan items with target"), _ppi_with_target()],
		[_("Budget lines with performance target"), _bl_with_target()],
	]
	return columns, data


def _count(doctype: str, filters: dict) -> int:
	return len(frappe.get_all(doctype, filters=filters, pluck="name", limit=2000))


def _pr_with_target() -> int:
	return frappe.db.sql(
		"""
		SELECT COUNT(*) FROM `tabPurchase Requisition`
		WHERE IFNULL(performance_target,'') != '' AND docstatus < 2
		"""
	)[0][0]


def _ppi_with_target() -> int:
	if not frappe.db.exists("DocType", "Procurement Plan Item"):
		return 0
	return frappe.db.sql(
		"""
		SELECT COUNT(*) FROM `tabProcurement Plan Item`
		WHERE IFNULL(performance_target,'') != '' AND docstatus < 2
		"""
	)[0][0]


def _bl_with_target() -> int:
	return frappe.db.sql(
		"""
		SELECT COUNT(*) FROM `tabBudget Line`
		WHERE IFNULL(performance_target,'') != '' AND docstatus < 2
		"""
	)[0][0]
