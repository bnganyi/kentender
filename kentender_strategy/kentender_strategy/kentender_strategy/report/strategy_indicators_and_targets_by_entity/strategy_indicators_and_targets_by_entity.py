# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe import _

from kentender_strategy.services.strategy_queries import (
	get_output_indicators_for_entity,
	get_performance_targets_for_entity,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	columns = get_columns()
	if not entity:
		return columns, []
	data = []
	for r in get_output_indicators_for_entity(entity):
		data.append(
			[
				_("Indicator"),
				r.get("name"),
				r.get("business_id"),
				r.get("indicator_code"),
				r.get("indicator_name"),
				r.get("program"),
				r.get("sub_program"),
				r.get("entity_strategic_plan"),
				r.get("status"),
				None,
				None,
			]
		)
	for r in get_performance_targets_for_entity(entity):
		data.append(
			[
				_("Target"),
				r.get("name"),
				r.get("business_id"),
				None,
				r.get("target_title"),
				r.get("program"),
				r.get("sub_program"),
				r.get("entity_strategic_plan"),
				r.get("status"),
				r.get("period_start_date"),
				r.get("period_end_date"),
			]
		)
	return columns, data


def get_columns():
	return [
		_("Record Type") + ":Data:90",
		_("Document") + ":Data:200",
		_("Business ID") + ":Data:120",
		_("Code") + ":Data:100",
		_("Title / Name") + ":Data:200",
		_("Program") + ":Link/Strategic Program:160",
		_("Sub Program") + ":Link/Strategic Sub Program:160",
		_("Entity Strategic Plan") + ":Link/Entity Strategic Plan:200",
		_("Status") + ":Data:90",
		_("Period Start") + ":Date:100",
		_("Period End") + ":Date:100",
	]
