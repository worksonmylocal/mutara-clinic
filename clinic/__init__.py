__version__ = "0.0.1"


def check_app_permission():
	"""The Clinic app is only shown to people who hold a clinic role."""
	from clinic.access import has_clinic_role

	return has_clinic_role()
