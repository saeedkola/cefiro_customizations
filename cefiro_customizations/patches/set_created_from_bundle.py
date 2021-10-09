# Copyright (c) 2017, Frappe and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe

def execute():
    dn_list = frappe.get_all("Delivery Note Item",filters={"docstatus":1})
    for dni in dn_list:
        frappe.db.set_value("Delivery Note Item",dni.name,"created_from_bundle",1,update_modified=False) 

        