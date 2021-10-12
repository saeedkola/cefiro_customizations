// Copyright (c) 2021, Element Labs and contributors
// For license information, please see license.txt


frappe.ui.form.on('Repackage Bundle', {
		onload: function(frm){
				frm.set_query("warehouse",function(){
						return{
								"filters":{
										"is_group": 0
								}
						}
				})
		},
		get_items: get_unallocated_items
});


function get_unallocated_items(frm,cdt,cdn){
	console.log("Butttton Cliccked");
	if (frm.doc.warehouse){
		frappe.call({
			method: "cefiro_customizations.filters.get_unallocated_items_batch_no",
			args:{warehouse:frm.doc.warehouse},
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
								warehouse: frm.doc.warehouse
							},
							callback:function(r){											
								var response = r.message;
								console.log(response);
								for(var key in response){
									var itemsTable = frm.add_child("items");
									frappe.model.set_value(itemsTable.doctype, itemsTable.name, "item", response[key].item);
									frappe.model.set_value(itemsTable.doctype, itemsTable.name, "batch", response[key].name);
									frappe.model.set_value(itemsTable.doctype, itemsTable.name, "warehouse", response[key].warehouse);

								}
								frm.refresh_fields("items");
							}
						});						
					}
				});				
			}
		});
	}
}	