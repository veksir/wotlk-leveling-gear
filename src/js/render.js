import { DATA } from "./data.js";
import {
  state, $, t, L, esc, SLOT_LABEL, STATS_EN, STAT_ORDER, FACTION_HEIRLOOM, classesEl,
  specsEl, factionsEl, slotsEl, levelInput, levelRange, levelNumber,
  bracketLabel, classNote, statList, statsHint, dungeonList, heirloomPanel,
  heirloomList, slotCount, allSpecsFor, specFor, clampLevel, armorText,
  bracketName, bracketAdvice, bracketFor, qColor, iconHtml, itemLink, statLine, ITEM_URL,
  specSlots, runtime, persist, renderSeg, scheduleRefresh, clearLootUndo, load, save, STORE, applyLanguage
} from "./core.js";
import { ENG, computeGear } from "./engine.js";
import { averageItemLevel, fmtIlvl } from "./heroic.js";
import { partLabel, rivalNote, whyHtml, badgeHtml, obtainInfo, dungeonByName, bisLabel, rankPill } from "./format.js";
import { renderLoot, renderEquip } from "./loot.js";
import { renderBis, bisCache } from "./bis.js";
import { candCache } from "./equipment.js";
function renderClasses() {
  classesEl.innerHTML = "";
  DATA.classOrder.forEach((name) => {
    const meta = DATA.classMeta[name];
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.style.setProperty("--chip", meta.color);
    btn.setAttribute("aria-pressed", String(name === state.cls));
    btn.textContent = name;
    btn.addEventListener("click", () => {
      state.cls = name;
      state.spec = allSpecsFor(name)[0];
      if (state.level < DATA.classMeta[name].min) state.level = DATA.classMeta[name].min;
      clearLootUndo();
      persist();
      renderClasses();
      renderSpecs();
      render();
    });
    classesEl.appendChild(btn);
  });
}


function renderOptions() {
  $("showHeirlooms").checked = state.showHeirlooms;
  $("fresh80").checked = state.fresh;
  $("fresh80").disabled = state.level !== 80 || state.pvp;
  $("fresh80").title = t("fresh80Hint");
  const set = (key, fn) => (v) => { fn(v); persist(); renderOptions(); render(); };
  renderSeg($("modes"), [{ value: "noraid", label: t("modeNoRaid") }, { value: "raid", label: t("modeRaid") }], state.scope, set("scope", (v) => { state.scope = v; if (v === "raid") state.fresh = false; }));
  renderSeg($("phases"), [1, 2, 3, 4].map((n) => ({ value: n, label: String(n) })).concat([{ value: 0, label: t("phaseAll") }]), state.phase, set("phase", (v) => { state.phase = v; }));
  renderSeg($("pvps"), [{ value: false, label: t("pvpOff") }, { value: true, label: t("pvpOn") }], state.pvp, set("pvp", (v) => { state.pvp = v; if (v) state.fresh = false; }));
  renderSeg($("alts"), [2, 5, 10].map((n) => ({ value: n, label: String(n) })), state.alts, set("alts", (v) => { state.alts = v; }));
}


function renderSpecs() {
  specsEl.innerHTML = "";
  allSpecsFor(state.cls).forEach((name) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "seg-btn";
    btn.setAttribute("aria-pressed", String(name === state.spec));
    btn.textContent = name;
    btn.addEventListener("click", () => {
      state.spec = name;
      clearLootUndo();
      persist();
      renderSpecs();
      render();
    });
    specsEl.appendChild(btn);
  });
  updateClassNote();
}


function renderFactions() {
  factionsEl.innerHTML = "";
  DATA.factions.forEach((faction) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "seg-btn";
    btn.dataset.faction = faction;
    btn.setAttribute("aria-pressed", String(faction === state.faction));
    btn.textContent = t(faction);
    btn.addEventListener("click", () => {
      state.faction = faction;
      persist();
      renderFactions();
      render();
    });
    factionsEl.appendChild(btn);
  });
}


