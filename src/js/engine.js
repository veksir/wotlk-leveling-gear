import { DATA } from "./data.js";
import { state, levelItem, itemHands, specSlots, poolOfSlot, titanGrip, pctDiff } from "./core.js";
import { averageItemLevel, isHeroicOnlyDrop, heroicRequirement } from "./heroic.js";

const ENG = DATA.engine;
const GEAR_ITEMS = Object.assign({}, DATA.items, DATA.heirlooms);
const ARMOR_KEYS = ["head", "shoulder", "chest", "wrist", "hands", "waist", "legs", "feet", "back"];


function itemFactions(it) {
  const src = it.src || {};
  const set = new Set();
  const norm = (v) => { v = String(v || "both").toLowerCase(); return v === "none" ? "both" : v; };
  if (src.t === "Quest") (src.q || []).forEach((q) => set.add(norm(q.f)));
  else if (src.t === "Vendor" || (src.t === "Drop" && src.f)) set.add(norm(src.f));
  if (!set.size) set.add("both");
  return set;
}
function armorUnlock(cls, at) { const m = ENG.armorUnlock[at]; return (m && m[cls]) || 1; }
function preferredArmor(cls, level) {
  if (["Mage", "Priest", "Warlock"].includes(cls)) return "Cloth";
  if (["Druid", "Rogue"].includes(cls)) return "Leather";
  if (["Hunter", "Shaman"].includes(cls)) return level < 40 ? "Leather" : "Mail";
  if (["Warrior", "Paladin"].includes(cls)) return level < 40 ? "Mail" : "Plate";
  return "Plate";
}
function armorFactor(cls, at, level) {
  const tiers = ENG.armorTiers[cls] || ["Cloth"];
  if (!tiers.includes(at)) return 0;
  const pref = preferredArmor(cls, level);
  if (level >= 40 && at !== pref) return 0;
  const diff = tiers.indexOf(at) - tiers.indexOf(pref);
  return diff >= 0 ? [1, 0.6, 0.35, 0.2][Math.min(diff, 3)] : 0.4;
}
function weightsFor(spec, pvp, level) {
  const specW = level === 80 ? (ENG.specWeights || {})[spec.cls + "|" + spec.name] : null;
  const w = Object.assign({}, ENG.weights[spec.role] || {}, specW || {});
  w.hs = w[spec.primary] || 0; // «mejor estadística» de un proc: la principal de la especialidad
  // Valor de un socket por debajo de nivel 80: la mejor de las gemas que recomiendan las guías para esta especialidad.
  const G = (ENG.gems || {})[spec.cls + "|" + spec.name] || null;
  const gemVal = (st) => Object.entries(st).reduce((a, [k, v]) => a + v * (w[k] || 0), 0);
  w.gv = Math.max.apply(null, [0].concat(G ? [].concat(G.red || [], G.yellow || [], G.blue || []).map(gemVal) : []));
  w.gc = level === 80 && G ? gemContext(G, w, spec, gemVal) : null; // modelo por color (solo nivel 80)
  if (pvp) w.res = 0.9;
  return w;
}
/* Modelo de gemas por color (nivel 80): valor de la mejor gema de cada color y de la meta-gema, que solo cuenta si
   compensa lo que cuesta activarla (poner gemas de un color que quizá no sean las mejores, o un Nightmare Tear, que cuenta
   como una gema de cada color pero es único). */
