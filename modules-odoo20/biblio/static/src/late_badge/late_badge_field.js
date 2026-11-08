import { Component, t, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { formatDate } from "@web/views/fields/formatters";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const { DateTime } = luxon;

export class LateBadgeField extends Component {
    static template = "biblio.LateBadgeField";

    // OWL 3 : `static props` est ignoré, les props se déclarent avec useProps()
    props = useProps({
        ...standardFieldProps,
        warnDays: t.number().optional(3),
    });

    get record() {
        return this.props.record;
    }

    /** Jours restants avant l'échéance (négatif = retard), null si pas d'échéance. */
    get days() {
        const due = this.record.data[this.props.name];
        if (!due) {
            return null;
        }
        const today = DateTime.local().startOf("day");
        return Math.round(due.startOf("day").diff(today, "days").days);
    }

    get status() {
        if (this.record.data.state === "returned") {
            return "returned";
        }
        if (this.days === null) {
            return "none";
        }
        if (this.days < 0) {
            return "late";
        }
        return this.days <= this.props.warnDays ? "soon" : "ok";
    }

    get label() {
        const days = this.days;
        switch (this.status) {
            case "returned":
                return _t("Rendu");
            case "late":
                return _t("%s j de retard", -days);
            case "soon":
                return days === 0 ? _t("À rendre aujourd'hui") : _t("À rendre dans %s j", days);
            case "ok":
                return formatDate(this.record.data[this.props.name]);
            default:
                return "";
        }
    }

    get badgeClass() {
        return {
            returned: "text-bg-secondary",
            late: "text-bg-danger",
            soon: "text-bg-warning",
            ok: "text-bg-success",
        }[this.status];
    }
}

export const lateBadgeField = {
    component: LateBadgeField,
    displayName: _t("Badge de retard"),
    supportedTypes: ["date"],
    // champs lus par le widget même si la vue ne les affiche pas
    fieldDependencies: [{ name: "state", type: "selection" }],
    extractProps: ({ options }) => ({
        warnDays: options.warn_days,
    }),
};

registry.category("fields").add("late_badge", lateBadgeField);
