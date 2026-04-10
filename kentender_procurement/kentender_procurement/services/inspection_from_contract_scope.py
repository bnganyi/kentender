# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""PROC-STORY-111: create inspection from contract / milestone / deliverable scope."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.services.inspection_result_services import apply_template_fields_to_inspection_document

PC = "Procurement Contract"
PCM = "Procurement Contract Milestone"
PCD = "Procurement Contract Deliverable"
IR = "Inspection Record"
IMT = "Inspection Method Template"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _normalize_scope_type(scope_type: str) -> str:
	s = _norm(scope_type).lower().replace("-", "_")
	mapping = {
		"contract": "Contract Wide",
		"contract_wide": "Contract Wide",
		"wide": "Contract Wide",
		"milestone": "Milestone",
		"deliverable": "Deliverable",
		"milestone_and_deliverable": "Milestone and Deliverable",
		"milestone_deliverable": "Milestone and Deliverable",
	}
	if s in mapping:
		return mapping[s]
	# allow exact desk labels
	raw = _norm(scope_type)
	for v in ("Contract Wide", "Milestone", "Deliverable", "Milestone and Deliverable"):
		if raw.lower() == v.lower():
			return v
	frappe.throw(
		_("Unknown scope_type: {0}").format(scope_type),
		frappe.ValidationError,
		title=_("Invalid scope"),
	)


def _unique_business_id() -> str:
	for _ in range(40):
		bid = f"INS-{_norm(frappe.generate_hash(length=14))}"
		if not frappe.db.exists(IR, {"business_id": bid}):
			return bid
	frappe.throw(_("Could not allocate a unique inspection business_id."), frappe.ValidationError)


def create_inspection_for_contract_scope(
	contract_id: str,
	scope_ref: str | None,
	scope_type: str,
	*,
	inspection_method_template: str | None = None,
	business_id: str | None = None,
	inspection_title: str | None = None,
	inspection_description: str | None = None,
) -> dict[str, Any]:
	"""Create a **Draft** Inspection Record for a contract scope.

	Does **not** create or update acceptance records (PROC-STORY-113).

	:param contract_id: **Procurement Contract** name.
	:param scope_ref: Milestone or Deliverable docname when required by ``scope_type``; otherwise ``None``.
	:param scope_type: ``contract`` / ``Contract Wide``, ``milestone``, ``deliverable``, or ``milestone_and_deliverable``.
	:param inspection_method_template: Required — **Inspection Method Template** name; drives method type and ``requires_*`` flags.
	:param business_id: Optional explicit ``business_id`` (must be unique).
	:param inspection_title: Optional title; defaults from contract / milestone / deliverable.
	:param inspection_description: Optional description.
	:returns: ``{"name": ..., "business_id": ...}``
	"""
	cn = _norm(contract_id)
	if not cn or not frappe.db.exists(PC, cn):
		frappe.throw(_("Procurement Contract not found."), frappe.ValidationError)

	tpl = _norm(inspection_method_template)
	if not tpl or not frappe.db.exists(IMT, tpl):
		frappe.throw(_("Inspection Method Template is required and must exist."), frappe.ValidationError)

	pc = frappe.get_doc(PC, cn)
	st = _normalize_scope_type(scope_type)

	ref = _norm(scope_ref)
	milestone_name: str | None = None
	deliverable_name: str | None = None
	default_title = ""

	if st == "Contract Wide":
		if ref:
			frappe.throw(_("scope_ref must be empty for contract-wide scope."), frappe.ValidationError)
		default_title = _("Inspection — {0}").format(_norm(pc.contract_title) or cn)

	elif st == "Milestone":
		if not ref or not frappe.db.exists(PCM, ref):
			frappe.throw(_("Milestone scope_ref is required and must exist."), frappe.ValidationError)
		ms = frappe.db.get_value(PCM, ref, ("procurement_contract", "title"), as_dict=True)
		if not ms or _norm(ms.procurement_contract) != cn:
			frappe.throw(_("Milestone must belong to the selected contract."), frappe.ValidationError)
		milestone_name = ref
		default_title = _("Inspection — {0}").format(_norm(ms.title) or ref)

	elif st == "Deliverable":
		if not ref or not frappe.db.exists(PCD, ref):
			frappe.throw(_("Deliverable scope_ref is required and must exist."), frappe.ValidationError)
		dd = frappe.db.get_value(
			PCD,
			ref,
			("procurement_contract", "deliverable_title"),
			as_dict=True,
		)
		if not dd or _norm(dd.procurement_contract) != cn:
			frappe.throw(_("Deliverable must belong to the selected contract."), frappe.ValidationError)
		deliverable_name = ref
		default_title = _("Inspection — {0}").format(_norm(dd.deliverable_title) or ref)

	else:  # Milestone and Deliverable
		if not ref or not frappe.db.exists(PCD, ref):
			frappe.throw(
				_("Deliverable scope_ref is required for milestone-and-deliverable scope."),
				frappe.ValidationError,
			)
		dd = frappe.db.get_value(
			PCD,
			ref,
			("procurement_contract", "contract_milestone", "deliverable_title"),
			as_dict=True,
		)
		if not dd or _norm(dd.procurement_contract) != cn:
			frappe.throw(_("Deliverable must belong to the selected contract."), frappe.ValidationError)
		cm = _norm(dd.contract_milestone) if dd else ""
		if not cm or not frappe.db.exists(PCM, cm):
			frappe.throw(
				_("Deliverable must reference a Contract Milestone for this scope type."),
				frappe.ValidationError,
			)
		ms_pc = frappe.db.get_value(PCM, cm, "procurement_contract")
		if _norm(ms_pc) != cn:
			frappe.throw(_("Milestone must belong to the selected contract."), frappe.ValidationError)
		milestone_name = cm
		deliverable_name = ref
		default_title = _("Inspection — {0}").format(_norm(dd.deliverable_title) or ref)

	bid = _norm(business_id) or _unique_business_id()
	if frappe.db.exists(IR, {"business_id": bid}):
		frappe.throw(_("Inspection business_id already exists."), frappe.ValidationError)

	doc = frappe.new_doc(IR)
	doc.business_id = bid
	doc.contract = cn
	doc.inspection_scope_type = st
	doc.contract_milestone = milestone_name
	doc.contract_deliverable = deliverable_name
	doc.procuring_entity = _norm(pc.procuring_entity)
	doc.responsible_department = pc.responsible_department or None
	doc.contract_manager_user = pc.contract_manager_user or None
	doc.inspection_title = _norm(inspection_title) or default_title
	doc.inspection_description = _norm(inspection_description) or None
	doc.status = "Draft"
	doc.workflow_state = "Draft"
	doc.inspection_result = "Pending"
	doc.acceptance_status = "Not Applicable"

	apply_template_fields_to_inspection_document(doc, tpl)
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "business_id": doc.business_id}
