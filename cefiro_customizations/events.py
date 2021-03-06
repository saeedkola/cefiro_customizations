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
def get_item_details_from_bundle_inserter_delivery_note(bundle_list,sales_order=""):
	item_list = []	

	for bundle in json.loads(bundle_list):
		if bundle['rate']:
			rate = bundle['rate']
		else:
			rate = 0
		sqlq = """select b.item_code,b.qty*{bundle_qty}/a.qty qty,b.batch as batch_no, 
				1 as created_from_bundle,t3.item_name,t3.description,
				t3.gst_hsn_code,t3.stock_uom as uom,t3.stock_uom, a.warehouse,
				'{sales_order}' as against_sales_order, {rate} as rate
				from (
					select name,product_bundle,bundle_batch,qty,warehouse from `tabBundle Movement` 
					where product_bundle = '{product_bundle}' and bundle_batch='{bundle_batch}' and warehouse="{warehouse}" and docstatus=1 and qty>0
					order by creation limit 1
				) a
				inner join `tabBundle Movement Item` b on a.name = b.parent
				LEFT JOIN `tabItem` t3 ON b.item_code = t3.name
					""".format(
						bundle_qty=bundle['bundle_qty'], 
						bundle_batch=bundle['bundle_batch'],
						product_bundle = bundle['product_bundle'],
						sales_order=sales_order,
						warehouse = bundle['warehouse'],
						rate=rate)


		items = frappe.db.sql(sqlq, as_dict=1)

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
	for item in doc.items:
		if not item.created_from_bundle:
			uan = frappe.get_doc({
					"doctype": "Unallocated items",
					"item": item.item_code,
					"batch_no": item.batch_no,
					"quantity": item.qty*1,
					"warehouse": item.warehouse,
					"ref_doctype": "Purchase Receipt",
					"ref_docname": doc.name
					})

			uan.save(ignore_permissions=True)
			uan.submit()

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

	for item in doc.items:
		if not item.created_from_bundle:
			uan = frappe.get_doc({
					"doctype": "Unallocated items",
					"item": item.item_code,
					"batch_no": item.batch_no,
					"quantity": item.qty*-1,
					"warehouse": item.warehouse,
					"ref_doctype": "Delivery Note" ,
					"ref_docname": doc.name
					})

			uan.save(ignore_permissions=True)
			uan.submit()


def validate_delivery_note(doc,methodName=None):
	for row in doc.items:
		if not row.created_from_bundle:
			sqlq = """select batch_no,sum(quantity) as quantity,warehouse from `tabUnallocated items`
					where warehouse = '{warehouse}' and batch_no="{batch_no}" and docstatus=1""".format(
						warehouse=row.warehouse,
						batch_no=row.batch_no
					)
			count = frappe.db.sql(sqlq,as_dict=1)
			if count[0]['quantity']:
				if row.qty>count[0]['quantity']:
					frappe.throw("Only {qty} qty available for Batch No {batch_no} in {warehouse}. Row {idx}".format(
						qty=count[0]['quantity'],
						batch_no=row.batch_no,
						warehouse=row.warehouse,
						idx=row.idx))
			else:
				frappe.throw("No loose qty available for Batch No {batch_no} in {warehouse}. Row {idx}".format(					
						batch_no=row.batch_no,
						warehouse=row.warehouse,
						idx=row.idx))


def before_cancel_delivery_note(doc,methodName=None):	
	cancel_bundle_movement("Delivery Note",doc.name)
	cancel_unalloc_items("Delivery Note",doc.name)

def before_cancel_purchase_receipt(doc,methodName=None):
	cancel_bundle_movement("Purchase Receipt",doc.name)
	cancel_unalloc_items("Purchase Receipt",doc.name)

def before_cancel_consume_bundle(doc,methodName=None):
	cancel_bundle_movement("Consume Bundle",doc.name)
	cancel_unalloc_items("Consume Bundle",doc.name)	

def before_cancel_repackage_bundle(doc,methodName=None):
	cancel_bundle_movement("Repackage Bundle",doc.name)
	cancel_unalloc_items("Repackage Bundle",doc.name)	

def check_if_batch_set(doc,methodName=None):
	if doc.variant_of and (not doc.has_batch_no):
		if frappe.db.get_value("Item",doc.variant_of,"has_batch_no"):
			doc.has_batch_no = 1
	if doc.variant_of and (not doc.gst_hsn_code):
		parent_hsn_code = frappe.db.get_value("Item",doc.variant_of,"gst_hsn_code")
		if parent_hsn_code:
			doc.gst_hsn_code = parent_hsn_code

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

