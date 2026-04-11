# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-019–021: create assets from GRN, lifecycle helpers, tracking queries."""

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_assets.services.asset_lifecycle_services import (
	complete_disposal_record,
	complete_maintenance_record,
	log_asset_condition,
	register_asset_assignment,
)
from kentender_assets.services.asset_tracking_queries import (
	get_assets_for_contract,
	get_assets_for_grn,
	get_draft_disposal_records,
	get_open_maintenance_records,
)
from kentender_assets.services.create_asset_from_grn import create_asset_from_grn
from kentender_stores.tests.test_grn_doctypes_003_004 import cleanup_procurement_chain, minimal_procurement_contract

PREFIX = "_KT_OPS019"
PC = "Procurement Contract"
GRN = "Goods Receipt Note"
STORE = "Store"
CAT = "KenTender Asset Category"
AST = "KenTender Asset"
AMR = "KenTender Asset Maintenance Record"
ADR = "KenTender Asset Disposal Record"
ASG = "KenTender Asset Assignment"
ACL = "KenTender Asset Condition Log"


def _skip_without_procurement():
	if not frappe.db.exists("DocType", PC):
		raise unittest.SkipTest("Procurement Contract DocType not available.")


def _cleanup_ops019(prefix: str):
	frappe.flags.allow_store_ledger_delete = True
	try:
		for row in frappe.get_all(GRN, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
			frappe.delete_doc(GRN, row, force=True, ignore_permissions=True)
	finally:
		frappe.flags.allow_store_ledger_delete = False

	for dt, bf in ((ADR, "business_id"), (AMR, "business_id"), (ASG, "business_id")):
		for name in frappe.get_all(dt, filters={bf: ("like", f"{prefix}%")}, pluck="name") or []:
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

	anames = frappe.get_all(AST, filters={"asset_code": ("like", f"{prefix}%")}, pluck="name") or []
	if anames:
		for name in frappe.get_all(ACL, filters={"asset": ("in", anames)}, pluck="name") or []:
			frappe.delete_doc(ACL, name, force=True, ignore_permissions=True)

	for name in frappe.get_all(AST, filters={"asset_code": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(AST, name, force=True, ignore_permissions=True)

	for name in frappe.get_all(CAT, filters={"category_code": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(CAT, name, force=True, ignore_permissions=True)

	for s in frappe.get_all(STORE, filters={"store_code": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(STORE, s, force=True, ignore_permissions=True)

	cleanup_procurement_chain(prefix)


class TestAssetServices019021(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(lambda: _cleanup_ops019(PREFIX))

	def tearDown(self):
		run_test_db_cleanup(lambda: _cleanup_ops019(PREFIX))
		super().tearDown()

	def _make_store(self, code: str) -> str:
		return (
			frappe.get_doc(
				{
					"doctype": STORE,
					"store_code": code,
					"store_name": "Test Store",
					"store_type": "Central",
					"location": "Block A",
					"store_manager_user": "Administrator",
					"status": "Active",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def test_KT_OPS019_create_asset_from_grn_skips_non_capital(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()
		pc = minimal_procurement_contract(PREFIX, "A", entity.name, currency)
		st = self._make_store(f"{PREFIX}_ST")
		cat = frappe.get_doc(
			{
				"doctype": CAT,
				"category_code": f"{PREFIX}_CAT",
				"category_name": "Equipment",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		grn = frappe.get_doc(
			{
				"doctype": GRN,
				"business_id": f"{PREFIX}_GRN",
				"contract": pc.name,
				"supplier": "S-1",
				"store": st,
				"receipt_datetime": now_datetime(),
				"received_by_user": "Administrator",
				"status": "Draft",
				"currency": currency,
				"items": [
					{
						"item_code": f"{PREFIX}_CAP",
						"item_name": "Laptop",
						"quantity": 2,
						"unit_of_measure": "Nos",
						"unit_rate": 500,
						"capital_asset": 1,
						"asset_category": cat.name,
					},
					{
						"item_code": f"{PREFIX}_CONS",
						"item_name": "Consumable",
						"quantity": 10,
						"unit_of_measure": "Nos",
						"unit_rate": 1,
						"capital_asset": 0,
					},
				],
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(GRN, grn.name, "status", "Received")

		out = create_asset_from_grn(grn.name, asset_code_prefix=f"{PREFIX}_AST")
		self.assertEqual(out["count"], 2)
		self.assertEqual(len(frappe.get_all(AST, filters={"source_grn": grn.name})), 2)
		row = frappe.get_doc(AST, out["assets"][0])
		self.assertEqual(row.source_contract, pc.name)
		self.assertEqual(row.supplier, "S-1")
		self.assertEqual(row.currency, currency)
		self.assertEqual(row.asset_category, cat.name)
		self.assertTrue(row.current_location)

	def test_KT_OPS019_requires_received_grn(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE2").insert()
		_bcp(f"{PREFIX}_BCP2", entity.name).insert()
		pc = minimal_procurement_contract(PREFIX, "B", entity.name, currency)
		st = self._make_store(f"{PREFIX}_ST2")
		cat = frappe.get_doc(
			{
				"doctype": CAT,
				"category_code": f"{PREFIX}_CAT2",
				"category_name": "X",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		grn = frappe.get_doc(
			{
				"doctype": GRN,
				"business_id": f"{PREFIX}_GRN2",
				"contract": pc.name,
				"supplier": "S-1",
				"store": st,
				"receipt_datetime": now_datetime(),
				"received_by_user": "Administrator",
				"status": "Draft",
				"currency": currency,
				"items": [
					{
						"item_code": f"{PREFIX}_X",
						"quantity": 1,
						"unit_of_measure": "Nos",
						"unit_rate": 1,
						"capital_asset": 1,
						"asset_category": cat.name,
					},
				],
			}
		).insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, lambda: create_asset_from_grn(grn.name))

	def test_KT_OPS021_tracking_queries(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE3").insert()
		_bcp(f"{PREFIX}_BCP3", entity.name).insert()
		pc = minimal_procurement_contract(PREFIX, "C", entity.name, currency)
		st = self._make_store(f"{PREFIX}_ST3")
		cat = frappe.get_doc(
			{
				"doctype": CAT,
				"category_code": f"{PREFIX}_CAT3",
				"category_name": "Y",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		grn = frappe.get_doc(
			{
				"doctype": GRN,
				"business_id": f"{PREFIX}_GRN3",
				"contract": pc.name,
				"supplier": "S-1",
				"store": st,
				"receipt_datetime": now_datetime(),
				"received_by_user": "Administrator",
				"status": "Draft",
				"currency": currency,
				"items": [
					{
						"item_code": f"{PREFIX}_ONE",
						"quantity": 1,
						"unit_of_measure": "Nos",
						"unit_rate": 100,
						"capital_asset": 1,
						"asset_category": cat.name,
					},
				],
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(GRN, grn.name, "status", "Received")
		out = create_asset_from_grn(grn.name, asset_code_prefix=f"{PREFIX}_T21")
		self.assertEqual(out["count"], 1)

		by_grn = get_assets_for_grn(grn.name)
		self.assertEqual(len(by_grn), 1)
		by_pc = get_assets_for_contract(pc.name)
		self.assertTrue(any(r["name"] == out["assets"][0] for r in by_pc))

	def test_KT_OPS020_lifecycle_services(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE4").insert()
		_bcp(f"{PREFIX}_BCP4", entity.name).insert()
		pc = minimal_procurement_contract(PREFIX, "D", entity.name, currency)
		st = self._make_store(f"{PREFIX}_ST4")
		cat = frappe.get_doc(
			{
				"doctype": CAT,
				"category_code": f"{PREFIX}_CAT4",
				"category_name": "Z",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		ast = frappe.get_doc(
			{
				"doctype": AST,
				"asset_code": f"{PREFIX}_LC1",
				"asset_name": "Vehicle",
				"asset_category": cat.name,
				"source_contract": pc.name,
				"supplier": "S",
				"acquisition_date": nowdate(),
				"acquisition_cost": 1,
				"currency": currency,
				"current_location": "HQ",
				"condition_status": "Good",
				"status": "In Maintenance",
			}
		).insert(ignore_permissions=True)

		mr = frappe.get_doc(
			{
				"doctype": AMR,
				"business_id": f"{PREFIX}_AMR",
				"asset": ast.name,
				"maintenance_type": "Preventive",
				"status": "Scheduled",
				"currency": currency,
			}
		).insert(ignore_permissions=True)
		complete_maintenance_record(mr.name, performed_by_user="Administrator", summary="Done")
		ast.reload()
		self.assertEqual(ast.status, "Active")

		out = log_asset_condition(ast.name, "Fair", "Administrator", remarks="Check")
		self.assertTrue(out.get("condition_log"))

		reg = register_asset_assignment(
			ast.name,
			f"{PREFIX}_ASG",
			"Administrator",
			"Permanent",
			to_location="Branch",
		)
		self.assertTrue(reg.get("assignment"))
		ast.reload()
		self.assertEqual(ast.assigned_to_user, "Administrator")

		dd = frappe.get_doc(
			{
				"doctype": ADR,
				"business_id": f"{PREFIX}_DISP",
				"asset": ast.name,
				"disposal_method": "Write-off",
				"disposal_datetime": now_datetime(),
				"currency": currency,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(any(r["name"] == dd.name for r in get_draft_disposal_records(limit=50)))
		complete_disposal_record(dd.name, approved_by_user="Administrator")
		ast.reload()
		self.assertEqual(ast.status, "Disposed")
		self.assertFalse(any(r["name"] == dd.name for r in get_draft_disposal_records(limit=500)))

		open_m = get_open_maintenance_records(limit=20)
		self.assertIsInstance(open_m, list)
