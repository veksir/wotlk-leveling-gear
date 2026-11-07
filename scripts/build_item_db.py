import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw_items.json"
ZONES_RAW = ROOT / "data" / "raw_zones.json"
OUT = ROOT / "data" / "items.json"

QUALITY = {"Uncommon": 2, "Rare": 3, "Epic": 4, "Legendary": 5, "Heirloom": 7}
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


JUNK_RE = re.compile(r"^(\[ph\]|test\b|zz|monster -|npc equip)|deprecated|\(test\)", re.I)


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
        if re.search(r"proc chance|chance to|for \d+ sec|each time|when you|whenever", lower):
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


EFFECT_STATS = [
    ("strength, agility, intellect, or spirit", "hs"),
    ("spell power", "sp"), ("attack power", "ap"), ("haste rating", "haste"), ("critical strike rating", "crit"),
    ("hit rating", "hit"), ("expertise rating", "exp"), ("armor penetration rating", "arp"),
    ("defense rating", "def"), ("dodge rating", "dodge"), ("parry rating", "parry"),
    ("intellect", "int"), ("strength", "str"), ("agility", "agi"), ("stamina", "sta"), ("spirit", "spi"),
]
# Cada cuántos segundos "llega" un evento que puede activar el proc (aproximación única para todas las clases)
PROC_EVENT_SECONDS = 1.5


def parse_effects(tooltip):
    """Procs y efectos de uso con duración ("gain N spell power for D sec").
    Devuelve el promedio estimado de cada estadística: cantidad x tiempo activo."""
    out = {}
    for t in tooltip:
        low = (t.get("label") or "").lower().replace("\xa0", " ")
        if not (low.startswith("use:") or low.startswith("equip:")):
            continue
        dm = re.search(r"for (\d+) sec", low)
        if not dm:
            continue
        duration = int(dm.group(1))
        if low.startswith("use:"):
            cm = re.search(r"\(([\d.]+) (min|sec)[a-z]* cooldown\)", low)
            if not cm:
                continue
            cooldown = float(cm.group(1)) * (60 if cm.group(2) == "min" else 1)
            uptime = min(1.0, duration / cooldown)
        else:
            pm = re.search(r"proc chance: ([\d.]+)%, ([\d.]+)(m|s) cooldown", low)
            if not pm:
                continue
            chance = float(pm.group(1)) / 100
            icd = float(pm.group(2)) * (60 if pm.group(3) == "m" else 1)
            uptime = min(1.0, duration / (icd + PROC_EVENT_SECONDS / max(chance, 0.01)))
        ramp = re.search(r"additional (\d+) every (\d+) sec", low)
        factor = (1 + duration / int(ramp.group(2))) / 2 if ramp else 1.0
        got_hs = False
        for phrase, key in EFFECT_STATS:
            if got_hs and key in ("str", "agi", "int", "spi", "sta"):
                continue  # ya cubierto por «mejor estadística»
            ph = re.escape(phrase)
            # El número debe acompañar a la estadística: "<estadística> by N" o "gain/grant N <estadística>"
            am = re.search(ph + r"\s+by\s+(\d+)", low) or re.search(r"(?:gain|grants?|by)\s+(\d+)\s+(?:additional\s+)?" + ph, low)
            if not am:
                continue
            got_hs = got_hs or key == "hs"
            out[key] = out.get(key, 0) + round(float(am.group(1)) * factor * uptime)
    return {k: v for k, v in out.items() if v > 0}


SOCKET_BONUS_STATS = {
    "spell power": "sp", "attack power": "ap", "strength": "str", "agility": "agi", "intellect": "int", "stamina": "sta",
    "spirit": "spi", "critical strike rating": "crit", "haste rating": "haste", "hit rating": "hit",
    "expertise rating": "exp", "armor penetration rating": "arp", "defense rating": "def", "dodge rating": "dodge",
    "parry rating": "parry", "resilience rating": "res", "mana per 5 sec": "mp5",
}


def parse_sockets(tooltip):
    """Cantidad de sockets normales (sin el meta) y la bonificación del socket."""
    sockets, bonus = 0, {}
    for t in tooltip:
        label = (t.get("label") or "").strip()
        if label.endswith("Socket") and "Meta" not in label and "Bonus" not in label:
            sockets += 1
        m = re.match(r"Socket Bonus:\s*\+(\d+)\s+(.+?)\.?$", label, re.I)
        if m and m.group(2).lower() in SOCKET_BONUS_STATS:
            bonus[SOCKET_BONUS_STATS[m.group(2).lower()]] = int(m.group(1))
    return sockets, (bonus if sockets else {})


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


