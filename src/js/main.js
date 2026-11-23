import { DATA } from "./data.js";
import * as core from "./core.js";
import * as engine from "./engine.js";
import * as heroic from "./heroic.js";
import * as equipment from "./equipment.js";
import * as format from "./format.js";
import * as loot from "./loot.js";
import * as bis from "./bis.js";
import * as renderer from "./render.js";
const { runtime, STORE, I18N, SLOT_LABEL, STAT_LABEL, STATS_EN, FACTION_HEIRLOOM, $, classesEl, specsEl, factionsEl, slotsEl, levelInput, levelRange, levelNumber, bracketLabel, classNote, statList, statsHint, dungeonList, heirloomPanel, heirloomList, slotCount, load, save, esc, state, STAT_ORDER, QUALITY_COLOR, allSpecsFor, specFor, clampLevel, t, applyLanguage, armorText, bracketName, bracketAdvice, bracketFor, qColor, ICON_LOCAL, iconSrc, iconHtml, itemLink, statLine, ITEM_URL, L, gearItem, itemHands, levelItem, zoneOf, specSlots, poolOfSlot, gearKey, equippedMap, currentSpec, titanGrip, equippedMainTwoHand, clearLootUndo, renderLootUndo, pctDiff, renderSeg, persist, eqNorm, refreshTimer, scheduleRefresh } = core;
const { ENG, GEAR_ITEMS, ARMOR_KEYS, itemFactions, armorUnlock, preferredArmor, armorFactor, weightsFor, gemContext, scoreParts, isRelevant, availableLevel, poolsFor, ARMOR_PENALTY_SCALE, softArmor, SUFFIX_SLOPE, SUFFIXES, withSuffix, FRESH_CURRENCIES, FROST_CUR, raidGated, freshAccessible, evalItem, BEAM_SLOTS, jointOptimize, computeGear } = engine;
const { HEROIC_REQ, HEROIC_REQ_DEFAULT, heroicReqCache, heroicRequirement, isHeroicOnlyDrop, equippedItemLevel, averageItemLevel, heroicAccess, fmtIlvl } = heroic;
const { SHIELD_CLASSES, DW_CLASSES, CLASS_RELIC, CLASS_RANGED, equipPools, evalEquip, candCache, candidates, equippedEntry, lootFilterForSlot, slotScore, targetEquipSlot } = equipment;
const { partLabel, reasonText, rivalNote, whyHtml, CURRENCY_LABEL, currencyLabel, goldLabel, obtainInfo, badgeHtml, DIFF_LABEL, diffLabel, normName, dungeonByName, bisLabel, rankClass, rankPill } = format;
const { equipLoot, setEquipped, renderEquip, syncEquipHighlight, autoDungeon, LOOT_SLOT_LABEL, lootSlotText, lootFilterValues, lootMatchesSlot, lootSlotLabel, collapsedBosses, lootHoverCard, lootHoverTimer, hideLootHover, showLootHover, lootPartVal, lootWhyHtml, capWarning, renderLoot, bindLootEvents } = loot;
const { BIS_PHASES, BIS_F80, BIS_TABS, bisTabShort, bisTabLabel, bisOpts, BIS_ALTS, bisCache, bisCtx, bisRows, bisGuideFor, applyRefBis, bisData, bisCompletes, bisPairLabel, bisOwned, GEM_COLORS, ES_MARK, NOTE_EN, noteText, gemColorName, gemLink, enchLink, refFor, gemPlan, gemColorOf, bisFx, enchValueText, renderGems, bisScore, ROUTE_MIN_GAIN, rowSlots, rowPool, rowCurrent, rowUpgrades, upLine, gameId, renderRoute, sourceGroup, renderPlan, bisLater, bisLaterHtml, bisCard, GEM_FAMILY, gemColors, colorWord, colorNoun, metaPlan, BIS_FIRST, bisItemStatus, bisStatusText, bisFindShow, bisFindMatches, bisFindSearch, renderBisFind, renderBis } = bis;
const { renderClasses, renderOptions, renderSpecs, renderFactions, updateClassNote, setLevel, renderSlot, renderCaps, renderHeroicStatus, renderSlots, renderStats, renderDungeons, renderHeirlooms, baseWeights, renderWeights, renderEqTools, arrangeSections, renderNav } = renderer;

runtime.render = renderer.render;

let eqNameIndex = null;

