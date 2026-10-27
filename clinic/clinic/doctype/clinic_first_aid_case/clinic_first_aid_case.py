import frappe
from frappe import _
from frappe.model.document import Document

from clinic import stock


class ClinicFirstAidCase(Document):
	def validate(self):
		if not frappe.db.get_value("Clinic First Aider", self.first_aider, "active"):
			frappe.throw(_("{0} is not an active first aider").format(self.first_aider))
		for row in self.items:
			if (row.qty or 0) <= 0:
				frappe.throw(_("Row {0}: the quantity used must be more than zero").format(row.idx))

	def after_insert(self):
		stock.issue_from_kit(self)
