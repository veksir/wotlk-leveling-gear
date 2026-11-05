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
- Playwright with Chromium for the smoke test

```bash
git clone https://github.com/veksir/wotlk-leveling-gear.git
cd wotlk-leveling-gear
python -m pip install playwright
python -m playwright install chromium
```

Build the data and page:

```bash
python scripts/fetch_raw.py
python scripts/fetch_atlasloot.py
python scripts/build_loot.py
python scripts/build_item_db.py
python scripts/build_recommendations.py
python scripts/build_page.py
```

Run the smoke test:

```bash
python tests/smoke.py
```

## Where to make changes

- `src/template.html`: HTML, CSS, and client-side JavaScript. This is the source for the page.
- `scripts/build_item_db.py`: item parsing, stats, required levels, armor/weapon metadata, and sources.
- `scripts/build_recommendations.py`: class/spec rules, faction filtering, armor/weapon eligibility, scoring, and ranking.
- `scripts/build_page.py`: injects data into the template and writes `tolltip.html`.
- `tests/smoke.py`: browser smoke test.

Do **not** edit `tolltip.html` by hand. It is generated. After changing the template or data, run the build again.

## Data rules

- Never commit `data/raw_items.json`, `data/raw_zones.json`, or `data/items.json`. They are ignored on purpose.
- Commit the generated `data/gear_data.json` when recommendations change.
- Keep item sources and faction availability accurate. If a source is unknown, label it as “Other source” rather than guessing.
- Do not add raid loot to the main leveling ranking unless the project scope changes.

## Interface rules

- Add new UI text to the `I18N` object in `src/template.html` for **both** Spanish and English.
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
- [ ] `python tests/smoke.py` passes.
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
