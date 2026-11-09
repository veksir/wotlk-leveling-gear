"""Modelo de gemas por color y meta-gemas (nivel 80).

Usa gemContext() y scoreParts() con datos sintéticos para comprobar las reglas del modelo,
más algunas comprobaciones con los datos reales.
Uso: python tests/gems.py   (requiere tolltip.html construido y Playwright)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()

JS = """() => {
  const val = (w) => (st) => Object.entries(st).reduce((a, [k, v]) => a + v * (w[k] || 0), 0);
  const spec = DATA.specs["Mage|Fire"];
  const ctx = (G, w) => gemContext(G, w, spec, val(w));
  const base = { red: [{ sp: 23 }], yellow: [{ sp: 20 }], blue: [{ sp: 5 }] };
  const wNoStats = { sp: 1, crit: 0.5 };                      // el Tear no aporta nada (sin pesos de str/agi/int/sta/spi)
  const wTear = { sp: 1, crit: 0.5, str: 1, agi: 1, int: 1, sta: 1, spi: 1 }; // el Tear vale 50
  const chaotic = (extra) => ({ ...base, meta: { st: { crit: 21 }, requires: { blue: 2 }, extraEp: extra } });
  const relentless = { ...base, meta: { st: { crit: 21 }, requires: { blue: 1 }, extraEp: 0 } };
  const item = DATA.items["50694"]; // rojo + azul + amarillo, bonus +9 poder de hechizos
  const gc = { red: 23, yellow: 20, blue: 12, any: 23, prismatic: 23, meta: 0 };
  const parts = (spWeight, g) => scoreParts(item, { sp: spWeight, gc: g || gc }).parts.map((p) => p.k);
  const holy = weightsFor(DATA.specs["Paladin|Holy"], false, 80);
  const low = weightsFor(DATA.specs["Paladin|Holy"], false, 79);
  const head = Object.values(DATA.items).find((i) => i.mt && i.s === "head" && i.ilvl >= 250);
  const notHead = scoreParts(DATA.items["50694"], { sp: 1, gc: { ...gc, meta: 50 } }).parts.some((p) => p.k === "meta");
  const headParts = (m) => scoreParts(head, { ...DATA.engine.weights.caster, gc: { ...gc, meta: m } }).parts.filter((p) => p.k === "meta").length;
  return {
    chaoticNoActivate: ctx(chaotic(0), wNoStats),          // 2 azules cuestan 36 y la meta solo aporta 10.5 -> no se activa
    chaoticActivate: ctx(chaotic(60), wNoStats),           // con el efecto extra (3% de daño crítico) sí compensa
    relentlessTear: ctx(relentless, wTear),                // con un Nightmare Tear se activa sin coste
    relentlessColors: ctx(relentless, wNoStats),           // sin valor para el Tear: se activa con 1 gema azul
    noBonus: parts(1), withBonus: parts(10),               // el bonus solo cuenta si compensa
    holyCtx: holy.gc && { meta: holy.gc.meta, plan: holy.gc.metaPlan }, lowGc: low.gc, lowGv: low.gv,
    notHead, headWith: headParts(40), headWithout: headParts(0), headFound: !!head,
  };
}"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL, wait_until="load")
        r = page.evaluate(JS)
        assert r["chaoticNoActivate"]["meta"] == 0, r["chaoticNoActivate"]
        assert r["chaoticActivate"]["meta"] > 0 and r["chaoticActivate"]["metaPlan"] == "colors", r["chaoticActivate"]
        assert r["relentlessTear"]["metaPlan"] == "tear" and r["relentlessTear"]["metaCost"] == 0, r["relentlessTear"]
        assert r["relentlessColors"]["metaPlan"] == "colors" and r["relentlessColors"]["metaCost"] == 18, r["relentlessColors"]
        assert "sbonus" not in r["noBonus"] and "sbonus" in r["withBonus"], (r["noBonus"], r["withBonus"])
        assert r["holyCtx"] and r["holyCtx"]["meta"] > 0, r["holyCtx"]
        assert r["lowGc"] is None and r["lowGv"] > 0, "por debajo de nivel 80 debe seguir el modelo anterior"
        assert r["headFound"] and r["headWith"] == 1 and r["headWithout"] == 0, r
        assert r["notHead"] is False, "la meta solo se cuenta en objetos con socket meta"
        assert not errors, errors
        print("gems ok: meta activation, socket bonus choice, nivel < 80 intacto")


if __name__ == "__main__":
    main()
