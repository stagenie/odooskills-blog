import { Component, usePlugin } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { RecentsPlugin } from "./recents_plugin";

export class RecentsSystray extends Component {
    static template = "oski_owl_recents.RecentsSystray";
    static components = { Dropdown, DropdownItem };

    recents = usePlugin(RecentsPlugin);
}

registry.category("systray").add("oski_owl_recents.systray", { Component: RecentsSystray }, { sequence: 5 });
