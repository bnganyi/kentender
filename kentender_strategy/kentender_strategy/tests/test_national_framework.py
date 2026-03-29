# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

DOCTYPE = "National Framework"


def _base_kwargs():
	return {
		"doctype": DOCTYPE,
		"framework_code": "NF-TEST",
		"framework_name": "Test National Framework",
		"framework_type": "National Development Plan",
		"version_label": "v1",
		"status": "Draft",
		"is_locked_reference": 0,
		"start_date": "2026-01-01",
		"end_date": "2026-12-31",
	}


class TestNationalFramework(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete(DOCTYPE, {"business_id": ("like", "_KT_NF_%")})
		frappe.db.commit()
		super().tearDown()

	def test_valid_create(self):
		doc = frappe.get_doc({**_base_kwargs(), "business_id": "_KT_NF_001"})
		doc.insert()
		self.assertEqual(doc.name, "_KT_NF_001")

	def test_duplicate_business_id_blocked(self):
		frappe.get_doc({**_base_kwargs(), "business_id": "_KT_NF_DUP"}).insert()
		dup = frappe.get_doc({**_base_kwargs(), "business_id": "_KT_NF_DUP", "version_label": "v2"})
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_duplicate_framework_code_version_blocked(self):
		frappe.get_doc({**_base_kwargs(), "business_id": "_KT_NF_A", "version_label": "2026"}).insert()
		dup = frappe.get_doc({**_base_kwargs(), "business_id": "_KT_NF_B", "version_label": "2026"})
		self.assertRaises(frappe.DuplicateEntryError, dup.insert)

	def test_same_code_different_version_allowed(self):
		frappe.get_doc({**_base_kwargs(), "business_id": "_KT_NF_C1", "version_label": "2025"}).insert()
		doc2 = frappe.get_doc({**_base_kwargs(), "business_id": "_KT_NF_C2", "version_label": "2026"})
		doc2.insert()
		self.assertEqual(doc2.framework_code, "NF-TEST")

	def test_invalid_date_range_blocked(self):
		doc = frappe.get_doc(
			{
				**_base_kwargs(),
				"business_id": "_KT_NF_DAT",
				"start_date": "2026-12-31",
				"end_date": "2026-01-01",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_active_locked_cannot_edit_core_fields(self):
		doc = frappe.get_doc(
			{
				**_base_kwargs(),
				"business_id": "_KT_NF_LK",
				"status": "Active",
				"is_locked_reference": 1,
			}
		)
		doc.insert()
		doc.framework_name = "Changed name"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_draft_can_edit(self):
		doc = frappe.get_doc({**_base_kwargs(), "business_id": "_KT_NF_ED"})
		doc.insert()
		doc.framework_name = "Updated title"
		doc.save()
		reloaded = frappe.get_doc(DOCTYPE, doc.name)
		self.assertEqual(reloaded.framework_name, "Updated title")
