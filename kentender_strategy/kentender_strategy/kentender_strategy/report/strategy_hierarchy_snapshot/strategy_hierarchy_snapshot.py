# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-only list of strategy records by layer — supports hierarchy explorer UX (code + name)."""

import frappe
from frappe import _


_LAYER_QUERIES: list[tuple[int, str, str, str, str]] = [
	(1, "National Framework", "`tabNational Framework`", "framework_code", "framework_name"),
	(2, "National Pillar", "`tabNational Pillar`", "pillar_code", "pillar_name"),
	(3, "National Objective", "`tabNational Objective`", "objective_code", "objective_name"),
	(4, "Entity Strategic Plan", "`tabEntity Strategic Plan`", "name", "plan_title"),
	(5, "Strategic Program", "`tabStrategic Program`", "program_code", "program_name"),
	(6, "Strategic Sub Program", "`tabStrategic Sub Program`", "sub_program_code", "sub_program_name"),
	(7, "Output Indicator", "`tabOutput Indicator`", "indicator_code", "indicator_name"),
	(8, "Performance Target", "`tabPerformance Target`", "name", "target_title"),
]


def execute(filters=None):
	columns = [
		_("Level") + ":Int:50",
		_("Layer") + ":Data:160",
		_("Code / Ref") + ":Data:140",
		_("Name / Title") + ":Data:240",
		_("DocType") + ":Data:160",
		_("Record") + ":Dynamic Link:200",
	]
	data: list[list] = []
	for level, label, tab, code_f, title_f in _LAYER_QUERIES:
		rows = frappe.db.sql(
			f"""
			SELECT name, `{code_f}`, `{title_f}` FROM {tab}
			WHERE docstatus < 2
			ORDER BY modified DESC
			LIMIT 80
			""",
			as_list=1,
		)
		doctype = label
		for name, code, title in rows:
			data.append([level, label, code or name, title or "", doctype, name])
	return columns, data
