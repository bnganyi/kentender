frappe.pages["award-decision"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Award Decision", "List");
	}, 0);

};
