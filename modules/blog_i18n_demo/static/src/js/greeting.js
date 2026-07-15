import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

// Chaîne côté client marquée pour la traduction avec _t()
const greetingService = {
    start() {
        return {
            message: _t("Bonjour depuis le module de démonstration."),
        };
    },
};

registry.category("services").add("blog_i18n_greeting", greetingService);
