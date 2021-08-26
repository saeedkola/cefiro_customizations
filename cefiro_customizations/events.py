import frappe,erpnext,json


@frappe.whitelist()
def get_items_from_bundle_inserter(bundle_list):
	unified_list = []
	bundle_list = json.loads(bundle_list)
	for bundle in bundle_list:
		product_bundle = frappe.get_doc("Product Bundle", bundle['product_bundle'])
		for item in product_bundle.items:
			unified_list.append({
				"item_code": item.item_code,
				"qty": item.qty*bundle['bundle_qty']
				})

	consolidated_list = {}
	for row in unified_list:
		if row['item_code'] in consolidated_list:
			consolidated_list[row['item_code']] += row['qty']
		else:
			consolidated_list[row['item_code']] = row['qty']

	return consolidated_list

def validate_purchase_receipt(doc,methodName = None):
	pass

def on_submit_purchase_receipt(doc,methodName = None):
	batch_of = {}
	for pr_item in doc.items:
		if pr_item.item_code not in batch_of.keys():
			batch_of[pr_item.item_code] = pr_item.batch_no

	for row in doc.product_bundle_inserter:
		bundle_batch = frappe.get_doc({
			"doctype": "Bundle Batch",
			"posting_date": doc.posting_date,
			"product_bundle": str(row.product_bundle)
			})
		bundle_batch.save(ignore_permissions=True)
		bundle_batch.submit()
		bundle_items = []
		
		pb = frappe.get_doc("Product Bundle",row.product_bundle)
		for bundle_item in pb.items:

			bundle_items.append({
				"item_code": bundle_item.item_code,
				"batch"	: batch_of[bundle_item.item_code],
				"qty"	: bundle_item.qty
				})


		bm = frappe.get_doc({
			"doctype":"Bundle Movement",
			"date" : doc.posting_date,
			"product_bundle" : row.product_bundle,
			"bundle_batch": bundle_batch.name,
			"qty" : row.bundle_qty,
			"ref_doctype" : "Purchase Receipt",
		 	"ref_docname" : doc.name,
		 	"bundle_items": bundle_items
		})
		bm.save(ignore_permissions=True)
		bm.submit()
		
def before_cancel_purchase_receipt(doc,methodName=None):
	bm_list = frappe.get_all("Bundle Movement",filters = {"ref_doctype": "Purchase Receipt","ref_docname": doc.name,"docstatus": 1})
	for bm in bm_list:
		bm = frappe.get_doc("Bundle Movement", bm.name)
		bm.docstatus = 2
		bm.save(ignore_permissions = True)