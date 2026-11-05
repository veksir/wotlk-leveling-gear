"""Regresiones de reliquias, off-spec y arma a dos manos.

Uso: python tests/heirlooms.py   (requiere tolltip.html construido y Playwright).
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL, wait_until="load")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")
        page.wait_for_timeout(700)

        # Estadísticas exactas por nivel y cambio de tipo de armadura antes del 40.
        stats = page.evaluate("""() => {
          const at = (level) => levelItem(DATA.heirlooms["44099"], level);
          return { one: at(1), twenty: at(20), forty: at(40), eighty: at(80) };
        }""")
        assert stats["one"]["ar"] == 64 and stats["one"]["st"] == {"res": 1, "sta": 1, "str": 1}
        assert stats["twenty"]["at"] == "Mail"
        assert stats["forty"]["ar"] == 360
        assert stats["forty"]["st"] == {"res": 9, "sta": 14, "str": 9}
        assert stats["eighty"]["at"] == "Plate" and stats["eighty"]["ar"] == 1570

        # Por defecto no se recomiendan reliquias: requieren moneda de nivel 80.
        page.evaluate("""() => {
          state.cls = "Warrior"; state.spec = "Protection"; state.level = 20;
          state.gear = {}; state.showHeirlooms = false; render();
        }""")
        page.wait_for_timeout(300)
        assert not page.locator("#showHeirlooms").is_checked()
        excluded = page.evaluate("""() => {
          const g = computeGear(DATA.specs["Warrior|Protection"], {level: 20, faction: "horde", scope: "noraid", phase: 0, pvp: false});
          return Object.values(g.slots).flatMap((s) => s.list).some((x) => x.id === "44099");
        }""")
        assert not excluded, "la reliquia aparece sin marcar que ya se tiene"

        # Al marcar que ya las tienes, entran en las recomendaciones.
        page.locator("#showHeirlooms").check()
        page.wait_for_timeout(300)
        rec = page.evaluate("""() => {
          const g = computeGear(DATA.specs["Warrior|Protection"], {level: 20, faction: "horde", scope: "noraid", phase: 0, pvp: false});
          const e = g.slots.shoulder.list.find((x) => x.id === "44099");
          return e ? { score: e.score, name: e.it.n } : null;
        }""")
        assert rec and rec["score"] > 0, "la reliquia de hombros no se recomienda con el toggle"
        page.evaluate("""() => setEquipped("shoulder", "44099")""")
        page.wait_for_timeout(300)
        assert page.locator("#eq-shoulder").input_value() == "Strengthened Stockade Pauldrons"

        # Una reliquia 2H ocupa la mano principal y bloquea la secundaria.
        page.evaluate("""() => {
          state.cls = "Mage"; state.spec = "Frost"; state.level = 20;
          state.gear = {}; render();
        }""")
        page.wait_for_timeout(300)
        page.evaluate("""() => setEquipped("mainhand", "42947")""")
        page.wait_for_timeout(300)
        assert page.locator("#eq-offhand").is_disabled()
        assert page.locator("#eq-offhand").input_value() == ""
        twoh = page.evaluate("""() => {
          const g = computeGear(DATA.specs["Mage|Frost"], {level: 40, faction: "horde", scope: "noraid", phase: 0, pvp: false});
          return { s: g.slots.mainhand.list[0].it.s, oh: g.slots.offhand.list.length };
        }""")
        assert twoh["s"] == "twohand" and twoh["oh"] == 0, twoh

        # Relevancia: un paladín tanque no recibe equipo de heal, pero el toggle lo muestra.
        page.evaluate("""() => {
          state.cls = "Paladin"; state.spec = "Protection"; state.level = 25;
          state.gear = {}; state.dungeon = 206; state.showOffspec = false; render();
        }""")
        page.wait_for_timeout(400)
        bad = page.evaluate("""() => {
          const g = computeGear(DATA.specs["Paladin|Protection"], {level: 80, faction: "horde", scope: "raid", phase: 0, pvp: false});
          return Object.values(g.slots).flatMap((s) => s.list)
            .filter((e) => e.it.st && (e.it.st.spi || e.it.st.sp || e.it.st.int)).map((e) => e.it.n);
        }""")
        assert bad == [], bad
        hidden_count = page.locator(".loot-row").count()
        assert "fuera de especialidad" in page.locator("#lootCount").inner_text()
        page.locator("#showOffspec").check()
        page.wait_for_timeout(400)
        shown_count = page.locator(".loot-row").count()
        assert shown_count > hidden_count, (hidden_count, shown_count)
        assert page.locator(".loot-row.offspec").count() > 0

        assert not errors, errors
        print("heirlooms ok:", hidden_count, "->", shown_count)
        browser.close()


if __name__ == "__main__":
    main()
