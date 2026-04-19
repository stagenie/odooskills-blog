#!/usr/bin/env python3
"""Render T24 visuals to PNG via Playwright."""
from __future__ import annotations

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
JOBS = [
    ("pyramid.html", "pyramid.png", 1200, 800),
    ("terminal-green.html", "terminal-green.png", 1200, 760),
    ("terminal-red.html", "terminal-red.png", 1200, 700),
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for html_name, png_name, w, h in JOBS:
            html = HERE / html_name
            png = HERE / png_name
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
            page = ctx.new_page()
            page.goto(f"file://{html}", wait_until="networkidle")
            page.wait_for_timeout(600)
            page.screenshot(path=str(png), full_page=False, clip={"x": 0, "y": 0, "width": w, "height": h})
            ctx.close()
            print(f"  [OK] {png_name} ({png.stat().st_size // 1024} KB @ {w*2}x{h*2})")
        browser.close()

    try:
        from PIL import Image
        for _, png_name, w, h in JOBS:
            src = HERE / png_name
            img = Image.open(src)
            if img.size != (w, h):
                img = img.resize((w, h), Image.LANCZOS)
                img.save(src, optimize=True)
                print(f"  [RES] {png_name} → {w}x{h} ({src.stat().st_size // 1024} KB)")
    except ImportError:
        pass

    print("\n[OK] 3 visuals rendues.")


if __name__ == "__main__":
    sys.exit(main() or 0)
