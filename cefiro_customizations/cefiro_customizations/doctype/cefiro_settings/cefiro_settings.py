# Copyright (c) 2021, Element Labs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import enqueue

class CefiroSettings(Document):
	def on_update(self):
		enqueue('cefiro_customizations.events.update_taxes_on_items',settings=self)