def cancel_unalloc_items(ref_doctype,ref_docname):
	unalloc_list = frappe.get_all("Unallocated items",
		filters = {
			"ref_doctype": ref_doctype,
			"ref_docname": ref_docname,
			"docstatus": 1
		}
	)
	for doc in unalloc_list:
		ua = frappe.get_doc("Unallocated items", doc.name)
		
		ua.docstatus = 2
		ua.save(ignore_permissions = True)
		frappe.delete_doc("Unallocated items", doc.name)


def on_submit_sales_order(doc,methodName=None):
	if doc.product_bundle_inserter:
		for row in doc.product_bundle_inserter:
			sqlq = """SELECT product_bundle,bundle_batch,warehouse,sum(qty) as qty FROM `tabBundle Movement` t1
			 left join `tabWarehouse` t2 on t1.warehouse = t2.name
			 where ifnull(t2.warehouse_type,"") != "Retention" and
			 product_bundle='{}' and t1.docstatus in (0,1)
			 group by product_bundle, bundle_batch,warehouse
			 having qty>0
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

def update_taxes_on_items(settings):
	item_list = frappe.db.sql("select name from tabItem where has_variants=1",as_dict=1)
	for item in item_list:
		frappe.logger().debug(item['name'])
		doc = frappe.get_doc("Item",item['name'])
		taxes_a = []
		doc.set("taxes",[])
		for tax in settings.taxes:
			doc.append('taxes',{
				"item_tax_template" : tax.item_tax_template,
				"tax_category"		: tax.tax_category,
				"valid_from"		: tax.valid_from,
				"minimum_net_rate"	: tax.minimum_net_rate,
				"maximum_net_rate"	: tax.maximum_net_rate,
				"modified"			: tax.modified
				})


		doc.save(ignore_version=True)

def validate_product_bundle(doc,methodName=None):
	pb_list = []
	for item in doc.items:
		pb_list.append([item.item_code,item.qty])

	pb_dict = str(sorted(pb_list))
	doc.pb_dict = pb_dict
	doc.hash = hash(pb_dict)

def before_submit_stock_entry(doc,methodName=None):
	if (doc.stock_entry_type == "Material Transfer"):
		if not doc.is_bundle_movement:
			for item in doc.items:
				uap = frappe.get_doc({
					"doctype": "Unallocated items",
					"item": item.item_code,
					"batch_no": item.batch_no,
					"quantity": item.qty,
					"warehouse": item.t_warehouse,
					"ref_doctype": "Stock Entry" ,
					"ref_docname": doc.name
					})

				uap.save(ignore_permissions=True)
				uap.submit()

				uan = frappe.get_doc({
					"doctype": "Unallocated items",
					"item": item.item_code,
					"batch_no": item.batch_no,
					"quantity": item.qty*-1,
					"warehouse": item.s_warehouse,
					"ref_doctype": "Stock Entry" ,
					"ref_docname": doc.name
					})
				uan.save(ignore_permissions=True)
				uan.submit()


def before_cancel_stock_entry(doc,methodName=None):
	cancel_unalloc_items("Stock Entry",doc.name)

def validate_stock_entry(doc,methodName=None):
	if (doc.stock_entry_type == "Material Transfer"):
		if not doc.is_bundle_movement:
			for item in doc.items:
				sqlq = """select batch_no,sum(quantity) as quantity,warehouse from `tabUnallocated items`
						where warehouse = '{warehouse}' and batch_no="{batch_no}" and docstatus=1""".format(
							warehouse=item.s_warehouse,batch_no=item.batch_no)
				count = frappe.db.sql(sqlq,as_dict=1)
				if count[0]['quantity']:
					if item.qty>count[0]['quantity']:
						frappe.throw("Only {qty} qty available for Batch No {batch_no} in {warehouse}. Row {idx}".format(
							qty=count[0]['quantity'],
							batch_no=item.batch_no,
							warehouse=item.s_warehouse,
							idx=item.idx))
				else:
					frappe.throw("No loose qty available for Batch No {batch_no} in {warehouse}. Row {idx}".format(					
						batch_no=item.batch_no,
						warehouse=item.s_warehouse,
						idx=item.idx))