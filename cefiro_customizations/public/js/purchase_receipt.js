frappe.ui.form.on('Product Bundle Inserter', {
    product_bundle: pbi_changed,
    bundle_qty    : pbi_changed
})

function pbi_changed(frm,cdt,cdn){
    console.log(frm.doc.product_bundle_inserter)
    frappe.call({
        method: "cefiro_customizations.events.get_items_from_bundle_inserter",
        args: {bundle_list : frm.doc.product_bundle_inserter},
        callback: function(r){
            var items = []
            frm.set_value("items",[])
            var response = r.message
            for (const row in response){
                var itemsTable = frm.add_child("items");
                frappe.model.set_value(itemsTable.doctype, itemsTable.name, "item_code", row);
                frappe.model.set_value(itemsTable.doctype, itemsTable.name, "qty", response[row]);               
            }
            
            frm.refresh_fields("items")
        }
    })
}