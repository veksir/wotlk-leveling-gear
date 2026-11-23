import { DATA } from "./data.js";
import { state, $, t, L, esc, currentSpec, specSlots, equippedMap, gearItem, itemLink, persist, renderSeg, scheduleRefresh, SLOT_LABEL, levelItem, eqNorm, iconSrc, STORE, load, save } from "./core.js";
import { ENG, GEAR_ITEMS, computeGear, weightsFor, freshAccessible, raidGated, itemFactions } from "./engine.js";
import { evalEquip } from "./equipment.js";
import { averageItemLevel, fmtIlvl, isHeroicOnlyDrop, heroicRequirement } from "./heroic.js";
import { partLabel, badgeHtml, obtainInfo, bisLabel, rankPill, diffLabel, currencyLabel } from "./format.js";
const BIS_PHASES = [
  { key: "PR", scope: "noraid", phase: 0, raidOpen: 0, es: "Pre-banda: todo lo que no es de banda, de todas las fases del servidor (las mazmorras ya están abiertas): heroicas de ToC, Forja/Foso/Salas de ICC, reputaciones, profesiones y emblemas. Quedan fuera los vendedores de Frost y el botín de banda: esperan a su tier.", en: "Pre-raid: everything that is not raid gear, from every phase of the server (dungeons are already open): ToC, Forge/Pit/Halls of ICC heroics, reputations, professions and emblems. Frost vendors and raid loot are left out: they wait for their tier." },
  { key: "T7", scope: "raid", phase: 1, raidOpen: 1, es: "Se abre la fase 1 de banda: Naxxramas, Obsidian Sanctum y Eye of Eternity, más todo lo anterior.", en: "Raid phase 1 opens: Naxxramas, Obsidian Sanctum and Eye of Eternity, plus everything before." },
  { key: "T8", scope: "raid", phase: 2, raidOpen: 2, es: "Se abre la fase 2 de banda: Ulduar, más todo lo anterior.", en: "Raid phase 2 opens: Ulduar, plus everything before." },
  { key: "T9", scope: "raid", phase: 3, raidOpen: 3, es: "Se abre la fase 3 de banda: Trial of the Crusader, más todo lo anterior.", en: "Raid phase 3 opens: Trial of the Crusader, plus everything before." },
  { key: "T10", scope: "raid", phase: 5, raidOpen: 5, es: "Se abren las fases 4 y 5 de banda: Icecrown Citadel y Ruby Sanctum (y los vendedores de Frost), más todo lo anterior.", en: "Raid phases 4 and 5 open: Icecrown Citadel and Ruby Sanctum (and Frost vendors), plus everything before." }
];

const BIS_F80 = { key: "F80", fresh: true, scope: "noraid", phase: 0,
  es: "Primer paso a nivel 80, sin heroicas: misiones, reputaciones, mazmorras normales, emblemas de Triunfo y crafting. Pasa a «PR» (con heroicas) cuando tu iLvl medio llegue a 180 (200 para ToC5, FoS y PoS; 219 para HoR).",
  en: "First step at level 80, no heroics: quests, reputations, normal dungeons, Triumph emblems and crafting. Move on to \"PR\" once your average item level reaches 180 (200 for ToC5, FoS and PoS; 219 for HoR)." };

const BIS_TABS = [BIS_F80].concat(BIS_PHASES);

const bisTabShort = (p) => (p.key === "F80" ? L("Recién 80", "Fresh 80") : p.key);

const bisTabLabel = (p) => ({ F80: L("Recién 80", "Fresh 80"), PR: L("Heroicas (PR)", "Heroics (PR)"), T7: "T7 Naxxramas", T8: "T8 Ulduar", T9: L("T9 Cruzado", "T9 Crusader"), T10: "T10 Icecrown" }[p.key] || p.key);

const bisOpts = (ph) => (ph.fresh
  ? { level: 80, faction: state.faction, scope: "noraid", phase: 0, pvp: false, fresh: true, assumeAvg: 0 }
  : { level: 80, faction: state.faction, scope: ph.scope, phase: 0, raidOpen: ph.raidOpen, pvp: false, fresh: false, noHeroicGate: true });

const BIS_ALTS = 6;

const bisCache = new Map();

const bisCtx = () => [state.cls, state.spec, state.faction, state.showHeirlooms ? 1 : 0, state.bisGuide ? 1 : 0, JSON.stringify((state.wOverride || {})[state.cls + "|" + state.spec] || 0)].join("|");


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

const bisGuideFor = (ph) => {
  const key = state.cls + "|" + state.spec;
  return ((ENG.refBisPhases || {})[key] || {})[ph.key] || (ph.key === "T10" ? (ENG.refBis || {})[key] : null) || null;
};

function applyRefBis(rows, ph) {
  const ref = bisGuideFor(ph);
  if (!ref) return;
  rows.forEach((r) => {
    const ids = ref[r.pair ? (r.slot === "ring1" ? "ring" : "trinket") : r.slot === "relic" ? "ranged" : r.slot];
    if (!ids || !ids.length) return;
    const seen = new Set(), head = [];
    ids.forEach((id) => {
      const it = gearItem(id);
      if (!it || seen.has(it.n)) return;
      const f = itemFactions(it);
      if (!f.has("both") && !f.has(state.faction)) return;
      seen.add(it.n);
      const found = r.list.find((e) => e.it.n === it.n);
      head.push(Object.assign({}, found || { id, it, score: 0 }, { curated: true }));
    });
    if (!head.length) return;
    r.list = head.concat(r.list.filter((e) => !seen.has(e.it.n))).slice(0, (r.pair ? 2 : 1) + BIS_ALTS);
  });
}

