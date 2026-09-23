"""Rend les 4 bannières de rubrique du blog OdooSkills en PNG.

Rendu en 2x puis réduction LANCZOS : les dimensions finales restent celles
attendues par les pièces jointes de production (aucun changement d'URL).

    /home/stadev/vscode-projects/odoo19-dev/venv/bin/python _capture.py
"""
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
COVERS = [
    ("fonctionnel-odoo.html", "fonctionnel-odoo.png", 1920, 700),
    ("developpement-odoo.html", "developpement-odoo.png", 1920, 700),
    ("radar-odoo.html", "radar-odoo.png", 1920, 600),
    ("la-bibliotheque.html", "la-bibliotheque.png", 1920, 600),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for html_name, png_name, w, h in COVERS:
        context = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
        page = context.new_page()
        page.goto(f"file://{HERE / html_name}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(400)
        out = HERE / png_name
        page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
        context.close()
        im = Image.open(out)
        if im.size != (w, h):
            im.convert("RGB").resize((w, h), Image.LANCZOS).save(out, optimize=True)
        print(f"OK  {png_name}  {Image.open(out).size}  {out.stat().st_size // 1024} Ko")
    browser.close()
