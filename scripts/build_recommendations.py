import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
ITEMS_PATH = ROOT / "data" / "items.json"
OUT = ROOT / "data" / "gear_data.json"
sys.path.insert(0, str(ROOT / "legacy"))
from data_leveling import payload as legacy  # noqa: E402

ARMOR_KEYS = ["head", "shoulder", "chest", "wrist", "hands", "waist", "legs", "feet", "back"]
SLOT_ORDER = [
    "head", "neck", "shoulder", "back", "chest", "wrist", "hands", "waist",
    "legs", "feet", "ring1", "ring2", "trinket1", "trinket2", "mainhand",
    "offhand", "ranged", "relic",
]
FACTIONS = ("horde", "alliance")

ALL_MELEE = ["Axe", "Sword", "Mace", "Dagger", "Fist Weapon", "Polearm", "Staff"]

WEAPON_HANDS = {
    "Death Knight": {"Axe": {1, 2}, "Sword": {1, 2}, "Mace": {1, 2}, "Polearm": {2}},
    "Druid": {"Mace": {1, 2}, "Staff": {2}, "Polearm": {2}, "Dagger": {1}, "Fist Weapon": {1}},
    "Hunter": {"Axe": {1, 2}, "Sword": {1, 2}, "Dagger": {1}, "Fist Weapon": {1}, "Polearm": {2}, "Staff": {2}},
    "Mage": {"Sword": {1}, "Dagger": {1}, "Staff": {2}},
    "Paladin": {"Mace": {1, 2}, "Sword": {1, 2}, "Polearm": {2}},
    "Priest": {"Mace": {1}, "Dagger": {1}, "Staff": {2}},
    "Rogue": {"Dagger": {1}, "Sword": {1}, "Mace": {1}, "Fist Weapon": {1}},
    "Shaman": {"Mace": {1, 2}, "Axe": {1}, "Dagger": {1}, "Staff": {2}, "Fist Weapon": {1}},
    "Warlock": {"Sword": {1}, "Dagger": {1}, "Staff": {2}},
    "Warrior": {"Axe": {1, 2}, "Sword": {1, 2}, "Mace": {1, 2}, "Dagger": {1}, "Fist Weapon": {1}, "Polearm": {2}, "Staff": {2}},
}

CLASS_WEAPONS = {
    "Death Knight": ["Axe", "Sword", "Mace", "Polearm"],
    "Druid": ["Mace", "Staff", "Polearm", "Dagger", "Fist Weapon"],
    "Hunter": ["Axe", "Sword", "Dagger", "Fist Weapon", "Polearm", "Staff"],
    "Mage": ["Sword", "Dagger", "Staff"],
    "Paladin": ["Mace", "Sword", "Polearm"],
    "Priest": ["Mace", "Dagger", "Staff"],
    "Rogue": ["Dagger", "Sword", "Mace", "Fist Weapon"],
    "Shaman": ["Mace", "Axe", "Dagger", "Staff", "Fist Weapon"],
    "Warlock": ["Sword", "Dagger", "Staff"],
    "Warrior": ALL_MELEE,
}