function bisData(ph) {
  const key = bisCtx() + "|" + ph.key;
  if (bisCache.has(key)) return bisCache.get(key);
  const spec = currentSpec();
  const gear = computeGear(spec, bisOpts(ph));
  const rows = bisRows(spec, gear);
  if (state.bisGuide) applyRefBis(rows, ph);
  const ranks = {};
  rows.forEach((r) => r.list.forEach((e, i) => {
    const prev = ranks[e.it.n];
    if (!prev || prev.i > i) ranks[e.it.n] = { i, label: bisLabel(i, r.pair) };
  }));
  const pos = {};
  Object.entries(gear.pools).forEach(([pk, list]) => list.forEach((e, i) => { const prev = pos[e.it.n]; if (!prev || i < prev.i) pos[e.it.n] = { i, n: list.length, pk }; }));
  const data = { rows, ranks, totals: gear.totals, caps: gear.caps, pos, pools: gear.pools };
  bisCache.set(key, data);
  if (bisCache.size > 18) bisCache.delete(bisCache.keys().next().value);
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
  const dict = ENG.gemNotesEn || {};
  return str.replace(/\(([^)]*)\)/g, (m, g) => {
    const k = g.replace(/ ID: \d+/g, "").trim();
    if (dict[k]) return "(" + dict[k] + ")";
    let x = g;
    NOTE_EN.forEach(([re, to]) => { x = x.replace(re, to); });
    return ES_MARK.test(x) ? "" : "(" + x + ")";
  }).replace(/ ID: \d+/g, "").replace(/\s+\(\)/g, "").replace(/\s+$/, "");
}

const gemColorName = (c) => (GEM_COLORS[c] || [c, c])[state.lang === "en" ? 1 : 0];

const gemLink = (g) => '<a class="gem-link" href="https://wotlk.evowow.com/?item=' + g.id + '" target="_blank" rel="noopener">' + esc(g.name) + "</a>";

const enchLink = (g) => (g.kind === "item" && g.id ? '<a class="gem-link" href="https://wotlk.evowow.com/?item=' + g.id + '" target="_blank" rel="noopener">' + esc(g.name) + "</a>" : '<a class="gem-link" href="https://wotlk.evowow.com/?search=' + encodeURIComponent(g.name) + '" target="_blank" rel="noopener">' + esc(g.name) + "</a>");

const refFor = () => (ENG.refGems || {})[state.cls + "|" + state.spec] || null;

function gemPlan(it, ref, w) {
  const cols = it.sg || [];
  if (!cols.length) return null;
  const gv = (g) => Object.entries(g.st || {}).reduce((a, [k, v]) => a + v * (w[k] || 0), 0);
  const best = (list) => (list || []).reduce((m, g) => (!m || gv(g) > gv(m) ? g : m), null);
  const any = best([].concat(ref.red, ref.yellow, ref.blue));
  const matched = cols.map((c) => (c === "prismatic" ? any : best(ref[c]) || any));
  const bonusVal = Object.entries(it.sb || {}).reduce((a, [k, v]) => a + v * (w[k] || 0), 0);
  const sumM = matched.reduce((a, g) => a + (g ? gv(g) : 0), 0) + bonusVal;
  const sumA = cols.length * (any ? gv(any) : 0);
  const respect = bonusVal > 0 && sumM >= sumA;
  return { gems: respect ? matched : cols.map(() => any), respect, bonus: it.sb || {} };
}

const gemColorOf = (ref, g) => (ref.red.includes(g) ? "red" : ref.yellow.includes(g) ? "yellow" : ref.blue.includes(g) ? "blue" : "prismatic");
// Kit de armadura de peletería (+18 Aguante): alternativa para tanques en pecho y pies (ID de objeto confirmado en Wowhead).

const ENCH_EXTRA = [{ name: "Heavy Borean Armor Kit", id: 38376, kind: "item", slots: ["chest", "feet"], st: { sta: 18 }, stats: "+18 Stamina", kit: true }];

const sameStatKeys = (a, b) => { const ka = Object.keys(a.st || {}).sort().join(), kb = Object.keys(b.st || {}).sort().join(); return !!ka && ka === kb; };

const statTotal = (g) => Object.values(g.st || {}).reduce((a, v) => a + v, 0);

function enchChoices(slot, ref, spec) {
  const prim = ref.enchants[slot];
  if (!prim) return null;
  const extras = spec.role === "tank" ? ENCH_EXTRA.filter((x) => x.slots.includes(slot)) : [];
  const others = (prim.alts || []).concat(extras).filter((x, i, arr) => x.name !== prim.name && arr.findIndex((y) => y.name === x.name) === i);
  let best = prim;
  others.forEach((x) => { if (sameStatKeys(best, x) && statTotal(x) > statTotal(best)) best = x; });
  const key = (x) => (sameStatKeys(best, x) ? statTotal(x) : -1);
  return { prim, best, others: [prim].concat(others).filter((x) => x !== best).sort((a, b) => key(b) - key(a)) };
}

