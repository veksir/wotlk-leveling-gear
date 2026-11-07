# WotLK Leveling Gear

**English** | [Español](README.es.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
![World of Warcraft](https://img.shields.io/badge/WotLK-3.3.5-0b2230)
![Static site](https://img.shields.io/badge/static-HTML%20%2B%20JS-75d7ef)

A static, client-side guide that answers one question:

> What is the strongest item I can equip in each slot at my current level?

It supports all 10 WotLK classes, 31 specializations, levels 1–80, Horde/Alliance, and both English and Spanish.

![English interface](docs/screenshot-en.png)

## Features

- **Full equipment sheet**: head, neck, shoulders, back, chest, wrists, hands, waist, legs, feet, rings, trinkets, main hand, off hand, ranged, and class relic.
- **Best item per slot** with 2, 5, or 10 alternatives, ranked by score (not by source).
- **How to get it**: every item shows its source (quest, vendor, dungeon boss with drop chance, raid, rare drop) and links to its EVOWOW page.
- **"Why this item?"** per slot: score breakdown by stat, armor-type penalty, comparison with the next alternative, and a warning when a higher item level option is hidden or weaker.
- **Content modes**: "No raids" (default) or "With raids", raid phase 1–4 or All, and a separate "PvP only" mode (PvE is the default; PvP gear is never mixed into PvE recommendations).
- **Legendary items included**: legendaries are scored like any other item and appear when they are the best option; raid legendaries require "With raids". The page shows the top choices per slot, not a full legendary catalog.
- **Proc-aware trinkets**: on-use and proc effects are averaged by duration and cooldown (≈). Curated trinket lists from the guides take priority in their slot.
- **Guide-recommended gems and sockets**: each socket is valued with the best gem recommended for the spec, and socket bonuses count for half.
- **Tier 10 set bonuses**: the estimated 2-piece or 4-piece bonus is shared only among the pieces the guide recommends, not every piece of the set.
- **Class relics**: sigils, totems, idols, and librams are normal gear and are recommended when the guide lists them. They are separate from leveling heirlooms.
- **Level 80 caps**: hit and expertise totals are shown; stats above the cap count for 15 %.
- **Loot browser**: enter what your character is wearing (or load the recommended set), pick a dungeon or raid, and see every item it can drop for your class and spec with the % change over your equipped piece. Off-spec items are hidden by default and can be revealed with a toggle.
- **Faction-aware**: quests and vendors are filtered for Horde or Alliance.
- **Bilingual UI**: Spanish and English.
- **Item details**: icon, quality color, item level, required level, relevant stats, and source.
- **Optional heirlooms**: all 35 leveling heirlooms have exact stats per level and armor-type changes before level 40. They stay out of recommendations unless you mark “Include leveling heirlooms I already own”, because their vendors require level-80 currency.
- **EVOWOW tooltips** for every item.
- **Responsive layout** and persisted selection (`localStorage`).
- **No backend** and no build step required to view the page.

## How it works

1. `scripts/fetch_raw.py` downloads the raw item and zone data, `scripts/fetch_heirloom_stats.py` adds level-by-level heirloom stats, and `scripts/fetch_atlasloot.py` + `scripts/build_loot.py` add per-boss loot tables for WotLK (Ulduar, Trial of the Crusader, Icecrown Citadel, heroic dungeons, 10/25) from AtlasLootClassic.
2. `scripts/build_item_db.py` normalizes items, stats (including averaged trinket procs, on-use effects, sockets, and socket bonuses), required levels, armor/weapon metadata, and sources.
3. `scripts/build_recommendations.py` emits the item database, spec definitions, stat weights, reference gems, T10 set bonuses, curated trinkets/relics, and the dungeon list. Level-80 weights follow each spec's Icy Veins priority, calibrated with WowSims where available; below 80 the role weights keep leveling gear sensible. Heirlooms are ranked only when the “already own” toggle is enabled; class relics are normal gear. The ranking itself runs in the browser, so mode, phase, PvP, and faction filters apply instantly.
4. `scripts/build_page.py` injects the generated JSON into `src/template.html` and writes `tolltip.html`.

The ranking is a practical heuristic, not a combat simulator: it sorts by a weighted stat score (item level only breaks ties), uses per-spec priorities at level 80 and role weights while leveling, penalizes armor types that are not ideal for the class, averages trinket procs and on-use effects by duration and cooldown, applies guide-recommended gems per socket, shares the T10 set bonus only among the recommended pieces, applies hit/expertise caps at level 80, and compares two-handers against one-hand + off-hand. A two-hander blocks the off-hand slot unless the spec uses Titan's Grip. Epic items with no recorded source at item level 213 or higher are treated as raid loot ("likely raid"). Enchants and random-enchant items are not scored yet.

## Quick start

Clone the repository and open `tolltip.html` in a browser.

Internet access is required for Google Fonts and EVOWOW item tooltips. The page itself works without a local server.

## Build from source

Requirements:

- Python 3.10+
- Playwright + Chromium for the smoke test

```bash
python -m pip install playwright
python -m playwright install chromium

python scripts/fetch_raw.py
python scripts/fetch_heirloom_stats.py
python scripts/fetch_atlasloot.py
python scripts/build_loot.py
python scripts/build_item_db.py
python scripts/build_recommendations.py
python scripts/build_page.py

python tests/smoke.py
python tests/check_reference.py
python tests/check_reference.py --ref=reference_bis_ids.json
python tests/heirlooms.py
python tests/spec_weights.py
python tests/features.py
python tests/reference_ids.py
```

`build_page.py` writes `tolltip.html` in the repository and, when available, to `~/Desktop/tolltip.html`. `check_reference.py` audits all 31 level-80 specializations against the Icy Veins BiS lists in `tests/reference_bis.json` (or `--ref=reference_bis_ids.json` for the ID-based reference) and reports hit/exact rates; `heirlooms.py` covers level scaling, off-spec filtering, two-handed weapons, and relic search; `features.py` covers gems/sockets, set bonuses, and curated relics; `reference_ids.py` validates the ID-based reference; `spec_weights.py` checks all 31 level-80 specializations.

## Project structure

```text
.
├── data/                  # generated gear_data.json (raw data is ignored)
├── docs/                  # README screenshots
├── legacy/                # previous heirloom-only implementation
├── scripts/               # data pipeline, ranking, and page builder
├── src/                   # HTML/CSS/JS template
├── tests/                 # Playwright smoke and regression tests
├── tolltip.html           # generated standalone page
├── CONTRIBUTING.md        # contribution guide (English)
├── CONTRIBUTING.es.md     # contribution guide (Spanish)
└── LICENSE
```

## Data and attribution

The item database is derived from [wow-classic-items](https://github.com/nexus-devs/wow-classic-items):

- `data/json/data.json`
- `data/json/zones.json`

Per-boss loot tables come from [AtlasLootClassic](https://github.com/Hoizame/AtlasLootClassic).

Item tooltips and icons are loaded from [EVOWOW](https://wotlk.evowow.com/).

Heirloom stats come from the [WoWWiki archive](https://wowwiki-archive.fandom.com/) level tables and the [Wowhead WotLK tooltip API](https://www.wowhead.com/wotlk). Level-80 stat priorities follow [Icy Veins WotLK Classic](https://www.icy-veins.com/wotlk-classic/) and, where available, are calibrated with [WowSims](https://wowsims.github.io/wotlk/) EP values; `data/spec_weights.json` records the source and priority for every specialization, and `data/reference_spec_stats.json` keeps the raw reference values. Guide-recommended gems, T10 set bonuses, trinkets, and class relics are stored in `data/reference_gems.json`, `data/reference_sets.json`, and `data/reference_trinkets.json`, with sources recorded in each file.

This project is not affiliated with Blizzard Entertainment. World of Warcraft and Wrath of the Lich King are trademarks of Blizzard Entertainment.

## Limitations

- The dataset is based on WotLK Classic; a few original 3.3.5 sources may be missing or labeled as “Other source”.
- "No raids" excludes raid loot and raid quest chains; "With raids" includes them.
- Stat weights are role-based while leveling and follow Icy Veins priorities, calibrated with WowSims where available, at level 80. They are designed to be useful, not to replace a full BiS simulator; haste soft caps and talent interactions are not modeled.
- Gem values assume the guide-recommended gem for each socket and count socket bonuses at half. Enchants, random enchants, and some trinket/set interactions are still simplified.
- The T10 set bonus is an estimate shared only among the pieces recommended by the guide; it is not a full simulation of 2-piece/4-piece uptime.
- Off-spec loot is hidden by default. The toggle reveals it faded so you can judge cross-spec upgrades without mixing it into the recommendation.
- Leveling heirlooms are not recommended by default: Emblems of Heroism and Wintergrasp Marks are earned at level 80. Enable “Include leveling heirlooms I already own” only if you actually have them. Class relics are separate and do appear in the ranking.
- Some very low-level slots may legitimately have no item with known stats.
- The page shows the best item plus alternatives per slot, not every item. A legendary only appears if it ranks for the selected spec, level, faction, mode, phase, and PvP filter. Low-level legendaries or ones that depend on an unmodeled setup may not appear.
- Weapon combinations cover dual-wield Frost Death Knights and Fury's Titan's Grip (two two-handed weapons). Other special setups remain simplified, so some BiS items may still be missing.
- The generated page embeds the item data, so `tolltip.html` is intentionally large (around 5.1 MB).

## Contributing

Bug reports, item corrections, translations, and UI improvements are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © 2026 veksir