function updateClassNote() {
  const meta = DATA.classMeta[state.cls];
  if (state.lang === "en") {
    classNote.textContent = state.cls === "Death Knight"
      ? "Death knights start at level 55. The minimum level adjusts automatically."
      : "Armor: " + armorText(state.cls, state.level) + ". Weapons: " + DATA.classMetaEn[state.cls].weapons + ".";
    return;
  }
  classNote.textContent = state.cls === "Death Knight"
    ? "Los caballeros de la muerte empiezan en el nivel 55. El nivel mínimo se ajusta solo."
    : "Armadura: " + armorText(state.cls, state.level) + ". Armas: " + meta.weapons + ".";
}


function setLevel(value) {
  const next = clampLevel(value);
  if (next === state.level) return;
  state.level = next;
  if (state.level !== 80) state.fresh = false;
  levelInput.value = state.level;
  levelRange.value = state.level;
  persist();
  render();
}


function renderSlot(spec, gear, slot) {
  const sl = gear.slots[slot];
  const list = sl.list.slice(0, 1 + state.alts);
  const e = list[0];
  const label = (SLOT_LABEL[state.lang] || SLOT_LABEL.es)[slot] || slot;
  if (!e) {
    return '<article class="slot empty"><div class="slot-top"><span class="slot-name">' + label +
      '</span><span class="slot-ilvl">—</span></div><div class="slot-body"><div class="item-icon placeholder">?</div><div><span class="item-name" style="color:var(--muted)">' + t("emptyItem") + '</span><div class="item-meta">' + t("emptyMeta") + '</div></div></div></article>';
  }
  const item = e.it;
  const alts = list.slice(1);
  const altHtml = alts.length
    ? '<ul class="alt-list" aria-label="' + t("moreAlts") + '">' + alts.map((a) => "<li>" + rankPill("ALT" + (alts.indexOf(a) + 1), t("bisAltTitle")) + itemLink(a.id, false, "alt-link") + "<span>iLvl " + a.it.ilvl + "</span><span>" + badgeHtml(obtainInfo(a.it)) + "</span></li>").join("") + "</ul>"
    : '<div class="alts">' + t("noAlts") + "</div>";
  let note = "";
  if (slot === "offhand" && gear.slots.mainhand && gear.slots.mainhand.list[0] && gear.slots.mainhand.list[0].it.s === "twohand") note = '<div class="alt-note">' + t("offhandNote") + "</div>";
  const warn = e.offspec ? L("Sin objetos útiles para tu especialidad en este slot a este nivel: es la mejor opción disponible.", "No items useful for your spec in this slot at this level: this is the best available option.") : rivalNote(e, sl.info);
  if (slot === "mainhand" && gear.loadout) {
    const lo = gear.loadout;
    note += '<div class="alt-note">' + (lo.use1 ? L("Arma de una mano + mano secundaria", "One-hand weapon + off hand") : L("Arma de dos manos", "Two-hand weapon")) +
      ": +" + lo.diff + L("% frente a ", "% over ") + esc(lo.other) + ".</div>";
  }
  let meta = item.req ? t("level") + item.req : t("noReq");
  if (item.dps) meta += " · " + item.dps + " DPS";
  if (item.ar) meta += " · " + item.ar + (state.lang === "en" ? " armor" : " armadura");
  return '<article class="slot" style="--q:' + qColor(item.q) + '">' +
    '<div class="slot-top"><span class="slot-name">' + label + '</span>' + rankPill(slot === "ring2" || slot === "trinket2" ? "BiS²" : "BiS", t("bisBisTitle")) + '<span class="slot-ilvl">iLvl ' + item.ilvl + "</span></div>" +
    '<div class="slot-body">' + iconHtml(item) + "<div>" + itemLink(e.id, false, "item-name") +
    '<div class="item-meta">' + meta + "</div>" +
    '<div class="item-source">' + badgeHtml(obtainInfo(item)) + "</div>" +
    '<div class="item-stats">' + statLine(item) + "</div></div></div>" +
    '<div class="slot-actions"><a class="mini-btn" href="' + ITEM_URL + e.id + '" target="_blank" rel="noopener">' + t("howTo") + "</a></div>" +
    (warn ? '<div class="warn">' + esc(warn) + "</div>" : "") + note +
    whyHtml(e, alts[0], sl.info) + altHtml + "</article>";
}


