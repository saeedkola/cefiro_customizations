// frappe.ui.form.on('Product Bundle Inserter', {
//     product_bundle: pbi_changed,
//     bundle_qty    : pbi_changed
// });
frappe.ui.form.on('Purchase Receipt',{
    get_items: function(frm,cdt,cdn){
      frappe.call({
        method: "cefiro_customizations.events.get_item_details_from_bundle_inserter",
        args: {
          bundle_list : frm.doc.product_bundle_inserter
        },
        callback: function(r){
          // frm.set_value("items",[])
          // var response = r.message
          // for (const row in response){
          //     // var itemsTable = frm.add_child("items");
          //     // frappe.model.set_value(itemsTable.doctype, itemsTable.name, "item_code", row);
          //     // frappe.model.set_value(itemsTable.doctype, itemsTable.name, "qty", response[row]);
          //     items.push({
          //       "item_code":row,
          //       "qty": response[row]
          //     })            
          // } 
          // var items = [];
          // frm.set_value("items",[]);
          // for (const row in r.message){
          //   items.push(r.message[row]);
          //   console.log(r.message[row]);
          // }
          frm.set_value("items",r.message);
          frm.refresh_field("items");
          // console.log(frm.doc.items);
        }
      });
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
    }
    // ,
    // validate: function(frm,cdt,cdn){
    //   $.each(frm.doc.product_bundle_inserter||[],function(key,row){
    //     if(!row.warehouse && frm.doc.set_warehouse){
    //       console.log("True");
    //       console.log(frm.doc.set_warehouse);
    //       row.warehouse = frm.doc.set_warehouse;
    //     }else{
    //       console.log("false");
    //     }
    //   });
    //   // frm.refresh_field("items");
    // }
});