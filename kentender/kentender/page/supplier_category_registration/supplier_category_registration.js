frappe.pages["supplier-category-registration"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Supplier Category Registration", "List");
	}, 0);

};
