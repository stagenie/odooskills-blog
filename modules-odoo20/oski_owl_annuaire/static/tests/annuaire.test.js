import { expect, test } from "@odoo/hoot";
import { queryAllTexts } from "@odoo/hoot-dom";
import { animationFrame } from "@odoo/hoot-mock";
import {
    Component,
    onMounted,
    onPatched,
    onWillDestroy,
    onWillPatch,
    onWillStart,
    onWillUnmount,
    proxy,
    useEffect,
    xml,
} from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { contains, mountWithCleanup, onRpc } from "@web/../tests/web_test_helpers";
import { Annuaire, FAVORITES_KEY } from "@oski_owl_annuaire/annuaire/annuaire";
import { ContactCard } from "@oski_owl_annuaire/annuaire/contact_card";

const PARTNERS = [
    { id: 16, name: "Azure Interior", email: "azure@example.com", city: "Fremont" },
    { id: 11, name: "Gemini Furniture", email: false, city: "Fairfield" },
    { id: 9, name: "Wood Corner", email: "wood@example.com", city: false },
];
const ACTION = { action: { type: "ir.actions.client", tag: "oski_owl_annuaire.annuaire" } };

function mockPartners() {
    onRpc("res.partner", "search_read", ({ kwargs }) => {
        expect.step(JSON.stringify(kwargs.domain));
        return PARTNERS;
    });
}

test("charge les sociétés au démarrage, filtre à la frappe", async () => {
    mockPartners();
    await mountWithCleanup(Annuaire, { props: ACTION });
    expect.verifySteps(['[["is_company","=",true]]']);
    expect(queryAllTexts(".o_annuaire_name")).toEqual(["Azure Interior", "Gemini Furniture", "Wood Corner"]);
    expect(".o_annuaire_search").toBeFocused();

    await contains(".o_annuaire_search").edit("wood");
    expect(queryAllTexts(".o_annuaire_name")).toEqual(["Wood Corner"]);

    await contains(".o_annuaire_search").edit("zzz");
    expect(".o_annuaire_card").toHaveCount(0);
    expect(".o_annuaire_empty").toHaveText("Aucune société ne correspond à « zzz ».");
});

test("l'étoile garde le favori dans le navigateur", async () => {
    browser.localStorage.setItem(FAVORITES_KEY, "[11]");
    mockPartners();
    await mountWithCleanup(Annuaire, { props: ACTION });
    expect.verifySteps(['[["is_company","=",true]]']);
    expect(".o_annuaire_card.border-warning .o_annuaire_name").toHaveText("Gemini Furniture");

    await contains(".o_annuaire_card:eq(0) .o_annuaire_star").click();
    expect(".o_annuaire_card.border-warning").toHaveCount(2);
    expect(browser.localStorage.getItem(FAVORITES_KEY)).toBe("[11,16]");

    await contains(".o_annuaire_only_fav").click();
    expect(queryAllTexts(".o_annuaire_name")).toEqual(["Azure Interior", "Gemini Furniture"]);
    expect(".o_annuaire_count").toHaveText("2 société(s) affichée(s), 2 favori(s)");
});

test("props validées : un rappel manquant est refusé", async () => {
    await expect(
        mountWithCleanup(ContactCard, { props: { partner: { id: 1, name: "Azure Interior" } } })
    ).rejects.toThrow(/Invalid component props \(ContactCard\)/);
});

test("ordre des hooks d'un composant", async () => {
    class Sonde extends Component {
        static template = xml`<span class="o_sonde" t-out="this.state.n"/>`;
        setup() {
            this.state = proxy({ n: 0 });
            expect.step("setup");
            useEffect(() => {
                expect.step(`effet n=${this.state.n}`);
                return () => expect.step("nettoyage de l'effet");
            });
            onWillStart(() => expect.step("onWillStart"));
            onMounted(() => expect.step("onMounted"));
            onWillPatch(() => expect.step("onWillPatch"));
            onPatched(() => expect.step("onPatched"));
            onWillUnmount(() => expect.step("onWillUnmount"));
            onWillDestroy(() => expect.step("onWillDestroy"));
        }
    }
    class Parent extends Component {
        static template = xml`<div><Sonde t-if="this.state.show"/></div>`;
        static components = { Sonde };
        setup() {
            this.state = proxy({ show: true });
        }
    }
    const parent = await mountWithCleanup(Parent);
    expect.verifySteps(["setup", "effet n=0", "onWillStart", "onMounted"]);

    const sonde = Object.values(parent.__owl__.children)[0].component;
    sonde.state.n = 1;
    await animationFrame();
    expect(".o_sonde").toHaveText("1");
    expect.verifySteps(["nettoyage de l'effet", "effet n=1", "onWillPatch", "onPatched"]);

    parent.state.show = false;
    await animationFrame();
    expect(".o_sonde").toHaveCount(0);
    expect.verifySteps(["onWillUnmount", "onWillDestroy", "nettoyage de l'effet"]);
});
