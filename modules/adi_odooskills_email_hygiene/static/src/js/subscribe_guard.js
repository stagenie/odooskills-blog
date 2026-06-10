/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Subscribe } from "@website_mass_mailing/interactions/subscribe";

/**
 * Garde anti double-soumission du formulaire newsletter.
 *
 * Le widget natif `Subscribe.onSubscribeClick` est `async` et `await` le RPC
 * `/website_mass_mailing/subscribe` sans verrouiller le bouton pendant la
 * requête. Un double-clic rapide (ou un renvoi navigateur) déclenche donc deux
 * appels concurrents : la 2e requête cherche le contact par email AVANT que la
 * 1re n'ait commit -> les deux le créent -> doublon dans la liste de contacts
 * (cas observé 2026-06-09 : ids 7463/7464 créés à 0,7 s d'écart).
 *
 * On ajoute un verrou de ré-entrée + on désactive le bouton tant que le RPC est
 * en vol. Le bouton est ré-activé uniquement si le visiteur voit encore le
 * formulaire (un abonnement réussi masque `.js_subscribe_wrap` et garde le
 * bouton désactivé volontairement côté natif).
 */
patch(Subscribe.prototype, {
    async onSubscribeClick() {
        if (this._subscribeInFlight) {
            return;
        }
        this._subscribeInFlight = true;
        const btnEl = this.el.querySelector(".js_subscribe_btn");
        if (btnEl) {
            btnEl.disabled = true;
        }
        try {
            return await super.onSubscribeClick(...arguments);
        } finally {
            this._subscribeInFlight = false;
            const subscribeWrapEl = this.el.querySelector(".js_subscribe_wrap");
            const stillSubscribing =
                !subscribeWrapEl || !subscribeWrapEl.classList.contains("d-none");
            if (btnEl && stillSubscribing) {
                btnEl.disabled = false;
            }
        }
    },
});
