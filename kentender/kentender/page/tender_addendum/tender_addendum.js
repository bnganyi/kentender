frappe.pages["tender-addendum"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Tender Addendum", "List");
	}, 0);

};
