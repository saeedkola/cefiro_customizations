// Copyright (c) 2021, Element Labs and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Receipt Import', {
	get_column_names: function(frm) {
		if(frm.doc.excel_file){
			frappe.call({
		      method: "cefiro_customizations.helpers.get_column_names",
		      args:{
		        file_name: frm.doc.excel_file
		      },
		      callback: function(r){
		        console.log(r.message);
		        var columns = r.message;
		        if (columns){
		        	for (var i in columns){
		        		var itemsTable = frm.add_child("column_map");
                        frappe.model.set_value(itemsTable.doctype, itemsTable.name, "excel_column", columns[i].excel_column);                        
		        	}
		        	frm.refresh_fields("column_map");
		        }
		       }		   
		    });
		}else{

		}
	}
});
