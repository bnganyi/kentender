# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Deliberation Status Event — append-only audit trail (GOV-STORY-008)."""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.utils.display_label import code_title_label

DS = "Deliberation Session"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class DeliberationStatusEvent(Document):
	def validate(self):
		if not self.is_new():
			if not frappe.flags.get("allow_deliberation_status_event_mutate"):
				frappe.throw(
					_("Deliberation Status Event is append-only; updates are not allowed."),
					frappe.ValidationError,
					title=_("Immutable record"),
				)

		if not self.deliberation_session or not frappe.db.exists(DS, self.deliberation_session):
			frappe.throw(_("Deliberation Session not found."), frappe.ValidationError)

		if self.actor_user and not frappe.db.exists("User", self.actor_user):
			frappe.throw(_("Actor user not found."), frappe.ValidationError)

		self._set_event_hash()
		self.display_label = code_title_label(
			_strip(self.event_type) or "—",
			_strip(self.deliberation_session)[:12] or "—",
		)

	def _set_event_hash(self) -> None:
		if _strip(self.event_hash):
			return
		payload = {
			"session": _strip(self.deliberation_session),
			"type": _strip(self.event_type),
			"dt": str(self.event_datetime or now_datetime()),
			"summary": (_strip(self.summary) or "")[:2000],
		}
		self.event_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

	def on_trash(self):
		if not frappe.flags.get("allow_deliberation_status_event_delete"):
			frappe.throw(_("Deliberation Status Event cannot be deleted."), frappe.ValidationError)
