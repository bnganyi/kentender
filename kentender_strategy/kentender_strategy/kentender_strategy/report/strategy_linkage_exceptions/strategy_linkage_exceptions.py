# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Exception list: operational records missing strategy linkage (Strategy UX exception panels)."""

import frappe
from frappe import _


def execute(filters=None):
	columns = [
		_("Record Type") + ":Data:160",
		_("Name") + ":Data:180",
		_("Issue") + ":Data:220",
	]
	data = []
	for row in _pr_rows():
		data.append(["Purchase Requisition", row[0], _("Missing performance target")])
	for row in _ppi_rows():
		data.append(["Procurement Plan Item", row[0], _("Missing performance target")])
	for row in _bl_rows():
		data.append(["Budget Line", row[0], _("Missing performance target")])
	return columns, data


def _pr_rows():
	return frappe.db.sql(
		"""
		SELECT name FROM `tabPurchase Requisition`
		WHERE IFNULL(performance_target,'') = '' AND docstatus < 2
		ORDER BY modified DESC
		LIMIT 200
		"""
	)


def _ppi_rows():
	if not frappe.db.exists("DocType", "Procurement Plan Item"):
		return []
	return frappe.db.sql(
		"""
		SELECT name FROM `tabProcurement Plan Item`
		WHERE IFNULL(performance_target,'') = '' AND docstatus < 2
		ORDER BY modified DESC
		LIMIT 200
		"""
	)


def _bl_rows():
	return frappe.db.sql(
		"""
		SELECT name FROM `tabBudget Line`
		WHERE IFNULL(performance_target,'') = '' AND docstatus < 2
		AND status = 'Active'
		ORDER BY modified DESC
		LIMIT 200
		"""
	)
