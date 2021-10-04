# Copyright (c) 2013, Element Labs and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):

	so = frappe.get_doc("Sales Order",filters.sales_order)
	# pb_list = []
	# for bundle in so.product_bundle_inserter:
	# 	pb_list.append(bundle.product_bundle)

	# if len(pb_list) > 1:
	# 	pb_tuple = tuple(pb_list)
	# else:
	# 	pb_tuple = "('{}')".format(pb_list[0])

	sqlq = """select t1.product_bundle,t2.bundle_batch,t2.warehouse,t2.qty from `tabProduct Bundle Inserter SO` t1 
				left join(
				SELECT product_bundle,bundle_batch,warehouse,ABS(qty) as qty FROM `tabBundle Movement`
				where ref_doctype = 'Sales Order' and ref_docname='{sales_order}'
				) t2 ON t2.product_bundle=t1.product_bundle
				where parent='{sales_order}'""".format(sales_order=filters.sales_order)
	
	data = frappe.db.sql(sqlq)

	columns = [
		"Bundle:Link/Product Bundle:500",
		"Bundle Batch:Data:200",
		"Warehouse:Link/Warehouse:100",
		"Quantity:Int:100"
	]

	return columns, data
