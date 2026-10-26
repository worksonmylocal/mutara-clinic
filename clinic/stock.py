"""Pharmacy stock: what is on the shelf, what is already promised to waiting prescriptions, and the issue entry."""

import frappe
from frappe import _
from frappe.utils import flt, nowdate, nowtime

WAREHOUSE_NAME = "Clinic Pharmacy"


def pharmacy_warehouse():
	return frappe.db.get_single_value("Clinic Settings", "pharmacy_warehouse")


def ensure_warehouse():
	"""Create the clinic's own warehouse and point Clinic Settings at it (once)."""
	if pharmacy_warehouse() and frappe.db.exists("Warehouse", pharmacy_warehouse()):
		return pharmacy_warehouse()
	company = frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name")
	if not company:
		return None
	abbr = frappe.db.get_value("Company", company, "abbr")
	name = f"{WAREHOUSE_NAME} - {abbr}"
	if not frappe.db.exists("Warehouse", name):
		parent = f"All Warehouses - {abbr}"
		frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": WAREHOUSE_NAME,
				"company": company,
				"parent_warehouse": parent if frappe.db.exists("Warehouse", parent) else None,
			}
		).insert(ignore_permissions=True)
	frappe.db.set_single_value("Clinic Settings", "pharmacy_warehouse", name)
	return name


def on_hand(items):
	"""{item: quantity on the pharmacy shelf}."""
	warehouse = pharmacy_warehouse()
	if not warehouse or not items:
		return {}
	rows = frappe.get_all(
		"Bin", filters={"warehouse": warehouse, "item_code": ["in", list(items)]}, fields=["item_code", "actual_qty"]
	)
	return {r.item_code: flt(r.actual_qty) for r in rows}


def reserved(items, exclude_consultation=None):
	"""{item: quantity prescribed to patients still waiting at the pharmacy (not dispensed yet)}."""
	if not items:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT i.drug, SUM(i.prescribed_qty) AS qty
		FROM `tabClinic Dispensing Item` i JOIN `tabClinic Dispensing` d ON d.name = i.parent
		WHERE d.docstatus = 0 AND i.drug IN %(items)s AND IFNULL(d.consultation, '') != %(exclude)s
		GROUP BY i.drug
		""",
		{"items": list(items), "exclude": exclude_consultation or ""},
		as_dict=True,
	)
	return {r.drug: flt(r.qty) for r in rows}


def available(items, exclude_consultation=None):
	"""{item: quantity still free to prescribe} = on the shelf minus what waiting prescriptions already hold."""
	stock, held = on_hand(items), reserved(items, exclude_consultation)
	return {item: max(stock.get(item, 0) - held.get(item, 0), 0) for item in items}


def issue_dispensed(dispensing):
	"""Take what the pharmacist handed out off the shelf (Stock Entry: Material Issue)."""
	lines = [r for r in dispensing.items if flt(r.dispensed_qty) > 0 and not r.not_available]
	if not lines:
		return
	warehouse = pharmacy_warehouse()
	if not warehouse:
		frappe.throw(_("Set the Pharmacy Warehouse in Clinic Settings first"))
	entry = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Issue",
			"purpose": "Material Issue",
			"company": frappe.db.get_value("Warehouse", warehouse, "company"),
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"remarks": _("Dispensed at the clinic: {0} ({1})").format(dispensing.name, dispensing.patient_name),
			"items": [
				{
					"item_code": r.drug,
					"s_warehouse": warehouse,
					"qty": flt(r.dispensed_qty),
					"uom": frappe.db.get_value("Item", r.drug, "stock_uom"),
				}
				for r in lines
			],
		}
	)
	entry.insert(ignore_permissions=True)
	entry.submit()
	dispensing.db_set("stock_entry", entry.name)


def reverse_issue(dispensing):
	if dispensing.stock_entry and frappe.db.get_value("Stock Entry", dispensing.stock_entry, "docstatus") == 1:
		frappe.get_doc("Stock Entry", dispensing.stock_entry).cancel()


@frappe.whitelist()
def add_opening_stock(quantity=100, rate=10):
	"""Book the starting stock of every clinic drug into the pharmacy warehouse (Material Receipt).

	Run from the bench: bench --site <site> execute clinic.stock.add_opening_stock --kwargs "{'quantity': 100, 'rate': 10}"
	The rate is the buying cost per unit, so the books get a real valuation.
	"""
	frappe.only_for(["System Manager", "Clinic Manager"])
	from clinic.api.consultation import drug_groups

	warehouse = ensure_warehouse()
	items = frappe.get_all("Item", filters={"disabled": 0, "is_stock_item": 1, "item_group": ["in", drug_groups()]}, pluck="name")
	entry = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"purpose": "Material Receipt",
			"company": frappe.db.get_value("Warehouse", warehouse, "company"),
			"remarks": "Clinic pharmacy opening stock",
			"items": [
				{
					"item_code": i,
					"t_warehouse": warehouse,
					"qty": flt(quantity),
					"basic_rate": flt(rate),
					"uom": frappe.db.get_value("Item", i, "stock_uom"),
				}
				for i in items
			],
		}
	)
	entry.insert(ignore_permissions=True)
	entry.submit()
	return entry.name
