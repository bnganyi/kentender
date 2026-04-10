# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

AR = "Acceptance Record"
IR = "Inspection Record"
NC = "Non Conformance Record"


class InspectionEvidence(Document):
	def validate(self):
		self.title = (self.title or "").strip()
		self.display_label = code_title_label(self.title, self.evidence_type or "")

		if self.acceptance_record:
			ar = frappe.db.get_value(AR, self.acceptance_record, ("inspection_record",), as_dict=True)
			if ar and ar.inspection_record and ar.inspection_record != self.inspection_record:
				frappe.throw(_("Acceptance Record must belong to the same Inspection Record."), frappe.ValidationError)

		if self.non_conformance_record:
			nc_ir = frappe.db.get_value(NC, self.non_conformance_record, "inspection_record")
			if nc_ir and nc_ir != self.inspection_record:
				frappe.throw(_("Non Conformance Record must belong to the same Inspection Record."), frappe.ValidationError)
