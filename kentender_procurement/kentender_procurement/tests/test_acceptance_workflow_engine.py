# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-014: Acceptance Record workflow + policy resolution."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.services.acceptance_decision_services import submit_acceptance_decision
from kentender_procurement.services.acceptance_workflow_actions import (
	approve_acceptance,
	reject_acceptance,
	submit_acceptance_for_approval,
)

AD = "Award Decision"
AR = "Acceptance Record"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Report"
EVAL = "Evaluation Session"
IMT = "Inspection Method Template"
IR = "Inspection Record"
IPL = "Inspection Parameter Line"
PC = "Procurement Contract"
TENDER = "Tender"
PREFIX = "_KT_ACCWF"


def _cleanup_accwf():
	for pol_code, tpl_code in (
		(f"{PREFIX}_POL_S", f"{PREFIX}_TPL_S"),
		(f"{PREFIX}_POL_C", f"{PREFIX}_TPL_C"),
	):
		for name in frappe.get_all(
			"KenTender Approval Route Instance",
			filters={"reference_docname": ("like", f"{PREFIX}%")},
			pluck="name",
		):
			try:
				frappe.delete_doc("KenTender Approval Route Instance", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.delete("KenTender Approval Action", {"reference_docname": ("like", f"{PREFIX}%")})
		if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
			frappe.delete_doc("KenTender Workflow Policy", pol_code, force=True, ignore_permissions=True)
		if frappe.db.exists("KenTender Approval Route Template", {"template_code": tpl_code}):
			frappe.delete_doc("KenTender Approval Route Template", tpl_code, force=True, ignore_permissions=True)

	frappe.flags.allow_inspection_status_event_delete = True
	for irn in frappe.get_all(IR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for dt in ("Inspection Status Event", AR):
			for row in frappe.get_all(dt, filters={"inspection_record": irn}, pluck="name") or []:
				frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(AR, filters={"inspection_record": irn}, pluck="name") or []:
			frappe.delete_doc(AR, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(IPL, filters={"inspection_record": irn}, pluck="name") or []:
			frappe.delete_doc(IPL, row, force=True, ignore_permissions=True)
		frappe.delete_doc(IR, irn, force=True, ignore_permissions=True)
	for row in frappe.get_all(IMT, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(IMT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(PC, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AD, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(EVAL, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(EVAL, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	frappe.db.delete("Budget Control Period", {"name": ("like", f"{PREFIX}%")})
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE"})
	frappe.flags.allow_inspection_status_event_delete = False


def _ensure_policies() -> None:
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": f"{PREFIX}_POL_S"}):
		return
	for tpl_code, step_name, pol_code, tmax, tmin, evo in (
		(f"{PREFIX}_TPL_S", "SimpleGoods", f"{PREFIX}_POL_S", 10000.0, None, 10),
		(f"{PREFIX}_TPL_C", "ComplexTech", f"{PREFIX}_POL_C", None, 10000.01, 20),
	):
		tpl = frappe.get_doc(
			{
				"doctype": "KenTender Approval Route Template",
				"template_code": tpl_code,
				"template_name": step_name,
				"object_type": AR,
				"steps": [
					{
						"doctype": "KenTender Approval Route Template Step",
						"step_order": 1,
						"step_name": step_name,
						"actor_type": "Role",
						"role_required": "System Manager",
					}
				],
			}
		)
		tpl.insert()
		pol = frappe.get_doc(
			{
				"doctype": "KenTender Workflow Policy",
				"policy_code": pol_code,
				"applies_to_doctype": AR,
				"linked_template": tpl.name,
				"active": 1,
				"evaluation_order": evo,
			}
		)
		if tmax is not None:
			pol.threshold_max = tmax
		if tmin is not None:
			pol.threshold_min = tmin
		pol.insert()


class TestAcceptanceWorkflowEngine(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_accwf)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_accwf)
		super().tearDown()

	def _pc_and_ir(self, suffix: str, *, bid_amount: float):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "ACCWF",
				"tender_number": f"{PREFIX}_TN{suffix}",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		s = frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": f"{PREFIX}_S{suffix}",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)
		r = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": f"{PREFIX}_R{suffix}",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		e = frappe.get_doc(
			{
				"doctype": EVAL,
				"business_id": f"{PREFIX}_E{suffix}",
				"tender": t.name,
				"procuring_entity": self.entity.name,
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
				"business_id": f"{PREFIX}_ER{suffix}",
				"evaluation_session": e.name,
				"tender": t.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		b = frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": f"{PREFIX}_B{suffix}",
				"tender": t.name,
				"supplier": f"S-{suffix}",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
				"quoted_total_amount": bid_amount,
			}
		).insert(ignore_permissions=True)
		ad = frappe.get_doc(
			{
				"doctype": AD,
				"business_id": f"{PREFIX}_AD{suffix}",
				"tender": t.name,
				"evaluation_session": e.name,
				"evaluation_report": rep.name,
				"decision_justification": "accwf",
				"recommended_bid_submission": b.name,
				"recommended_supplier": f"S-{suffix}",
				"recommended_amount": bid_amount,
				"approved_bid_submission": b.name,
				"approved_supplier": f"S-{suffix}",
				"approved_amount": bid_amount,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC{suffix}",
				"contract_title": "accwf contract",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-{suffix}",
				"procuring_entity": self.entity.name,
				"contract_value": bid_amount,
				"currency": self.currency,
				"contract_start_date": getdate(nowdate()),
			}
		).insert(ignore_permissions=True)
		tpl = frappe.get_doc(
			{
				"doctype": IMT,
				"template_code": f"{PREFIX}_IMT{suffix}",
				"template_name": "Tpl",
				"inspection_domain": "General",
				"applicable_contract_type": "Goods",
				"inspection_method_type": "Parameter Testing",
				"default_pass_logic": "All Mandatory Pass",
				"active": 1,
			}
		).insert(ignore_permissions=True)
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IR{suffix}",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "accwf inspection",
				"inspection_method_type": "Parameter Testing",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Completed",
				"workflow_state": "Completed",
				"inspection_result": "Pass",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "M1",
				"parameter_name": "Mandatory",
				"parameter_category": "Dimensional",
				"tolerance_type": "MinMax",
				"expected_min_value": 0.0,
				"expected_max_value": 10.0,
				"mandatory_for_acceptance": 1,
				"status": "Passed",
			}
		).insert(ignore_permissions=True)
		return ir, bid_amount

	def test_policy_resolves_simple_vs_complex_template(self):
		_ensure_policies()
		ir_low, amt_low = self._pc_and_ir("L", bid_amount=1000.0)
		out_low = submit_acceptance_decision(
			ir_low.name,
			{
				"business_id": f"{PREFIX}_ACC_LOW",
				"acceptance_decision": "Accepted",
				"use_engine_workflow": True,
				"accepted_value_amount": amt_low,
			},
		)
		submit_acceptance_for_approval(out_low["name"])
		inst_low = frappe.db.get_value(
			"KenTender Approval Route Instance",
			{"reference_docname": out_low["name"], "status": "Active"},
			["template_used", "name"],
			as_dict=True,
		)
		tpl_name_simple = frappe.db.get_value(
			"KenTender Approval Route Template", {"template_code": f"{PREFIX}_TPL_S"}, "name"
		)
		self.assertEqual(inst_low.template_used, tpl_name_simple)

		ir_hi, amt_hi = self._pc_and_ir("H", bid_amount=50000.0)
		out_hi = submit_acceptance_decision(
			ir_hi.name,
			{
				"business_id": f"{PREFIX}_ACC_HI",
				"acceptance_decision": "Accepted",
				"use_engine_workflow": True,
				"accepted_value_amount": amt_hi,
			},
		)
		submit_acceptance_for_approval(out_hi["name"])
		inst_hi = frappe.db.get_value(
			"KenTender Approval Route Instance",
			{"reference_docname": out_hi["name"], "status": ("in", ("Active", "Completed"))},
			["template_used"],
			as_dict=True,
		)
		tpl_name_complex = frappe.db.get_value(
			"KenTender Approval Route Template", {"template_code": f"{PREFIX}_TPL_C"}, "name"
		)
		self.assertEqual(inst_hi.template_used, tpl_name_complex)

	def test_approve_and_reject(self):
		_ensure_policies()
		ir, amt = self._pc_and_ir("R", bid_amount=2000.0)
		out = submit_acceptance_decision(
			ir.name,
			{
				"business_id": f"{PREFIX}_ACC_R",
				"acceptance_decision": "Accepted",
				"use_engine_workflow": True,
				"accepted_value_amount": amt,
			},
		)
		submit_acceptance_for_approval(out["name"])
		approve_acceptance(out["name"])
		ar = frappe.get_doc(AR, out["name"])
		self.assertEqual(ar.workflow_state, "Approved")
		self.assertEqual(frappe.db.get_value(IR, ir.name, "acceptance_status"), "Accepted")

		ir2, amt2 = self._pc_and_ir("J", bid_amount=2000.0)
		out2 = submit_acceptance_decision(
			ir2.name,
			{
				"business_id": f"{PREFIX}_ACC_J",
				"acceptance_decision": "Rejected",
				"use_engine_workflow": True,
				"accepted_value_amount": amt2,
				"decision_reason": "no",
			},
		)
		submit_acceptance_for_approval(out2["name"])
		reject_acceptance(out2["name"])
		self.assertEqual(frappe.db.get_value(AR, out2["name"], "workflow_state"), "Rejected")

	def test_mandatory_failure_still_blocks_acceptance_decision(self):
		_ensure_policies()
		ir, amt = self._pc_and_ir("M", bid_amount=1000.0)
		frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "M2",
				"parameter_name": "Bad",
				"parameter_category": "Dimensional",
				"tolerance_type": "MinMax",
				"expected_min_value": 0.0,
				"expected_max_value": 10.0,
				"mandatory_for_acceptance": 1,
				"status": "Failed",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			submit_acceptance_decision(
				ir.name,
				{
					"business_id": f"{PREFIX}_ACC_BLK",
					"acceptance_decision": "Accepted",
					"use_engine_workflow": True,
					"accepted_value_amount": amt,
				},
			)

	def test_direct_workflow_save_blocked(self):
		_ensure_policies()
		ir, amt = self._pc_and_ir("P", bid_amount=1000.0)
		out = submit_acceptance_decision(
			ir.name,
			{
				"business_id": f"{PREFIX}_ACC_P",
				"acceptance_decision": "Accepted",
				"use_engine_workflow": True,
				"accepted_value_amount": amt,
			},
		)
		submit_acceptance_for_approval(out["name"])
		ar = frappe.get_doc(AR, out["name"])
		with self.assertRaises(frappe.ValidationError):
			ar.workflow_state = "Approved"
			ar.save(ignore_permissions=True)

	def test_mutation_context_allows_save(self):
		_ensure_policies()
		ir, amt = self._pc_and_ir("Q", bid_amount=1000.0)
		out = submit_acceptance_decision(
			ir.name,
			{
				"business_id": f"{PREFIX}_ACC_Q",
				"acceptance_decision": "Accepted",
				"use_engine_workflow": True,
				"accepted_value_amount": amt,
			},
		)
		submit_acceptance_for_approval(out["name"])
		ar = frappe.get_doc(AR, out["name"])
		with workflow_mutation_context():
			ar.workflow_state = "Draft"
			ar.status = "Draft"
			ar.save(ignore_permissions=True)
