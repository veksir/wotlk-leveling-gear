# Contributing

**English** | [Español](CONTRIBUTING.es.md)

Thanks for taking the time to improve WotLK Leveling Gear. This project is a static page with a Python data pipeline, so most changes fall into one of three areas: item data, ranking logic, or the interface.

## Ways to contribute

- Report item mistakes (wrong item, wrong level, wrong source, wrong faction).
- Improve stat weights or weapon/armor filtering.
- Add or fix translations.
- Improve layout, accessibility, or mobile behavior.
- Fix bugs or improve the build scripts.

## Before you start

For small fixes, open a pull request directly. For larger changes (new features, data source changes, scoring redesign), open an issue first so the approach can be discussed.

## Setup

Requirements:

- Python 3.10+
- Node.js 22.12+ (or 20.19+) and npm
- Playwright with Chromium for the smoke test

```bash
git clone https://github.com/veksir/wotlk-leveling-gear.git
cd wotlk-leveling-gear
npm install
python -m pip install playwright
python -m playwright install chromium
```

Build the data and page:

```bash
python scripts/fetch_raw.py
python scripts/fetch_heirloom_stats.py
python scripts/fetch_atlasloot.py
python scripts/build_loot.py
python scripts/build_item_db.py
python scripts/build_recommendations.py
python scripts/build_page.py
```

Run the smoke and regression tests:

```bash
python tests/smoke.py
python tests/sockets.py
python tests/gems.py
python tests/optimizer.py
python tests/check_reference.py
python tests/check_reference.py --ref=reference_bis_ids.json
python tests/check_reference.py --min=497
python tests/fresh80.py
python tests/heirlooms.py
python tests/spec_weights.py
python tests/features.py
python tests/reference_sets.py
python tests/reference_ids.py
```

## Where to make changes

- `src/index.html`: page shell and DOM. It loads `styles/app.css` and `js/main.js`.
- `src/styles/app.css`: all page styles.
- `src/js/`: client-side ES modules (`core`, `data`, `engine`, `heroic`, `equipment`, `format`, `loot`, `bis`, `render`, `main`). `data.js` imports `data/gear_data.json`; `main.js` wires events and exposes the test globals.
- `scripts/build_item_db.py`: item parsing, stats, required levels, armor/weapon metadata, and sources.
- `scripts/build_recommendations.py`: class/spec rules, faction filtering, armor/weapon eligibility, scoring, and ranking. Level-80 priorities live in `data/spec_weights.json`.
- `scripts/fetch_heirloom_stats.py`: level-by-level heirloom stats from the WoWWiki archive and Wowhead.
- `scripts/build_page.py`: runs the Vite single-file build and copies `dist/index.html` to `tolltip.html`.
- `tests/smoke.py`: browser smoke test.
- `tests/sockets.py`: socket colors, meta sockets, and exceptions such as item 23232.
- `tests/gems.py`: meta-gem activation, gem choice by color, and socket bonuses.
- `tests/optimizer.py`: level-80 beam search, performance (<750 ms), and that level 79 does not use it.
- `tests/check_reference.py`: Icy Veins BiS accuracy audit for all 31 level-80 specializations; `--ref=reference_bis_ids.json` uses the ID-based reference, `--min=497` enforces the gate, and `--strict` is the final 518/518 target.
- `tests/reference_bis_ids.json`: ID-based reference with alternatives; validated by `reference_ids.py`.
- `tests/heirlooms.py`: heirloom scaling, off-spec filtering, two-handed off-hand rules, and relic search.
- `tests/features.py`: gems/sockets, T10 set bonuses, and curated trinkets/class relics.
- `tests/reference_sets.py`: validates the T10 set pieces used by the set bonus.
- `tests/reference_ids.py`: validates that every ID reference exists, has the right name, and belongs to a compatible slot.
- `tests/spec_weights.py`: all 31 level-80 specializations.
- `tests/fresh80.py`: Fresh 80 coverage for all 31 specializations and both factions, plus the checkbox, route, persistence, and disabling in PvP/With raids.

Do **not** edit `tolltip.html` by hand. It is generated. After changing the source modules, styles, or data, run the build again.

## Data rules

- Never commit `data/raw_items.json`, `data/raw_zones.json`, or `data/items.json`. They are ignored on purpose.
- Commit the generated `data/gear_data.json` when recommendations change.
- Commit `data/heirloom_stats.json` when heirloom stats change and `data/spec_weights.json` when priorities change. Every spec entry keeps its source (Icy Veins and, when applicable, WowSims) and priority; `data/reference_spec_stats.json` holds the raw calibration values.
- Keep item sources and faction availability accurate. If a source is unknown, label it as “Other source” rather than guessing.
- For badge, reputation, and PvP vendors, set `source.cur` and `source.cost` in `scripts/build_item_db.py`; `build_item_db.py` warns about level-80 vendors without a known currency, and `tests/fresh80.py` rejects Frost, raid tokens, raid gear, and PvP gear.
- When updating `tests/reference_bis_ids.json`, make sure every referenced item exists in the dataset and belongs to the slot where the guide lists it. Run `python tests/reference_ids.py`.
- Guide-recommended gems, T10 set bonuses, trinkets, and class relics live in `data/reference_gems.json`, `data/reference_sets.json`, and `data/reference_trinkets.json`. Meta gems and their activation cost live in `data/reference_meta_gems.json`. Keep their `source`/`contrast_source` fields and update the generated `data/gear_data.json`.
- Do not add raid loot to the main leveling ranking unless the project scope changes.

## Interface rules

- Add new UI text to the `I18N` object in `src/js/core.js` for **both** Spanish and English.
- Keep slot, stat, source, and bracket labels consistent between languages.
- Check the page at desktop and mobile widths.
- Preserve the item tooltip behavior (`rel="lvl=N noopener"` for heirlooms, `rel="noopener"` for regular items).

## Commit style

Use short, atomic commits. Conventional Commits are preferred:

```text
feat(ui): add faction selector
feat(engine): filter quests by faction
fix(data): correct required level for item 52572
test: cover English language toggle
docs: update build instructions
```

Avoid mixing unrelated changes in one commit.

## Pull request checklist

- [ ] The page builds with `python scripts/build_page.py`.
- [ ] `python tests/smoke.py`, `tests/sockets.py`, `tests/gems.py`, `tests/optimizer.py`, `tests/check_reference.py`, `tests/check_reference.py --ref=reference_bis_ids.json`, `tests/fresh80.py`, `tests/heirlooms.py`, `tests/spec_weights.py`, `tests/features.py`, `tests/reference_sets.py`, and `tests/reference_ids.py` pass.
- [ ] `data/gear_data.json` and `tolltip.html` are regenerated if needed.
- [ ] Both Spanish and English UI strings are updated.
- [ ] No raw data, caches, or `__pycache__` files are included.
- [ ] Screenshots are attached for visible UI changes.

## Reporting an item issue

Please include:

```text
Class/Spec:
Level:
Faction:
Slot:
Expected item:
Current item:
Why it is wrong:
Screenshot (optional):
```

Item issues are much easier to fix with the exact class, spec, level, and faction.

## License

By contributing, you agree that your changes are released under the [MIT License](LICENSE).
