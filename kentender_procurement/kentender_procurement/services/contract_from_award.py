# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Create Procurement Contract from Award Decision (PROC-STORY-094)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.services.contract_readiness_gate import get_award_contract_readiness

AD = "Award Decision"
PC = "Procurement Contract"
TENDER = "Tender"
PCSE = "Procurement Contract Status Event"

SOURCE_MODULE = "kentender_procurement.contract_from_award"
EVT_CREATED = "procurement_contract.created_from_award"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _procuring_entity_for_tender(tender_id: str) -> str | None:
	if not tender_id:
		return None
	return frappe.db.get_value(TENDER, tender_id, "procuring_entity")


def create_contract_from_award(
	award_decision_id: str,
	*,
	business_id: str | None = None,
) -> dict[str, Any]:
	"""Draft **Procurement Contract** when the award passes the contract readiness gate."""
	an = _norm(award_decision_id)
	if not an or not frappe.db.exists(AD, an):
		frappe.throw(_("Award Decision not found."), frappe.ValidationError, title=_("Invalid award"))

	if frappe.db.exists(PC, {"award_decision": an}):
		frappe.throw(_("A procurement contract already exists for this award."), frappe.ValidationError)

	readiness = get_award_contract_readiness(an)
	if not readiness.get("ready"):
		frappe.throw(
			_("Award is not ready for contract creation: {0}").format(", ".join(readiness.get("blockers") or [])),
			frappe.ValidationError,
			title=_("Not ready"),
		)

	ad = frappe.get_doc(AD, an)
	tn = _norm(ad.tender)
	es = _norm(ad.evaluation_session)
	bid = _norm(ad.approved_bid_submission) or _norm(ad.recommended_bid_submission)
	sup = _norm(ad.approved_supplier) or _norm(ad.recommended_supplier)
	if not bid:
		frappe.throw(_("Award has no approved or recommended bid."), frappe.ValidationError)

	tender = frappe.get_doc(TENDER, tn)
	amt = ad.approved_amount if ad.approved_amount is not None else ad.recommended_amount
	cur = _norm(ad.currency) or _norm(tender.currency)

	doc = frappe.new_doc(PC)
	doc.business_id = _norm(business_id) or f"PC-{_norm(ad.business_id) or an[:12]}"
	doc.contract_title = _("Contract for {0}").format(_norm(tender.title) or tn)
	doc.award_decision = an
	doc.tender = tn
	doc.evaluation_session = es
	doc.procurement_plan_item = _norm(tender.procurement_plan_item) or None
	doc.approved_bid_submission = bid
	doc.supplier = sup or _norm(frappe.db.get_value("Bid Submission", bid, "supplier"))
	doc.procuring_entity = _norm(tender.procuring_entity)
	doc.requesting_department = tender.requesting_department
	doc.responsible_department = tender.responsible_department
	doc.procurement_officer_user = tender.procurement_officer
	doc.entity_strategic_plan = tender.entity_strategic_plan
	doc.program = tender.program
	doc.sub_program = tender.sub_program
	doc.output_indicator = tender.output_indicator
	doc.performance_target = tender.performance_target
	doc.national_objective = tender.national_objective
	doc.budget = tender.budget
	doc.budget_line = tender.budget_line
	doc.funding_source = tender.funding_source
	doc.contract_value = flt(amt) if amt is not None else 0.0
	doc.currency = cur
	doc.scope_summary = _norm(ad.award_summary_notes) or _("Derived from award decision.")
	doc.status = "Draft"
	doc.workflow_state = "Draft"
	doc.approval_status = "Draft"
	doc.commitment_status = "Uncommitted"
	doc.variation_count = 0

	with workflow_mutation_context():
		doc.insert(ignore_permissions=True)

	ts = now_datetime()
	frappe.get_doc(
		{
			"doctype": PCSE,
			"procurement_contract": doc.name,
			"event_type": "Created",
			"event_datetime": ts,
			"actor_user": _norm(frappe.session.user) or "Administrator",
			"summary": _("Contract created from award decision."),
		}
	).insert(ignore_permissions=True)

	pe = _procuring_entity_for_tender(tn)
	log_audit_event(
		event_type=EVT_CREATED,
		actor=_norm(frappe.session.user) or "Administrator",
		source_module=SOURCE_MODULE,
		target_doctype=PC,
		target_docname=doc.name,
		procuring_entity=pe,
		new_state=json.dumps({"award_decision": an, "tender": tn}),
		reason=_("Procurement contract created from award"),
		event_datetime=ts,
	)

	return {"name": doc.name, "business_id": doc.business_id}
