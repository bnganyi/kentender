frappe.pages["evaluation-committee"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Evaluation Committee", "List");
	}, 0);

};
