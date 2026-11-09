"""Compara el ranking de la herramienta con listas BiS de referencia (tests/reference_bis_ids.json).

Por especialidad, en modo «Con bandas», fase de la referencia (4), nivel 80:
  - slot acertado: la primera opción de la herramienta está en la lista de la guía (BiS o alternativas).
    Para anillos y abalorios (2 slots) cuenta cuántas de las 2 primeras opciones están en la lista.
  - exacto: la primera opción coincide con el BiS que pone la guía en primer lugar.
Falla si algún objeto de la guía no existe en el dataset (error de datos).
Uso: python tests/check_reference.py [--ref=reference_bis_ids.json] [--verbose] [--min=N] [--strict] [Clase|Especialidad ...]
  --min=N   falla si los aciertos bajan de N (guardarraíl contra regresiones)
  --strict  falla si cualquier slot de la referencia no acierta"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
JS = """(ref) => {
  const spec = DATA.specs[ref.spec];
  const g = computeGear(spec, { level: ref.level, faction: ref.faction, scope: 'raid', phase: ref.phase || 0, pvp: false, heirlooms: false });
  const norm = (n) => String(n).replace(/\\u2019/g, "'").toLowerCase();
  const key = (w) => (typeof w === 'object' ? 'id:' + w.id : norm(w));
  const db = new Set(Object.values(DATA.items).map((i) => norm(i.n)).concat(Object.keys(DATA.items).map((i) => 'id:' + i)));
  const out = [];
  for (const slot in ref.slots) {
    const want = ref.slots[slot];
    const pairs = slot === 'ring' || slot === 'trinket';
    // Para las clases con reliquia, la referencia la lista bajo «ranged»; la herramienta la pone en «relic».
    const real = slot === 'ranged' && !g.slots.ranged && g.slots.relic ? 'relic' : slot;
    const sl = pairs ? [slot + '1', slot + '2'] : [real];
    const topE = sl.map((s) => (g.slots[s] && g.slots[s].list[0]) || null);
    const tops = topE.map((e) => (e ? e.it.n : null));
    const same = (e, w) => e && (typeof w === 'object' ? String(e.id) === String(w.id) : norm(e.it.n) === norm(w));
    const hits = topE.filter((e) => e && want.slice(0, pairs ? 3 : 4).some((w) => same(e, w))).length;
    out.push({ slot, want: want.map((w) => (typeof w === 'object' ? w.name : w)), tops, units: sl.length, hits,
               exact: pairs ? topE.filter((e) => e && want.slice(0, 2).some((w) => same(e, w))).length : (topE[0] && same(topE[0], want[0]) ? 1 : 0),
               missing: want.filter((w) => !db.has(key(w))).map((w) => (typeof w === 'object' ? w.name : w)) });
  }
  return out;
}"""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--verbose" in sys.argv
    ref_file = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--ref=")), "reference_bis_ids.json")
    refs = json.loads((ROOT / "tests" / ref_file).read_text(encoding="utf-8"))
    bad_data = 0
    tot_u = tot_h = tot_e = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto((ROOT / "tolltip.html").as_uri(), wait_until="load")
        for spec, ref in refs.items():
            if args and spec not in args:
                continue
            rows = page.evaluate(JS, {"spec": spec, "level": ref["level"], "faction": ref["faction"], "phase": ref.get("phase", 0), "slots": ref["slots"]})
            u = sum(r["units"] for r in rows)
            h = sum(r["hits"] for r in rows)
            e = sum(r["exact"] for r in rows)
            tot_u, tot_h, tot_e = tot_u + u, tot_h + h, tot_e + e
            miss = [(r["slot"], n) for r in rows for n in r["missing"]]
            bad_data += len(miss)
            print(f"{spec:26} acierta {h:2}/{u:2} ({h * 100 // u:3}%)  exacto {e:2}/{u:2}" + (f"  FALTA EN DATASET: {miss}" if miss else ""))
            if verbose:
                for r in rows:
                    if r["hits"] < r["units"]:
                        print(f"     {r['slot']:9} guía: {r['want'][:2]}  herramienta: {r['tops']}")
        browser.close()
    print(f"\nTOTAL acierta {tot_h}/{tot_u} ({tot_h * 100 // max(tot_u, 1)}%), exacto {tot_e}/{tot_u}")
    minimum = next((int(x.split("=", 1)[1]) for x in sys.argv[1:] if x.startswith("--min=")), None)
    failed = bad_data > 0
    if "--strict" in sys.argv and tot_h < tot_u:
        print(f"STRICT: faltan {tot_u - tot_h} slots sin acierto")
        failed = True
    if minimum is not None and tot_h < minimum:
        print(f"REGRESIÓN: {tot_h} aciertos, el mínimo exigido es {minimum}")
        failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
