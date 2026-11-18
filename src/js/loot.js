import { DATA } from "./data.js";
import {
  state, $, t, L, esc, SLOT_LABEL, gearKey, gearItem, itemHands, currentSpec, specSlots,
  equippedMap, equippedMainTwoHand, levelItem, poolOfSlot, titanGrip, persist, runtime,
  clearLootUndo, renderLootUndo, qColor, itemLink, pctDiff
} from "./core.js";
import { ENG, weightsFor, evalItem } from "./engine.js";
import { evalEquip, candidates, equippedEntry, targetEquipSlot, lootFilterForSlot } from "./equipment.js";
import { heroicAccess, fmtIlvl } from "./heroic.js";
import { badgeHtml, obtainInfo, diffLabel, partLabel } from "./format.js";

function equipLoot(id) {
  const spec = currentSpec(), source = gearItem(id);
  if (!source) return;
  const it = levelItem(source, state.level);
  const r = evalEquip(it, spec, weightsFor(spec, false, state.level), { level: state.level, faction: state.faction });
  if (!r || r.al > state.level) return;
  const slot = targetEquipSlot(spec, r.pk);
  if (!slot || (slot === "offhand" && equippedMainTwoHand(spec))) return;
  runtime.lastEquip = { key: gearKey(), gear: JSON.parse(JSON.stringify(equippedMap())), name: it.n };
  setEquipped(slot, id, { keepUndo: true });
}
function setEquipped(slot, id, opts) {
  if (!opts || !opts.keepUndo) clearLootUndo();
  const g = (state.gear[gearKey()] = state.gear[gearKey()] || {}), spec = currentSpec();
  if (slot === "offhand" && equippedMainTwoHand(spec)) return;
  if (id) g[slot] = id; else delete g[slot];
  if (slot === "mainhand") {
    const it = id && gearItem(id);
    if (it && itemHands(it) === 2 && !titanGrip(spec, state.level)) delete g.offhand;
  }
  persist();
  runtime.render();
}
function renderEquip(spec) {
  const grid = $("eqGrid"), pools = candidates(spec);
  const labels = SLOT_LABEL[state.lang] || SLOT_LABEL.es;
  const order = specSlots(spec), used = new Set();
  const pick = (slots) => slots.filter((slot) => {
    if (!order.includes(slot) || used.has(slot)) return false;
    used.add(slot);
    return true;
  });
  const slotHtml = (slot) => {
    const blocked = slot === "offhand" && equippedMainTwoHand(spec);
    const cur = blocked ? null : equippedEntry(spec, slot);
    const ph = blocked ? t("offhandBlocked") : t("eqPlaceholder");
    const active = state.lootSlot && lootFilterForSlot(slot) === state.lootSlot;
    return '<div class="eq-slot' + (active ? " is-active" : "") + '"><label for="eq-' + slot + '">' + (labels[slot] || slot) + '</label><div class="eq-field"><input id="eq-' + slot +
      '" type="text" autocomplete="off" data-slot="' + slot + '" placeholder="' + esc(ph) + '" value="' + esc(cur ? cur.it.n : "") + '"' + (blocked ? " disabled" : "") + '>' +
      (cur ? '<button type="button" class="eq-x" data-slot="' + slot + '" aria-label="' + esc(t("eqRemove")) + '">✕</button>' : "") + '<ul class="eq-sug" hidden></ul></div></div>';
  };
  const left = pick(["head", "neck", "shoulder", "back", "chest", "wrist"]);
  const right = pick(["hands", "waist", "legs", "feet", "ring1", "ring2"]);
  const bottom = pick(["mainhand", "offhand", "ranged", "relic", "trinket1", "trinket2"]).concat(order.filter((slot) => !used.has(slot)));
  grid.innerHTML = '<div class="eq-doll"><div class="eq-doll-col">' + left.map(slotHtml).join("") +
    '</div><div class="eq-doll-col">' + right.map(slotHtml).join("") +
    '</div><div class="eq-doll-bottom">' + bottom.map(slotHtml).join("") + "</div></div>";
  grid.querySelectorAll("input").forEach((inp) => {
    const slot = inp.dataset.slot, ul = inp.parentNode.querySelector(".eq-sug");
    const curName = () => { const id = equippedMap()[slot], it = id && gearItem(id); return it ? it.n : ""; };
    const show = () => {
      const q = inp.value.trim().toLowerCase();
      const q2 = q === curName().toLowerCase() ? "" : q;
      const matches = (pools[poolOfSlot(slot)] || []).filter((e) => !q2 || e.it.n.toLowerCase().includes(q2));
      matches.sort((a, b) => {
        const an = a.it.n.toLowerCase(), bn = b.it.n.toLowerCase();
        const ar = an === q2 ? 0 : an.startsWith(q2) ? 1 : 2;
        const br = bn === q2 ? 0 : bn.startsWith(q2) ? 1 : 2;
        return ar - br;
      });
      const list = matches.slice(0, 20);
      ul.innerHTML = list.map((e) => '<li data-id="' + e.id + '"><span style="color:' + qColor(e.it.q) + '">' + esc(e.it.n) + "</span><small>iLvl " + e.it.ilvl + " · " + esc(obtainInfo(e.it).kind) + "</small></li>").join("") || '<li class="none">' + t("eqNone") + "</li>";
      ul.hidden = false;
    };
    inp.addEventListener("focus", () => {
      inp.select(); show();
      const filter = lootFilterForSlot(slot);
      if (state.lootSlot !== filter) {
        state.lootSlot = filter;
        persist();
        const slotSel = $("lootSlot");
        if (slotSel) slotSel.value = filter;
        syncEquipHighlight();
        renderLoot(currentSpec());
      }
    });
    inp.addEventListener("input", show);
    inp.addEventListener("blur", () => setTimeout(() => { ul.hidden = true; inp.value = curName(); }, 150));
    ul.addEventListener("mousedown", (ev) => {
      ev.preventDefault();
      const li = ev.target.closest("li[data-id]");
      if (li) setEquipped(slot, li.dataset.id);
    });
  });
  grid.querySelectorAll(".eq-x").forEach((b) => b.addEventListener("click", () => setEquipped(b.dataset.slot, null)));
}
function syncEquipHighlight() {
  document.querySelectorAll("#eqGrid input[data-slot]").forEach((inp) => {
    const slot = inp.dataset.slot;
    const box = inp.closest(".eq-slot");
    if (box) box.classList.toggle("is-active", !!state.lootSlot && lootFilterForSlot(slot) === state.lootSlot);
  });
}

