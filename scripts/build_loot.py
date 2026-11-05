"""Convierte data-wrath.lua de AtlasLootClassic en data/loot_wrath.json (jefe -> objetos por dificultad)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "raw_atlasloot_wrath.lua"
OUT = ROOT / "data" / "loot_wrath.json"

ZONE_NAMES = {
    "AhnKahet": "Ahn'kahet: The Old Kingdom", "AzjolNerub": "Azjol-Nerub", "DrakTharonKeep": "Drak'Tharon Keep",
    "ForgeOfSouls": "The Forge of Souls", "Gundrak": "Gundrak", "HallsOfReflection": "Halls of Reflection",
    "HallsofLightning": "Halls of Lightning", "HallsofStone": "Halls of Stone", "IcecrownCitadel": "Icecrown Citadel",
    "NaxxramasWrath": "Naxxramas", "ObsidianSanctum": "The Obsidian Sanctum", "PitOfSaron": "Pit of Saron",
    "RubySanctum": "The Ruby Sanctum", "TheCullingOfStratholme": "The Culling of Stratholme",
    "TheEyeOfEternity": "The Eye of Eternity", "TheNexus": "The Nexus", "TheOculus": "The Oculus",
    "TrialoftheChampion": "Trial of the Champion", "TrialoftheCrusader": "Trial of the Crusader", "Ulduar": "Ulduar",
    "UtgardeKeep": "Utgarde Keep", "UtgardePinnacle": "Utgarde Pinnacle", "VaultofArchavon": "Vault of Archavon",
    "VioletHold": "The Violet Hold", "WrathOnyxiasLair": "Onyxia's Lair",
}
DIFF_CODES = {"NORMAL": "N", "HEROIC": "H", "RAID10": "10", "RAID25": "25", "RAID10H": "10H", "RAID25H": "25H",
              "T10_1": "25", "T10_2": "25H"}  # ALPHA/BETA (runas de Titán) y VENDOR se ignoran


def main():
    zones, cur, boss, diff, in_items, fac = {}, None, None, None, False, None
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("--"):
            continue
        m = re.match(r'^data\["(\w+)"\]\s*=\s*\{', line)
        if m:
            key = m.group(1)
            cur = zones.setdefault(key, {"key": key, "n": ZONE_NAMES.get(key, key), "id": None, "type": "Dungeon", "lv": None, "bosses": {}})
            boss, diff, in_items = None, None, False
            continue
        if not cur:
            continue
        if not in_items:
            m = re.search(r"MapID = (\d+)", line)
            if m and cur["id"] is None:
                cur["id"] = int(m.group(1))
            if "ContentType = RAID" in line:
                cur["type"] = "Raid"
            m = re.search(r"LevelRange = \{(\d+), (\d+)", line)
            if m:
                cur["lv"] = [int(m.group(1)), int(m.group(2))]
            if re.match(r"^\s*items = \{", line):
                in_items = True
            continue
        m = re.match(r'^\s*name = AL\["(.+?)"\],', line)
        if m:
            boss, diff = m.group(1), None
            cur["bosses"].setdefault(boss, {})
            continue
        m = re.search(r"\[(\w+)_DIFF\]\s*=", line)
        if m:
            diff, fac = DIFF_CODES.get(m.group(1)), None
            continue
        # Trial of the Crusader: cada dificultad trae una lista de Horda y otra de Alianza
        if re.match(r"^\s*\{\s*--\s*horde", line, re.I):
            fac = "horde"
            continue
        if re.match(r"^\s*\{\s*--\s*alli", line, re.I):
            fac = "alliance"
            continue
        m = re.match(r"^\s*\{\s*(\d+)\s*,\s*(\d+)\s*\}", line)
        if m and boss and diff:
            entry = cur["bosses"][boss].setdefault(m.group(2), {"d": set(), "f": fac})
            entry["d"].add(diff)
    out = []
    for z in zones.values():
        if z["id"] is None:
            continue
        z["bosses"] = {b: {i: {"d": sorted(e["d"]), **({"f": e["f"]} if e["f"] else {})} for i, e in items.items()}
                       for b, items in z["bosses"].items() if items}
        if z["type"] == "Raid" and not z["lv"]:
            z["lv"] = [80, 80]
        out.append(z)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("zonas", len(out), "jefes", sum(len(z["bosses"]) for z in out), "objetos", sum(len(i) for z in out for i in z["bosses"].values()))


if __name__ == "__main__":
    main()
