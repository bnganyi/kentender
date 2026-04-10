# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.status_model.derived_status import (
	PR_DOCTYPE,
	apply_registered_summary_fields,
	derive_purchase_requisition_summary_status,
	derive_summary_status,
)


class TestDerivedStatus(FrappeTestCase):
	def test_pr_mapping_table(self):
		self.assertEqual(derive_purchase_requisition_summary_status("Draft"), "Draft")
		self.assertEqual(derive_purchase_requisition_summary_status("Submitted"), "Pending")
		self.assertEqual(derive_purchase_requisition_summary_status("Under Review"), "Pending")
		self.assertEqual(derive_purchase_requisition_summary_status("Approved"), "Approved")
		self.assertEqual(derive_purchase_requisition_summary_status("Rejected"), "Rejected")
		self.assertEqual(derive_purchase_requisition_summary_status("Cancelled"), "Cancelled")
		self.assertEqual(
			derive_purchase_requisition_summary_status("Pending HOD Approval"), "Pending"
		)
		self.assertEqual(
			derive_purchase_requisition_summary_status("Pending Finance Approval"), "Pending"
		)
		self.assertEqual(
			derive_purchase_requisition_summary_status("Returned for Amendment"), "Draft"
		)

	def test_pr_unknown_state_echoes(self):
		self.assertEqual(derive_purchase_requisition_summary_status("Future State X"), "Future State X")

	def test_derive_summary_status_dispatches(self):
		self.assertEqual(derive_summary_status(PR_DOCTYPE, "Submitted"), "Pending")

	def test_unknown_doctype_echoes_workflow(self):
		self.assertEqual(derive_summary_status("Nonexistent DocType", "Foo"), "Foo")

	def test_apply_registered_sets_fields_unsaved(self):
		doc = frappe.get_doc(
			{
				"doctype": PR_DOCTYPE,
				"workflow_state": "Pending Finance Approval",
				"status": "Draft",
				"approval_status": "X",
			}
		)
		apply_registered_summary_fields(doc)
		self.assertEqual(doc.status, "Pending")
		self.assertEqual(doc.approval_status, "Pending Finance Approval")
