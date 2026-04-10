# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-073–079: Award chain DocTypes validation."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
ERPT = "Evaluation Report"
AD = "Award Decision"
ADR = "Award Deviation Record"
SSP = "Standstill Period"
AN = "Award Notification"
AAR = "Award Approval Record"
ARR = "Award Return Record"
BCP = "Budget Control Period"
PREFIX = "_KT_AWD07"


def _cleanup_awd07():
	for ad_name in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for dt in (ARR, AN, AAR, ADR, SSP):
			for row in frappe.get_all(dt, filters={"award_decision": ad_name}, pluck="name") or []:
				frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
		frappe.delete_doc(AD, ad_name, force=True, ignore_permissions=True)
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
	frappe.db.delete(BCP, {"name": ("like", f"{PREFIX}%")})
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE"})


class TestAwardDocTypes073to079(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_awd07)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_awd07)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "AWD07 tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _opening_session(self, tender_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": business_id,
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)

	def _register(self, tender_name: str, session_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": business_id,
				"tender": tender_name,
				"bid_opening_session": session_name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def _evaluation_session(self, tender_name: str, bos_name: str, bor_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": ES,
				"business_id": business_id,
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"opening_session": bos_name,
				"opening_register": bor_name,
				"evaluation_mode": "Two Envelope",
				"conflict_clearance_status": "Pending",
			}
		).insert(ignore_permissions=True)

	def _report(self, business_id: str, evaluation_session: str, tender: str):
		return frappe.get_doc(
			{
				"doctype": ERPT,
				"business_id": business_id,
				"evaluation_session": evaluation_session,
				"tender": tender,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def _bid(self, tender_name: str, business_id: str, supplier: str):
		return frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": business_id,
				"tender": tender_name,
				"supplier": supplier,
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)

	def _minimal_chain(self, suffix: str):
		t = self._tender(f"{PREFIX}_T{suffix}")
		s = self._opening_session(t.name, f"{PREFIX}_S{suffix}")
		r = self._register(t.name, s.name, f"{PREFIX}_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"{PREFIX}_E{suffix}")
		rep = self._report(f"{PREFIX}_ER{suffix}", e.name, t.name)
		return t, e, rep

	def _award_base(self, t, e, rep, business_id: str, **extra):
		data = {
			"doctype": AD,
			"business_id": business_id,
			"tender": t.name,
			"evaluation_session": e.name,
			"evaluation_report": rep.name,
			"decision_justification": "Award aligns with evaluation outcome.",
			**extra,
		}
		return frappe.get_doc(data)

	def test_KT_AWD073_valid_award_decision(self):
		t, e, rep = self._minimal_chain("1")
		b = self._bid(t.name, f"{PREFIX}_B1", "AWD07-S1")
		doc = self._award_base(t, e, rep, f"{PREFIX}_AD1", recommended_bid_submission=b.name, recommended_supplier="AWD07-S1")
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertTrue(doc.display_label)

	def test_KT_AWD073_report_session_mismatch(self):
		t, e, rep = self._minimal_chain("2")
		t2 = self._tender(f"{PREFIX}_T2X")
		s2 = self._opening_session(t2.name, f"{PREFIX}_S2X")
		r2 = self._register(t2.name, s2.name, f"{PREFIX}_R2X")
		e2 = self._evaluation_session(t2.name, s2.name, r2.name, f"{PREFIX}_E2X")
		rep2 = self._report(f"{PREFIX}_ER2X", e2.name, t2.name)
		doc = self._award_base(t, e, rep2, f"{PREFIX}_AD2")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_KT_AWD073_negative_bid_count_blocked(self):
		t, e, rep = self._minimal_chain("3")
		doc = self._award_base(t, e, rep, f"{PREFIX}_AD3", responsive_bid_count=-1)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_KT_AWD073_outcome_line_bid_tender_mismatch(self):
		t, e, rep = self._minimal_chain("4")
		t_other = self._tender(f"{PREFIX}_TO")
		b_other = self._bid(t_other.name, f"{PREFIX}_BO", "AWD07-OTHER")
		doc = self._award_base(t, e, rep, f"{PREFIX}_AD4")
		doc.append(
			"outcome_lines",
			{"bid_submission": b_other.name, "supplier": "AWD07-OTHER", "outcome_type": "Unsuccessful"},
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_KT_AWD074_approval_record(self):
		t, e, rep = self._minimal_chain("5")
		ad = self._award_base(t, e, rep, f"{PREFIX}_AD5").insert(ignore_permissions=True)
		rec = frappe.get_doc(
			{
				"doctype": AAR,
				"award_decision": ad.name,
				"workflow_step": "L1",
				"decision_level": "Entity",
				"approver_user": "Administrator",
				"action_type": "Recommend",
				"action_datetime": now_datetime(),
			}
		).insert(ignore_permissions=True)
		self.assertTrue(rec.display_label)

	def test_KT_AWD075_deviation_bid_wrong_tender(self):
		t, e, rep = self._minimal_chain("6")
		ad = self._award_base(t, e, rep, f"{PREFIX}_AD6").insert(ignore_permissions=True)
		t_other = self._tender(f"{PREFIX}_T6O")
		b0 = self._bid(t_other.name, f"{PREFIX}_B6O", "X")
		b1 = self._bid(t.name, f"{PREFIX}_B6A", "A")
		b2 = self._bid(t.name, f"{PREFIX}_B6B", "B")
		dev = frappe.get_doc(
			{
				"doctype": ADR,
				"award_decision": ad.name,
				"recommended_bid_submission": b1.name,
				"approved_bid_submission": b0.name,
				"recommended_supplier": "A",
				"approved_supplier": "X",
				"deviation_type": "Different Bid",
				"deviation_reason": "Test mismatch bid tender.",
			}
		)
		self.assertRaises(frappe.ValidationError, dev.insert, ignore_permissions=True)

	def test_KT_AWD076_notification_tender_mismatch(self):
		t, e, rep = self._minimal_chain("7")
		ad = self._award_base(t, e, rep, f"{PREFIX}_AD7").insert(ignore_permissions=True)
		t_other = self._tender(f"{PREFIX}_T7O")
		b = self._bid(t.name, f"{PREFIX}_B7", "S7")
		n = frappe.get_doc(
			{
				"doctype": AN,
				"business_id": f"{PREFIX}_N7",
				"award_decision": ad.name,
				"tender": t_other.name,
				"supplier": "S7",
				"bid_submission": b.name,
				"notification_type": "Successful",
			}
		)
		self.assertRaises(frappe.ValidationError, n.insert, ignore_permissions=True)

	def test_KT_AWD077_standstill_end_before_start(self):
		t, e, rep = self._minimal_chain("8")
		ad = self._award_base(t, e, rep, f"{PREFIX}_AD8").insert(ignore_permissions=True)
		start = now_datetime()
		end = add_to_date(start, days=-1)
		sp = frappe.get_doc(
			{
				"doctype": SSP,
				"award_decision": ad.name,
				"start_datetime": start,
				"end_datetime": end,
			}
		)
		self.assertRaises(frappe.ValidationError, sp.insert, ignore_permissions=True)

	def test_KT_AWD079_return_record(self):
		t, e, rep = self._minimal_chain("9")
		ad = self._award_base(t, e, rep, f"{PREFIX}_AD9").insert(ignore_permissions=True)
		ret = frappe.get_doc(
			{
				"doctype": ARR,
				"award_decision": ad.name,
				"returned_by_user": "Administrator",
				"return_type": "Other",
				"return_reason": "Need clarification.",
				"returned_on": now_datetime(),
			}
		).insert(ignore_permissions=True)
		self.assertTrue(ret.display_label)

	def test_KT_AWD073_wrong_deviation_link_on_save(self):
		t1, e1, rep1 = self._minimal_chain("A")
		t2, e2, rep2 = self._minimal_chain("B")
		ad1 = self._award_base(t1, e1, rep1, f"{PREFIX}_ADA").insert(ignore_permissions=True)
		ad2 = self._award_base(t2, e2, rep2, f"{PREFIX}_ADB").insert(ignore_permissions=True)
		b1a = self._bid(t1.name, f"{PREFIX}_BAA", "SA")
		b1b = self._bid(t1.name, f"{PREFIX}_BAB", "SB")
		dev1 = frappe.get_doc(
			{
				"doctype": ADR,
				"award_decision": ad1.name,
				"recommended_bid_submission": b1a.name,
				"approved_bid_submission": b1b.name,
				"recommended_supplier": "SA",
				"approved_supplier": "SB",
				"deviation_type": "Different Bid",
				"deviation_reason": "R",
			}
		).insert(ignore_permissions=True)
		ad2.deviation_record = dev1.name
		self.assertRaises(frappe.ValidationError, ad2.save, ignore_permissions=True)
