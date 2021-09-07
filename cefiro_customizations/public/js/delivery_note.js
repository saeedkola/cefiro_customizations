frappe.ui.form.on('Delivery Note',{
	get_items: function(frm,cdt,cdn){
      if(frm.doc.product_bundle_inserter){
        set_default_warehouse(frm,cdt,cdn);
        if(validate_pbi(frm,cdt,cdn)){
          frappe.call({
            method: "cefiro_customizations.events.get_item_details_from_bundle_inserter_delivery_note",
            args: {
              bundle_list : frm.doc.product_bundle_inserter
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
        console.log("FAlse");
      }
    },
    set_warehouse: function(frm,cdt,cdn){
    	set_default_warehouse(frm,cdt,cdn);
    },
    validate:function(frm,cdt,cdn){
    	set_default_warehouse(frm,cdt,cdn);
    	validate_pbi(frm,cdt,cdn);
    }
});

function validate_pbi(frm,cdt,cdn){
  var ret;
  $.each(frm.doc.product_bundle_inserter,function(key,row){
    if(!row.product_bundle || !row.bundle_batch || !row.warehouse){
      let row_no = row.idx;
      let message = `Mandatory fields not set in row {row_no}`;
      frappe.throw(__(message));
      ret = false;
    }else{
      ret = true;
    }
  });
  return ret;
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
	},
  warehouse: get_available_qty,
  bundle_batch: get_available_qty,
  bundle_qty:function(frm,cdt,cdn){
    var row = locals[cdt][cdn];
    if (row.bundle_qty > row.available_qty){
      let row_no = row.idx;
      let message = `Available Qty less than Bundle Qty in row {row_no}`;
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