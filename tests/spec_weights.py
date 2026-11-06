"""Regresiones de los pesos por especialidad a nivel 80.

Uso: python tests/spec_weights.py   (requiere tolltip.html construido y Playwright).
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
        page.wait_for_timeout(600)

        assert page.evaluate("Object.keys(DATA.engine.specWeights).length") == 31
        missing = page.evaluate("""() => Object.keys(DATA.specs).filter((k) => !(k in DATA.engine.specWeights))""")
        assert missing == [], missing
        invalid = page.evaluate("""() => Object.entries(DATA.engine.specWeights).flatMap(([k, w]) =>
          Object.entries(w).filter(([, v]) => typeof v !== "number" || v < 0 || v > 2).map(([s]) => k + ":" + s))""")
        assert invalid == [], invalid

        # Los pesos de especialidad solo se aplican a nivel 80; por debajo manda el rol.
        levels = page.evaluate("""() => {
          const s = DATA.specs["Mage|Fire"];
          return { low: weightsFor(s, false, 79).crit, cap: weightsFor(s, false, 80).crit,
                   role: DATA.engine.weights.caster.crit, spec: DATA.engine.specWeights["Mage|Fire"].crit };
        }""")
        # Por debajo de 80 manda el peso del rol; a 80, el de la especialidad (el valor concreto se calibra con las guías).
        assert levels["low"] == levels["role"] and levels["cap"] == levels["spec"] and levels["cap"] != levels["low"], levels

        # Todas las especialidades producen un set completo a nivel 80 con bandas.
        incomplete = page.evaluate("""() => Object.entries(DATA.specs).filter(([k, spec]) => {
          const g = computeGear(spec, {level: 80, faction: "horde", scope: "raid", phase: 0, pvp: false});
          return Object.values(g.slots).filter((s) => s.list.length).length < 10;
        }).map(([k]) => k)""")
        assert incomplete == [], incomplete

        # Prioridades visibles: el tanque feral no recibe equipo de hechizos y Retribución usa 2H.
        checks = page.evaluate("""() => {
          const top = (key, slot, o) => {
            const g = computeGear(DATA.specs[key], Object.assign({level: 80, faction: "horde", scope: "raid", phase: 0, pvp: false}, o || {}));
            return g.slots[slot].list[0].it;
          };
          const bear = top("Druid|Feral Tank", "head"), ret = top("Paladin|Retribution", "mainhand");
          return { bear: bear.st, ret: ret.s };
        }""")
        assert "sta" in checks["bear"] and "agi" in checks["bear"], checks
        assert "sp" not in checks["bear"] and "int" not in checks["bear"], checks
        assert checks["ret"] == "twohand", checks

        assert not errors, errors
        print("spec weights ok: 31")
        browser.close()


if __name__ == "__main__":
    main()
