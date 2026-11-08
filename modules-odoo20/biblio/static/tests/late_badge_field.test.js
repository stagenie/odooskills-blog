import { expect, test } from "@odoo/hoot";
import { queryAllTexts } from "@odoo/hoot-dom";
import { mockDate } from "@odoo/hoot-mock";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import {
    defineModels,
    fields,
    models,
    mountView,
} from "@web/../tests/web_test_helpers";

class LibraryLoan extends models.Model {
    _name = "library.loan";
    date_due = fields.Date({ string: "À rendre le" });
    state = fields.Selection({
        selection: [
            ["ongoing", "En cours"],
            ["returned", "Rendu"],
        ],
    });
    _records = [
        { id: 1, date_due: "2026-11-21", state: "ongoing" },
        { id: 2, date_due: "2026-11-10", state: "ongoing" },
        { id: 3, date_due: "2026-11-05", state: "ongoing" },
        { id: 4, date_due: "2026-11-02", state: "returned" },
        { id: 5, date_due: false, state: "ongoing" },
    ];
}

defineMailModels(); // biblio dépend de mail : ses services veulent ses modèles
defineModels([LibraryLoan]);

test("le badge suit l'échéance et l'état, sans colonne state dans la vue", async () => {
    mockDate("2026-11-08 10:00:00");
    await mountView({
        type: "list",
        resModel: "library.loan",
        arch: `<list><field name="date_due" widget="late_badge"/></list>`,
    });
    expect(".o_late_badge").toHaveCount(4);
    expect(queryAllTexts(".o_late_badge")).toEqual([
        "Nov 21",
        "À rendre dans 2 j",
        "3 j de retard",
        "Rendu",
    ]);
    expect(".o_late_badge.text-bg-danger").toHaveCount(1);
});

test("l'option warn_days élargit la fenêtre d'alerte", async () => {
    mockDate("2026-11-08 10:00:00");
    await mountView({
        type: "list",
        resModel: "library.loan",
        arch: `<list><field name="date_due" widget="late_badge" options="{'warn_days': 15}"/></list>`,
    });
    expect(queryAllTexts(".o_late_badge")).toEqual([
        "À rendre dans 13 j",
        "À rendre dans 2 j",
        "3 j de retard",
        "Rendu",
    ]);
});
