frappe.ui.form.on("Clinic Visit", {
	refresh(frm) {
		if (frm.is_new()) return;
		const status = frm.doc.status;
		const closed = ["Completed", "Cancelled"].includes(status);

		if (status === "Waiting Triage") {
			frm.add_custom_button(__("Record Triage"), () => {
				if (frm.doc.triage) return frappe.set_route("Form", "Clinic Triage", frm.doc.triage);
				frappe.new_doc("Clinic Triage", { visit: frm.doc.name });
			}).addClass("btn-primary");
		}

		if (["Waiting Consultation", "In Consultation"].includes(status)) {
			frm.add_custom_button(__("Open Consultation"), () => {
				if (frm.doc.consultation) return frappe.set_route("Form", "Clinic Consultation", frm.doc.consultation);
				frappe.new_doc("Clinic Consultation", { visit: frm.doc.name });
			}).addClass("btn-primary");
		}

		if (!closed) {
			frm.add_custom_button(__("Cancel Visit"), () => {
				frappe.confirm(__("Cancel this visit?"), () => {
					frm.call("cancel_visit").then(() => frm.reload_doc());
				});
			}, __("Actions"));
		}

		if (frm.doc.triage) {
			frm.add_custom_button(__("Triage"), () => frappe.set_route("Form", "Clinic Triage", frm.doc.triage), __("View"));
		}
	},
});
