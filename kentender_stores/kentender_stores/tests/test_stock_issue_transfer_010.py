# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-010: stock issue and transfer services (ledger posting)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import run_test_db_cleanup
from kentender_stores.services.stock_issue_transfer_services import issue_stock_from_store, transfer_stock_between_stores

PREFIX = "_KT_OPS010"
STORE = "Store"
SLE = "Store Ledger Entry"
SM = "Stock Movement"
SI = "Store Issue"


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


def _cleanup_ops010():
	frappe.flags.allow_store_ledger_delete = True
	try:
		for sid in frappe.get_all(STORE, filters={"store_code": ("like", f"{PREFIX}%")}, pluck="name") or []:
			for le in frappe.get_all(SLE, filters={"store": sid}, pluck="name") or []:
				frappe.delete_doc(SLE, le, force=True, ignore_permissions=True)
	finally:
		frappe.flags.allow_store_ledger_delete = False

	for dt, bf in ((SI, "business_id"), (SM, "business_id")):
		for name in frappe.get_all(dt, filters={bf: ("like", f"{PREFIX}%")}, pluck="name") or []:
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

	for sid in frappe.get_all(STORE, filters={"store_code": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(STORE, sid, force=True, ignore_permissions=True)


class TestStockIssueTransfer010(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_ops010)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ops010)
		super().tearDown()

	def test_KT_OPS010_transfer_posts_out_and_in_ledgers(self):
		a = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_A")).insert(ignore_permissions=True).name
		b = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_B")).insert(ignore_permissions=True).name
		out = transfer_stock_between_stores(
			a,
			b,
			items=[{"item_code": f"{PREFIX}_SKU", "quantity": 4.0, "unit_of_measure": "EA"}],
			movement_business_id=f"{PREFIX}_MV1",
			initiated_by_user="Administrator",
		)
		self.assertEqual(len(out["store_ledger_entries"]), 2)
		self.assertEqual(frappe.db.get_value(SM, out["stock_movement"], "status"), "Completed")

		n1, n2 = out["store_ledger_entries"]
		self.assertEqual(frappe.db.get_value(SLE, n1, "entry_type"), "Transfer")
		self.assertEqual(frappe.db.get_value(SLE, n1, "store"), a)
		self.assertEqual(frappe.db.get_value(SLE, n1, "entry_direction"), "Out")
		self.assertEqual(frappe.db.get_value(SLE, n2, "store"), b)
		self.assertEqual(frappe.db.get_value(SLE, n2, "entry_direction"), "In")

	def test_KT_OPS010_issue_posts_outbound_ledger(self):
		st = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_S")).insert(ignore_permissions=True).name
		out = issue_stock_from_store(
			st,
			"Administrator",
			items=[{"item_code": f"{PREFIX}_G", "quantity": 1.5, "unit_of_measure": "Nos"}],
			issue_business_id=f"{PREFIX}_IS1",
			purpose="Field use",
		)
		self.assertEqual(len(out["store_ledger_entries"]), 1)
		self.assertEqual(frappe.db.get_value(SI, out["store_issue"], "status"), "Issued")
		n = out["store_ledger_entries"][0]
		self.assertEqual(frappe.db.get_value(SLE, n, "entry_type"), "Issue")
		self.assertEqual(frappe.db.get_value(SLE, n, "entry_direction"), "Out")

	def test_KT_OPS010_transfer_rejects_same_store(self):
		a = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_C")).insert(ignore_permissions=True).name
		self.assertRaises(
			frappe.ValidationError,
			lambda: transfer_stock_between_stores(
				a,
				a,
				items=[{"item_code": "X", "quantity": 1.0}],
				movement_business_id=f"{PREFIX}_BAD",
			),
		)