/* ---------- Explicaciones y fuentes ---------- */


function autoDungeon(level) {
  const ds = DATA.dungeons;
  const inRange = ds.filter((d) => level >= d.lv[0] && level <= d.lv[1]);
  if (inRange.length) return inRange[inRange.length - 1].id;
  return ds.slice().sort((a, b) => Math.abs(level - a.lv[0]) - Math.abs(level - b.lv[0]))[0].id;
}
const LOOT_SLOT_LABEL = {
  head: ["Cabeza", "Head"], neck: ["Cuello", "Neck"], shoulder: ["Hombros", "Shoulders"],
  back: ["Espalda", "Back"], chest: ["Pecho", "Chest"], wrist: ["Muñecas", "Wrists"],
  hands: ["Manos", "Hands"], waist: ["Cintura", "Waist"], legs: ["Piernas", "Legs"], feet: ["Pies", "Feet"],
  ring: ["Anillo", "Ring"], trinket: ["Abalorio", "Trinket"],
  mainhand: ["Mano principal", "Main hand"], offhand: ["Mano secundaria", "Off hand"],
  ranged: ["A distancia", "Ranged"], relic: ["Reliquia de clase", "Class relic"]
};
function lootSlotText(slot) {
  const v = LOOT_SLOT_LABEL[slot];
  return v ? v[state.lang === "en" ? 1 : 0] : ((SLOT_LABEL[state.lang] || SLOT_LABEL.es)[slot] || slot);
}
function lootFilterValues(spec) {
  const out = [];
  specSlots(spec).forEach((slot) => {
    const v = slot === "ring1" || slot === "ring2" ? "ring" : slot === "trinket1" || slot === "trinket2" ? "trinket" : slot;
    if (!out.includes(v)) out.push(v);
  });
  return out;
}
function lootMatchesSlot(pk, filter) {
  const want = filter === "ring" ? ["ring1", "ring2"] : filter === "trinket" ? ["trinket1", "trinket2"] : [filter];
  return pk.some((p) => want.includes(p));
}
function lootSlotLabel(it, pk) {
  if (it.s === "ring" || it.s === "trinket" || it.s === "relic") return lootSlotText(it.s);
  if (it.s === "ranged" || it.s === "thrown") return lootSlotText("ranged");
  if (["twohand", "onehand", "held", "mainhand", "offhand"].includes(it.s)) {
    const p = pk || [];
    if (p.includes("mainhand") && p.includes("offhand")) return L("Mano principal / secundaria", "Main / off hand");
    if (p.includes("offhand") && !p.includes("mainhand")) return lootSlotText("offhand");
    if (p.includes("mainhand")) return lootSlotText("mainhand");
  }
  return lootSlotText(it.s);
}
const collapsedBosses = new Set();
let lootHoverCard = null, lootHoverTimer = 0;
function hideLootHover() {
  clearTimeout(lootHoverTimer);
  if (lootHoverCard) {
    lootHoverCard.remove();
    lootHoverCard = null;
  }
}
function showLootHover(item) {
  hideLootHover();
  const why = item.querySelector(".loot-why");
  if (!why) return;
  const clone = why.cloneNode(true);
  clone.open = true;
  const summary = clone.querySelector("summary");
  if (summary) summary.remove();
  const card = document.createElement("div");
  card.id = "lootHover";
  card.className = "loot-why loot-hover";
  card.setAttribute("role", "tooltip");
  const link = item.querySelector(".loot-row a");
  card.innerHTML = (link ? '<div class="loot-hover-title">' + esc(link.textContent) + "</div>" : "") + clone.innerHTML;
  document.body.appendChild(card);
  lootHoverCard = card;
  const rect = item.getBoundingClientRect(), margin = 10;
  const width = card.offsetWidth, height = card.offsetHeight;
  let left = Math.min(Math.max(8, rect.left), window.innerWidth - width - 8);
  let top = rect.top - height - margin;
  if (top < 8) top = rect.bottom + margin;
  if (top + height > window.innerHeight - 8) top = Math.max(8, window.innerHeight - height - 8);
  card.style.left = left + "px";
  card.style.top = top + "px";
}
window.addEventListener("scroll", hideLootHover, { passive: true });
window.addEventListener("resize", hideLootHover);
function lootPartVal(p) {
  if (!p || !p.v) return "—";
  if (p.k === "armor" || p.k === "dps") return String(p.v);
  return (p.fx ? "≈+" : "+") + p.v;
}
function lootWhyHtml(r, capText, isSet) {
  const cur = r.vs, curParts = cur && cur.parts ? cur.parts : [], keys = [];
  r.parts.forEach((p) => { if (p.k !== "ilvl" && !keys.includes(p.k)) keys.push(p.k); });
  curParts.forEach((p) => { if (p.k !== "ilvl" && !keys.includes(p.k)) keys.push(p.k); });
  const rows = keys.map((k) => {
    const a = r.parts.find((p) => p.k === k) || { v: 0 }, b = curParts.find((p) => p.k === k) || { v: 0 };
    if (!a.v && !b.v) return "";
    const d = (a.v || 0) - (b.v || 0), cls = d > 0 ? "up" : d < 0 ? "dn" : "";
    return "<tr><td>" + esc(partLabel(k)) + "</td><td>" + lootPartVal(a) + "</td><td>" + lootPartVal(b) + '</td><td class="' + cls + '">' + (d > 0 ? "+" : "") + d + "</td></tr>";
  }).join("");
  const diff = cur ? pctDiff(r.score, cur.score) : 100;
  const score = t("scoreWord") + ": " + r.score.toFixed(1) + (cur ? " · " + t("lootWearing") + ": " + cur.score.toFixed(1) + " · " + (diff >= 0 ? "+" : "") + diff + "%" : "");
  return '<details class="loot-why"><summary>' + t("lootWhy") + '</summary><table><thead><tr><th></th><th>' + t("lootThis") + "</th><th>" + t("lootWearing") + "</th><th>" + t("lootDiff") + "</th></tr></thead><tbody>" + rows + "</tbody></table><p><b>" + score + "</b></p><p>" + t("lootNoteGems") + "</p><p>" + t("lootNoteCaps") + "</p>" + (isSet ? "<p>" + t("lootSetNote") + "</p>" : "") + (capText ? '<p class="warn">' + esc(capText) + "</p>" : "") + "</details>";
}
function capWarning(r, targetSlot, totals, eq) {
  const caps = runtime.lastGear && runtime.lastGear.caps;
  if (!caps) return "";
  const cur = eq[targetSlot], old = cur && cur.it ? (cur.it.st || {}) : {};
  const keys = Object.keys(caps).filter((k) => ((r.it.st || {})[k] || 0) || old[k]);
  if (!keys.length) return "";
  const over = keys.filter((k) => (totals[k] || 0) - (old[k] || 0) + ((r.it.st || {})[k] || 0) > caps[k]);
  if (!over.length) return "";
  return t("lootCapsWarn") + over.map(partLabel).join(", ") + t("lootCapsSuffix");
}
function renderLoot(spec) {
  const level = state.level, w = weightsFor(spec, false, level);
  const cur = state.dungeon || autoDungeon(level);
  const access = heroicAccess(spec, cur), heroicLocked = !!(access && access.known && access.locked);
  const sel = $("dungeonSelect");
  const autoName = (zoneOf(autoDungeon(level)) || {}).n || "";
  sel.innerHTML = '<option value="0">' + esc(t("lootAuto") + ": " + autoName) + "</option>" +
    '<optgroup label="' + esc(t("lootDungeons")) + '">' + DATA.dungeons.map((d) => '<option value="' + d.id + '">' + esc(d.n) + " (" + d.lv[0] + "–" + d.lv[1] + ")</option>").join("") + "</optgroup>" +
    '<optgroup label="' + esc(t("lootRaids")) + '">' + (DATA.raids || []).map((d) => '<option value="' + d.id + '">' + esc(d.n) + " (" + d.lv[0] + (d.lv[1] !== d.lv[0] ? "–" + d.lv[1] : "") + ")</option>").join("") + "</optgroup>";
  sel.value = String(state.dungeon || 0);
  const slotSel = $("lootSlot"), filterValues = lootFilterValues(spec);
  if (state.lootSlot && !filterValues.includes(state.lootSlot)) state.lootSlot = "";
  slotSel.innerHTML = '<option value="">' + esc(t("lootSlotAll")) + "</option>" +
    filterValues.map((v) => '<option value="' + v + '">' + esc(lootSlotText(v)) + "</option>").join("");
  slotSel.value = state.lootSlot;
  const sortSel = $("lootSort");
  if (!["boss", "upgrade", "ilvl"].includes(state.lootSort)) state.lootSort = "boss";
  sortSel.innerHTML = '<option value="boss">' + esc(t("lootSortBoss")) + '</option><option value="upgrade">' + esc(t("lootSortUpgrade")) + '</option><option value="ilvl">' + esc(t("lootSortIlvl")) + "</option>";
  sortSel.value = state.lootSort;
  $("onlyUp").checked = state.onlyUp;
  $("showOffspec").checked = state.showOffspec;
  const accessEl = $("lootAccess");
  if (!access) accessEl.hidden = true;
  else {
    const fill = (key, values) => t(key).replace(/\{(\w+)\}/g, (m, k) => values[k] != null ? "<b>" + values[k] + "</b>" : m);
    accessEl.hidden = false;
    accessEl.className = "loot-access" + (access.known && !access.locked ? " ok" : "");
    if (!access.known) accessEl.innerHTML = fill("lootHeroicNeedGear", { req: access.req });
    else if (access.locked) accessEl.innerHTML = fill("lootHeroicLocked", { req: access.req, avg: fmtIlvl(access.avg) }) + ' <span class="note">' + esc(t("lootHeroicNote")) + "</span>";
    else accessEl.innerHTML = fill("lootHeroicOpen", { req: access.req, avg: fmtIlvl(access.avg) });
  }
  const slotFilter = state.lootSlot;
  const eq = {};
  specSlots(spec).forEach((sl) => { eq[sl] = equippedEntry(spec, sl); });
  const anyEq = Object.values(eq).some(Boolean);
  const eqTotals = {};
  specSlots(spec).forEach((sl) => {
    const e = eq[sl];
    if (!e) return;
    Object.entries(e.it.st || {}).forEach(([k, v]) => { eqTotals[k] = (eqTotals[k] || 0) + v; });
  });
  const setInfo = (ENG.setBonus || {})[spec.cls + "|" + spec.name];
  const setIds = new Set(((setInfo && setInfo.ids) || []).map(String));
  const slotsOf = (p) => (p === "ring" ? ["ring1", "ring2"] : p === "trinket" ? ["trinket1", "trinket2"] : [p]).filter((sl) => sl in eq);
  const bosses = {};
  let ups = 0, hidden = 0, heroicHidden = 0;
  const zoneLoot = (DATA.loot || {})[cur] || {};
  for (const boss in zoneLoot) for (const id in zoneLoot[boss]) {
    const it = DATA.items[id];
    if (!it) continue;
    const tags = zoneLoot[boss][id];
    const fac = tags.find((x) => x === "horde" || x === "alliance");
    if (fac && fac !== state.faction) continue;
    if (state.phase && it.ph > state.phase) continue;
    if (heroicLocked && tags.includes("H") && !tags.includes("N")) { heroicHidden++; continue; }
    const r = evalItem(it, spec, w, { level, faction: state.faction }, false);
    if (!r) continue;
    if (slotFilter && !lootMatchesSlot(r.pk, slotFilter)) continue;
    if (equippedMainTwoHand(spec) && r.pk.length === 1 && r.pk[0] === "offhand") continue;
    if (!r.rel && !state.showOffspec) { hidden++; continue; }
    const offspec = !r.rel;
    let bestD = -1e9, vs = null;
    r.pk.forEach((p) => {
      let worst = null;
      slotsOf(p).forEach((sl) => { const sc = eq[sl] ? eq[sl].score : 0; if (!worst || sc < worst.sc) worst = { sc, e: eq[sl] }; });
      if (!worst) return;
      const d = worst.sc > 0 ? pctDiff(r.score, worst.sc) : 100;
      if (d > bestD) { bestD = d; vs = worst.e; }
    });
    if (bestD === -1e9) continue;
    const usable = r.al <= level, up = usable && bestD >= 3;
    if (up) ups++;
    if (state.onlyUp && !up) continue;
    const s = it.src || {};
    const target = targetEquipSlot(spec, r.pk);
    (bosses[boss] = bosses[boss] || []).push({
      id, it, pk: r.pk, parts: r.parts, score: r.score, delta: bestD, usable, al: r.al, target,
      df: tags.filter((x) => x !== fac).join("/"), dc: s.n === boss ? s.dc : null, vs, offspec,
      isSet: setIds.has(String(id))
    });
  }
  $("lootCount").textContent = ups + t("lootUps") + (hidden ? " · " + hidden + t("lootHidden") : "") + (heroicHidden ? " · " + heroicHidden + t("lootHeroicHidden") : "");
  const hint = anyEq ? "" : '<p class="note">' + t("eqHintNone") + "</p>";
  const rowCmp = (a, b) => {
    if (a.offspec !== b.offspec) return a.offspec - b.offspec;
    if (a.usable !== b.usable) return b.usable - a.usable;
    if (state.lootSort === "ilvl") return b.it.ilvl - a.it.ilvl || b.delta - a.delta;
    return b.delta - a.delta || b.it.ilvl - a.it.ilvl;
  };
  const sortedRows = (n) => bosses[n].slice().sort(rowCmp);
  const alpha = (a, b) => (a === "" ? 1 : b === "" ? -1 : a.localeCompare(b));
  const names = Object.keys(bosses);
  if (state.lootSort === "upgrade") names.sort((a, b) => sortedRows(b)[0].delta - sortedRows(a)[0].delta || alpha(a, b));
  else if (state.lootSort === "ilvl") names.sort((a, b) => sortedRows(b)[0].it.ilvl - sortedRows(a)[0].it.ilvl || alpha(a, b));
  else names.sort(alpha);
  if (!names.length) {
    const actions = [];
    if (slotFilter) actions.push('<button type="button" class="mini-btn" data-loot-action="slot">' + esc(t("lootClearSlotFilter")) + "</button>");
    if (state.onlyUp) actions.push('<button type="button" class="mini-btn" data-loot-action="onlyup">' + esc(t("lootClearOnlyUp")) + "</button>");
    if (hidden) actions.push('<button type="button" class="mini-btn" data-loot-action="offspec">' + esc(t("lootShowOffspec")) + "</button>");
    if (anyEq && slotFilter) actions.push('<button type="button" class="mini-btn" data-loot-action="clearslot">' + esc(t("lootClearSlot")) + "</button>");
    const msg = (slotFilter || state.onlyUp) ? t("lootEmptyFiltered") : (heroicLocked && heroicHidden) ? t("lootHeroicEmpty").replace("{req}", access.req) : t("lootEmpty");
    $("lootBody").innerHTML = hint + '<div class="loot-empty"><p class="note">' + msg + "</p>" + (actions.length ? '<div class="loot-empty-actions">' + actions.join("") + "</div>" : "") + "</div>";
    bindLootEvents();
    renderLootUndo();
    return;
  }
  $("lootBody").innerHTML = hint + names.map((n) => {
    const rows = sortedRows(n).map((r) => {
      const badge = r.offspec ? '<span class="delta off">' + t("offspecTag") + "</span>"
        : !r.usable ? '<span class="delta lv">' + t("level") + (r.al || "?") + "</span>"
        : !r.vs ? '<span class="delta up">' + t("eqEmpty") + "</span>"
        : r.delta >= 3 ? '<span class="delta up">↑ +' + r.delta + "%</span>"
        : r.delta > -3 ? '<span class="delta eq">≈</span>' : '<span class="delta dn">↓ ' + r.delta + "%</span>";
      const vs = r.vs ? " · vs " + esc(r.vs.it.n) : "";
      const equip = r.usable ? '<button type="button" class="mini-btn loot-equip" data-id="' + r.id + '" data-slot="' + r.target + '">' + esc(t("lootEquip")) + "</button>" : "";
      return '<div class="loot-item"><div class="loot-row' + (r.usable ? "" : " na") + (r.offspec ? " offspec" : "") + '"><span class="m">' + esc(lootSlotLabel(r.it, r.pk)) + "</span><span>" + itemLink(r.id, false, "") +
        ' <span class="m">iLvl ' + r.it.ilvl + (r.df ? " · " + diffLabel(r.df) : "") + (r.dc ? " · " + r.dc + "%" : "") + vs + '</span></span><span class="loot-actions">' + badge + equip + "</span></div>" +
        lootWhyHtml(r, capWarning(r, r.target, eqTotals, eq), r.isSet) + "</div>";
    }).join("");
    return '<details class="boss"' + (collapsedBosses.has(n) ? "" : " open") + ' data-boss="' + esc(n) + '"><summary><h3>' + esc(n || t("zoneDrops")) + "</h3></summary>" + rows + "</details>";
  }).join("");
  bindLootEvents();
  renderLootUndo();
}
function bindLootEvents() {
  $("lootBody").querySelectorAll(".loot-equip").forEach((btn) => btn.addEventListener("click", () => equipLoot(btn.dataset.id)));
  $("lootBody").querySelectorAll("[data-loot-action]").forEach((btn) => btn.addEventListener("click", () => {
    const action = btn.dataset.lootAction;
    if (action === "slot") state.lootSlot = "";
    else if (action === "onlyup") state.onlyUp = false;
    else if (action === "offspec") state.showOffspec = true;
    else if (action === "clearslot") {
      const g = (state.gear[gearKey()] = state.gear[gearKey()] || {});
      const slots = state.lootSlot === "ring" ? ["ring1", "ring2"] : state.lootSlot === "trinket" ? ["trinket1", "trinket2"] : [state.lootSlot];
      slots.forEach((slot) => delete g[slot]);
      clearLootUndo();
    }
    persist();
    runtime.render();
  }));
  $("lootBody").querySelectorAll("details.boss").forEach((d) => d.addEventListener("toggle", () => {
    if (d.open) collapsedBosses.delete(d.dataset.boss); else collapsedBosses.add(d.dataset.boss);
  }));
  hideLootHover();
  if (window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    $("lootBody").querySelectorAll(".loot-item").forEach((item) => {
      if (!item.querySelector(".loot-why")) return;
      item.addEventListener("mouseenter", () => {
        clearTimeout(lootHoverTimer);
        lootHoverTimer = setTimeout(() => showLootHover(item), 180);
      });
      item.addEventListener("mouseleave", hideLootHover);
    });
  }
}

export {
  equipLoot, setEquipped, renderEquip, syncEquipHighlight, autoDungeon,
  LOOT_SLOT_LABEL, lootSlotText, lootFilterValues, lootMatchesSlot, lootSlotLabel,
  collapsedBosses, hideLootHover, showLootHover, lootPartVal, lootWhyHtml,
  capWarning, renderLoot, bindLootEvents
};
