import { registry } from "@web/core/registry";
import {
    ProgressBarField,
    progressBarField,
} from "@web/views/fields/progress_bar/progress_bar_field";
import { onWillUnmount, useEffect } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";

const REFRESH_DELAY = 5000;
const REFRESH_DELAY_MAX = 30000;

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
 *
 * Elle réarme aussi son horloge à chaque bascule du booléen isImporting
 * (none/done <-> pending/running, via useEffect — pending -> running ne
 * la redéclenche pas, les deux valant "true") : quand action_start_backlog()
 * recharge le formulaire déjà ouvert, OWL patche ce composant au lieu de
 * le remonter (Renderer et Field ne sont pas keyés), donc rien d'autre ne
 * relancerait le minuteur pour le geste « cliquer puis regarder ».
 *
 * Enfin, l'intervalle s'élargit (5 s -> 30 s max) quand ni l'état ni le
 * compteur n'ont bougé d'un tick à l'autre : une boîte bloquée en
 * 'pending' (identifiants invalides, avalés en silence par le cron) ne
 * doit pas être interrogée indéfiniment au même rythme qu'un import qui
 * avance. Le moindre mouvement ramène l'intervalle à 5 s.
 */
export class OskiBacklogGauge extends ProgressBarField {
    setup() {
        super.setup();
        this.timer = null;
        this.isDestroyed = false;
        this.pollDelay = REFRESH_DELAY;
        useEffect(
            () => {
                this.pollDelay = REFRESH_DELAY;
                this.scheduleRefresh();
            },
            () => [this.isImporting],
        );
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
        this.timer = browser.setTimeout(() => this.refresh(), this.pollDelay);
    }

    _snapshot() {
        const data = this.props.record.data;
        return data.backlog_state + ":" + data.backlog_done_count;
    }

    async refresh() {
        try {
            if (this.isDestroyed) {
                return;
            }
            if (await this.props.record.isDirty()) {
                return;
            }
            const before = this._snapshot();
            await this.props.record.load();
            this.pollDelay = (before === this._snapshot())
                ? Math.min(this.pollDelay * 2, REFRESH_DELAY_MAX)
                : REFRESH_DELAY;
        } catch {
            // Une jauge est un confort, pas une fonction critique : un
            // rafraîchissement en échec (réseau, session expirée...) ne
            // doit jamais faire lever d'erreur non gérée au client. Mais
            // un serveur qui échoue à chaque appel doit lui aussi reculer,
            // sinon il serait interrogé toutes les 5 s indéfiniment — la
            // seule promesse du docstring qu'un échec pourrait rompre.
            this.pollDelay = Math.min(this.pollDelay * 2, REFRESH_DELAY_MAX);
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
    fieldDependencies: [
        { name: "backlog_state", type: "selection" },
        { name: "backlog_done_count", type: "integer" },
    ],
};

registry.category("fields").add("oski_backlog_gauge", oskiBacklogGauge);
