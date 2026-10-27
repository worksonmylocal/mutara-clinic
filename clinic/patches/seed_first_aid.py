from clinic.setup import ensure_roles, seed_first_aid_items


def execute():
	ensure_roles()
	seed_first_aid_items()
