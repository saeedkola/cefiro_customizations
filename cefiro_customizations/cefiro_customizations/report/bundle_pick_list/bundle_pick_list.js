// Copyright (c) 2016, Element Labs and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bundle Pick List"] = {
	"filters": [
		{
			"fieldname"	: "sales_order",
			"label"		: __("Sales Order"),
			"fieldtype"	: "Link",
			"options"	: "Sales Order",
			"reqd"		: 1
		}
	]
};
