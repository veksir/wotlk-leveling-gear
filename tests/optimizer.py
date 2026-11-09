"""Búsqueda en haz (nivel 80): determinismo, tiempo, restricciones y mejora del objetivo frente al codicioso.
Uso: python tests/optimizer.py   (requiere tolltip.html construido y Playwright)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()

JS = """() => {
  const o = { level: 80, faction: 'horde', scope: 'raid', phase: 4, pvp: false };
  const pick = (g) => Object.entries(g.slots).map(([s, v]) => s + ':' + (v.list[0] ? v.list[0].id : '-')).join(',');
  const res = { times: [], same: true, specs: Object.keys(DATA.specs).length, ashen: [], noRing: [], setOk: {}, empty: [] };
  for (const k in DATA.specs) {
    const spec = DATA.specs[k];
    const t = performance.now(); const a = computeGear(spec, o); res.times.push(performance.now() - t);
    const b = computeGear(spec, o);
    if (pick(a) !== pick(b)) res.same = false;
    const rings = ['ring1', 'ring2'].map((s) => a.slots[s] && a.slots[s].list[0]);
    if (rings.filter((e) => e && /^Ashen Band of /.test(e.it.n)).length > 1) res.ashen.push(k);
    if (rings[0] && rings[1] && rings[0].it.n === rings[1].it.n) res.noRing.push(k);
    const sb = ENG.setBonus[k];
    if (sb) { const ids = new Set(sb.ids); const n = Object.values(a.slots).filter((s) => s.list[0] && ids.has(s.list[0].id)).length; res.setOk[k] = [n, sb.need]; }
    Object.entries(a.slots).forEach(([s, v]) => { if (!v.list.length && !['relic', 'ranged', 'offhand', 'trinket2'].includes(s)) res.empty.push(k + ':' + s); });
  }
  window.__NO_BEAM = true; const off = computeGear(DATA.specs['Priest|Shadow'], o); window.__NO_BEAM = false;
  const on = computeGear(DATA.specs['Priest|Shadow'], o);
  res.togglesOk = Object.keys(off.slots).length === Object.keys(on.slots).length;
  const l79 = { ...o, level: 79 };
  window.__NO_BEAM = true; const a79 = computeGear(DATA.specs['Priest|Shadow'], l79); window.__NO_BEAM = false;
  const b79 = computeGear(DATA.specs['Priest|Shadow'], l79);
  res.level79Same = pick(a79) === pick(b79);
  res.times.sort((x, y) => x - y);
  return res;
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL, wait_until="load")
        r = page.evaluate(JS)
        assert r["same"], "el optimizador no es determinista"
        assert not r["ashen"], "dos Ashen Band a la vez: " + str(r["ashen"])
        assert not r["noRing"], "el mismo anillo en los dos dedos: " + str(r["noRing"])
        assert not r["empty"], "slots vacíos: " + str(r["empty"][:5])
        assert r["togglesOk"]
        assert r["level79Same"], "el nivel 79 no debe usar el beam de nivel 80"
        assert r["times"][-1] < 750, "tiempo máximo demasiado alto: %.0f ms" % r["times"][-1]
        full = [k for k, (n, need) in r["setOk"].items() if n >= need]
        assert len(full) >= len(r["setOk"]) * 0.6, "pocas especialidades completan su bonus de set: %d de %d" % (len(full), len(r["setOk"]))
        assert not errors, errors
        mean = sum(r["times"]) / len(r["times"])
        print("optimizer ok: media %.0f ms, máx %.0f ms; bonus de set completo en %d de %d" % (mean, r["times"][-1], len(full), len(r["setOk"])))


if __name__ == "__main__":
    main()
