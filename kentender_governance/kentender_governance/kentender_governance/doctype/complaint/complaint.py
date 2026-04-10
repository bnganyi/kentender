# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import re

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

ER = "Exception Record"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class Complaint(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if self.complaint_title is not None:
			self.complaint_title = self.complaint_title.strip()
		for fld in ("complainant_name", "complainant_contact_email", "complainant_contact_phone"):
			v = getattr(self, fld, None)
			if v is not None and isinstance(v, str):
				setattr(self, fld, v.strip())

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.complaint_title))

		email = _strip(self.complainant_contact_email)
		if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
			frappe.throw(_("Complainant contact email is not valid."), frappe.ValidationError)

		if self.received_by_user and not frappe.db.exists("User", self.received_by_user):
			frappe.throw(_("Received By user not found."), frappe.ValidationError)
		if self.reviewed_by_user and not frappe.db.exists("User", self.reviewed_by_user):
			frappe.throw(_("Reviewed By user not found."), frappe.ValidationError)
		if self.supplier and frappe.db.exists("DocType", "Supplier") and not frappe.db.exists("Supplier", self.supplier):
			frappe.throw(_("Supplier not found."), frappe.ValidationError)

		if self.exception_record and not frappe.db.exists(ER, self.exception_record):
			frappe.throw(_("Exception Record not found."), frappe.ValidationError)

		for dt, val in (
			("Tender", self.tender),
			("Bid Submission", self.bid_submission),
			("Evaluation Session", self.evaluation_session),
			("Award Decision", self.award_decision),
			("Procurement Contract", self.contract),
		):
			if val and not frappe.db.exists(dt, val):
				frappe.throw(_("{0} not found.").format(dt), frappe.ValidationError)
