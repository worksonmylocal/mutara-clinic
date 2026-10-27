import frappe
from frappe import _
from frappe.model.document import Document

from clinic import stock


class ClinicKitIssue(Document):
	def validate(self):
		for row in self.items:
			if (row.qty or 0) <= 0:
				frappe.throw(_("Row {0}: the quantity must be more than zero").format(row.idx))

	def on_submit(self):
		stock.transfer_to_kit(self)

	def on_cancel(self):
		stock.reverse_entry(self)
