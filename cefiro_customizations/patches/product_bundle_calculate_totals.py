# Copyright (c) 2017, Frappe and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe

def execute():
    pb_list = frappe.get_all("Product Bundle")
    for pb in pb_list:
        pb = frappe.get_doc("Product Bundle", pb.name)
        count = 0
        for item in pb.items:
            count += item.qty
        pb.total_quantity = count
        pb.save()


