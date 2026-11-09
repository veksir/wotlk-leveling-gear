import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
ITEMS_PATH = ROOT / "data" / "items.json"
OUT = ROOT / "data" / "gear_data.json"
SPEC_WEIGHTS_PATH = ROOT / "data" / "spec_weights.json"
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
    "Paladin": {"Axe": {1, 2}, "Mace": {1, 2}, "Sword": {1, 2}, "Polearm": {2}},
    "Priest": {"Mace": {1}, "Dagger": {1}, "Staff": {2}},
    "Rogue": {"Dagger": {1}, "Axe": {1}, "Sword": {1}, "Mace": {1}, "Fist Weapon": {1}},
    "Shaman": {"Mace": {1, 2}, "Axe": {1, 2}, "Dagger": {1}, "Staff": {2}, "Fist Weapon": {1}},
    "Warlock": {"Sword": {1}, "Dagger": {1}, "Staff": {2}},
    "Warrior": {"Axe": {1, 2}, "Sword": {1, 2}, "Mace": {1, 2}, "Dagger": {1}, "Fist Weapon": {1}, "Polearm": {2}, "Staff": {2}},
}

CLASS_WEAPONS = {
    "Death Knight": ["Axe", "Sword", "Mace", "Polearm"],
    "Druid": ["Mace", "Staff", "Polearm", "Dagger", "Fist Weapon"],
    "Hunter": ["Axe", "Sword", "Dagger", "Fist Weapon", "Polearm", "Staff"],
    "Mage": ["Sword", "Dagger", "Staff"],
    "Paladin": ["Axe", "Mace", "Sword", "Polearm"],
    "Priest": ["Mace", "Dagger", "Staff"],
    "Rogue": ["Dagger", "Axe", "Sword", "Mace", "Fist Weapon"],
    "Shaman": ["Mace", "Axe", "Dagger", "Staff", "Fist Weapon"],
    "Warlock": ["Sword", "Dagger", "Staff"],
    "Warrior": ALL_MELEE,
}

