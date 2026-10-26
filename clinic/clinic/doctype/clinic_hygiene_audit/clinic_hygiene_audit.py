import frappe
from frappe import _
from frappe.model.document import Document


class ClinicHygieneAudit(Document):
	def validate(self):
		if self.rating and not 1 <= self.rating <= 5:
			frappe.throw(_("Rating must be between 1 and 5"))
