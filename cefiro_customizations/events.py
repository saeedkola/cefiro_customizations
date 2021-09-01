import frappe,erpnext,json


@frappe.whitelist()
def get_items_from_bundle_inserter(bundle_list):
	unified_list = []
	bundle_list = json.loads(bundle_list)
	for bundle in bundle_list:
		if "product_bundle" in bundle.keys():
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

@frappe.whitelist()
def get_item_details_from_bundle_inserter(bundle_list):
	pb_list = []
	pb_dict = {}
	for bundle in json.loads(bundle_list):
		pb_list.append(bundle['product_bundle'])
		pb_dict[bundle['product_bundle']] = {
			"bundle_qty" 	: bundle['bundle_qty'],
			"bundle_rate"	: bundle['rate'],
			"warehouse"	 	: bundle['warehouse']
		}
	if len(pb_list) > 1:
		pb_tuple = tuple(pb_list)
	else:
		pb_tuple = "({})".format(pb_list[0])

	sqlq = """SELECT t2.parent,t2.item_code,t2.qty,t3.item_name,t3.description,t3.gst_hsn_code,t3.stock_uom,t3.stock_uom as uom FROM `tabProduct Bundle`t1 
			INNER JOIN `tabProduct Bundle Item` t2
			ON t1.name=t2.parent
			LEFT JOIN `tabItem` t3
			ON t2.item_code = t3.name
			where t1.name IN {list}""".format(list=pb_tuple)

	item_details = frappe.db.sql(sqlq,as_dict=1)
	for item in item_details:		
		item['received_qty'] = item['qty'] = item['qty']*pb_dict[item['parent']]["bundle_qty"]
		item['rate'] = pb_dict[item['parent']]["bundle_rate"]
		item['warehouse'] = pb_dict[item['parent']]['warehouse']
		item['conversion_factor'] = 1
		del item['parent']

	return item_details


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
				"qty"	: bundle_item.qty*row.bundle_qty
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
		frappe.delete_doc("Bundle Movement", bm.name)

def check_if_batch_set(doc,methodName=None):
	if doc.variant_of and (not doc.has_batch_no):
		if frappe.db.get_value("Item",doc.variant_of,"has_batch_no"):
			doc.has_batch_no = 1

