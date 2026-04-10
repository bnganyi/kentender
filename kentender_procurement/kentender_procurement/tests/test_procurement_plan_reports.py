# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-022: procurement plan script reports and planning pipeline smoke."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.plan_item_tender_eligibility import get_plan_item_tender_eligibility
from kentender_procurement.services.procurement_plan_revision_apply import apply_procurement_plan_revision
from kentender_procurement.services.requisition_plan_consolidation import consolidate_requisitions_into_plan

PR = "Purchase Requisition"
RPL = "Requisition Planning Link"
PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PCS = "Plan Consolidation Source"
PPR = "Procurement Plan Revision"
PPRL = "Procurement Plan Revision Line"
PFA = "Plan Fragmentation Alert"
BCP = "Budget Control Period"

_REPORT_MODULES = (
	"kentender_procurement.kentender_procurement.report.planning_queue.planning_queue",
	"kentender_procurement.kentender_procurement.report.draft_procurement_plans.draft_procurement_plans",
	"kentender_procurement.kentender_procurement.report.active_procurement_plans.active_procurement_plans",
	"kentender_procurement.kentender_procurement.report.plan_items_ready_for_tender.plan_items_ready_for_tender",
	"kentender_procurement.kentender_procurement.report.fragmentation_alerts.fragmentation_alerts",
)


def _cleanup_pp022():
	frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"reason": ("like", "%_KT_PP022%")})
	for row in frappe.get_all(PPR, filters={"revision_business_id": ("like", "_KT_PP022_%")}, pluck="name") or []:
		frappe.delete_doc(PPR, row, force=True, ignore_permissions=True)
	for name in frappe.get_all(PFA, filters={"business_id": ("like", "_KT_PP022_%")}, pluck="name") or []:
		frappe.delete_doc(PFA, name, force=True, ignore_permissions=True)
	for pn in frappe.get_all(PP, filters={"name": ("like", "_KT_PP022_%")}, pluck="name") or []:
		for lnk in frappe.get_all(RPL, filters={"procurement_plan": pn}, pluck="name") or []:
			frappe.delete_doc(RPL, lnk, force=True, ignore_permissions=True)
		for pin in frappe.get_all(PPI, filters={"procurement_plan": pn}, pluck="name") or []:
			for src in frappe.get_all(PCS, filters={"procurement_plan_item": pin}, pluck="name") or []:
				frappe.delete_doc(PCS, src, force=True, ignore_permissions=True)
			frappe.delete_doc(PPI, pin, force=True, ignore_permissions=True)
		frappe.delete_doc(PP, pn, force=True, ignore_permissions=True)
	for prn in frappe.get_all(PR, filters={"name": ("like", "_KT_PP022_%")}, pluck="name") or []:
		frappe.db.delete(RPL, {"purchase_requisition": prn})
		frappe.delete_doc(PR, prn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PP022_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PP022_PE"})


def _approved_pr(entity: str, currency: str, business_id: str):
	return frappe.get_doc(
		{
			"doctype": PR,
			"name": business_id,
			"title": "PP022 test",
			"requisition_type": "Goods",
			"status": "Draft",
			"workflow_state": "Approved",
			"approval_status": "Approved",
			"procuring_entity": entity,
			"fiscal_year": "2026-2027",
			"currency": currency,
			"request_date": "2026-04-01",
			"priority_level": "Medium",
			"budget_reservation_status": "None",
			"planning_status": "Unplanned",
			"items": [
				{
					"doctype": "Purchase Requisition Item",
					"item_description": "Line",
					"quantity": 10.0,
					"estimated_unit_cost": 10.0,
				}
			],
		}
	).insert(ignore_permissions=True)


class TestProcurementPlanScriptReports(FrappeTestCase):
	def test_each_script_report_execute_returns_columns_and_data(self):
		for mod_path in _REPORT_MODULES:
			mod = importlib.import_module(mod_path)
			cols, data = mod.execute({})
			self.assertTrue(isinstance(cols, list) and len(cols) > 0, msg=mod_path)
			self.assertIsInstance(data, list, msg=mod_path)
			filters = mod.get_filters()
			self.assertIsInstance(filters, list)


class TestProcurementPlanPipeline022(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pp022)
		self.entity = _make_entity("_KT_PP022_PE").insert()
		self.period = _bcp("_KT_PP022_BCP", self.entity.name).insert()
		self.plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PP022_PP",
				"plan_title": "PP022 integration plan",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pp022)
		super().tearDown()

	def test_consolidation_revision_then_tender_eligible_and_report_row(self):
		pr = _approved_pr(self.entity.name, self.currency, "_KT_PP022_PR1")
		out = consolidate_requisitions_into_plan(
			self.plan.name,
			[{"purchase_requisition": pr.name}],
			mode="separate",
		)
		self.assertEqual(len(out["plan_items_created"]), 1)
		ppi_name = out["plan_items_created"][0]

		frappe.db.set_value(
			PP,
			self.plan.name,
			{
				"workflow_state": "Active",
				"status": "Active",
				"approval_status": "Approved",
			},
			update_modified=False,
		)
		frappe.db.set_value(
			PPI,
			ppi_name,
			{
				"status": "Active",
				"fragmentation_alert_status": "Clear",
			},
			update_modified=False,
		)

		rev = frappe.get_doc(
			{
				"doctype": PPR,
				"revision_business_id": "_KT_PP022_REV1",
				"source_procurement_plan": self.plan.name,
				"revision_type": "Budget",
				"revision_reason": "PP022 pipeline test",
				"requested_by": frappe.session.user,
				"requested_on": "2026-04-10 09:00:00",
				"status": "Approved",
				"approved_by": frappe.session.user,
				"approved_on": "2026-04-10 12:00:00",
				"revision_lines": [
					{
						"doctype": PPRL,
						"affected_plan_item": ppi_name,
						"action_type": "Update",
						"change_amount": 50,
					}
				],
			}
		)
		rev.insert(ignore_permissions=True)
		apply_res = apply_procurement_plan_revision(rev.name)
		self.assertEqual(apply_res["lines_applied"], 1)

		meta = get_plan_item_tender_eligibility(ppi_name)
		self.assertTrue(meta.get("eligible"), msg=meta.get("reasons"))

		ppi = frappe.get_doc(PPI, ppi_name)
		self.assertEqual(flt(ppi.estimated_amount), 150.0)

		tender_mod = importlib.import_module(_REPORT_MODULES[3])
		_cols, rows = tender_mod.execute({})
		self.assertTrue(any(r[0] == ppi_name for r in rows))

	def test_fragmentation_alert_report_lists_open_alert(self):
		frappe.get_doc(
			{
				"doctype": PFA,
				"business_id": "_KT_PP022_FA1",
				"procurement_plan": self.plan.name,
				"alert_type": "Similar Demand Split",
				"severity": "High",
				"risk_score": 0.5,
				"rule_trigger_summary": "PP022 report scaffolding.",
				"status": "Open",
				"raised_on": "2026-05-01 09:00:00",
				"raised_by_system": 1,
			}
		).insert(ignore_permissions=True)

		fa_mod = importlib.import_module(_REPORT_MODULES[4])
		_cols, rows = fa_mod.execute({"procuring_entity": self.entity.name})
		self.assertTrue(any((r[1] or "") == "_KT_PP022_FA1" for r in rows))
