import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("oski_code_client_tour", {
    steps: () => [
        {
            content: "Le contact n'a pas encore de code : cliquer sur le bouton",
            trigger: ".o_form_view button[name='action_oski_generer_code']",
            run: "click",
        },
        {
            content: "Le code apparaît sur la fiche",
            trigger: ".o_field_widget[name='oski_code']:contains(CLI-)",
        },
        {
            content: "Le bouton a disparu",
            trigger: ".o_form_view:not(:has(button[name='action_oski_generer_code']))",
        },
    ],
});
