"""Prueba de navegación, filtros plegables en móvil, foco visible, tamaños de letra y metadatos de la página."""
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()
errors = []


def main():
    index = (ROOT / "src" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "src" / "styles" / "app.css").read_text(encoding="utf-8")
    tiny = [m for m in re.findall(r"font-size:\s*([0-9.]+)px", css) if float(m) < 11]
    assert not tiny, f"hay tamaños de letra menores de 11px: {tiny}"
    for tag in ('name="description"', 'name="theme-color"', 'rel="icon"', 'name="color-scheme"'):
        assert tag in index, tag
    assert "power.js" in index and "defer" in index[index.index("power.js"):index.index("power.js") + 120]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1500)

        # Navegación entre secciones: enlaces, destinos y sticky
        links = page.locator("#jump a")
        assert links.count() == 5 and page.locator("nav[aria-label]").count() == 1
        for sec in ("sheetPanel", "bisPanel", "gemPanel", "lootPanel", "top"):
            assert page.locator("#" + sec).count() == 1, sec
        page.locator("#jump a[data-j='gem']").click()
        page.wait_for_function("(() => { const y = document.getElementById('gemPanel').getBoundingClientRect().top; return y >= 0 && y < 200; })()", timeout=6000)
        assert page.evaluate("getComputedStyle(document.getElementById('jump')).position") == "sticky"
        assert page.locator("#jump a[aria-current='true']").count() == 1
        page.locator("#jump a[data-j='top']").click()
        page.wait_for_function("window.scrollY < 50", timeout=6000)
        assert page.locator("h1").count() == 1

        # Foco visible con teclado
        page.keyboard.press("Tab"); page.keyboard.press("Tab")
        outline = page.evaluate("(() => { const s = getComputedStyle(document.activeElement); return s.outlineStyle + ' ' + s.outlineWidth; })()")
        assert outline.startswith("solid 2px"), outline

        # Idioma del documento
        page.locator('.lang-switch button[data-lang="en"]').click()
        page.wait_for_timeout(300)
        assert page.evaluate("document.documentElement.lang") == "en"
        assert "Recommended gear" in page.locator("#jump a[data-j='sheet']").inner_text()
        page.locator('.lang-switch button[data-lang="es"]').click()

        # Móvil: los filtros se pliegan y se recuerda la elección; sin desbordes horizontales
        mob = browser.new_page(viewport={"width": 390, "height": 844})
        mob.on("pageerror", lambda e: errors.append(str(e)))
        mob.goto(URL, wait_until="load")
        mob.wait_for_timeout(1500)
        assert mob.locator("#deckToggle").is_visible() and mob.locator("#deckMain").is_visible()
        mob.locator("#deckToggle").click()
        assert not mob.locator("#deckMain").is_visible()
        assert mob.locator("#deckToggle").get_attribute("aria-expanded") == "false"
        mob.reload(wait_until="load"); mob.wait_for_timeout(1200)
        assert not mob.locator("#deckMain").is_visible(), "debería recordar que los filtros están plegados"
        assert mob.evaluate("document.documentElement.scrollWidth") <= 392
        mob.locator("#deckToggle").click()
        assert mob.locator("#deckMain").is_visible()
        assert not page.locator("#deckToggle").is_visible()
        browser.close()
    assert not errors, errors
    print("ux OK")


if __name__ == "__main__":
    main()
