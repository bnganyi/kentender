# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Backfill ``display_label`` on strategy DocTypes after adding the field."""

import frappe

from kentender.utils.display_label import code_title_label


def execute():
	for row in frappe.get_all("National Pillar", fields=["name", "pillar_code", "pillar_name"]):
		lbl = code_title_label(row.pillar_code, row.pillar_name)
		frappe.db.set_value("National Pillar", row.name, "display_label", lbl, update_modified=False)

	for row in frappe.get_all("National Objective", fields=["name", "objective_code", "objective_name"]):
		lbl = code_title_label(row.objective_code, row.objective_name)
		frappe.db.set_value("National Objective", row.name, "display_label", lbl, update_modified=False)

	for row in frappe.get_all("Strategic Program", fields=["name", "program_code", "program_name"]):
		lbl = code_title_label(row.program_code, row.program_name)
		frappe.db.set_value("Strategic Program", row.name, "display_label", lbl, update_modified=False)

	for row in frappe.get_all(
		"Strategic Sub Program", fields=["name", "sub_program_code", "sub_program_name"]
	):
		lbl = code_title_label(row.sub_program_code, row.sub_program_name)
		frappe.db.set_value("Strategic Sub Program", row.name, "display_label", lbl, update_modified=False)

	for row in frappe.get_all("Output Indicator", fields=["name", "indicator_code", "indicator_name"]):
		lbl = code_title_label(row.indicator_code, row.indicator_name)
		frappe.db.set_value("Output Indicator", row.name, "display_label", lbl, update_modified=False)

	for row in frappe.get_all("Performance Target", fields=["name", "target_title"]):
		lbl = code_title_label(row.name, row.target_title)
		frappe.db.set_value("Performance Target", row.name, "display_label", lbl, update_modified=False)
