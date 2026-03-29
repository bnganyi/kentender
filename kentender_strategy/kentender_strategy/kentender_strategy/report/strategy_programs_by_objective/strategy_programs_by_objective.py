# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe import _

from kentender_strategy.services.strategy_queries import get_programs_for_national_objective


def execute(filters=None):
	filters = filters or {}
	obj = (filters.get("national_objective") or "").strip()
	columns = get_columns()
	if not obj:
		return columns, []
	rows = get_programs_for_national_objective(obj)
	data = [
		[
			r.get("name"),
			r.get("business_id"),
			r.get("program_code"),
			r.get("program_name"),
			r.get("procuring_entity"),
			r.get("entity_strategic_plan"),
			r.get("status"),
		]
		for r in rows
	]
	return columns, data


def get_columns():
	return [
		_("Program") + ":Link/Strategic Program:200",
		_("Business ID") + ":Data:120",
		_("Program Code") + ":Data:100",
		_("Program Name") + ":Data:180",
		_("Procuring Entity") + ":Link/Procuring Entity:160",
		_("Entity Strategic Plan") + ":Link/Entity Strategic Plan:200",
		_("Status") + ":Data:100",
	]
