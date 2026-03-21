frappe.pages["tender"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender", "List");
	}, 0);

};
