import { usePlugin } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { RecentsPlugin } from "./recents_plugin";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.recents = usePlugin(RecentsPlugin);
    },

    async onRootLoaded() {
        await super.onRootLoaded(...arguments);
        const root = this.model.root;
        if (root.resId && !this.env.inDialog) {
            this.recents.visit({
                resModel: root.resModel,
                resId: root.resId,
                displayName: this.displayName(),
            });
        }
    },
});
