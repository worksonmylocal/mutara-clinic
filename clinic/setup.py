import frappe

from clinic.seed_data import DIAGNOSES, INVESTIGATIONS

ROLES = [
	"Clinic Receptionist",
	"Clinic Nurse",
	"Clinic Doctor",
	"Clinic Pharmacist",
	"Clinic Manager",
]


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
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


def before_install():
	ensure_roles()


def after_install():
	ensure_roles()
	seed_investigations()
	seed_diagnoses()
