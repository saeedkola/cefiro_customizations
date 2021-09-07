# Copyright (c) 2013, Element Labs and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	if filters.batch_wise and filters.warehouse:
		sqlq = """SELECT product_bundle,bundle_batch,warehouse,sum(qty) as qty FROM `tabBundle Movement` 
			group by product_bundle, bundle_batch,warehouse ORDER BY product_bundle;"""
		columns = [
			"Bundle:Link/Product Bundle:300",
			"Bundle Batch:Data:200",
			"Warehouse:Link/Warehouse:100",
			"Quantity:Int:100"
		]
	else:
		if filters.batch_wise:
			sqlq ="""SELECT product_bundle,bundle_batch,sum(qty) as qty FROM `tabBundle Movement` 
					group by product_bundle, bundle_batch ORDER BY product_bundle;"""
			columns = [
				"Bundle:Link/Product Bundle:300",
				"Bundle Batch:Data:200",
				"Quantity:Int:100"
			]
		elif filters.warehouse:
			sqlq = """SELECT product_bundle,warehouse,sum(qty) as qty FROM `tabBundle Movement` 
				group by product_bundle, warehouse ORDER BY product_bundle;"""

			columns = [
				"Bundle:Link/Product Bundle:300",			
				"Warehouse:Link/Warehouse:100",
				"Quantity:Int:100"
			]
		else:
			sqlq = """SELECT product_bundle,sum(qty) as qty FROM `tabBundle Movement` 
				group by product_bundle, warehouse ORDER BY product_bundle;"""

			columns = [
				"Bundle:Link/Product Bundle:300",				
				"Quantity:Int:100"
			]



	data = frappe.db.sql(sqlq,as_list=1)
	return columns, data
