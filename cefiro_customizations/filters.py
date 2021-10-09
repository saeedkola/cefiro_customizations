import frappe,erpnext,json
from collections import defaultdict


@frappe.whitelist()
def get_variant_items(item_template,colour="",size=""):
	sqlq = """Select t1.parent from (
	  SELECT parent,attribute_value AS colour FROM `tabItem Variant Attribute`
	  where variant_of='{item_template}' and attribute='Colour' and attribute_value LIKE '%{colour}%'
	  ) t1
	  INNER JOIN (
	  SELECT parent,attribute_value AS size FROM `tabItem Variant Attribute`
	  where variant_of='{item_template}' and attribute='Size' and attribute_value LIKE '%{size}%'
	  ) t2
	  ON t1.parent = t2.parent;""".format(item_template=item_template,colour=colour,size=size)
	response = frappe.db.sql(sqlq,as_list=1)
	ret = []
	for row in response:
		ret.append(row[0])
	return ret
	
@frappe.whitelist()
def get_unallocated_items_batch_no(warehouse):
	sqlq = """select batch_no from (
		select batch_no,sum(quantity) as quantity,warehouse from `tabUnallocated items`
		where warehouse = '{warehouse}'
		group by batch_no,warehouse
		) t1 where t1.quantity>0""".format(warehouse=warehouse)

	response = frappe.db.sql(sqlq,as_list=1)
	ret = []
	for row in response:
		ret.append(row[0])
	return ret

@frappe.whitelist()
def create_bundle_name(items):
	ic_list = []
	ic_qty = {}
	for item in json.loads(items):
		ic_list.append(item['item_code'])
		ic_qty[item['item_code']] = item['qty']

	if len(ic_list) > 1:
		t = tuple(ic_list)
	else:
		t = "('{}')".format(ic_list[0])
	

	sqlq ="""Select t1.parent,colour,size, variant_of from (
			SELECT parent,attribute_value AS colour, variant_of FROM `tabItem Variant Attribute`
			where attribute='Colour' and parent in {list}
			) t1
			INNER JOIN (
			SELECT parent,attribute_value AS size FROM `tabItem Variant Attribute`
			where attribute='Size' and parent in {list}
			) t2
			ON t1.parent = t2.parent;""".format(list=t)
	response = frappe.db.sql(sqlq,as_dict=1)
	
	str_dict = {}
	
	for row in response:
		variant_of = row['variant_of']
		colour = row['colour']
		size = row['size']
		parent = row['parent']

		if variant_of not in str_dict.keys():
			str_dict[row['variant_of']] = {}

		if row['colour'] not in str_dict[row['variant_of']].keys():
			str_dict[row['variant_of']][row['colour']] = {}
		

		str_dict[variant_of][colour][size] = ic_qty[parent]


	parent_ic = ""
	pack_qty = 0

	for variant_of in sorted(str_dict):
		parent_ic += variant_of + " - "
		for colour in sorted(str_dict[variant_of]):
			parent_ic += colour+"("
			for size in sorted(str_dict[variant_of][colour]):
				qty = str_dict[variant_of][colour][size]
				pack_qty += qty
				qty = str(qty)
				parent_ic += size+"/"+qty+","

			parent_ic = parent_ic[:-1]+") "
	parent_ic+= "Pack of {}".format(pack_qty)

	if len(parent_ic) < 140:
		item = frappe.get_doc({
			"doctype": "Item",
			"item_code": parent_ic,
			"item_name": parent_ic,
			"item_group": "All Item Groups",
			"stock_uom": "Box",
			"is_stock_item": 0
			})
		item.insert(ignore_permissions=True)


	return [parent_ic,len(parent_ic),item.item_code]



	# variant_of
	# 	colour
	# 		size Qty
	# 			pack of {qty}

@frappe.whitelist()
def get_bundle_quantity(product_bundle,bundle_batch=None,warehouse=None):
	sqlq ="""SELECT sum(qty) as qty FROM `tabBundle Movement` 
		WHERE product_bundle='{product_bundle}'""".format(product_bundle=product_bundle)
	if bundle_batch:
		sqlq += """ and bundle_batch='{bundle_batch}'""".format(bundle_batch=bundle_batch)
	if warehouse:
		sqlq += """ and warehouse='{warehouse}'""".format(warehouse=warehouse)
	else:
		sqlq += """ and warehouse!='BM-ST - LII'"""

	sqlq += ";"

	qty = frappe.db.sql(sqlq,as_dict=1)

	return qty

@frappe.whitelist()
def get_details_from_bundle_batch(batch,sales_order=None):
	if sales_order:
		sqlq = """select t1.*,t2.rate from (
				SELECT product_bundle,bundle_batch,warehouse,sum(qty) qty 
				FROM `tabBundle Movement` 
				where bundle_batch="{batch}"
				group by warehouse
				) t1
				left join 
				(
				select product_bundle,rate from `tabProduct Bundle Inserter SO`
				where parent="{sales_order}"
				) t2
				on t1.product_bundle=t2.product_bundle""".format(batch=batch,sales_order=sales_order)
	else:
		sqlq = """SELECT product_bundle,bundle_batch,warehouse,sum(qty) qty 
			FROM `tabBundle Movement` 
			where bundle_batch="{batch}"
			group by warehouse;""".format(batch=batch)

	return frappe.db.sql(sqlq,as_dict=1)
	


@frappe.whitelist()
def get_hsn_from_bundle(bundle):
	gst_a = frappe.db.sql("""SELECT t2.gst_hsn_code FROM `tabProduct Bundle Item` t1 
		left join `tabItem` t2 on t2.name=t1.item_code
		where t1.parent="{}" limit 1""".format(bundle),as_dict=1)
	if gst_a[0]['gst_hsn_code']:
		return gst_a[0]['gst_hsn_code']
	else:
		return ""

@frappe.whitelist()
def get_tax_rate_from_price(price):
	if price > 1000:
		return "18%"
	else:
		return "5%"

@frappe.whitelist()
def get_bundle_rate(product_bundle,sales_order):
	sqlq = """select product_bundle,rate from `tabProduct Bundle Inserter SO`
				where parent='{sales_order}' and product_bundle='{product_bundle}'""".format(sales_order=sales_order,product_bundle=product_bundle)
	return frappe.db.sql(sqlq,as_dict=1)



def fix_all_hsn_codes():
	item_list = frappe.db.sql("select name,variant_of from `tabItem` where variant_of is not null and gst_hsn_code is null",as_dict=1);
	for item in item_list:
		parent_hsn = frappe.db.get_value("Item",item['variant_of'],"gst_hsn_code")
		if parent_hsn:
			doc = frappe.get_doc("Item",item['name'])
			doc.gst_hsn_code = parent_hsn
			doc.save()
			frappe.db.commit()

@frappe.whitelist()
def get_unallocated_items_batch_no(warehouse):
	sqlq = """select batch_no from (
		select batch_no,sum(quantity) as quantity,warehouse from `tabUnallocated items`
		where warehouse = '{warehouse}'
		group by batch_no,warehouse
		) t1 where t1.quantity>0""".format(warehouse=warehouse)

	response = frappe.db.sql(sqlq,as_list=1)
	ret = []
	for row in response:
		ret.append(row[0])
	return ret

