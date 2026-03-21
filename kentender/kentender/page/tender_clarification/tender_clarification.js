frappe.pages["tender-clarification"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender Clarification", "List");
	}, 0);

};
