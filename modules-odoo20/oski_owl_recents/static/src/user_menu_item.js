import { usePlugin } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { RecentsPlugin } from "./recents_plugin";

export function clearRecentsItem() {
    // en Odoo 20, la fonction est appelée dans la portée du menu : les hooks y sont permis
    const recents = usePlugin(RecentsPlugin);
    return {
        type: "item",
        id: "oski_recents_clear",
        description: "Vider les derniers consultés",
        hide: !recents.items.length,
        callback: () => recents.clear(),
        sequence: 45,
    };
}

registry.category("user_menuitems").add("oski_recents_clear", clearRecentsItem);
