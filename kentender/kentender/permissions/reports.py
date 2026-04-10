# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Report access helpers (PERM-004).

Layer B: Frappe enforces Report **Has Role** and ref DocType ``report`` permission.
Use these helpers in tests and server code before building custom report menus.
"""

from __future__ import annotations

import frappe


def user_can_open_script_report(report_name: str, user: str | None = None) -> bool:
	"""Return True if *user* may open standard report *report_name* (Script/Query).

	Combines ``Report.is_permitted()`` with ``has_permission(ref_doctype, \"report\")``.
	"""
	u = (user or frappe.session.user or "").strip()
	if not u or u == "Guest":
		return False
	if not frappe.db.exists("Report", report_name):
		return False

	prev = frappe.session.user
	if u != prev:
		frappe.set_user(u)
	try:
		rdoc = frappe.get_doc("Report", report_name)
		if not rdoc.is_permitted():
			return False
		ref = (rdoc.ref_doctype or "").strip()
		if not ref:
			return True
		return bool(frappe.has_permission(ref, ptype="report", user=u))
	finally:
		if u != prev:
			frappe.set_user(prev)
