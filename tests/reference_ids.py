"""Valida tests/reference_bis_ids.json contra data/gear_data.json.

Cada entrada debe existir, tener el mismo nombre y pertenecer a una ranura compatible.
Uso: python tests/reference_ids.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEAR = json.loads((ROOT / "data" / "gear_data.json").read_text(encoding="utf-8"))
ITEMS = GEAR["items"]
REFS = json.loads((ROOT / "tests" / "reference_bis_ids.json").read_text(encoding="utf-8"))


def norm(name):
    return re.sub(r"\s+", " ", str(name or "").replace("\u2019", "'")).strip().lower()


def compatible(ref_slot, item_slot):
    if ref_slot == "ranged":
        return item_slot in ("ranged", "thrown", "relic")
    if ref_slot == "relic":
        return item_slot == "relic"
    if ref_slot == "mainhand":
        return item_slot in ("mainhand", "onehand", "twohand")
    if ref_slot == "offhand":
        return item_slot in ("offhand", "held", "onehand", "twohand")
    return item_slot == ref_slot


def main():
    bad = []
    entries = 0
    for spec, ref in REFS.items():
        for slot, values in ref["slots"].items():
            for value in values:
                entries += 1
                item = ITEMS.get(str(value["id"]))
                if not item:
                    bad.append(f"{spec} {slot}: falta {value['name']} ({value['id']})")
                elif norm(item.get("n")) != norm(value["name"]):
                    bad.append(f"{spec} {slot}: {value['id']} es {item.get('n')}, no {value['name']}")
                elif not compatible(slot, item.get("s")):
                    bad.append(f"{spec} {slot}: {value['name']} es {item.get('s')}")
    # La referencia debe ser coherente con el tipo de armas de la especialidad (p. ej. sin offhand con dos manos)
    for spec, ref in REFS.items():
        d = GEAR["specs"][spec]
        if not d["off"] and ref["slots"].get("offhand"):
            bad.append(f"{spec}: tiene mano secundaria pero la especialidad no la usa (modo {d['mode']})")
    assert REFS and entries, "reference_bis_ids.json vacío"
    assert not bad, "\n".join(bad[:20])
    print(f"reference ids ok: {len(REFS)} specs, {entries} entradas")


if __name__ == "__main__":
    main()
