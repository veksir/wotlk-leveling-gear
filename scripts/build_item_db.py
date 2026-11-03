import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw_items.json"
ZONES_RAW = ROOT / "data" / "raw_zones.json"
OUT = ROOT / "data" / "items.json"

QUALITY = {"Uncommon": 2, "Rare": 3, "Epic": 4, "Heirloom": 7}
SLOT_MAP = {
    "Head": "head", "Neck": "neck", "Shoulder": "shoulder", "Back": "back",
    "Chest": "chest", "Wrist": "wrist", "Hands": "hands", "Waist": "waist",
    "Legs": "legs", "Feet": "feet", "Finger": "ring", "Trinket": "trinket",
    "Two-Hand": "twohand", "One-Hand": "onehand", "Main Hand": "mainhand",
    "Off Hand": "offhand", "Held In Off-hand": "held", "Ranged": "ranged",
    "Thrown": "thrown", "Relic": "relic",
}
ARMOR_SLOTS = {"head", "shoulder", "chest", "wrist", "hands", "waist", "legs", "feet", "back"}
STAT_NAMES = {
    "Strength": "str", "Agility": "agi", "Intellect": "int",
    "Stamina": "sta", "Spirit": "spi",
}

RATING_PATTERNS = [
    (r"critical strike", "crit"),
    (r"\bcrit\b", "crit"),
    (r"hit rating|\bhit\b", "hit"),
    (r"haste", "haste"),
    (r"expertise", "exp"),
    (r"defense", "def"),
    (r"dodge", "dodge"),
    (r"parry", "parry"),
    (r"shield block|block rating", "block"),
    (r"resilience", "res"),
    (r"armor penetration", "arp"),
    (r"mana per 5", "mp5"),
    (r"spell power|damage and healing done by magical spells", "sp"),
    (r"healing done", "heal"),
    (r"attack power", "ap"),
    (r"block value", "blockval"),
    (r"spell penetration", "spen"),
]


def infer_req(ilvl):
    if ilvl <= 65:
        return max(1, min(60, ilvl - 5))
    if ilvl <= 99:
        return 60
    if ilvl <= 160:
        return 70
    if ilvl <= 174:
        return 77
    if ilvl <= 190:
        return 78
    return 80


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_stats(tooltip):
    stats = {}
    armor = 0
    dps = 0.0
    speed = 0.0
    text_lines = [(t.get("label") or "") for t in tooltip]
    text = "\n".join(text_lines)

    for line in text_lines:
        m = re.match(r"^(\d+) Armor$", line)
        if m:
            armor = int(m.group(1))
            continue
        m = re.match(r"^\+(\d+) (Strength|Agility|Intellect|Stamina|Spirit)$", line)
        if m:
            stats[STAT_NAMES[m.group(2)]] = stats.get(STAT_NAMES[m.group(2)], 0) + int(m.group(1))
            continue
        m = re.match(r"^\+(\d+) (Strength|Agility|Intellect|Stamina|Spirit) ", line)
        if m:
            stats[STAT_NAMES[m.group(2)]] = stats.get(STAT_NAMES[m.group(2)], 0) + int(m.group(1))
            continue
        m = re.match(r"^Speed ([\d.]+)$", line)
        if m:
            speed = float(m.group(1))
            continue
        m = re.search(r"\(([\d.]+) damage per second\)", line)
        if m:
            dps = max(dps, float(m.group(1)))
            continue

        lower = line.lower()
        if "chance on hit" in lower:
            continue
        if not (lower.startswith("equip:") or lower.startswith("increases") or lower.startswith("improves") or lower.startswith("restores")):
            continue
        m = re.search(r"(?:by|up to|restores)\s+(\d+)", lower)
        if not m:
            continue
        value = int(m.group(1))
        if "attack power" in lower and ("cat, bear" in lower or "dire bear" in lower or "moonkin" in lower):
            stats["feralap"] = stats.get("feralap", 0) + value
            continue
        for pattern, key in RATING_PATTERNS:
            if re.search(pattern, lower):
                stats[key] = stats.get(key, 0) + value
                break
    return stats, armor, dps, speed


