"""Simule le conteneur du blog (380 px de haut, background cover centré)
et rend chaque bannière telle que le site l'affichera, en 1440 et 1920."""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "_apercu"
OUT.mkdir(exist_ok=True)
PNGS = ["fonctionnel-odoo.png", "developpement-odoo.png", "radar-odoo.png", "la-bibliotheque.png"]
TMP = OUT / "_frame.html"

with sync_playwright() as p:
    b = p.chromium.launch()
    for vw in (1440, 1920):
        pg = b.new_context(viewport={"width": vw, "height": 380}).new_page()
        for png in PNGS:
            TMP.write_text(
                f'<style>html,body{{margin:0}}div{{width:{vw}px;height:380px;'
                f'background:url("../{png}") center/cover no-repeat}}</style><div></div>',
                encoding='utf-8')
            pg.goto(f"file://{TMP}?v={png}{vw}")
            pg.wait_for_timeout(350)
            pg.screenshot(path=str(OUT / f"{png[:-4]}-{vw}.png"))
        pg.close()
        print("rendu", vw)
    b.close()
TMP.unlink()
