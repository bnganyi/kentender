frappe.pages["evaluation-worksheet"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Evaluation Worksheet", "List");
	}, 0);

};