SPECS = [
    ("Death Knight", "Blood Tank", "tank", "str", "2h", None, None, "Sigil"),
    ("Death Knight", "Frost DPS", "str", "str", "2h", None, None, "Sigil"),
    ("Death Knight", "Unholy DPS", "str", "str", "2h", None, None, "Sigil"),
    ("Druid", "Balance", "caster", "int", "any", "held", None, "Idol"),
    ("Druid", "Feral DPS", "agi", "agi", "2h", None, None, "Idol"),
    ("Druid", "Feral Tank", "bear", "agi", "2h", None, None, "Idol"),
    ("Druid", "Restoration", "healer", "int", "any", "held", None, "Idol"),
    ("Hunter", "Beast Mastery", "hunter", "agi", "any", None, "ranged", None),
    ("Hunter", "Marksmanship", "hunter", "agi", "any", None, "ranged", None),
    ("Hunter", "Survival", "hunter", "agi", "any", None, "ranged", None),
    ("Mage", "Arcane", "caster", "int", "any", "held", "wand", None),
    ("Mage", "Fire", "caster", "int", "any", "held", "wand", None),
    ("Mage", "Frost", "caster", "int", "any", "held", "wand", None),
    ("Paladin", "Holy", "healer", "int", "1h", "shield", None, "Libram"),
    ("Paladin", "Protection", "tank", "str", "1h", "shield", None, "Libram"),
    ("Paladin", "Retribution", "str", "str", "2h", None, None, "Libram"),
    ("Priest", "Discipline", "healer", "int", "any", "held", "wand", None),
    ("Priest", "Holy", "healer", "int", "any", "held", "wand", None),
    ("Priest", "Shadow", "caster", "int", "any", "held", "wand", None),
    ("Rogue", "Assassination", "agi", "agi", "1h", "dw", "thrown", None),
    ("Rogue", "Combat", "agi", "agi", "1h", "dw", "thrown", None),
    ("Rogue", "Subtlety", "agi", "agi", "1h", "dw", "thrown", None),
    ("Shaman", "Elemental", "caster", "int", "any", "shield", None, "Totem"),
    ("Shaman", "Enhancement", "agi", "agi", "1h", "dw", None, "Totem"),
    ("Shaman", "Restoration", "healer", "int", "any", "shield", None, "Totem"),
    ("Warlock", "Affliction", "caster", "int", "any", "held", "wand", None),
    ("Warlock", "Demonology", "caster", "int", "any", "held", "wand", None),
    ("Warlock", "Destruction", "caster", "int", "any", "held", "wand", None),
    ("Warrior", "Arms", "str", "str", "2h", None, "thrown", None),
    ("Warrior", "Fury", "str", "str", "1h", "dw", "thrown", None),
    ("Warrior", "Protection", "tank", "str", "1h", "shield", "thrown", None),
]

ARMOR_TIERS = {
    "Mage": ["Cloth"], "Priest": ["Cloth"], "Warlock": ["Cloth"],
    "Druid": ["Leather", "Cloth"], "Rogue": ["Leather", "Cloth"],
    "Hunter": ["Mail", "Leather", "Cloth"], "Shaman": ["Mail", "Leather", "Cloth"],
    "Warrior": ["Plate", "Mail", "Leather", "Cloth"],
    "Paladin": ["Plate", "Mail", "Leather", "Cloth"],
    "Death Knight": ["Plate", "Mail", "Leather", "Cloth"],
}

CLASS_META_EN = {
    "Death Knight": {"armor": "Plate", "weapons": "Swords, axes, maces, and polearms"},
    "Druid": {"armor": "Leather", "weapons": "Staves, two-handed maces, polearms, and daggers"},
    "Hunter": {"armor": "Mail at 40", "weapons": "Swords, axes, polearms, staves, bows, and guns"},
    "Mage": {"armor": "Cloth", "weapons": "Staves, swords, daggers, and wands"},
    "Paladin": {"armor": "Plate at 40", "weapons": "Swords, maces, polearms, and shields"},
    "Priest": {"armor": "Cloth", "weapons": "Staves, one-handed maces, daggers, and wands"},
    "Rogue": {"armor": "Leather", "weapons": "Daggers, swords, one-handed maces, and fist weapons"},
    "Shaman": {"armor": "Mail at 40", "weapons": "Maces, one-handed axes, staves, daggers, and shields"},
    "Warlock": {"armor": "Cloth", "weapons": "Staves, swords, daggers, and wands"},
    "Warrior": {"armor": "Plate at 40", "weapons": "All melee weapons, bows, guns, thrown, and shields"},
}

