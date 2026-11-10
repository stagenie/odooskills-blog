import {
    Component,
    computed,
    onMounted,
    onWillStart,
    proxy,
    signal,
    useEffect,
    useListener,
    usePlugin,
    useProps,
} from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { ORM } from "@web/core/orm_plugin";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { ContactCard } from "./contact_card";

export const FAVORITES_KEY = "oski_owl_annuaire.favoris";

function readFavorites() {
    try {
        return JSON.parse(browser.localStorage.getItem(FAVORITES_KEY)) || [];
    } catch {
        return [];
    }
}

export class Annuaire extends Component {
    static template = "oski_owl_annuaire.Annuaire";
    static components = { ContactCard };

    // 1. Props : celles que le gestionnaire d'actions passe à toute action client
    props = useProps({ ...standardActionServiceProps });
    orm = usePlugin(ORM);
    searchInput = signal.ref();

    setup() {
        // 2. État réactif : toute écriture redessine ce qui la lit
        this.state = proxy({
            partners: [],
            query: "",
            onlyFavorites: false,
            favoriteIds: readFavorites(),
        });
        // 3. Valeur dérivée, recalculée seulement quand ce qu'elle lit change
        this.visiblePartners = computed(() => {
            const query = this.state.query.trim().toLowerCase();
            return this.state.partners.filter(
                (p) =>
                    (!query || p.name.toLowerCase().includes(query)) &&
                    (!this.state.onlyFavorites || this.state.favoriteIds.includes(p.id))
            );
        });

        // 4. Hooks de cycle de vie
        onWillStart(async () => {
            this.state.partners = await this.orm.searchRead(
                "res.partner",
                [["is_company", "=", true]],
                ["name", "email", "city"],
                { order: "name" }
            );
        });
        onMounted(() => this.searchInput()?.focus());
        useEffect(() => {
            browser.localStorage.setItem(FAVORITES_KEY, JSON.stringify(this.state.favoriteIds));
        });
        useListener(browser, "keydown", (ev) => {
            // pas de raccourci pendant une saisie, dans la recherche ou ailleurs
            if (ev.key === "/" && !["INPUT", "TEXTAREA"].includes(ev.target.tagName)) {
                ev.preventDefault();
                this.searchInput()?.focus();
            }
        });
    }

    toggleFavorite(partnerId) {
        const ids = this.state.favoriteIds;
        const index = ids.indexOf(partnerId);
        if (index >= 0) {
            ids.splice(index, 1);
        } else {
            ids.push(partnerId);
        }
    }

    toggleOnlyFavorites() {
        this.state.onlyFavorites = !this.state.onlyFavorites;
    }
}

registry.category("actions").add("oski_owl_annuaire.annuaire", Annuaire);
