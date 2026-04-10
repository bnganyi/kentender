# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Create a **Tender** from an eligible **Procurement Plan Item** (PROC-STORY-031).

Does not publish the tender or create lots/criteria/documents.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, get_datetime, getdate, now_datetime, strip_html

from kentender_procurement.kentender_procurement.doctype.tender.tender import ORIGIN_FROM_PLAN_ITEM
from kentender_procurement.services.plan_item_tender_eligibility import get_plan_item_tender_eligibility

PPI_DOCTYPE = "Procurement Plan Item"
PTTL_DOCTYPE = "Plan to Tender Link"
TENDER_DOCTYPE = "Tender"

SHORT_DESCRIPTION_MAX = 240


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _duplicate_guard(ppi_doc: frappe.model.document.Document) -> None:
	st = _norm(getattr(ppi_doc, "tender_creation_status", None) or "")
	if st == "Created":
		frappe.throw(
			_("A tender has already been created for this plan item (tender creation status is Created)."),
			frappe.ValidationError,
			title=_("Already created"),
		)
	lt = _norm(getattr(ppi_doc, "latest_tender", None) or "")
	if lt:
		frappe.throw(
			_("This plan item already references a latest tender ({0}).").format(frappe.bold(lt)),
			frappe.ValidationError,
			title=_("Already linked"),
		)


def _default_ids(plan_item_id: str) -> tuple[str, str, str]:
	"""Return (tender_name, business_id, tender_number) derived from plan item name."""
	base = _norm(plan_item_id)
	td_name = f"TD-{base}"
	biz = f"TD-{base}"
	tnum = f"TN-{base}"
	if len(td_name) > 120:
		sfx = frappe.generate_hash(length=8)
		td_name = f"TD-{sfx}"
		biz = f"TD-{sfx}"
		tnum = f"TN-{sfx}"
	if frappe.db.exists(TENDER_DOCTYPE, td_name):
		sfx = frappe.generate_hash(length=6)
		td_name = f"TD-{base}-{sfx}"[:120]
		biz = td_name
		tnum = f"TN-{base}-{sfx}"[:120]
	return td_name, biz, tnum


def _schedule_from_ppi(ppi_doc: frappe.model.document.Document) -> dict[str, Any]:
	"""Map PPI planned dates to tender datetimes only if a non-decreasing chain can be formed."""
	pub_d = ppi_doc.get("planned_publication_date")
	sub_d = ppi_doc.get("planned_submission_deadline")
	awd_d = ppi_doc.get("planned_award_date")

	if not pub_d or not sub_d:
		return {}

	try:
		d_pub = getdate(pub_d)
		d_sub = getdate(sub_d)
	except Exception:
		return {}

	if d_sub < d_pub:
		return {}

	if d_pub == d_sub:
		pub_dt = datetime.combine(d_pub, time(9, 0))
		clar_dt = datetime.combine(d_pub, time(12, 0))
		sub_dt = datetime.combine(d_sub, time(17, 0))
		open_dt = datetime.combine(d_sub + timedelta(days=1), time(10, 0))
	else:
		d_clar = min(d_pub + timedelta(days=7), d_sub - timedelta(days=1))
		if d_clar <= d_pub:
			d_clar = d_pub + timedelta(days=1)
		if d_clar >= d_sub:
			return {}
		pub_dt = datetime.combine(d_pub, time(9, 0))
		clar_dt = datetime.combine(d_clar, time(17, 0))
		sub_dt = datetime.combine(d_sub, time(17, 0))
		d_open = d_sub + timedelta(days=1)
		if awd_d:
			try:
				d_awd = getdate(awd_d)
				if d_awd > d_sub:
					d_open = d_awd
			except Exception:
				pass
		open_dt = datetime.combine(d_open, time(10, 0))

	chain = (pub_dt, clar_dt, sub_dt, open_dt)
	for a, b in zip(chain, chain[1:]):
		if get_datetime(a) is None or get_datetime(b) is None or b < a:
			return {}

	return {
		"publication_datetime": pub_dt.strftime("%Y-%m-%d %H:%M:%S"),
		"clarification_deadline": clar_dt.strftime("%Y-%m-%d %H:%M:%S"),
		"submission_deadline": sub_dt.strftime("%Y-%m-%d %H:%M:%S"),
		"opening_datetime": open_dt.strftime("%Y-%m-%d %H:%M:%S"),
	}


def _short_from_description(html: str | None) -> str | None:
	if not html:
		return None
	plain = strip_html(html) or ""
	plain = plain.strip()
	if not plain:
		return None
	if len(plain) > SHORT_DESCRIPTION_MAX:
		return plain[: SHORT_DESCRIPTION_MAX - 1].rstrip() + "…"
	return plain


