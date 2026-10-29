import frappe
from frappe.model.document import Document

from clinic import stock


class ClinicFirstAidKit(Document):
	def before_insert(self):
		if not self.warehouse:
			self.warehouse = stock.ensure_kit_warehouse(self.kit_name)
