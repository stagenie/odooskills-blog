/** Popup capture email — PC uniquement, déclencheur min(5min, scroll 60%). */
document.addEventListener("DOMContentLoaded", function () {
    initLeadPopup();
    initPdfGate();
});

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
    // CTA inline (Task 6) : ouverture explicite → passe par show() (PC uniquement).
    document.addEventListener("click", function (e) {
        const trigger = e.target.closest(".osk-open-popup");
        if (!trigger) {
            return;
        }
        e.preventDefault();
        if (!isMobile) {
            show();
        }
    });

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
    const gMsg = modal.querySelector(".osk-lead-msg");
    document.querySelectorAll(".osk-pdf-gate .osk-pdf-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            pendingPostId = this.closest(".osk-pdf-gate").dataset.postId;
            modal.style.display = "flex";
        });
    });
    modal.querySelector(".osk-lead-close").addEventListener("click", () => {
        modal.style.display = "none";
    });
    modal.querySelector(".osk-gate-form").addEventListener("submit", async function (e) {
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
                gMsg.textContent = "Merci ! Téléchargement en cours…";
                window.location.href = r.pdf_url;
                setTimeout(() => { modal.style.display = "none"; }, 1500);
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
