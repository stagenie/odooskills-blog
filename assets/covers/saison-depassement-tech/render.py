#!/usr/bin/env python3
"""Render 3 cover variants to PNG 1920x700 via Playwright."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
DIRECTIONS = ["A", "B", "C"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 700},
            device_scale_factor=2,
        )
        page = ctx.new_page()

        for d in DIRECTIONS:
            html = HERE / f"cover-{d}.html"
            png = HERE / f"cover-direction-{d}.png"
            print(f"→ rendering {html.name}")
            page.goto(f"file://{html}", wait_until="networkidle")
            page.wait_for_timeout(800)
            page.screenshot(
                path=str(png),
                full_page=False,
                clip={"x": 0, "y": 0, "width": 1920, "height": 700},
                omit_background=False,
            )
            print(f"  [OK]   {png} ({png.stat().st_size // 1024} KB)")

        browser.close()

    # Downscale to final output 1920x700 (from retina 3840x1400) via Pillow for web use
    try:
        from PIL import Image

        for d in DIRECTIONS:
            src = HERE / f"cover-direction-{d}.png"
            img = Image.open(src)
            if img.size != (1920, 700):
                img = img.resize((1920, 700), Image.LANCZOS)
                img.save(src, optimize=True)
                print(f"  [RES]  {src.name} → 1920x700 ({src.stat().st_size // 1024} KB)")
    except ImportError:
        print("  [WARN] Pillow non installé — PNG restent à 3840x1400 retina")

    print("\n[OK] 3 covers rendues.")


if __name__ == "__main__":
    sys.exit(main() or 0)
