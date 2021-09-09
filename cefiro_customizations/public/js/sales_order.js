frappe.ui.form.on('Sales Order',{
	get_items: function(frm,cdt,cdn){
    check_for_duplicate_bundles(frm,cdt,cdn);
    if(frm.doc.product_bundle_inserter && frm.doc.set_warehouse){        
      frappe.call({
        method: "cefiro_customizations.events.get_item_details_from_bundle_inserter",
        args: {
          bundle_list : frm.doc.product_bundle_inserter,
          set_warehouse: frm.doc.set_warehouse,
          delivery_date: frm.doc.delivery_date
        },
        callback: function(r){        
          frm.set_value("items",r.message);
          frm.refresh_field("items");
          console.log(frm.doc.items);
        }
      });              
    }else{
      console.log("False");
    }
  },
	validate:function(frm,cdt,cdn){
		// set_default_warehouse(frm,cdt,cdn);
	  validate(frm,cdt,cdn);
		validate_pbi(frm,cdt,cdn);
	},
	refresh: function(frm,cdt,cdn){
	  if(frm.doc.docstatus == 1){
	    frm.add_custom_button(__("Bundle Pick List"),function(){
	      frappe.set_route('query-report','Bundle Pick List',{
	        sales_order: frm.doc.name
	      });
	    });
	  }
	}
});


function validate(frm,cdt,cdn){
  check_for_duplicate_bundles(frm,cdt,cdn);
  // set_default_warehouse(frm,cdt,cdn);
  
}

function check_for_duplicate_bundles(frm,cdt,cdn){
  $.each(frm.doc.product_bundle_inserter,function(key,item){
    $.each(frm.doc.product_bundle_inserter,function(key,row){
      if ((item.product_bundle == row.product_bundle)&&(item.idx != row.idx)){
        let dup1 = item.idx;
        let dup2 = row.idx;
        let message = `Duplicates row ${dup1} and ${dup2}`;
        frappe.throw(__(message));
        return false;
      }
    });
  });
}


function validate_pbi(frm,cdt,cdn){
  $.each(frm.doc.product_bundle_inserter,function(key,row){
    if(!row.product_bundle || (row.bundle_qty < 1)){
      let row_no = row.idx;
      let message = `Mandatory fields not set in row ${row_no}`;
      frappe.throw(__(message));
      return false;
    }else{
      return true;
    }
  });
}

frappe.ui.form.on('Product Bundle Inserter SO', {
  product_bundle: function(frm,cdt,cdn) {
    var row = locals[cdt][cdn];
    frm.refresh_field("product_bundle_inserter");
    get_available_qty(frm,cdt,cdn);
  },  
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
    };
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
    });
  }
}
