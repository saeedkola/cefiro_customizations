frappe.ui.form.on('Delivery Note',{
	get_items: function(frm,cdt,cdn){
      if(frm.doc.product_bundle_inserter){
        set_default_warehouse(frm,cdt,cdn);
        if(validate_pbi(frm,cdt,cdn)){
          frappe.call({
            method: "cefiro_customizations.events.get_item_details_from_bundle_inserter_delivery_note",
            args: {
              bundle_list : frm.doc.product_bundle_inserter,
              sales_order: frm.doc.against_sales_order
            },
            callback: function(r){        
              frm.set_value("items",r.message);
              frm.refresh_field("items");
              console.log(frm.doc.items);
            }
          });
        }else{
          console.log("PBI Invalidated");
        }
        
      }else{
        console.log("False");
      }
    },
    set_warehouse: function(frm,cdt,cdn){
    	set_default_warehouse(frm,cdt,cdn);
    },
    validate:function(frm,cdt,cdn){
    	set_default_warehouse(frm,cdt,cdn);
    	validate_pbi(frm,cdt,cdn);
    },
    scan_bundle_batch_barcode: on_batch_trigger
});

function on_batch_trigger(frm,cdt,cdn){
  if(!frm.doc.against_sales_order && !frm.doc.override_sales_order_mandate){
    frappe.throw("Sales Order Not Set");
  }
  if(frm.doc.scan_bundle_batch_barcode){
    frappe.call({
      method: "cefiro_customizations.filters.get_details_from_bundle_batch",
      args:{
        batch: frm.doc.scan_bundle_batch_barcode,
        sales_order: frm.doc.against_sales_order
      },
      callback: function(r){      
        var res = r.message;
        if(res.length){
          if (res.length > 1){
            var options ="";
            for (var key in res){
              var wh =  res[key].warehouse;
              options += "\n"+wh;
            }
            let d = new frappe.ui.Dialog({
              title: 'Select Warehouse',
              fields: [
                  {
                      label: 'warehouse',
                      fieldname: 'warehouse',
                      fieldtype: 'Select',
                      options: options
                  }
              ],
              primary_action_label: 'Insert',
              primary_action(values) {
                  
                  for( var key in res){
                    if(res[key].warehouse == values.warehouse){
                      add_child_to_pbi(res[key].product_bundle,res[key].bundle_batch,res[key].warehouse,frm.doc.product_bundle_inserter,res[key].rate);
                    }
                  }                  
                  frm.set_value("scan_bundle_batch_barcode","");
                  d.hide();
                  $("[data-fieldname=scan_bundle_batch_barcode]").focus();
              }
            });
            d.show();
        
          }else{           
            add_child_to_pbi(res[0].product_bundle,res[0].bundle_batch,res[0].warehouse,frm.doc.product_bundle_inserter,res[0].rate);
            frm.set_value("scan_bundle_batch_barcode","");
            $("[data-fieldname=scan_bundle_batch_barcode]").focus();

          }
        }
      }
    });
  }
}

function add_child_to_pbi(product_bundle,batch,warehouse,pbi,rate){
  if(!rate){
    if(cur_frm.doc.sales_order){
      frappe.throw("Bundle not in sales order");
    }else{
      rate = 0;
    }
  }
  var check = check_if_exists_in_pbi(batch,warehouse,pbi);
  if(!check){
    var bundle = cur_frm.add_child("product_bundle_inserter");
    bundle.product_bundle = product_bundle;
    bundle.bundle_batch = batch;
    bundle.warehouse = warehouse;
    bundle.rate=rate;
    cur_frm.refresh_field("product_bundle_inserter"); 
  }
  
  
}


function check_if_exists_in_pbi(batch,warehouse,pbi){
  var key = 0;
  console.log(pbi);
    for(const row in pbi){
      console.log(pbi[row]);
      if(pbi[row].bundle_batch == batch){
        if(pbi[row].warehouse == warehouse){
          cur_frm.get_field("product_bundle_inserter").grid.grid_rows[row].doc.bundle_qty = pbi[row].bundle_qty+1;
          cur_frm.get_field("product_bundle_inserter").grid.grid_rows[row].refresh_field("bundle_qty");
          return true;

        }      
      }
      key++;
    }
   
  return false;
}

