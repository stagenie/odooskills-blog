import { Component, computed, onWillStart, proxy, usePlugin, useProps } from "@odoo/owl";
import { ORM } from "@web/core/orm_plugin";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

/** Regroupe des devis lus par searchRead ; user_id vaut [id, nom] ou false. */
export function groupBySalesperson(orders) {
    const groups = new Map();
    for (const order of orders) {
        const name = order.user_id ? order.user_id[1] : "Sans commercial";
        const group = groups.get(name) || { name, count: 0, total: 0 };
        group.count += 1;
        group.total += order.amount_untaxed;
        groups.set(name, group);
    }
    return [...groups.values()].sort((a, b) => b.total - a.total);
}

export class DevisParCommercial extends Component {
    static template = "oski_owl_debogage.DevisParCommercial";

    props = useProps({ ...standardActionServiceProps });
    orm = usePlugin(ORM);

    setup() {
        this.state = proxy({ orders: [] });
        this.groups = computed(() => groupBySalesperson(this.state.orders));
        onWillStart(() => this.load());
    }

    async load() {
        this.state.orders = await this.orm.searchRead(
            "sale.order",
            [["state", "in", ["draft", "sent"]]],
            ["name", "user_id", "amount_untaxed"],
            { order: "name" }
        );
    }
}

registry.category("actions").add("oski_owl_debogage.devis_par_commercial", DevisParCommercial);
