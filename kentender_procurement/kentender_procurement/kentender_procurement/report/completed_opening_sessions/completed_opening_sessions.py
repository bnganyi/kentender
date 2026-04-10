# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.opening_queue_queries import (
	get_completed_opening_sessions,
	opening_report_entity_filter,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_completed_opening_sessions(procuring_entity=entity or None)
	cols = [
		"Session:Link/Bid Opening Session:180",
		"Business ID:Data:140",
		"Tender:Link/Tender:160",
		"Workflow:Data:130",
		"Status:Data:100",
		"Actual Opening:Datetime:150",
		"Opened Bids:Int:90",
		"Excluded:Int:90",
		"Modified:Datetime:150",
	]
	data = [
		[
			r.get("name"),
			r.get("business_id"),
			r.get("tender"),
			r.get("workflow_state"),
			r.get("status"),
			r.get("actual_opening_datetime"),
			r.get("opened_bid_count"),
			r.get("excluded_bid_count"),
			r.get("modified"),
		]
		for r in rows
	]
	return cols, data


def get_filters():
	return opening_report_entity_filter()