def create_tender_from_plan_item(
	plan_item_id: str,
	*,
	tender_name: str | None = None,
	business_id: str | None = None,
	tender_number: str | None = None,
	link_type: str = "Direct",
	ignore_permissions: bool = True,
) -> dict[str, Any]:
	"""Create a draft Tender from an eligible Procurement Plan Item, then an Active Plan to Tender Link.

	:param plan_item_id: Procurement Plan Item name.
	:returns: ``tender``, ``plan_to_tender_link``, ``procurement_plan_item`` names.
	"""
	pi_name = _norm(plan_item_id)
	if not pi_name:
		frappe.throw(_("Procurement Plan Item is required."), frappe.ValidationError, title=_("Missing"))

	info = get_plan_item_tender_eligibility(pi_name)
	if not info.get("eligible"):
		reasons = info.get("reasons") or []
		detail = "; ".join(reasons) if reasons else _("Plan item is not eligible for tender creation.")
		frappe.throw(
			_("Cannot create tender from plan item: {0}").format(detail),
			frappe.ValidationError,
			title=_("Not eligible"),
		)

	ppi = frappe.get_doc(PPI_DOCTYPE, pi_name)
	_duplicate_guard(ppi)

	amt = flt(ppi.estimated_amount)
	if amt <= 0:
		frappe.throw(
			_("Estimated amount on the plan item must be greater than zero to link a tender."),
			frappe.ValidationError,
			title=_("Invalid amount"),
		)

	plan_name = _norm(ppi.procurement_plan)
	if not plan_name:
		frappe.throw(_("Procurement Plan Item has no procurement plan."), frappe.ValidationError)

	def_name, def_biz, def_tnum = _default_ids(pi_name)
	tn = _norm(tender_name) or def_name
	bid = _norm(business_id) or def_biz
	tnum = _norm(tender_number) or def_tnum

	if frappe.db.exists(TENDER_DOCTYPE, tn):
		frappe.throw(
			_("Tender {0} already exists.").format(frappe.bold(tn)),
			frappe.ValidationError,
			title=_("Duplicate name"),
		)

	row: dict[str, Any] = {
		"doctype": TENDER_DOCTYPE,
		"name": tn,
		"business_id": bid,
		"title": _norm(ppi.title) or _("Tender"),
		"tender_number": tnum,
		"workflow_state": "Draft",
		"status": "Draft",
		"approval_status": "Draft",
		"origin_type": ORIGIN_FROM_PLAN_ITEM,
		"procurement_plan": plan_name,
		"procurement_plan_item": pi_name,
		"procuring_entity": ppi.procuring_entity,
		"requesting_department": ppi.requesting_department,
		"responsible_department": ppi.responsible_department,
		"procurement_category": ppi.procurement_category,
		"procurement_method": ppi.procurement_method,
		"currency": ppi.currency,
		"estimated_amount": amt,
		"entity_strategic_plan": ppi.entity_strategic_plan,
		"program": ppi.program,
		"sub_program": ppi.sub_program,
		"output_indicator": ppi.output_indicator,
		"performance_target": ppi.performance_target,
		"national_objective": ppi.national_objective,
		"budget": ppi.budget,
		"budget_line": ppi.budget_line,
		"funding_source": ppi.funding_source,
	}
	if ppi.description:
		row["description"] = ppi.description
	sd = _short_from_description(ppi.description)
	if sd:
		row["short_description"] = sd

	row.update(_schedule_from_ppi(ppi))

	tender_doc = frappe.get_doc(row)
	tender_doc.insert(ignore_permissions=ignore_permissions)

	pttl = frappe.get_doc(
		{
			"doctype": PTTL_DOCTYPE,
			"procurement_plan_item": pi_name,
			"tender": tender_doc.name,
			"link_type": link_type or "Direct",
			"linked_amount": amt,
			"linked_on": now_datetime(),
			"status": "Active",
		}
	)
	pttl.insert(ignore_permissions=ignore_permissions)

	tender_doc.reload()
	tender_doc.plan_to_tender_link = pttl.name
	tender_doc.save(ignore_permissions=ignore_permissions)

	ppi.reload()
	ppi.latest_tender = tender_doc.name
	ppi.tender_creation_status = "Created"
	ppi.save(ignore_permissions=ignore_permissions)

	return {
		"tender": tender_doc.name,
		"plan_to_tender_link": pttl.name,
		"procurement_plan_item": pi_name,
	}
