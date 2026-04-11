# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-013–018: KenTender Asset master and satellite DocTypes.

DocType names are prefixed **KenTender …** so they do not collide with ERPNext **Asset** / **Asset Category**.
"""

import unittest

import frappe
from frappe.model.base_document import get_controller
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_stores.tests.test_grn_doctypes_003_004 import cleanup_procurement_chain, minimal_procurement_contract

PREFIX = "_KT_OPS013"
PC = "Procurement Contract"
CAT = "KenTender Asset Category"
AST = "KenTender Asset"
ASG = "KenTender Asset Assignment"
ACL = "KenTender Asset Condition Log"
AMR = "KenTender Asset Maintenance Record"
ADR = "KenTender Asset Disposal Record"


def _skip_without_procurement():
	if not frappe.db.exists("DocType", PC):
		raise unittest.SkipTest("Procurement Contract DocType not available.")


def _cleanup_assets(prefix: str):
	for dt, bf in (
		(ADR, "business_id"),
		(AMR, "business_id"),
		(ASG, "business_id"),
	):
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

	cleanup_procurement_chain(prefix)


def _cleanup_ops013():
	_cleanup_assets(PREFIX)


class TestAssetDoctypes013018(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_ops013)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ops013)
		super().tearDown()

	def test_KT_OPS013_018_controllers_import(self):
		get_controller(CAT)
		get_controller(AST)
		get_controller(ASG)
		get_controller(ACL)
		get_controller(AMR)
		get_controller(ADR)

	def test_KT_OPS014_ken_tender_asset_category(self):
		doc = frappe.get_doc(
			{
				"doctype": CAT,
				"category_code": f"{PREFIX}_CAT",
				"category_name": "IT Equipment",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.display_label)

	def test_KT_OPS013_asset_and_satellites_with_contract(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()
		pc = minimal_procurement_contract(PREFIX, "Ast", entity.name, currency)

		cat = frappe.get_doc(
			{
				"doctype": CAT,
				"category_code": f"{PREFIX}_CAT2",
				"category_name": "Vehicles",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		ast = frappe.get_doc(
			{
				"doctype": AST,
				"asset_code": f"{PREFIX}_A1",
				"asset_name": "Laptop",
				"asset_category": cat.name,
				"source_contract": pc.name,
				"supplier": "ACME",
				"acquisition_date": nowdate(),
				"acquisition_cost": 1200,
				"currency": currency,
				"current_location": "HQ",
				"assigned_to_user": "Administrator",
				"condition_status": "Good",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(ast.display_label)

		frappe.get_doc(
			{
				"doctype": ASG,
				"business_id": f"{PREFIX}_ASG1",
				"asset": ast.name,
				"assignment_datetime": now_datetime(),
				"assignment_type": "Permanent",
				"assigned_to_user": "Administrator",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		frappe.get_doc(
			{
				"doctype": ACL,
				"asset": ast.name,
				"condition_datetime": now_datetime(),
				"condition_status": "Fair",
				"assessed_by_user": "Administrator",
			}
		).insert(ignore_permissions=True)

		frappe.get_doc(
			{
				"doctype": AMR,
				"business_id": f"{PREFIX}_AMR1",
				"asset": ast.name,
				"maintenance_type": "Preventive",
				"status": "Scheduled",
				"currency": currency,
			}
		).insert(ignore_permissions=True)

		frappe.get_doc(
			{
				"doctype": ADR,
				"business_id": f"{PREFIX}_ADR1",
				"asset": ast.name,
				"disposal_method": "Write-off",
				"disposal_datetime": now_datetime(),
				"currency": currency,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def test_KT_OPS013_asset_requires_procurement_link(self):
		cat = frappe.get_doc(
			{
				"doctype": CAT,
				"category_code": f"{PREFIX}_CAT3",
				"category_name": "Misc",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		self.assertRaises(
			frappe.ValidationError,
			lambda: frappe.get_doc(
				{
					"doctype": AST,
					"asset_code": f"{PREFIX}_BAD",
					"asset_name": "X",
					"asset_category": cat.name,
					"supplier": "S",
					"acquisition_date": nowdate(),
					"acquisition_cost": 1,
					"currency": _ensure_test_currency(),
					"current_location": "—",
					"condition_status": "Unknown",
					"status": "Draft",
				}
			).insert(ignore_permissions=True),
		)
