import { DATA } from "./data.js";
import { state, gearItem, itemHands, equippedMap, currentSpec, titanGrip, equippedMainTwoHand, specSlots, poolOfSlot, levelItem } from "./core.js";
import { ENG, GEAR_ITEMS, ARMOR_KEYS, itemFactions, availableLevel, armorFactor, softArmor, scoreParts, weightsFor, withSuffix } from "./engine.js";

const SHIELD_CLASSES = ["Warrior", "Paladin", "Shaman"];
const DW_CLASSES = ["Rogue", "Warrior", "Death Knight", "Hunter", "Shaman"];
const CLASS_RELIC = {}, CLASS_RANGED = {};
Object.values(DATA.specs).forEach((sp) => { if (sp.relic) CLASS_RELIC[sp.cls] = sp.relic; if (sp.ranged) CLASS_RANGED[sp.cls] = sp.ranged; });
function equipPools(it, spec, level) {
  const cls = spec.cls, slot = it.s, sub = it.sub;
  if (ARMOR_KEYS.includes(slot)) {
    if (slot === "back") return ["back"];
    if (!it.at) return [slot];
    return (ENG.armorTiers[cls] || []).includes(it.at) ? [slot] : [];
  }
  if (slot === "neck" || slot === "ring" || slot === "trinket") return [slot];
  if (slot === "offhand" && it.at === "Shield") return SHIELD_CLASSES.includes(cls) ? ["offhand"] : [];
  if (slot === "held") return ["offhand"];
  if (["twohand", "onehand", "mainhand", "offhand"].includes(slot)) {
    const hands = itemHands(it);
    const known = (ENG.classWeapons[cls] || []).includes(sub) && ((ENG.weaponHands[cls] || {})[sub] || []).includes(hands);
    if (!known) {
      if (["Miscellaneous", "Fishing Pole", "Exotic"].includes(sub)) return slot === "offhand" ? ["offhand"] : ["mainhand"];
      return [];
    }
    if (hands === 2) return titanGrip(spec, level) && cls === "Warrior" ? ["mainhand", "offhand"] : ["mainhand"];
    return hands === 1 && (spec.off === "dw" || DW_CLASSES.includes(cls)) ? ["mainhand", "offhand"] : ["mainhand"];
  }
  if ((slot === "ranged" || slot === "thrown") && CLASS_RANGED[cls]) {
    const r = CLASS_RANGED[cls];
    const ok = r === "ranged" ? slot === "ranged" && ["Bow", "Gun", "Crossbow"].includes(sub)
      : r === "anyranged" ? (slot === "ranged" && ["Bow", "Gun", "Crossbow"].includes(sub)) || slot === "thrown"
      : r === "wand" ? slot === "ranged" && sub === "Wand"
      : slot === "thrown" || (slot === "ranged" && sub === "Thrown");
    return ok ? ["ranged"] : [];
  }
  if (slot === "relic" && CLASS_RELIC[cls] === sub) return ["relic"];
  return [];
}
function evalEquip(it, spec, w, o) {
  if (it.re) it = withSuffix(it, w);
  if (it.cl && !it.cl.includes(spec.cls)) return null;
  const fs = itemFactions(it);
  if (!(fs.has("both") || fs.has(o.faction))) return null;
  const pk = equipPools(it, spec, o.level);
  if (!pk.length) return null;
  const al = availableLevel(it, spec);
  if (al === null) return null;
  const tiered = it.at && it.s !== "back" && ARMOR_KEYS.includes(it.s);
  const af = tiered ? softArmor(armorFactor(spec.cls, it.at, o.level), spec.role) : 1;
  const sp = scoreParts(it, w);
  return { pk, al, parts: sp.parts, base: sp.base, af, score: Math.max(sp.base, 0) * af };
}
let candCache = { key: "", pools: null };
function candidates(spec) {
  const key = [spec.cls, spec.name, state.level, state.faction].join("|");
  if (candCache.key === key) return candCache.pools;
  const w = weightsFor(spec, false, state.level);
  const pools = {};
  for (const id in GEAR_ITEMS) {
    const it = levelItem(GEAR_ITEMS[id], state.level);
    const r = evalEquip(it, spec, w, { level: state.level, faction: state.faction });
    if (!r) continue;
    const e = { id, it, score: r.score, usable: r.al <= state.level };
    r.pk.forEach((p) => (pools[p] || (pools[p] = [])).push(e));
  }
  for (const p in pools) pools[p].sort((a, b) => (b.usable - a.usable) || b.score - a.score || b.it.ilvl - a.it.ilvl);
  candCache = { key, pools };
  return pools;
}
function equippedEntry(spec, slot) {
  const id = equippedMap()[slot], source = id && gearItem(id);
  if (!source) return null;
  const it = levelItem(source, state.level);
  const r = evalEquip(it, spec, weightsFor(spec, false, state.level), { level: state.level, faction: state.faction });
  return { id, it, score: r ? r.score : 0, parts: r ? r.parts : [], base: r ? r.base : 0, af: r ? r.af : 1 };
}


const lootFilterForSlot = (slot) => slot === "ring1" || slot === "ring2" ? "ring" : slot === "trinket1" || slot === "trinket2" ? "trinket" : slot;
function slotScore(spec, slot) {
  const e = equippedEntry(spec, slot);
  return e ? e.score : 0;
}
function targetEquipSlot(spec, pk) {
  const g = equippedMap(), empty = (s) => !g[s];
  if (pk.includes("mainhand") && pk.includes("offhand")) {
    if (empty("mainhand")) return "mainhand";
    if (empty("offhand") && !equippedMainTwoHand(spec)) return "offhand";
    if (equippedMainTwoHand(spec)) return "mainhand";
    return slotScore(spec, "mainhand") <= slotScore(spec, "offhand") ? "mainhand" : "offhand";
  }
  if (pk.includes("ring")) {
    if (empty("ring1")) return "ring1";
    if (empty("ring2")) return "ring2";
    return slotScore(spec, "ring1") <= slotScore(spec, "ring2") ? "ring1" : "ring2";
  }
  if (pk.includes("trinket")) {
    if (empty("trinket1")) return "trinket1";
    if (empty("trinket2")) return "trinket2";
    return slotScore(spec, "trinket1") <= slotScore(spec, "trinket2") ? "trinket1" : "trinket2";
  }
  return pk[0] || "";
}

export {
  SHIELD_CLASSES, DW_CLASSES, CLASS_RELIC, CLASS_RANGED, equipPools, evalEquip,
  candCache, candidates, equippedEntry, lootFilterForSlot, slotScore, targetEquipSlot
};
