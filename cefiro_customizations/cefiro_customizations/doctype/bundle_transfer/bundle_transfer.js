// Copyright (c) 2021, Element Labs and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bundle Transfer', {
  setup: function(frm){
    frm.set_query("from_warehouse",function(){
      return {
        filters:{
          "is_group": 0
        }
      }
    });
    frm.set_query("to_warehouse",function(){
      return {
        filters:{
          "is_group": 0
        }
      }
    });
    frm.set_query("from_warehouse","product_bundles",function(){
      return {
        filters:{
          "is_group": 0
        }
      }
    });
    frm.set_query("to_warehouse","product_bundles",function(){
      return {
        filters:{
          "is_group": 0
        }
      }
    });
  },
  refresh: function(frm){
    frm.fields_dict['product_bundles'].grid.get_field('bundle_batch').get_query = function(doc, cdt, cdn) {
      var child = locals[cdt][cdn];    
      return{  
        filters:[
          ['product_bundle', '=', child.product_bundle]    
        ],

      }
    }
  },
  scan_bundle_batch_barcode: on_batch_trigger
});


function on_batch_trigger(frm,cdt,cdn){
  if(frm.doc.scan_bundle_batch_barcode){
    frappe.call({
      method: "cefiro_customizations.filters.get_details_from_bundle_batch",
      args:{
        batch: frm.doc.scan_bundle_batch_barcode
      },
      callback: function(r){
        console.log(r.message);
        var res = r.message;
        if(res.length){
          if (res.length > 1){
            // res_array = []
            // for (batch in res){
            //   res_array.push(res.bundle_batch);
            // }
            // new frappe.ui.form.MultiSelectDialog({
            //   doctype: "Warehouse",
            //   target: frm,
            //   setters:{
            //   },              
            //   get_query() {
            //       return {
            //           filters:{
            //               name: ["in",res_array]
            //           }                      
            //       };
            //   },
            //   action(selections) {
            //       console.log(selections);
            //       for (const row in selections){
            //           var itemsTable = frm.add_child("items");                      
            //       }          
            //   }
            // }); 
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
  console.log(check);
  if(!check){
    var bundle = cur_frm.add_child("product_bundles");
    bundle.product_bundle = product_bundle;
    bundle.bundle_batch = batch;
    bundle.from_warehouse = warehouse;
    bundle.to_warehouse = cur_frm.doc.to_warehouse;
    bundle.quantity = 1;
    cur_frm.refresh_field("product_bundles");
  } 
  
}


function check_if_exists_in_pbi(batch,warehouse,pbi){
  var key = 0;
  console.log(pbi);
    for(const row in pbi){
      console.log(pbi[row]);
      if(pbi[row].bundle_batch == batch){
        if(pbi[row].from_warehouse == warehouse){
          cur_frm.get_field("product_bundles").grid.grid_rows[row].doc.quantity = pbi[row].quantity+1;
          cur_frm.get_field("product_bundles").grid.grid_rows[row].refresh_field("quantity");
          return true;

        }      
      }
      key++;
    }
   
  return false;
}

frappe.ui.form.on('Bundle Transfer Item', {
  product_bundle: function(frm,cdt,cdn) {
    var row = locals[cdt][cdn];
    if (frm.doc.from_warehouse){
      row.from_warehouse = frm.doc.from_warehouse;

    }
    if (frm.doc.to_warehouse){
      row.to_warehouse = frm.doc.to_warehouse;

    }
    frm.refresh_field("product_bundles");
    get_available_qty(frm,cdt,cdn);
  },
  from_warehouse: get_available_qty,
  bundle_batch: get_available_qty,
  quantity:function(frm,cdt,cdn){
    var row = locals[cdt][cdn];
    if (row.quantity > row.available_qty){
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
      args['warehouse'] = row.from_warehouse
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