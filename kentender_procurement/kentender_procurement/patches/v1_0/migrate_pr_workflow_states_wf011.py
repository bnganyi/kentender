# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-011: map legacy Purchase Requisition workflow_state values to spec v2 §7.1 labels."""

from __future__ import annotations

import frappe


def execute():
	frappe.db.sql(
		"""
		UPDATE `tabPurchase Requisition`
		SET workflow_state = 'Pending HOD Approval'
		WHERE workflow_state IN ('Submitted', 'Under Review')
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabPurchase Requisition`
		SET approval_status = workflow_state
		WHERE IFNULL(approval_status, '') != IFNULL(workflow_state, '')
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabPurchase Requisition`
		SET status = CASE workflow_state
			WHEN 'Draft' THEN 'Draft'
			WHEN 'Pending HOD Approval' THEN 'Pending'
			WHEN 'Pending Finance Approval' THEN 'Pending'
			WHEN 'Approved' THEN 'Approved'
			WHEN 'Rejected' THEN 'Rejected'
			WHEN 'Returned for Amendment' THEN 'Draft'
			WHEN 'Cancelled' THEN 'Cancelled'
			ELSE status
		END
		WHERE workflow_state IS NOT NULL
		"""
	)
