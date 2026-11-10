import { expect, test } from "@odoo/hoot";
import { queryAllTexts } from "@odoo/hoot-dom";
import { contains, mountWithCleanup, onRpc } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import {
    DevisParCommercial,
    groupBySalesperson,
} from "@oski_owl_debogage/devis_par_commercial";

const ORDERS = [
    { id: 1, name: "S00001", user_id: [5, "Marc Demo"], amount_untaxed: 1740 },
    { id: 2, name: "S00002", user_id: [2, "Mitchell Admin"], amount_untaxed: 2947.5 },
    { id: 3, name: "S00003", user_id: false, amount_untaxed: 377.5 },
    { id: 5, name: "S00005", user_id: [5, "Marc Demo"], amount_untaxed: 405 },
];
// le module dépend de sale, donc de mail : ses modèles doivent être déclarés
defineMailModels();

const ACTION = { action: { type: "ir.actions.client", tag: "oski_owl_debogage.devis_par_commercial" } };

test("un devis sans commercial a sa propre ligne", () => {
    expect(groupBySalesperson(ORDERS)).toEqual([
        { name: "Mitchell Admin", count: 1, total: 2947.5 },
        { name: "Marc Demo", count: 2, total: 2145 },
        { name: "Sans commercial", count: 1, total: 377.5 },
    ]);
});

test("l'action lit les devis en cours et se met à jour", async () => {
    let orders = ORDERS.slice(0, 2);
    onRpc("sale.order", "search_read", ({ kwargs }) => {
        expect.step(JSON.stringify(kwargs.domain));
        return orders;
    });
    await mountWithCleanup(DevisParCommercial, { props: ACTION });
    expect.verifySteps(['[["state","in",["draft","sent"]]]']);
    expect(queryAllTexts(".o_devis_group td:first-child")).toEqual(["Mitchell Admin", "Marc Demo"]);

    orders = ORDERS;
    await contains(".o_devis_reload").click();
    expect.verifySteps(['[["state","in",["draft","sent"]]]']);
    expect(queryAllTexts(".o_devis_group td:first-child")).toEqual([
        "Mitchell Admin",
        "Marc Demo",
        "Sans commercial",
    ]);
});
