"""Regenera las capturas de docs/ (requiere Playwright + Chromium y tolltip.html ya construido)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang, mode, name in (("es", "Con bandas", "Warrior"), ("en", "With raids", "Warrior")):
            page = browser.new_page(viewport={"width": 1360, "height": 1000})
            page.goto((ROOT / "tolltip.html").as_uri(), wait_until="load")
            page.evaluate("localStorage.clear()")
            page.reload(wait_until="load")
            page.locator('.lang-switch button[data-lang="%s"]' % lang).click()
            page.get_by_role("button", name=name, exact=True).click()
            page.locator("#levelInput").fill("80")
            page.locator("#levelInput").dispatch_event("change")
            page.get_by_role("button", name=mode, exact=True).click()
            page.wait_for_timeout(600)
            page.screenshot(path=str(ROOT / "docs" / ("screenshot-%s.png" % lang)), clip={"x": 0, "y": 0, "width": 1360, "height": 1700})
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
