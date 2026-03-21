frappe.pages["suspension-debarment-register"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Suspension Debarment Register", "List");
	}, 0);

};
