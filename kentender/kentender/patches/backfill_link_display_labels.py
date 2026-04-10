# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Backfill ``display_label`` on KenTender core, budget, and procurement DocTypes."""

import frappe

from kentender.utils.display_label import code_title_label


def _can_query(doctype: str, fieldnames: list[str]) -> bool:
	"""Skip backfill when the table or required columns are not on this site yet."""
	if not frappe.db.table_exists(doctype):
		return False
	try:
		for fn in fieldnames:
			if fn != "name" and not frappe.db.has_column(doctype, fn):
				return False
	except frappe.db.TableMissingError:
		return False
	return True


def execute():
	if _can_query("Procuring Department", ["name", "department_code", "department_name"]):
		for row in frappe.get_all(
			"Procuring Department", fields=["name", "department_code", "department_name"]
		):
			lbl = code_title_label(row.department_code, row.department_name)
			frappe.db.set_value("Procuring Department", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Funding Source", ["name", "funding_source_code", "funding_source_name"]):
		for row in frappe.get_all(
			"Funding Source", fields=["name", "funding_source_code", "funding_source_name"]
		):
			lbl = code_title_label(row.funding_source_code, row.funding_source_name)
			frappe.db.set_value("Funding Source", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Procurement Category", ["name", "category_code", "category_name"]):
		for row in frappe.get_all(
			"Procurement Category", fields=["name", "category_code", "category_name"]
		):
			lbl = code_title_label(row.category_code, row.category_name)
			frappe.db.set_value("Procurement Category", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Procurement Method", ["name", "method_code", "method_name"]):
		for row in frappe.get_all(
			"Procurement Method", fields=["name", "method_code", "method_name"]
		):
			lbl = code_title_label(row.method_code, row.method_name)
			frappe.db.set_value("Procurement Method", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Document Type Registry", ["name", "document_type_code", "document_type_name"]):
		for row in frappe.get_all(
			"Document Type Registry",
			fields=["name", "document_type_code", "document_type_name"],
		):
			lbl = code_title_label(row.document_type_code, row.document_type_name)
			frappe.db.set_value("Document Type Registry", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Budget", ["name", "budget_title"]):
		for row in frappe.get_all("Budget", fields=["name", "budget_title"]):
			lbl = code_title_label(row.name, row.budget_title)
			frappe.db.set_value("Budget", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Budget Control Period", ["name", "period_label"]):
		for row in frappe.get_all(
			"Budget Control Period", fields=["name", "period_label"]
		):
			lbl = code_title_label(row.name, row.period_label)
			frappe.db.set_value("Budget Control Period", row.name, "display_label", lbl, update_modified=False)

	if _can_query(
		"Budget Line",
		["name", "fiscal_year", "external_reference_name", "external_budget_code"],
	):
		for row in frappe.get_all(
			"Budget Line",
			fields=[
				"name",
				"fiscal_year",
				"external_reference_name",
				"external_budget_code",
			],
		):
			sub = (row.external_reference_name or row.external_budget_code or row.fiscal_year or "").strip()
			lbl = code_title_label(row.name, sub)
			frappe.db.set_value("Budget Line", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Budget Allocation", ["name", "allocation_reference", "allocation_type"]):
		for row in frappe.get_all(
			"Budget Allocation",
			fields=["name", "allocation_reference", "allocation_type"],
		):
			sub = (row.allocation_reference or row.allocation_type or "").strip()
			lbl = code_title_label(row.name, sub)
			frappe.db.set_value("Budget Allocation", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Budget Ledger Entry", ["name", "entry_type"]):
		for row in frappe.get_all("Budget Ledger Entry", fields=["name", "entry_type"]):
			lbl = code_title_label(row.name, row.entry_type)
			frappe.db.set_value("Budget Ledger Entry", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Budget Revision", ["name", "revision_type"]):
		for row in frappe.get_all("Budget Revision", fields=["name", "revision_type"]):
			lbl = code_title_label(row.name, row.revision_type)
			frappe.db.set_value("Budget Revision", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Purchase Requisition", ["name", "title"]):
		for row in frappe.get_all("Purchase Requisition", fields=["name", "title"]):
			lbl = code_title_label(row.name, row.title)
			frappe.db.set_value("Purchase Requisition", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Requisition Approval Record", ["name", "purchase_requisition", "workflow_step"]):
		for row in frappe.get_all(
			"Requisition Approval Record",
			fields=["name", "purchase_requisition", "workflow_step"],
		):
			lbl = code_title_label(row.purchase_requisition, row.workflow_step)
			frappe.db.set_value("Requisition Approval Record", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Requisition Amendment Record", ["name", "purchase_requisition", "amendment_type"]):
		for row in frappe.get_all(
			"Requisition Amendment Record",
			fields=["name", "purchase_requisition", "amendment_type"],
		):
			lbl = code_title_label(row.purchase_requisition, row.amendment_type)
			frappe.db.set_value("Requisition Amendment Record", row.name, "display_label", lbl, update_modified=False)

	if _can_query("Requisition Planning Link", ["name", "purchase_requisition", "status"]):
		for row in frappe.get_all(
			"Requisition Planning Link", fields=["name", "purchase_requisition", "status"]
		):
			lbl = code_title_label(row.purchase_requisition, row.status)
			frappe.db.set_value("Requisition Planning Link", row.name, "display_label", lbl, update_modified=False)
