# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-001: Store master (central / project / department)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

PD = "Procuring Department"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class Store(Document):
	def validate(self):
		if self.store_code is not None:
			self.store_code = self.store_code.strip()
		if self.store_name is not None:
			self.store_name = self.store_name.strip()
		if self.location is not None:
			self.location = self.location.strip()

		self.display_label = code_title_label(_strip(self.store_code), _strip(self.store_name))

		if self.store_manager_user and not frappe.db.exists("User", self.store_manager_user):
			frappe.throw(_("Store Manager user not found."), frappe.ValidationError)
		if self.responsible_department and not frappe.db.exists(PD, self.responsible_department):
			frappe.throw(_("Responsible Department not found."), frappe.ValidationError)
