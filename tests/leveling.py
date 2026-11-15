"""Cobertura al subir de nivel (niveles 1-79): no deben faltar objetos cuando el juego los tiene.

Comprueba, para todas las especialidades y ambas facciones, que los slots principales no queden vacíos desde el primer
nivel en que existe algún objeto para ellos (cabeza y hombros desde el 15, cuello desde el 13, anillo desde el 5, segundo
anillo desde el 15), que los objetos con encantamiento aleatorio se estiman con sufijo, que no se recomienda equipo de
desarrollo/GM y que el recurso de reserva avisa en la tarjeta.
Uso: python tests/leveling.py   (requiere tolltip.html construido y Playwright)."""
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()
LEVELS = [1, 5, 9, 13, 14, 15, 16, 20, 24, 25, 30, 40, 50, 60, 70, 79]
FIRST = {"chest": 1, "hands": 1, "waist": 1, "legs": 1, "feet": 1, "wrist": 1, "back": 1, "mainhand": 1,
         "head": 15, "shoulder": 15, "neck": 13, "ring1": 5, "ring2": 15}

JS = """(a) => { const out = [];
  for (const k in DATA.specs) { const spec = DATA.specs[k];
    for (const lv of a.levels) { if (lv < spec.min) continue;
      for (const fac of ['horde', 'alliance']) {
        const g = computeGear(spec, { level: lv, faction: fac, scope: 'noraid', phase: 0, pvp: false, heirlooms: false });
        for (const s in a.first) if (g.slots[s] && lv >= Math.max(a.first[s], spec.min) && !g.slots[s].list.length) out.push(k + ' ' + lv + ' ' + fac + ' ' + s);
      } } }
  const g = computeGear(DATA.specs['Mage|Frost'], { level: 8, faction: 'horde', scope: 'noraid', phase: 0, pvp: false, heirlooms: false });
  const rnd = Object.values(g.slots).map((s) => s.list[0]).filter((e) => e && e.it.est);
  const junk = Object.values(GEAR_ITEMS).filter((i) => !i.x && /gamemaster|crobinson|action figure|do not use|engineer.s shield \\d/i.test(i.n)).map((i) => i.n);
  return { empty: out, rnd: rnd.map((e) => [e.it.n, Object.keys(e.it.px || {}).length, e.it.est]), junk };
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1000})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL, wait_until="load")
        r = page.evaluate(JS, {"levels": LEVELS, "first": FIRST})
        assert not r["empty"], f"{len(r['empty'])} slots vacíos al subir de nivel, p. ej.: " + "; ".join(r["empty"][:6])
        assert r["rnd"], "no se recomienda ningún objeto con encantamiento aleatorio a nivel 8 (Mage Frost)"
        assert all(re.search(r" of the \w+$", n) and k == 2 and est for n, k, est in r["rnd"]), r["rnd"]
        assert not r["junk"], "objetos de desarrollo/GM en el ranking: " + str(r["junk"][:5])
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")
        page.get_by_role("button", name="Warrior", exact=True).click()
        page.get_by_role("button", name="Arms", exact=True).click()
        page.locator("#levelInput").fill("22")
        page.locator("#levelInput").dispatch_event("change")
        page.wait_for_timeout(500)
        warns = page.locator("#slots .warn").all_inner_texts()
        assert any("mejor opción disponible" in w for w in warns), warns
        assert not errors, errors
        print(f"leveling ok: {len(LEVELS)} niveles x 31 especialidades x 2 facciones sin huecos, "
              f"{len(r['rnd'])} objetos aleatorios estimados")
        browser.close()


if __name__ == "__main__":
    main()
