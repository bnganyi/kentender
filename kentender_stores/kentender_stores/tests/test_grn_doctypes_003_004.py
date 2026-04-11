# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-003–004: Goods Receipt Note + GRN Line."""

import unittest

import frappe
from frappe.model.base_document import get_controller
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, now_datetime, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

PREFIX = "_KT_OPS003"
GRN = "Goods Receipt Note"
STORE = "Store"
STORE_ITEM = "Store Item"
PC = "Procurement Contract"
IR = "Inspection Record"
AR = "Acceptance Record"
SLE = "Store Ledger Entry"
IMT = "Inspection Method Template"
AD = "Award Decision"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Report"
EVAL = "Evaluation Session"
TENDER = "Tender"


def cleanup_procurement_chain(prefix: str) -> None:
	"""Delete procurement + store test rows created with the given ``prefix`` (also Store Ledger rows)."""
	frappe.flags.allow_store_ledger_delete = True
	try:
		for s in frappe.get_all(STORE, filters={"store_code": ("like", f"{prefix}%")}, pluck="name") or []:
			for le in frappe.get_all(SLE, filters={"store": s}, pluck="name") or []:
				frappe.delete_doc(SLE, le, force=True, ignore_permissions=True)
	finally:
		frappe.flags.allow_store_ledger_delete = False
	pcs = frappe.get_all(PC, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []
	if pcs:
		for row in frappe.get_all(GRN, filters={"contract": ["in", pcs]}, pluck="name") or []:
			frappe.delete_doc(GRN, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(GRN, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(GRN, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(AR, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(AR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(IR, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(IR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(IMT, filters={"name": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(IMT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PC, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(PC, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(AD, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(AD, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(EVAL, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(EVAL, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for si in frappe.get_all(STORE_ITEM, filters={"item_code": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(STORE_ITEM, si, force=True, ignore_permissions=True)
	for s in frappe.get_all(STORE, filters={"store_code": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc(STORE, s, force=True, ignore_permissions=True)
	frappe.db.delete("Budget Control Period", {"name": ("like", f"{prefix}%")})
	for pe in frappe.get_all("Procuring Entity", filters={"entity_code": ("like", f"{prefix}%")}, pluck="name") or []:
		frappe.delete_doc("Procuring Entity", pe, force=True, ignore_permissions=True)


def _cleanup_ops003():
	cleanup_procurement_chain(PREFIX)


def minimal_procurement_contract(prefix: str, suffix: str, entity_name: str, currency: str):
	"""Build a minimal signed procurement chain; used by GRN tests and OPS-009."""
	t = frappe.get_doc(
		{
			"doctype": TENDER,
			"name": f"{prefix}_T{suffix}",
			"business_id": f"{prefix}_T{suffix}-BIZ",
			"title": "GRN test",
			"tender_number": f"{prefix}_TN{suffix}",
			"workflow_state": "Draft",
			"status": "Draft",
			"approval_status": "Draft",
			"origin_type": "Manual",
			"procuring_entity": entity_name,
			"currency": currency,
		}
	).insert(ignore_permissions=True)
	s = frappe.get_doc(
		{
			"doctype": BOS,
			"business_id": f"{prefix}_S{suffix}",
			"tender": t.name,
			"procuring_entity": entity_name,
			"status": "Draft",
			"workflow_state": "Draft",
		}
	).insert(ignore_permissions=True)
	r = frappe.get_doc(
		{
			"doctype": BOR,
			"business_id": f"{prefix}_R{suffix}",
			"tender": t.name,
			"bid_opening_session": s.name,
			"status": "Draft",
		}
	).insert(ignore_permissions=True)
	e = frappe.get_doc(
		{
			"doctype": EVAL,
			"business_id": f"{prefix}_E{suffix}",
			"tender": t.name,
			"procuring_entity": entity_name,
			"status": "Draft",
			"workflow_state": "Draft",
			"opening_session": s.name,
			"opening_register": r.name,
			"evaluation_mode": "Two Envelope",
			"conflict_clearance_status": "Pending",
		}
	).insert(ignore_permissions=True)
	rep = frappe.get_doc(
		{
			"doctype": ES,
			"business_id": f"{prefix}_ER{suffix}",
			"evaluation_session": e.name,
			"tender": t.name,
			"status": "Draft",
		}
	).insert(ignore_permissions=True)
	b = frappe.get_doc(
		{
			"doctype": "Bid Submission",
			"business_id": f"{prefix}_B{suffix}",
			"tender": t.name,
			"supplier": f"S-{suffix}",
			"tender_lot_scope": "Whole Tender",
			"procuring_entity": entity_name,
			"procurement_method": "Open National Tender",
			"status": "Draft",
			"workflow_state": "Draft",
			"submission_version_no": 1,
			"quoted_total_amount": 5000,
		}
	).insert(ignore_permissions=True)
	ad = frappe.get_doc(
		{
			"doctype": AD,
			"business_id": f"{prefix}_AD{suffix}",
			"tender": t.name,
			"evaluation_session": e.name,
			"evaluation_report": rep.name,
			"decision_justification": "GRN test.",
			"recommended_bid_submission": b.name,
			"recommended_supplier": f"S-{suffix}",
			"recommended_amount": 5000,
			"approved_bid_submission": b.name,
			"approved_supplier": f"S-{suffix}",
			"approved_amount": 5000,
			"currency": currency,
		}
	).insert(ignore_permissions=True)
	return frappe.get_doc(
		{
			"doctype": PC,
			"business_id": f"{prefix}_PC{suffix}",
			"contract_title": "GRN contract",
			"award_decision": ad.name,
			"tender": t.name,
			"evaluation_session": e.name,
			"approved_bid_submission": b.name,
			"supplier": f"S-{suffix}",
			"procuring_entity": entity_name,
			"contract_value": 5000,
			"currency": currency,
			"contract_start_date": getdate(nowdate()),
		}
	).insert(ignore_permissions=True)


def _skip_without_procurement():
	if not frappe.db.exists("DocType", PC):
		raise unittest.SkipTest("Procurement Contract DocType not available.")


class TestGRNDoctypes003004(FrappeTestCase):
	def setUp(self):
		super().setUp()
		run_test_db_cleanup(_cleanup_ops003)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ops003)
		super().tearDown()

	def test_KT_OPS003_controllers_import(self):
		get_controller(GRN)
		get_controller("GRN Line")

	def test_KT_OPS003_grn_create_with_lines_and_refs(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()
		if not frappe.db.exists("UOM", "Nos"):
			frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)

		pc = minimal_procurement_contract(PREFIX, "X", entity.name, currency)
		st = self._make_store(f"{PREFIX}_ST1")
		tpl = frappe.get_doc(
			{
				"doctype": IMT,
				"template_code": f"{PREFIX}_TPL",
				"template_name": "GRN test template",
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
				"inspection_title": "Receive check",
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

		doc = frappe.get_doc(
			{
				"doctype": GRN,
				"business_id": f"{PREFIX}_GRN1",
				"contract": pc.name,
				"supplier": "S-TEST",
				"store": st,
				"receipt_datetime": now_datetime(),
				"received_by_user": "Administrator",
				"inspection_reference": ir.name,
				"acceptance_reference": ar.name,
				"status": "Draft",
				"currency": currency,
				"items": [
					{
						"item_code": f"{PREFIX}_SKU1",
						"item_name": "Widget",
						"quantity": 2,
						"unit_of_measure": "Nos",
						"unit_rate": 10,
					}
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value(GRN, doc.name, "total_received_value"), 20.0)

	def test_KT_OPS003_inspection_must_match_contract(self):
		_skip_without_procurement()
		currency = _ensure_test_currency()
		entity = _make_entity(f"{PREFIX}_PE").insert()
		_bcp(f"{PREFIX}_BCP", entity.name).insert()
		pc_a = minimal_procurement_contract(PREFIX, "A", entity.name, currency)
		pc_b = minimal_procurement_contract(PREFIX, "B", entity.name, currency)
		tpl = frappe.get_doc(
			{
				"doctype": IMT,
				"template_code": f"{PREFIX}_TPL2",
				"template_name": "GRN test template 2",
				"inspection_domain": "General",
				"applicable_contract_type": "Goods",
				"inspection_method_type": "Checklist",
				"default_pass_logic": "All Mandatory Pass",
			}
		).insert(ignore_permissions=True)
		ir_b = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRB",
				"contract": pc_b.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "Other",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": entity.name,
			}
		).insert(ignore_permissions=True)
		st = self._make_store(f"{PREFIX}_ST2")
		self.assertRaises(
			frappe.ValidationError,
			lambda: frappe.get_doc(
				{
					"doctype": GRN,
					"business_id": f"{PREFIX}_GRN_BAD",
					"contract": pc_a.name,
					"supplier": "S-X",
					"store": st,
					"receipt_datetime": now_datetime(),
					"received_by_user": "Administrator",
					"inspection_reference": ir_b.name,
					"status": "Draft",
					"currency": currency,
					"items": [
						{
							"item_code": f"{PREFIX}_SKU",
							"quantity": 1,
							"unit_of_measure": "Nos",
							"unit_rate": 1,
						}
					],
				}
			).insert(ignore_permissions=True),
		)

	def _make_store(self, code: str) -> str:
		return (
			frappe.get_doc(
				{
					"doctype": STORE,
					"store_code": code,
					"store_name": "Test",
					"store_type": "Central",
					"store_manager_user": "Administrator",
					"status": "Active",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

