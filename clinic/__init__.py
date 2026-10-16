__version__ = "0.0.1"


def check_app_permission():
	"""Show the Clinic app to system managers and anyone with a clinic role."""
	import frappe

	if frappe.session.user == "Administrator":
		return True
	roles = set(frappe.get_roles())
	return bool(roles & {"System Manager", "Clinic Manager", "Clinic Receptionist", "Clinic Nurse", "Clinic Doctor", "Clinic Pharmacist"})
