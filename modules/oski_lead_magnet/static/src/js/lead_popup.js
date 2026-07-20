/** Popup capture email — PC uniquement, déclencheur min(5min, scroll 60%). */
// Les bundles frontend Odoo s'exécutent souvent APRÈS DOMContentLoaded : un
// simple addEventListener('DOMContentLoaded') ne se déclencherait jamais et le
// popup resterait mort. On lance donc immédiatement si le DOM est déjà prêt.
// ⚠️ L'appel onReady() est en BAS du fichier : s'il tourne ici (DOM déjà prêt),
// il s'exécute de façon synchrone AVANT les const ci-dessous (hasCookie…) →
// ReferenceError (TDZ). En fin de fichier, toutes les const sont initialisées.
function onReady(fn) {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", fn);
    } else {
        fn();
    }
}

const SEEN = "osk_lead_seen";
const hasCookie = (n) => document.cookie.split("; ").some((c) => c.startsWith(n + "="));
const setCookie = (n, days) => {
    const d = new Date();
    d.setTime(Date.now() + days * 864e5);
    document.cookie = `${n}=1; expires=${d.toUTCString()}; path=/`;
};

function initLeadPopup() {
    const popup = document.querySelector(".osk-lead-popup");
    if (!popup) {
        return;
    }
    // Ne pas interrompre un acheteur en cours de paiement.
    if (/^\/shop\/(cart|checkout|payment|confirmation)/.test(location.pathname)) {
        return;
    }
    const isMobile = window.matchMedia("(max-width: 767px)").matches ||
        /Mobi|Android/i.test(navigator.userAgent);

    let shown = false;
    let gridLoaded = false;
    let timer = null;
    function loadGrid() {
        if (gridLoaded) {
            return;
        }
        gridLoaded = true;
        fetch("/oski/offer/grid", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} }),
        }).then((r) => r.json()).then((data) => {
            const rows = (data.result && data.result.rows) || [];
            const grid = popup.querySelector(".osk-lead-grid");
            if (!grid || !rows.length) {
                return;
            }
            grid.innerHTML = rows.map((row) =>
                `<div class="osk-lead-grid-row"><span>${row.name}</span>` +
                `<span><s>${row.regular.toFixed(2)}€</s> ` +
                `<strong>${row.discounted.toFixed(2)}€</strong></span></div>`
            ).join("");
        }).catch(() => {});
    }
    // show() est le SEUL chemin d'affichage : il démantèle systématiquement
    // tous les déclencheurs auto (timer + scroll + exit-intent) au 1er appel,
    // qu'il soit invoqué par un trigger auto OU par le CTA inline.
    function show() {
        if (shown) {
            return;
        }
        shown = true;
        clearTimeout(timer);
        window.removeEventListener("scroll", onScroll);
        document.removeEventListener("mouseout", onExit);
        loadGrid();
        popup.style.display = "block";
    }
    // exit-intent (souris vers le haut de la fenêtre)
    function onExit(e) {
        if (e.clientY <= 0) {
            show();
        }
    }
    // scroll 60%
    function onScroll() {
        const h = document.documentElement;
        const pct = (h.scrollTop + window.innerHeight) / h.scrollHeight;
        if (pct >= 0.6) {
            show();
        }
    }

    function dismiss() {
        popup.style.display = "none";
        setCookie(SEEN, 30);
    }
    popup.querySelector(".osk-lead-close").addEventListener("click", dismiss);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && popup.style.display === "block") {
            dismiss();
        }
    });
    // Chargement grille sur demande explicite (event harmless : show() charge déjà).
    popup.addEventListener("osk:forceGrid", loadGrid);
    // Le CTA inline ".osk-open-popup" (badge carte catalogue + lien fiche
    // produit) a été retiré le 19/07/2026 (product_cta_templates.xml
    // supprimé, remise désormais permanente sur le prix affiché) : plus
    // aucun élément ne porte cette classe, le handler de clic dédié est
    // retiré pour ne pas laisser de référence morte à une classe qui n'est
    // plus jamais rendue.

    // Déclencheurs AUTO : uniquement PC + visiteur pas encore vu.
    if (!isMobile && !hasCookie(SEEN)) {
        timer = setTimeout(show, 5 * 60 * 1000);
        window.addEventListener("scroll", onScroll, { passive: true });
        document.addEventListener("mouseout", onExit);
    }

    popup.querySelector(".osk-lead-form").addEventListener("submit", async function (e) {
        e.preventDefault();
        const email = this.email.value;
        const consent = this.consent.checked;
        const msg = popup.querySelector(".osk-lead-msg");
        try {
            const resp = await fetch("/oski/lead/subscribe", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0", method: "call",
                    params: { email, consent, source: "popup" },
                }),
            });
            const data = await resp.json();
            const r = data.result || {};
            msg.style.display = "block";
            const pct = popup.dataset.percent || "30";
            if (r.ok) {
                msg.textContent = r.new
                    ? `Merci ! Vérifiez votre boîte : votre remise -${pct}% vous attend.`
                    : "Merci, vous êtes inscrit !";
                setCookie(SEEN, 30);
                setTimeout(dismiss, 2500);
            } else if (r.error === "disposable") {
                msg.textContent = "Merci d'utiliser une adresse email valide.";
            } else if (r.error === "rate_limited") {
                msg.textContent = "Trop de tentatives, réessayez dans une minute.";
            } else {
                msg.textContent = "Email invalide.";
            }
        } catch (err) {
            msg.style.display = "block";
            msg.textContent = "Une erreur est survenue, réessayez.";
        }
    });
}

