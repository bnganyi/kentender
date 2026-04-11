# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-036: execution audit trail for report runs."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

RD = "KenTender Report Definition"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderReportExecutionLog(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.status) or "—")

		if not self.report_definition or not frappe.db.exists(RD, self.report_definition):
			frappe.throw(_("Report Definition not found."), frappe.ValidationError)

		if self.executed_by_user and not frappe.db.exists("User", self.executed_by_user):
			frappe.throw(_("Executed By user not found."), frappe.ValidationError)
