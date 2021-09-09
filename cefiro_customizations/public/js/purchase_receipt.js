frappe.ui.form.on('Product Bundle Inserter', {
    product_bundle: function(frm,cdt,cdn){
      var item = locals[cdt][cdn];
      console.log(item.product_bundle);
      $.each(frm.doc.product_bundle_inserter,function(key,row){
        if ((item.product_bundle == row.product_bundle)&&(item.idx != row.idx)){
          let dup1 = item.idx;
          let dup2 = row.idx;
          let message = `Duplicates row ${dup1} and ${dup2}`;
          frappe.throw(__(message));
        }
      });
    }
});
frappe.ui.form.on('Purchase Receipt',{
    get_items: function(frm,cdt,cdn){
      if(frm.doc.set_warehouse && frm.doc.product_bundle_inserter){
        set_default_warehouse(frm,cdt,cdn);
        frappe.call({
          method: "cefiro_customizations.events.get_item_details_from_bundle_inserter",
          args: {
            bundle_list : frm.doc.product_bundle_inserter
          },
          callback: function(r){
            frm.set_value("items",r.message);
            frm.refresh_field("items");
            // console.log(frm.doc.items);
          }
        });
      }
    },
    refresh: function(frm,cdt,cdn){
      if(frm.doc.docstatus == 1){
        frm.add_custom_button(__("Generate Barcodes"),function(){
          frappe.set_route('query-report','Barcode Generation',{
            ref_doctype: "Purchase Receipt",
            ref_docname: frm.doc.name
          });
        });
      }
    },
    validate: validate
});

function validate(frm,cdt,cdn){
  check_for_duplicate_bundles(frm,cdt,cdn);
  set_default_warehouse(frm,cdt,cdn);
  
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


function set_default_warehouse(frm,cdt,cdn){
  $.each(frm.doc.product_bundle_inserter||[],function(key,row){
    if(!row.warehouse && frm.doc.set_warehouse){        
      row.warehouse = frm.doc.set_warehouse;
    }
  });
  frm.refresh_field("product_bundle_inserter");
}