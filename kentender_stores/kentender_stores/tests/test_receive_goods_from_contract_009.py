# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-009: receive_goods_from_contract service."""

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_stores.services.receive_goods_from_contract import receive_goods_from_contract
from kentender_stores.tests.test_grn_doctypes_003_004 import (
	AR,
	GRN,
	IR,
	IMT,
	PC,
	SLE,
	cleanup_procurement_chain,
	minimal_procurement_contract,
)

PREFIX = "_KT_OPS009"


def _cleanup_ops009():
	cleanup_procurement_chain(PREFIX)


def _skip_without_procurement():
	if not frappe.db.exists("DocType", PC):
		raise unittest.SkipTest("Procurement Contract DocType not available.")


class TestReceiveGoodsFromContract009(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_ops009)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ops009)
		super().tearDown()

	def test_KT_OPS009_receive_creates_grn_and_ledger_and_progress(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()
		if not frappe.db.exists("UOM", "Nos"):
			frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)

		pc = minimal_procurement_contract(PREFIX, "R", entity.name, currency)
		frappe.db.set_value(PC, pc.name, "completion_percent", 0)

		st = (
			frappe.get_doc(
				{
					"doctype": "Store",
					"store_code": f"{PREFIX}_ST",
					"store_name": "Recv",
					"store_type": "Central",
					"store_manager_user": "Administrator",
					"status": "Active",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

		tpl = frappe.get_doc(
			{
				"doctype": IMT,
				"template_code": f"{PREFIX}_TPL",
				"template_name": "Recv test",
				"inspection_domain": "General",
				"applicable_contract_type": "Goods",
				"inspection_method_type": "Checklist",
				"default_pass_logic": "All Mandatory Pass",
			}
		).insert(ignore_permissions=True)
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IR1",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "Delivery",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": entity.name,
			}
		).insert(ignore_permissions=True)
		ar = frappe.get_doc(
			{
				"doctype": AR,
				"business_id": f"{PREFIX}_AR1",
				"inspection_record": ir.name,
				"contract": pc.name,
				"status": "Approved",
				"workflow_state": "Approved",
				"acceptance_decision": "Accepted",
			}
		).insert(ignore_permissions=True)

		out = receive_goods_from_contract(
			pc.name,
			ar.name,
			st,
			items=[
				{
					"item_code": f"{PREFIX}_SKU",
					"item_name": "Bolt",
					"quantity": 2,
					"unit_of_measure": "Nos",
					"unit_rate": 500,
				}
			],
			grn_business_id=f"{PREFIX}_GRN_RG1",
		)

		self.assertTrue(out.get("goods_receipt_note"))
		self.assertEqual(len(out.get("store_ledger_entries") or []), 1)
		self.assertIsNotNone(out.get("completion_percent"))

		grn_name = out["goods_receipt_note"]
		self.assertEqual(frappe.db.get_value(GRN, grn_name, "status"), "Received")
		self.assertEqual(frappe.db.get_value(GRN, grn_name, "acceptance_reference"), ar.name)

		sle_name = out["store_ledger_entries"][0]
		self.assertEqual(frappe.db.get_value(SLE, sle_name, "entry_type"), "Receipt")
		self.assertEqual(frappe.db.get_value(SLE, sle_name, "source_doctype"), GRN)
		self.assertEqual(frappe.db.get_value(SLE, sle_name, "source_docname"), grn_name)

	def test_KT_OPS009_rejects_pending_acceptance(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()

		pc = minimal_procurement_contract(PREFIX, "P", entity.name, currency)
		st = (
			frappe.get_doc(
				{
					"doctype": "Store",
					"store_code": f"{PREFIX}_ST2",
					"store_name": "Recv",
					"store_type": "Central",
					"store_manager_user": "Administrator",
					"status": "Active",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		tpl = frappe.get_doc(
			{
				"doctype": IMT,
				"template_code": f"{PREFIX}_TPL2",
				"template_name": "Recv test 2",
				"inspection_domain": "General",
				"applicable_contract_type": "Goods",
				"inspection_method_type": "Checklist",
				"default_pass_logic": "All Mandatory Pass",
			}
		).insert(ignore_permissions=True)
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IR2",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "X",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": entity.name,
			}
		).insert(ignore_permissions=True)
		ar = frappe.get_doc(
			{
				"doctype": AR,
				"business_id": f"{PREFIX}_AR2",
				"inspection_record": ir.name,
				"contract": pc.name,
				"status": "Draft",
				"acceptance_decision": "Pending",
			}
		).insert(ignore_permissions=True)

		self.assertRaises(
			frappe.ValidationError,
			lambda: receive_goods_from_contract(
				pc.name,
				ar.name,
				st,
				items=[{"item_code": "X", "quantity": 1, "unit_rate": 1}],
				grn_business_id=f"{PREFIX}_GRN_BAD",
			),
		)

	def test_KT_OPS009_duplicate_receive_blocked(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()

		pc = minimal_procurement_contract(PREFIX, "D", entity.name, currency)
		frappe.db.set_value(PC, pc.name, "completion_percent", 0)

		st = (
			frappe.get_doc(
				{
					"doctype": "Store",
					"store_code": f"{PREFIX}_ST3",
					"store_name": "Recv",
					"store_type": "Central",
					"store_manager_user": "Administrator",
					"status": "Active",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		tpl = frappe.get_doc(
			{
				"doctype": IMT,
				"template_code": f"{PREFIX}_TPL3",
				"template_name": "Recv test 3",
				"inspection_domain": "General",
				"applicable_contract_type": "Goods",
				"inspection_method_type": "Checklist",
				"default_pass_logic": "All Mandatory Pass",
			}
		).insert(ignore_permissions=True)
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IR3",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "Y",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": entity.name,
			}
		).insert(ignore_permissions=True)
		ar = frappe.get_doc(
			{
				"doctype": AR,
				"business_id": f"{PREFIX}_AR3",
				"inspection_record": ir.name,
				"contract": pc.name,
				"status": "Approved",
				"workflow_state": "Approved",
				"acceptance_decision": "Accepted",
			}
		).insert(ignore_permissions=True)

		kw = dict(
			items=[{"item_code": f"{PREFIX}_SKU", "quantity": 1, "unit_rate": 100}],
			grn_business_id=f"{PREFIX}_GRN_D1",
		)
		receive_goods_from_contract(pc.name, ar.name, st, **kw)
		self.assertRaises(
			frappe.ValidationError,
			lambda: receive_goods_from_contract(
				pc.name,
				ar.name,
				st,
				items=[{"item_code": f"{PREFIX}_SKU2", "quantity": 1, "unit_rate": 1}],
				grn_business_id=f"{PREFIX}_GRN_D2",
			),
		)
