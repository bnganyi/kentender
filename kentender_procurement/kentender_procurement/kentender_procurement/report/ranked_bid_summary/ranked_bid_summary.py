# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.evaluation_queue_queries import (
	evaluation_queue_report_columns,
	evaluation_queue_row_values,
	evaluation_report_entity_filter,
	get_ranked_bid_summary,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	es = (filters.get("evaluation_session") or "").strip()
	rows = get_ranked_bid_summary(
		procuring_entity=entity or None,
		evaluation_session=es or None,
	)
	keys = [
		"name",
		"evaluation_session",
		"bid_submission",
		"supplier",
		"combined_score",
		"ranking_position",
		"preliminary_result",
		"overall_result",
		"calculation_status",
		"modified",
	]
	data = [evaluation_queue_row_values(r, keys) for r in rows]
	return evaluation_queue_report_columns(keys), data


def get_filters():
	base = evaluation_report_entity_filter()
	base.append(
		{
			"fieldname": "evaluation_session",
			"label": "Evaluation Session",
			"fieldtype": "Link",
			"options": "Evaluation Session",
			"default": "",
		}
	)
	return base
