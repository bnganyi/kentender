# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-049: Bid Opening Attendance."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOA = "Bid Opening Attendance"
BCP = "Budget Control Period"


def _cleanup_boa049():
	sessions = frappe.get_all(BOS, filters={"business_id": ("like", "_KT_BOA049_%")}, pluck="name") or []
	for sn in sessions:
		for row in frappe.get_all(BOA, filters={"bid_opening_session": sn}, pluck="name") or []:
			frappe.delete_doc(BOA, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_BOA049_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BOA049_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_BOA049_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BOA049_PE"})


class TestBidOpeningAttendance049(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_boa049)
		self.entity = _make_entity("_KT_BOA049_PE").insert()
		self.period = _bcp("_KT_BOA049_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_boa049)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "BOA049 tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _session(self, tender_name: str):
		return frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": f"_KT_BOA049_{tender_name}",
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)

	def test_internal_attendee_with_user(self):
		t = self._tender("_KT_BOA049_T1")
		s = self._session(t.name)
		doc = frappe.get_doc(
			{
				"doctype": BOA,
				"bid_opening_session": s.name,
				"attendee_user": "Administrator",
				"attendee_role_type": "Committee Chair",
				"attendance_status": "Present",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)

	def test_external_attendee_with_name_only(self):
		t = self._tender("_KT_BOA049_T2")
		s = self._session(t.name)
		doc = frappe.get_doc(
			{
				"doctype": BOA,
				"bid_opening_session": s.name,
				"attendee_name": "External Witness Ltd",
				"attendee_role_type": "External Witness",
				"attendance_status": "Present",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)

	def test_blocks_neither_user_nor_name(self):
		t = self._tender("_KT_BOA049_T3")
		s = self._session(t.name)
		doc = frappe.get_doc(
			{
				"doctype": BOA,
				"bid_opening_session": s.name,
				"attendee_role_type": "Observer",
				"attendance_status": "Invited",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
