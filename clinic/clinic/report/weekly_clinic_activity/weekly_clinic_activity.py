import frappe
from frappe.utils import cint

from clinic.reports import weekly_data


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = weekly_data(filters.week_of, cint(filters.include_sunday))
	columns = [{"fieldname": "activity", "label": "Activity", "fieldtype": "Data", "width": 280}]
	for i, day in enumerate(data["days"]):
		columns.append({"fieldname": f"d{i}", "label": f"{day['label']} {day['short']}", "fieldtype": "Data", "width": 190})
	columns.append({"fieldname": "total", "label": "Total", "fieldtype": "Data", "width": 70})
	rows = []
	for r in data["rows"]:
		row = {"activity": r["label"], "total": r["total"]}
		for i, cell in enumerate(r["cells"]):
			row[f"d{i}"] = cell
		rows.append(row)
	return columns, rows
