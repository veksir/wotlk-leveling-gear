import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from bisect import insort

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

PVP_RE = re.compile(
    r"Gladiator|Field Marshal|Warlord|Marshal's|General's|Champion's|Lieutenant Commander's|"
    r"Knight-Captain|Knight-Lieutenant|Knight's|Legionnaire|Grand Marshal|High Warlord|Sergeant|"
    r"Stone Guard|Blood Guard|Centurion|Battlemaster",
    re.I,
)


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


def source_priority(item):
    known = bool(item.get("src")) and item.get("src", {}).get("t") != "Otra"
    if known and not PVP_RE.search(item.get("n", "")):
        return 2
    if known:
        return 1
    return 0


def norm_faction(value):
    if not value:
        return "both"
    value = str(value).lower()
    return "both" if value in ("both", "none") else value


def item_factions(item):
    src = item.get("src") or {}
    factions = set()
    if src.get("t") == "Quest":
        for quest in src.get("q") or []:
            factions.add(norm_faction(quest.get("f")))
    elif src.get("t") == "Vendor":
        factions.add(norm_faction(src.get("f")))
    return factions or {"both"}


def item_score(item, weights):
    total = item.get("ar", 0) * weights.get("armor", 0) + item.get("dps", 0) * weights.get("dps", 0) + item.get("ilvl", 0) * 0.01
    for key, value in (item.get("st") or {}).items():
        total += value * weights.get(key, 0)
    return round(total, 4)


def armor_unlock(cls, at):
    if at == "Plate":
        if cls == "Death Knight":
            return 55
        if cls in ("Warrior", "Paladin"):
            return 40
    if at == "Mail" and cls in ("Hunter", "Shaman"):
        return 40
    return 1


def preferred_armor(spec_cls, level):
    if spec_cls in ("Mage", "Priest", "Warlock"):
        return "Cloth"
    if spec_cls in ("Druid", "Rogue"):
        return "Leather"
    if spec_cls in ("Hunter", "Shaman"):
        return "Leather" if level < 40 else "Mail"
    if spec_cls in ("Warrior", "Paladin"):
        return "Mail" if level < 40 else "Plate"
    return "Plate"


def armor_factor(spec_cls, at, level):
    tiers = ARMOR_TIERS.get(spec_cls, ["Cloth"])
    if at not in tiers:
        return 0
    pref = preferred_armor(spec_cls, level)
    diff = tiers.index(at) - tiers.index(pref)
    return [1.0, 0.6, 0.35, 0.2][max(0, diff)] if diff >= 0 else 0.4


def spec_slots(spec):
    _, _, role, primary, mode, off, ranged, relic = spec
    slots = list(ARMOR_KEYS) + ["neck", "ring1", "ring2", "trinket1", "trinket2", "mainhand"]
    if off:
        slots.append("offhand")
    if ranged:
        slots.append("ranged")
    if relic:
        slots.append("relic")
    return slots