BRACKET_EN = {
    1: ("Learning", "Don't spend gold on gear: quests give more than enough. Keep pieces with your spec's primary stat."),
    20: ("First dungeons", "Dungeons start here. Run each one once for the rewards and keep leveling; don't farm gear you will replace in a few levels."),
    40: ("Specialization", "Higher armor unlocks: mail for hunters and shamans, plate for warriors and paladins. Refresh pieces every 5 or 8 levels."),
    60: ("Outland", "Level 60+ quest gear beats almost everything before it. Take the blue dungeon pieces you find and don't stop to farm."),
    70: ("Northrend", "Level 70+ quest gear is the baseline. Northrend dungeons fill the gaps so you can reach 80 without suffering."),
    80: ("Max level", "You no longer need leveling gear. From here, pick the level 80 BiS for your spec and content phase."),
}

def weights_for(role):
    w = defaultdict(float)
    if role in ("str", "agi"):
        key = role
        w.update({key: 1.0, "sta": 0.10, "ap": 0.50, "feralap": 0.50 if key == "agi" else 0.0,
                  "hit": 0.70, "crit": 0.55, "haste": 0.40, "exp": 0.65, "arp": 0.50,
                  "armor": 0.004, "dps": 5.0})
    elif role == "caster":
        w.update({"int": 1.0, "sta": 0.08, "sp": 0.80, "hit": 0.70, "crit": 0.50,
                  "haste": 0.50, "spi": 0.15, "armor": 0.001})
    elif role == "healer":
        w.update({"int": 1.0, "sta": 0.08, "sp": 0.70, "heal": 0.50, "mp5": 0.50,
                  "spi": 0.40, "crit": 0.30, "haste": 0.40, "armor": 0.001})
    elif role == "tank":
        w.update({"sta": 1.0, "str": 0.30, "agi": 0.20, "armor": 0.020, "def": 0.80,
                  "dodge": 0.70, "parry": 0.70, "block": 0.50, "blockval": 0.005,
                  "hit": 0.35, "exp": 0.35, "ap": 0.10, "dps": 1.5})
    elif role == "bear":
        w.update({"sta": 1.0, "agi": 0.80, "armor": 0.020, "dodge": 0.60,
                  "exp": 0.50, "hit": 0.50, "ap": 0.20, "feralap": 0.50, "dps": 2.0, "def": 0.30})
    elif role == "hunter":
        w.update({"agi": 1.0, "sta": 0.10, "ap": 0.50, "hit": 0.70, "crit": 0.55,
                  "haste": 0.35, "arp": 0.50, "armor": 0.002, "dps": 4.0})
    return w


ARMOR_UNLOCK = {"Plate": {"Death Knight": 55, "Warrior": 40, "Paladin": 40}, "Mail": {"Hunter": 40, "Shaman": 40}}
# Pesos propios de una especialidad (se aplican sobre los del rol). Solo hay entradas con una
# fuente verificada; el resto de especialidades usa los pesos genéricos de su rol.
SPEC_WEIGHTS = {
    # Icy Veins WotLK Classic: golpe hasta el tope > poder de hechizos > celeridad > crítico > espíritu
    "Priest|Shadow": {"int": 0.3, "sp": 1.0, "haste": 0.8, "crit": 0.5, "spi": 0.2, "hit": 0.9},
}
# Topes a nivel 80 en puntuación, sin talentos ni bonificaciones raciales (que los bajan):
# golpe de hechizos 17 %, golpe cuerpo a cuerpo/a distancia 8 %, pericia 26.
CAPS = {"caster": {"hit": 446}, "str": {"hit": 263, "exp": 214}, "agi": {"hit": 263, "exp": 214}, "hunter": {"hit": 263}}
ROLES = ["str", "agi", "caster", "healer", "tank", "bear", "hunter"]


