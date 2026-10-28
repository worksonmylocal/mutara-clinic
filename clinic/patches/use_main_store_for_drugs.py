from clinic.stock import ensure_warehouse


def execute():
	"""Drugs live in the Main Store under the Clinic Drugs item group. Leaves a warehouse that is already set alone."""
	ensure_warehouse()
