import frappe

from clinic.seed_data import (
	DIAGNOSES,
	DRUG_ITEM_GROUP,
	DRUGS,
	FIRST_AID_ITEM_GROUP,
	FIRST_AID_ITEMS,
	INVESTIGATIONS,
)

ROLES = [
	"Clinic Receptionist",
	"Clinic Nurse",
	"Clinic Doctor",
	"Clinic Pharmacist",
	"Clinic Manager",
	"Clinic First Aider",
]


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 0 if role == "Clinic First Aider" else 1}
			).insert(
				ignore_permissions=True
			)


def seed_investigations():
	for name, category in INVESTIGATIONS:
		if not frappe.db.exists("Clinic Investigation Type", name):
			frappe.get_doc(
				{"doctype": "Clinic Investigation Type", "investigation_name": name, "category": category}
			).insert(ignore_permissions=True)


def seed_diagnoses():
	for name, icd_code, category, occupational in DIAGNOSES:
		if frappe.db.exists("Clinic Diagnosis", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Clinic Diagnosis",
				"diagnosis": name,
				"icd_code": icd_code,
				"category": category,
				"is_occupational": occupational,
			}
		).insert(ignore_permissions=True)


def seed_drugs():
	"""The clinic's drug item group and a starting list of drugs (ERPNext Items)."""
	if not frappe.db.exists("Item Group", DRUG_ITEM_GROUP):
		frappe.get_doc(
			{"doctype": "Item Group", "item_group_name": DRUG_ITEM_GROUP, "parent_item_group": "All Item Groups"}
		).insert(ignore_permissions=True)
	for name in DRUGS:
		if frappe.db.exists("Item", {"item_name": name}):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": name,
				"item_name": name,
				"item_group": DRUG_ITEM_GROUP,
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"description": "Clinic drug",
			}
		).insert(ignore_permissions=True)


def seed_pharmacy_warehouse():
	from clinic.stock import ensure_warehouse

	ensure_warehouse()


NOTIFIABLE = ["Typhoid Fever", "Tuberculosis", "Brucellosis", "Cholera", "Measles", "Meningitis", "Ebola Virus Disease"]


def seed_notifiable():
	"""Diseases that must be reported: counted under Notifiable Diseases in the clinic reports."""
	for name in NOTIFIABLE:
		if not frappe.db.exists("Clinic Diagnosis", name):
			frappe.get_doc(
				{"doctype": "Clinic Diagnosis", "diagnosis": name, "category": "Infectious", "is_notifiable": 1}
			).insert(ignore_permissions=True)
		elif not frappe.db.get_value("Clinic Diagnosis", name, "is_notifiable"):
			frappe.db.set_value("Clinic Diagnosis", name, "is_notifiable", 1)


def seed_first_aid_items():
	"""The first aid supplies item group and a starting list of kit supplies (ERPNext Items)."""
	if not frappe.db.exists("Item Group", FIRST_AID_ITEM_GROUP):
		frappe.get_doc(
			{"doctype": "Item Group", "item_group_name": FIRST_AID_ITEM_GROUP, "parent_item_group": "All Item Groups"}
		).insert(ignore_permissions=True)
	for name in FIRST_AID_ITEMS:
		if frappe.db.exists("Item", {"item_name": name}):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": name,
				"item_name": name,
				"item_group": FIRST_AID_ITEM_GROUP,
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"description": "First aid kit supply",
			}
		).insert(ignore_permissions=True)


def before_install():
	ensure_roles()


def after_install():
	ensure_roles()
	seed_investigations()
	seed_diagnoses()
	seed_drugs()
	seed_pharmacy_warehouse()
	seed_notifiable()
	seed_first_aid_items()
