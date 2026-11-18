import { state, $, t, L, esc, currentSpec, specSlots, equippedMap, gearItem, itemLink, persist, renderSeg, scheduleRefresh, SLOT_LABEL } from "./core.js";
import { ENG, computeGear } from "./engine.js";
import { partLabel, badgeHtml, obtainInfo, bisLabel, rankPill } from "./format.js";

/* ---------- BiS por fase (estilo BiS-Tooltip) ---------- */
const BIS_PHASES = [
  { key: "PR", scope: "noraid", phase: 1, es: "Pre-banda: mazmorras heroicas, reputaciones, profesiones y emblemas, sin entrar a banda.", en: "Pre-raid: heroic dungeons, reputations, professions and emblems, without raiding." },
  { key: "T7", scope: "raid", phase: 1, es: "Fase 1: Naxxramas, Obsidian Sanctum y Eye of Eternity, más todo lo anterior.", en: "Phase 1: Naxxramas, Obsidian Sanctum and Eye of Eternity, plus everything before." },
  { key: "T8", scope: "raid", phase: 2, es: "Fase 2: Ulduar, más todo lo anterior.", en: "Phase 2: Ulduar, plus everything before." },
  { key: "T9", scope: "raid", phase: 3, es: "Fase 3: Trial of the Crusader, más todo lo anterior.", en: "Phase 3: Trial of the Crusader, plus everything before." },
  { key: "T10", scope: "raid", phase: 5, es: "Fases 4 y 5: Icecrown Citadel y Ruby Sanctum, más todo lo anterior.", en: "Phases 4 and 5: Icecrown Citadel and Ruby Sanctum, plus everything before." }
];
const BIS_ALTS = 6;
const bisCache = new Map();
const bisCtx = () => [state.cls, state.spec, state.faction, state.showHeirlooms ? 1 : 0].join("|");