def compact(it):
    """Quita campos vacíos y derivables: la página calcula el resto en el navegador."""
    out = {k: it[k] for k in ("n", "i", "q", "ilvl", "req", "s", "sub", "src") if it.get(k) not in (None, "")}
    for k in ("at", "ar", "dps", "cl", "st", "px"):
        if it.get(k):
            out[k] = it[k]
    for k in ("raid", "pvp", "ph"):
        if it.get(k):
            out[k] = 1 if k != "ph" else it[k]
    return out


def main():
    items = json.loads(ITEMS_PATH.read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "data" / "raw_items.json").read_text(encoding="utf-8"))
    zones = {z["id"]: z for z in json.loads((ROOT / "data" / "raw_zones.json").read_text(encoding="utf-8"))}
    raw_by_id = {str(x["itemId"]): x for x in raw}
    heirloom_ids = set(legacy["heirlooms"].keys())
    heirlooms = {}
    for iid in heirloom_ids:
        item = items.get(iid)
        if item:
            heirlooms[iid] = item
            continue
        raw_item = raw_by_id.get(iid)
        if raw_item:
            heirlooms[iid] = {
                "n": raw_item.get("name") or "", "i": raw_item.get("icon") or "", "q": 7,
                "ilvl": raw_item.get("itemLevel") or 1, "req": 0, "s": "heirloom",
                "sub": raw_item.get("subclass") or "", "src": None,
            }

    class_min = {name: legacy["classMeta"][name]["min"] for name in legacy["classOrder"]}
    specs = {}
    for cls, name, role, primary, mode, off, ranged, relic in SPECS:
        specs[f"{cls}|{name}"] = {"cls": cls, "name": name, "role": role, "primary": primary,
                                  "min": class_min[cls], "off": off, "ranged": ranged, "relic": relic, "mode": mode}

    heirloom_sets = {}
    for cls, spec_map in legacy["specs"].items():
        for spec_name, data in spec_map.items():
            heirloom_sets[f"{cls}|{spec_name}"] = {
                "set": data.get("set"), "weapons": data.get("weapons") or [], "offhand": data.get("offhand"),
            }

    brackets = []
    for bracket in legacy["brackets"]:
        name_en, advice_en = BRACKET_EN.get(bracket["min"], (bracket["name"], bracket["advice"]))
        item = dict(bracket)
        item["nameEn"] = name_en
        item["adviceEn"] = advice_en
        brackets.append(item)

    loot = json.loads((ROOT / "data" / "loot.json").read_text(encoding="utf-8"))
    def zone_list(kind):
        return sorted(({"id": z["id"], "n": z["n"], "lv": z["lv"]} for z in loot.values() if z["ty"] == kind and z["lv"][0]),
                      key=lambda d: (d["lv"][0], d["n"]))
    dungeons, raids = zone_list("Dungeon"), zone_list("Raid")

    engine = {
        "specWeights": SPEC_WEIGHTS,
        "caps": CAPS,
        "weights": {role: dict(weights_for(role)) for role in ROLES},
        "armorTiers": ARMOR_TIERS,
        "armorUnlock": ARMOR_UNLOCK,
        "classWeapons": CLASS_WEAPONS,
        "weaponHands": {c: {sub: sorted(h) for sub, h in m.items()} for c, m in WEAPON_HANDS.items()},
    }
    data = {
        "items": {iid: compact(it) for iid, it in items.items()},
        "heirlooms": heirlooms,
        "heirloomSets": heirloom_sets,
        "legacySets": legacy["sets"],
        "specs": specs,
        "engine": engine,
        "dungeons": dungeons,
        "raids": raids,
        "loot": {zid: z["b"] for zid, z in loot.items()},
        "classOrder": legacy["classOrder"],
        "classMeta": legacy["classMeta"],
        "classMetaEn": CLASS_META_EN,
        "brackets": brackets,
        "stats": legacy["stats"],
        "slotOrder": SLOT_ORDER,
        "factions": list(FACTIONS),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("specs", len(specs), "items", len(data["items"]), "dungeons", len(dungeons), "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
