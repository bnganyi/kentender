# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-020: apply procurement plan revision."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.procurement_plan_revision_apply import (
	AUDIT_REVISION_APPLIED,
	apply_procurement_plan_revision,
)

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PPR = "Procurement Plan Revision"
PPRL = "Procurement Plan Revision Line"
BCP = "Budget Control Period"


def _cleanup_ppr020():
	frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"reason": ("like", "%_KT_PPR020%")})
	for row in frappe.get_all(PPR, filters={"revision_business_id": ("like", "_KT_PPR020_%")}, pluck="name") or []:
		frappe.delete_doc(PPR, row, force=True, ignore_permissions=True)
	for pin in frappe.get_all(PPI, filters={"name": ("like", "_KT_PPR020_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, pin, force=True, ignore_permissions=True)
	for pp in frappe.get_all(PP, filters={"name": ("like", "_KT_PPR020_%")}, pluck="name") or []:
		frappe.delete_doc(PP, pp, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PPR020_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PPR020_PE"})


class TestProcurementPlanRevisionApply(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_ppr020)
		self.entity = _make_entity("_KT_PPR020_PE").insert()
		self.period = _bcp("_KT_PPR020_BCP", self.entity.name).insert()
		self.plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PPR020_PP",
				"plan_title": "Apply revision plan",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
				"allow_manual_items": 1,
			}
		).insert(ignore_permissions=True)
		self.item = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPR020_IA",
				"procurement_plan": self.plan.name,
				"title": "Item A",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Manual",
				"manual_entry_justification": "Test",
				"estimated_amount": 5000,
				"priority_level": "Medium",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ppr020)
		super().tearDown()

	def _revision_doc(self, status: str, bid: str, **extra):
		payload = {
			"doctype": PPR,
			"revision_business_id": bid,
			"source_procurement_plan": self.plan.name,
			"revision_type": "Budget",
			"revision_reason": "Test apply",
			"requested_by": frappe.session.user,
			"requested_on": "2026-04-10 09:00:00",
			"status": status,
			"revision_lines": [
				{
					"doctype": PPRL,
					"affected_plan_item": self.item.name,
					"action_type": "Update",
					"change_amount": 250,
				}
			],
		}
		if status == "Approved":
			payload["approved_by"] = frappe.session.user
			payload["approved_on"] = "2026-04-10 12:00:00"
		payload.update(extra)
		return frappe.get_doc(payload)

	def test_draft_revision_blocked(self):
		doc = self._revision_doc("Draft", "_KT_PPR020_RD")
		doc.insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			apply_procurement_plan_revision(doc.name)

	def test_apply_updates_amount_and_marks_applied(self):
		doc = self._revision_doc("Approved", "_KT_PPR020_OK")
		doc.insert(ignore_permissions=True)

		n_before = len(
			frappe.get_all(
				AUDIT_EVENT_DOCTYPE,
				filters={"event_type": AUDIT_REVISION_APPLIED, "target_docname": doc.name},
			)
			or []
		)

		out = apply_procurement_plan_revision(doc.name)
		self.assertEqual(out["lines_applied"], 1)
		self.assertIn(self.item.name, out["items_touched"])

		self.item.reload()
		self.assertEqual(flt(self.item.estimated_amount), 5250.0)

		doc.reload()
		self.assertEqual(doc.status, "Applied")

		ev = frappe.get_all(
			AUDIT_EVENT_DOCTYPE,
			filters={"event_type": AUDIT_REVISION_APPLIED, "target_docname": doc.name},
		)
		self.assertEqual(len(ev), n_before + 1)

	def test_second_apply_blocked(self):
		doc = self._revision_doc("Approved", "_KT_PPR020_TW")
		doc.insert(ignore_permissions=True)
		apply_procurement_plan_revision(doc.name)
		with self.assertRaises(frappe.ValidationError):
			apply_procurement_plan_revision(doc.name)
