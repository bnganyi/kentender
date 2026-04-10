# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import hashlib
import os

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_files_path

from kentender.utils.display_label import code_title_label

C = "Complaint"
CP = "Complaint Party"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ComplaintEvidence(Document):
	def validate(self):
		if not self.complaint or not frappe.db.exists(C, self.complaint):
			frappe.throw(_("Complaint not found."), frappe.ValidationError)
		if self.submitted_by_user and not frappe.db.exists("User", self.submitted_by_user):
			frappe.throw(_("Submitted By user not found."), frappe.ValidationError)
		if self.submitted_by_party:
			if not frappe.db.exists(CP, self.submitted_by_party):
				frappe.throw(_("Complaint Party not found."), frappe.ValidationError)
			pp = frappe.db.get_value(CP, self.submitted_by_party, "complaint")
			if pp != self.complaint:
				frappe.throw(_("Complaint Party must belong to this complaint."), frappe.ValidationError)

		self.display_label = code_title_label(_strip(self.evidence_type) or "—", (_strip(self.description) or "")[:40])
		self._set_hash_from_file()

	def _set_hash_from_file(self) -> None:
		if _strip(self.hash_value):
			return
		f = _strip(self.file)
		if not f or "/files/" not in f:
			return
		try:
			fn = f.split("/files/", 1)[-1]
			path = os.path.join(get_files_path(), fn)
			if not os.path.isfile(path):
				return
			with open(path, "rb") as fh:
				self.hash_value = hashlib.sha256(fh.read()).hexdigest()
		except OSError:
			return
