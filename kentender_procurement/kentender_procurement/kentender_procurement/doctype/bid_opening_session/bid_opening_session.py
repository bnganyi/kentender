# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Opening Session — scheduled opening ceremony header (PROC-STORY-048)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

TENDER = "Tender"
BOR = "Bid Opening Register"
EXCEPTION_RECORD = "Exception Record"

# Non-terminal workflow stages: at most one row per tender among these.
_TERMINAL_WORKFLOW = frozenset({"Completed", "Cancelled"})


def _strip(s: str | None) -> str:
	return (s or "").strip()


class BidOpeningSession(Document):
	def validate(self):
		self._normalize_text()
		self._set_display_label()
		self._validate_tender_and_entity()
		self._validate_one_active_session_per_tender()
		self._validate_exception_record()
		self._validate_opening_register()

	def _normalize_text(self) -> None:
		for fn in ("business_id", "meeting_reference", "opening_committee_assignment_ref", "latest_event_hash"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())
		if self.notes and isinstance(self.notes, str):
			self.notes = self.notes.strip()

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.business_id), _strip(self.tender) or "—")

	def _validate_tender_and_entity(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		if not frappe.db.exists(TENDER, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)
		ent = _strip(self.procuring_entity)
		if not ent:
			return
		t_ent = frappe.db.get_value(TENDER, tn, "procuring_entity")
		if t_ent and _strip(t_ent) != ent:
			frappe.throw(
				_("Procuring Entity must match the selected Tender."),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)

	def _validate_one_active_session_per_tender(self) -> None:
		"""Only one non-terminal opening session per tender (draft/scheduled/in-progress)."""
		tn = _strip(self.tender)
		if not tn:
			return
		ws = _strip(self.workflow_state)
		if ws in _TERMINAL_WORKFLOW:
			return
		filters = {"tender": tn, "workflow_state": ("not in", list(_TERMINAL_WORKFLOW))}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		other = frappe.db.exists("Bid Opening Session", filters)
		if other:
			frappe.throw(
				_("This tender already has an active Bid Opening Session ({0}). Complete or cancel it first.").format(
					frappe.bold(other)
				),
				frappe.ValidationError,
				title=_("Active session exists"),
			)

	def _validate_exception_record(self) -> None:
		er = _strip(self.exception_record)
		if not er:
			return
		if not frappe.db.exists(EXCEPTION_RECORD, er):
			frappe.throw(
				_("Exception Record {0} does not exist.").format(frappe.bold(er)),
				frappe.ValidationError,
				title=_("Invalid exception record"),
			)

	def _validate_opening_register(self) -> None:
		rn = _strip(self.opening_register)
		if not rn:
			return
		if not frappe.db.exists(BOR, rn):
			frappe.throw(
				_("Bid Opening Register {0} does not exist.").format(frappe.bold(rn)),
				frappe.ValidationError,
				title=_("Invalid register"),
			)
		row = frappe.db.get_value(BOR, rn, ["tender", "bid_opening_session"], as_dict=True)
		if not row:
			return
		tn = _strip(self.tender)
		if tn and _strip(row.get("tender")) != tn:
			frappe.throw(
				_("Opening Register must belong to the same tender as this session."),
				frappe.ValidationError,
				title=_("Register mismatch"),
			)
		sn = _strip(self.name)
		if sn and _strip(row.get("bid_opening_session")) != sn:
			frappe.throw(
				_("Opening Register must point to this Bid Opening Session."),
				frappe.ValidationError,
				title=_("Register mismatch"),
			)
