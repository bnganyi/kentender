frappe.pages["evaluation-consensus-record"].on_page_load = function () {
	setTimeout(function () {
		frappe.set_route("List", "Evaluation Consensus Record", "List");
	}, 0);

};
