# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-005: Store Ledger Entry — append-only stock postings (no running balance stored)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from kentender.utils.display_label import code_title_label

S = "Store"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _payload_hash(payload: dict[str, Any]) -> str:
	return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class StoreLedgerEntry(Document):
	def validate(self):
		if not self.is_new():
			if not frappe.flags.get("allow_store_ledger_mutate"):
				frappe.throw(
					_("Store Ledger Entry is append-only; updates are not allowed."),
					frappe.ValidationError,
					title=_("Immutable record"),
				)

		if not frappe.db.exists(S, self.store):
			frappe.throw(_("Store not found."), frappe.ValidationError)
		if flt(self.quantity) <= 0:
			frappe.throw(_("Quantity must be greater than zero."), frappe.ValidationError)

		sdt = _strip(self.source_doctype)
		sdn = _strip(self.source_docname)
		if not sdt or not frappe.db.exists("DocType", sdt):
			frappe.throw(_("Source DocType is not valid."), frappe.ValidationError)
		if not sdn or not frappe.db.exists(sdt, sdn):
			frappe.throw(_("Source document does not exist."), frappe.ValidationError)

		self.display_label = code_title_label(_strip(self.item_reference), _strip(self.entry_type) or "—")
		self._set_entry_hash()

	def on_trash(self):
		if not frappe.flags.get("allow_store_ledger_delete"):
			frappe.throw(_("Store Ledger Entry cannot be deleted."), frappe.ValidationError)

	def _set_entry_hash(self) -> None:
		if _strip(self.entry_hash):
			return
		payload = {
			"store": _strip(self.store),
			"item_reference": _strip(self.item_reference),
			"entry_type": _strip(self.entry_type),
			"entry_direction": _strip(self.entry_direction),
			"quantity": str(flt(self.quantity)),
			"unit_of_measure": _strip(self.unit_of_measure),
			"posting_datetime": str(self.posting_datetime or now_datetime()),
			"source_doctype": _strip(self.source_doctype),
			"source_docname": _strip(self.source_docname),
		}
		self.entry_hash = _payload_hash(payload)