function eqIndex() {
  if (eqNameIndex) return eqNameIndex;
  eqNameIndex = new Map();
  for (const id in GEAR_ITEMS) { const k = eqNorm(GEAR_ITEMS[id].n); const cur = eqNameIndex.get(k); if (!cur || GEAR_ITEMS[id].ilvl > GEAR_ITEMS[cur].ilvl) eqNameIndex.set(k, id); }
  return eqNameIndex;
}

function exportEquipText() {
  const spec = currentSpec(), g = equippedMap(), labels = SLOT_LABEL[state.lang] || SLOT_LABEL.es;
  const lines = ["# WotLK Leveling Gear · " + state.cls + " " + state.spec + " · " + state.faction];
  specSlots(spec).forEach((sl) => { const it = g[sl] && gearItem(g[sl]); if (it) lines.push((labels[sl] || sl) + ": " + it.n + " (" + g[sl] + ")"); });
  return lines.join("\n");
}

function parseEquipText(text) {
  const spec = currentSpec(), rev = {};
  ["es", "en"].forEach((lg) => Object.entries(SLOT_LABEL[lg]).forEach(([k, v]) => { rev[eqNorm(v)] = k; }));
  const set = {}, bad = [], extra = { ring: 0, trinket: 0 };
  String(text || "").split(/\r?\n/).forEach((raw) => {
    const line = raw.trim();
    if (!line || line.startsWith("#")) return;
    const i = line.indexOf(":");
    const label = i > 0 ? eqNorm(line.slice(0, i)) : "", body = i > 0 && rev[label] ? line.slice(i + 1) : line;
    let slot = i > 0 ? rev[label] : null;
    let id = (/\((\d{3,6})\)/.exec(body) || /\b(\d{4,6})\b/.exec(body) || [])[1];
    if (!id || !gearItem(id)) id = eqIndex().get(eqNorm(body.replace(/\(\d+\)/g, "")));
    const it = id && gearItem(id);
    if (!it) { bad.push(line); return; }
    if (!slot) {
      const pk = equipPools(it, spec, 80);
      if (!pk.length) { bad.push(line); return; }
      slot = pk.includes("ring") ? "ring" + (++extra.ring > 1 ? 2 : 1) : pk.includes("trinket") ? "trinket" + (++extra.trinket > 1 ? 2 : 1) : pk[0];
    }
    set[slot] = String(id);
  });
  return { set, bad };
}

async function eqCopy(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch (e) {
    const ta = $("eqText"); ta.value = text; ta.select();
    try { return document.execCommand("copy"); } catch (e2) { return false; }
  }
}

function eqShareUrl() {
  const payload = { c: state.cls, s: state.spec, f: state.faction, l: state.level, g: equippedMap() };
  return location.href.split("#")[0] + "#eq=" + btoa(unescape(encodeURIComponent(JSON.stringify(payload))));
}

function applyEquipHash() {
  const m = /^#eq=(.+)$/.exec(location.hash || "");
  if (!m) return false;
  try {
    const d = JSON.parse(decodeURIComponent(escape(atob(m[1]))));
    if (!DATA.specs[d.c + "|" + d.s]) return false;
    state.cls = d.c; state.spec = d.s;
    if (DATA.factions.includes(d.f)) state.faction = d.f;
    if (d.l >= 1 && d.l <= 80) state.level = d.l;
    const g = {};
    Object.entries(d.g || {}).forEach(([sl, id]) => { if (gearItem(String(id))) g[sl] = String(id); });
    state.gear[d.c + "|" + d.s] = g;
    persist();
    history.replaceState(null, "", location.href.split("#")[0]);
    return true;
  } catch (e) { return false; }
}

const eqMsg = (m) => { $("eqIoMsg").textContent = m; };
$("eqExport").addEventListener("click", async () => {
  const text = exportEquipText();
  $("eqIo").hidden = false; $("eqText").value = text;
  const n = text.split("\n").length - 1;
  eqMsg(n ? ((await eqCopy(text)) ? L("Copiado: " + n + " piezas.", "Copied: " + n + " pieces.") : L("Selecciona el texto y cópialo.", "Select the text and copy it.")) : L("No hay piezas en tu equipo.", "There are no pieces in your gear."));
});
$("eqImport").addEventListener("click", () => {
  $("eqIo").hidden = false; $("eqText").value = ""; $("eqText").focus();
  eqMsg(L("Pega aquí tu lista (una pieza por línea) y pulsa Aplicar.", "Paste your list here (one piece per line) and press Apply."));
});
$("eqApply").addEventListener("click", () => {
  const r = parseEquipText($("eqText").value), n = Object.keys(r.set).length;
  if (!n) { eqMsg(L("No se reconoció ninguna pieza.", "No piece was recognised.")); return; }
  clearLootUndo();
  state.gear[gearKey()] = r.set; persist(); runtime.render();
  eqMsg(L("Importadas " + n + " piezas" + (r.bad.length ? "; sin reconocer: " + r.bad.length : "") + ".", "Imported " + n + " pieces" + (r.bad.length ? "; not recognised: " + r.bad.length : "") + "."));
});
$("eqLink").addEventListener("click", async () => {
  const url = eqShareUrl();
  $("eqIo").hidden = false; $("eqText").value = url;
  eqMsg((await eqCopy(url)) ? L("Enlace copiado.", "Link copied.") : L("Selecciona el enlace y cópialo.", "Select the link and copy it."));
});

