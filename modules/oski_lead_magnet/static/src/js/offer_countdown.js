/** Countdown de la landing offre. Vanilla, pas d'OWL (page website simple). */
document.addEventListener("DOMContentLoaded", function () {
    const el = document.getElementById("osk_countdown");
    if (!el || !el.dataset.deadline) {
        return;
    }
    const deadline = new Date(el.dataset.deadline + "Z").getTime();
    function tick() {
        const diff = deadline - Date.now();
        if (diff <= 0) {
            el.textContent = "Expirée";
            return;
        }
        const h = Math.floor(diff / 3.6e6);
        const m = Math.floor((diff % 3.6e6) / 6e4);
        const s = Math.floor((diff % 6e4) / 1e3);
        el.textContent = `${h}h ${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s`;
        setTimeout(tick, 1000);
    }
    tick();
});
