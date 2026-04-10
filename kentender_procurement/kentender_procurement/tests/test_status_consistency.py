# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""STAT-014: regression tests for standardized PR status fields."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.status_model.derived_status import derive_purchase_requisition_summary_status
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.services.requisition_queue_queries import (
	requisition_report_columns,
	requisition_report_row_values,
)

PR = "Purchase Requisition"


class TestStatusConsistencySTAT014(FrappeTestCase):
	def test_mapping_covers_all_pr_workflow_options(self):
		options = (
			"Draft",
			"Pending HOD Approval",
			"Pending Finance Approval",
			"Approved",
			"Rejected",
			"Returned for Amendment",
			"Cancelled",
		)
		for o in options:
			s = derive_purchase_requisition_summary_status(o)
			self.assertTrue(s, msg=f"empty summary for {o!r}")

	def test_report_columns_reference_stage_not_legacy_duplicate(self):
		cols = " ".join(requisition_report_columns())
		self.assertIn("Stage", cols)
		self.assertNotIn("Approval Status", cols)

	def test_report_row_width_matches_columns(self):
		row = {
			"name": "PR-TEST",
			"name": "B1",
			"title": "T",
			"workflow_state": "Pending HOD Approval",
			"status": "Pending",
			"planning_status": "Unplanned",
			"requested_amount": 0,
			"procuring_entity": "E",
			"requested_by_user": "u@test",
			"modified": None,
		}
		self.assertEqual(len(requisition_report_row_values(row)), len(requisition_report_columns()))

	def test_pr_validate_keeps_derived_fields_aligned(self):
		cur = _ensure_test_currency()
		ent = _make_entity("_KT_STAT014_PE").insert()
		try:
			doc = frappe.get_doc(
				{
					"doctype": PR,
					"name": "_KT_STAT014_1",
					"title": "Consistency",
					"requisition_type": "Goods",
					"status": "Approved",
					"workflow_state": "Pending HOD Approval",
					"approval_status": "Wrong",
					"procuring_entity": ent.name,
					"fiscal_year": "2026-2027",
					"currency": cur,
					"request_date": "2026-04-01",
					"priority_level": "Medium",
					"budget_reservation_status": "None",
					"planning_status": "Unplanned",
					"items": [
						{
							"doctype": "Purchase Requisition Item",
							"item_description": "L",
							"quantity": 1,
							"estimated_unit_cost": 1,
						}
					],
				}
			)
			doc.insert()
			doc.reload()
			self.assertEqual(doc.status, "Pending")
			self.assertEqual(doc.approval_status, "Pending HOD Approval")
		finally:
			for name in frappe.get_all(PR, filters={"name": "_KT_STAT014_1"}, pluck="name"):
				frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
			frappe.db.delete("Procuring Entity", {"entity_code": "_KT_STAT014_PE"})
			frappe.db.commit()

	def test_workflow_state_only_mutation_sets_summary_on_save(self):
		cur = _ensure_test_currency()
		ent = _make_entity("_KT_STAT014_PE2").insert()
		try:
			doc = frappe.get_doc(
				{
					"doctype": PR,
					"name": "_KT_STAT014_2",
					"title": "Mut",
					"requisition_type": "Goods",
					"status": "Draft",
					"workflow_state": "Draft",
					"approval_status": "Draft",
					"procuring_entity": ent.name,
					"fiscal_year": "2026-2027",
					"currency": cur,
					"request_date": "2026-04-01",
					"priority_level": "Medium",
					"budget_reservation_status": "None",
					"planning_status": "Unplanned",
					"items": [
						{
							"doctype": "Purchase Requisition Item",
							"item_description": "L",
							"quantity": 1,
							"estimated_unit_cost": 1,
						}
					],
				}
			)
			doc.insert()
			with workflow_mutation_context():
				doc.reload()
				doc.workflow_state = "Approved"
				doc.save()
			doc.reload()
			self.assertEqual(doc.workflow_state, "Approved")
			self.assertEqual(doc.status, "Approved")
			self.assertEqual(doc.approval_status, "Approved")
		finally:
			for name in frappe.get_all(PR, filters={"name": "_KT_STAT014_2"}, pluck="name"):
				frappe.delete_doc(PR, name, force=True, ignore_permissions=True)
			frappe.db.delete("Procuring Entity", {"entity_code": "_KT_STAT014_PE2"})
			frappe.db.commit()