function gemContext(G, w, spec, gemVal) {
  const best = (list) => Math.max.apply(null, [0].concat((list || []).map(gemVal)));
  const ctx = { red: best(G.red), yellow: best(G.yellow), blue: best(G.blue), meta: 0, metaCost: 0, metaPlan: null };
  ctx.any = Math.max(ctx.red, ctx.yellow, ctx.blue);
  ctx.prismatic = ctx.any;
  const M = G.meta;
  if (M) {
    const req = M.requires || {};
    const loss = (c) => Math.max(0, ctx.any - (ctx[c] || 0));
    const tear = (ENG.metaGems && ENG.metaGems.wildcard) ? gemVal(ENG.metaGems.wildcard.st) : 0;
    const noTear = Object.entries(req).reduce((a, [c, n]) => a + n * loss(c), 0);
    const withTear = Math.max(0, ctx.any - tear) + Object.entries(req).reduce((a, [c, n]) => a + Math.max(0, n - 1) * loss(c), 0);
    ctx.metaCost = Math.min(noTear, withTear);
    ctx.metaPlan = withTear < noTear ? "tear" : "colors";
    ctx.meta = Math.max(0, gemVal(M.st) + (M.extraEp || 0) - ctx.metaCost);
  }
  return ctx;
}
function scoreParts(it, w) {
  const parts = [];
  const add = (k, v, wt, fx) => { if (v && wt) parts.push({ k, v, c: v * wt, fx: !!fx }); };
  add("armor", it.ar || 0, w.armor);
  add("dps", it.dps || 0, w.dps);
  Object.entries(it.st || {}).forEach(([k, v]) => add(k, v, w[k]));
  Object.entries(it.px || {}).forEach(([k, v]) => add(k, v, w[k], true));
  // Sockets
  if (it.sc && w.gc) {
    // Nivel 80: cada socket lleva la mejor gema de su color y el bonus de socket solo cuenta si compensa frente a poner
    // en todos los sockets la mejor gema de cualquier color (entonces el bonus se pierde).
    const g = w.gc, cols = it.sg && it.sg.length ? it.sg : new Array(it.sc).fill("prismatic");
    const scale = Math.min(1, Math.max(0, ((it.ilvl || 0) - 60) / 180));
    const matched = cols.reduce((a, c) => a + (g[c] !== undefined ? g[c] : g.any), 0) * scale;
    const any = cols.length * g.any * scale;
    const sb = Object.entries(it.sb || {});
    const bonus = sb.reduce((a, [k, v]) => a + v * (w[k] || 0), 0);
    const useBonus = bonus > 0 && matched + bonus >= any;
    parts.push({ k: "gems", v: it.sc, c: useBonus ? matched : any, fx: false });
    if (useBonus) parts.push({ k: "sbonus", v: sb.reduce((a, [, v]) => a + v, 0), c: bonus, fx: false });
  } else if (it.sc && w.gv) {
    // Por debajo de nivel 80: cada socket vale una gema recomendada y el bonus cuenta la mitad.
    const scale = Math.min(1, Math.max(0, ((it.ilvl || 0) - 60) / 180));
    add("gems", it.sc, w.gv * scale);
    const sb = Object.entries(it.sb || {});
    const bonus = sb.reduce((a, [k, v]) => a + v * (w[k] || 0) * 0.5, 0);
    if (bonus > 0) parts.push({ k: "sbonus", v: sb.reduce((a, [, v]) => a + v, 0), c: bonus, fx: false });
  }
  // Meta-gema: una sola vez, en el casco con socket meta, y solo si compensa su coste de activación.
  if (it.mt && w.gc && w.gc.meta > 0) parts.push({ k: "meta", v: 1, c: w.gc.meta, fx: true });
  return { parts, base: parts.reduce((a, p) => a + p.c, 0) + (it.ilvl || 0) * 0.01 };
}
// Relevancia: un objeto puede ser equipable por la clase y aun así no aportar nada a la
// especialidad (por ejemplo, plate de heal para un paladín tanque). La puntuación no cambia;
// solo se usa para decidir qué mostrar como recomendación o botín útil.
function isRelevant(it, spec, w) {
  const ignore = new Set(["sta", "armor"]);
  let signature = 0, foreign = 0;
  const add = (k, v) => {
    if (!v || ignore.has(k) || k === "dps") return;
    if (k === "feralap" && !(w.feralap > 0)) return; // solo es relevante para quien lo pondera (druida feral)
    if (k === "hs") {
      if ((w[spec.primary] || 0) > 0) signature += v;
      return;
    }
    if ((w[k] || 0) > 0) signature += v; else foreign += v;
  };
  Object.entries(it.st || {}).forEach(([k, v]) => add(k, v));
  Object.entries(it.px || {}).forEach(([k, v]) => add(k, v));
  if (it.dps && (w.dps || 0) > 0) signature += it.dps;
  if (it.at === "Shield" && spec.off === "shield") return true;
  // Un arma con una estadística principal que no es la de la especialidad no le sirve (p. ej. un arma de agilidad
  // para un guerrero o un arma de fuerza para un pícaro).
  // Las armas a distancia son la excepción: llevan agilidad aunque la clase no la use (guerreros, pícaros...).
  if (it.dps && it.s !== "ranged" && it.s !== "thrown") {
    const main = ["str", "agi", "int"].filter((k) => (it.st || {})[k] > 0);
    if (main.length && !main.includes(spec.primary)) return false;
  }
  if (!Object.keys(it.st || {}).length && !Object.keys(it.px || {}).length && (it.ar || it.dps)) return true;
  if (signature <= 0) {
    const pureTankStamina = !foreign && (it.st || {}).sta && (spec.role === "tank" || spec.role === "bear");
    return !!pureTankStamina;
  }
  return foreign === 0 || signature >= foreign * 0.5;
}
function availableLevel(it, spec) {
  let lv = Math.max(it.req > 0 ? it.req : 1, spec.min);
  if (it.at) lv = Math.max(lv, armorUnlock(spec.cls, it.at));
  return lv <= 80 ? lv : null;
}
function poolsFor(it, spec, level) {
  const { cls, off, ranged, relic, mode } = spec;
  const slot = it.s, sub = it.sub, at = it.at, hands = itemHands(it);
  if (ARMOR_KEYS.includes(slot)) {
    if (slot === "back") return ["back"];
    return (ENG.armorTiers[cls] || []).includes(at) ? [slot] : [];
  }
  if (slot === "neck" || slot === "ring" || slot === "trinket") return [slot];
  if (slot === "offhand" && at === "Shield" && off === "shield") return ["offhand"];
  if (["twohand", "onehand", "mainhand", "offhand"].includes(slot)) {
    if (!ENG.classWeapons[cls].includes(sub)) return [];
    if (!((ENG.weaponHands[cls] || {})[sub] || []).includes(hands)) return [];
    if (mode === "tg") {
      if (level >= 60) return hands === 2 ? ["mainhand", "offhand"] : [];
      if (hands !== 1) return [];
    } else {
      if (mode === "2h" && hands !== 2) return [];
      if (mode === "1h" && hands !== 1) return [];
    }
    return off === "dw" && hands === 1 ? ["mainhand", "offhand"] : ["mainhand"];
  }
  if (slot === "held" && off === "held") return ["offhand"];
  if ((slot === "ranged" || slot === "thrown") && ranged) {
    let ok = false;
    if (ranged === "ranged") ok = slot === "ranged" && ["Bow", "Gun", "Crossbow"].includes(sub);
    else if (ranged === "anyranged") ok = (slot === "ranged" && ["Bow", "Gun", "Crossbow"].includes(sub)) || slot === "thrown";
    else if (ranged === "wand") ok = slot === "ranged" && sub === "Wand";
    else if (ranged === "thrown") ok = slot === "thrown" || (slot === "ranged" && sub === "Thrown");
    return ok ? ["ranged"] : [];
  }
  if (slot === "relic" && relic && sub === relic) return ["relic"];
  return [];
}


