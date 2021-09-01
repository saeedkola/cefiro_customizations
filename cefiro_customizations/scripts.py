import frappe







for item in frappe.get_all("Item",filters={
	"has_variants":0,
	"has_batch_no":0},fields=['name','has_batch_no','variant_of']):
	item = frappe.get_doc("Item",item.name)
	if item.variant_of:
		print(item.name)
		item.has_batch_no = frappe.db.get_value("Item",item.name,"has_batch_no")
		item.save()




def before_save_purchase_receipt(doc,methodName=None):
	if doc.product_bundle_inserter:
		unified_list =[]
		for bundle in product_bundle_inserter:
			if bundle.product_bundle:
				product_bundle = frappe.get_doc("Product Bundle", bundle.product_bundle)
				for item in product_bundle.items:
					unified_list.append({
						"item_code": item.item_code,
						"qty": item.qty*bundle.bundle_qty
						})
		doc.items = unified_list
