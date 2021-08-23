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

def on_submit_purchase_receipt(doc,methodName = None):
	for row in doc.product_bundle_inserter:
		bm = frappe.get_doc({
			"doctype":"Bundle Movement",
			"date" : doc.posting_date,
			"product_bundle" : row.product_bundle,
			"qty" : row.bundle_qty,
			"ref_doctype" : "Purchase Receipt",
		 	"ref_docname" : doc.name
		})
		bm.save(ignore_permissions=True)
		bm.submit()
		
def before_cancel_purchase_receipt(doc,methodName=None):
	bm_list = frappe.get_all("Bundle Movement",filters = {"ref_doctype": "Purchase Receipt","ref_docname": doc.name,"docstatus": 1})
	for bm in bm_list:
		bm = frappe.get_doc("Bundle Movement", bm.name)
		bm.docstatus = 2
		bm.save(ignore_permissions = True)