# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-086–093: Procurement Contract chain DocTypes (avoids ERPNext CRM **Contract** name)."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

PC = "Procurement Contract"
PCP = "Procurement Contract Party"
PCM = "Procurement Contract Milestone"
PCD = "Procurement Contract Deliverable"
PCV = "Procurement Contract Variation"
PCAR = "Procurement Contract Approval Record"
PCSR = "Procurement Contract Signing Record"
PCSE = "Procurement Contract Status Event"
AD = "Award Decision"
TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
ERPT = "Evaluation Report"
PREFIX = "_KT_CON086"


def _cleanup_con086():
	frappe.flags.allow_contract_status_event_delete = True
	for row in frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for dt in (PCSE, PCSR, PCAR, PCV, PCD, PCM, PCP):
			for ch in frappe.get_all(dt, filters={"procurement_contract": row}, pluck="name") or []:
				frappe.delete_doc(dt, ch, force=True, ignore_permissions=True)
		frappe.delete_doc(PC, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AD, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ERPT, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(ERPT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete("Budget Control Period", {"name": ("like", f"{PREFIX}%")})
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE"})
	frappe.flags.allow_contract_status_event_delete = False


class TestContractDocTypes086to093(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_con086)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_con086)
		super().tearDown()

	def _minimal_award(self, suffix: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "CON086",
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
				"doctype": ES,
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
				"doctype": ERPT,
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
				"quoted_total_amount": 5000,
			}
		).insert(ignore_permissions=True)
		ad = frappe.get_doc(
			{
				"doctype": AD,
				"business_id": f"{PREFIX}_AD{suffix}",
				"tender": t.name,
				"evaluation_session": e.name,
				"evaluation_report": rep.name,
				"decision_justification": "Award for contract tests.",
				"recommended_bid_submission": b.name,
				"recommended_supplier": f"S-{suffix}",
				"recommended_amount": 5000,
				"approved_bid_submission": b.name,
				"approved_supplier": f"S-{suffix}",
				"approved_amount": 5000,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		return t, e, rep, b, ad

	def test_KT_CON086_procurement_contract_valid(self):
		t, e, _rep, b, ad = self._minimal_award("1")
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC1",
				"contract_title": "Test contract",
				"award_decision": ad.name,
				"tender": t.name,
				"procurement_plan_item": None,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-1",
				"procuring_entity": self.entity.name,
				"contract_value": 5000,
				"currency": self.currency,
				"contract_start_date": getdate(nowdate()),
				"contract_end_date": add_days(getdate(nowdate()), 365),
			}
		).insert(ignore_permissions=True)
		self.assertTrue(pc.display_label)

	def test_KT_CON087_party(self):
		t, e, _r, b, ad = self._minimal_award("2")
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC2",
				"contract_title": "T",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-2",
				"procuring_entity": self.entity.name,
				"contract_value": 1,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		p = frappe.get_doc(
			{
				"doctype": PCP,
				"procurement_contract": pc.name,
				"party_type": "Entity",
				"party_name": "Entity party",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(p.display_label)

	def test_KT_CON088_milestone_dates(self):
		t, e, _r, b, ad = self._minimal_award("3")
		sd = getdate(nowdate())
		ed = add_days(sd, 30)
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC3",
				"contract_title": "T",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-3",
				"procuring_entity": self.entity.name,
				"contract_value": 1,
				"currency": self.currency,
				"contract_start_date": sd,
				"contract_end_date": ed,
			}
		).insert(ignore_permissions=True)
		m = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M3",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "M1",
				"planned_due_date": add_days(ed, 1),
				"status": "Planned",
			}
		)
		self.assertRaises(frappe.ValidationError, m.insert, ignore_permissions=True)

	def test_KT_CON089_deliverable_milestone_contract(self):
		t, e, _r, b, ad = self._minimal_award("4")
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC4",
				"contract_title": "T",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-4",
				"procuring_entity": self.entity.name,
				"contract_value": 1,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		pc2 = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC4B",
				"contract_title": "Other",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-4",
				"procuring_entity": self.entity.name,
				"contract_value": 2,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		m = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M4",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "M",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		d = frappe.get_doc(
			{
				"doctype": PCD,
				"procurement_contract": pc2.name,
				"contract_milestone": m.name,
				"deliverable_title": "D",
				"status": "Planned",
			}
		)
		self.assertRaises(frappe.ValidationError, d.insert, ignore_permissions=True)

	def test_KT_CON090_variation(self):
		t, e, _r, b, ad = self._minimal_award("5")
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC5",
				"contract_title": "T",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-5",
				"procuring_entity": self.entity.name,
				"contract_value": 100,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		v = frappe.get_doc(
			{
				"doctype": PCV,
				"business_id": f"{PREFIX}_V5",
				"procurement_contract": pc.name,
				"variation_no": 1,
				"variation_type": "Value",
				"reason": "Test",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(v.display_label)

	def test_KT_CON091_approval_record(self):
		t, e, _r, b, ad = self._minimal_award("6")
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC6",
				"contract_title": "T",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-6",
				"procuring_entity": self.entity.name,
				"contract_value": 1,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		a = frappe.get_doc(
			{
				"doctype": PCAR,
				"procurement_contract": pc.name,
				"workflow_step": "L1",
				"approver_user": "Administrator",
				"action_type": "Comment",
				"action_datetime": frappe.utils.now_datetime(),
				"decision_level": "Entity",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(a.display_label)

	def test_KT_CON092_signing_record(self):
		t, e, _r, b, ad = self._minimal_award("7")
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC7",
				"contract_title": "T",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-7",
				"procuring_entity": self.entity.name,
				"contract_value": 1,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		s = frappe.get_doc(
			{
				"doctype": PCSR,
				"procurement_contract": pc.name,
				"signing_method": "Digital",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(s.display_label)

	def test_KT_CON093_status_event_append_only(self):
		t, e, _r, b, ad = self._minimal_award("8")
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC8",
				"contract_title": "T",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-8",
				"procuring_entity": self.entity.name,
				"contract_value": 1,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		ev = frappe.get_doc(
			{
				"doctype": PCSE,
				"procurement_contract": pc.name,
				"event_type": "Other",
				"event_datetime": frappe.utils.now_datetime(),
				"summary": "e",
			}
		).insert(ignore_permissions=True)
		ev.summary = "changed"
		self.assertRaises(frappe.ValidationError, ev.save, ignore_permissions=True)