PVP_RE = re.compile(
    r"Gladiator|Field Marshal|Warlord|Marshal's|General's|Champion's|Lieutenant Commander's|"
    r"Knight-Captain|Knight-Lieutenant|Knight's|Legionnaire|Grand Marshal|High Warlord|Sergeant|"
    r"Stone Guard|Blood Guard|Centurion|Battlemaster",
    re.I,
)
# Una misión de recompensa con este nivel de objeto o más es de cadena de banda
# (Ojo de la Eternidad, Ulduar, Ciudadela de la Corona de Hielo...). Las cartas
# de Darkmoon (200) y las misiones diarias quedan por debajo.
RAID_QUEST_MIN_ILVL = 213
# Épico sin fuente registrada y con este nivel de objeto o más: casi seguro viene de banda
# (fichas de set, botín sin jefe asignado). Se oculta en "Sin bandas" y se rotula "probable".
UNSOURCED_RAID_MIN_ILVL = 213


def source_info(source, zones, ilvl=0, quality=0):
    """Devuelve (src, tipo, es_banda). Campos cortos para que el JSON pese poco."""
    if not source or not source.get("category"):
        return None, "unknown", False
    cat = source.get("category")
    if cat == "Quest":
        quests = source.get("quests") or []
        variants = [{"n": q.get("name") or "Misión", "f": q.get("faction") or "Both", "id": q.get("questId")} for q in quests]
        name = variants[0]["n"] if variants else "Misión"
        raid_quest = quality == 5 or ilvl >= RAID_QUEST_MIN_ILVL
        return {"t": "Quest", "n": name, "q": variants, **({"rq": 1} if raid_quest else {})}, "quest", raid_quest
    if cat == "Vendor":
        return {"t": "Vendor", "n": source.get("name", "Vendedor"), "f": source.get("faction") or "Both"}, "vendor", False
    if cat in ("Boss Drop", "Zone Drop"):
        zid = source.get("zone")
        z = zones.get(zid)
        zone_name = z["name"] if z else None
        zone_cat = z.get("category") if z else None
        chance = source.get("dropChance")
        out = {"t": "Drop", "z": zone_name, "zc": zone_cat, "zid": zid}
        if cat == "Boss Drop":
            out["n"] = source.get("name")
        if isinstance(chance, (int, float)) and 0 < chance <= 1:
            out["dc"] = round(chance * 100, 1)
        return out, "drop", zone_cat == "Raid"
    if cat == "Rare Drop":
        chance = source.get("dropChance")
        out = {"t": "Rare"}
        if isinstance(chance, (int, float)) and 0 < chance <= 1:
            out["dc"] = round(chance * 100, 2)
        return out, "rare", False
    return {"t": cat or "Fuente"}, "other", False


LOOT_PATH = Path(__file__).resolve().parent.parent / "data" / "loot_wrath.json"
LOOT_OUT = Path(__file__).resolve().parent.parent / "data" / "loot.json"
DIFF_ORDER = ["N", "H", "10", "25", "10H", "25H"]


