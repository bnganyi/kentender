# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget Ledger Entry — append-only authoritative procurement control movements (BUD-007).

**Entry types** (amount > 0, direction In unless reversing):

- **Reserve**: increases reserved.
- **Release Reservation**: decreases reserved, increases released (capacity returned).
- **Commit From Reserved**: decreases reserved, increases committed (no released change).
- **Commit From Available**: increases committed only.
- **Release Commitment**: decreases committed, increases released.

**Entry direction**: **In** applies the movement; **Out** negates the same bucket deltas (reversal rows).

Posting services (BUD-008+) create rows; do not add business posting logic here beyond validation and immutability.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime

from kentender.utils.display_label import code_title_label


def _compute_entry_hash(payload: dict[str, Any], salt: str) -> str:
	canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
	raw = f"{canonical}|{salt}".encode("utf-8")
	return hashlib.sha256(raw).hexdigest()


class BudgetLedgerEntry(Document):
	def validate(self):
		self.display_label = code_title_label(
			(self.name or "").strip(),
			(self.entry_type or "").strip(),
		)
		if not self.is_new():
			frappe.throw(
				_("Budget Ledger Entry records cannot be modified."),
				frappe.ValidationError,
				title=_("Append-only record"),
			)
		self._validate_amount_positive()
		self._validate_source_context()
		self._validate_header_alignment()
		self._validate_reversal_link()

	def before_insert(self):
		if not (self.created_by_user or "").strip():
			self.created_by_user = frappe.session.user
		self._set_event_hash()

	def on_trash(self):
		frappe.throw(
			_("Budget Ledger Entry records cannot be deleted."),
			frappe.ValidationError,
			title=_("Append-only record"),
		)

	def _validate_amount_positive(self):
		if flt(self.amount) <= 0:
			frappe.throw(
				_("Amount must be greater than zero."),
				frappe.ValidationError,
				title=_("Invalid amount"),
			)

	def _validate_source_context(self):
		for label, val in (
			(_("Source DocType"), self.source_doctype),
			(_("Source Doc Name"), self.source_docname),
			(_("Source Action"), self.source_action),
		):
			if not (val or "").strip():
				frappe.throw(
					_("{0} is required.").format(label),
					frappe.ValidationError,
					title=_("Missing source context"),
				)

	def _validate_header_alignment(self):
		line = (self.budget_line or "").strip()
		if not line or not frappe.db.exists("Budget Line", line):
			return
		row = frappe.db.get_value(
			"Budget Line",
			line,
			["budget", "procuring_entity", "fiscal_year", "currency"],
			as_dict=True,
		)
		if not row:
			return
		if (self.budget or "").strip() and row.budget and self.budget != row.budget:
			frappe.throw(
				_("Budget must match the selected Budget Line."),
				frappe.ValidationError,
				title=_("Header mismatch"),
			)
		if (self.procuring_entity or "").strip() and row.procuring_entity and self.procuring_entity != row.procuring_entity:
			frappe.throw(
				_("Procuring Entity must match the selected Budget Line."),
				frappe.ValidationError,
				title=_("Header mismatch"),
			)
		if (self.fiscal_year or "").strip() and row.fiscal_year and self.fiscal_year != row.fiscal_year:
			frappe.throw(
				_("Fiscal Year must match the selected Budget Line."),
				frappe.ValidationError,
				title=_("Header mismatch"),
			)
		if (self.currency or "").strip() and row.currency and self.currency != row.currency:
			frappe.throw(
				_("Currency must match the selected Budget Line."),
				frappe.ValidationError,
				title=_("Header mismatch"),
			)

	def _validate_reversal_link(self):
		rev = (self.reversal_of_entry or "").strip()
		if not rev:
			return
		if not frappe.db.exists("Budget Ledger Entry", rev):
			frappe.throw(
				_("Reversal Of Entry {0} does not exist.").format(frappe.bold(rev)),
				frappe.ValidationError,
				title=_("Invalid reversal"),
			)

	def _set_event_hash(self):
		site = frappe.get_site_config()
		salt = str(site.get("budget_ledger_event_salt") or site.get("audit_event_salt") or "")
		payload = {
			"amount": str(flt(self.amount)),
			"budget": self.budget or "",
			"budget_line": self.budget_line or "",
			"currency": self.currency or "",
			"entry_direction": self.entry_direction or "",
			"entry_type": self.entry_type or "",
			"fiscal_year": self.fiscal_year or "",
			"posting_datetime": _dt_iso(self.posting_datetime),
			"procuring_entity": self.procuring_entity or "",
			"reversal_of_entry": self.reversal_of_entry or "",
			"source_action": self.source_action or "",
			"source_docname": self.source_docname or "",
			"source_doctype": self.source_doctype or "",
			"status": self.status or "",
		}
		self.event_hash = _compute_entry_hash(payload, salt)


def _dt_iso(value) -> str:
	if value is None:
		return ""
	if hasattr(value, "isoformat"):
		return value.isoformat()
	return str(get_datetime(value) or value)