/* ---------- Navegación entre secciones y filtros plegables ---------- */
STORE.deck = "wotlk-gear-deck-collapsed";
state.deckCollapsed = load(STORE.deck, "0") === "1";


levelRange.addEventListener("input", (e) => setLevel(e.target.value));
levelInput.addEventListener("change", (e) => setLevel(e.target.value));
levelInput.addEventListener("blur", (e) => {
  if (Number(e.target.value) !== state.level) setLevel(e.target.value);
});

$("resetBtn").addEventListener("click", () => {
  Object.assign(state, { cls: "Warrior", spec: "Arms", level: 20, scope: "noraid", phase: 0, pvp: false, alts: 2, dungeon: 0, lootSlot: "", lootSort: "boss", onlyUp: false, showOffspec: false, showHeirlooms: false, fresh: false, bisPhase: "F80" });
  clearLootUndo();
  persist();
  renderClasses();
  renderSpecs();
  renderFactions();
  renderOptions();
  runtime.render();
});

$("dungeonSelect").addEventListener("change", (e) => { state.dungeon = Number(e.target.value) || 0; persist(); runtime.render(); });
$("lootSlot").addEventListener("change", (e) => { state.lootSlot = e.target.value; persist(); runtime.render(); });
$("lootSort").addEventListener("change", (e) => { state.lootSort = e.target.value; persist(); runtime.render(); });
$("lootUndoBtn").addEventListener("click", () => {
  if (!runtime.lastEquip || runtime.lastEquip.key !== gearKey()) return;
  state.gear[gearKey()] = runtime.lastEquip.gear;
  runtime.lastEquip = null;
  persist();
  runtime.render();
});
$("onlyUp").addEventListener("change", (e) => { state.onlyUp = e.target.checked; persist(); runtime.render(); });
$("showOffspec").addEventListener("change", (e) => { state.showOffspec = e.target.checked; persist(); runtime.render(); });
$("showHeirlooms").addEventListener("change", (e) => { state.showHeirlooms = e.target.checked; persist(); runtime.render(); });
$("fresh80").addEventListener("change", (e) => {
  state.fresh = e.target.checked;
  if (state.fresh) { state.scope = "noraid"; state.pvp = false; }
  persist();
  renderOptions();
  runtime.render();
});
$("eqUseRec").addEventListener("click", () => {
  if (!runtime.lastGear) return;
  const spec = DATA.specs[state.cls + "|" + state.spec], g = {};
  specSlots(spec).forEach((sl) => { const e = runtime.lastGear.slots[sl] && runtime.lastGear.slots[sl].list[0]; if (e) g[sl] = e.id; });
  const mh = g.mainhand && gearItem(g.mainhand);
  if (mh && itemHands(mh) === 2 && !titanGrip(spec, state.level)) delete g.offhand;
  clearLootUndo();
  state.gear[gearKey()] = g;
  persist();
  runtime.render();
});
$("eqClear").addEventListener("click", () => { clearLootUndo(); state.gear[gearKey()] = {}; persist(); runtime.render(); });

document.querySelectorAll(".lang-switch button").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.lang = btn.dataset.lang;
    persist();
    renderFactions();
    renderOptions();
    runtime.render();
  });
});

applyEquipHash();
state.level = clampLevel(state.level);
renderClasses();
renderSpecs();
renderFactions();
renderOptions();
runtime.render();

Object.assign(window, { DATA }, core, engine, heroic, equipment, format, loot, bis, renderer, { exportEquipText, parseEquipText, eqShareUrl, applyEquipHash, eqNorm, eqIndex, eqMsg });
