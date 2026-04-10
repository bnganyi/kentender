# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-052–055: opening precondition, candidates, execution, lock."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.opening_candidate_bids import resolve_candidate_bids_for_tender
from kentender_procurement.services.opening_execution import execute_bid_opening
from kentender_procurement.services.opening_post_opening import lock_opening_register_and_finalize
from kentender_procurement.services.opening_preconditions import validate_opening_preconditions

TENDER = "Tender"
BS = "Bid Submission"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
BOEL = "Bid Opening Event Log"
BCP = "Budget Control Period"


def _cleanup_opn():
	for sn in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_OPN_%")}, pluck="name") or []:
		frappe.db.delete(BOEL, {"bid_opening_session": sn})
	for sn in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_OPN_%")}, pluck="name") or []:
		for rn in frappe.get_all(BOR, filters={"bid_opening_session": sn}, pluck="name") or []:
			frappe.delete_doc(BOR, rn, force=True, ignore_permissions=True)
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_OPN_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_OPN_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_OPN_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_OPN_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_OPN_PE"})


class TestOpeningServices052to055(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_opn)
		self.entity = _make_entity("_KT_OPN_PE").insert()
		self.period = _bcp("_KT_OPN_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_opn)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "OPN tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _published_tender_past_deadline(self, name: str):
		t = self._tender(name)
		past = add_days(now_datetime(), -1)
		frappe.db.set_value(
			TENDER,
			t.name,
			{
				"workflow_state": "Published",
				"status": "Active",
				"approval_status": "Published",
				"submission_status": "Open",
				"submission_deadline": past,
				"opening_datetime": add_days(now_datetime(), 1),
			},
			update_modified=False,
		)
		return t

	def _session(self, tender_name: str):
		return frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": f"_KT_OPN_S_{tender_name}",
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)

	def _draft_bid(self, tender_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": BS,
				"business_id": business_id,
				"tender": tender_name,
				"supplier": "OPN-SUP",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)

	def test_preconditions_pass(self):
		t = self._published_tender_past_deadline("_KT_OPN_T1")
		s = self._session(t.name)
		out = validate_opening_preconditions(t.name, s.name)
		self.assertTrue(out.get("ok"))

	def test_preconditions_fail_before_deadline(self):
		t = self._tender("_KT_OPN_T2")
		future = add_days(now_datetime(), 2)
		frappe.db.set_value(
			TENDER,
			t.name,
			{
				"workflow_state": "Published",
				"status": "Active",
				"approval_status": "Published",
				"submission_status": "Open",
				"submission_deadline": future,
			},
			update_modified=False,
		)
		s = self._session(t.name)
		out = validate_opening_preconditions(t.name, s.name)
		self.assertFalse(out.get("ok"))

	def test_candidate_resolution(self):
		t = self._published_tender_past_deadline("_KT_OPN_T3")
		b = self._draft_bid(t.name, "_KT_OPN_B1")
		frappe.db.set_value(
			BS,
			b.name,
			{
				"workflow_state": "Submitted",
				"status": "Submitted",
				"is_final_submission": 1,
				"active_submission_flag": 1,
				"sealed_status": "Sealed",
				"submitted_on": now_datetime(),
			},
			update_modified=False,
		)
		res = resolve_candidate_bids_for_tender(t.name)
		self.assertEqual(len(res.get("candidates")), 1)

	def test_execute_and_lock(self):
		t = self._published_tender_past_deadline("_KT_OPN_T4")
		s = self._session(t.name)
		b = self._draft_bid(t.name, "_KT_OPN_B2")
		frappe.db.set_value(
			BS,
			b.name,
			{
				"workflow_state": "Submitted",
				"status": "Submitted",
				"is_final_submission": 1,
				"active_submission_flag": 1,
				"sealed_status": "Sealed",
				"submitted_on": now_datetime(),
			},
			update_modified=False,
		)
		out = execute_bid_opening(s.name, actor_user="Administrator")
		self.assertTrue(out.get("register"))
		reg = frappe.db.get_value(BOR, out.get("register"), ["is_locked", "status"], as_dict=True)
		self.assertEqual(int(reg.get("is_locked") or 0), 1)
		self.assertEqual(reg.get("status"), "Locked")
		b.reload()
		self.assertEqual(b.workflow_state, "Opened")

	def test_lock_idempotent_safe(self):
		t = self._published_tender_past_deadline("_KT_OPN_T5")
		s = self._session(t.name)
		reg = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": "_KT_OPN_RG",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Generated",
			}
		).insert(ignore_permissions=True)
		lock_opening_register_and_finalize(reg.name, s.name, actor_user="Administrator")
		r2 = frappe.db.get_value(BOR, reg.name, "is_locked")
		self.assertEqual(int(r2 or 0), 1)