const ARMOR_PENALTY_SCALE = { caster: 0.1, healer: 0.1, hunter: 0.1, agi: 0.5, feral: 0.5 };
const softArmor = (f, role) => (f > 0 && ARMOR_PENALTY_SCALE[role] !== undefined ? 1 - (1 - f) * ARMOR_PENALTY_SCALE[role] : f);
const SUFFIX_SLOPE = { head: 0.31, legs: 0.30, chest: 0.28, shoulder: 0.227, hands: 0.22, feet: 0.215, waist: 0.22, back: 0.157, wrist: 0.16, neck: 0.16, ring: 0.158, offhand: 0.158, held: 0.158, onehand: 0.125, mainhand: 0.14, twohand: 0.275, ranged: 0.1, thrown: 0.1 };
const SUFFIXES = [["agi", "sta", "of the Monkey"], ["sta", "int", "of the Eagle"], ["str", "sta", "of the Bear"], ["sta", "spi", "of the Whale"], ["int", "spi", "of the Owl"],
  ["str", "int", "of the Gorilla"], ["agi", "int", "of the Falcon"], ["str", "spi", "of the Boar"], ["agi", "spi", "of the Wolf"], ["str", "agi", "of the Tiger"]];
function withSuffix(it, w) {
  const val = Math.max(1, Math.round((SUFFIX_SLOPE[it.s] || 0.15) * Math.max(0, (it.ilvl || 0) - 6)));
  let best = SUFFIXES[0], bestV = -1;
  SUFFIXES.forEach((s) => { const v = val * ((w[s[0]] || 0) + (w[s[1]] || 0)); if (v > bestV) { bestV = v; best = s; } });
  return Object.assign({}, it, { n: it.n + " " + best[2], px: { [best[0]]: val, [best[1]]: val }, est: 1 });
}
const FRESH_CURRENCIES = new Set(["heroism", "valor", "conquest", "triumph", "gold", "reputation"]);
function freshAccessible(it) {
  if (it.raid || it.pvp) return false;
  const s = it.src || {};
  if (s.t === "RaidProb" || s.t === "PvP" || s.rq) return false;
  if (s.t === "Vendor") {
    if (s.cur) return FRESH_CURRENCIES.has(s.cur);
    if ((it.ilvl || 0) >= 251) return false;
  }
  return true;
}
function evalItem(it, spec, w, o, cap, curated) {
  if (it.x) return null;
  if (it.re) it = withSuffix(it, w);
  if (it.cl && !it.cl.includes(spec.cls)) return null;
  const fs = itemFactions(it);
  if (!(fs.has("both") || fs.has(o.faction))) return null;
  const pk = poolsFor(it, spec, o.level);
  if (!pk.length) return null;
  const al = availableLevel(it, spec);
  if (al === null || (cap && al > o.level)) return null;
  const sp = scoreParts(it, w);
  if (sp.base <= 0 && !curated) return null;
  // La penalización de armadura solo aplica a piezas de armadura (no a escudos ni a capas).
  const tiered = it.at && it.s !== "back" && ARMOR_KEYS.includes(it.s);
  const pref = (ENG.weaponPref || {})[spec.cls + "|" + spec.name];
  const weaponF = it.dps && pref && !pref.includes(it.sub) ? 0.9 : 1;
  const af = (tiered ? softArmor(armorFactor(spec.cls, it.at, o.level), spec.role) : 1) * weaponF;
  if (af <= 0) return null;
  return { pk, al, parts: sp.parts, base: sp.base, af, score: sp.base * af, rel: curated || isRelevant(it, spec, w), item: it.est ? it : null };
}