function validate_pbi(frm,cdt,cdn){  
  $.each(frm.doc.product_bundle_inserter,function(key,row){
    if(!row.product_bundle || !row.bundle_batch || !row.warehouse){
      let row_no = row.idx;
      let message = `Mandatory fields not set in row ${row_no}`;
      frappe.throw(__(message));
      return false;

      
    }
  });
  return true;
}

//bundle batch filter based on available qty
frappe.ui.form.on("Delivery Note", "refresh", function(frm) {
	frm.fields_dict['product_bundle_inserter'].grid.get_field('bundle_batch').get_query = function(doc, cdt, cdn) {
		var child = locals[cdt][cdn];		
		return{	
			filters:[
				['product_bundle', '=', child.product_bundle]		
			],

		}
	}
});

function set_default_warehouse(frm,cdt,cdn){
  $.each(frm.doc.product_bundle_inserter||[],function(key,row){
    if(!row.warehouse && frm.doc.set_warehouse){        
      row.warehouse = frm.doc.set_warehouse;
    }
  });
  frm.refresh_field("product_bundle_inserter");
}

frappe.ui.form.on('Product Bundle Inserter', {
	product_bundle: function(frm,cdt,cdn) {
		var row = locals[cdt][cdn];
		row.warehouse = frm.doc.set_warehouse;
		frm.refresh_field("product_bundle_inserter");
    get_available_qty(frm,cdt,cdn);
    get_price_from_sales_order(frm,cdt,cdn);
	},
  warehouse: get_available_qty,
  bundle_batch: get_available_qty,
  bundle_qty:function(frm,cdt,cdn){
    var row = locals[cdt][cdn];
    if (row.bundle_qty > row.available_qty){
      let row_no = row.idx;
      let message = `Available Qty less than Bundle Qty in row ${row_no}`;
      frappe.msgprint(__(message));
    }
  }
});

function get_available_qty(frm,cdt,cdn){
  var row = locals[cdt][cdn];
  if (row.product_bundle){
    var args = {
      product_bundle: row.product_bundle
    }
    if (row.bundle_batch){
      args['bundle_batch'] = row.bundle_batch
    }
    if (row.warehouse){
      args['warehouse'] = row.warehouse
    }
    frappe.call({
      method: "cefiro_customizations.filters.get_bundle_quantity",
      args : args,
      callback: function(r){
        console.log(r.message);
        var av_qty = r.message[0].qty;
        if (av_qty !== null){
          row.available_qty = av_qty;
        }else{
          row.available_qty = 0;
        }
        frm.refresh_field("product_bundle_inserter");
      }
    })
  }
}

function get_price_from_sales_order(frm,cdt,cdn){
  var row = locals[cdt][cdn];
  if (row.product_bundle){
    if(!frm.doc.against_sales_order){
      if(!frm.doc.override_sales_order_mandate){
        frappe.throw("Sales Order Not Set");
      }
    }else{
      var args = {
        product_bundle: row.product_bundle,
        sales_order: frm.doc.against_sales_order
      }
      frappe.call({
        method: "cefiro_customizations.filters.get_bundle_rate",
        args : args,
        callback: function(r){
          console.log(r.message);
          var rate = r.message[0].rate;
          if (rate !== null){
            row.rate = rate;
          }else{
            row.rate = 0;
          }
          frm.refresh_field("product_bundle_inserter");
        }
      })
    }    
  } 
}



frappe.ui.form.on('Delivery Note', {
  refresh: function(frm,cdt,cdn){    
    if(frm.docstatus!==1 || frm.docstatus!==2){
      frm.add_custom_button(__("Get Loose Items"),function(frm){
        // console.log("Butttton Cliccked");
        var frm = cur_frm;
        if (frm.doc.set_warehouse){
          frappe.call({
            method: "cefiro_customizations.filters.get_unallocated_items_batch_no",
            args:{warehouse:frm.doc.set_warehouse},
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
                      warehouse: frm.doc.set_warehouse
                    },
                    callback:function(r){                      
                      var response = r.message;
                      console.log(response);
                      for(var key in response){
                        var itemsTable = frm.add_child("items");
                        frappe.model.set_value(itemsTable.doctype, itemsTable.name, "item_code", response[key].item);
                        frappe.model.set_value(itemsTable.doctype, itemsTable.name, "qty", 1);
                        frappe.model.set_value(itemsTable.doctype, itemsTable.name, "batch_no", response[key].name);
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
      });
    }  
  }
});
