import frappe
from frappe.model.document import Document

from clinic import stock


class ClinicFirstAidKit(Document):
	def before_insert(self):
		self.warehouse = stock.ensure_kit_warehouse(self.kit_name)
