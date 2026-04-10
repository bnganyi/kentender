# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Complaint Status Event — append-only audit trail (GOV-STORY-020)."""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.utils.display_label import code_title_label

C = "Complaint"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ComplaintStatusEvent(Document):
	def validate(self):
		if not self.is_new():
			if not frappe.flags.get("allow_complaint_status_event_mutate"):
				frappe.throw(
					_("Complaint Status Event is append-only; updates are not allowed."),
					frappe.ValidationError,
					title=_("Immutable record"),
				)

		if not self.complaint or not frappe.db.exists(C, self.complaint):
			frappe.throw(_("Complaint not found."), frappe.ValidationError)
		if self.actor_user and not frappe.db.exists("User", self.actor_user):
			frappe.throw(_("Actor user not found."), frappe.ValidationError)

		self._set_event_hash()
		self.display_label = code_title_label(_strip(self.event_type) or "—", _strip(self.complaint)[:12] or "—")

	def _set_event_hash(self) -> None:
		if _strip(self.event_hash):
			return
		payload = {
			"complaint": _strip(self.complaint),
			"type": _strip(self.event_type),
			"dt": str(self.event_datetime or now_datetime()),
			"summary": (_strip(self.summary) or "")[:2000],
		}
		self.event_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

	def on_trash(self):
		if not frappe.flags.get("allow_complaint_status_event_delete"):
			frappe.throw(_("Complaint Status Event cannot be deleted."), frappe.ValidationError)
