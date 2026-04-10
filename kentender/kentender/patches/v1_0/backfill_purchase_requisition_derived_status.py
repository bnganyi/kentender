# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""STAT-013: align PR summary fields with workflow_state (see docs/workflow/STAT-013 migration notes.md)."""

import frappe


def execute():
	if not frappe.db.table_exists("Purchase Requisition"):
		return
	# Legacy mirror: approval_status tracks authoritative stage label.
	frappe.db.sql(
		"""
		UPDATE `tabPurchase Requisition`
		SET approval_status = workflow_state
		WHERE IFNULL(approval_status, '') != IFNULL(workflow_state, '')
		"""
	)
	# Derived summary status (Standard Status Model).
	frappe.db.sql(
		"""
		UPDATE `tabPurchase Requisition`
		SET status = CASE workflow_state
			WHEN 'Draft' THEN 'Draft'
			WHEN 'Submitted' THEN 'Pending'
			WHEN 'Under Review' THEN 'Pending'
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
	frappe.db.commit()
