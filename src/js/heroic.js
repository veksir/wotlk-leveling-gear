import { DATA } from "./data.js";
import { state, gearItem, equippedMap, specSlots, equippedMainTwoHand } from "./core.js";

const HEROIC_REQ = { 4723: 200, 4809: 200, 4813: 200, 4820: 219 };
const HEROIC_REQ_DEFAULT = 180;
const heroicReqCache = {};
function heroicRequirement(zoneId) {
  zoneId = Number(zoneId);
  if (!zoneId) return 0;
  if (zoneId in heroicReqCache) return heroicReqCache[zoneId];
  let req = 0;
  if (DATA.dungeons.some((d) => d.id === zoneId)) {
    const loot = (DATA.loot || {})[zoneId] || {};
    outer: for (const boss in loot) for (const id in loot[boss]) {
      if (loot[boss][id].includes("H")) { req = HEROIC_REQ[zoneId] || HEROIC_REQ_DEFAULT; break outer; }
    }
  }
  return (heroicReqCache[zoneId] = req);
}
function isHeroicOnlyDrop(it) {
  const s = it.src || {};
  if (s.t !== "Drop" || s.zc !== "Dungeon" || !s.zid || !heroicRequirement(s.zid)) return false;
  const df = String(s.df || "").split("/");
  return df.includes("H") && !df.includes("N");
}
function equippedItemLevel(id) {
  const it = gearItem(id);
  if (!it) return 0;
  return it.hl ? (it.ilvl || 1) : (it.ilvl || 0);
}
function averageItemLevel(spec) {
  const g = equippedMap(), slots = specSlots(spec);
  if (!slots.some((slot) => g[slot])) return null;
  const counted = equippedMainTwoHand(spec) ? slots.filter((slot) => slot !== "offhand") : slots;
  const denom = !g.mainhand && !g.offhand ? 16 : counted.length;
  const sum = counted.reduce((total, slot) => total + (g[slot] ? equippedItemLevel(g[slot]) : 0), 0);
  return sum / denom;
}
function heroicAccess(spec, zoneId) {
  if (state.level !== 80) return null;
  const req = heroicRequirement(zoneId);
  if (!req) return null;
  const avg = averageItemLevel(spec);
  return { req, avg, known: avg != null, locked: avg != null && avg < req };
}
const fmtIlvl = (v) => (v == null ? "—" : (Math.round(v * 10) / 10).toFixed(1));

export {
  HEROIC_REQ, HEROIC_REQ_DEFAULT, heroicReqCache, heroicRequirement,
  isHeroicOnlyDrop, equippedItemLevel, averageItemLevel, heroicAccess, fmtIlvl
};
