import re

import frappe
from frappe import _
from frappe.model.document import Document


class ClinicStaffProfile(Document):
	def validate(self):
		self.validate_lock_pin()
		if self.lock_after_minutes is not None and self.lock_after_minutes != 0:
			if not 1 <= self.lock_after_minutes <= 240:
				frappe.throw(_("Lock Screen After must be between 1 and 240 minutes"))
		elif not self.lock_after_minutes:
			self.lock_after_minutes = None

	def validate_lock_pin(self):
		pin = self.get("screen_lock_pin")
		if not pin or set(pin) == {"*"}:
			return  # empty, or the masked value of a PIN that is already saved
		if not re.fullmatch(r"\d{4}", pin):
			frappe.throw(_("The Screen Lock PIN must be exactly 4 digits"))
