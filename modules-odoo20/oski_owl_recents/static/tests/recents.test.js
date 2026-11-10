import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { queryAllTexts } from "@odoo/hoot-dom";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import {
    clearRegistry,
    contains,
    defineModels,
    fields,
    getService,
    makeTestApp,
    mockService,
    models,
    mountView,
    mountWithCleanup,
    serverState,
} from "@web/../tests/web_test_helpers";
import { MAX_RECENTS, RecentsPlugin } from "@oski_owl_recents/recents_plugin";
import { RecentsSystray } from "@oski_owl_recents/recents_systray";
import { clearRecentsItem } from "@oski_owl_recents/user_menu_item";

class Partner extends models.Model {
    name = fields.Char();
    _records = [
        { id: 1, name: "Azure Interior" },
        { id: 2, name: "Wood Corner" },
    ];
}
defineModels([Partner]);

describe.current.tags("desktop");

function mockDoAction() {
    mockService("action", {
        doAction(action) {
            expect.step(`${action.res_model},${action.res_id}`);
        },
    });
}

beforeEach(() => {
    serverState.userId = 7;
});

test("le service garde les derniers consultés, sans doublon, par utilisateur", async () => {
    await makeTestApp();
    const recents = getService(RecentsPlugin);
    expect(getService("oski_recents")).toBe(recents); // le pont rend la même instance

    for (let id = 1; id <= MAX_RECENTS + 2; id++) {
        recents.visit({ resModel: "partner", resId: id, displayName: `P${id}` });
    }
    recents.visit({ resModel: "partner", resId: 5, displayName: "P5" });
    expect(recents.items.length).toBe(MAX_RECENTS);
    expect(recents.items.slice(0, 3).map((i) => i.displayName)).toEqual(["P5", "P10", "P9"]);
    const stored = JSON.parse(browser.localStorage.getItem("oski_owl_recents.7"));
    expect(stored[0]).toEqual({ resModel: "partner", resId: 5, displayName: "P5" });
});

test("le formulaire patché alimente le service", async () => {
    await mountView({ type: "form", resModel: "partner", resId: 1, resIds: [1, 2] });
    const recents = getService(RecentsPlugin);
    expect(recents.items.map((i) => i.displayName)).toEqual(["Azure Interior"]);

    await contains(".o_pager_next").click();
    expect(recents.items.map((i) => i.displayName)).toEqual(["Wood Corner", "Azure Interior"]);
});

test("le systray liste les récents et rouvre l'enregistrement", async () => {
    mockDoAction();
    await mountWithCleanup(RecentsSystray);
    expect(".o_recents_count").toHaveCount(0);

    getService(RecentsPlugin).visit({ resModel: "partner", resId: 2, displayName: "Wood Corner" });
    await contains(".o_recents_systray").click();
    expect(".o_recents_count").toHaveText("1");
    expect(queryAllTexts(".o_recents_item span")).toEqual(["Wood Corner"]);

    await contains(".o_recents_item").click();
    expect.verifySteps(["partner,2"]);
});

test("menu utilisateur : l'entrée n'apparaît que s'il y a des récents", async () => {
    clearRegistry(registry.category("user_menuitems"));
    registry.category("user_menuitems").add("oski_recents_clear", clearRecentsItem);
    await mountWithCleanup(UserMenu);
    await contains("button.dropdown-toggle").click();
    expect("[data-menu=oski_recents_clear]").toHaveCount(0);

    getService(RecentsPlugin).visit({ resModel: "partner", resId: 1, displayName: "Azure Interior" });
    await contains("button.dropdown-toggle").click(); // referme
    await contains("button.dropdown-toggle").click(); // rouvre
    await contains("[data-menu=oski_recents_clear]").click();
    expect(getService(RecentsPlugin).items.length).toBe(0);
    expect(browser.localStorage.getItem("oski_owl_recents.7")).toBe("[]");
});

test("patch : ordre d'application et dépatch", () => {
    const salut = {
        dire() {
            return "original";
        },
    };
    const unpatchA = patch(salut, {
        dire() {
            return `A(${super.dire()})`;
        },
    });
    const unpatchB = patch(salut, {
        dire() {
            return `B(${super.dire()})`;
        },
    });
    expect(salut.dire()).toBe("B(A(original))"); // le dernier patch appliqué s'exécute en premier

    unpatchA(); // retire A, réapplique B
    expect(salut.dire()).toBe("B(original)");
    unpatchB();
    expect(salut.dire()).toBe("original");

    expect(() => patch(salut, "mon_patch", {})).toThrow(/Second argument is not the patch name anymore/);
});
