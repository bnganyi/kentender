# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Award notifications and standstill lifecycle (PROC-STORY-083)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime

from kentender.services.audit_event_service import log_audit_event

AD = "Award Decision"
AN = "Award Notification"
SSP = "Standstill Period"

SOURCE_MODULE = "kentender_procurement.award_notification_standstill_services"
EVT_NOTIFY = "award.notifications.generated"
EVT_STANDSTILL = "award.standstill.initialized"
EVT_RELEASE = "award.standstill.released_for_contract"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _procuring_entity_for_award(doc) -> str | None:
	tn = _norm(doc.tender)
	if not tn:
		return None
	return frappe.db.get_value("Tender", tn, "procuring_entity")


def send_award_notifications(award_decision_id: str) -> dict[str, Any]:
	"""Create **Award Notification** rows from outcome lines (delivery is abstract / desk workflow)."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	doc = frappe.get_doc(AD, an)
	tender = _norm(doc.tender)
	if not tender:
		frappe.throw(_("Award Decision has no tender."), frappe.ValidationError)

	created: list[str] = []
	for i, row in enumerate(doc.outcome_lines or [], start=1):
		bid = _norm(row.bid_submission)
		sup = _norm(row.supplier)
		if not bid or not sup:
			continue
		ntype = "Successful" if _norm(row.outcome_type) == "Awarded" else "Unsuccessful"
		biz = f"{_norm(doc.business_id)}-N-{i}"
		while frappe.db.exists(AN, {"business_id": biz}):
			i += 1
			biz = f"{_norm(doc.business_id)}-N-{i}"
		n = frappe.get_doc(
			{
				"doctype": AN,
				"business_id": biz,
				"award_decision": an,
				"tender": tender,
				"supplier": sup,
				"bid_submission": bid,
				"notification_type": ntype,
				"status": "Draft",
				"subject": _("Award outcome notification"),
				"message_body": _("Notification record created; channel delivery is handled outside this service."),
			}
		)
		n.insert(ignore_permissions=True)
		created.append(n.name)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_NOTIFY,
		actor=_norm(frappe.session.user) or "Administrator",
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"notifications": len(created)}),
		reason=_("Award notifications generated"),
		event_datetime=now_datetime(),
	)

	return {"award_decision": an, "notifications": created}


def initialize_standstill_period(
	award_decision_id: str,
	*,
	days: int = 10,
) -> dict[str, Any]:
	"""Create a **Standstill Period** when ``standstill_required`` is set."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	doc = frappe.get_doc(AD, an)
	if not int(doc.standstill_required or 0):
		return {"skipped": True, "reason": "standstill_not_required"}
	if _norm(doc.standstill_period):
		frappe.throw(_("Standstill period is already linked."), frappe.ValidationError, title=_("Already initialized"))

	start = now_datetime()
	end = add_to_date(start, days=days)
	sp = frappe.new_doc(SSP)
	sp.award_decision = an
	sp.start_datetime = start
	sp.end_datetime = end
	sp.status = "Active"
	sp.insert(ignore_permissions=True)

	doc.standstill_period = sp.name
	doc.ready_for_contract_creation = 0
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_STANDSTILL,
		actor=_norm(frappe.session.user) or "Administrator",
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"standstill_period": sp.name}),
		reason=_("Standstill initialized"),
		event_datetime=now_datetime(),
	)

	return {"name": sp.name, "award_decision": an}


def release_award_for_contract(award_decision_id: str) -> dict[str, Any]:
	"""Release standstill (if any) and mark the award ready for contract creation."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	doc = frappe.get_doc(AD, an)
	spn = _norm(doc.standstill_period)

	if int(doc.standstill_required or 0):
		if not spn:
			frappe.throw(_("Standstill period is not initialized."), frappe.ValidationError, title=_("Missing standstill"))
		sp = frappe.get_doc(SSP, spn)
		if int(sp.complaint_hold_flag or 0):
			frappe.throw(
				_("Complaint hold is active; cannot release for contract."),
				frappe.ValidationError,
				title=_("Complaint hold"),
			)
		sp.status = "Released"
		sp.released_for_contract_on = now_datetime()
		sp.save(ignore_permissions=True)

	doc.ready_for_contract_creation = 1
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_award(doc)
	log_audit_event(
		event_type=EVT_RELEASE,
		actor=_norm(frappe.session.user) or "Administrator",
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=an,
		procuring_entity=pe,
		new_state=json.dumps({"ready_for_contract_creation": 1}),
		reason=_("Award released for contract creation"),
		event_datetime=now_datetime(),
	)

	return {"name": an, "ready_for_contract_creation": 1}
