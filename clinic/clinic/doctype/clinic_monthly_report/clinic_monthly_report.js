frappe.ui.form.on("Clinic Monthly Report", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Print Report"), () => {
			window.open(`/clinic/monthly?month=${frm.doc.period_start.slice(0, 7)}`, "_blank");
		}).addClass("btn-primary");
	},
});
