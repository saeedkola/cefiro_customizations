# Copyright (c) 2021, Element Labs and contributors
# For license information, please see license.txt

import frappe,json
from frappe.model.document import Document
from cefiro_customizations.events import get_item_details_from_bundle_inserter_delivery_note

class ConsumeBundle(Document):
	def validate(self):
		if self.product_bundles:
			for row in self.product_bundles:
				sqlq = """select t1.product_bundle,t1.qty,t1.bundle_batch,t1.warehouse,t2.item_code,t2.batch as item_batch,t2.qty/t1.qty*{bundle_qty} as item_qty from `tabBundle Movement` t1 
						left join `tabBundle Movement Item` t2 on t1.name =t2.parent
						where t1.bundle_batch='{bundle_batch}' and t1.qty>0""".format(
							bundle_qty=row.bundle_qty,
							bundle_batch=row.bundle_batch
							)
				item_list = frappe.db.sql(sqlq,as_dict=1)
				self.set("consumed_items",[])

				for item in item_list:
					self.append("consumed_items",{
						"item"	:	item['item_code'],
						"batch"	: item['item_batch'],
						"qty"	: item['item_qty'],
						"warehouse"	: row.warehouse
					})


	def before_submit(self):
		for row in self.product_bundles:
			bundle_items = []
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
					"qty"	: bundle_item.qty/bm.qty*row.bundle_qty*-1
					})

			bm = frappe.get_doc({
				"doctype":"Bundle Movement",
				"date" : self.posting_date,
				"product_bundle" : row.product_bundle,
				"bundle_batch": row.bundle_batch,
				"qty" : row.bundle_qty*-1,
				"warehouse": row.warehouse,
				"ref_doctype" : "Consume Bundle",
			 	"ref_docname" : self.name,
			 	"bundle_items": bundle_items
			})
			bm.save(ignore_permissions=True)
			bm.submit()


		for row in self.consumed_items:
			unalloc = frappe.get_doc({
				"doctype": "Unallocated items",
				"item": row.item,
				"batch_no": row.batch,
				"quantity": row.qty,
				"warehouse": row.warehouse,
				"ref_doctype":"Consume Bundle",
				"ref_docname":self.name
				})
			unalloc.save(ignore_permissions=True)
			unalloc.submit()
