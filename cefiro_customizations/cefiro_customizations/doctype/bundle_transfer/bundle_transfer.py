# Copyright (c) 2021, Element Labs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from cefiro_customizations.events import cancel_bundle_movement

class BundleTransfer(Document):
	def on_submit(doc):
		#create Bundle movement entry
		
		for row in doc.product_bundles:
			bundle_items = []
			bundle_items_to = []
			bm_list = frappe.get_all("Bundle Movement",
				filters={
					"product_bundle": row.product_bundle,
					"bundle_batch"	: row.bundle_batch,
					"qty": [">",0]
				})
			bm = frappe.get_doc("Bundle Movement",bm_list[0].name)

			for bundle_item in bm.bundle_items:
				bundle_items.append({
					"item_code": bundle_item.item_code,
					"batch"	: bundle_item.batch,
					"qty"	: bundle_item.qty/bm.qty*row.quantity*-1
					})

				bundle_items_to.append({
					"item_code": bundle_item.item_code,
					"batch"	: bundle_item.batch,
					"qty"	: bundle_item.qty/bm.qty*row.quantity
					})

			bm = frappe.get_doc({
				"doctype":"Bundle Movement",
				"date" : doc.posting_date,
				"product_bundle" : row.product_bundle,
				"bundle_batch": row.bundle_batch,
				"qty" : row.quantity*-1,
				"warehouse": row.from_warehouse,
				"ref_doctype" : "Bundle Transfer",
			 	"ref_docname" : doc.name,
			 	"bundle_items": bundle_items
			})

			bmt = frappe.get_doc({
				"doctype":"Bundle Movement",
				"date" : doc.posting_date,
				"product_bundle" : row.product_bundle,
				"bundle_batch": row.bundle_batch,
				"qty" : row.quantity,
				"warehouse": row.to_warehouse,
				"ref_doctype" : "Bundle Transfer",
			 	"ref_docname" : doc.name,
			 	"bundle_items": bundle_items_to
			})
			bm.save(ignore_permissions=True)
			bmt.save(ignore_permissions=True)
			bm.submit()
			bmt.submit()

	def before_submit(doc):
		#create stock transfer entry
		for row in doc.product_bundles:
			stock_entry_items = []
			bm_list = frappe.get_all("Bundle Movement",
				filters={
					"product_bundle": row.product_bundle,
					"bundle_batch"	: row.bundle_batch,
					"qty": [">",0]
				})
			bm = frappe.get_doc("Bundle Movement",bm_list[0].name)

			for bundle_item in bm.bundle_items:
				stock_entry_items.append({
					"s_warehouse": row.from_warehouse,
					"t_warehouse": row.to_warehouse,					
					"item_code": bundle_item.item_code,
					"batch_no"	: bundle_item.batch,
					"qty"	: bundle_item.qty/bm.qty*row.quantity
					})

			se = frappe.get_doc({
				"doctype"	: "Stock Entry",
				"stock_entry_type"	: "Material Transfer",
				"items"	: stock_entry_items
				})
			se.save(ignore_permissions=True)
			se.submit()
			row.stock_entry = se.name
		
	def on_cancel(doc):
		# cancel bundle movement entry
		# bm_list = frappe.get_all("Bundle Movement",
		# 	filters = {
		# 		"ref_doctype": "Bundle Transfer",
		# 		"ref_docname": doc.name,
		# 		"docstatus": 1
		# 	}
		# )
		# for bm in bm_list:
		# 	bm = frappe.get_doc("Bundle Movement", bm.name)
		# 	bm.docstatus = 2
		# 	bm.save(ignore_permissions = True)
		# 	frappe.delete_doc("Bundle Movement", bm.name)
		cancel_bundle_movement("Bundle Transfer",doc.name)

		#cancel stock entries
		for row in doc.product_bundles:
			se = frappe.get_doc("Stock Entry", row.stock_entry)
			se.docstatus =2
			se.save(ignore_permissions=True)			

	def validate(self):
		pass
