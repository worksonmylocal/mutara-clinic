import frappe
from frappe.model.document import Document
from frappe.utils import get_first_day


class ClinicMonthlyReport(Document):
	def validate(self):
		self.period_start = get_first_day(self.period_start)
		if not self.prepared_by:
			self.prepared_by = frappe.db.get_value("User", frappe.session.user, "full_name")
