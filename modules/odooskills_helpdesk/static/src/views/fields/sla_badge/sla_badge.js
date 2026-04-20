/** @odoo-module **/
import { Component, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * SlaBadgeField — widget field OWL pour le champ `sla_status`.
 *
 * T26 : affiche une pastille colorée (ok / warning / breach) avec icône et label.
 * T27 : s'abonne au canal bus.bus `odooskills.sla` pour rafraîchir la pastille
 *        en temps réel quand le serveur pousse un événement `sla_status_changed`.
 *
 * Cycle de vie bus :
 *   onMounted  → addChannel("odooskills.sla") + subscribe(type, cb)
 *   onWillUnmount → unsubscribe(type, cb)   [évite les fuites mémoire]
 *
 * Quand payload.id == resId du record courant, on appelle record.load()
 * pour déclencher un rechargement ORM sans F5.
 */
export class SlaBadgeField extends Component {
    static template = "odooskills_helpdesk.SlaBadge";
    static props = {
        ...standardFieldProps,
        icon: { type: Boolean, optional: true },
        compact: { type: Boolean, optional: true },
        /** live=true (défaut) active le rafraîchissement temps réel via bus.bus. */
        live: { type: Boolean, optional: true },
    };
    static defaultProps = {
        icon: true,
        compact: false,
        live: true,
    };

    setup() {
        // T27 — abonnement bus uniquement si l'option `live` est activée (défaut : true)
        if (this.props.live) {
            this.busService = useService("bus_service");

            // Lier `this` explicitement — nécessaire pour unsubscribe par référence
            this._onSlaChanged = this._onSlaChanged.bind(this);

            onMounted(() => {
                // Demande au SharedWorker d'écouter ce canal.
                // Sans _build_bus_channel_list côté serveur, cette ligne est ignorée.
                this.busService.addChannel("odooskills.sla");
                this.busService.subscribe("sla_status_changed", this._onSlaChanged);
            });

            onWillUnmount(() => {
                // Désabonnement obligatoire pour éviter les callbacks orphelins
                // quand le widget est détruit (navigation entre records).
                this.busService.unsubscribe("sla_status_changed", this._onSlaChanged);
            });
        }
    }

    /**
     * Callback T27 — appelé par bus_service à chaque notification `sla_status_changed`.
     *
     * On filtre sur `payload.id` pour n'agir que sur le record affiché dans
     * cet onglet. Plusieurs onglets peuvent être ouverts — seul celui qui
     * affiche ce ticket se rechargera.
     *
     * @param {Object} payload  { id, reference, new_status, name }
     */
    _onSlaChanged(payload) {
        if (payload && payload.id === this.props.record.resId) {
            // record.load() déclenche un rechargement ORM du record courant.
            // Les props OWL sont réactifs → le template se re-rend automatiquement.
            this.props.record.load();
        }
    }

    /** Valeur courante du champ selection (défaut : 'ok' si vide). */
    get value() {
        return this.props.record.data[this.props.name] || "ok";
    }

    /** Label lisible correspondant à la valeur selection. */
    get label() {
        const labels = {
            ok: _t("Dans les temps"),
            warning: _t("Proche échéance"),
            breach: _t("SLA dépassé"),
        };
        return labels[this.value] || this.value;
    }

    /** Classe Font Awesome pour l'icône de statut. */
    get iconClass() {
        const icons = {
            ok: "fa-check-circle",
            warning: "fa-clock-o",
            breach: "fa-exclamation-triangle",
        };
        return icons[this.value] || "fa-circle-o";
    }

    /** Classes CSS de la pastille combinant état, compact et éventuel refresh. */
    get pillClass() {
        const base = this.props.compact ? "o_sla_pill o_sla_pill--compact" : "o_sla_pill";
        return `${base} o_sla_pill--${this.value}`;
    }
}

export const slaBadgeField = {
    component: SlaBadgeField,
    displayName: _t("SLA Badge"),
    supportedTypes: ["selection"],
    supportedOptions: [
        {
            label: _t("Show icon"),
            name: "icon",
            type: "boolean",
            default: true,
        },
        {
            label: _t("Compact display"),
            name: "compact",
            type: "boolean",
            default: false,
        },
        {
            label: _t("Live refresh (T27)"),
            name: "live",
            type: "boolean",
            default: true,
        },
    ],
    extractProps: ({ options }) => ({
        icon: options.icon !== false,
        compact: options.compact === true,
        live: options.live !== false,
    }),
};

registry.category("fields").add("sla_badge", slaBadgeField);
