"""Importa una lista BiS por fase (copiada de una guía) y la guarda en data/reference_bis_phases.json.

Formato del archivo de texto: una línea por slot, con los objetos separados por «;» en orden (el primero es el BiS):

    Cabeza: Sanctified Lightsworn Helmet; Valorous Redemption Faceguard
    Anillos: Ring of A; Ring of B; Ring of C
    Abalorios: Trinket A; Trinket B

Uso:
    python scripts/import_bis_list.py "Paladin|Protection" PR lista.txt
    fase: F80, PR, T7, T8, T9 o T10   (opciones: --out ruta.json, --allow-missing)

Los nombres se resuelven con data/gear_data.json (se elige el de mayor iLvl si hay varios). Después ejecuta
python scripts/build_page.py: la página usa esa lista como BiS de la fase (casilla «Usar la guía de referencia»)."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "gear_data.json"
OUT = ROOT / "data" / "reference_bis_phases.json"
PHASES = ["F80", "PR", "T7", "T8", "T9", "T10"]
SLOTS = {
    "head": "head", "cabeza": "head", "neck": "neck", "cuello": "neck", "shoulder": "shoulder", "shoulders": "shoulder", "hombros": "shoulder",
    "back": "back", "cloak": "back", "espalda": "back", "chest": "chest", "pecho": "chest", "wrist": "wrist", "wrists": "wrist", "bracers": "wrist",
    "muñecas": "wrist", "hands": "hands", "manos": "hands", "waist": "waist", "belt": "waist", "cintura": "waist", "legs": "legs", "piernas": "legs",
    "feet": "feet", "pies": "feet", "ring": "ring", "rings": "ring", "anillo": "ring", "anillos": "ring", "trinket": "trinket", "trinkets": "trinket",
    "abalorio": "trinket", "abalorios": "trinket", "mainhand": "mainhand", "main hand": "mainhand", "weapon": "mainhand", "mano principal": "mainhand",
    "offhand": "offhand", "off hand": "offhand", "shield": "offhand", "mano secundaria": "offhand", "ranged": "ranged", "relic": "ranged",
    "reliquia": "ranged", "a distancia": "ranged", "libram": "ranged", "idol": "ranged", "totem": "ranged", "sigil": "ranged", "wand": "ranged",
}


def norm(name):
    return " ".join(str(name).replace("\u2018", "'").replace("\u2019", "'").lower().split())


def parse_list(text):
    """Devuelve ({slot: [nombres]}, [líneas que no se entienden])."""
    out, bad = {}, []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        label, sep, rest = line.partition(":")
        slot = SLOTS.get(norm(label)) if sep else None
        if not slot:
            bad.append(line)
            continue
        names = [n.strip() for n in rest.split(";") if n.strip()]
        out.setdefault(slot, []).extend(names)
    return out, bad


def resolve(names_by_slot, items):
    index = {}
    for iid, it in items.items():
        k = norm(it["n"])
        if k not in index or it["ilvl"] > items[index[k]]["ilvl"]:
            index[k] = iid
    ids, missing = {}, []
    for slot, names in names_by_slot.items():
        for n in names:
            iid = index.get(norm(n))
            if iid:
                ids.setdefault(slot, [])
                if iid not in ids[slot]:
                    ids[slot].append(iid)
            else:
                missing.append(f"{slot}: {n}")
    return ids, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help='por ejemplo "Paladin|Protection"')
    ap.add_argument("phase", choices=PHASES)
    ap.add_argument("file", type=Path)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--allow-missing", action="store_true", help="guarda lo que se resuelva aunque falten nombres")
    a = ap.parse_args(argv)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if a.spec not in data["specs"]:
        sys.exit(f"Especialidad desconocida: {a.spec}")
    names, bad = parse_list(a.file.read_text(encoding="utf-8"))
    ids, missing = resolve(names, data["items"])
    for line in bad:
        print("No entiendo la línea:", line)
    for m in missing:
        print("No encontrado:", m)
    if (bad or missing) and not a.allow_missing:
        sys.exit("Corrige los nombres (o usa --allow-missing) y vuelve a ejecutar.")
    if not ids:
        sys.exit("No se resolvió ningún objeto.")
    store = json.loads(a.out.read_text(encoding="utf-8")) if a.out.exists() else {}
    store.setdefault(a.spec, {})[a.phase] = ids
    a.out.write_text(json.dumps(store, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{a.spec} {a.phase}: {sum(len(v) for v in ids.values())} objetos en {len(ids)} slots -> {a.out}")


if __name__ == "__main__":
    main()
