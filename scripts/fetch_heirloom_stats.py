"""Genera data/heirloom_stats.json con estadísticas por nivel de las reliquias.

Fuente principal: tablas «Item statistics by level» del archivo de WoWWiki.
Las reliquias PvP sin tabla se consultan en el tooltip de Wowhead WotLK.
El archivo generado se versiona para que el build no dependa de la red.
"""
import concurrent.futures
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "heirloom_stats.json"
sys.path.insert(0, str(ROOT / "legacy"))
from data_leveling import payload as legacy  # noqa: E402

NAMES = json.loads((ROOT / "legacy" / "heirloom_names.json").read_text(encoding="utf-8"))
WIKI_API = "https://wowwiki-archive.fandom.com/api.php"
WOWHEAD = "https://nether.wowhead.com/wotlk/tooltip/item/{id}?data=1&lvl={level}"

HEADER = {
    "armor": "ar", "dps": "dps", "strength": "str", "agility": "agi",
    "intellect": "int", "stamina": "sta", "spirit": "spi", "spell power": "sp",
    "attack power": "ap", "critical strike": "crit", "crit": "crit",
    "hit rating": "hit", "haste rating": "haste", "expertise rating": "exp",
    "armor penetration": "arp", "armor pentration": "arp", "defense rating": "def",
    "dodge rating": "dodge", "parry rating": "parry", "block rating": "block",
    "block value": "blockval", "resilience": "res", "resilence": "res",
    "mana per 5 sec": "mp5", "min - max damage": None, "level": None,
}
STATS = {"Strength": "str", "Agility": "agi", "Intellect": "int", "Stamina": "sta", "Spirit": "spi"}
RATINGS = [
    (r"critical strike rating", "crit"), (r"hit rating", "hit"), (r"haste rating", "haste"),
    (r"expertise rating", "exp"), (r"defense rating", "def"), (r"dodge rating", "dodge"),
    (r"parry rating", "parry"), (r"block rating", "block"), (r"resilience rating", "res"),
    (r"armor penetration rating", "arp"), (r"mana per 5 sec", "mp5"),
    (r"spell power", "sp"), (r"healing power|healing done", "heal"), (r"attack power", "ap"),
    (r"block value", "blockval"),
]


def get_json(url, attempts=3):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            if attempt + 1 == attempts:
                raise
            time.sleep(1 + attempt)


def parse_wiki(item_id):
    url = WIKI_API + "?" + urllib.parse.urlencode({
        "action": "parse", "page": NAMES[item_id], "prop": "wikitext", "format": "json", "redirects": "1",
    })
    data = get_json(url)
    if "parse" not in data:
        return None
    text = data["parse"]["wikitext"]["*"]
    if "Item statistics by level" not in text:
        return None
    text = text.split("Item statistics by level", 1)[1]
    rows, header = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("!"):
            header = [HEADER.get(x.strip().lower()) for x in line[1:].split("!!")]
        elif line.startswith("|") and line[1:2].isdigit() and header:
            cells = line[1:].split("||")
            if len(cells) != len(header):
                continue
            level = int(cells[0])
            row = {"st": {}}
            for key, value in zip(header[1:], cells[1:]):
                if not key:
                    continue
                value = value.replace(",", "").strip()
                if not re.fullmatch(r"[\d.]+", value):
                    continue
                number = float(value)
                if number == 0:
                    continue
                if key in ("ar", "dps"):
                    row[key] = int(number) if key == "ar" else number
                else:
                    row["st"][key] = int(number)
            rows.append([level, row])
    return rows if len(rows) == 80 else None


def strip_tags(html):
    html = re.sub(r"<br\s*/?>", "\n", html)
    html = re.sub(r"<[^>]+>", "", html)
    return html.replace("&nbsp;", " ").replace("&amp;", "&")


def parse_wowhead(item_id, level):
    data = get_json(WOWHEAD.format(id=item_id, level=level))
    text = strip_tags(data.get("tooltip") or "")
    row = {"st": {}}
    m = re.search(r"(\d+)\s+Armor", text)
    if m:
        row["ar"] = int(m.group(1))
    m = re.search(r"\(([\d.]+)\s+damage per second\)", text)
    if m:
        row["dps"] = float(m.group(1))
    for value, name in re.findall(r"\+(\d+)\s+(Strength|Agility|Intellect|Stamina|Spirit)", text):
        row["st"][STATS[name]] = row["st"].get(STATS[name], 0) + int(value)
    for line in text.splitlines():
        low = line.lower()
        m = re.search(r"(?:by|up to|restores)\s+(\d+)", low)
        if not m:
            continue
        value = int(m.group(1))
        for pattern, key in RATINGS:
            if re.search(pattern, low):
                row["st"][key] = row["st"].get(key, 0) + value
                break
    return [level, row]


def fetch_wowhead(item_id):
    levels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for row in pool.map(lambda lv: parse_wowhead(item_id, lv), range(1, 81)):
            levels.append(row)
    return levels


def compress(levels):
    out, previous = [], None
    for level, row in levels:
        clean = {"st": {k: v for k, v in sorted((row.get("st") or {}).items()) if v}}
        if row.get("ar"):
            clean["ar"] = row["ar"]
        if row.get("dps"):
            clean["dps"] = row["dps"]
        if clean != previous:
            out.append([level, clean])
            previous = clean
    return out


def scale_weapon_dps(rows, base_dps, base_max):
    """El tooltip de Wowhead escala las estadísticas pero no el daño de las reliquias PvP.
    Todas comparten la curva de DPS de nivel; se normaliza por su DPS a nivel 80."""
    max_dps = rows[-1][1].get("dps") or 0
    if not max_dps or not base_max:
        return rows
    factor = max_dps / base_max
    for level, row in rows:
        if base_dps.get(level):
            row["dps"] = round(base_dps[level] * factor, 1)
    return rows


def main():
    result = {}
    base = parse_wiki("42943")
    base_dps = {level: row.get("dps", 0) for level, row in base}
    base_max = base_dps.get(80, 0)
    for item_id in legacy["heirlooms"]:
        rows = parse_wiki(item_id)
        if rows is None and item_id in ("42991", "42992"):
            rows = [[1, {"st": {}}] for _ in range(80)]
        if rows is None:
            rows = scale_weapon_dps(fetch_wowhead(item_id), base_dps, base_max)
        result[item_id] = compress(rows)
        print(item_id, NAMES[item_id], len(result[item_id]), "tramos")
    OUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("escrito", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
