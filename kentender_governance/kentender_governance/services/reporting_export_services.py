# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-038: run **KenTender Report Definition** and log **KenTender Report Execution Log**."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.desk.query_report import run as run_report
from frappe.utils import now_datetime

RD = "KenTender Report Definition"
REL = "KenTender Report Execution Log"


def execute_report_definition(
	report_definition_name: str,
	filters_json: str | None = None,
	*,
	executed_by_user: str | None = None,
) -> dict[str, Any]:
	"""Execute linked **Report** (if any), persist execution log, return row count."""
	if not frappe.db.exists(RD, report_definition_name):
		frappe.throw(_("KenTender Report Definition not found."), frappe.DoesNotExistError)

	rd = frappe.get_doc(RD, report_definition_name)
	if not rd.is_active:
		frappe.throw(_("Report Definition is inactive."), frappe.ValidationError)

	user = (executed_by_user or frappe.session.user or "Administrator").strip()
	if not frappe.db.exists("User", user):
		frappe.throw(_("Executed By user not found."), frappe.ValidationError)

	biz = f"RUN-{frappe.generate_hash(length=12)}"
	log = frappe.get_doc(
		{
			"doctype": REL,
			"business_id": biz,
			"report_definition": rd.name,
			"executed_by_user": user,
			"started_at": now_datetime(),
			"status": "Running",
		}
	)
	log.insert(ignore_permissions=True)

	row_count = 0
	summary = ""
	err_msg: str | None = None

	try:
		merged: dict[str, Any] = {}
		if rd.filter_defaults_json:
			merged.update(json.loads(rd.filter_defaults_json))
		if filters_json:
			merged.update(json.loads(filters_json))

		if rd.standard_report:
			result = run_report(rd.standard_report, filters=merged or None, user=user)
			rows = result.get("result") or []
			row_count = len(rows)
			summary = _("Executed standard report {0}").format(rd.standard_report)
		else:
			summary = _("No standard report linked; nothing executed.")
	except Exception as e:  # noqa: BLE001
		err_msg = str(e)
		summary = _("Execution failed.")

	log.reload()
	log.status = "Failed" if err_msg else "Success"
	log.completed_at = now_datetime()
	log.row_count = row_count
	log.summary_text = (summary or "")[:140]
	if err_msg:
		log.error_message = err_msg
	log.save(ignore_permissions=True)

	if err_msg:
		frappe.throw(_(err_msg), frappe.ValidationError)

	return {
		"report_definition": rd.name,
		"execution_log": log.name,
		"row_count": row_count,
		"summary": summary,
	}


@frappe.whitelist()
def execute_report_definition_api(
	report_definition_name: str | None = None,
	filters_json: str | None = None,
	executed_by_user: str | None = None,
):
	if not report_definition_name:
		frappe.throw(_("report_definition_name is required."), frappe.ValidationError)
	return execute_report_definition(report_definition_name, filters_json, executed_by_user=executed_by_user)
