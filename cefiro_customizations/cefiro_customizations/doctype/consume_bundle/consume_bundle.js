// Copyright (c) 2021, Element Labs and contributors
// For license information, please see license.txt

frappe.ui.form.on('Consume Bundle', {
	refresh: function(frm) {
		frm.fields_dict['product_bundles'].grid.get_field('bundle_batch').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			return{	
				filters:[
					['product_bundle', '=', child.product_bundle]
				]
			}
		}
	},
	scan_bundle_batch_barcode: on_batch_trigger
});

// frappe.ui.form.on('Consume Bundle',{
//   refresh: function(frm,cdt,cdn){
//     if(frm.doc.docstatus == 1){
//       frm.add_custom_button(__("Repack"),function(){
//         new frappe.ui.form.MultiSelectDialog({})
//       });
//     }
//   }
// })


frappe.ui.form.on('Product Bundle Inserter', {
	product_bundle: function(frm,cdt,cdn) {
		var row = locals[cdt][cdn];
		row.warehouse = frm.doc.set_warehouse;
		frm.refresh_field("product_bundles");
    	get_available_qty(frm,cdt,cdn);
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
        frm.refresh_field("product_bundles");
      }
    })
  }
}


function on_batch_trigger(frm,cdt,cdn){
  if(frm.doc.scan_bundle_batch_barcode){
    frappe.call({
      method: "cefiro_customizations.filters.get_details_from_bundle_batch",
      args:{
        batch: frm.doc.scan_bundle_batch_barcode      
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
                      add_child_to_pbi(res[key].product_bundle,res[key].bundle_batch,res[key].warehouse,frm.doc.product_bundles,res[key].rate);
                    }
                  }                  
                  frm.set_value("scan_bundle_batch_barcode","");
                  d.hide();
                  $("[data-fieldname=scan_bundle_batch_barcode]").focus();
              }
            });
            d.show();
        
          }else{           
            add_child_to_pbi(res[0].product_bundle,res[0].bundle_batch,res[0].warehouse,frm.doc.product_bundles);
            frm.set_value("scan_bundle_batch_barcode","");
            $("[data-fieldname=scan_bundle_batch_barcode]").focus();

          }
        }
      }
    });
  }
}

function add_child_to_pbi(product_bundle,batch,warehouse,pbi){
  var check = check_if_exists_in_pbi(batch,warehouse,pbi);
  if(!check){
    var bundle = cur_frm.add_child("product_bundles");
    bundle.product_bundle = product_bundle;
    bundle.bundle_batch = batch;
    bundle.warehouse = warehouse;
    // bundle.rate=rate;
    cur_frm.refresh_field("product_bundles"); 
  }
  
  
}


function check_if_exists_in_pbi(batch,warehouse,pbi){
  var key = 0;
    for(const row in pbi){      
      if(pbi[row].bundle_batch == batch){
        if(pbi[row].warehouse == warehouse){
          cur_frm.get_field("product_bundles").grid.grid_rows[row].doc.bundle_qty = pbi[row].bundle_qty+1;
          cur_frm.get_field("product_bundles").grid.grid_rows[row].refresh_field("bundle_qty");
          return true;

        }      
      }
      key++;
    }
   
  return false;
}