def parse_restrictions(tooltip):
    classes = None
    races = None
    for t in tooltip:
        label = (t.get("label") or "").strip()
        if label.startswith("Classes:"):
            classes = [x.strip() for x in label.split(":", 1)[1].split(",") if x.strip()]
        elif label.startswith("Races:"):
            races = [x.strip() for x in label.split(":", 1)[1].split(",") if x.strip()]
    return classes, races


def source_info(source, zones):
    if not source:
        return None, "unknown", False
    cat = source.get("category")
    if cat == "Quest":
        quests = source.get("quests") or []
        name = quests[0].get("name") if quests else "Misión"
        return {"t": "Quest", "n": name}, "quest", False
    if cat == "Vendor":
        return {"t": "Vendor", "n": source.get("name", "Vendedor")}, "vendor", False
    if cat in ("Boss Drop", "Zone Drop"):
        z = zones.get(source.get("zone"))
        zone_name = z["name"] if z else None
        zone_cat = z.get("category") if z else None
        if cat == "Boss Drop":
            return {"t": "Drop", "n": source.get("name"), "z": zone_name, "zc": zone_cat}, "drop", zone_cat == "Raid"
        return {"t": "Drop", "z": zone_name, "zc": zone_cat}, "drop", zone_cat == "Raid"
    if cat == "Rare Drop":
        return {"t": "Rare"}, "rare", False
    return {"t": cat or "Fuente"}, "other", False


def main():
    raw = load_json(RAW)
    zones_list = load_json(ZONES_RAW)
    zones = {z["id"]: z for z in zones_list}

    items = {}
    for it in raw:
        if it.get("class") not in ("Armor", "Weapon"):
            continue
        slot = SLOT_MAP.get(it.get("slot"))
        if not slot:
            continue
        quality = QUALITY.get(it.get("quality"))
        if quality not in (2, 3, 4):
            continue
        req = int(it.get("requiredLevel") or 0)
        ilvl = int(it.get("itemLevel") or 0)
        inferred = infer_req(ilvl)
        if it.get("quality") != "Heirloom" and (req == 0 or inferred - req > 15):
            req = inferred
        if req > 80 or ilvl > 284 or ilvl < 1:
            continue
        tooltip = it.get("tooltip") or []
        labels = " ".join((t.get("label") or "") for t in tooltip)
        if "Random enchantment" in labels:
            continue
        stats, armor, dps, speed = parse_stats(tooltip)
        if not stats and dps == 0 and not (slot == "offhand" and armor > 0):
            continue
        classes, races = parse_restrictions(tooltip)
        src, src_kind, is_raid = source_info(it.get("source"), zones)
        if src is None:
            src, src_kind = {"t": "Otra"}, "other"
        sub = it.get("subclass") or ""
        cls = it.get("class")
        armor_type = sub if cls == "Armor" and sub in ("Cloth", "Leather", "Mail", "Plate", "Shield") else None
        hands = 2 if slot == "twohand" else (1 if slot in ("onehand", "mainhand", "offhand") else 0)
        ranged = slot in ("ranged", "thrown")
        items[str(it["itemId"])] = {
            "n": it.get("name") or "",
            "i": it.get("icon") or "",
            "q": quality,
            "ilvl": ilvl,
            "req": req,
            "s": slot,
            "sub": sub,
            "at": armor_type,
            "st": stats,
            "ar": armor,
            "dps": round(dps, 1),
            "spd": speed,
            "src": src,
            "sk": src_kind,
            "raid": is_raid,
            "cl": classes,
            "ra": races,
            "h": hands,
            "rg": ranged,
        }

    print("items", len(items))
    from collections import Counter
    print("slots", Counter(v["s"] for v in items.values()))
    print("leveling", sum(1 for v in items.values() if v["src"] and not v["raid"] and v["sk"] != "unknown"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
