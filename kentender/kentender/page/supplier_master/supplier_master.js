frappe.pages["supplier-master"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Supplier Master", "List");
	}, 0);

};
