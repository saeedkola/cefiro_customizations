from __future__ import unicode_literals

import frappe

def execute():
	pb_list = frappe.get_all("Product Bundle")
	for bundle in pb_list:
		doc = frappe.get_doc("Product Bundle", bundle.name)
		print(bundle.name)
		pb_list = []
		for item in doc.items:
			pb_list.append([item.item_code,item.qty])

		pb_dict = str(sorted(pb_list))
		doc.pb_dict = pb_dict
		doc.hash = hash(pb_dict)
		doc.save()
		
		frappe.db.commit()
		