SPECS = [
    ("Death Knight", "Blood Tank", "tank", "str", "2h", None, None, "Sigil"),
    ("Death Knight", "Frost DPS", "str", "str", "1h", "dw", None, "Sigil"),
    ("Death Knight", "Unholy DPS", "str", "str", "2h", None, None, "Sigil"),
    ("Druid", "Balance", "caster", "int", "any", "held", None, "Idol"),
    ("Druid", "Feral DPS", "feral", "agi", "2h", None, None, "Idol"),
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
    ("Rogue", "Assassination", "agi", "agi", "1h", "dw", "anyranged", None),
    ("Rogue", "Combat", "agi", "agi", "1h", "dw", "anyranged", None),
    ("Rogue", "Subtlety", "agi", "agi", "1h", "dw", "anyranged", None),
    ("Shaman", "Elemental", "caster", "int", "any", "shield", None, "Totem"),
    ("Shaman", "Enhancement", "agi", "agi", "1h", "dw", None, "Totem"),
    ("Shaman", "Restoration", "healer", "int", "any", "shield", None, "Totem"),
    ("Warlock", "Affliction", "caster", "int", "any", "held", "wand", None),
    ("Warlock", "Demonology", "caster", "int", "any", "held", "wand", None),
    ("Warlock", "Destruction", "caster", "int", "any", "held", "wand", None),
    ("Warrior", "Arms", "str", "str", "2h", None, "anyranged", None),
    ("Warrior", "Fury", "str", "str", "tg", "dw", "anyranged", None),
    ("Warrior", "Protection", "tank", "str", "1h", "shield", "anyranged", None),
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
    if role in ("str", "agi", "feral"):
        key = "agi" if role == "feral" else role
        # El poder de ataque feral solo vale para el druida feral (rol «feral»), no para todo el rol «agi»
        w.update({key: 1.0, "sta": 0.10, "ap": 0.50, "feralap": 0.50 if role == "feral" else 0.0,
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
# Pesos por especialidad a nivel 80, derivados de las prioridades de Icy Veins WotLK Classic
# (data/spec_weights.json guarda fuente y prioridad). En niveles inferiores se usan los del rol.
def load_spec_weights():
    source = json.loads(SPEC_WEIGHTS_PATH.read_text(encoding="utf-8"))
    source.pop("_meta", None)
    known = {f"{cls}|{name}" for cls, name, *_ in SPECS}
    missing, extra = known - source.keys(), source.keys() - known
    if missing or extra:
        raise SystemExit(f"spec_weights.json: faltan {sorted(missing)}; sobran {sorted(extra)}")
    for key, entry in source.items():
        if not entry.get("source") or not entry.get("priority") or not isinstance(entry.get("weights"), dict):
            raise SystemExit(f"spec_weights.json: entrada incompleta para {key}")
    return {key: entry["weights"] for key, entry in source.items()}

SPEC_WEIGHTS = load_spec_weights()
# Topes a nivel 80 en puntuación, sin talentos ni bonificaciones raciales (que los bajan):
# golpe de hechizos 17 %, golpe cuerpo a cuerpo/a distancia 8 %, pericia 26.
CAPS = {"caster": {"hit": 446}, "str": {"hit": 263, "exp": 214}, "agi": {"hit": 263, "exp": 214}, "feral": {"hit": 263, "exp": 214}, "hunter": {"hit": 263}}
# Familias de arma que prefieren las guías para cada especialidad (el resto se penaliza un 10 %, no se excluye)
WEAPON_PREF = {
    "Rogue|Assassination": ["Dagger"], "Rogue|Subtlety": ["Dagger"],
    "Rogue|Combat": ["Sword", "Axe", "Mace", "Fist Weapon"],
    "Shaman|Enhancement": ["Axe", "Mace", "Fist Weapon"],
    "Hunter|Beast Mastery": ["Polearm", "Staff"], "Hunter|Marksmanship": ["Polearm", "Staff"], "Hunter|Survival": ["Polearm", "Staff"],
    "Paladin|Protection": ["Mace"], "Warrior|Protection": ["Mace"],
}
ROLES = ["str", "agi", "feral", "caster", "healer", "tank", "bear", "hunter"]


def compact(it):
    """Quita campos vacíos y derivables: la página calcula el resto en el navegador."""
    out = {k: it[k] for k in ("n", "i", "q", "ilvl", "req", "s", "sub", "src") if it.get(k) not in (None, "")}
    for k in ("at", "ar", "dps", "cl", "st", "px", "sc", "sg", "mt", "sb"):
        if it.get(k):
            out[k] = it[k]
    for k in ("raid", "pvp", "ph"):
        if it.get(k):
            out[k] = 1 if k != "ph" else it[k]
    return out


HEIRLOOM_SLOTS = {
    "Head": "head", "Neck": "neck", "Shoulder": "shoulder", "Back": "back",
    "Chest": "chest", "Wrist": "wrist", "Hands": "hands", "Waist": "waist",
    "Legs": "legs", "Feet": "feet", "Finger": "ring", "Trinket": "trinket",
    "Two-Hand": "twohand", "One-Hand": "onehand", "Main Hand": "mainhand",
    "Off Hand": "offhand", "Held In Off-hand": "held", "Ranged": "ranged",
    "Thrown": "thrown", "Relic": "relic",
}
HEIRLOOM_ARMOR = {"Cloth", "Leather", "Mail", "Plate"}

SET_SLOT_ALIASES = {
    "head": "head", "helm": "head", "helmet": "head", "cabeza": "head",
    "shoulder": "shoulder", "shoulders": "shoulder", "pauldrons": "shoulder", "hombro": "shoulder", "hombros": "shoulder",
    "chest": "chest", "torso": "chest", "pecho": "chest",
    "hand": "hands", "hands": "hands", "gloves": "hands", "gauntlets": "hands", "manos": "hands", "guantes": "hands",
    "leg": "legs", "legs": "legs", "leggings": "legs", "legplates": "legs", "piernas": "legs",
}


def recommended_set_slots(text):
    """Ranuras que la guía recomienda llevar del set, p. ej. «2 piezas (Head y Shoulder) + ...»."""
    m = re.search(r"\(([^)]*)\)", str(text or ""))
    if not m:
        return []
    out = []
    for token in re.split(r",|/|\by\b", m.group(1).lower()):
        slot = SET_SLOT_ALIASES.get(token.strip())
        if slot and slot not in out:
            out.append(slot)
    return out


def build_set_bonus():
    """Bonus de set T10 por especialidad, a partir de data/reference_sets.json (guías de Icy Veins/Wowhead).
    Cada especialidad recibe las piezas recomendadas por la guía, cuántas piezas usa (2 o 4) y el valor
    aproximado del bonus en % (acotado a 2-8 %; 5 % si la guía no da un número)."""
    path = ROOT / "data" / "reference_sets.json"
    if not path.exists():
        return {}

    def pct(text):
        t = str(text or "")
        m = (re.search(r"~\s*([\d.]+)\s*(?:-|–|a)\s*([\d.]+)\s*%", t) or re.search(r"~\s*([\d.]+)\s*%", t)
             or re.search(r"([\d.]+)\s*(?:-|–)\s*([\d.]+)\s*%", t) or re.search(r"([\d.]+)\s*%", t))
        if not m:
            return None
        vals = [float(x) for x in m.groups() if x]
        return sum(vals) / len(vals)

    out = {}
    for cls, cv in json.loads(path.read_text(encoding="utf-8")).items():
        if cls == "resumen_calidad":
            continue
        for var in cv["variants"].values():
            all_ids = sorted({str(e["id"]) for lst in var["pieces"].values() for e in lst})
            for spec, rec in var["recommendations_by_spec"].items():
                need = 2 if re.match(r"\s*2\s*pieza", str(rec.get("recommended_pieces", "")), re.I) else 4
                slots = recommended_set_slots(rec.get("recommended_pieces"))
                slots = slots[:need]
                if slots:
                    ids = sorted({str(e["id"]) for slot in slots for e in var["pieces"].get(slot, [])})
                else:
                    ids = all_ids
                value = pct(rec.get("approx_value"))
                out[spec] = {"ids": ids, "need": need, "slots": slots,
                             "pct": round(min(8.0, max(2.0, value)), 2) if value else 5.0}
    return out


def build_curated():
    """Abalorios y reliquias recomendados por las guías (data/reference_trinkets.json), en orden.
    El motor no puede valorar bien sus procs y efectos, así que estas listas mandan en esos dos slots."""
    path = ROOT / "data" / "reference_trinkets.json"
    if not path.exists():
        return {}
    out = {}
    for spec, v in json.loads(path.read_text(encoding="utf-8")).items():
        trinkets = []
        for e in list(v.get("bis_trinkets") or []) + sorted(v.get("top_6_trinkets") or [], key=lambda x: x.get("rank", 99)):
            if str(e["id"]) not in trinkets:
                trinkets.append(str(e["id"]))
        relic = v.get("relic")
        out[spec] = {"trinket": trinkets, "relic": [str(relic["id"])] if isinstance(relic, dict) and relic.get("id") else []}
    return out


GEM_STAT_NAMES = {"spell power": "sp", "attack power": "ap", "strength": "str", "agility": "agi", "intellect": "int", "stamina": "sta",
                  "spirit": "spi", "critical strike rating": "crit", "crit rating": "crit", "haste rating": "haste", "hit rating": "hit",
                  "expertise rating": "exp", "armor penetration rating": "arp", "defense rating": "def", "dodge rating": "dodge",
                  "parry rating": "parry", "resilience rating": "res", "mp5": "mp5", "mana per 5 sec": "mp5"}


def parse_gem_stats(text):
    """'+21 Intellect and Chance to restore mana' -> {'int': 21} (los efectos sin número no se parsean aquí)."""
    import re
    clean = re.sub(r"\(.*?\)", "", str(text or ""))
    st = {}
    for num, stat in re.findall(r"\+(\d+)\s+([A-Za-z0-9 ]+?)(?=\s+and\b|,|\.|$)", clean):
        key = GEM_STAT_NAMES.get(stat.strip().lower())
        if key:
            st[key] = st.get(key, 0) + int(num)
    return st


def load_meta_gems():
    path = ROOT / "data" / "reference_meta_gems.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"gems": {}}


def build_gems():
    """Gemas recomendadas por especialidad y color (data/reference_gems.json) y su meta-gema.

    ENG.gems[spec] = {red: [st], yellow: [st], blue: [st], meta: {id, name, st, requires, extraEp}}"""
    path = ROOT / "data" / "reference_gems.json"
    if not path.exists():
        return {}
    metas = load_meta_gems()["gems"]
    out = {}
    for spec, v in json.loads(path.read_text(encoding="utf-8")).items():
        entry = {}
        for color in ("red", "yellow", "blue"):
            seen, gems = set(), []
            for g in v.get(f"{color}_socket") or []:
                if g.get("id") in seen:
                    continue
                seen.add(g.get("id"))
                st = parse_gem_stats(g.get("stats"))
                if st:
                    gems.append(st)
            entry[color] = gems
        meta = v.get("meta_gem") or {}
        info = metas.get(str(meta.get("id")))
        if info:
            entry["meta"] = {"id": meta["id"], "name": info["name"], "st": parse_gem_stats(meta.get("stats")),
                             "requires": info["requires"], "extraEp": info.get("extra_ep", 0)}
        out[spec] = entry
    return out


def build_caps_by_spec():
    """Topes de golpe y pericia por especialidad a nivel 80 (data/reference_stats.json, Icy Veins/Wowhead).
    Se usa el tope más bajo que se alcanza con los talentos de la propia especialidad, sin bonus racial, y se
    descartan las variantes de golpe blanco (dual wield), venenos y raza: lo que el equipo tiene que cubrir."""
    path = ROOT / "data" / "reference_stats.json"
    if not path.exists():
        return {}
    skip = ("draenei", "white", "poison", "frostfire", "dwarf", "human")
    roles = {f"{c}|{n}": role for c, n, role, *_ in SPECS}
    out = {}
    for spec, v in json.loads(path.read_text(encoding="utf-8")).items():
        caps = v.get("caps") if isinstance(v, dict) else None
        role = roles.get(spec)
        if not isinstance(caps, dict) or role not in CAPS:
            continue
        spell = role in ("caster", "healer")
        hits = [x for k, x in caps.items() if isinstance(x, (int, float)) and "hit" in k and not any(t in k for t in skip)
                and (("spell" in k) if spell else ("spell" not in k))]
        exps = [x for k, x in caps.items() if isinstance(x, (int, float)) and "expertise" in k and not any(t in k for t in skip)]
        entry = {}
        if "hit" in CAPS[role] and hits:
            entry["hit"] = int(min(hits))
        if "exp" in CAPS[role] and exps:
            entry["exp"] = int(min(exps))
        if entry:
            out[spec] = entry
    return out


def main():
    items = json.loads(ITEMS_PATH.read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "data" / "raw_items.json").read_text(encoding="utf-8"))
    zones = {z["id"]: z for z in json.loads((ROOT / "data" / "raw_zones.json").read_text(encoding="utf-8"))}
    raw_by_id = {str(x["itemId"]): x for x in raw}
    stats_path = ROOT / "data" / "heirloom_stats.json"
    heirloom_stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {}
    heirloom_ids = sorted(legacy["heirlooms"].keys(), key=int)
    heirlooms = {}
    for iid in heirloom_ids:
        raw_item = raw_by_id.get(iid)
        if not raw_item:
            continue
        subclass = raw_item.get("subclass") or ""
        source = (legacy["heirlooms"].get(iid) or {}).get("source") or ""
        entry = {
            "n": raw_item.get("name") or "", "i": raw_item.get("icon") or "", "q": 7,
            "ilvl": raw_item.get("itemLevel") or 1, "req": 0,
            "s": HEIRLOOM_SLOTS.get(raw_item.get("slot") or "", "heirloom"),
            "sub": subclass,
            "src": {"t": "Vendor", "n": "Emblemas de Heroísmo" if source == "Emblemas" else "Marcas de la Conquista del Invierno", "f": "Both"},
        }
        if subclass in HEIRLOOM_ARMOR:
            entry["at"] = subclass
        if iid in heirloom_stats:
            entry["hl"] = heirloom_stats[iid]
        heirlooms[iid] = entry

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
        "setBonus": build_set_bonus(),
        "curated": build_curated(),
        "gems": build_gems(),
        "metaGems": {"wildcard": load_meta_gems().get("wildcard")},
        "caps": CAPS,
        "capsBySpec": build_caps_by_spec(),
        "weaponPref": WEAPON_PREF,
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
        "stats": {**legacy["stats"], "feral": legacy["stats"]["agi"]},
        "slotOrder": SLOT_ORDER,
        "factions": list(FACTIONS),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("specs", len(specs), "items", len(data["items"]), "dungeons", len(dungeons), "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
