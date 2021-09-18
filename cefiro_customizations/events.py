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
def get_item_details_from_bundle_inserter(bundle_list,set_warehouse=None,delivery_date=None):
	pb_list = []
	pb_dict = {}
	for bundle in json.loads(bundle_list):
		pb_list.append(bundle['product_bundle'])
		pb_dict[bundle['product_bundle']] = {
			"bundle_qty" 	: bundle['bundle_qty'],
			"bundle_rate"	: bundle['rate']
		}
		if 'warehouse' in bundle.keys():
			pb_dict[bundle['product_bundle']]['warehouse'] = bundle['warehouse']
		elif set_warehouse:
			pb_dict[bundle['product_bundle']]['warehouse'] = set_warehouse


	if len(pb_list) > 1:
		pb_tuple = tuple(pb_list)
	else:
		pb_tuple = "('{}')".format(pb_list[0])

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
		item['created_from_bundle'] = 1
		if delivery_date:
			item['delivery_date'] = delivery_date
		item['conversion_factor'] = 1
		del item['parent']

	return item_details

@frappe.whitelist()
def get_item_details_from_bundle_inserter_delivery_note(bundle_list,sales_order=None):
	item_list = []
	for bundle in json.loads(bundle_list):
		sqlq = """select b.item_code,b.qty*{bundle_qty}/a.qty qty,b.batch as batch_no, 1 as created_from_bundle,t3.item_name,t3.description,t3.gst_hsn_code,t3.stock_uom as uom,t3.stock_uom, a.warehouse
				from `tabBundle Movement` a
				inner join `tabBundle Movement Item` b on a.name = b.parent
				LEFT JOIN `tabItem` t3 ON b.item_code = t3.name
				where a.warehouse = '{warehouse}' and 
				a.product_bundle = '{product_bundle}' 
				and a.bundle_batch = '{bundle_batch}'
				and a.docstatus = 1;""".format(
					bundle_qty=bundle['bundle_qty'], 
					warehouse=bundle['warehouse'], 
					bundle_batch=bundle['bundle_batch'],
					product_bundle = bundle['product_bundle'])

		items = frappe.db.sql(sqlq, as_dict=1)
		if bundle['rate'] or sales_order:
			for item in items:
				if bundle['rate']:
					item['rate'] = bundle['rate']

				if sales_order:
					item['against_sales_order'] = sales_order

		item_list += items
	return item_list


def validate_purchase_receipt(doc,methodName = None):
	pass

def before_submit_purchase_receipt(doc,methodName = None):
	#force all batch numbers in one transaction for an item code to be same
	batch_dict = {}
	for item in doc.items:
		if item.item_code in batch_dict.keys():
			if item.batch_no and item.batch_no != batch_dict[item.item_code]:
				item.batch_no = batch_dict[item.item_code]
		else:
			batch_dict[item.item_code] = item.batch_no

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
			"warehouse": row.warehouse,
			"ref_doctype" : "Purchase Receipt",
		 	"ref_docname" : doc.name,
		 	"bundle_items": bundle_items
		})
		bm.save(ignore_permissions=True)
		bm.submit()

def on_submit_delivery_note(doc,methodName=None):
	
	for row in doc.product_bundle_inserter:
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
			"date" : doc.posting_date,
			"product_bundle" : row.product_bundle,
			"bundle_batch": row.bundle_batch,
			"qty" : row.bundle_qty*-1,
			"warehouse": row.warehouse,
			"ref_doctype" : "Delivery Note",
		 	"ref_docname" : doc.name,
		 	"bundle_items": bundle_items
		})
		bm.save(ignore_permissions=True)
		bm.submit()
	if doc.against_sales_order:
		delete_reserved_entries(doc.against_sales_order)

def before_cancel_delivery_note(doc,methodName=None):	
	cancel_bundle_movement("Delivery Note",doc.name)

def before_cancel_purchase_receipt(doc,methodName=None):
	cancel_bundle_movement("Purchase Receipt",doc.name)

def check_if_batch_set(doc,methodName=None):
	if doc.variant_of and (not doc.has_batch_no):
		if frappe.db.get_value("Item",doc.variant_of,"has_batch_no"):
			doc.has_batch_no = 1

def cancel_bundle_movement(ref_doctype,ref_docname):
	bm_list = frappe.get_all("Bundle Movement",
		filters = {
			"ref_doctype": ref_doctype,
			"ref_docname": ref_docname,
			"docstatus": 1
		}
	)
	for bm in bm_list:
		bm = frappe.get_doc("Bundle Movement", bm.name)
		
		bm.docstatus = 2
		bm.save(ignore_permissions = True)
		frappe.delete_doc("Bundle Movement", bm.name)


def on_submit_sales_order(doc,methodName=None):
	if doc.product_bundle_inserter:
		for row in doc.product_bundle_inserter:
			sqlq = """SELECT product_bundle,bundle_batch,warehouse,sum(qty) as qty FROM `tabBundle Movement`
			 where product_bundle='{}' and docstatus in (0,1)
			 group by product_bundle, bundle_batch,warehouse 	
			 ORDER BY bundle_batch""".format(row.product_bundle)

			data = frappe.db.sql(sqlq,as_dict=1)
			req_qty = row.bundle_qty
			allocated_qty = 0
			batch_list = []
			for batch in data:
				if batch.qty <= (req_qty - allocated_qty):
					# reserve full row
					bat_reserve_qty = batch.qty

				elif batch.qty > (req_qty - allocated_qty):
					#reserve req_qty - allocated_qty
					bat_reserve_qty = req_qty - allocated_qty
				

				allocated_qty += bat_reserve_qty
				if bat_reserve_qty:
					bm = frappe.get_doc({
							"doctype":"Bundle Movement",
							"date" : doc.transaction_date,
							"product_bundle" : batch.product_bundle,
							"bundle_batch": batch.bundle_batch,
							"qty" : bat_reserve_qty*-1,
							"warehouse": batch.warehouse,
							"ref_doctype" : "Sales Order",
						 	"ref_docname" : doc.name			
						})
					bm.save(ignore_permissions=True)


def on_cancel_sales_order(doc,methodName=None):
	delete_reserved_entries(doc.name)

def delete_reserved_entries(sales_order):
	bm_list = frappe.get_all("Bundle Movement",
		filters = {
			"ref_doctype": "Sales Order",
			"ref_docname": sales_order,
			"docstatus": 0
		}
	)
	for bm in bm_list:
		bm = frappe.get_doc("Bundle Movement", bm.name)		
		frappe.delete_doc("Bundle Movement", bm.name)

	#on cancel delivery note
		#reserve again