/* opts: { level, faction, scope: "noraid"|"raid", phase: 0 (todas)|1-4, pvp: bool (solo equipo PvP), fresh: bool (recién 80) } */
const BEAM_SLOTS = ["head", "neck", "shoulder", "back", "chest", "wrist", "hands", "waist", "legs", "feet", "ring1", "ring2"];
function jointOptimize(spec, w, caps, sb, slots, pools, opts) {
  const width = (opts && opts.width) || 60, K = (opts && opts.k) || 8;
  const capN = opts && opts.capN != null ? opts.capN : 2;
  const opt = BEAM_SLOTS.filter((s) => slots[s] && slots[s].list[0]);
  const plain = (e) => e.base * e.af;
  const capKeys = caps ? Object.keys(caps) : [];
  const setIds = sb ? new Set(sb.ids) : null;
  let fixedPlain = 0, fixedSet = 0;
  const fixedStats = {};
  specSlots(spec).filter((s) => !opt.includes(s)).forEach((s) => {
    const e = slots[s] && slots[s].list[0];
    if (!e) return;
    fixedPlain += plain(e);
    capKeys.forEach((k) => { fixedStats[k] = (fixedStats[k] || 0) + ((e.it.st || {})[k] || 0); });
    if (setIds && setIds.has(e.id)) fixedSet++;
  });
  const fam = (e) => (/^Ashen Band of /.test(e.it.n) ? "ashen" : null);
  // candidatos: los mejores por puntuación base, los que más aportan a un tope y las mejores piezas del set
  const cands = {};
  opt.forEach((s) => {
    const pool = (pools[poolOfSlot(s)] || []).slice().sort((a, b) => plain(b) - plain(a));
    const top = pool.slice(0, K);
    const capTop = [];
    if (capN > 0) capKeys.forEach((k) => {
      pool.slice().sort((a, b) => ((b.it.st || {})[k] || 0) - ((a.it.st || {})[k] || 0)).slice(0, capN).forEach((e) => capTop.push(e));
    });
    const sets = setIds ? pool.filter((e) => setIds.has(e.id) && !top.includes(e)).slice(0, 3) : [];
    const list = [];
    top.concat(capTop, sets).forEach((e) => { if (e && !list.includes(e)) list.push(e); });
    cands[s] = list;
  });
  const evaluate = (st, final) => {
    const total = st.plain + fixedPlain;
    let v = total;
    capKeys.forEach((k) => { v -= Math.max(0, (st.stats[k] || 0) + (fixedStats[k] || 0) - caps[k]) * (w[k] || 0) * 0.85; });
    if (sb) {
      const n = st.setN + fixedSet;
      v += n >= sb.need ? (sb.pct / 100) * total : final ? 0 : (sb.pct / 100) * total * (n / sb.need) * 0.5;
    }
    return v;
  };
  let beam = [{ sel: {}, plain: 0, stats: {}, setN: 0 }];
  opt.forEach((s) => {
    const next = [];
    beam.forEach((st) => {
      cands[s].forEach((e) => {
        if (s === "ring2") {
          const r1 = st.sel.ring1;
          if (r1 && (r1 === e || r1.it.n === e.it.n || (fam(r1) && fam(r1) === fam(e)))) return;
        }
        const stats = Object.assign({}, st.stats);
        capKeys.forEach((k) => { stats[k] = (stats[k] || 0) + ((e.it.st || {})[k] || 0); });
        next.push({ sel: Object.assign({}, st.sel, { [s]: e }), plain: st.plain + plain(e), stats, setN: st.setN + (setIds && setIds.has(e.id) ? 1 : 0) });
      });
    });
    next.forEach((st) => { st.v = evaluate(st, false); });
    next.sort((a, b) => b.v - a.v);
    beam = next.slice(0, width);
  });
  if (!beam.length) return slots;
  let best = beam[0], bestV = -Infinity;
  beam.forEach((st) => { const v = evaluate(st, true); if (v > bestV) { bestV = v; best = st; } });
  const out = Object.assign({}, slots);
  opt.forEach((s) => {
    const chosen = best.sel[s];
    out[s] = { list: [chosen].concat(slots[s].list.filter((e) => e !== chosen)), info: slots[s].info };
  });
  return out;
}

