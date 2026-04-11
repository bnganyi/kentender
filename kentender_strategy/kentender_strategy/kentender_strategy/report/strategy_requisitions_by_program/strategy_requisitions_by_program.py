# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Alignment panel: requisitions aggregated by strategic program."""

import frappe
from frappe import _


def execute(filters=None):
	columns = [
		_("Strategic Program") + ":Link/Strategic Program:220",
		_("Requisitions") + ":Int:100",
		_("Total requested amount") + ":Currency:160",
	]
	rows = frappe.db.sql(
		"""
		SELECT program, COUNT(*) AS cnt, COALESCE(SUM(requested_amount), 0) AS amt
		FROM `tabPurchase Requisition`
		WHERE IFNULL(program,'') != '' AND docstatus < 2
		GROUP BY program
		ORDER BY cnt DESC
		LIMIT 200
		"""
	)
	data = [[r[0], r[1], r[2]] for r in rows]
	return columns, data
