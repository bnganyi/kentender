# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-035: registry for runnable transparency reports."""

import json

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderReportDefinition(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if self.report_title is not None:
			self.report_title = self.report_title.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.report_title))

		if self.standard_report and not frappe.db.exists("Report", self.standard_report):
			frappe.throw(_("Standard Report not found."), frappe.ValidationError)

		if self.filter_defaults_json:
			try:
				json.loads(self.filter_defaults_json)
			except json.JSONDecodeError:
				frappe.throw(_("Filter defaults must be valid JSON."), frappe.ValidationError)

		if self.owner_user and not frappe.db.exists("User", self.owner_user):
			frappe.throw(_("Owner user not found."), frappe.ValidationError)
