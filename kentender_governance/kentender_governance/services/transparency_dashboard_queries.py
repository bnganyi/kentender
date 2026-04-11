# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-039: lightweight desk metrics for transparency + audit surfaces."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_to_date, now_datetime

PDR = "KenTender Public Disclosure Record"
DS = "KenTender Disclosure Dataset"
RD = "KenTender Report Definition"
REL = "KenTender Report Execution Log"
AQ = "KenTender Audit Query"


def get_transparency_dashboard_stats() -> dict[str, Any]:
	"""Aggregate counts for dashboards / number cards (no heavy joins)."""
	out: dict[str, Any] = {}

	if frappe.db.exists("DocType", PDR):
		out["public_disclosure_published"] = frappe.db.count(PDR, {"status": "Published"})
		out["public_disclosure_draft"] = frappe.db.count(PDR, {"status": "Draft"})

	if frappe.db.exists("DocType", DS):
		out["disclosure_dataset_active"] = frappe.db.count(DS, {"status": "Active"})

	since = add_to_date(now_datetime(), days=-7, as_datetime=True)
	if frappe.db.exists("DocType", REL):
		out["report_executions_7d"] = len(
			frappe.get_all(REL, filters=[["creation", ">=", since]], pluck="name", limit=2000) or []
		)

	if frappe.db.exists("DocType", RD):
		out["report_definitions_active"] = frappe.db.count(RD, {"is_active": 1})

	if frappe.db.exists("DocType", AQ):
		out["open_audit_queries"] = len(
			frappe.get_all(
				AQ,
				filters={"status": ["in", ["Draft", "Open", "Pending Response"]]},
				pluck="name",
				limit=5000,
			)
			or []
		)

	return out


@frappe.whitelist()
def get_transparency_dashboard_stats_api():
	return get_transparency_dashboard_stats()
