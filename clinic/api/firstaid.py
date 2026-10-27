"""First aiders' own page: they record the first aid they give on the farm and see their kit.

First aiders have no access to clinic records. Everything here works on their own cases and their own kit, and the
role has no document permissions: the checks are in these functions.
"""

import frappe
from frappe import _
from frappe.utils import add_days, get_first_day, nowdate

from clinic import stock
from clinic.api.common import clean, minutes_since, require, to_number

CASE_FIELDS = ["name", "case_datetime", "patient_name", "department", "nature", "outcome", "reviewed", "supplies_note"]


def _me():
	"""The caller's first aider record."""
	name = frappe.db.get_value("Clinic First Aider", {"user": frappe.session.user, "active": 1}, "name")
	if not name:
		frappe.throw(_("You are not registered as a first aider. Ask the clinic to add you."), frappe.PermissionError)
	return frappe.get_doc("Clinic First Aider", name)


@frappe.whitelist()
def dashboard():
	require("firstaid")
	me = _me()
	warehouse = frappe.db.get_value("Clinic First Aid Kit", me.kit, "warehouse")
	cases = frappe.get_all(
		"Clinic First Aid Case", filters={"first_aider": me.name}, fields=CASE_FIELDS, order_by="case_datetime desc", limit=30
	)
	month = frappe.db.count(
		"Clinic First Aid Case", {"first_aider": me.name, "case_datetime": [">=", f"{get_first_day(nowdate())} 00:00:00"]}
	)
	kit = stock.kit_stock(warehouse) if warehouse else []
	return {
		"me": {"name": me.full_name, "kit": me.kit, "department": me.department, "certificate_expiry": me.certificate_expiry},
		"kpis": {"cases_month": month, "cases_total": frappe.db.count("Clinic First Aid Case", {"first_aider": me.name}),
			"kit_items": len(kit), "low_items": sum(1 for r in kit if r["qty"] <= 2)},
		"cases": cases,
		"kit": kit,
	}


@frappe.whitelist()
def search_employees(q=""):
	require("firstaid")
	_me()
	q = (q or "").strip()
	if len(q) < 2:
		return []
	like = f"%{q}%"
	return frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		or_filters=[["employee_name", "like", like], ["name", "like", like]],
		fields=["name", "employee_name", "department"],
		order_by="employee_name asc",
		limit=10,
	)


@frappe.whitelist()
def record_case(data):
	require("firstaid")
	me = _me()
	data = frappe.parse_json(data)
	items = [
		{"item": r.get("item"), "qty": to_number(r.get("qty")) or 0}
		for r in data.get("items", [])
		if r.get("item") and (to_number(r.get("qty")) or 0) > 0
	]
	kit_items = {r["item"] for r in stock.kit_stock(frappe.db.get_value("Clinic First Aid Kit", me.kit, "warehouse") or "")}
	for r in items:
		if r["item"] not in kit_items:
			frappe.throw(_("{0} is not in your kit").format(r["item"]))
	doc = frappe.get_doc(
		{
			"doctype": "Clinic First Aid Case",
			"first_aider": me.name,
			"patient_name": clean(data.get("patient_name")),
			"employee": clean(data.get("employee")),
			"department": clean(data.get("department")),
			"location": clean(data.get("location")),
			"nature": clean(data.get("nature")),
			"description": clean(data.get("description")),
			"treatment": clean(data.get("treatment")),
			"outcome": clean(data.get("outcome")) or "Treated on site",
			"items": items,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.reload()
	return {"name": doc.name, "supplies_note": doc.supplies_note}
