frappe.pages["award-contract-handoff"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Award Contract Handoff", "List");
	}, 0);

};
