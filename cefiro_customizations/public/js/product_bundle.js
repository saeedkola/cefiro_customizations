frappe.ui.form.on('Product Bundle', {
    onload: function(frm){
        frm.set_query("item_template",function(){
            return{
                "filters":{
                    "has_variants": 1
                }
            }
        })
    },
    insert_items: button_clicked
});


function button_clicked(frm,cdt,cdn){

    if (frm.doc.item_template){
        var args = {
            item_template: frm.doc.item_template
        }
        if(frm.doc.colour){
            args['colour']= frm.doc.colour;
        }
        if(frm.doc.size){
            args['size']= frm.doc.size;
        }
        frappe.call({
            method: "cefiro_customizations.filters.get_variant_items",
            args:args,
            callback:function(r){
                console.log(r)
                var res_array = r.message;
                new frappe.ui.form.MultiSelectDialog({
                    doctype: "Item",
                    target: frm,
                    setters:{
                    },              
                    get_query() {
                        return {
                            filters:{
                                item_code: ["in",res_array]
                            }
                            
                        };
                    },
                    action(selections) {
                        console.log(selections);
                        for (const row in selections){
                            var itemsTable = frm.add_child("items");
                            frappe.model.set_value(itemsTable.doctype, itemsTable.name, "item_code", selections[row]);               
                        }
                        frm.refresh_fields("items");
                    }
                });                
                
            }
        });
    }
    
}