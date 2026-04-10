# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-027: Tender Approval Record."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TAR = "Tender Approval Record"
BCP = "Budget Control Period"


def _cleanup_tar027():
	# Append-only records block delete_doc/on_trash; use direct DB delete for test cleanup.
	for row in frappe.get_all(TAR, filters={"tender": ("like", "_KT_TAR027_%")}, pluck="name") or []:
		frappe.db.delete(TAR, {"name": row})
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TAR027_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_TAR027_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TAR027_PE"})


class TestTenderApprovalRecord(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tar027)
		self.entity = _make_entity("_KT_TAR027_PE").insert()
		self.period = _bcp("_KT_TAR027_BCP", self.entity.name).insert()
		self.tender = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": "_KT_TAR027_T1",
				"business_id": "_KT_TAR027_B1",
				"title": "TAR tender",
				"tender_number": "TAR-027-001",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tar027)
		super().tearDown()

	def _tar_doc(self, **kwargs):
		base = {
			"doctype": TAR,
			"tender": self.tender.name,
			"workflow_step": "Authority",
			"decision_level": "L1",
			"approver_user": frappe.session.user,
			"action_type": "Approve",
			"action_datetime": "2026-04-02 10:00:00",
			"comments": "OK",
		}
		base.update(kwargs)
		return frappe.get_doc(base)

	def test_valid_create_and_linkage(self):
		rec = self._tar_doc()
		rec.insert(ignore_permissions=True)
		self.assertTrue(rec.name)
		self.assertEqual(rec.tender, self.tender.name)
		self.assertIn(self.tender.name, rec.display_label or "")
		self.assertIn("Authority", rec.display_label or "")
		rec.reload()
		self.assertEqual(rec.action_type, "Approve")

	def test_append_only_update_blocked(self):
		rec = self._tar_doc(workflow_step="Finance", action_type="Reject", action_datetime="2026-04-02 11:00:00")
		rec.insert(ignore_permissions=True)
		rec.comments = "changed"
		self.assertRaises(frappe.ValidationError, rec.save)

	def test_append_only_delete_blocked(self):
		rec = self._tar_doc(
			workflow_step="HOD",
			action_type="Recommend",
			action_datetime="2026-04-02 12:00:00",
		)
		rec.insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, TAR, rec.name, force=True)

	def test_invalid_tender_blocked(self):
		doc = self._tar_doc(tender="NONEXISTENT_TENDER_TAR027")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_invalid_exception_record_blocked(self):
		doc = self._tar_doc(exception_record="NONEXISTENT-EX-TAR027")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
