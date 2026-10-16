import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import formatdate, getdate, nowdate

from clinic.utils import age_text


class ClinicPatient(Document):
	def onload(self):
		self.age = age_text(self.date_of_birth)

	def validate(self):
		self.validate_date_of_birth()
		self.validate_type_fields()
		self.age = age_text(self.date_of_birth)

	def validate_date_of_birth(self):
		if self.date_of_birth and getdate(self.date_of_birth) > getdate(nowdate()):
			frappe.throw(
				_("Date of birth {0} is in the future. Check the day and month are the right way round.").format(
					formatdate(self.date_of_birth)
				)
			)

	def validate_type_fields(self):
		if self.patient_type != "Employee":
			self.employee = self.staff_no = self.section = self.department = None
			return
		if self.employee:
			duplicate = frappe.db.exists("Clinic Patient", {"employee": self.employee, "name": ["!=", self.name]})
			if duplicate:
				frappe.throw(_("Employee {0} is already registered as patient {1}").format(self.employee, duplicate))
			if not self.department:
				self.department = frappe.db.get_value("Employee", self.employee, "department")
		if self.staff_no:
			duplicate = frappe.db.exists(
				"Clinic Patient", {"staff_no": self.staff_no, "name": ["!=", self.name]}
			)
			if duplicate:
				frappe.throw(_("Staff no. {0} is already registered as patient {1}").format(self.staff_no, duplicate))
		self.department = self.department or self.section
