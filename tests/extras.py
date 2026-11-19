"""Prueba de las funciones extra: guía BiS (T10), plan de farmeo, gemas por pieza, pesos editables,
exportar/importar/compartir equipo, traducción de notas de gemas y tamaño del HTML comprimido.
Uso: python tests/extras.py   (requiere tolltip.html construido y Playwright)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "tolltip.html"
URL = FILE.as_uri()
errors = []


def main():
    assert FILE.stat().st_size < 2_500_000, "tolltip.html debería ir comprimido (< 2,5 MB)"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Paladin", exact=True).click()
        page.get_by_role("button", name="Protection", exact=True).click()

        # 1. Guía de Icy Veins como BiS en T10 (y solo ahí)
        res = page.evaluate("""() => {
          const t10 = BIS_PHASES[4], t8 = BIS_PHASES[2];
          const ref = ENG.refBis['Paladin|Protection'].chest[0];
          const on = bisData(t10).rows.find((r) => r.slot === 'chest').list[0];
          const curatedT8 = bisData(t8).rows.some((r) => r.list.some((e) => e.curated));
          state.bisGuide = false; const off = bisData(t10).rows.some((r) => r.list.some((e) => e.curated)); state.bisGuide = true;
          return { ref, on: on.id, curated: on.curated === true, curatedT8, off };
        }""")
        assert res["on"] == res["ref"] and res["curated"] and not res["curatedT8"] and not res["off"], res
        page.locator("#bisTabs button", has_text="T10").click()
        assert page.locator("#bisGuideBox").is_visible()
        assert page.locator(".bis-guide-tag").count() >= 8
        page.locator("#bisGuide").uncheck()
        assert page.locator(".bis-guide-tag").count() == 0
        page.locator("#bisGuide").check()

        # 2. Plan de farmeo y porcentaje del BiS
        assert page.locator("#bisPlan .plan-grid .bis-card").count() >= 3
        res = page.evaluate("""() => {
          const d = bisData(BIS_PHASES[4]), g = {};
          d.rows.forEach((r) => { g[r.slot] = r.list[0].id; if (r.pair) g[r.slot.slice(0, -1) + '2'] = r.list[1].id; });
          state.gear[gearKey()] = g; render();
          return document.getElementById('bisPlan').innerText;
        }""")
        assert ("100" in res and "todo el BiS" in res), res[:300]
        page.evaluate("state.gear[gearKey()] = {}; persist(); render();")

        # 3. Gemas por pieza: respeta o ignora el bonus según el valor
        txt = page.locator("#bisGrid").inner_text().lower()
        assert "respeta los colores" in txt or "ignora el bonus" in txt, txt[:200]

        # 4. Pesos editables: cambian el ranking y se pueden restablecer
        before = page.evaluate("bisData(BIS_PHASES[2]).rows.map((r) => r.list.map((e) => e.it.n).join(',')).join('|')")
        page.locator("#wDetails summary").click()
        inp = page.locator("#w_sta")
        assert inp.count() == 1
        inp.fill("0"); inp.dispatch_event("change"); page.wait_for_timeout(300)
        after = page.evaluate("bisData(BIS_PHASES[2]).rows.map((r) => r.list.map((e) => e.it.n).join(',')).join('|')")
        assert before != after, "el peso de Stamina a 0 debería cambiar el ranking de un tanque"
        assert page.evaluate("JSON.stringify(state.wOverride)") != "{}"
        page.locator("#wReset").click(); page.wait_for_timeout(300)
        assert page.evaluate("JSON.stringify(state.wOverride)") == "{}"
        assert page.evaluate("bisData(BIS_PHASES[2]).rows.map((r) => r.list.map((e) => e.it.n).join(',')).join('|')") == before

        # 5. Exportar, importar y compartir
        page.evaluate("""() => { const d = bisData(BIS_PHASES[4]), g = {}; d.rows.forEach((r) => { g[r.slot] = r.list[0].id; if (r.pair) g[r.slot.slice(0, -1) + '2'] = r.list[1].id; }); state.gear[gearKey()] = g; render(); }""")
        want = page.evaluate("JSON.stringify(equippedMap())")
        page.locator("#eqExport").click(); page.wait_for_timeout(300)
        text = page.locator("#eqText").input_value()
        assert text.startswith("# WotLK Leveling Gear") and text.count("\\n") >= 12 or text.count("\n") >= 12, text[:200]
        page.evaluate("state.gear[gearKey()] = {}; persist(); render();")
        page.locator("#eqImport").click(); page.locator("#eqText").fill(text); page.locator("#eqApply").click(); page.wait_for_timeout(400)
        assert page.evaluate("JSON.stringify(equippedMap())") == want
        # importar por nombre y sin etiqueta
        page.evaluate("state.gear[gearKey()] = {}; persist(); render();")
        page.locator("#eqImport").click(); page.locator("#eqText").fill("Conqueror's Aegis Faceguard\nCabeza: Nombre inventado\nPecho: Blightborne Warplate"); page.locator("#eqApply").click(); page.wait_for_timeout(300)
        got = page.evaluate("Object.keys(equippedMap()).sort().join(',')")
        assert got == "chest,head", got
        assert "sin reconocer: 1" in page.locator("#eqIoMsg").inner_text()
        # enlace compartible
        page.evaluate("state.gear[gearKey()] = {}; persist(); render();")
        page.evaluate("""() => { const d = bisData(BIS_PHASES[4]); state.gear[gearKey()] = { head: d.rows[0].list[0].id }; render(); }""")
        link = page.evaluate("eqShareUrl()")
        want = page.evaluate("JSON.stringify(equippedMap())")
        page2 = browser.new_page(viewport={"width": 1360, "height": 1000})
        page2.on("pageerror", lambda e: errors.append(str(e)))
        page2.goto(link, wait_until="load"); page2.wait_for_timeout(1500)
        assert page2.evaluate("state.cls + '|' + state.spec") == "Paladin|Protection"
        assert page2.evaluate("JSON.stringify(equippedMap())") == want
        assert "#eq=" not in page2.url
        page2.close()
        page.evaluate("state.gear[gearKey()] = {}; persist(); render();")

        # 6. Inglés: ninguna nota de gemas queda sin traducir y las 31 reglas existen
        res = page.evaluate("""() => {
          state.lang = 'en'; const bad = [];
          for (const k of Object.keys(DATA.specs)) {
            const ref = ENG.refGems[k];
            if (!ref.ruleEn || ES_MARK.test(ref.ruleEn.replace(/\\b(a|an)\\b/g, ''))) bad.push(k + ' regla');
            [].concat(ref.red, ref.yellow, ref.blue, ref.meta ? [ref.meta] : [], Object.values(ref.enchants)).forEach((g) => {
              const orig = (g.stats.match(/\\(([^)]*)\\)/g) || []).length, now = (noteText(g.stats).match(/\\(([^)]*)\\)/g) || []).length;
              if (orig !== now) bad.push(k + ' ' + g.name);
            });
          }
          state.lang = 'es'; return bad;
        }""")
        assert not res, res[:6]

        # 7. «Recién 80» primero y sin heroicas; PR ya las incluye
        res = page.evaluate("""() => {
          const heroic = (ph) => bisData(ph).rows.flatMap((r) => r.list).filter((e) => isHeroicOnlyDrop(e.it)).length;
          return { f80: heroic(BIS_TABS[0]), pr: heroic(BIS_PHASES[0]), first: BIS_TABS[0].key };
        }""")
        assert res["first"] == "F80" and res["f80"] == 0 and res["pr"] > 0, res

        res = page.evaluate("""() => {
          const bad = [];
          for (const key of Object.keys(DATA.specs)) {
            const [cls, spec] = key.split('|'); state.cls = cls; state.spec = spec;
            const d = bisData(BIS_TABS[0]);
            if (d.rows.length < 12) bad.push(key + ' filas ' + d.rows.length);
            if (d.rows.some((r) => r.list.length === 0 && r.slot !== 'offhand')) bad.push(key + ' slot vacío');
            if (d.rows.flatMap((r) => r.list).some((e) => isHeroicOnlyDrop(e.it) || (e.it.raid && e.it.ph > 0 && e.it.src && e.it.src.t === 'Drop' && e.it.raid))) bad.push(key + ' heroica o banda en Recién 80');
          }
          return bad;
        }""")
        assert not res, res[:8]
        page.get_by_role("button", name="Paladin", exact=True).click(); page.get_by_role("button", name="Protection", exact=True).click()

        # 8. Orden de secciones: a nivel 80 el BiS va antes del equipo recomendado; por debajo, después
        page.locator("#levelInput").fill("80"); page.locator("#levelInput").dispatch_event("change"); page.wait_for_timeout(500)
        order = page.evaluate("[...document.querySelector('main').children].map((e) => e.id || e.className.split(' ')[0]).join('>')")
        assert order.index("bisPanel") < order.index("gemPanel") < order.index("main") < order.index("lootPanel"), order
        assert page.evaluate("[...document.querySelectorAll('#jump a')].map((a) => a.dataset.j).join()") == "bis,gem,sheet,loot,top"
        page.locator("#levelInput").fill("60"); page.locator("#levelInput").dispatch_event("change"); page.wait_for_timeout(500)
        order = page.evaluate("[...document.querySelector('main').children].map((e) => e.id || e.className.split(' ')[0]).join('>')")
        assert order.index("main") < order.index("bisPanel") < order.index("gemPanel") < order.index("lootPanel"), order
        page.locator("#bisTabs button", has_text="Recién").click()
        assert page.locator("#bisGuideBox").is_hidden(), "la casilla de la guía solo debe verse en T10"
        page.locator("#bisTabs button", has_text="T10").click()
        assert page.locator("#bisGuideBox").is_visible()

        # 9. Opciones plegables con resumen y fuentes incrustadas (sin Google Fonts)
        assert "Sin bandas" in page.locator("#advState").inner_text()
        assert page.evaluate("""Promise.all([document.fonts.load('700 16px Cinzel'), document.fonts.load('400 16px "Source Sans 3"')]).then((r) => r.every((f) => f.length > 0))"""), "las fuentes incrustadas no cargan"
        assert "fonts.googleapis" not in FILE.read_text(encoding="utf-8")
        browser.close()
    assert not errors, errors
    print("extras OK")


if __name__ == "__main__":
    main()