def compute_slots(items, spec, faction, minlevel):
    cls, name, role, primary, mode, off, ranged, relic = spec
    weights = weights_for(role)
    out_slots = {key: [[] for _ in range(81)] for key in spec_slots(spec)}
    referenced = set()

    def eligible(item):
        if item.get("raid"):
            return False
        if item.get("cl") and cls not in item["cl"]:
            return False
        factions = item_factions(item)
        return "both" in factions or faction in factions

    def available_level(item):
        req = item.get("req") or 0
        level = max(1 if req <= 0 else req, minlevel)
        if item.get("at"):
            level = max(level, armor_unlock(cls, item["at"]))
        return level if level <= 80 else None

    by_level = defaultdict(lambda: defaultdict(list))
    for iid, item in items.items():
        if not eligible(item):
            continue
        slot = item["s"]
        sub = item.get("sub")
        at = item.get("at")
        hands = item.get("h", 0)
        score = item_score(item, weights)
        if score <= 0:
            continue
        level = available_level(item)
        if level is None:
            continue
        prio = source_priority(item)

        if slot in ARMOR_KEYS:
            if slot == "back":
                by_level["back"].setdefault(level, []).append((score, item.get("ilvl", 0), iid, None, prio))
            elif at in ARMOR_TIERS.get(cls, []):
                by_level[slot].setdefault(level, []).append((score, item.get("ilvl", 0), iid, at, prio))
        elif slot in ("neck", "ring", "trinket"):
            by_level[slot].setdefault(level, []).append((score, item.get("ilvl", 0), iid, None, prio))
        elif slot == "offhand" and at == "Shield" and off == "shield":
            by_level["offhand"].setdefault(level, []).append((score, item.get("ilvl", 0), iid, None, prio))
        elif slot in ("twohand", "onehand", "mainhand", "offhand"):
            if sub not in CLASS_WEAPONS[cls]:
                continue
            if hands not in WEAPON_HANDS.get(cls, {}).get(sub, set()):
                continue
            if mode == "2h" and hands != 2:
                continue
            if mode == "1h" and hands != 1:
                continue
            if mode == "any" and hands not in (1, 2):
                continue
            by_level["mainhand"].setdefault(level, []).append((score, item.get("ilvl", 0), iid, None, prio))
            if off == "dw" and hands == 1:
                by_level["offhand"].setdefault(level, []).append((score, item.get("ilvl", 0), iid, None, prio))
        elif slot == "held" and off == "held":
            by_level["offhand"].setdefault(level, []).append((score, item.get("ilvl", 0), iid, None, prio))
        elif slot in ("ranged", "thrown") and ranged:
            if ranged == "ranged":
                ok = slot == "ranged" and sub in ("Bow", "Gun", "Crossbow")
            elif ranged == "wand":
                ok = slot == "ranged" and sub == "Wand"
            elif ranged == "thrown":
                ok = slot == "thrown" or (slot == "ranged" and sub == "Thrown")
            else:
                ok = False
            if ok:
                by_level["ranged"].setdefault(level, []).append((score, item.get("ilvl", 0), iid, None, prio))
        elif slot == "relic" and relic and sub == relic:
            by_level["relic"].setdefault(level, []).append((score, item.get("ilvl", 0), iid, None, prio))

    pools = {key: [] for key in out_slots}
    for level in range(1, 81):
        for slot, bucket in by_level.items():
            for entry in bucket.get(level, []):
                insort(pools.setdefault(slot, []), entry)
        for slot in out_slots:
            source = "ring" if slot in ("ring1", "ring2") else ("trinket" if slot in ("trinket1", "trinket2") else slot)
            pool = pools.get(source, [])

            def adjusted(entry):
                return entry[0] * (armor_factor(cls, entry[3], level) if entry[3] else 1.0)

            top = sorted(pool, key=lambda x: (-x[4], -adjusted(x), -x[1]))[:4]
            if slot == "ring1":
                ids = [x[2] for x in top[:3]]
            elif slot == "ring2":
                ids = [x[2] for x in top[1:4]]
            elif slot == "trinket1":
                ids = [x[2] for x in top[:3]]
            elif slot == "trinket2":
                ids = [x[2] for x in top[1:4]]
            elif slot == "offhand" and off == "dw":
                main = out_slots["mainhand"][level]
                exclude = main[0] if main else None
                ids = [x[2] for x in top if x[2] != exclude][:3]
            else:
                ids = [x[2] for x in top[:3]]
            out_slots[slot][level] = ids
            referenced.update(ids)
    return out_slots, referenced


def main():
    items = json.loads(ITEMS_PATH.read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "data" / "raw_items.json").read_text(encoding="utf-8"))
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
                "sub": raw_item.get("subclass") or "", "at": None, "st": {}, "ar": 0,
                "dps": 0, "spd": 0, "src": None, "sk": "heirloom", "raid": False,
                "cl": None, "ra": None, "h": 0, "rg": False,
            }

    recommendations = {}
    referenced = set(heirloom_ids)
    class_min = {name: legacy["classMeta"][name]["min"] for name in legacy["classOrder"]}

    for spec in SPECS:
        cls, name, role, primary, mode, off, ranged, relic = spec
        key = f"{cls}|{name}"
        rec = {
            "cls": cls, "name": name, "role": role, "primary": primary,
            "min": class_min[cls], "off": off, "ranged": ranged, "relic": relic,
            "mode": mode, "slots": {},
        }
        for faction in FACTIONS:
            slots, used = compute_slots(items, spec, faction, class_min[cls])
            rec["slots"][faction] = slots
            referenced.update(used)
        recommendations[key] = rec

    heirloom_sets = {}
    for cls, spec_map in legacy["specs"].items():
        for spec_name, data in spec_map.items():
            heirloom_sets[f"{cls}|{spec_name}"] = {
                "set": data.get("set"),
                "weapons": data.get("weapons") or [],
                "offhand": data.get("offhand"),
            }

    brackets = []
    for bracket in legacy["brackets"]:
        try:
            name_en, advice_en = BRACKET_EN.get(bracket["min"], (bracket["name"], bracket["advice"]))
        except Exception:
            name_en, advice_en = bracket["name"], bracket["advice"]
        item = dict(bracket)
        item["nameEn"] = name_en
        item["adviceEn"] = advice_en
        brackets.append(item)

    data = {
        "items": {iid: items[iid] for iid in referenced if iid in items},
        "heirlooms": heirlooms,
        "heirloomSets": heirloom_sets,
        "legacySets": legacy["sets"],
        "specs": recommendations,
        "classOrder": legacy["classOrder"],
        "classMeta": legacy["classMeta"],
        "classMetaEn": CLASS_META_EN,
        "brackets": brackets,
        "stats": legacy["stats"],
        "slotOrder": SLOT_ORDER,
        "factions": list(FACTIONS),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("specs", len(recommendations), "items used", len(data["items"]), "bytes", OUT.stat().st_size)
    for key in ["Warrior|Arms", "Mage|Frost", "Paladin|Holy", "Hunter|Marksmanship"]:
        rec = recommendations[key]
        print("\n", key)
        for faction in FACTIONS:
            for level in (20, 60, 80):
                print(faction, level, {s: rec["slots"][faction][s][level] for s in ("head", "chest", "mainhand", "ranged") if s in rec["slots"][faction]})


if __name__ == "__main__":
    main()
