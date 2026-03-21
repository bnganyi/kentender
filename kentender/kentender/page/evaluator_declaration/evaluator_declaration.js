frappe.pages["evaluator-declaration"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Evaluator Declaration", "List");
	}, 0);

};
