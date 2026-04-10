# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-001: Deliberation Session."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from kentender.tests.test_procuring_entity import _make_entity, run_test_db_cleanup

DS = "Deliberation Session"
PREFIX = "_KT_GOV001"


def _cleanup_gov001():
	for row in frappe.get_all(DS, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(DS, row, force=True, ignore_permissions=True)
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE"})


class TestDeliberationSession001(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_gov001)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_gov001)
		super().tearDown()

	def _base_row(self, suf: str):
		return {
			"doctype": DS,
			"business_id": f"{PREFIX}_{suf}",
			"session_title": "Governance session",
			"session_type": "Board",
			"status": "Draft",
			"procuring_entity": self.entity.name,
			"scheduled_datetime": now_datetime(),
		}

	def test_KT_GOV001_valid_create(self):
		doc = frappe.get_doc(self._base_row("OK")).insert(ignore_permissions=True)
		self.assertTrue(doc.display_label)
		self.assertEqual(doc.name, f"{PREFIX}_OK")

	def test_KT_GOV001_duplicate_business_id_blocked(self):
		frappe.get_doc(self._base_row("DUP")).insert(ignore_permissions=True)
		dup = frappe.get_doc(self._base_row("DUP"))
		self.assertRaises(frappe.DuplicateEntryError, dup.insert, ignore_permissions=True)

	def test_KT_GOV001_invalid_linked_document(self):
		row = self._base_row("LINK")
		row["linked_doctype"] = "User"
		row["linked_docname"] = "nonexistent_user_name_xyz_12345"
		doc = frappe.get_doc(row)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_KT_GOV001_actual_end_before_start_blocked(self):
		row = self._base_row("TIME")
		t0 = now_datetime()
		row["actual_start_datetime"] = add_to_date(t0, hours=2)
		row["actual_end_datetime"] = t0
		doc = frappe.get_doc(row)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
