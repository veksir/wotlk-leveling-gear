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
        # Los fallos de red (fuentes, iconos y tooltips de EVOWOW) no son errores de la página.
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1800)

        assert page.locator(".chip").count() == 10
        assert page.locator("#factions button").count() == 2
        assert page.locator(".slot").count() >= 15
        assert "undefined" not in page.locator("body").inner_text().lower()

        page.get_by_role("button", name="Mage", exact=True).click()
        page.get_by_role("button", name="Frost", exact=True).click()
        page.locator("#levelInput").fill("40")
        page.locator("#levelInput").dispatch_event("change")
        page.wait_for_timeout(400)
        assert page.locator("#levelNumber").inner_text() == "40"
        assert page.locator(".slot").first.inner_text().startswith("Cabeza")
        assert "Sin objeto" not in page.locator(".slot").first.inner_text()

        page.get_by_role("button", name="Death Knight", exact=True).click()
        page.wait_for_timeout(300)
        assert page.locator("#levelNumber").inner_text() == "55"

        page.locator('#factions button[data-faction="alliance"]').click()
        page.locator('.lang-switch button[data-lang="en"]').click()
        page.wait_for_timeout(500)
        assert page.locator("h1").inner_text().startswith("What to wear")
        assert page.locator("#classLabel").inner_text() == "Class"
        assert page.locator("#factions button[aria-pressed='true']").inner_text() == "Alliance"
        assert page.locator(".slot").first.inner_text().startswith("Head")

        page.reload(wait_until="load")
        page.wait_for_timeout(900)
        assert page.locator("#levelNumber").inner_text() == "55"
        assert page.locator("#factions button[aria-pressed='true']").inner_text() == "Alliance"
        assert page.locator("h1").inner_text().startswith("What to wear")


        # --- motor v2: bandas, fase, PvP, explicación, fuentes y mazmorras ---
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")
        page.wait_for_timeout(900)
        gear = """(o) => {
          const spec = DATA.specs[o.spec];
          const g = computeGear(spec, o.opts);
          return Object.values(g.slots).flatMap((s) => s.list.map((e) => ({ n: e.it.n, raid: !!e.it.raid, pvp: !!e.it.pvp, ph: e.it.ph || 0, rp: !!e.it.src && e.it.src.t === 'RaidProb' })));
        }"""
        base = {"level": 80, "faction": "horde", "phase": 0, "pvp": False}
        for spec in ("Warrior|Arms", "Death Knight|Frost DPS"):
            raid = page.evaluate(gear, {"spec": spec, "opts": {**base, "scope": "raid"}})
            plain = page.evaluate(gear, {"spec": spec, "opts": {**base, "scope": "noraid"}})
            assert any(x["n"] == "Shadowmourne" for x in raid), spec + ": Shadowmourne debe aparecer con bandas"
            assert not any(x["n"] == "Shadowmourne" for x in plain), spec + ": no debe aparecer sin bandas"
            assert not any(x["raid"] or x["rp"] for x in plain), "sin bandas no admite objetos de banda (ni probables)"
        assert not any(x["n"] == "Shadowmourne" for x in page.evaluate(gear, {"spec": "Paladin|Retribution", "opts": {**base, "scope": "raid"}}))
        assert not any(x["pvp"] for x in page.evaluate(gear, {"spec": "Warrior|Arms", "opts": {**base, "scope": "raid"}})), "PvP excluido por defecto"
        pvp_only = page.evaluate(gear, {"spec": "Warrior|Arms", "opts": {**base, "scope": "raid", "pvp": True}})
        assert len(pvp_only) > 10 and all(x["pvp"] for x in pvp_only), "el modo PvP muestra solo equipo PvP"
        # Regresión: a nivel 25 Paladin Protection debe tener mano secundaria (escudo).
        for fac in ("horde", "alliance"):
            off = page.evaluate("""(f) => computeGear(DATA.specs["Paladin|Protection"], {level: 25, faction: f, scope: "noraid", phase: 0, pvp: false}).slots.offhand.list.length""", fac)
            assert off > 0, "falta la mano secundaria de Paladin Protection (" + fac + ")"
        for ph in (1, 2, 3, 4):
            res = page.evaluate(gear, {"spec": "Mage|Frost", "opts": {**base, "scope": "raid", "phase": ph}})
            assert all(x["ph"] <= ph for x in res), "fase " + str(ph)
        for fac, other in (("horde", "Alianza"), ("alliance", "Horda")):
            res = page.evaluate("""(f) => Object.values(computeGear(DATA.specs["Paladin|Protection"], {level: 40, faction: f, scope: "noraid", phase: 0, pvp: false}).slots)
              .flatMap((s) => s.list.map((e) => e.it.src && e.it.src.t === "Quest" ? (e.it.src.q || []).map((q) => q.f) : []))""", fac)
            assert all(any(str(f).lower() in ("both", fac) for f in fs) for fs in res if fs), "facción " + fac

        # Regresión: «Mi equipo actual» acepta piezas no ideales para la especialidad.
        eq = page.evaluate("""() => { const p = candidates(DATA.specs["Paladin|Protection"]);
          return { twohand: (p.mainhand || []).some((e) => e.it.s === "twohand"), cloth: (p.chest || []).some((e) => e.it.at === "Cloth"),
                   zero: Object.values(p).some((l) => l.some((e) => e.score === 0)) }; }""")
        assert eq["twohand"] and eq["cloth"], "el buscador de equipo debe ofrecer armas de dos manos y otra armadura"
        # Regresiones del motor: procs, topes, 2 manos vs 1 mano + secundaria, raids en el panel.
        eng = page.evaluate("""() => {
          const phy = Object.values(DATA.items).filter((i) => i.n === "Phylactery of the Nameless Lich");
          const shadow = computeGear(DATA.specs["Priest|Shadow"], { level: 80, faction: "horde", scope: "raid", phase: 0, pvp: false });
          const arms = computeGear(DATA.specs["Warrior|Arms"], { level: 80, faction: "horde", scope: "raid", phase: 0, pvp: false });
          const low = computeGear(DATA.specs["Warrior|Arms"], { level: 60, faction: "horde", scope: "raid", phase: 0, pvp: false });
          return { phy: phy.length, phyPx: phy.every((i) => i.px && i.px.sp > 0), loadout: !!shadow.loadout,
                   capsHit: arms.totals && arms.totals.hit > 0, noCapsBelow80: low.totals === null,
                   groups: document.querySelectorAll("#dungeonSelect optgroup").length }; }""")
        assert eng["phy"] == 2 and eng["phyPx"], "Phylactery debe estar con su proc estimado"
        assert eng["loadout"] and eng["capsHit"] and eng["noCapsBelow80"], eng
        assert eng["groups"] == 2, "el selector del botín debe tener mazmorras y bandas"
        page.get_by_role("button", name="Warrior", exact=True).click()
        page.get_by_role("button", name="Arms", exact=True).click()
        page.locator("#levelInput").fill("80")
        page.locator("#levelInput").dispatch_event("change")
        page.get_by_role("button", name="Con bandas", exact=True).click()
        page.locator("#alts button", has_text="10").click()
        page.wait_for_timeout(400)
        assert page.locator("#capsBox").is_visible(), "el panel de topes debe verse a nivel 80"
        assert page.locator(".slot details.why").count() >= 15, "falta el desplegable por qué"
        assert page.locator(".slot .src-badge").count() >= 15, "falta la fuente"
        assert page.locator('#slots a[href$="item=49623"]').count() > 0, "Shadowmourne debe verse con bandas"
        assert page.locator("#alts button[aria-pressed='true']").inner_text() == "10"
        
        page.get_by_role("button", name="Sin bandas", exact=True).click()
        page.wait_for_timeout(300)
        assert page.locator('#slots a[href$="item=49623"]').count() == 0, "Shadowmourne no debe ser un objeto recomendado sin bandas"
        assert "Shadowmourne" in page.locator("#slots .warn").all_inner_texts().__str__(), "debe explicar que el objeto oculto es de banda"

        page.get_by_role("button", name="Paladin", exact=True).click()
        page.get_by_role("button", name="Protection", exact=True).click()
        page.locator("#levelInput").fill("25")
        page.locator("#levelInput").dispatch_event("change")
        page.wait_for_timeout(300)
        page.select_option("#dungeonSelect", value="206")  # Utgarde Keep
        page.wait_for_timeout(300)
        assert page.locator(".loot-row").count() > 0, "el botín de mazmorra no muestra objetos"
        empty_rows = page.locator(".loot-row .delta.up").count()
        page.locator("#eqUseRec").click()
        page.wait_for_timeout(300)
        assert page.locator("#eqGrid input").first.input_value() != "", "Usar el recomendado debe llenar el equipo"
        assert page.locator(".loot-row").count() > 0
        assert page.locator(".loot-row .delta.up").count() <= empty_rows, "con equipo puesto hay menos mejoras que con slots vacíos"
        page.locator("#eqGrid input").first.click()
        assert page.locator(".eq-sug li").count() > 0, "el buscador de equipo debe sugerir objetos"
        page.locator("#eqClear").click()
        page.wait_for_timeout(200)
        assert page.locator("#eqGrid input").first.input_value() == ""
        for zone, name in (("4812", "Icecrown Citadel"), ("4273", "Ulduar"), ("4722", "Trial of the Crusader")):
            page.locator("#levelInput").fill("80")
            page.locator("#levelInput").dispatch_event("change")
            page.select_option("#dungeonSelect", value=zone)
            page.wait_for_timeout(300)
            assert page.locator(".boss h3").count() >= 3, name + ": el botín de banda debe mostrar jefes"
            assert page.locator(".loot-row").count() > 20, name + ": faltan objetos"
        page.select_option("#dungeonSelect", value="0")
        assert page.locator(".loot-row").count() > 0
        assert page.locator("details.calc").count() == 1 and page.locator(".side details.calc").count() == 0

        assert not errors, errors
        print("smoke ok:", page.locator(".slot").count(), "slots")
        browser.close()


if __name__ == "__main__":
    main()
