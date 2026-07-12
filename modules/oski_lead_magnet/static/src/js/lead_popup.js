/** Popup capture email — PC uniquement, déclencheur min(5min, scroll 60%). */
document.addEventListener("DOMContentLoaded", function () {
    const popup = document.querySelector(".osk-lead-popup");
    if (!popup) {
        return;
    }
    const SEEN = "osk_lead_seen";
    const hasCookie = (n) => document.cookie.split("; ").some((c) => c.startsWith(n + "="));
    const setCookie = (n, days) => {
        const d = new Date();
        d.setTime(Date.now() + days * 864e5);
        document.cookie = `${n}=1; expires=${d.toUTCString()}; path=/`;
    };
    const isMobile = window.matchMedia("(max-width: 767px)").matches ||
        /Mobi|Android/i.test(navigator.userAgent);
    if (isMobile || hasCookie(SEEN)) {
        return;
    }

    let shown = false;
    function show() {
        if (shown) {
            return;
        }
        shown = true;
        popup.style.display = "block";
        window.removeEventListener("scroll", onScroll);
    }
    // 5 min
    const timer = setTimeout(show, 5 * 60 * 1000);
    // scroll 60%
    function onScroll() {
        const h = document.documentElement;
        const pct = (h.scrollTop + window.innerHeight) / h.scrollHeight;
        if (pct >= 0.6) {
            clearTimeout(timer);
            window.removeEventListener("scroll", onScroll);
            show();
        }
    }
    window.addEventListener("scroll", onScroll, { passive: true });

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
            if (r.ok) {
                msg.textContent = r.new
                    ? "Merci ! Vérifiez votre boîte : votre remise -50% vous attend."
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

    // ----- Gate PDF -----
    const modal = document.querySelector(".osk-gate-modal");
    if (modal) {
        let pendingPostId = null;
        const gMsg = modal.querySelector(".osk-lead-msg");
        document.querySelectorAll(".osk-pdf-gate .osk-pdf-btn").forEach((btn) => {
            btn.addEventListener("click", function () {
                pendingPostId = this.closest(".osk-pdf-gate").dataset.postId;
                modal.style.display = "block";
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
});
