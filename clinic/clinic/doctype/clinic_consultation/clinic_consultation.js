frappe.ui.form.on("Clinic Consultation", {
	setup(frm) {
		frm.set_query("visit", () => ({
			filters: { status: ["not in", ["Completed", "Cancelled"]] },
		}));
	},

	refresh(frm) {
		if (frm.doc.vitals_summary) {
			const alerts = frm.doc.vitals_summary.includes("Alerts:");
			frm.set_intro(frappe.utils.escape_html(frm.doc.vitals_summary).replace(/\n/g, "<br>"), alerts ? "orange" : "blue");
		}
		if (frm.is_new()) return;

		if (frm.doc.status !== "Completed") {
			if ((frm.doc.prescriptions || []).length) {
				frm.add_custom_button(__("Send to Pharmacy"), () => run(frm, "send_to_pharmacy"), __("Finish"));
			} else {
				frm.add_custom_button(__("Complete Consultation"), () => run(frm, "complete_consultation"), __("Finish"));
			}
		}

		const has = (category) => (frm.doc.investigations || []).some((row) => row.category === category);
		const open = (url) => window.open(url, "_blank");
		if (has("Laboratory")) {
			frm.add_custom_button(__("Lab Referral"), () => open(`/clinic/referral?consultation=${frm.doc.name}&type=Laboratory`), __("Print"));
		}
		if (has("Imaging")) {
			frm.add_custom_button(__("Imaging Referral"), () => open(`/clinic/referral?consultation=${frm.doc.name}&type=Imaging`), __("Print"));
		}
		if (frm.doc.consultation_type !== "Consultation") {
			frm.add_custom_button(__("Medical Report"), () => open(`/clinic/certificate?consultation=${frm.doc.name}`), __("Print"));
		}

		if (frm.doc.dispensing) {
			frm.add_custom_button(__("Dispensing"), () => frappe.set_route("Form", "Clinic Dispensing", frm.doc.dispensing), __("View"));
		}
		if (frm.doc.triage) {
			frm.add_custom_button(__("Triage"), () => frappe.set_route("Form", "Clinic Triage", frm.doc.triage), __("View"));
		}
		frm.add_custom_button(__("Patient History"), () => frappe.set_route("List", "Clinic Consultation", { patient: frm.doc.patient }), __("View"));
	},
});

// Save any pending edits, then call the server action on the saved document.
function run(frm, method) {
	const saved = frm.is_dirty() ? frm.save() : Promise.resolve();
	return saved.then(() => frm.call(method)).then(() => frm.reload_doc());
}