def apply_atlasloot(items, zones):
    """Une el botín de AtlasLoot (WotLK, por jefe y dificultad) con las fuentes del dataset.
    Escribe data/loot.json: zona -> jefe -> objeto -> dificultades, que usa el panel de botín."""
    loot = {}
    # 1) Fuentes de jefe que ya trae el dataset principal
    for iid, it in items.items():
        s = it.get("src") or {}
        if s.get("t") == "Drop" and s.get("zid"):
            z = loot.setdefault(s["zid"], {"id": s["zid"], "n": s.get("z"), "ty": s.get("zc"),
                                           "lv": (zones.get(s["zid"]) or {}).get("level"), "b": {}})
            z["b"].setdefault(s.get("n") or "", {}).setdefault(iid, {"d": []})
    # 2) AtlasLoot: completa Ulduar, ToC, ICC... y marca normal/heroica y 10/25
    if LOOT_PATH.exists():
        for zone in json.loads(LOOT_PATH.read_text(encoding="utf-8")):
            z = loot.setdefault(zone["id"], {"id": zone["id"], "n": zone["n"], "ty": zone["type"], "lv": zone["lv"], "b": {}})
            z["n"], z["ty"], z["lv"] = zone["n"], zone["type"], zone["lv"] or z.get("lv")
            for boss, entries in zone["bosses"].items():
                for iid, e in entries.items():
                    it = items.get(iid)
                    if not it:
                        continue
                    z["b"].setdefault(boss, {})[iid] = e
                    src = it.get("src") or {}
                    if src.get("t") in ("Otra", "RaidProb"):  # sin fuente hasta ahora
                        it["src"] = {"t": "Drop", "z": zone["n"], "zc": zone["type"], "zid": zone["id"], "n": boss}
                        it["sk"] = "drop"
                        it["raid"] = zone["type"] == "Raid"
                    if e.get("f") and (it["src"] or {}).get("t") == "Drop":
                        it["src"]["f"] = e["f"]
                    if (it["src"] or {}).get("zid") == zone["id"] and (it["src"] or {}).get("n") == boss:
                        it["src"]["df"] = "/".join(sorted(e["d"], key=DIFF_ORDER.index)) if e["d"] else None
                        if not it["src"]["df"]:
                            del it["src"]["df"]
    out = {}
    for zid, z in loot.items():
        bosses = {b: {i: sorted(e.get("d", []), key=DIFF_ORDER.index) + ([e["f"]] if e.get("f") else []) for i, e in its.items()}
                  for b, its in z["b"].items() if its}
        if bosses and z.get("n") and z.get("ty") in ("Dungeon", "Raid"):
            out[str(zid)] = {"id": zid, "n": z["n"], "ty": z["ty"], "lv": z.get("lv") or [0, 0], "b": bosses}
    LOOT_OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("zonas con botín", len(out), "(raids:", sum(1 for z in out.values() if z["ty"] == "Raid"), ")")


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
        if quality not in (2, 3, 4, 5):
            continue
        req = int(it.get("requiredLevel") or 0)
        ilvl = int(it.get("itemLevel") or 0)
        inferred = infer_req(ilvl)
        if it.get("quality") != "Heirloom" and (req == 0 or inferred - req > 15):
            req = inferred
        if req > 80 or ilvl > 284 or ilvl < 1:
            continue
        if JUNK_RE.search(it.get("name") or ""):
            continue
        tooltip = it.get("tooltip") or []
        labels = " ".join((t.get("label") or "") for t in tooltip)
        if "Random enchantment" in labels:
            continue
        stats, armor, dps, speed = parse_stats(tooltip)
        px = parse_effects(tooltip)
        sockets, socket_bonus = parse_sockets(tooltip)
        if not stats and not px and dps == 0 and slot != "relic" and not (slot == "offhand" and armor > 0):
            continue
        classes, races = parse_restrictions(tooltip)
        is_pvp = bool(PVP_RE.search(it.get("name") or "")) or bool(stats.get("res"))
        src, src_kind, is_raid = source_info(it.get("source"), zones, ilvl, quality)
        if src is None:
            src, src_kind = {"t": "Otra"}, "other"
            if is_pvp:
                src = {"t": "PvP"}
            elif quality >= 4 and ilvl >= UNSOURCED_RAID_MIN_ILVL:
                src, is_raid = {"t": "RaidProb"}, True
        sub = it.get("subclass") or ""
        cls = it.get("class")
        armor_type = sub if cls == "Armor" and sub in ("Cloth", "Leather", "Mail", "Plate", "Shield") else None
        hands = 2 if slot == "twohand" else (1 if slot in ("onehand", "mainhand", "offhand") else 0)
        ranged = slot in ("ranged", "thrown")
        phase = it.get("contentPhase")
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
            "px": px,
            "sc": sockets,
            "sb": socket_bonus,
            "ar": armor,
            "dps": round(dps, 1),
            "spd": speed,
            "src": src,
            "sk": src_kind,
            "raid": is_raid,
            "pvp": is_pvp,
            "ph": phase if isinstance(phase, int) else 0,
            "cl": classes,
            "ra": races,
            "h": hands,
            "rg": ranged,
        }

    apply_atlasloot(items, zones)
    print("items", len(items))
    from collections import Counter
    print("slots", Counter(v["s"] for v in items.values()))
    print("leveling", sum(1 for v in items.values() if v["src"] and not v["raid"] and v["sk"] != "unknown"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
