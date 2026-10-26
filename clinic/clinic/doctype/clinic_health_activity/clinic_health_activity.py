import frappe
from frappe.model.document import Document


class ClinicHealthActivity(Document):
	def validate(self):
		self.attendance_pct = (
			round(self.attendees * 100 / self.expected_attendees, 1) if self.expected_attendees and self.attendees else 0
		)
