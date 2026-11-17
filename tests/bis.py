"""Prueba del panel «BiS por fase» y del tooltip de posiciones (estilo BiS-Tooltip)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()
errors = []


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1200)

        # Pestañas de fase y leyenda
        assert page.locator("#bisTabs button").all_inner_texts() == ["PR", "T7", "T8", "T9", "T10"]
        legend = page.locator("#bisLegend").inner_text()
        assert "BiS²" in legend and "ALT6" in legend

        # Todas las clases y especialidades: cada slot lleva BiS y, como mucho, 6 ALT; los anillos/abalorios llevan BiS²
        res = page.evaluate("""() => {
          const bad = [];
          for (const key of Object.keys(DATA.specs)) {
            const [cls, spec] = key.split('|');
            state.cls = cls; state.spec = spec;
            for (const ph of BIS_PHASES) {
              const d = bisData(ph);
              if (d.rows.length < 12) bad.push(key + ' ' + ph.key + ' filas ' + d.rows.length);
              d.rows.forEach((r) => {
                if (r.list.length > (r.pair ? 8 : 7)) bad.push(key + ' ' + ph.key + ' ' + r.slot + ' demasiados');
                const names = r.list.map((e) => e.it.n);
                if (new Set(names).size !== names.length) bad.push(key + ' ' + ph.key + ' ' + r.slot + ' repetidos');
              });
              const pairs = d.rows.filter((r) => r.pair);
              if (pairs.length !== 2 || pairs.some((r) => r.list.length < 2)) bad.push(key + ' ' + ph.key + ' falta BiS²');
            }
          }
          return bad;
        }""")
        assert not res, res[:10]

        # Las fases son acumulativas: ningún objeto de una fase posterior aparece antes
        res = page.evaluate("""() => {
          state.cls = 'Mage'; state.spec = 'Fire';
          const pr = bisData(BIS_PHASES[0]), t7 = bisData(BIS_PHASES[1]);
          const raidInPr = pr.rows.flatMap((r) => r.list).filter((e) => e.it.raid);
          return { raidInPr: raidInPr.length, t7Raid: t7.rows.flatMap((r) => r.list).filter((e) => e.it.raid).length };
        }""")
        assert res["raidInPr"] == 0 and res["t7Raid"] > 0, res

        # Render del panel: cambiar de pestaña actualiza la nota y la rejilla
        page.get_by_role("button", name="Mage", exact=True).click()
        page.get_by_role("button", name="Fire", exact=True).click()
        page.locator("#bisTabs button", has_text="T9").click()
        page.wait_for_timeout(300)
        assert "Trial of the Crusader" in page.locator("#bisPhaseNote").inner_text()
        assert page.locator("#bisTabs button[aria-pressed='true']").inner_text() == "T9"
        assert page.locator(".bis-card").count() >= 14
        assert page.locator(".bis-card .rank-bis").count() >= 14
        assert page.locator(".bis-card .rank-bis2").count() == 2

        # Tooltip: pasar el cursor por un objeto muestra su posición en cada fase
        page.locator(".bis-card a.bis-name").first.hover()
        page.wait_for_timeout(300)
        tip = page.locator("#bisTip")
        assert tip.is_visible()
        text = tip.inner_text()
        assert "BiS-Tooltip" in text and all(k in text for k in ["PR", "T7", "T8", "T9", "T10"]), text
        page.mouse.move(5, 5)
        page.wait_for_timeout(150)
        assert not tip.is_visible()

        # Etiquetas BiS / ALT también en la ficha principal
        assert page.locator("#slots .slot .rank-bis").count() >= 10
        assert page.locator("#slots .alt-list .rank-alt").count() > 0

        # Persistencia e idioma
        page.reload(wait_until="load")
        page.wait_for_timeout(900)
        assert page.locator("#bisTabs button[aria-pressed='true']").inner_text() == "T9"
        page.locator('.lang-switch button[data-lang="en"]').click()
        page.wait_for_timeout(400)
        assert page.locator("#bisHeading").inner_text() == "BiS by phase"
        assert "Phase 3" in page.locator("#bisPhaseNote").inner_text()
        assert "undefined" not in page.locator("#bisGrid").inner_text().lower()

        browser.close()
    assert not errors, errors
    print("bis OK")


if __name__ == "__main__":
    main()
