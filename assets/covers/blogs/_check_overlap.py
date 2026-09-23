"""Contrôle des bannières : bande de bas de page neutralisée, texte dans la zone
réellement affichée par le blog (conteneur de 380 px de haut, mesuré en prod)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PAGES = [("radar-odoo.html", 1920, 600), ("la-bibliotheque.html", 1920, 600),
         ("fonctionnel-odoo.html", 1920, 700), ("developpement-odoo.html", 1920, 700)]
BAS = {"radar-odoo.html": ".coords", "la-bibliotheque.html": ".coords",
       "fonctionnel-odoo.html": ".foot", "developpement-odoo.html": ".foot"}

ok = True
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h in PAGES:
        pg = b.new_context(viewport={"width": w, "height": h}).new_page()
        pg.goto(f"file://{HERE / name}?v={__import__('time').time()}")
        pg.wait_for_load_state("networkidle")
        cache = pg.locator(BAS[name]).is_hidden()
        # zone sûre : bande centrale de 380/700 (resp. /600) de la source
        vis = 380 * (h / 380) if False else 380 * (1920 / 1920)
        marge = (h - 380) / 2
        haut, bas = marge, h - marge
        blocs = {}
        for sel in (".pill, .overline", ".title, h1.title", ".tagline, p.tagline"):
            loc = pg.locator(sel).first
            if loc.count():
                bb = loc.bounding_box()
                blocs[sel.split(',')[0]] = (bb["y"], bb["y"] + bb["height"])
        dedans = all(haut - 1 <= y0 and y1 <= bas + 1 for y0, y1 in blocs.values())
        ok &= cache and dedans
        print(f"{'OK ' if cache and dedans else 'KO '} {name:26} bande cachée={cache} | "
              f"zone sûre {haut:.0f}-{bas:.0f} | " +
              " ".join(f"{k}={y0:.0f}-{y1:.0f}" for k, (y0, y1) in blocs.items()))
        pg.close()
    b.close()
raise SystemExit(0 if ok else 1)
