# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-001–002: Store and Store Item."""

import frappe
from frappe.model.base_document import get_controller
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup

PREFIX = "_KT_OPS001"
STORE = "Store"
STORE_ITEM = "Store Item"


def _cleanup_stores(prefix: str):
	for si in frappe.get_all(
		STORE_ITEM,
		filters={"item_code": ("like", f"{prefix}%")},
		pluck="name",
	) or []:
		frappe.delete_doc(STORE_ITEM, si, force=True, ignore_permissions=True)
	for s in frappe.get_all(
		STORE,
		filters={"store_code": ("like", f"{prefix}%")},
		pluck="name",
	) or []:
		frappe.delete_doc(STORE, s, force=True, ignore_permissions=True)


def _store_payload(*, store_code: str):
	return {
		"doctype": STORE,
		"store_code": store_code,
		"store_name": "Test Store",
		"store_type": "Central",
		"location": "Block A",
		"store_manager_user": "Administrator",
		"status": "Active",
	}


class TestStoreDoctypes001002(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: _cleanup_stores(PREFIX))

	def tearDown(self):
		run_test_db_cleanup(lambda: _cleanup_stores(PREFIX))
		super().tearDown()

	def test_KT_OPS001_controllers_import(self):
		get_controller(STORE)
		get_controller(STORE_ITEM)

	def test_KT_OPS001_create_and_display_label(self):
		doc = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_S1")).insert(ignore_permissions=True)
		self.assertTrue(doc.display_label)
		self.assertEqual(doc.name, f"{PREFIX}_S1")

	def test_KT_OPS001_duplicate_store_code(self):
		frappe.get_doc(_store_payload(store_code=f"{PREFIX}_DUP")).insert(ignore_permissions=True)
		self.assertRaises(
			frappe.DuplicateEntryError,
			lambda: frappe.get_doc(_store_payload(store_code=f"{PREFIX}_DUP")).insert(ignore_permissions=True),
		)

	def test_KT_OPS001_invalid_manager_user(self):
		p = _store_payload(store_code=f"{PREFIX}_BADU")
		p["store_manager_user"] = "nonexistent_store_mgr_user_zz"
		self.assertRaises(frappe.ValidationError, lambda: frappe.get_doc(p).insert(ignore_permissions=True))

	def test_KT_OPS002_store_item_unique_per_store(self):
		sid = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_ST")).insert(ignore_permissions=True).name
		frappe.get_doc(
			{
				"doctype": STORE_ITEM,
				"store": sid,
				"item_code": f"{PREFIX}_ITEM1",
				"item_name": "Widget",
				"unit_of_measure": "EA",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		self.assertRaises(
			frappe.ValidationError,
			lambda: frappe.get_doc(
				{
					"doctype": STORE_ITEM,
					"store": sid,
					"item_code": f"{PREFIX}_ITEM1",
					"item_name": "Dup",
					"status": "Active",
				}
			).insert(ignore_permissions=True),
		)
