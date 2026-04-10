# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-005–008: Store Ledger Entry, Stock Movement, Store Issue, Store Reconciliation Record."""

import frappe
from frappe.model.base_document import get_controller
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import run_test_db_cleanup

PREFIX = "_KT_OPS005"
STORE = "Store"
SLE = "Store Ledger Entry"
SM = "Stock Movement"
SI = "Store Issue"
SRR = "Store Reconciliation Record"


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


def _cleanup_ops005():
	for dt, bf in (
		(SI, "business_id"),
		(SM, "business_id"),
		(SRR, "business_id"),
	):
		for name in frappe.get_all(dt, filters={bf: ("like", f"{PREFIX}%")}, pluck="name") or []:
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

	frappe.flags.allow_store_ledger_delete = True
	try:
		for sid in frappe.get_all(STORE, filters={"store_code": ("like", f"{PREFIX}%")}, pluck="name") or []:
			for le in frappe.get_all(SLE, filters={"store": sid}, pluck="name") or []:
				frappe.delete_doc(SLE, le, force=True, ignore_permissions=True)
	finally:
		frappe.flags.allow_store_ledger_delete = False

	for si in frappe.get_all("Store Item", filters={"item_code": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc("Store Item", si, force=True, ignore_permissions=True)
	for sid in frappe.get_all(STORE, filters={"store_code": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(STORE, sid, force=True, ignore_permissions=True)


class TestStoreChain005008(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_ops005)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ops005)
		super().tearDown()

	def test_KT_OPS005_controllers_import(self):
		get_controller(SLE)
		get_controller(SM)
		get_controller(SI)
		get_controller(SRR)

	def test_KT_OPS005_ledger_create_append_only_and_delete_guard(self):
		st = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_S1")).insert(ignore_permissions=True).name
		le = frappe.get_doc(
			{
				"doctype": SLE,
				"store": st,
				"item_reference": f"{PREFIX}_ITEM",
				"entry_type": "Receipt",
				"entry_direction": "In",
				"quantity": 1.0,
				"unit_of_measure": "EA",
				"posting_datetime": now_datetime(),
				"source_doctype": STORE,
				"source_docname": st,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(le.entry_hash)
		le.quantity = 2.0
		self.assertRaises(frappe.ValidationError, le.save)

		self.assertRaises(frappe.ValidationError, lambda: frappe.delete_doc(SLE, le.name))

		frappe.flags.allow_store_ledger_delete = True
		try:
			frappe.delete_doc(SLE, le.name, force=True, ignore_permissions=True)
		finally:
			frappe.flags.allow_store_ledger_delete = False

	def test_KT_OPS006_stock_movement_two_stores(self):
		a = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_MA")).insert(ignore_permissions=True).name
		b = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_MB")).insert(ignore_permissions=True).name
		doc = frappe.get_doc(
			{
				"doctype": SM,
				"business_id": f"{PREFIX}_MV1",
				"from_store": a,
				"to_store": b,
				"movement_datetime": now_datetime(),
				"status": "Draft",
				"initiated_by_user": "Administrator",
				"items": [
					{
						"item_code": f"{PREFIX}_LINE",
						"quantity": 3.0,
						"unit_of_measure": "EA",
					}
				],
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.display_label)

	def test_KT_OPS007_store_issue(self):
		st = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_SI")).insert(ignore_permissions=True).name
		doc = frappe.get_doc(
			{
				"doctype": SI,
				"business_id": f"{PREFIX}_ISS1",
				"store": st,
				"issue_datetime": now_datetime(),
				"issued_to_user": "Administrator",
				"status": "Draft",
				"items": [
					{
						"item_code": f"{PREFIX}_G1",
						"quantity": 2.0,
						"unit_of_measure": "EA",
					}
				],
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.display_label)

	def test_KT_OPS008_reconciliation_variance(self):
		st = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_SR")).insert(ignore_permissions=True).name
		doc = frappe.get_doc(
			{
				"doctype": SRR,
				"business_id": f"{PREFIX}_REC1",
				"store": st,
				"reconciliation_datetime": now_datetime(),
				"counted_by_user": "Administrator",
				"status": "Draft",
				"items": [
					{
						"item_code": f"{PREFIX}_R1",
						"book_quantity": 10.0,
						"counted_quantity": 8.0,
						"unit_of_measure": "EA",
					}
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(doc.items[0].variance_quantity, -2.0)
