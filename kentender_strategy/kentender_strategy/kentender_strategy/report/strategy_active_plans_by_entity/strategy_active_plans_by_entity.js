// Copyright (c) 2025, Midas and contributors
// License: MIT. See LICENSE

frappe.query_reports["Strategy Active Plans By Entity"] = {
	filters: [
		{
			fieldname: "procuring_entity",
			label: __("Procuring Entity"),
			fieldtype: "Link",
			options: "Procuring Entity",
			reqd: 1,
		},
	],
};
