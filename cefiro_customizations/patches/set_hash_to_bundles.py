from __future__ import unicode_literals

import frappe

def execute():
	pb_list = frappe.get_all("Product Bundle")

	for bundle in pb_list:
		sqlq ="""select item_code,qty from `tabProduct Bundle Item` where parent = '{}' order by item_code""".format(bundle.name)
		bundle_items = frappe.db.sql(sqlq,as_list=1)
		frappe.db.set_value("Product Bundle",bundle.name,"hash",hash(str(bundle_items)))
		frappe.db.commit()
		