function bisRows(spec, gear) {
  const rows = [];
  specSlots(spec).forEach((slot) => {
    if (slot === "ring2" || slot === "trinket2") return;
    const sl = gear.slots[slot];
    if (!sl) return;
    let list = sl.list, pair = false;
    if (slot === "ring1" || slot === "trinket1") {
      pair = true;
      const other = gear.slots[slot.slice(0, -1) + "2"];
      const seen = new Set(), merged = [];
      [list[0], other && other.list[0]].concat(list.slice(1), other ? other.list.slice(1) : []).forEach((e) => {
        if (e && !seen.has(e.it.n)) { seen.add(e.it.n); merged.push(e); }
      });
      list = merged;
    }
    rows.push({ slot, pair, list: list.slice(0, (pair ? 2 : 1) + BIS_ALTS) });
  });
  return rows;
}
function bisData(ph) {
  const key = bisCtx() + "|" + ph.key;
  if (bisCache.has(key)) return bisCache.get(key);
  const spec = currentSpec();
  const gear = computeGear(spec, { level: 80, faction: state.faction, scope: ph.scope, phase: ph.phase, pvp: false, fresh: false, noHeroicGate: true });
  const rows = bisRows(spec, gear);
  const ranks = {};
  rows.forEach((r) => r.list.forEach((e, i) => {
    const prev = ranks[e.it.n];
    if (!prev || prev.i > i) ranks[e.it.n] = { i, label: bisLabel(i, r.pair) };
  }));
  const data = { rows, ranks, totals: gear.totals, caps: gear.caps };
  bisCache.set(key, data);
  if (bisCache.size > 60) bisCache.delete(bisCache.keys().next().value);
  return data;
}
function bisCompletes(e, data) {
  if (!data.totals || !data.caps) return "";
  const ks = Object.keys(data.caps).filter((k) => (data.totals[k] || 0) < data.caps[k] && ((e.it.st || {})[k] || 0) > 0);
  return ks.length ? '<span class="bis-fill">' + L("completa ", "fills ") + esc(ks.map((k) => partLabel(k).toLowerCase()).join(" + ")) + "</span>" : "";
}
function bisPairLabel(slot) { return slot === "ring1" ? t("bisPairRing") : slot === "trinket1" ? t("bisPairTrinket") : (SLOT_LABEL[state.lang] || SLOT_LABEL.es)[slot] || slot; }
function bisOwned(r) {
  const g = equippedMap(), slots = r.pair ? [r.slot, r.slot.slice(0, -1) + "2"] : [r.slot];
  const names = new Set(slots.map((sl) => g[sl] && gearItem(g[sl]) && gearItem(g[sl]).n).filter(Boolean));
  return names;
}
/* ---------- Gemas y encantamientos (Icy Veins / Wowhead por especialidad) ---------- */
const GEM_COLORS = { red: ["Roja", "Red"], yellow: ["Amarilla", "Yellow"], blue: ["Azul", "Blue"], prismatic: ["Prismática", "Prismatic"], meta: ["Meta", "Meta"] };
const ES_MARK = /\b(si|para|el|la|los|las|con|una|un|solo|ranura|ranuras|gema|gemas|cuando|hasta|tras|una vez|que|del|en|de|se|ya|aún|alcanzado|alcanzó|llegó|falta|bonus es|variante|perfil|máximo|amenaza|menor|inferior|débiles|ignorando|alternativa|ignora|busca|tiene|está|por|mejor|pieza|demás|resto|azules|azul|roja|rojas|activa|activar)\b/i;
const NOTE_EN = [
  [/\+1 ranura/g, "+1 socket"], [/\bo (?=[A-Z+])/g, "or "], [/ o (?=[A-Z+])/g, " or "], [/si falta golpe/g, "if hit is missing"], [/si falta Hit para el cap de/g, "if short of Hit for the cap of"],
  [/si falta Hit para los/g, "if short of Hit for"], [/si falta Hit/g, "if Hit is missing"], [/si falta Defense/g, "if Defense is missing"], [/si se ignora el bonus/g, "if the socket bonus is ignored"],
  [/en el resto de ranuras azules/g, "in the remaining blue sockets"], [/en todas las demás ranuras azules/g, "in all other blue sockets"], [/en las demás ranuras azules/g, "in the other blue sockets"],
  [/1 sola en la pieza con mejor bonus de (\w+) para activar/g, "just 1 on the piece with the best $1 bonus to activate"], [/1 sola en la pieza con mejor bonus para activar/g, "just 1 on the piece with the best bonus to activate"],
  [/1 sola para activar/g, "just 1 to activate"], [/1 sola/g, "just 1"], [/una vez alcanzado el hard cap de/g, "once the hard cap of"], [/una vez alcanzado el cap de/g, "once the cap of"],
  [/hasta alcanzar exactamente/g, "up to exactly"], [/hasta alcanzar/g, "up to"], [/hasta el cap de/g, "up to the cap of"], [/solo si falta para el cap de/g, "only if short of the cap of"],
  [/o bonus >= /g, "or bonus >= "], [/para activar meta o bonus >= /g, "to activate the meta or bonus >= "], [/para máximo EHP/g, "for maximum EHP"], [/para amenaza/g, "for threat"],
  [/si el bonus es >= /g, "if the bonus is >= "], [/cuando el bonus sea >= /g, "when the bonus is >= "], [/para activar la meta/g, "to activate the meta"], [/para activar/g, "to activate"]
];
function noteText(str) {
  if (!str) return "";
  if (state.lang !== "en") return str.replace(/ ID: \d+/g, "");
  return str.replace(/\(([^)]*)\)/g, (m, g) => {
    let x = g;
    NOTE_EN.forEach(([re, to]) => { x = x.replace(re, to); });
    return ES_MARK.test(x) ? "" : "(" + x + ")";
  }).replace(/ ID: \d+/g, "").replace(/\s+\(\)/g, "").replace(/\s+$/, "");
}
const gemColorName = (c) => (GEM_COLORS[c] || [c, c])[state.lang === "en" ? 1 : 0];
const gemLink = (g) => '<a class="gem-link" href="https://wotlk.evowow.com/?item=' + g.id + '" target="_blank" rel="noopener">' + esc(g.name) + "</a>";
const enchLink = (g) => '<a class="gem-link" href="https://wotlk.evowow.com/?search=' + encodeURIComponent(g.name) + '" target="_blank" rel="noopener">' + esc(g.name) + "</a>";
const refFor = () => (ENG.refGems || {})[state.cls + "|" + state.spec] || null;
function bisFx(r) {
  const ref = refFor(), e = r.list[0];
  if (!ref || !e) return "";
  const parts = [];
  const sg = e.it.sg || [];
  if (sg.length || e.it.mt) {
    const gems = sg.map((c) => { const list = ref[c === "prismatic" ? "red" : c] || []; return list[0] ? '<span class="gem g-' + esc(c) + '"></span>' + gemLink(list[0]) : ""; }).filter(Boolean);
    if (e.it.mt && ref.meta) gems.unshift('<span class="gem g-meta"></span>' + gemLink(ref.meta));
    if (gems.length) parts.push('<div class="bis-fx-row"><b>' + t("gemSockets") + "</b> " + gems.join(" · ") + "</div>");
  }
  const en = ref.enchants[r.slot] || (r.slot === "ring1" ? null : null);
  if (en) parts.push('<div class="bis-fx-row"><b>' + t("gemEnchant") + "</b> " + enchLink(en) + ' <span class="bis-fx-st">' + esc(noteText(en.stats)) + "</span></div>");
  return parts.length ? '<div class="bis-fx">' + parts.join("") + "</div>" : "";
}
function renderGems() {
  const ref = refFor(), box = $("gemBody");
  $("gemSpec").textContent = state.cls + " · " + state.spec;
  if (!ref) { box.innerHTML = ""; return; }
  const col = (title, list) => '<article class="bis-card"><h3>' + esc(title) + "</h3>" + (list.length ? "<ol class=\"gem-list\">" + list.map((g, i) => "<li>" + (i === 0 ? rankPill("1ª") : rankPill(i + 1 + "ª")) + "<div>" + gemLink(g) + '<span class="bis-sub">' + esc(noteText(g.stats)) + "</span></div></li>").join("") + "</ol>" : '<div class="bis-empty">—</div>') + "</article>";
  const metaList = ref.meta ? [ref.meta] : [];
  const slotsOrder = ["head", "shoulder", "back", "chest", "wrist", "hands", "waist", "legs", "feet", "mainhand", "offhand", "ranged"];
  const labels = SLOT_LABEL[state.lang] || SLOT_LABEL.es;
  const ench = slotsOrder.filter((k) => ref.enchants[k]).map((k) => "<li><span class=\"gem-slot\">" + esc(labels[k] || k) + "</span><div>" + enchLink(ref.enchants[k]) + '<span class="bis-sub">' + esc(noteText(ref.enchants[k].stats)) + "</span></div></li>").join("");
  const rule = state.lang === "en" ? "" : ref.rule;
  box.innerHTML = '<div class="bis-grid">' + col(t("gemMeta"), metaList) + col(gemColorName("red"), ref.red) + col(gemColorName("yellow"), ref.yellow) + col(gemColorName("blue"), ref.blue) +
    '<article class="bis-card gem-ench"><h3>' + t("gemEnchants") + "</h3><ol class=\"gem-list\">" + ench + "</ol></article></div>" +
    (rule ? '<p class="gem-rule"><b>' + t("gemRule") + "</b> " + esc(rule) + "</p>" : "");
}
function bisCard(r, data) {
  const owned = bisOwned(r);
  const items = r.list.map((e, i) => {
    const lab = bisLabel(i, r.pair), isAlt = lab.startsWith("ALT");
    const icon = e.it.i ? '<img class="bis-ic" src="https://wotlk.evowow.com/static/images/wow/icons/medium/' + esc(e.it.i) + '.jpg" alt="" loading="lazy" onerror="this.style.visibility=\'hidden\'">' : '<span class="bis-ic"></span>';
    const have = owned.has(e.it.n);
    return '<li' + (have ? ' class="owned"' : "") + ">" + rankPill(lab) + icon + "<div>" + itemLink(e.id, false, "bis-name") + (have ? '<span class="bis-have">✓ ' + t("bisHave") + "</span>" : "") + (isAlt ? bisCompletes(e, data) : "") +
      '<span class="bis-sub">iLvl ' + e.it.ilvl + " · " + badgeHtml(obtainInfo(e.it)) + "</span></div></li>";
  }).join("");
  return '<article class="bis-card"><h3>' + esc(bisPairLabel(r.slot)) + "</h3>" + (items ? "<ol>" + items + "</ol>" + bisFx(r) : '<div class="bis-empty">' + t("bisEmptySlot") + "</div>") + "</article>";
}
function renderBis(spec) {
  const ph = BIS_PHASES.find((p) => p.key === state.bisPhase) || BIS_PHASES[0];
  renderSeg($("bisTabs"), BIS_PHASES.map((p) => ({ value: p.key, label: p.key })), ph.key, (v) => { state.bisPhase = v; persist(); renderBis(currentSpec()); scheduleRefresh(); });
  $("bisSpec").textContent = state.cls + " · " + state.spec;
  $("bisPhaseNote").textContent = ph[state.lang === "en" ? "en" : "es"];
  $("bisLegend").innerHTML = "<span>" + rankPill("BiS") + t("bisLegendBis") + "</span><span>" + rankPill("BiS²") + t("bisLegendBis2") + "</span><span>" + rankPill("ALT1") + "–" + rankPill("ALT" + BIS_ALTS) + t("bisLegendAlt") + "</span>";
  const data = bisData(ph);
  const box = $("bisCaps");
  if (data.totals && data.caps) {
    box.hidden = false;
    box.innerHTML = "<strong>" + t("capsTitle") + "</strong> " + Object.keys(data.caps).map((k) => {
      const have = data.totals[k], cap = data.caps[k];
      return '<span class="cap ' + (have >= cap ? "ok" : "low") + '">' + esc(partLabel(k)) + " " + have + " / " + cap + " · " + (have > cap ? t("capsOver") + " " + (have - cap) : have === cap ? t("capsEq") : t("capsMissing") + " " + (cap - have)) + "</span>";
    }).join("") + "<small>" + t("capsNote") + "</small>";
  } else box.hidden = true;
  $("bisGrid").innerHTML = data.rows.map((r) => bisCard(r, data)).join("");
  renderGems();
  const haveN = data.rows.filter((r) => bisOwned(r).size && r.list.some((e) => bisOwned(r).has(e.it.n))).length;
  $("bisOwnedNote").textContent = Object.keys(equippedMap()).length ? t("bisOwnedPre") + haveN + " / " + data.rows.length + t("bisOwnedPost") : t("bisOwnedNone");
}

export {
  BIS_PHASES, BIS_ALTS, bisCache, bisCtx, bisRows, bisData, bisCompletes,
  bisPairLabel, bisOwned, GEM_COLORS, ES_MARK, NOTE_EN, noteText, gemColorName,
  gemLink, enchLink, refFor, bisFx, renderGems, bisCard, renderBis
};
