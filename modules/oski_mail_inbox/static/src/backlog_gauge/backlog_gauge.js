import { registry } from "@web/core/registry";
import {
    ProgressBarField,
    progressBarField,
} from "@web/views/fields/progress_bar/progress_bar_field";
import { onWillUnmount } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";

const REFRESH_DELAY = 5000;

/**
 * Jauge d'import. Se rafraîchit toute seule tant qu'un import est en
 * attente ou en cours, et s'arrête dès qu'il n'y en a plus : un onglet
 * laissé ouvert ne doit pas interroger le serveur indéfiniment.
 *
 * Elle s'abstient de recharger l'enregistrement si le formulaire porte une
 * saisie non enregistrée (signature, dossiers...) : record.load() efface
 * silencieusement les changements en cours (record.js: _setData vide
 * _changes et remet dirty à false), ce qui ferait perdre à l'utilisateur
 * ce qu'il tape pendant que l'import tourne en tâche de fond.
 */
export class OskiBacklogGauge extends ProgressBarField {
    setup() {
        super.setup();
        this.timer = null;
        this.isDestroyed = false;
        this.scheduleRefresh();
        onWillUnmount(() => {
            this.isDestroyed = true;
            this.clearTimer();
        });
    }

    get isImporting() {
        return ["pending", "running"].includes(this.props.record.data.backlog_state);
    }

    scheduleRefresh() {
        this.clearTimer();
        if (!this.isImporting) {
            return;
        }
        // Un setTimeout qui se reprogramme lui-même une fois le
        // rafraîchissement terminé, plutôt qu'un setInterval : sur un
        // aller-retour lent, un setInterval empilerait des ticks au lieu
        // d'attendre que le précédent soit fini.
        this.timer = browser.setTimeout(() => this.refresh(), REFRESH_DELAY);
    }

    async refresh() {
        try {
            if (!this.isDestroyed && !(await this.props.record.isDirty())) {
                await this.props.record.load();
            }
        } catch {
            // Une jauge est un confort, pas une fonction critique : un
            // rafraîchissement en échec (réseau, session expirée...) ne
            // doit jamais faire lever d'erreur non gérée au client.
        } finally {
            if (!this.isDestroyed) {
                this.scheduleRefresh();
            }
        }
    }

    clearTimer() {
        if (this.timer) {
            browser.clearTimeout(this.timer);
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