function renderCaps(spec, gear) {
  const box = $("capsBox");
  if (!gear.totals) { box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = "<strong>" + t("capsTitle") + "</strong> " + Object.keys(gear.caps).map((k) => {
    const have = gear.totals[k], cap = gear.caps[k], diff = Math.abs(have - cap);
    const state2 = have > cap ? t("capsOver") + " " + diff : have === cap ? t("capsEq") : t("capsMissing") + " " + diff;
    return '<span class="cap ' + (have >= cap ? "ok" : "low") + '">' + esc(partLabel(k)) + " " + have + " / " + cap + " · " + state2 + "</span>";
  }).join("") + '<small>' + t("capsNote") + "</small>";
}


function renderHeroicStatus(spec, level) {
  const el = $("heroicStatus");
  if (level !== 80) { el.hidden = true; return; }
  const avg = averageItemLevel(spec);
  el.hidden = false;
  el.classList.toggle("ok", avg != null && avg >= 219);
  if (avg == null) el.textContent = t("heroicGeneralNeedGear");
  else if (avg >= 219) el.textContent = t("heroicGeneralOpen").replace("{avg}", fmtIlvl(avg));
  else if (avg >= 180) el.textContent = t("heroicGeneralPartial").replace("{avg}", fmtIlvl(avg));
  else el.textContent = t("heroicGeneralLocked").replace("{avg}", fmtIlvl(avg));
}


function renderSlots(spec, level) {
  const gear = computeGear(spec, { level, faction: state.faction, scope: state.scope, phase: state.phase, pvp: state.pvp, fresh: state.fresh });
  const order = specSlots(spec);
  slotCount.textContent = order.length + t("slots");
  slotsEl.innerHTML = order.map((slot) => renderSlot(spec, gear, slot)).join("");
  return gear;
}


function renderStats(spec) {
  const key = DATA.stats[spec.role] ? spec.role : "str";
  const list = state.lang === "en" ? (STATS_EN[key] || STATS_EN.str) : (DATA.stats[key] || DATA.stats.str);
  statList.innerHTML = list.map((s) => "<li>" + esc(s) + "</li>").join("");
  const hints = state.lang === "en" ? {
    str: "Hit and expertise to cap, then crit and haste.",
    agi: "Agility, hit, and expertise are the base; crit scales very well.",
    caster: "Intellect and spell power first; fix hit, then crit or haste.",
    healer: "Intellect and spirit sustain your heals; haste gains value with level.",
    tank: "Stamina and armor first; defense, dodge, and parry before damage.",
    bear: "Stamina and agility are the base; dodge, expertise, and hit before damage.",
    hunter: "Agility and hit lead; crit and attack power follow."
  } : {
    str: "Golpe y pericia hasta los topes; después crítico y celeridad.",
    agi: "Agilidad, golpe y pericia son la base; el crítico escala muy bien.",
    caster: "Intelecto y poder de hechizos primero; ajusta golpe y luego crítico o celeridad.",
    healer: "Intelecto y espíritu sostienen tus curas; la celeridad gana valor con el nivel.",
    tank: "Aguante y armadura primero; defensa, esquiva y parada antes de buscar daño.",
    bear: "Aguante y agilidad son la base; esquiva, pericia y golpe antes de buscar daño.",
    hunter: "Agilidad y golpe mandan; crítico y poder de ataque vienen después."
  };
  statsHint.textContent = hints[key] || "";
}


function renderDungeons(bracket, level) {
  const anyActive = bracket.dungeons.some((d) => level >= d[1] && level <= d[2]);
  const upcoming = !anyActive ? bracket.dungeons.find((d) => d[1] > level) : null;
  dungeonList.innerHTML = bracket.dungeons.map((d) => {
    const name = d[0], min = d[1], max = d[2];
    const current = level >= min && level <= max;
    const next = upcoming === d;
    const label = bracket.min === 80 ? "" : (current ? t("now") : (next ? t("next") : ""));
    const zone = dungeonByName(name);
    const inner = "<span>" + esc(name) + label + '</span><span class="range">' + min + "–" + max + "</span>";
    return '<li class="' + (current || next ? "current" : "") + '">' + (zone ? '<button type="button" data-zone="' + zone.id + '" title="' + t("lootTitle") + '">' + inner + "</button>" : inner) + "</li>";
  }).join("");
  dungeonList.querySelectorAll("button[data-zone]").forEach((btn) => btn.addEventListener("click", () => {
    state.dungeon = Number(btn.dataset.zone);
    persist();
    render();
    $("lootHeading").scrollIntoView({ behavior: "smooth", block: "start" });
  }));
}


function renderHeirlooms(key, level) {
  const hs = DATA.heirloomSets[key];
  const set = hs && DATA.legacySets[hs.set];
  if (!hs || !set) {
    heirloomPanel.hidden = true;
    return;
  }
  const groups = [
    [t("shoulders"), set.shoulders || []],
    [t("chest"), set.chest || []],
    [t("weapons"), (hs.weapons && hs.weapons.length) ? hs.weapons : (set.weapons || [])],
    [t("trinkets"), set.trinkets || []]
  ].map((g) => [g[0], g[1].filter((id) => !FACTION_HEIRLOOM[id] || FACTION_HEIRLOOM[id] === state.faction)])
   .filter((g) => g[1].length);
  if (!groups.length) {
    heirloomPanel.hidden = true;
    return;
  }
  heirloomPanel.hidden = false;
  heirloomList.innerHTML = '<p class="note">' + t("heirloomNote") + "</p>" + groups.map((g) => {
    const links = g[1].map((id) => itemLink(id, true, "heirloom-link")).filter(Boolean).join("");
    return '<div class="heirloom-group"><b>' + g[0] + "</b>" + links + "</div>";
  }).join("");
}


function render() {
  const level = state.level;
  const meta = DATA.classMeta[state.cls];
  const spec = specFor(state.cls, state.spec);
  if (!spec) return;
  const bracket = bracketFor(level);
  const next = DATA.brackets.find((b) => b.min > level);

  applyLanguage();
  factionsEl.querySelectorAll("button").forEach((btn) => {
    btn.textContent = t(btn.dataset.faction);
    btn.setAttribute("aria-pressed", String(btn.dataset.faction === state.faction));
  });
  document.documentElement.style.setProperty("--class", meta.color);
  levelInput.min = meta.min;
  levelRange.min = meta.min;
  levelInput.value = level;
  levelRange.value = level;
  levelNumber.textContent = level;
  levelRange.style.setProperty("--pct", (((level - 1) / 79) * 100) + "%");
  bracketLabel.textContent = bracketName(bracket);
  $("statusBracket").textContent = level === 80
    ? t("levelMax")
    : bracketName(bracket) + " · " + bracket.min + (state.lang === "en" ? " to " : " a ") + bracket.max;
  $("statusArmor").textContent = armorText(state.cls, level);
  $("statusNext").textContent = next ? t("level") + next.min + " · " + bracketName(next) : t("nextBiS");
  const fresh = state.fresh && level === 80 && !state.pvp && state.scope !== "raid";
  $("fresh80").checked = state.fresh;
  $("fresh80").disabled = level !== 80 || state.pvp;
  $("freshRoute").hidden = !fresh;
  $("sheetIntro").textContent = state.pvp ? t("sheetIntroPvp") + level + "."
    : level === 80 ? t(fresh ? "sheetIntro80Fresh" : state.scope === "raid" ? "sheetIntro80Raid" : "sheetIntro80")
    : t("sheetIntro") + level + ".";
  $("sourcesValue").textContent = state.pvp ? t("sourcesPvpOnly") : fresh ? t("sourcesFresh") : t(state.scope === "raid" ? "sourcesRaid" : "sourcesValue");
  $("bracketAdvice").textContent = bracketAdvice(bracket);
  updateClassNote();
  renderHeroicStatus(spec, level);
  const gear = renderSlots(spec, level);
  renderCaps(spec, gear);
  runtime.lastGear = gear;
  renderEquip(spec);
  renderLoot(spec);
  renderBis(spec);
  renderWeights(spec);
  renderEqTools();
  renderNav();
  renderStats(spec);
  renderDungeons(bracket, level);
  renderHeirlooms(state.cls + "|" + state.spec, level);
  slotsEl.classList.remove("reveal");
  void slotsEl.offsetWidth;
  slotsEl.classList.add("reveal");
  scheduleRefresh();
}

/* ---------- BiS por fase (estilo BiS-Tooltip) ---------- */

function baseWeights(spec) {
  const specW = (ENG.specWeights || {})[spec.cls + "|" + spec.name] || {};
  return Object.assign({}, ENG.weights[spec.role] || {}, specW);
}

function renderWeights(spec) {
  const key = spec.cls + "|" + spec.name;
  $("wHeading").textContent = L("Ajustar pesos de estadísticas", "Adjust stat weights");
  $("wHint").textContent = L("Valores relativos: cambian el ranking de la ficha, el BiS por fase y el plan de farmeo (la guía de T10 sigue mandando en el BiS si está activada).", "Relative values: they change the sheet ranking, the BiS by phase and the farming plan (the T10 guide still leads the BiS when enabled).");
  $("wReset").textContent = L("Restablecer pesos", "Reset weights");
  const base = baseWeights(spec), ov = (state.wOverride || {})[key] || {};
  const keys = STAT_ORDER.filter((k) => (base[k] || 0) > 0 || ov[k] != null);
  const sig = key + "|" + L("es", "en") + "|" + JSON.stringify(ov);
  const grid = $("wGrid");
  if (grid.dataset.sig === sig) return;
  grid.dataset.sig = sig;
  grid.innerHTML = keys.map((k) => "<label for=\"w_" + k + "\">" + esc(partLabel(k)) + '</label><input id="w_' + k + '" data-k="' + k + '" type="number" min="0" max="10" step="0.05" value="' + (ov[k] != null ? ov[k] : base[k]) + '">').join("");
  grid.querySelectorAll("input").forEach((inp) => inp.addEventListener("change", () => {
    const k = inp.dataset.k, v = parseFloat(inp.value), cur = (state.wOverride[key] = state.wOverride[key] || {});
    if (!isFinite(v) || v < 0 || Math.abs(v - (base[k] || 0)) < 1e-9) delete cur[k]; else cur[k] = v;
    if (!Object.keys(cur).length) delete state.wOverride[key];
    bisCache.clear(); candCache.key = ""; persist(); render();
  }));
}
$("bisGuide").addEventListener("change", (e) => { state.bisGuide = e.target.checked; bisCache.clear(); persist(); render(); });
$("wReset").addEventListener("click", () => {
  delete state.wOverride[state.cls + "|" + state.spec];
  $("wGrid").dataset.sig = ""; bisCache.clear(); candCache.key = ""; persist(); render();
});

/* ---------- Exportar, importar y compartir el equipo ---------- */

function renderEqTools() {
  $("eqExport").textContent = L("Copiar equipo", "Copy gear");
  $("eqImport").textContent = L("Importar", "Import");
  $("eqLink").textContent = L("Copiar enlace", "Copy link");
  $("eqApply").textContent = L("Aplicar", "Apply");
}

function arrangeSections() {
  const main = document.querySelector(".main"), route = $("routePanel"), bis = $("bisPanel"), gem = $("gemPanel"), loot = $("lootPanel");
  if (!main || !route || !bis || !gem || !loot) return;
  const top80 = state.level === 80;
  if (top80 && main.previousElementSibling !== gem) main.before(route, bis, gem);
  else if (!top80 && gem.nextElementSibling !== loot) loot.before(route, bis, gem);
  const eqp = $("eqPanel"), eqSlot = $("routeEqSlot");
  if (top80 && eqp.parentElement !== eqSlot) eqSlot.appendChild(eqp);
  else if (!top80 && eqp.parentElement === eqSlot) loot.querySelector(".loot-ctl").before(eqp);
  $("advNote").hidden = !top80;
  $("advNote").textContent = L("A nivel 80 estos filtros solo cambian la ficha «Equipamiento recomendado»; «Tu ruta» usa la etapa del paso 2.", "At level 80 these filters only change the \"Recommended gear\" sheet; \"Your route\" uses the stage from step 2.");
  document.body.classList.toggle("lvl80", top80);
  const nav = $("jump");
  (top80 ? ["route", "bis", "gem", "sheet", "loot", "top"] : ["sheet", "route", "bis", "gem", "loot", "top"]).forEach((k) => nav.appendChild(nav.querySelector('[data-j="' + k + '"]')));
}

function renderNav() {
  arrangeSections();
  const names = { sheet: L("Equipo recomendado", "Recommended gear"), route: L("Tu ruta", "Your route"), bis: L("Ranking por slot", "Ranking by slot"), gem: L("Gemas y encantamientos", "Gems and enchants"), loot: L("Botín y mi equipo", "Loot and my gear"), top: L("↑ Arriba", "↑ Top") };
  document.querySelectorAll("#jump a").forEach((a) => { a.textContent = names[a.dataset.j]; });
  const fac = (state.faction === "alliance" ? L("Alianza", "Alliance") : L("Horda", "Horde"));
  $("deckToggle").innerHTML = "<span>" + esc(state.cls + " · " + state.spec + " · " + fac + " · " + L("Nivel ", "Level ") + state.level) + "</span><span>" + (state.deckCollapsed ? L("Cambiar ▾", "Change ▾") : L("Ocultar ▴", "Hide ▴")) + "</span>";
  $("deckToggle").setAttribute("aria-expanded", String(!state.deckCollapsed));
  $("advLabel").textContent = L("Más opciones", "More options");
  const act = [state.scope === "raid" ? L("Con bandas", "With raids") : L("Sin bandas", "No raids")];
  if (state.phase) act.push(L("Fase ", "Phase ") + state.phase);
  if (state.pvp) act.push("PvP");
  if (state.fresh) act.push(L("Recién 80", "Fresh 80"));
  if (state.alts !== 2) act.push(state.alts + " alt.");
  $("advState").textContent = act.join(" · ");
  $("deck").classList.toggle("collapsed", state.deckCollapsed);
}
STORE.rank = "wotlk-gear-rank-open";
$("rankDetails").open = load(STORE.rank, "0") === "1";
$("rankDetails").addEventListener("toggle", () => save(STORE.rank, $("rankDetails").open ? "1" : "0"));
$("routeSummary").addEventListener("click", (e) => {
  if (e.target.id !== "openRank") return;
  $("rankDetails").open = true;
  $("bisGrid").scrollIntoView({ behavior: "smooth", block: "start" });
});
STORE.adv = "wotlk-gear-adv-open";
$("advOpts").open = load(STORE.adv, "1") === "1";
$("advOpts").addEventListener("toggle", () => save(STORE.adv, $("advOpts").open ? "1" : "0"));
$("deckToggle").addEventListener("click", () => { state.deckCollapsed = !state.deckCollapsed; save(STORE.deck, state.deckCollapsed ? "1" : "0"); renderNav(); });
if ("IntersectionObserver" in window) {
  const ids = ["routePanel", "sheetPanel", "bisPanel", "gemPanel", "lootPanel"], seen = new Set();
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) seen.add(e.target.id); else seen.delete(e.target.id); });
    const cur = ids.find((id) => seen.has(id));
    document.querySelectorAll("#jump a").forEach((a) => a.setAttribute("aria-current", String(cur && a.getAttribute("href") === "#" + cur)));
  }, { rootMargin: "-20% 0px -60% 0px" });
  ids.forEach((id) => { const el = document.getElementById(id); if (el) io.observe(el); });
}


export { renderClasses, renderOptions, renderSpecs, renderFactions, updateClassNote, setLevel, renderSlot, renderCaps, renderHeroicStatus, renderSlots, renderStats, renderDungeons, renderHeirlooms, render, baseWeights, renderWeights, renderEqTools, arrangeSections, renderNav };
