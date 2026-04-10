# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Inspection Status Event — append-only lifecycle log (PROC-STORY-110)."""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.utils.display_label import code_title_label

AR = "Acceptance Record"
IR = "Inspection Record"
NC = "Non Conformance Record"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class InspectionStatusEvent(Document):
	def validate(self):
		if not self.is_new():
			if not frappe.flags.get("allow_inspection_status_event_mutate"):
				frappe.throw(
					_("Inspection Status Event is append-only; updates are not allowed."),
					frappe.ValidationError,
					title=_("Immutable record"),
				)
		self._validate_related()
		self._set_event_hash()
		self.display_label = code_title_label(_strip(self.event_type) or "—", _strip(self.inspection_record)[:12] or "—")

	def _validate_related(self) -> None:
		ir = _strip(self.inspection_record)
		if not ir or not frappe.db.exists(IR, ir):
			frappe.throw(_("Inspection Record not found."), frappe.ValidationError)

		ra = _strip(self.related_acceptance_record)
		if ra:
			if not frappe.db.exists(AR, ra):
				frappe.throw(_("Related Acceptance Record not found."), frappe.ValidationError)
			ar_ir = frappe.db.get_value(AR, ra, "inspection_record")
			if ar_ir != ir:
				frappe.throw(_("Related Acceptance Record must belong to this inspection."), frappe.ValidationError)

		rn = _strip(self.related_non_conformance_record)
		if rn:
			if not frappe.db.exists(NC, rn):
				frappe.throw(_("Related Non Conformance Record not found."), frappe.ValidationError)
			nc_ir = frappe.db.get_value(NC, rn, "inspection_record")
			if nc_ir != ir:
				frappe.throw(_("Related Non Conformance Record must belong to this inspection."), frappe.ValidationError)

	def _set_event_hash(self) -> None:
		if _strip(self.event_hash):
			return
		payload = {
			"inspection": _strip(self.inspection_record),
			"type": _strip(self.event_type),
			"dt": str(self.event_datetime or now_datetime()),
			"summary": (_strip(self.summary) or "")[:2000],
		}
		self.event_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

	def on_trash(self):
		if not frappe.flags.get("allow_inspection_status_event_delete"):
			frappe.throw(_("Inspection Status Event cannot be deleted."), frappe.ValidationError)
