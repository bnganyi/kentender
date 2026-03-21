frappe.pages["award-recommendation"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Award Recommendation", "List");
	}, 0);

};
