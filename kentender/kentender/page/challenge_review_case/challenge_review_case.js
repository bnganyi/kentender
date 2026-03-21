frappe.pages["challenge-review-case"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Challenge Review Case", "List");
	}, 0);

};