// ----- Gate PDF ----- doit fonctionner pour TOUS (mobile inclus, sans cookie guard).
function initPdfGate() {
    const modal = document.querySelector(".osk-gate-modal");
    if (!modal) {
        return;
    }
    let pendingPostId = null;
    let autoCloseTimer = null;
    const gMsg = modal.querySelector(".osk-lead-msg");
    const cover = modal.querySelector(".osk-gate-cover");

    function closeModal() {
        clearTimeout(autoCloseTimer);
        modal.style.display = "none";
    }

    // Le modal se referme seul une fois qu'il n'attend plus rien de personne.
    function autoClose(delay) {
        clearTimeout(autoCloseTimer);
        autoCloseTimer = setTimeout(closeModal, delay);
    }

    document.querySelectorAll(".osk-pdf-gate .osk-pdf-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            const gate = this.closest(".osk-pdf-gate");
            pendingPostId = gate.dataset.postId;
            // Habille le bandeau avec la couverture de l'article ; sans
            // couverture on laisse le dégradé défini en CSS.
            if (cover) {
                const url = gate.dataset.cover;
                cover.style.backgroundImage = url ? 'url("' + url + '")' : "";
            }
            clearTimeout(autoCloseTimer);
            modal.style.display = "flex";
        });
    });
    modal.querySelector(".osk-lead-close").addEventListener("click", closeModal);
    const form = modal.querySelector(".osk-gate-form");
    const done = modal.querySelector(".osk-gate-done");
    const optin = done ? done.querySelector(".osk-gate-optin") : null;
    const optinMsg = done ? done.querySelector(".osk-optin-msg") : null;

    // Bascule le modal en écran de confirmation. `askConsent` est faux si
    // l'internaute a déjà donné son accord (case cochée, ou déjà inscrit) :
    // inutile de le lui redemander.
    function showDone(askConsent) {
        if (!done) {
            closeModal();
            return;
        }
        form.style.display = "none";
        modal.querySelector(".osk-gate-icon").style.display = "none";
        modal.querySelector(".osk-lead-title").style.display = "none";
        modal.querySelector(".osk-lead-sub").style.display = "none";
        if (optin && !askConsent) {
            optin.style.display = "none";
        }
        done.style.display = "block";
        // Rien n'est attendu de l'internaute déjà inscrit : on referme.
        // Sinon on laisse le temps de lire et de répondre.
        if (!askConsent) {
            autoClose(3500);
        }
    }

    if (done) {
        done.querySelector(".osk-optin-no").addEventListener("click", closeModal);
        done.querySelector(".osk-optin-yes").addEventListener("click", async () => {
            try {
                const resp = await fetch("/oski/lead/consent", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} }),
                });
                const data = await resp.json();
                optin.style.display = "none";
                optinMsg.style.display = "block";
                const ok = (data.result || {}).ok;
                optinMsg.textContent = ok
                    ? "C'est noté, merci ! À bientôt."
                    : "Une erreur est survenue, réessayez plus tard.";
                // Réponse donnée : le modal n'a plus rien à demander.
                autoClose(ok ? 2200 : 4000);
            } catch (err) {
                optinMsg.style.display = "block";
                optinMsg.textContent = "Une erreur est survenue, réessayez plus tard.";
                autoClose(4000);
            }
        });
    }

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const email = this.email.value;
        const consent = this.consent.checked;
        try {
            const resp = await fetch("/oski/lead/subscribe", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0", method: "call",
                    params: { email, consent, source: "pdf", blog_post_id: pendingPostId },
                }),
            });
            const data = await resp.json();
            const r = data.result || {};
            gMsg.style.display = "block";
            if (r.ok && r.pdf_url) {
                gMsg.style.display = "none";
                window.location.href = r.pdf_url;
                // On garde le modal ouvert : l'accord se demande une fois le
                // PDF obtenu, quand l'attention n'est plus sur le bouton.
                showDone(!consent && !r.subscribed);
            } else if (r.ok) {
                gMsg.textContent = "Merci ! Le PDF n'est pas encore disponible.";
            } else if (r.error === "disposable") {
                gMsg.textContent = "Merci d'utiliser une adresse email valide.";
            } else if (r.error === "rate_limited") {
                gMsg.textContent = "Trop de tentatives, réessayez dans une minute.";
            } else {
                gMsg.textContent = "Email invalide.";
            }
        } catch (err) {
            gMsg.style.display = "block";
            gMsg.textContent = "Une erreur est survenue, réessayez.";
        }
    });
}

// Point d'entrée — en fin de fichier pour que toutes les const/fonctions
// ci-dessus soient initialisées quand onReady s'exécute en mode synchrone
// (DOM déjà prêt, cas fréquent des bundles frontend Odoo).
onReady(function () {
    initPdfGate();
});
