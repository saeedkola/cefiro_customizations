// Copyright (c) 2021, Element Labs and contributors
// For license information, please see license.txt
frappe.ui.form.on('Stock Entry', {
	refresh: function(frm,cdt,cdn){	  
		if(frm.docstatus!==1 || frm.docstatus!==2){
			frm.add_custom_button(__("Get Loose Items"),function(frm){
				console.log("Butttton Cliccked");
				var frm = cur_frm;
				if (frm.doc.from_warehouse){
					frappe.call({
						method: "cefiro_customizations.filters.get_unallocated_items_batch_no",
						args:{warehouse:frm.doc.from_warehouse},
						callback:function(r){
							console.log(r)
							var res_array = r.message;
							new frappe.ui.form.MultiSelectDialog({
								doctype: "Batch",
								target: frm,
								setters:{
									item: ""
								},              
								get_query() {
									return {
										filters:{
												name: ["in",res_array]
										}										
									};
								},
								action(selections) {
									console.log(selections);
									frappe.call({
										method:"cefiro_customizations.filters.get_items_by_batch",
										args:{
											batch_list: selections,
											warehouse: frm.doc.from_warehouse
										},
										callback:function(r){											
											var response = r.message;
											console.log(response);
											for(var key in response){
												var itemsTable = frm.add_child("items");
												frappe.model.set_value(itemsTable.doctype, itemsTable.name, "item_code", response[key].item);
												frappe.model.set_value(itemsTable.doctype, itemsTable.name, "qty", 1);
												frappe.model.set_value(itemsTable.doctype, itemsTable.name, "batch_no", response[key].name);
												frappe.model.set_value(itemsTable.doctype, itemsTable.name, "s_warehouse", response[key].warehouse);
												frappe.model.set_value(itemsTable.doctype, itemsTable.name, "uom", "Pair");
												if(frm.doc.to_warehouse){
													frappe.model.set_value(itemsTable.doctype, itemsTable.name, "t_warehouse", frm.doc.to_warehouse);	
												}

											}
											frm.refresh_fields("items");
										}
									});						
								}
							});				
						}
					});
				}
			});
		}  
	}
});

