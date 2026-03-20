// KenTender: Purchase Requisition desk UX (context + progressive guidance)
frappe.ui.form.on("Purchase Requisition", {
	refresh(frm) {
		frm.clear_intro();

		const parts = [
			__(
				"Work across the tabs below in order: <strong>Budget &amp; APP</strong> → <strong>Line items</strong> → <strong>Approvals</strong> → governance / tender fields as needed."
			),
		];

		if (frm.doc.source_mode === "One-Off") {
			parts.push(
				__(
					"<strong>One-Off</strong>: enable the One-Off flag and complete exception routing where required."
				)
			);
		}
		if (frm.doc.requisition_type === "Emergency") {
			parts.push(__("<strong>Emergency</strong>: confirm the Emergency flag and justification are complete."));
		}

		frm.set_intro(parts.join(" "), "blue");
	},
});
