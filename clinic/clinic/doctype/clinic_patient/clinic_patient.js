frappe.ui.form.on("Clinic Patient", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("New Visit"), () => {
				frappe.new_doc("Clinic Visit", { patient: frm.doc.name });
			});
			frm.add_custom_button(__("Visit History"), () => {
				frappe.set_route("List", "Clinic Visit", { patient: frm.doc.name });
			}, __("View"));
		}
	},
});
