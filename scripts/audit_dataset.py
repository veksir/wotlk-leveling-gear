"""Audita qué objetos del dataset crudo se descartan y por qué (para detectar pérdidas sistemáticas).

Uso: python scripts/audit_dataset.py
Repite los filtros de build_item_db.py, en el mismo orden, y cuenta el primer motivo de descarte."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_item_db as b  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    raw = json.loads((ROOT / "data" / "raw_items.json").read_text(encoding="utf-8"))
    kept = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
    reasons = Counter()
    samples = defaultdict(list)
    levels = defaultdict(Counter)

    def drop(reason, it, extra=""):
        reasons[reason] += 1
        if len(samples[reason]) < 8:
            samples[reason].append(f"{it['name']} (iLvl {it.get('itemLevel')}{extra})")
        levels[reason][min(80, int(it.get("requiredLevel") or 0)) // 10 * 10] += 1

    considered = 0
    for it in raw:
        if it.get("class") not in ("Armor", "Weapon"):
            continue
        slot = b.SLOT_MAP.get(it.get("slot"))
        if not slot:
            drop("slot no soportado (camisa, tabardo...)", it, f", {it.get('slot')}")
            continue
        quality = b.QUALITY.get(it.get("quality"))
        if quality not in (2, 3, 4, 5):
            drop("calidad gris/blanca/heirloom", it)
            continue
        ilvl = int(it.get("itemLevel") or 0)
        req = int(it.get("requiredLevel") or 0)
        if req > 80 or ilvl > 284 or ilvl < 1:
            drop("fuera de rango (req>80, iLvl>284)", it)
            continue
        considered += 1
        if b.JUNK_RE.search(it.get("name") or ""):
            drop("nombre basura (test/old)", it)
            continue
        labels = " ".join((t.get("label") or "") for t in it.get("tooltip") or [])
        if "Random enchantment" in labels:
            drop("encantamiento aleatorio (…of the Bear/Monkey)", it)
            continue
        stats, armor, dps, _ = b.parse_stats(it.get("tooltip") or [])
        if not stats and not b.parse_effects(it.get("tooltip") or []) and dps == 0 and not (slot == "offhand" and armor > 0):
            drop("sin estadísticas reconocidas", it)
            continue
        if str(it["itemId"]) not in kept:
            drop("OTRO (revisar)", it)

    print(f"Armadura/armas con calidad y nivel válidos: {considered}   incluidos en el dataset: {len(kept)}\n")
    for reason, n in reasons.most_common():
        spread = ", ".join(f"{k}-{k + 9}: {v}" for k, v in sorted(levels[reason].items()))
        print(f"{n:6d}  {reason}\n        niveles req -> {spread}\n        ej.: {'; '.join(samples[reason][:5])}\n")


if __name__ == "__main__":
    main()
