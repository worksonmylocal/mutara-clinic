frappe.query_reports["Weekly Clinic Activity"] = {
	filters: [
		{ fieldname: "week_of", label: __("Week Of (any date in the week)"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
		{ fieldname: "include_sunday", label: __("Include Sunday"), fieldtype: "Check", default: 0 },
	],
	onload(report) {
		report.page.add_inner_button(__("Print Weekly Report"), () => {
			const f = report.get_values();
			window.open(`/clinic/weekly?week=${f.week_of}&sunday=${f.include_sunday || 0}`, "_blank");
		});
	},
};
