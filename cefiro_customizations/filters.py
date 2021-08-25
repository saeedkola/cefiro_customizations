import frappe,erpnext,json


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

