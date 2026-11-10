"""Audita si los pesos de cada especialidad respetan el orden de prioridad escrito en las guías
(data/reference_stats.json, campo stat_priority). Un peso inconsistente es el que, estando una estadística antes que
otra en la guía, vale menos. Los empates «(o)» no cuentan como violación.

Uso: python scripts/audit_weights.py"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEAR = json.loads((ROOT / "data" / "gear_data.json").read_text(encoding="utf-8"))
PHRASES = [
    ("spell power", "sp"), ("attack power", "ap"), ("armor penetration", "arp"), ("critical strike", "crit"),
    ("crit", "crit"), ("haste", "haste"), ("expertise", "exp"), ("hit", "hit"), ("strength", "str"), ("agility", "agi"),
    ("intellect", "int"), ("spirit", "spi"), ("mp5", "mp5"), ("stamina", "sta"), ("defense", "def"), ("dodge", "dodge"),
    ("parry", "parry"), ("armor", "armor"),
]


def stat_key(text):
    low = text.lower()
    for phrase, key in PHRASES:
        if low.strip().startswith(phrase) or re.match(r"^(ranged |melee |spell )?" + re.escape(phrase), low.strip()):
            return key
    return None


def ranks(priority):
    out, rank = {}, 0
    for entry in priority:
        keys = [k for k in (stat_key(p) for p in re.split(r"\s*\(o\)\s*", str(entry), flags=re.I)) if k]
        for k in keys:
            out.setdefault(k, rank)
        if keys:
            rank += 1
    return out


def weights_of(spec):
    sw = json.loads((ROOT / "data" / "spec_weights.json").read_text(encoding="utf-8"))
    role = GEAR["specs"][spec]["role"]
    w = dict(GEAR["engine"]["weights"].get(role, {}))
    w.update(sw.get(spec, {}).get("weights", {}))
    return w


def main():
    stats = json.loads((ROOT / "data" / "reference_stats.json").read_text(encoding="utf-8"))
    total = 0
    for spec in GEAR["specs"]:
        pr = stats.get(spec, {}).get("stat_priority") or []
        r, w = ranks(pr), weights_of(spec)
        bad = []
        for a, ra in r.items():
            for b, rb in r.items():
                if ra < rb and w.get(a, 0) < w.get(b, 0) - 1e-6:
                    bad.append(f"{a}({w.get(a, 0):.2f}) < {b}({w.get(b, 0):.2f})")
        total += len(bad)
        if bad:
            print(f"{spec:26} {len(bad)}: " + "; ".join(bad[:5]))
    print(f"\nTotal de inconsistencias: {total}")


if __name__ == "__main__":
    main()
