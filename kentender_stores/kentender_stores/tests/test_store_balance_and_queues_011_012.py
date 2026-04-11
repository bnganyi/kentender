# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-011–012: ledger balances, queue queries, script reports."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import run_test_db_cleanup
from kentender_stores.report.pending_store_issues.pending_store_issues import execute as pending_issues_execute
from kentender_stores.report.store_stock_balance.store_stock_balance import execute as stock_balance_execute
from kentender_stores.services.store_ledger_balance import get_item_balance, get_store_balances
from kentender_stores.services.store_queue_queries import get_open_stock_movements, get_pending_store_issues

PREFIX = "_KT_OPS011"
STORE = "Store"
SLE = "Store Ledger Entry"
SI = "Store Issue"
SM = "Stock Movement"


def _store_payload(*, store_code: str):
	return {
		"doctype": STORE,
		"store_code": store_code,
		"store_name": "Bal",
		"store_type": "Central",
		"store_manager_user": "Administrator",
		"status": "Active",
	}


def _cleanup_ops011():
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


class TestStoreBalanceAndQueues011012(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_ops011)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ops011)
		super().tearDown()

	def test_KT_OPS011_balance_from_ledger_in_out(self):
		st = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_S")).insert(ignore_permissions=True).name
		sku = f"{PREFIX}_SKU"
		dt = now_datetime()
		for direction, qty in (("In", 10.0), ("Out", 3.0)):
			frappe.get_doc(
				{
					"doctype": SLE,
					"store": st,
					"item_reference": sku,
					"entry_type": "Receipt" if direction == "In" else "Issue",
					"entry_direction": direction,
					"quantity": qty,
					"unit_of_measure": "EA",
					"posting_datetime": dt,
					"source_doctype": STORE,
					"source_docname": st,
				}
			).insert(ignore_permissions=True)

		self.assertEqual(get_item_balance(st, sku), 7.0)
		rows = get_store_balances(st, include_zero=False)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["quantity"], 7.0)

	def test_KT_OPS012_queue_queries_and_reports(self):
		st = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_Q")).insert(ignore_permissions=True).name
		st_b = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_Q2")).insert(ignore_permissions=True).name
		frappe.get_doc(
			{
				"doctype": SI,
				"business_id": f"{PREFIX}_SI1",
				"store": st,
				"issue_datetime": now_datetime(),
				"issued_to_user": "Administrator",
				"status": "Draft",
				"items": [{"item_code": "A", "quantity": 1, "unit_of_measure": "Nos"}],
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": SM,
				"business_id": f"{PREFIX}_SM1",
				"from_store": st,
				"to_store": st_b,
				"movement_datetime": now_datetime(),
				"status": "Draft",
				"initiated_by_user": "Administrator",
				"items": [{"item_code": "B", "quantity": 1, "unit_of_measure": "Nos"}],
			}
		).insert(ignore_permissions=True)

		pending = get_pending_store_issues()
		self.assertTrue(any(r.get("business_id") == f"{PREFIX}_SI1" for r in pending))

		open_mv = get_open_stock_movements()
		self.assertTrue(any(r.get("business_id") == f"{PREFIX}_SM1" for r in open_mv))

		cols, data = pending_issues_execute()
		self.assertTrue(len(cols) >= 3)
		self.assertIsInstance(data, list)

	def test_KT_OPS011_stock_balance_report_execute(self):
		st = frappe.get_doc(_store_payload(store_code=f"{PREFIX}_R")).insert(ignore_permissions=True).name
		sku = f"{PREFIX}_ITM"
		frappe.get_doc(
			{
				"doctype": SLE,
				"store": st,
				"item_reference": sku,
				"entry_type": "Receipt",
				"entry_direction": "In",
				"quantity": 2.0,
				"unit_of_measure": "Nos",
				"posting_datetime": now_datetime(),
				"source_doctype": STORE,
				"source_docname": st,
			}
		).insert(ignore_permissions=True)

		cols, data = stock_balance_execute({"store": st})
		self.assertTrue(len(cols) >= 2)
		self.assertEqual(len(data), 1)
		self.assertEqual(data[0][0], sku)
		self.assertEqual(float(data[0][1]), 2.0)
