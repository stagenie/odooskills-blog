import { Plugin, proxy, usePlugin } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { services } from "@web/core/services";
import { user } from "@web/core/user";
import { ActionPlugin } from "@web/webclient/actions/action_plugin";

export const MAX_RECENTS = 8;

export function storageKey() {
    return `oski_owl_recents.${user.userId}`;
}

/** Service : les derniers enregistrements ouverts en formulaire, par utilisateur. */
export class RecentsPlugin extends Plugin {
    // dépendance : un autre service, déclaré comme un champ
    action = usePlugin(ActionPlugin);
    // état partagé par tous les composants qui utilisent le service
    items = proxy([]);

    setup() {
        try {
            this.items.push(...(JSON.parse(browser.localStorage.getItem(storageKey())) || []));
        } catch {
            // valeur illisible : on repart d'une liste vide
        }
    }

    visit({ resModel, resId, displayName }) {
        const index = this.items.findIndex((i) => i.resModel === resModel && i.resId === resId);
        if (index >= 0) {
            this.items.splice(index, 1);
        }
        this.items.unshift({ resModel, resId, displayName });
        this.items.splice(MAX_RECENTS);
        this.save();
    }

    open(item) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: item.resModel,
            res_id: item.resId,
            views: [[false, "form"]],
        });
    }

    clear() {
        this.items.splice(0);
        this.save();
    }

    save() {
        browser.localStorage.setItem(storageKey(), JSON.stringify(this.items));
    }
}

// 1. le service lui-même : démarré par le client web avec les autres
services.add(RecentsPlugin);

// 2. un pont facultatif, pour le code qui appelle encore useService("oski_recents")
registry.category("services").add("oski_recents", {
    start() {
        return usePlugin(RecentsPlugin);
    },
});
