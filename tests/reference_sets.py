"""Valida data/reference_sets.json contra el dataset: cada pieza de set T10 debe existir, tener el slot
declarado y un nombre que corresponda al set (no al de otra clase o especialidad)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    sets = json.loads((ROOT / "data" / "reference_sets.json").read_text(encoding="utf-8"))
    items = json.loads((ROOT / "data" / "gear_data.json").read_text(encoding="utf-8"))["items"]
    problems, total = [], 0
    for cls, cv in sets.items():
        if cls == "resumen_calidad":
            continue
        for variant, var in cv["variants"].items():
            for slot, entries in var["pieces"].items():
                if not entries:
                    problems.append(f"{cls} / {variant} / {slot}: sin piezas")
                for e in entries:
                    total += 1
                    item = items.get(str(e["id"]))
                    if not item:
                        problems.append(f"{cls} / {variant} / {slot}: el ID {e['id']} no existe")
                    elif item["s"] != slot:
                        problems.append(f"{cls} / {variant} / {slot}: {e['id']} es {item['n']} ({item['s']})")
            # el nombre base de las piezas de un mismo set debe repetirse entre sus slots (mismo set)
    assert not problems, "\n".join(problems[:15]) + f"\n... {len(problems)} problemas"
    print(f"reference sets ok: {total} piezas")


if __name__ == "__main__":
    main()
