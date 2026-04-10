# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Contract Status Event — append-only lifecycle log (PROC-STORY-093)."""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.utils.display_label import code_title_label

PC = "Procurement Contract"
PCV = "Procurement Contract Variation"
PCM = "Procurement Contract Milestone"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ProcurementContractStatusEvent(Document):
	def validate(self):
		if not self.is_new():
			if not frappe.flags.get("allow_contract_status_event_mutate"):
				frappe.throw(
					_("Contract Status Event is append-only; updates are not allowed."),
					frappe.ValidationError,
					title=_("Immutable record"),
				)
		self._validate_contract_links()
		self._set_event_hash()
		self._set_display_label()

	def _validate_contract_links(self) -> None:
		cn = _strip(self.procurement_contract)
		if not cn or not frappe.db.exists(PC, cn):
			frappe.throw(_("Procurement Contract not found."), frappe.ValidationError)
		rv = _strip(self.related_variation)
		if rv and not frappe.db.exists(PCV, rv):
			frappe.throw(_("Related Variation not found."), frappe.ValidationError)
		if rv and _strip(frappe.db.get_value(PCV, rv, "procurement_contract")) != cn:
			frappe.throw(_("Related Variation must belong to this contract."), frappe.ValidationError)
		rm = _strip(self.related_milestone)
		if rm and not frappe.db.exists(PCM, rm):
			frappe.throw(_("Related Milestone not found."), frappe.ValidationError)
		if rm and _strip(frappe.db.get_value(PCM, rm, "procurement_contract")) != cn:
			frappe.throw(_("Related Milestone must belong to this contract."), frappe.ValidationError)

	def _set_event_hash(self) -> None:
		if _strip(self.event_hash):
			return
		payload = {
			"contract": _strip(self.procurement_contract),
			"type": _strip(self.event_type),
			"dt": str(self.event_datetime or now_datetime()),
			"summary": (_strip(self.summary) or "")[:2000],
		}
		self.event_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.event_type) or "—", _strip(self.status_result) or "—")

	def on_trash(self):
		if not frappe.flags.get("allow_contract_status_event_delete"):
			frappe.throw(_("Contract Status Event cannot be deleted."), frappe.ValidationError)
