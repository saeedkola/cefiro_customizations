// Copyright (c) 2016, Element Labs and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bundle Stock Summary"] = {
	"filters": [
		{
			"fieldname"	: "batch_wise",
			"label"		: "Group by Batch",
			"fieldtype"	: "Check",
			"default"	: 1
		},
		{
			"fieldname"	: "warehouse",
			"label"		: "Group by warehouse",
			"fieldtype"	: "Check",		
			"default"	: 1
		}
	]
};
