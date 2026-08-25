import { registry } from "@web/core/registry";
import {
    ProgressBarField,
    progressBarField,
} from "@web/views/fields/progress_bar/progress_bar_field";
import { onWillUnmount } from "@odoo/owl";

const REFRESH_DELAY = 5000;

/**
 * Jauge d'import. Se rafraîchit toute seule tant que l'import tourne, et
 * s'arrête dès qu'il est fini : un onglet laissé ouvert ne doit pas
 * interroger le serveur indéfiniment.
 */
export class OskiBacklogGauge extends ProgressBarField {
    setup() {
        super.setup();
        this.timer = null;
        this.startTimerIfRunning();
        onWillUnmount(() => this.clearTimer());
    }

    get isRunning() {
        return this.props.record.data.backlog_state === "running";
    }

    startTimerIfRunning() {
        if (!this.isRunning || this.timer) {
            return;
        }
        this.timer = setInterval(async () => {
            await this.props.record.load();
            if (!this.isRunning) {
                this.clearTimer();
            }
        }, REFRESH_DELAY);
    }

    clearTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
}

export const oskiBacklogGauge = {
    ...progressBarField,
    component: OskiBacklogGauge,
    fieldDependencies: [{ name: "backlog_state", type: "selection" }],
};

registry.category("fields").add("oski_backlog_gauge", oskiBacklogGauge);
