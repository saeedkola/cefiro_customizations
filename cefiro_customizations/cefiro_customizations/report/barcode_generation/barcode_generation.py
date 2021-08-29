# Copyright (c) 2013, Element Labs and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):

	sqlq = """select item_code,qty,batch from (
	  select BMI.item_code,BMI.qty,BMI.batch,2 SortOrder from `tabBundle Movement Item` BMI
	  inner join `tabBundle Movement` BM on BMI.parent = BM.name
	  where BM.ref_docname = '{dn}' and BM.ref_doctype = '{dt}'
	  union 
	  select product_bundle,qty,bundle_batch,1 SortOrder from `tabBundle Movement`
	  where ref_docname ='{dn}' and ref_doctype ='{dt}') f
	  order by SortOrder,item_code""".format(dt=filters.ref_doctype,dn=filters.ref_docname)
	
	data = frappe.db.sql(sqlq,as_list=1)
	columns = [
		"Item/Bundle Code:Data:140",
		"Qty:Int:10",
		"Batch No:Data:100"
	]

	# columns, data = [], []
	return columns, data
