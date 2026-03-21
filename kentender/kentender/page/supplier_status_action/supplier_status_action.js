frappe.pages["supplier-status-action"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Supplier Status Action", "List");
	}, 0);

};
