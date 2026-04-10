# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-111: create_inspection_for_contract_scope."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.inspection_from_contract_scope import create_inspection_for_contract_scope

AD = "Award Decision"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ERPT = "Evaluation Report"
ES = "Evaluation Session"
IMT = "Inspection Method Template"
IR = "Inspection Record"
PC = "Procurement Contract"
PCD = "Procurement Contract Deliverable"
PCM = "Procurement Contract Milestone"
TENDER = "Tender"
PREFIX = "_KT_INSP111"


def _cleanup():
	for row in frappe.get_all(IR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(IR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(IMT, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(IMT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for dt in (PCD, PCM):
			for ch in frappe.get_all(dt, filters={"procurement_contract": row}, pluck="name") or []:
				frappe.delete_doc(dt, ch, force=True, ignore_permissions=True)
		frappe.delete_doc(PC, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AD, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ERPT, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(ERPT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
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


class TestInspectionFromContractScope111(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup)
		super().tearDown()

	def _pc_and_tpl(self, suf: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suf}",
				"business_id": f"{PREFIX}_T{suf}-BIZ",
				"title": "T",
				"tender_number": f"{PREFIX}_TN{suf}",
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
				"business_id": f"{PREFIX}_S{suf}",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)
		r = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": f"{PREFIX}_R{suf}",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		e = frappe.get_doc(
			{
				"doctype": ES,
				"business_id": f"{PREFIX}_E{suf}",
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
				"doctype": ERPT,
				"business_id": f"{PREFIX}_ER{suf}",
				"evaluation_session": e.name,
				"tender": t.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		b = frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": f"{PREFIX}_B{suf}",
				"tender": t.name,
				"supplier": f"S-{suf}",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
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
				"business_id": f"{PREFIX}_AD{suf}",
				"tender": t.name,
				"evaluation_session": e.name,
				"evaluation_report": rep.name,
				"decision_justification": "x",
				"recommended_bid_submission": b.name,
				"recommended_supplier": f"S-{suf}",
				"recommended_amount": 5000,
				"approved_bid_submission": b.name,
				"approved_supplier": f"S-{suf}",
				"approved_amount": 5000,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC{suf}",
				"contract_title": f"Contract {suf}",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-{suf}",
				"procuring_entity": self.entity.name,
				"contract_value": 5000,
				"currency": self.currency,
				"contract_start_date": getdate(nowdate()),
			}
		).insert(ignore_permissions=True)
		tpl_code = f"{PREFIX}_TPL{suf}"
		tpl = frappe.get_doc(
			{
				"doctype": IMT,
				"template_code": tpl_code,
				"template_name": "Template",
				"inspection_domain": "General",
				"applicable_contract_type": "Goods",
				"inspection_method_type": "Checklist",
				"default_pass_logic": "All Mandatory Pass",
				"requires_sampling": 1,
			}
		).insert(ignore_permissions=True)
		return pc, tpl

	def test_KT_INSP111_contract_wide(self):
		pc, tpl = self._pc_and_tpl("A")
		r = create_inspection_for_contract_scope(
			pc.name,
			None,
			"contract_wide",
			inspection_method_template=tpl.name,
			business_id=f"{PREFIX}_IRW",
		)
		doc = frappe.get_doc(IR, r["name"])
		self.assertEqual(doc.inspection_scope_type, "Contract Wide")
		self.assertEqual(doc.contract, pc.name)
		self.assertEqual(doc.procuring_entity, self.entity.name)
		self.assertEqual(int(doc.requires_sampling or 0), 1)
		self.assertEqual(doc.acceptance_status, "Not Applicable")

	def test_KT_INSP111_milestone(self):
		pc, tpl = self._pc_and_tpl("B")
		m = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M1",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "Gate 1",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		r = create_inspection_for_contract_scope(
			pc.name,
			m.name,
			"milestone",
			inspection_method_template=tpl.name,
			business_id=f"{PREFIX}_IRM",
		)
		doc = frappe.get_doc(IR, r["name"])
		self.assertEqual(doc.inspection_scope_type, "Milestone")
		self.assertEqual(doc.contract_milestone, m.name)

	def test_KT_INSP111_deliverable(self):
		pc, tpl = self._pc_and_tpl("C")
		d = frappe.get_doc(
			{
				"doctype": PCD,
				"procurement_contract": pc.name,
				"deliverable_title": "Widgets",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		r = create_inspection_for_contract_scope(
			pc.name,
			d.name,
			"deliverable",
			inspection_method_template=tpl.name,
			business_id=f"{PREFIX}_IRD",
		)
		doc = frappe.get_doc(IR, r["name"])
		self.assertEqual(doc.inspection_scope_type, "Deliverable")
		self.assertEqual(doc.contract_deliverable, d.name)

	def test_KT_INSP111_milestone_and_deliverable(self):
		pc, tpl = self._pc_and_tpl("D")
		m = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M2",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "M",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		d = frappe.get_doc(
			{
				"doctype": PCD,
				"procurement_contract": pc.name,
				"contract_milestone": m.name,
				"deliverable_title": "Batch A",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		r = create_inspection_for_contract_scope(
			pc.name,
			d.name,
			"milestone_and_deliverable",
			inspection_method_template=tpl.name,
			business_id=f"{PREFIX}_IRMD",
		)
		doc = frappe.get_doc(IR, r["name"])
		self.assertEqual(doc.inspection_scope_type, "Milestone and Deliverable")
		self.assertEqual(doc.contract_milestone, m.name)
		self.assertEqual(doc.contract_deliverable, d.name)

	def test_KT_INSP111_milestone_wrong_contract_blocked(self):
		pc1, tpl1 = self._pc_and_tpl("E1")
		pc2, tpl2 = self._pc_and_tpl("E2")
		m = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M3",
				"procurement_contract": pc1.name,
				"milestone_no": 1,
				"title": "X",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		self.assertRaises(
			frappe.ValidationError,
			create_inspection_for_contract_scope,
			pc2.name,
			m.name,
			"milestone",
			inspection_method_template=tpl2.name,
			business_id=f"{PREFIX}_BAD",
		)

	def test_KT_INSP111_template_required(self):
		pc, _tpl = self._pc_and_tpl("F")
		self.assertRaises(
			frappe.ValidationError,
			create_inspection_for_contract_scope,
			pc.name,
			None,
			"contract_wide",
			inspection_method_template=None,
		)
