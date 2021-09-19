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
    insert_items: button_clicked,
    create_item: create_item,
    validate: calculate_total

});

//Add filter to child item code, maintain_stock:!

function create_item(frm,cdt,cdn){
    var items =[]
    frm.doc.items.forEach(function(item,index){
        if(item.item_code){
            items.push({
                item_code: item.item_code,
                qty: item.qty
            });
        }
        
    });
    frappe.call({
        method: "cefiro_customizations.filters.create_bundle_name",
        args: {"items": items},
        callback: function(r){
            console.log(r.message);
            frm.set_value('new_item_code',r.message[2]);
            frm.refresh_fields('new_item_code');           
        }
    });
    // console.log(items)
}

function calculate_total(frm,cdt,cdn){
    var count = 0;
    for (var item in frm.doc.items){
       count = count+frm.doc.items[item].qty;
    }
    frm.set_value("total_quantity",count);
    frm.refresh_fields('total_quantity');

}

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
                            frappe.model.set_value(itemsTable.doctype, itemsTable.name, "qty", 1);
                        }
                        frm.refresh_fields("items");
                        calculate_total(frm,cdt,cdn);
                    }
                });                
                
            }
        });
    }
    
}