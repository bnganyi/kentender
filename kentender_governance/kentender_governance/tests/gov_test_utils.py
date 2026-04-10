# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Shared helpers for kentender_governance DocType tests (GOV-STORY-002+)."""

import frappe
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import _make_entity

DS = "Deliberation Session"


def make_procuring_entity(entity_code: str):
	return _make_entity(entity_code).insert()


def make_deliberation_session(*, business_id: str, procuring_entity: str):
	return (
		frappe.get_doc(
			{
				"doctype": DS,
				"business_id": business_id,
				"session_title": "Test session",
				"session_type": "Board",
				"status": "Draft",
				"procuring_entity": procuring_entity,
				"scheduled_datetime": now_datetime(),
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def cleanup_gov_chain(prefix: str):
	"""Delete deliberation docs for sessions whose business_id starts with prefix, then PE."""
	frappe.flags.allow_deliberation_status_event_delete = True
	try:
		ss = frappe.get_all(DS, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []
		for s in ss:
			for dt, field in (
				("Deliberation Status Event", "deliberation_session"),
				("Follow Up Action", "deliberation_session"),
				("Deliberation Minute", "deliberation_session"),
				("Recommendation Record", "deliberation_session"),
				("Resolution Record", "deliberation_session"),
				("Deliberation Attendance", "deliberation_session"),
				("Deliberation Agenda Item", "deliberation_session"),
			):
				for name in frappe.get_all(dt, filters={field: s}, pluck="name") or []:
					frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
			frappe.delete_doc(DS, s, force=True, ignore_permissions=True)
		frappe.db.delete("Procuring Entity", {"entity_code": f"{prefix}_PE"})
	finally:
		frappe.flags.allow_deliberation_status_event_delete = False


def cleanup_complaint_chain(prefix: str):
	"""Delete complaint-related docs whose Complaint.business_id starts with prefix."""
	CMP = "Complaint"
	frappe.flags.allow_complaint_status_event_delete = True
	try:
		cids = frappe.get_all(CMP, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []
		for cid in cids:
			for dt, field in (
				("Complaint Status Event", "complaint"),
				("Complaint Action", "complaint"),
				("Appeal Record", "complaint"),
				("Complaint Decision", "complaint"),
				("Complaint Review Record", "complaint"),
				("Complaint Review Panel Assignment", "complaint"),
				("Complaint Evidence", "complaint"),
				("Complaint Party", "complaint"),
			):
				for name in frappe.get_all(dt, filters={field: cid}, pluck="name") or []:
					frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
			frappe.delete_doc(CMP, cid, force=True, ignore_permissions=True)
	finally:
		frappe.flags.allow_complaint_status_event_delete = False
