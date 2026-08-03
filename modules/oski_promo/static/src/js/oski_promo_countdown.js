/** @odoo-module **/

import { whenReady } from "@odoo/owl";

const TICK_MS = 1000;

function deuxChiffres(n) {
    return n < 10 ? "0" + n : "" + n;
}

function formatReste(ms) {
    const total = Math.floor(ms / 1000);
    const jours = Math.floor(total / 86400);
    const heures = Math.floor((total % 86400) / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const secondes = total % 60;
    const horloge =
        deuxChiffres(heures) + ":" + deuxChiffres(minutes) + ":" + deuxChiffres(secondes);
    return jours > 0 ? jours + "j " + horloge : horloge;
}

function eteindre(el) {
    // Le bandeau disparaît entièrement.
    if (el.classList.contains("oski-promo-banner")) {
        el.remove();
        return;
    }
    // Un bloc tarif : on retire le compteur et on revient au prix courant,
    // déjà présent dans le DOM sous data-after.
    el.querySelectorAll(".oski-countdown").forEach((c) => c.remove());
    const apres = el.dataset.after;
    const paye = el.querySelector(".oski-price-pay");
    if (apres && paye) {
        paye.textContent = apres + " €";
    }
    // Le barré n'est pas propre à la campagne : il ne survit que si le
    // prix courant après l'échéance lui reste inférieur, exactement comme
    // le rendu serveur (info['barre'] > info['payer']). Défensif : un
    // attribut absent ou non numérique ne retire rien.
    const barre = parseFloat(el.dataset.barre);
    const apresValeur = parseFloat(el.dataset.afterValue);
    if (!Number.isNaN(barre) && !Number.isNaN(apresValeur) && barre <= apresValeur) {
        const barreEl = el.querySelector(".oski-price-strike");
        if (barreEl) {
            barreEl.remove();
        }
    }
    delete el.dataset.deadline;
}

/**
 * Publie la hauteur réelle du bandeau dans --oski-promo-banner-h, que le
 * SCSS reporte sur tout ce qui est ancré en bas de page (bouton d'achat
 * collant des landings, retour en haut, pied de page). Mesurée et non
 * figée : un libellé long passe à la ligne sur mobile. Remise à 0 dès que
 * le bandeau disparaît, sinon la page garderait un blanc au pied.
 */
function mesurerBandeau() {
    const bandeau = document.querySelector(".oski-promo-banner");
    const hauteur = bandeau ? bandeau.offsetHeight : 0;
    document.documentElement.style.setProperty(
        "--oski-promo-banner-h", hauteur + "px");
}

function tic() {
    const maintenant = Date.now();
    document.querySelectorAll("[data-deadline]").forEach((el) => {
        const echeance = Date.parse(el.dataset.deadline);
        if (Number.isNaN(echeance)) {
            return;
        }
        const reste = echeance - maintenant;
        if (reste <= 0) {
            eteindre(el);
            return;
        }
        const horloge = el.querySelector(".oski-countdown-clock, .oski-promo-banner-clock");
        if (horloge) {
            horloge.textContent = formatReste(reste);
        }
    });
    mesurerBandeau();
}

whenReady(() => {
    tic();
    setInterval(tic, TICK_MS);
});
