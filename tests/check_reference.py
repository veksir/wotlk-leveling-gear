"""Compara el ranking de la herramienta con listas BiS de referencia (tests/reference_bis.json).

Para cada pieza esperada informa: si existe en el dataset, en qué puesto queda (modo «Con bandas»,
todas las fases) y cuál es la primera opción de la herramienta. Falla si falta algún objeto en el
dataset (eso es un error de datos); el puesto es solo informativo (puede ser el motor).
Uso: python tests/check_reference.py   (requiere tolltip.html construido y Playwright)."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
JS = """(ref) => {
  const spec = DATA.specs[ref.spec];
  const g = computeGear(spec, { level: ref.level, faction: ref.faction, scope: 'raid', phase: 0, pvp: false });
  const out = [];
  for (const slot in ref.slots) {
    const pool = g.pools[slot] || [];
    for (const name of ref.slots[slot]) {
      const found = Object.values(DATA.items).filter((i) => i.n === name);
      const idx = pool.findIndex((e) => e.it.n === name);
      out.push({ slot, name, inDb: found.length, rank: idx < 0 ? null : idx + 1, top: pool[0] ? pool[0].it.n : null });
    }
  }
  return out;
}"""


def main():
    refs = json.loads((ROOT / "tests" / "reference_bis.json").read_text(encoding="utf-8"))
    missing = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto((ROOT / "tolltip.html").as_uri(), wait_until="load")
        for spec, ref in refs.items():
            rows = page.evaluate(JS, {"spec": spec, "level": ref["level"], "faction": ref["faction"], "slots": ref["slots"]})
            ok_top = sum(1 for r in rows if r["rank"] == 1)
            print(f"\n{spec}  ({ref['source']})")
            for r in rows:
                flag = "FALTA EN DATASET" if not r["inDb"] else ("#1" if r["rank"] == 1 else f"puesto {r['rank']}")
                print(f"  {r['slot']:9} {r['name'][:38]:40} {flag:18} top: {r['top']}")
                missing += 0 if r["inDb"] else 1
            print(f"  -> {ok_top}/{len(rows)} piezas de la guía son la primera opción")
        browser.close()
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
