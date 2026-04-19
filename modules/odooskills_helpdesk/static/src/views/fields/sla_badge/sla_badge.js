/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";

export class SlaBadgeField extends Component {
    static template = "odooskills_helpdesk.SlaBadge";
    static props = {
        ...standardFieldProps,
        icon: { type: Boolean, optional: true },
        compact: { type: Boolean, optional: true },
    };
    static defaultProps = {
        icon: true,
        compact: false,
    };

    get value() {
        return this.props.record.data[this.props.name] || "ok";
    }

    get label() {
        const labels = {
            ok: _t("Dans les temps"),
            warning: _t("Proche échéance"),
            breach: _t("SLA dépassé"),
        };
        return labels[this.value] || this.value;
    }

    get iconClass() {
        const icons = {
            ok: "fa-check-circle",
            warning: "fa-clock-o",
            breach: "fa-exclamation-triangle",
        };
        return icons[this.value] || "fa-circle-o";
    }

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
    ],
    extractProps: ({ options }) => ({
        icon: options.icon !== false,
        compact: options.compact === true,
    }),
};

registry.category("fields").add("sla_badge", slaBadgeField);
