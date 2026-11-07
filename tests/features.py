"""Regresiones de gemas/sockets, bonus de set, reliquias curadas y procs sin probabilidad.

Uso: python tests/features.py   (requiere tolltip.html construido y Playwright).
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

        data = page.evaluate("""() => {
          const holy = ENG.setBonus["Paladin|Holy"];
          const rogue = ENG.setBonus["Rogue|Assassination"];
          const gems = ENG.gems["Paladin|Holy"];
          const w = weightsFor(DATA.specs["Paladin|Holy"], false, 80);
          const socketItem = DATA.items["50684"];
          const socketParts = scoreParts(socketItem, w).parts;
          const trophy = DATA.items["28830"], scale = DATA.items["54571"];
          return {holy, rogue, gems, gv: w.gv, socketItem, socketParts,
                  proc: trophy && trophy.px, scale: scale && {px: scale.px, ph: scale.ph, raid: scale.raid}};
        }""")
        assert data["holy"]["slots"] == ["head", "shoulder"], data["holy"]
        assert data["rogue"]["slots"] == ["head", "hands"], data["rogue"]
        assert not set(data["holy"]["ids"]) & {"50869", "50865", "50866"}, data["holy"]
        assert not set(data["rogue"]["ids"]) & {"50105", "50083", "50086"}, data["rogue"]
        assert data["gems"] and data["gv"] > 0, data
        assert data["socketItem"]["sc"] >= 1 and data["socketItem"]["sb"], data["socketItem"]
        assert any(p["k"] == "gems" and not p["fx"] for p in data["socketParts"]), data["socketParts"]
        assert any(p["k"] == "sbonus" and not p["fx"] for p in data["socketParts"]), data["socketParts"]
        assert data["proc"] == {"haste": 118}, data["proc"]
        assert data["scale"] and data["scale"]["px"] == {"dodge": 140} and data["scale"]["ph"] == 5, data["scale"]

        gear = page.evaluate("""() => {
          state.showHeirlooms = false;
          const holy = computeGear(DATA.specs["Paladin|Holy"], {level: 80, faction: "horde", scope: "raid", phase: 4, pvp: false});
          const dk = computeGear(DATA.specs["Death Knight|Blood Tank"], {level: 80, faction: "horde", scope: "raid", phase: 4, pvp: false});
          const relic = dk.slots.relic && dk.slots.relic.list[0];
          return {
            holyChestBonus: holy.pools.chest.some((e) => e.setBonus > 0),
            holyHeadBonus: holy.pools.head.some((e) => e.setBonus > 0),
            dkRelic: relic && {id: relic.id, name: relic.it.n, rank: relic.curRank},
            dkHeirloom: Object.values(dk.slots).flatMap((s) => s.list).some((e) => DATA.heirlooms[e.id]),
            holyTrinket: holy.slots.trinket1.list[0] && holy.slots.trinket1.list[0].id,
          };
        }""")
        assert not gear["holyChestBonus"], "el bonus de set no debe llegar a piezas off-set"
        assert gear["holyHeadBonus"], "el bonus de set debe llegar a las piezas recomendadas"
        assert gear["dkRelic"] and gear["dkRelic"]["id"] == "50462", gear["dkRelic"]
        assert gear["dkRelic"]["rank"] == 1, gear["dkRelic"]
        assert not gear["dkHeirloom"], "los heirlooms no deben aparecer sin el check"
        assert gear["holyTrinket"] == "46051", gear["holyTrinket"]

        assert not errors, errors
        print("features ok: gems, set bonus, curated relic, proc fallback")
        browser.close()


if __name__ == "__main__":
    main()