function computeGear(spec, o) {
  const w = weightsFor(spec, o.pvp, o.level);
  const caps = o.level === 80 ? ((ENG.capsBySpec || {})[spec.cls + "|" + spec.name] || (ENG.caps || {})[spec.role] || null) : null;
  const capKeys = caps ? Object.keys(caps) : [];
  const specKey = spec.cls + "|" + spec.name;
  const cur = (ENG.curated || {})[specKey];
  const curatedRelic = new Set((cur && cur.relic) || []);
  const avgIlvl = o.noHeroicGate ? null : averageItemLevel(spec);
  const pools = {}, info = {}, fallback = {};
  for (const id in GEAR_ITEMS) {
    if (!state.showHeirlooms && DATA.heirlooms[id]) continue;
    const it = levelItem(GEAR_ITEMS[id], o.level);
    if (o.pvp && !it.pvp) continue;
    const freshBlocked = o.fresh && !freshAccessible(it);
    const r = evalItem(it, spec, w, o, true, curatedRelic.has(id));
    if (!r) continue;
    if (!r.rel) {
      if (o.level < 80 && !freshBlocked && !(it.pvp && !o.pvp) && !(it.raid && o.scope !== "raid") && !(o.phase && it.ph > o.phase)) {
        const fe = { id, it: r.item || it, parts: r.parts, base: r.base, af: r.af, score: r.score, capPen: 0, offspec: true };
        r.pk.forEach((p) => (fallback[p] = fallback[p] || []).push(fe));
      }
      continue;
    }
    const e = { id, it: r.item || it, parts: r.parts, base: r.base, af: r.af, score: r.score, capPen: 0 };
    const reasons = [];
    if (freshBlocked) reasons.push("fresh");
    if (!o.pvp) {
      if (it.pvp) reasons.push("pvp");
      if (it.raid && o.scope !== "raid") reasons.push("raid");
    }
    if (o.phase && it.ph > o.phase) reasons.push("phase");
    if (o.level === 80 && !o.pvp && avgIlvl != null && isHeroicOnlyDrop(it) && avgIlvl < heroicRequirement(it.src.zid)) reasons.push("heroic");
    if (reasons.length) e.reasons = reasons;
    r.pk.forEach((p) => {
      const inf = info[p] || (info[p] = { top: null, blocked: null });
      if (!inf.top || it.ilvl > inf.top.it.ilvl || (it.ilvl === inf.top.it.ilvl && e.score > inf.top.score)) inf.top = e;
      if (reasons.length) { if (!inf.blocked || e.score > inf.blocked.score) inf.blocked = e; }
      else (pools[p] || (pools[p] = [])).push(e);
    });
  }
  const sortPool = (p) => pools[p].sort((a, b) => (b.cur || 0) - (a.cur || 0) || b.score - a.score || b.it.ilvl - a.it.ilvl);
  for (const p in pools) {
    sortPool(p);
    const seen = new Set();
    pools[p] = pools[p].filter((e) => (seen.has(e.it.n) ? false : (seen.add(e.it.n), true)));
  }
  for (const p in fallback) {
    if (pools[p] && pools[p].length) continue;
    fallback[p].sort((a, b) => b.score - a.score || b.it.ilvl - a.it.ilvl);
    const seen = new Set();
    pools[p] = fallback[p].filter((e) => (seen.has(e.it.n) ? false : (seen.add(e.it.n), true)));
  }
  // Bonus de set T10: el valor del bonus de 2 o 4 piezas (en % del total del equipo) se reparte entre las
  // piezas que recomienda la guía, no entre todas las piezas del set.
  const sb = (ENG.setBonus || {})[specKey];
  if (sb && !o.pvp) {
    const ids = new Set(sb.ids);
    let total = 0;
    for (const p in pools) if (pools[p][0]) total += pools[p][0].score;
    const piece = (sb.pct / 100) * total / sb.need;
    for (const p in pools) {
      pools[p].forEach((e) => { if (ids.has(e.id)) { e.setBonus = piece; e.score += piece; } });
      sortPool(p);
    }
  }
  // Abalorios y reliquias: mandan las guías (sus procs y efectos no se pueden puntuar bien). Se emparejan por nombre
  // para que valgan también las versiones normal/heroica del mismo objeto.
  if (cur && !o.pvp) {
    ["trinket", "relic"].forEach((p) => {
      const ranks = {};
      (cur[p] || []).forEach((id, i) => { const n = DATA.items[id] && DATA.items[id].n; if (n && !(n in ranks)) ranks[n] = { b: cur[p].length - i, r: i + 1 }; });
      if (!pools[p]) return;
      pools[p].forEach((e) => { if (e.it.n in ranks) { e.cur = ranks[e.it.n].b; e.curRank = ranks[e.it.n].r; } });
      sortPool(p);
    });
  }
  const buildSlots = () => {
    const out = {};
    const mainBest = (pools.mainhand || [])[0];
    const twoHandMain = !!mainBest && itemHands(mainBest.it) === 2;
    const tg = titanGrip(spec, o.level);
    specSlots(spec).forEach((slot) => {
      const src = poolOfSlot(slot);
      let pool = pools[src] || [];
      if (slot === "offhand" && twoHandMain && !tg) pool = [];
      if (slot === "offhand" && spec.off === "dw" && mainBest) pool = pool.filter((e) => e.it.n !== mainBest.it.n);
      let list = pool;
      if (slot.startsWith("ring") || slot.startsWith("trinket")) {
        // Equipamiento único: los anillos «Ashen Band» de Ashen Verdict comparten restricción (solo se lleva uno).
        const fam = (e) => (/^Ashen Band of /.test(e.it.n) ? "ashen" : null);
        const first = pool[0];
        const second = first ? pool.find((e) => e !== first && !(fam(first) && fam(e) === fam(first))) : null;
        const rest = pool.filter((e) => e !== first && e !== second);
        list = (slot.endsWith("1") ? [first] : [second]).concat(rest).filter(Boolean);
      }
      out[slot] = { list, info: info[src] || null };
    });
    return out;
  };
  let slots = buildSlots();
  // Topes (nivel 80): lo que sobra por encima del tope vale solo un 15 %. Cada vuelta penaliza según lo que aportan los
  // demás slots; como el proceso puede oscilar (penalizar el golpe, quedarse sin él, volver a elegirlo...), se evalúa
  // cada vuelta con un único objetivo (puntuación del equipo menos el exceso sobre el tope) y se queda la mejor.
  if (capKeys.length) {
    const selected = () => {
      const total = {}, byPool = {};
      specSlots(spec).forEach((slot) => {
        const e = slots[slot].list[0], p = poolOfSlot(slot);
        if (!e) return;
        capKeys.forEach((k) => {
          const v = (e.it.st || {})[k] || 0;
          total[k] = (total[k] || 0) + v;
          (byPool[p] = byPool[p] || {})[k] = ((byPool[p] || {})[k] || 0) + v;
        });
      });
      return { total, byPool };
    };
    const objective = (tb) => {
      let f = 0;
      specSlots(spec).forEach((slot) => { const e = slots[slot].list[0]; if (e) f += e.base * e.af + (e.setBonus || 0); });
      capKeys.forEach((k) => { f -= Math.max(0, (tb.total[k] || 0) - caps[k]) * (w[k] || 0) * 0.85; });
      return f;
    };
    const applyCaps = (tb) => {
      for (const p in pools) {
        pools[p].forEach((e) => {
          let pen = 0;
          if (tb) capKeys.forEach((k) => {
            const v = (e.it.st || {})[k] || 0;
            if (!v) return;
            const others = (tb.total[k] || 0) - ((tb.byPool[p] || {})[k] || 0);
            pen += Math.max(0, v - Math.max(0, caps[k] - others)) * (w[k] || 0) * 0.85 * e.af;
          });
          e.capPen = pen;
          e.score = e.base * e.af - pen + (e.setBonus || 0);
        });
        sortPool(p);
      }
    };
    let best = { f: objective(selected()), tb: null };
    for (let iter = 0; iter < 5; iter++) {
      const tb = selected();
      applyCaps(tb);
      slots = buildSlots();
      const f = objective(selected());
      if (f > best.f) best = { f, tb };
    }
    applyCaps(best.tb);
    slots = buildSlots();
  }
  // Dos manos o arma + mano secundaria: se queda el conjunto que más puntúa.
  let loadout = null;
  if (spec.mode === "any" && spec.off && pools.mainhand) {
    const two = pools.mainhand.find((e) => itemHands(e.it) === 2);
    const one = pools.mainhand.find((e) => itemHands(e.it) === 1);
    const off = (pools.offhand || []).find((e) => !one || e.it.n !== one.it.n);
    if (two && one && off) {
      const use1 = one.score + off.score > two.score;
      loadout = { use1, diff: pctDiff(use1 ? one.score + off.score : two.score, use1 ? two.score : one.score + off.score), other: use1 ? two.it.n : one.it.n + " + " + off.it.n };
      pools.mainhand = pools.mainhand.filter((e) => (itemHands(e.it) === 1) === use1);
      if (!use1) pools.offhand = [];
      slots = buildSlots();
    }
  }
  // Búsqueda en haz (nivel 80): elige a la vez los slots sin lista curada ni arma midiendo lo que el proceso codicioso solo
  // aproxima: el bonus de set exacto (todo o nada), los topes sobre el conjunto completo y el anillo único Ashen Band.
  if (o.level === 80 && !o.pvp && o.beam !== false && !(typeof window !== "undefined" && window.__NO_BEAM)) {
    slots = jointOptimize(spec, w, caps, sb, slots, pools, { width: o.beamWidth, k: o.beamK, capN: o.beamCapN });
  }
  Object.values(slots).forEach((sl) => { sl.list = sl.list.slice(0, 11); });
  // Totales de golpe/pericia de lo recomendado (solo objetos: sin gemas, encantamientos ni talentos)
  let totals = null;
  if (capKeys.length) {
    totals = {};
    capKeys.forEach((k) => {
      totals[k] = specSlots(spec).reduce((a, slot) => a + (((slots[slot].list[0] || { it: {} }).it.st || {})[k] || 0), 0);
    });
  }
  return { pools, info, slots, loadout, totals, caps };
}

export {
  ENG, GEAR_ITEMS, ARMOR_KEYS, itemFactions, armorUnlock, preferredArmor,
  armorFactor, weightsFor, gemContext, scoreParts, isRelevant, availableLevel,
  poolsFor, ARMOR_PENALTY_SCALE, softArmor, SUFFIX_SLOPE, SUFFIXES, withSuffix,
  FRESH_CURRENCIES, freshAccessible, evalItem, BEAM_SLOTS, jointOptimize, computeGear
};
