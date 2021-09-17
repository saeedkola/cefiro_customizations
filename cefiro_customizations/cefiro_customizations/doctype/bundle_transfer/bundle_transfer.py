# Copyright (c) 2021, Element Labs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class BundleTransfer(Document):
	def on_submit(self):
		#create Bundle movement entry

		#create stock transfer entry
		pass
	def validate(self):
		pass