function enchHtml(slot, ref, spec, w, compact) {
  const c = enchChoices(slot, ref, spec);
  if (!c) return "";
  const stat = (g) => (g.stats ? " " + noteText(g.stats) : "");
  const val = (g) => enchValueText(g, spec, w);
  let h = enchLink(c.best) + ' <span class="bis-fx-st">' + esc(noteText(c.best.stats || "")) + val(c.best) + "</span>";
  const short = (g) => noteText(g.stats || "").replace(/\s*\(.*$/, "");
  if (c.best !== c.prim) {
    const stName = partLabel(Object.keys(c.best.st)[0]).toLowerCase(), why = /speed/i.test(c.prim.stats || "") ? L("por la velocidad", "for the speed") : L("por su efecto extra", "for its extra effect");
    h += '<span class="bis-fx-note">' + L("La guía de Icy Veins recomienda " + c.prim.name + " (" + short(c.prim) + ") " + why + "; esta opción da más " + stName + ".", "The Icy Veins guide recommends " + c.prim.name + " (" + short(c.prim) + ") " + why + "; this option gives more " + stName + ".") + "</span>";
  }
  if (!compact && c.others.length) h += '<span class="bis-fx-note">' + L("Otras opciones: ", "Other options: ") + c.others.map((x) => esc(x.name) + (short(x) ? " (" + esc(short(x)) + ")" : "")).join(" · ") + "</span>";
  return h;
}

function bisFx(r) {
  const ref = refFor(), e = r.list[0];
  if (!ref || !e) return "";
  const parts = [], spec = currentSpec(), w = weightsFor(spec, false, 80);
  const plan = gemPlan(e.it, ref, w);
  if (plan || e.it.mt) {
    const counts = [];
    (plan ? plan.gems : []).filter(Boolean).forEach((g) => { const f = counts.find((c) => c.g === g); if (f) f.n++; else counts.push({ g, n: 1 }); });
    const gems = counts.map((c) => '<span class="gem g-' + gemColorOf(ref, c.g) + '"></span>' + (c.n > 1 ? c.n + "× " : "") + gemLink(c.g));
    if (e.it.mt && ref.meta) gems.unshift('<span class="gem g-meta"></span>' + gemLink(ref.meta));
    const bonusTxt = plan && Object.keys(plan.bonus).length ? Object.entries(plan.bonus).map(([k, v]) => "+" + v + " " + partLabel(k)).join(" ") : "";
    const how = !plan || !bonusTxt ? "" : plan.respect ? ' <span class="bis-fx-st">· ' + L("respeta los colores: bonus ", "match colors: bonus ") + esc(bonusTxt) + "</span>" : ' <span class="bis-fx-st">· ' + L("ignora el bonus (", "ignore the bonus (") + esc(bonusTxt) + ")</span>";
    if (gems.length) parts.push('<div class="bis-fx-row"><b>' + t("gemSockets") + "</b> " + gems.join(" · ") + how + "</div>");
  }
  if (ref.enchants[r.slot]) parts.push('<div class="bis-fx-row"><b>' + t("gemEnchant") + "</b> " + enchHtml(r.slot, ref, spec, w, true) + "</div>");
  return parts.length ? '<div class="bis-fx">' + parts.join("") + "</div>" : "";
}

function enchValueText(en, spec, w) {
  const total = Object.entries(en.st || {}).reduce((a, [k, v]) => a + v * (w[k] || 0), 0), main = w[spec.primary] || 0;
  if (!total || !main) return "";
  return " · " + L("equivale a ≈ ", "worth ≈ ") + Math.round(total / main) + " " + partLabel(spec.primary);
}

function renderGems() {
  const ref = refFor(), box = $("gemBody");
  $("gemSpec").textContent = state.cls + " · " + state.spec;
  if (!ref) { box.innerHTML = ""; return; }
  const col = (title, list) => '<article class="bis-card"><h3>' + esc(title) + "</h3>" + (list.length ? "<ol class=\"gem-list\">" + list.map((g, i) => "<li>" + (i === 0 ? rankPill("1ª") : rankPill(i + 1 + "ª")) + "<div>" + gemLink(g) + '<span class="bis-sub">' + esc(noteText(g.stats)) + "</span></div></li>").join("") + "</ol>" : '<div class="bis-empty">—</div>') + "</article>";
  const metaList = ref.meta ? [ref.meta] : [];
  const slotsOrder = ["head", "shoulder", "back", "chest", "wrist", "hands", "waist", "legs", "feet", "mainhand", "offhand", "ranged"];
  const labels = SLOT_LABEL[state.lang] || SLOT_LABEL.es;
  const ench = slotsOrder.filter((k) => ref.enchants[k]).map((k) => "<li><span class=\"gem-slot\">" + esc(labels[k] || k) + '</span><div class="gem-ench-cell">' + enchHtml(k, ref, currentSpec(), weightsFor(currentSpec(), false, 80), false) + "</div></li>").join("");
  const rule = state.lang === "en" ? ref.ruleEn || "" : ref.rule;
  box.innerHTML = '<div class="bis-grid">' + col(t("gemMeta"), metaList) + col(gemColorName("red"), ref.red) + col(gemColorName("yellow"), ref.yellow) + col(gemColorName("blue"), ref.blue) +
    '<article class="bis-card gem-ench"><h3>' + t("gemEnchants") + "</h3><ol class=\"gem-list\">" + ench + "</ol></article></div>" +
    (rule ? '<p class="gem-rule"><b>' + t("gemRule") + "</b> " + esc(rule) + "</p>" : "");
}

function bisScore(spec, w, it) {
  const r = evalEquip(levelItem(it, 80), spec, w, { level: 80, faction: state.faction });
  return r ? r.score : 0;
}

const ROUTE_MIN_GAIN = 0.03;

const rowSlots = (r) => (r.pair ? [r.slot, r.slot.slice(0, -1) + "2"] : [r.slot]);

const rowPool = (r) => (r.slot === "relic" ? "ranged" : r.slot.replace(/\d$/, ""));

function equippedMark(r, it) {
  const i = r.list.findIndex((e) => e.it.n === it.n);
  return ' <span class="up-mine">✓ ' + L("lo llevas", "equipped") + "</span>" + (i >= 0 ? " " + rankPill(bisLabel(i, r.pair)) : ' <span class="up-out">' + L("fuera del top", "outside the top") + "</span>");
}

function rowCurrent(r, spec, w) {
  const eq = equippedMap(), items = rowSlots(r).map((sl) => (eq[sl] && gearItem(eq[sl])) || null);
  const scores = items.map((it) => (it ? bisScore(spec, w, it) : 0)), owned = items.filter(Boolean);
  return { items: owned, names: new Set(owned.map((it) => it.n)), score: r.pair ? Math.min(...scores) : scores[0] || 0, sum: scores.reduce((a, c) => a + c, 0), hasAny: owned.length > 0 };
}

function rowUpgrades(r, data, spec, w, cur) {
  const weapon = ["mainhand", "offhand", "ranged", "relic"].includes(r.slot);
  const cands = (weapon ? [] : (data.pools[rowPool(r)] || []).slice(0, 90).map((e) => e.it)).concat(r.list.map((e) => e.it));
  const seen = new Set(), out = [];
  cands.forEach((it) => {
    if (seen.has(it.n) || cur.names.has(it.n)) return;
    seen.add(it.n);
    const sc = bisScore(spec, w, it);
    if (!sc) return;
    const gain = cur.score > 0 ? (sc - cur.score) / cur.score : Infinity;
    if (gain >= ROUTE_MIN_GAIN) out.push({ it, sc, gain });
  });
  return out.sort((a, b) => b.sc - a.sc);
}

function upLine(x, r, withGain) {
  const i = r.list.findIndex((e) => e.it.n === x.it.n), lab = i >= 0 ? bisLabel(i, r.pair) : "";
  const gain = !withGain ? '<span class="up-gain empty">' + L("conseguir", "get") + "</span>" : x.gain === Infinity ? '<span class="up-gain empty">' + L("pieza vacía", "empty slot") + "</span>" : '<span class="up-gain">+' + Math.round(x.gain * 100) + " %</span>";
  return "<li>" + gain + "<span>" + itemLink(gameId(x.it), false, "bis-name") + ' <span class="bis-sub" style="display:inline">iLvl ' + x.it.ilvl + " · " + badgeHtml(obtainInfo(x.it)) + "</span>" + (lab ? " " + rankPill(lab) : "") + "</span></li>";
}

function gameId(it) { return Object.keys(GEAR_ITEMS).find((id) => GEAR_ITEMS[id] === it || GEAR_ITEMS[id].n === it.n) || ""; }

function renderRoute(data, ph) {
  const spec = currentSpec(), w = weightsFor(spec, false, 80), labels = SLOT_LABEL[state.lang] || SLOT_LABEL.es;
  $("routeHeading").textContent = L("Tu ruta a nivel 80", "Your level 80 route");
  $("routeIntro").textContent = L("Tres pasos: indica lo que ya tienes, elige hasta dónde está abierto tu servidor y mira qué te mejora y dónde conseguirlo. Todo se calcula para nivel 80.", "Three steps: enter what you already have, choose how far your server is open, and see what upgrades you and where to get it. Everything is calculated for level 80.");
  $("routeSpec").textContent = state.cls + " · " + state.spec;
  $("routeS1").textContent = L("Tu equipo actual", "Your current gear");
  $("routeS1Hint").textContent = L("Marca lo que llevas puesto (o pulsa «Importar»). Si empiezas de cero, déjalo vacío y verás qué conseguir primero.", "Mark what you are wearing (or press \"Import\"). If you are starting from scratch, leave it empty and you will see what to get first.");
  $("routeS2").textContent = L("Etapa de tu servidor", "Your server's stage");
  $("routeS2Hint").textContent = L("Elige hasta dónde tienes abierto: «Recién 80» no usa heroicas; «Heroicas» suma todas las mazmorras; de T7 a T10 se van abriendo las bandas.", "Choose how far you are open: \"Fresh 80\" uses no heroics; \"Heroics\" adds every dungeon; T7 to T10 open the raids one by one.");
  $("routeS3").textContent = L("Qué te mejora y dónde conseguirlo", "What upgrades you and where to get it");
  const hasGear = Object.keys(equippedMap()).length > 0;
  let tgt = 0, got = 0;
  const rows = data.rows.filter((r) => r.list.length).map((r) => {
    const cur = rowCurrent(r, spec, w), ups = rowUpgrades(r, data, spec, w, cur), take = r.pair ? 2 : 1;
    tgt += r.list.slice(0, take).reduce((a, e) => a + bisScore(spec, w, e.it), 0);
    got += cur.sum;
    return { r, cur, ups, label: r.pair ? bisPairLabel(r.slot) : labels[r.slot] || r.slot };
  });
  const pct = tgt ? Math.min(100, Math.round((got / tgt) * 100)) : 0;
  const withUps = rows.filter((x) => x.ups.length), without = rows.filter((x) => !x.ups.length);
  withUps.sort((a, b) => (b.ups[0].gain === Infinity ? 1e9 : b.ups[0].gain) - (a.ups[0].gain === Infinity ? 1e9 : a.ups[0].gain));
  const stage = bisTabLabel(ph);
  $("routeSummary").innerHTML = hasGear
    ? L("En <b>" + esc(stage) + "</b> tu equipo actual cubre un <b>" + pct + " %</b> del BiS. Tienes mejoras posibles en <b>" + withUps.length + "</b> de " + rows.length + " slots; empieza por los de arriba (mayor mejora).", "In <b>" + esc(stage) + "</b> your current gear covers <b>" + pct + "%</b> of the BiS. You have possible upgrades in <b>" + withUps.length + "</b> of " + rows.length + " slots; start with the ones on top (biggest upgrade).")
    : L("Aún no indicaste tu equipo (paso 1). Esto es lo primero que te conviene conseguir en cada slot en <b>" + esc(stage) + "</b>.", "You have not entered your gear yet (step 1). This is what to get first in each slot in <b>" + esc(stage) + "</b>.");
  if (hasGear) $("routeSummary").insertAdjacentHTML("beforeend", ' <button type="button" class="mini-btn" id="openRank">' + L("Ver el ranking con tus piezas marcadas", "See the ranking with your pieces marked") + "</button>");
  const shown = hasGear ? 3 : 2;
  $("routeUpgrades").innerHTML = withUps.map((x) => {
    const have = x.cur.hasAny ? L("Llevas: ", "You wear: ") + x.cur.items.map((it) => esc(it.n) + " (iLvl " + it.ilvl + ")" + equippedMark(x.r, it)).join(" · ") : L("Sin pieza", "Nothing equipped");
    const head = x.ups.slice(0, shown), rest = hasGear ? x.ups.slice(shown, 30) : [];
    return '<div class="up-row"><div class="up-head"><span class="up-slot">' + esc(x.label) + '</span><span class="up-have">' + have + '</span></div><ul class="up-list">' + head.map((u) => upLine(u, x.r, hasGear)).join("") + "</ul>" +
      (rest.length ? '<details class="up-more"><summary>' + L("Ver " + rest.length + " mejoras más", "See " + rest.length + " more upgrades") + '</summary><ul class="up-list">' + rest.map((u) => upLine(u, x.r, hasGear)).join("") + "</ul></details>" : "") + "</div>";
  }).join("") + (hasGear && without.length ? '<div class="up-done">✓ ' + L("Sin mejoras en esta etapa (ya llevas lo mejor): ", "No upgrades in this stage (you already wear the best): ") + without.map((x) => '<span class="up-chip">' + esc(x.label) + (x.cur.items[0] ? equippedMark(x.r, x.cur.items[0]).replace(/<span class="up-mine">.*?<\/span>/, "") : "") + "</span>").join(" ") + "</div>" : "");
  renderPlan(withUps, hasGear);
}

function sourceGroup(it) {
  const s = it.src || {}, o = obtainInfo(it);
  if (s.t === "Drop") return { key: "D|" + (s.zid || s.z) + "|" + (s.n || ""), title: [s.z, s.n || L("drop de la zona", "zone drop"), s.df ? diffLabel(s.df) : ""].filter(Boolean).join(" · "), o };
  if (s.t === "Vendor") return { key: "V|" + (s.n || "") + "|" + (s.cur || ""), title: [s.n, s.cur === "gold" ? L("Oro", "Gold") : s.cur === "reputation" ? L("Reputación", "Reputation") : s.cur ? currencyLabel(s.cur) : ""].filter(Boolean).join(" · "), o };
  return { key: "X|" + s.t + "|" + o.detail, title: o.detail, o };
}

function renderPlan(withUps, hasGear) {
  const groups = new Map();
  withUps.forEach((x) => {
    const u = x.ups[0], g = sourceGroup(u.it);
    if (!groups.has(g.key)) groups.set(g.key, Object.assign({ items: [] }, g));
    groups.get(g.key).items.push({ slot: x.label, u });
  });
  const list = [...groups.values()].sort((a, b) => b.items.length - a.items.length || a.title.localeCompare(b.title));
  $("bisPlan").innerHTML = !list.length ? "" : "<h3>" + L("Dónde farmearlo (mejor mejora por slot, agrupado por fuente)", "Where to farm it (best upgrade per slot, grouped by source)") + "</h3>" +
    '<div class="plan-grid">' + list.map((g) => '<article class="bis-card"><p class="card-title"><span class="src-badge src-' + g.o.cls + '">' + esc(g.o.kind) + "</span> " + esc(g.title) + " · " + g.items.length + "</p><ol class=\"plan-list\">" +
      g.items.map((x) => "<li><span class=\"gem-slot\">" + esc(x.slot) + "</span><div>" + itemLink(gameId(x.u.it), false, "bis-name") + '<span class="bis-sub">iLvl ' + x.u.it.ilvl + (x.u.gain === Infinity ? "" : " · +" + Math.round(x.u.gain * 100) + " %") + "</span></div></li>").join("") + "</ol></article>").join("") + "</div>";
}

function bisLater(r, ph) {
  const start = BIS_TABS.findIndex((t) => t.key === ph.key);
  let prev = r.list[0] && r.list[0].it.n;
  const out = [];
  for (let i = start + 1; i < BIS_TABS.length; i++) {
    const row = bisData(BIS_TABS[i]).rows.find((x) => x.slot === r.slot);
    const top = row && row.list[0];
    if (top && top.it.n !== prev) { out.push({ tab: BIS_TABS[i], it: top.it, id: top.id }); prev = top.it.n; }
  }
  return out;
}

function bisLaterHtml(r, ph) {
  const later = bisLater(r, ph).slice(0, 3);
  if (!later.length) return "";
  return '<div class="bis-later"><b>' + L("Más adelante", "Later") + "</b> " + later.map((x) => "<span><em>" + esc(bisTabShort(x.tab)) + "</em> " + itemLink(x.id, false, "gem-link") + "</span>").join(" · ") + "</div>";
}

function bisCard(r, data, ph) {
  const owned = bisOwned(r);
  const items = r.list.map((e, i) => {
    const lab = bisLabel(i, r.pair), isAlt = lab.startsWith("ALT");
    const icon = e.it.i ? '<img class="bis-ic" src="' + esc(iconSrc(e.it.i)) + '" alt="" loading="lazy" onerror="this.style.visibility=\'hidden\'">' : '<span class="bis-ic"></span>';
    const have = owned.has(e.it.n);
    return '<li' + (have ? ' class="owned"' : "") + ">" + rankPill(lab) + icon + "<div>" + itemLink(e.id, false, "bis-name") + (e.curated ? '<span class="bis-guide-tag" title="Icy Veins">' + L("guía", "guide") + "</span>" : "") + (have ? '<span class="bis-have">✓ ' + t("bisHave") + "</span>" : "") + (isAlt ? bisCompletes(e, data) : "") +
      '<span class="bis-sub">iLvl ' + e.it.ilvl + " · " + badgeHtml(obtainInfo(e.it)) + "</span></div></li>";
  }).join("");
  return '<article class="bis-card"><h3>' + esc(bisPairLabel(r.slot)) + "</h3>" + (items ? "<ol>" + items + "</ol>" + bisLaterHtml(r, ph) + bisFx(r) : '<div class="bis-empty">' + t("bisEmptySlot") + "</div>") + "</article>";
}

const GEM_FAMILY = [[/Cardinal Ruby/i, ["red"]], [/Majestic Zircon/i, ["blue"]], [/King's Amber/i, ["yellow"]], [/Dreadstone/i, ["red", "blue"]], [/Ametrine/i, ["red", "yellow"]], [/Eye of Zul/i, ["yellow", "blue"]], [/Nightmare Tear/i, ["red", "yellow", "blue"]]];

const gemColors = (name) => { const f = GEM_FAMILY.find(([re]) => re.test(name || "")); return f ? f[1] : []; };

const colorWord = (c, n) => ({ red: ["roja", "rojas", "red"], yellow: ["amarilla", "amarillas", "yellow"], blue: ["azul", "azules", "blue"] }[c] || [c, c, c]);

const colorNoun = (c, n) => { const w = colorWord(c, n); return state.lang === "en" ? w[2] : n > 1 ? w[1] : w[0]; };
/* Plan de meta-gema del set BiS: parte de las gemas recomendadas por pieza, cuenta los colores REALES de cada gema
   (una morada cuenta como roja y azul; el Nightmare Tear, como las tres) y, si falta alguno, cambia las gemas que
   menos valor pierdan, cuidando de no perder el bonus de socket donde ya se aprovechaba. */

function metaPlan(data) {
  const spec = currentSpec(), G = (ENG.gems || {})[state.cls + "|" + state.spec], M = G && G.meta, ref = refFor();
  if (!M || !M.requires || !ref) return "";
  const w = weightsFor(spec, false, 80);
  if (!w.gc || !(w.gc.meta > 0) || !data.rows.some((r) => r.list[0] && r.list[0].it.mt)) return "";
  const labels = SLOT_LABEL[state.lang] || SLOT_LABEL.es;
  const gv = (g) => Object.entries(g.st || {}).reduce((a, [k, v]) => a + v * (w[k] || 0), 0);
  const socks = [];
  data.rows.forEach((r) => r.list.slice(0, r.pair ? 2 : 1).forEach((e) => {
    const plan = gemPlan(e.it, ref, w);
    if (!plan) return;
    const bonus = Object.entries(e.it.sb || {}).reduce((a, [k, v]) => a + v * (w[k] || 0), 0);
    (e.it.sg || []).forEach((c, i) => socks.push({ slot: r.pair ? bisPairLabel(r.slot) : labels[r.slot] || r.slot, name: e.it.n, c, gem: plan.gems[i], bonus: plan.respect ? bonus / Math.max(1, (e.it.sg || []).length) : 0, swap: null }));
  }));
  if (!socks.length) return "";
  const have = { red: 0, yellow: 0, blue: 0 };
  socks.forEach((x) => gemColors(x.gem && x.gem.name).forEach((c) => { have[c]++; }));
  const need = {};
  Object.entries(M.requires).forEach(([c, n]) => { need[c] = Math.max(0, n - have[c]); });
  const pool = [].concat(ref.red, ref.yellow, ref.blue).filter((g, i, a) => a.findIndex((h) => h.name === g.name) === i);
  const tear = ENG.metaGems && ENG.metaGems.wildcard ? { id: ENG.metaGems.wildcard.id, name: ENG.metaGems.wildcard.name, st: ENG.metaGems.wildcard.st } : null;
  if (tear) pool.push(tear);
  let tearUsed = false;
  const unmet = () => Object.values(need).reduce((a, n) => a + n, 0);
  const fits = (g, c) => c === "prismatic" || gemColors(g.name).includes(c);
  while (unmet() > 0) {
    let best = null;
    socks.forEach((x) => {
      if (x.swap) return;
      pool.forEach((g) => {
        if (g === tear && tearUsed) return;
        const gain = gemColors(g.name).filter((c) => need[c] > 0).length;
        if (!gain) return;
        const loss = Math.max(0, gv(x.gem || {}) - gv(g)) + (x.bonus && !fits(g, x.c) ? x.bonus : 0);
        const score = loss / gain;
        if (!best || score < best.score - 1e-9 || (Math.abs(score - best.score) < 1e-9 && gain > best.gain)) best = { x, g, gain, score };
      });
    });
    if (!best) break;
    best.x.swap = best.g;
    if (best.g === tear) tearUsed = true;
    gemColors(best.g.name).forEach((c) => { if (need[c] > 0) need[c]--; });
  }
  const reqTxt = Object.entries(M.requires).map(([c, n]) => n + " " + colorNoun(c, n)).join(" + ");
  const head = "<b>" + L("Meta-gema", "Meta gem") + ": " + esc(M.name) + "</b> — " + L("requiere ", "requires ") + esc(reqTxt) + ". ";
  const swaps = socks.filter((x) => x.swap);
  if (!swaps.length) return head + L("Con las gemas recomendadas de este set ya se activa, sin cambios.", "The recommended gems of this set already activate it, no changes needed.");
  const groups = new Map();
  swaps.forEach((x) => { const k = x.swap.name; if (!groups.has(k)) groups.set(k, { g: x.swap, where: [] }); groups.get(k).where.push(x.slot + " (" + x.name + ")"); });
  const colorsOf = (g) => gemColors(g.name).map((c) => colorNoun(c, 1)).join("/");
  const steps = [...groups.values()].map(({ g, where }) => where.length + " × " + g.name + (g.name === (tear && tear.name) ? "" : " (" + colorsOf(g) + ")") + " " + L("en ", "in ") + where.join(", "));
  return head + L("Para activarla cambia ", "To activate it, swap in ") + esc(steps.join(" · ")) + (unmet() > 0 ? " " + L("(con las gemas de la guía no llega a cubrir todo el requisito).", "(the guide's gems cannot cover the whole requirement).") : ".");
}
/* ---------- Buscador: ¿me sirve este objeto? ---------- */

const BIS_FIRST = (it) => { if (!raidGated(it)) return "PR"; const n = it.ph || 4; return n <= 1 ? "T7" : n === 2 ? "T8" : n === 3 ? "T9" : "T10"; };

function bisItemStatus(it, ph) {
  const spec = currentSpec(), w = weightsFor(spec, false, 80), o = bisOpts(ph), it80 = levelItem(it, 80);
  const r = evalItem(it80, spec, w, o, true, false);
  if (!r) return { kind: "class" };
  if (!r.rel) return { kind: "useless" };
  const rs = [];
  if (o.fresh && !freshAccessible(it80)) rs.push("fresh");
  if (it80.pvp) rs.push("pvp");
  if (it80.raid && o.scope !== "raid") rs.push("raid");
  if (o.raidOpen != null ? raidGated(it80) && it80.ph > o.raidOpen : o.phase && it80.ph > o.phase) rs.push("phase");
  const avg = o.noHeroicGate ? null : o.assumeAvg != null ? o.assumeAvg : averageItemLevel(spec);
  if (avg != null && isHeroicOnlyDrop(it80) && avg < heroicRequirement(it80.src.zid)) rs.push("heroic");
  if (rs.length) return { kind: "blocked", reasons: rs, it: it80 };
  const p = bisData(ph).pos[it.n];
  return p ? { kind: "pos", i: p.i, n: p.n, pk: p.pk } : { kind: "useless" };
}

function bisStatusText(st) {
  if (st.kind === "top") return rankPill(st.label);
  if (st.kind === "pos") return L("puesto " + (st.i + 1) + " de " + st.n + " (fuera del top)", "rank " + (st.i + 1) + " of " + st.n + " (outside the top)");
  if (st.kind === "blocked") {
    const it = st.it, first = BIS_FIRST(it), req = it.src && it.src.zid ? heroicRequirement(it.src.zid) : "?";
    const why = { phase: L("aún no: se abre en " + first, "not yet: opens in " + first), raid: L("es de banda", "raid item"), pvp: "PvP", fresh: L("no entra en Recién 80", "not part of Fresh 80"),
      heroic: L("heroica: se abre con iLvl medio " + req, "heroic: opens at average item level " + req) };
    return st.reasons.map((r) => why[r] || r).join(" · ");
  }
  return "—";
}

function bisFindShow(id) {
  const it = gearItem(id), out = $("bisFindOut");
  if (!it) { out.innerHTML = ""; return; }
  const who = state.cls + " " + state.spec, labels = SLOT_LABEL[state.lang] || SLOT_LABEL.es;
  const rows = BIS_TABS.map((ph) => {
    const data = bisData(ph);
    for (const r of data.rows) { const i = r.list.findIndex((e) => e.it.n === it.n); if (i >= 0) return { ph, st: { kind: "top", label: bisLabel(i, r.pair), row: r } }; }
    return { ph, st: bisItemStatus(it, ph) };
  });
  const first = BIS_FIRST(it), zone = it.src && it.src.z ? it.src.z : "";
  const avail = !raidGated(it) ? L("Se consigue sin entrar a banda: disponible desde PR.", "No raid needed: available from PR.") : L("Es de banda" + (zone ? " (" + zone + ")" : "") + ": solo estará disponible cuando abra " + first + ".", "Raid gear" + (zone ? " (" + zone + ")" : "") + ": it will only be available once " + first + " opens.");
  const tops = rows.filter((x) => x.st.kind === "top"), poss = rows.filter((x) => x.st.kind === "pos");
  const usable = rows.some((x) => x.st.kind === "top" || x.st.kind === "pos" || x.st.kind === "blocked");
  let cls = "maybe", msg;
  if (!usable) {
    cls = "no";
    msg = rows.every((x) => x.st.kind === "class") ? L("No te sirve (" + who + "): tu clase no puede equiparlo (tipo de armadura o de arma).", "It does not suit you (" + who + "): your class cannot equip it (armor or weapon type).") : L("No te sirve (" + who + "): no aporta estadísticas útiles a esta especialidad.", "It does not suit you (" + who + "): it has no useful stats for this spec.");
  } else if (tops.length) {
    cls = "yes";
    const byLabel = new Map();
    tops.forEach((x) => { const k = x.st.label; byLabel.set(k, (byLabel.get(k) || []).concat(bisTabShort(x.ph))); });
    msg = L("Sí te sirve (" + who + "): ", "Yes, it suits you (" + who + "): ") + [...byLabel].map(([k, v]) => k + L(" en ", " in ") + v.join(", ")).join("; ") + ".";
  } else if (poss.length) {
    const b = poss.slice().sort((a, c) => a.st.i / a.st.n - c.st.i / c.st.n)[0];
    msg = L("Te sirve, pero hay mejores opciones: en su mejor pestaña (" + bisTabShort(b.ph) + ") es el puesto " + (b.st.i + 1) + " de " + b.st.n + ".", "It works for you, but there are better options: in its best tab (" + bisTabShort(b.ph) + ") it ranks " + (b.st.i + 1) + " of " + b.st.n + ".");
  } else msg = L("Podría servirte, pero hoy está bloqueado: " + bisStatusText(rows.find((x) => x.st.kind === "blocked").st) + ".", "It could suit you, but it is blocked today: " + bisStatusText(rows.find((x) => x.st.kind === "blocked").st) + ".");
  // comparación con el BiS de la pestaña que estás viendo
  let cmp = "", rowSel = null;
  const cur = rows.find((x) => x.ph.key === state.bisPhase);
  if (cur && (cur.st.kind === "top" || cur.st.kind === "pos")) {
    const data = bisData(cur.ph), spec = currentSpec(), w = weightsFor(spec, false, 80);
    const row = (rowSel = cur.st.kind === "top" ? cur.st.row : data.rows.find((r) => r.slot.replace(/\d$/, "") === cur.st.pk));
    if (row && row.list[0] && row.list[0].it.n !== it.n) {
      const mine = bisScore(spec, w, it), best = bisScore(spec, w, row.list[0].it);
      if (best > 0) cmp = '<p class="bis-find-cmp">' + L("En «" + bisTabShort(cur.ph) + "» el BiS de " + (row.pair ? bisPairLabel(row.slot) : labels[row.slot] || row.slot) + " es " + row.list[0].it.n + ": tu objeto vale un " + Math.round((mine / best) * 100) + " % de ese BiS.", "In \"" + bisTabShort(cur.ph) + "\" the BiS for " + (row.pair ? bisPairLabel(row.slot) : labels[row.slot] || row.slot) + " is " + row.list[0].it.n + ": your item is worth " + Math.round((mine / best) * 100) + "% of it.") + "</p>";
    }
  }
  if (rowSel) {
    const spec2 = currentSpec(), w2 = weightsFor(spec2, false, 80), c2 = rowCurrent(rowSel, spec2, w2);
    if (c2.hasAny && c2.score > 0) {
      const g = Math.round(((bisScore(spec2, w2, it) - c2.score) / c2.score) * 100), have = c2.items.map((x) => x.n).join(" · ");
      cmp += '<p class="bis-find-cmp">' + (g >= 3 ? L("Frente a lo que llevas (" + have + "): te mejora un +" + g + " %.", "Compared with what you wear (" + have + "): it upgrades you by +" + g + "%.") : g <= -3 ? L("Frente a lo que llevas (" + have + "): es peor (" + g + " %), no te conviene.", "Compared with what you wear (" + have + "): it is worse (" + g + "%), not worth it.") : L("Frente a lo que llevas (" + have + "): es prácticamente igual (" + (g >= 0 ? "+" : "") + g + " %).", "Compared with what you wear (" + have + "): practically the same (" + (g >= 0 ? "+" : "") + g + "%).")) + "</p>";
    }
  }
  out.innerHTML = '<div class="bis-find-card"><div>' + itemLink(id, false, "bis-name") + ' <span class="bis-sub" style="display:inline">iLvl ' + it.ilvl + " · " + esc(it.sub || "") + " " + esc(labels[it.s] || it.s || "") + " · " + badgeHtml(obtainInfo(it)) + '</span></div><p class="bis-find-avail">' + esc(avail) + '</p><p class="verdict ' + cls + '">' + esc(msg) + "</p>" + cmp +
    '<ul class="bis-find-tabs">' + rows.map((x) => "<li><b>" + esc(bisTabShort(x.ph)) + "</b><span>" + bisStatusText(x.st) + "</span></li>").join("") + "</ul></div>";
  out.dataset.id = id;
}

let bisFindMatches = [];

function bisFindSearch(q) {
  const list = $("bisFindList"), t = String(q || "").trim();
  const num = /(?:item=)?(\d{4,6})\s*$/.exec(t);
  if (num && gearItem(num[1])) { list.hidden = true; bisFindShow(num[1]); return; }
  if (t.length < 3) { list.hidden = true; return; }
  const k = eqNorm(t);
  bisFindMatches = Object.keys(GEAR_ITEMS).filter((id) => { const it = GEAR_ITEMS[id]; return (it.ilvl >= 100 || it.req >= 60) && eqNorm(it.n).includes(k); })
    .sort((a, b) => eqNorm(GEAR_ITEMS[a].n).indexOf(k) - eqNorm(GEAR_ITEMS[b].n).indexOf(k) || GEAR_ITEMS[b].ilvl - GEAR_ITEMS[a].ilvl).slice(0, 8);
  list.innerHTML = bisFindMatches.map((id, i) => '<li role="option" data-id="' + id + '"' + (i === 0 ? ' aria-selected="true"' : "") + "><span>" + esc(GEAR_ITEMS[id].n) + "</span><small>iLvl " + GEAR_ITEMS[id].ilvl + " · " + esc(((SLOT_LABEL[state.lang] || SLOT_LABEL.es)[GEAR_ITEMS[id].s]) || GEAR_ITEMS[id].s || "") + "</small></li>").join("");
  list.hidden = !bisFindMatches.length;
}

function renderBisFind() {
  $("bisFindLabel").textContent = L("¿Te salió un objeto? ¿Te sirve?", "Got a drop? Does it suit you?");
  $("bisFind").placeholder = L("Escribe el nombre (por ejemplo Titanium Links of Lore) o pega el enlace", "Type the name (for example Titanium Links of Lore) or paste the link");
  const cur = $("bisFindOut").dataset.id;
  if (cur) bisFindShow(cur);
}
$("bisFind").addEventListener("input", (e) => bisFindSearch(e.target.value));
$("bisFind").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && bisFindMatches.length && !$("bisFindList").hidden) { e.preventDefault(); const id = bisFindMatches[0]; $("bisFindOut").dataset.id = id; $("bisFindList").hidden = true; bisFindShow(id); }
  if (e.key === "Escape") $("bisFindList").hidden = true;
});
$("bisFindList").addEventListener("click", (e) => {
  const li = e.target.closest("li[data-id]");
  if (!li) return;
  $("bisFindOut").dataset.id = li.dataset.id; $("bisFind").value = GEAR_ITEMS[li.dataset.id].n; $("bisFindList").hidden = true; bisFindShow(li.dataset.id);
});
document.addEventListener("click", (e) => { if (!e.target.closest(".bis-find")) $("bisFindList").hidden = true; });

