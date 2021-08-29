// Copyright (c) 2016, Element Labs and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Barcode Generation"] = {
	"filters": [
		{
			"fieldname"	: "ref_doctype",
			"label"		: __("Ref Doctype"),
			"fieldtype"	: "Link",
			"options"	: "DocType",
			"reqd"		: 1
		},
		{
			"fieldname"	: "ref_docname",
			"label"		: __("Ref Docname"),
			"fieldtype"	: "Data",
			"reqd"		: 1
		}
	]
};
