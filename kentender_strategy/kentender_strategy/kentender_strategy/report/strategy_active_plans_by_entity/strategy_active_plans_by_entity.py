# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe import _

from kentender_strategy.services.strategy_queries import get_active_strategic_plans_for_entity


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	columns = get_columns()
	if not entity:
		return columns, []
	rows = get_active_strategic_plans_for_entity(entity)
	data = [
		[
			r.get("name"),
			r.get("name"),
			r.get("plan_title"),
			r.get("version_no"),
			r.get("status"),
			r.get("plan_period_label"),
			r.get("start_date"),
			r.get("end_date"),
		]
		for r in rows
	]
	return columns, data


def get_columns():
	return [
		_("Plan") + ":Link/Entity Strategic Plan:200",
		_("Reference") + ":Data:120",
		_("Plan Title") + ":Data:180",
		_("Version No.") + ":Int:80",
		_("Status") + ":Data:100",
		_("Plan Period Label") + ":Data:120",
		_("Start Date") + ":Date:100",
		_("End Date") + ":Date:100",
	]
