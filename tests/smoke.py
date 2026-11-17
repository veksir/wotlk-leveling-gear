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
        for spec in ("Warrior|Arms", "Death Knight|Unholy DPS"):
            raid = page.evaluate(gear, {"spec": spec, "opts": {**base, "scope": "raid"}})
            plain = page.evaluate(gear, {"spec": spec, "opts": {**base, "scope": "noraid"}})
            assert any(x["n"] == "Shadowmourne" for x in raid), spec + ": Shadowmourne debe aparecer con bandas"
            assert not any(x["n"] == "Shadowmourne" for x in plain), spec + ": no debe aparecer sin bandas"
            assert not any(x["raid"] or x["rp"] for x in plain), "sin bandas no admite objetos de banda (ni probables)"
        # Los paladines sí pueden usar hachas de dos manos (la guía lo recomienda para Retribution)
        assert any(x["n"] == "Shadowmourne" for x in page.evaluate(gear, {"spec": "Paladin|Retribution", "opts": {**base, "scope": "raid"}}))
        assert not any(x["n"] == "Shadowmourne" for x in page.evaluate(gear, {"spec": "Paladin|Retribution", "opts": {**base, "scope": "noraid"}}))
        wpn = page.evaluate("""() => ({paladin: ENG.weaponHands.Paladin.Axe, rogue: ENG.weaponHands.Rogue.Axe, shaman: ENG.weaponHands.Shaman.Axe})""")
        assert wpn == {"paladin": [1, 2], "rogue": [1], "shaman": [1, 2]}, wpn
        dw = page.evaluate("""() => {
          const pick = (g, slot) => g.slots[slot].list[0] && g.slots[slot].list[0].it;
          const frost = computeGear(DATA.specs["Death Knight|Frost DPS"], {level: 80, faction: "horde", scope: "raid", phase: 0, pvp: false});
          const fury = computeGear(DATA.specs["Warrior|Fury"], {level: 80, faction: "horde", scope: "raid", phase: 4, pvp: false});
          const low = computeGear(DATA.specs["Warrior|Fury"], {level: 40, faction: "horde", scope: "noraid", phase: 0, pvp: false});
          const fh = pick(frost, "mainhand"), fo = pick(frost, "offhand");
          const mh = pick(fury, "mainhand"), oh = pick(fury, "offhand");
          const lm = pick(low, "mainhand"), lo = pick(low, "offhand");
          return {frost: [itemHands(fh), itemHands(fo)], fury: [itemHands(mh), itemHands(oh)],
                  names: [mh && mh.n, oh && oh.n], low: [itemHands(lm), itemHands(lo)]};
        }""")
        assert dw["frost"] == [1, 1], dw
        assert dw["fury"] == [2, 2] and dw["names"][0] != dw["names"][1], dw
        assert dw["low"] == [1, 1], dw
        page.evaluate("""() => { state.cls = "Warrior"; state.spec = "Fury"; state.level = 80; state.gear = {}; render(); }""")
        page.wait_for_timeout(200)
        page.evaluate("""() => setEquipped("mainhand", "49623")""")
        page.wait_for_timeout(200)
        assert not page.locator("#eq-offhand").is_disabled(), "Titan's Grip no debe bloquear la mano secundaria"
        page.evaluate("""() => setEquipped("offhand", "50070")""")
        page.wait_for_timeout(200)
        assert page.locator("#eq-offhand").input_value().startswith("Glorenzelg")
        page.evaluate("""() => { state.level = 40; state.gear = {}; render(); }""")
        page.wait_for_timeout(200)
        page.evaluate("""() => setEquipped("mainhand", "49623")""")
        page.wait_for_timeout(200)
        assert page.locator("#eq-offhand").is_disabled(), "sin Titan's Grip la mano secundaria debe bloquearse"
        page.evaluate("""() => { state.gear = {}; }""")
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
        assert any("oculto" in w and "banda" in w for w in page.locator("#slots .warn").all_inner_texts()), "debe explicar que hay objetos ocultos por ser de banda"

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
        assert page.locator("#eqGrid .eq-doll").count() == 1, "el equipo actual debe usar el layout de paper-doll"
        assert page.locator("#eqGrid .eq-doll-col").count() == 2, "el paper-doll debe tener dos columnas laterales"
        assert page.locator("#eqGrid .eq-doll-bottom .eq-slot").count() >= 3, "el paper-doll debe agrupar armas y abalorios abajo"
        slot_options = page.locator("#lootSlot option").all_inner_texts()
        assert "Todas las partes" in slot_options and "Cabeza" in slot_options, "el filtro de botín debe listar las partes"
        page.select_option("#lootSlot", "head")
        page.wait_for_timeout(200)
        head_labels = page.locator(".loot-row > .m:first-child").all_inner_texts()
        assert head_labels and set(head_labels) == {"Cabeza"}, "el filtro de botín debe dejar solo la parte elegida"
        page.select_option("#lootSlot", "")
        page.wait_for_timeout(200)
        assert page.locator(".loot-row").count() > 0, "quitar el filtro debe recuperar el botín"
        page.locator("#eq-head").focus()
        page.wait_for_timeout(250)
        assert page.locator("#lootSlot").input_value() == "head", "enfocar un slot debe filtrar el botín"
        assert page.locator(".eq-slot.is-active #eq-head").count() == 1, "el slot enfocado debe resaltarse"
        page.select_option("#lootSlot", "")
        page.wait_for_timeout(200)
        page.locator("#eqGrid input").first.click()
        assert page.locator(".eq-sug li").count() > 0, "el buscador de equipo debe sugerir objetos"
        page.locator("#eqClear").click()
        page.select_option("#lootSlot", "")
        page.wait_for_timeout(250)
        assert page.locator("#eqGrid input").first.input_value() == ""
        assert page.locator("#lootSort option").count() == 3, "el selector de orden debe tener tres opciones"
        page.select_option("#lootSort", "upgrade")
        page.wait_for_timeout(250)
        assert page.locator("#lootSort").input_value() == "upgrade"
        first_boss = page.locator("details.boss").first
        first_boss.locator("> summary").click()
        page.wait_for_timeout(150)
        assert not first_boss.evaluate("d => d.open"), "el jefe debe poder plegarse"
        first_boss.locator("> summary").click()
        page.wait_for_timeout(150)
        assert first_boss.evaluate("d => d.open"), "el jefe debe poder desplegarse"
        page.select_option("#lootSlot", "neck")
        page.wait_for_timeout(250)
        assert page.locator("#lootBody .loot-empty").is_visible(), "un filtro sin resultados debe mostrar estado vacío"
        page.locator('[data-loot-action="slot"]').click()
        page.wait_for_timeout(250)
        assert page.locator("#lootSlot").input_value() == ""
        page.locator("#levelInput").fill("80")
        page.locator("#levelInput").dispatch_event("change")
        page.select_option("#dungeonSelect", value="4812")
        page.wait_for_timeout(400)
        item = page.locator(".loot-item").first
        item.scroll_into_view_if_needed()
        page.wait_for_timeout(150)
        item.hover()
        page.wait_for_timeout(350)
        hover = page.locator("#lootHover")
        assert hover.is_visible(), "pasar el ratón por el objeto debe mostrar una ventana flotante"
        assert hover.locator("table tbody tr").count() > 0, "la ventana flotante debe comparar estadísticas"
        assert "Puntuación" in hover.inner_text(), "la ventana flotante debe mostrar la puntuación"
        assert not item.locator(".loot-why").evaluate("d => d.open"), "el hover no debe abrir el panel fijo"
        page.mouse.move(0, 0)
        page.wait_for_timeout(200)
        assert page.locator("#lootHover").count() == 0, "salir del objeto debe cerrar la ventana flotante"
        why = item.locator(".loot-why")
        why.locator("summary").click()
        page.wait_for_timeout(150)
        assert why.evaluate("d => d.open"), "el clic debe abrir el desglose fijo"
        why_text = why.inner_text()
        assert why.locator("table tbody tr").count() > 0, "el desglose debe mostrar las estadísticas"
        assert "Puntuación" in why_text and "lootScore" not in why_text, "faltan textos traducidos en el desglose"
        equip = page.locator(".loot-equip").first
        assert equip.count() == 1, "los drops usables deben tener botón Equipar"
        equip_slot = equip.get_attribute("data-slot")
        equip.click()
        page.wait_for_timeout(300)
        assert page.locator("#eq-" + equip_slot).input_value() != "", "Equipar debe llenar el slot correcto"
        assert page.locator("#lootUndo").is_visible(), "Equipar debe ofrecer deshacer"
        page.locator("#lootUndoBtn").click()
        page.wait_for_timeout(300)
        assert page.locator("#eq-" + equip_slot).input_value() == "", "Deshacer debe restaurar el equipo"
        assert page.locator("#lootUndo").is_hidden(), "Deshacer debe ocultar el aviso"
        for zone, name in (("4812", "Icecrown Citadel"), ("4273", "Ulduar"), ("4722", "Trial of the Crusader")):
            page.locator("#levelInput").fill("80")
            page.locator("#levelInput").dispatch_event("change")
            page.select_option("#dungeonSelect", value=zone)
            page.wait_for_timeout(300)
            assert page.locator(".boss h3").count() >= 3, name + ": el botín de banda debe mostrar jefes"
            assert page.locator(".loot-row").count() > 20, name + ": faltan objetos"
        page.select_option("#dungeonSelect", value="4812")
        page.wait_for_timeout(300)
        raw_slots = {"head", "neck", "shoulder", "back", "chest", "wrist", "hands", "waist", "legs", "feet",
                     "ring", "trinket", "mainhand", "offhand", "ranged", "relic", "onehand", "twohand", "held", "thrown"}
        for value in page.locator("#lootSlot option").evaluate_all("els => els.map((e) => e.value).filter(Boolean)"):
            page.select_option("#lootSlot", value)
            page.wait_for_timeout(80)
            labels = set(page.locator(".loot-row > .m:first-child").all_inner_texts())
            bad = labels & raw_slots
            assert not bad, "etiqueta de slot sin traducir: " + ", ".join(sorted(bad))
        page.select_option("#lootSlot", "head")
        page.select_option("#lootSort", "upgrade")
        page.wait_for_timeout(300)
        page.reload(wait_until="load")
        page.wait_for_timeout(700)
        assert page.locator("#lootSlot").input_value() == "head", "el filtro de parte debe persistir"
        assert page.locator("#lootSort").input_value() == "upgrade", "el orden del botín debe persistir"
        page.select_option("#lootSlot", "")
        page.select_option("#lootSort", "boss")
        page.wait_for_timeout(250)
        page.select_option("#dungeonSelect", value="0")
        assert page.locator(".loot-row").count() > 0
        assert page.locator("details.calc").count() == 1 and page.locator(".side details.calc").count() == 0

        reqs = page.evaluate("""() => ({
          uk: heroicRequirement(206), toc: heroicRequirement(4723), fos: heroicRequirement(4809),
          pos: heroicRequirement(4813), hor: heroicRequirement(4820), raid: heroicRequirement(4812)
        })""")
        assert reqs == {"uk": 180, "toc": 200, "fos": 200, "pos": 200, "hor": 219, "raid": 0}, reqs
        access = page.evaluate("""() => {
          state.cls = "Warrior"; state.spec = "Arms"; state.level = 80; state.faction = "horde";
          state.dungeon = 206; state.lootSlot = ""; state.lootSort = "boss"; state.onlyUp = false; state.showOffspec = true;
          const spec = DATA.specs["Warrior|Arms"], slots = specSlots(spec);
          const low = {}; slots.forEach((s) => low[s] = "42944");
          state.gear["Warrior|Arms"] = low; render();
          const lowAvg = averageItemLevel(spec);
          const lowRows = [...document.querySelectorAll("#lootBody .loot-row a")].map((a) => a.getAttribute("href").split("=")[1]);
          const lowAccess = document.getElementById("lootAccess").innerText;
          const lowGeneral = document.getElementById("heroicStatus").innerText;
          const lowRec = computeGear(spec, {level: 80, faction: "horde", scope: "noraid", phase: 0, pvp: false});
          const lowRecH = Object.values(lowRec.slots).flatMap((s) => s.list).filter((e) => isHeroicOnlyDrop(e.it)).length;
          const highId = Object.keys(DATA.items).find((id) => DATA.items[id].ilvl >= 219 && !DATA.items[id].hl);
          const high = {}; slots.forEach((s) => high[s] = highId);
          state.gear["Warrior|Arms"] = high; render();
          const highAvg = averageItemLevel(spec);
          const highRows = [...document.querySelectorAll("#lootBody .loot-row a")].map((a) => a.getAttribute("href").split("=")[1]);
          const highAccess = document.getElementById("lootAccess").innerText;
          const highGeneral = document.getElementById("heroicStatus").innerText;
          const highRec = computeGear(spec, {level: 80, faction: "horde", scope: "noraid", phase: 0, pvp: false});
          const highRecH = Object.values(highRec.slots).flatMap((s) => s.list).filter((e) => isHeroicOnlyDrop(e.it)).length;
          const loot = DATA.loot[206] || {}, byId = {};
          for (const boss in loot) for (const id in loot[boss]) {
            const tags = loot[boss][id].filter((t) => t !== "horde" && t !== "alliance");
            (byId[id] = byId[id] || []).push(tags);
          }
          const heroicIds = Object.keys(byId).filter((id) => byId[id].every((tags) => tags.includes("H") && !tags.includes("N")));
          return {lowAvg, highAvg, lowAccess, highAccess, lowGeneral, highGeneral,
                  lowHeroicRows: lowRows.filter((id) => heroicIds.includes(id)).length,
                  highHeroicRows: highRows.filter((id) => heroicIds.includes(id)).length,
                  lowRecH, highRecH};
        }""")
        assert access["lowAvg"] < 180 and access["highAvg"] >= 219, access
        assert "180" in access["lowAccess"] and "1.0" in access["lowAccess"], access["lowAccess"]
        assert "bloqueadas" in access["lowGeneral"], access["lowGeneral"]
        assert access["lowHeroicRows"] == 0, "con iLvl bajo no deben verse objetos exclusivos de heroica"
        assert access["lowRecH"] == 0, "las recomendaciones deben evitar heroicas si no puedes entrar"
        assert access["highHeroicRows"] > 0, "con iLvl alto deben volver a verse las heroicas"
        assert access["highRecH"] > 0, "con iLvl alto las heroicas deben volver a las recomendaciones"
        assert "desbloqueada" in access["highAccess"], access["highAccess"]
        assert "desbloqueadas" in access["highGeneral"], access["highGeneral"]

        assert not errors, errors
        print("smoke ok:", page.locator(".slot").count(), "slots")
        browser.close()


if __name__ == "__main__":
    main()