function renderBis(spec) {
  const ph = BIS_TABS.find((p) => p.key === state.bisPhase) || BIS_TABS[0];
  renderSeg($("bisTabs"), BIS_TABS.map((p) => ({ value: p.key, label: bisTabLabel(p) })), ph.key, (v) => { state.bisPhase = v; persist(); renderBis(currentSpec()); scheduleRefresh(); });
  $("bisSpec").textContent = state.cls + " · " + state.spec;
  $("bisHeading").textContent = t("bisTitle");
  $("bisIntro").textContent = t("bisIntro");
  const hasGuide = !!bisGuideFor(ph);
  $("bisPhaseNote").textContent = ph[state.lang === "en" ? "en" : "es"] + " " + (hasGuide ? (state.bisGuide ? L("BiS según la guía de referencia; las alternativas se completan con el cálculo de la herramienta.", "BiS from the reference guide; alternatives are filled in by the tool's calculation.") : L("Calculado por el motor de la herramienta.", "Calculated by the tool's engine.")) : ph.key === "F80" ? "" : L("Calculado por el motor (no hay guía de referencia para esta fase).", "Calculated by the engine (no reference guide for this phase)."));
  if (ph.key === "F80" || ph.key === "PR") {
    const avg = averageItemLevel(spec);
    if (avg != null) $("bisPhaseNote").textContent += " " + L("Tu iLvl medio: ", "Your average item level: ") + fmtIlvl(avg) + ".";
  }
  $("bisGuideBox").hidden = !hasGuide;
  $("bisGuide").checked = state.bisGuide;
  $("bisGuideText").textContent = L("Usar la guía de referencia como BiS", "Use the reference guide as BiS");
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
  $("bisGrid").innerHTML = data.rows.map((r) => bisCard(r, data, ph)).join("");
  renderBisFind();
  const mp = metaPlan(data);
  $("bisMeta").hidden = !mp;
  $("bisMeta").innerHTML = mp;
  renderGems();
  renderRoute(data, ph);
  const haveN = data.rows.filter((r) => bisOwned(r).size && r.list.some((e) => bisOwned(r).has(e.it.n))).length;
  $("bisOwnedNote").textContent = Object.keys(equippedMap()).length ? t("bisOwnedPre") + haveN + " / " + data.rows.length + t("bisOwnedPost") : t("bisOwnedNone");
}
/* ---------- Pesos de estadísticas editables ---------- */

export { BIS_PHASES, BIS_F80, BIS_TABS, bisTabShort, bisTabLabel, bisOpts, BIS_ALTS, bisCache, bisCtx, bisRows, bisGuideFor, applyRefBis, bisData, bisCompletes, bisPairLabel, bisOwned, GEM_COLORS, ES_MARK, NOTE_EN, noteText, gemColorName, gemLink, enchLink, refFor, gemPlan, gemColorOf, ENCH_EXTRA, sameStatKeys, statTotal, enchChoices, enchHtml, bisFx, enchValueText, renderGems, bisScore, ROUTE_MIN_GAIN, rowSlots, rowPool, equippedMark, rowCurrent, rowUpgrades, upLine, gameId, renderRoute, sourceGroup, renderPlan, bisLater, bisLaterHtml, bisCard, GEM_FAMILY, gemColors, colorWord, colorNoun, metaPlan, BIS_FIRST, bisItemStatus, bisStatusText, bisFindShow, bisFindMatches, bisFindSearch, renderBisFind, renderBis };
