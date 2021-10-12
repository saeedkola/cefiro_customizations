# Copyright (c) 2021, Element Labs and contributors
# For license information, please see license.txt

import frappe,json
from frappe.model.document import Document
from cefiro_customizations.filters import create_bundle_name

class RepackageBundle(Document):
	def validate(doc):
		pb_list = []

		for item in doc.items:
			pb_list.append([item.item,float(item.qty)])

		# frappe.logger().debug(pb_list)
		pb_dict = doc.pb_dict=str(sorted(pb_list))
		doc.pb_hash=hash(pb_dict)

	def before_submit(doc):
		existing_bundles = frappe.get_list("Product Bundle",filters={'pb_dict':doc.pb_dict})
		if existing_bundles:
			product_bundle = existing_bundles[0].name

		else:
			item_list = []
			for item in doc.items:
				item_list.append({
					"item_code": item.item,
					"qty": item.qty
					})
			pb_name = create_bundle_name(json.dumps(item_list))

			pb = frappe.get_doc({
				"doctype": "Product Bundle",
				"new_item_code": pb_name[2]
				})
			for item in doc.items:
				pb.append("items",{
					"item_code": item.item,
					"qty": item.qty
					})
			pb.save(ignore_permissions=True)
			product_bundle = pb.name


		bundle_batch = frappe.get_doc({
			"doctype": "Bundle Batch",
			"posting_date": doc.posting_date,
			"product_bundle": str(product_bundle)
		})
		bundle_batch.save(ignore_permissions=True)
		bundle_batch.submit()

		bm = frappe.get_doc({
			"doctype": "Bundle Movement",
			"date": doc.posting_date,
			"product_bundle": product_bundle,
			"bundle_batch": bundle_batch.name,
			"qty": 1,
			"warehouse": doc.warehouse,
			"ref_doctype": "Repackage Bundle",
			"ref_docname": doc.name
		})

		for item in doc.items:
			unalloc = frappe.get_doc({
				"doctype": "Unallocated items",
				"item": item.item,
				"batch_no": item.batch,
				"quantity": item.qty*-1,
				"warehouse": doc.warehouse,
				"ref_doctype": "Repackage Bundle",
				"ref_docname": doc.name
				})
			unalloc.save(ignore_permissions=True)
			unalloc.submit()

			bm.append("bundle_items",{
				"item_code": item.item,
				"batch": item.batch,
				"qty": item.qty
			})

		bm.save(ignore_permissions=True)
		bm.submit()





