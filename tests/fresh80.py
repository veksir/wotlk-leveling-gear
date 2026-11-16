"""Modo «Recién 80»: equipo accesible sin Frost, T10, PvP ni fichas de raid.

Comprueba que las 31 especialidades, en ambas facciones, llenan todos los slots con equipo accesible, que el panel de
ruta aparece y persiste, y que el filtro se desactiva al cambiar de nivel o al entrar en PvP/«Con bandas».
Uso: python tests/fresh80.py   (requiere tolltip.html construido y Playwright)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()

COVERAGE = """() => {
  const bad = [], empty = [], cats = {};
  for (const k in DATA.specs) {
    const spec = DATA.specs[k];
    for (const fac of ['horde', 'alliance']) {
      const g = computeGear(spec, { level: 80, faction: fac, scope: 'noraid', phase: 0, pvp: false, fresh: true, heirlooms: false });
      for (const s in g.slots) {
        const e = g.slots[s].list[0];
        if (!e) { empty.push(k + ' ' + fac + ' ' + s); continue; }
        const src = e.it.src || {};
        cats[src.cur || src.t || '?'] = (cats[src.cur || src.t || '?'] || 0) + 1;
        if (e.it.raid || e.it.pvp || src.rq || src.cur === 'frost' || src.cur === 'frost-token' || src.t === 'RaidProb')
          bad.push([k, fac, s, e.it.n, e.it.ilvl, src.t, src.cur || '', !!e.it.raid, !!e.it.pvp, !!src.rq]);
      }
    }
  }
  const rep = Object.values(GEAR_ITEMS).find((i) => !i.x && i.src && i.src.cur === 'reputation' && i.src.cost);
  const frost = Object.values(GEAR_ITEMS).find((i) => !i.x && i.src && i.src.cur === 'frost');
  const token = Object.values(GEAR_ITEMS).find((i) => !i.x && i.src && i.src.cur === 'frost-token');
  const raid = Object.values(GEAR_ITEMS).find((i) => !i.x && i.raid && i.src && i.src.t !== 'RaidProb');
  const pvp = Object.values(GEAR_ITEMS).find((i) => !i.x && i.pvp);
  const rq = Object.values(GEAR_ITEMS).find((i) => !i.x && i.src && i.src.rq);
  const prob = Object.values(GEAR_ITEMS).find((i) => !i.x && i.src && i.src.t === 'RaidProb');
  return {
    bad, empty, cats,
    checks: {
      rep: !!(rep && freshAccessible(rep)),
      frost: !!(frost && freshAccessible(frost)),
      token: !!(token && freshAccessible(token)),
      raid: !!(raid && freshAccessible(raid)),
      pvp: !!(pvp && freshAccessible(pvp)),
      rq: !!(rq && freshAccessible(rq)),
      prob: !!(prob && freshAccessible(prob))
    }
  };
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1000})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL, wait_until="load")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")
        page.wait_for_timeout(300)

        r = page.evaluate(COVERAGE)
        assert not r["empty"], f"{len(r['empty'])} slots vacíos en Recién 80: " + "; ".join(r["empty"][:6])
        assert not r["bad"], "equipo no accesible en Recién 80: " + str(r["bad"][:6])
        assert r["checks"] == {"rep": True, "frost": False, "token": False, "raid": False, "pvp": False, "rq": False, "prob": False}, r["checks"]
        assert all(r["cats"].get(k, 0) for k in ("triumph", "conquest", "gold", "Quest", "Drop")), r["cats"]

        assert page.locator("#fresh80").is_disabled(), "Recién 80 debe estar desactivado por debajo de 80"
        page.get_by_role("button", name="Paladin", exact=True).click()
        page.get_by_role("button", name="Protection", exact=True).click()
        page.locator("#levelInput").fill("80")
        page.locator("#levelInput").dispatch_event("change")
        page.wait_for_timeout(500)
        assert not page.locator("#fresh80").is_disabled(), "Recién 80 debe activarse a nivel 80"

        page.locator("#fresh80").check()
        page.wait_for_timeout(900)
        assert page.locator("#fresh80").is_checked()
        assert page.locator("#freshRoute").is_visible(), "el panel de ruta debe mostrarse"
        assert page.locator("#freshRoute ol li").count() == 5
        assert "sin Frost" in page.locator("#sheetIntro").inner_text()
        assert "Triunfo" in page.locator("#sourcesValue").inner_text()

        srcs = page.locator("#slots .item-source").all_inner_texts()
        joined = "\n".join(srcs)
        assert "Emblema de Triunfo" in joined, srcs
        assert "Emblema de Conquista" in joined, srcs
        assert "1250 g" in joined, srcs
        assert "Escarcha" not in joined and "marca de raid" not in joined and "Banda" not in joined and "PvP" not in joined, srcs

        page.reload(wait_until="load")
        page.wait_for_timeout(600)
        assert page.locator("#fresh80").is_checked(), "Recién 80 debe persistir"
        assert page.locator("#freshRoute").is_visible()

        page.locator("#pvps .seg-btn", has_text="Solo PvP").click()
        page.wait_for_timeout(300)
        assert not page.locator("#fresh80").is_checked(), "PvP debe desactivar Recién 80"
        assert page.locator("#fresh80").is_disabled()
        assert page.locator("#freshRoute").is_hidden()

        page.locator("#pvps .seg-btn", has_text="PvE").click()
        page.locator("#modes .seg-btn", has_text="Con bandas").click()
        page.wait_for_timeout(300)
        assert not page.locator("#fresh80").is_checked()
        assert page.locator("#fresh80").is_disabled() is False

        page.locator("#levelInput").fill("79")
        page.locator("#levelInput").dispatch_event("change")
        page.wait_for_timeout(300)
        assert not page.locator("#fresh80").is_checked()
        assert page.locator("#fresh80").is_disabled()
        assert page.locator("#freshRoute").is_hidden()
        assert not errors, errors
        print(f"fresh80 ok: {len(r['cats'])} tipos de fuente, {sum(r['cats'].values())} slots cubiertos; "
              "sin Frost, T10, PvP ni fichas de raid")
        browser.close()


if __name__ == "__main__":
    main()
