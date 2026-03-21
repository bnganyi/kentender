frappe.pages["supplier-registration-application"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Supplier Registration Application", "List");
	}, 0);

};
