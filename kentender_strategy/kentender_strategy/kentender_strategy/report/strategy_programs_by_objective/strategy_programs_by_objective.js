// Copyright (c) 2025, Midas and contributors
// License: MIT. See LICENSE

frappe.query_reports["Strategy Programs By Objective"] = {
	filters: [
		{
			fieldname: "national_objective",
			label: __("National Objective"),
			fieldtype: "Link",
			options: "National Objective",
			reqd: 1,
		},
	],
};
