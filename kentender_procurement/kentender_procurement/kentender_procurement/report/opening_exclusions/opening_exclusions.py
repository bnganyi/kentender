# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe import _

from kentender_procurement.services.opening_queue_queries import (
	get_opening_exclusion_rows,
	opening_report_entity_filter,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_opening_exclusion_rows(procuring_entity=entity or None)
	cols = [
		_("Register Line") + ":Data:140",
		_("Register") + ":Link/Bid Opening Register:180",
		_("Bid Submission") + ":Link/Bid Submission:180",
		_("Supplier") + ":Data:120",
		_("Exclusion Reason") + ":Small Text:200",
	]
	data = []
	for r in rows:
		data.append(
			[
				r.get("name"),
				r.get("parent"),
				r.get("bid_submission"),
				r.get("supplier"),
				r.get("exclusion_reason"),
			]
		)
	return cols, data


def get_filters():
	return opening_report_entity_filter()
