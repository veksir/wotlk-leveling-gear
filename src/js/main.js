import { DATA } from "./data.js";
import {
  state, $, gearKey, gearItem, itemHands, specSlots, titanGrip, clampLevel,
  persist, clearLootUndo, runtime
} from "./core.js";
import * as core from "./core.js";
import * as engine from "./engine.js";
import * as heroic from "./heroic.js";
import * as equipment from "./equipment.js";
import * as format from "./format.js";
import * as loot from "./loot.js";
import * as bis from "./bis.js";
import * as renderer from "./render.js";
import { renderClasses, renderSpecs, renderFactions, renderOptions, setLevel, render } from "./render.js";

runtime.render = render;
Object.assign(window, { DATA }, core, engine, heroic, equipment, format, loot, bis, renderer);

levelRange.addEventListener("input", (e) => setLevel(e.target.value));
levelInput.addEventListener("change", (e) => setLevel(e.target.value));
levelInput.addEventListener("blur", (e) => {
  if (Number(e.target.value) !== state.level) setLevel(e.target.value);
});

$("resetBtn").addEventListener("click", () => {
  Object.assign(state, { cls: "Warrior", spec: "Arms", level: 20, scope: "noraid", phase: 0, pvp: false, alts: 2, dungeon: 0, lootSlot: "", lootSort: "boss", onlyUp: false, showOffspec: false, showHeirlooms: false, fresh: false, bisPhase: "PR" });
  clearLootUndo();
  persist();
  renderClasses();
  renderSpecs();
  renderFactions();
  renderOptions();
  render();
});

$("dungeonSelect").addEventListener("change", (e) => { state.dungeon = Number(e.target.value) || 0; persist(); render(); });
$("lootSlot").addEventListener("change", (e) => { state.lootSlot = e.target.value; persist(); render(); });
$("lootSort").addEventListener("change", (e) => { state.lootSort = e.target.value; persist(); render(); });
$("lootUndoBtn").addEventListener("click", () => {
  if (!runtime.lastEquip || runtime.lastEquip.key !== gearKey()) return;
  state.gear[gearKey()] = runtime.lastEquip.gear;
  runtime.lastEquip = null;
  persist();
  render();
});
$("onlyUp").addEventListener("change", (e) => { state.onlyUp = e.target.checked; persist(); render(); });
$("showOffspec").addEventListener("change", (e) => { state.showOffspec = e.target.checked; persist(); render(); });
$("showHeirlooms").addEventListener("change", (e) => { state.showHeirlooms = e.target.checked; persist(); render(); });
$("fresh80").addEventListener("change", (e) => {
  state.fresh = e.target.checked;
  if (state.fresh) { state.scope = "noraid"; state.pvp = false; }
  persist();
  renderOptions();
  render();
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
  render();
});
$("eqClear").addEventListener("click", () => { clearLootUndo(); state.gear[gearKey()] = {}; persist(); render(); });

document.querySelectorAll(".lang-switch button").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.lang = btn.dataset.lang;
    persist();
    renderFactions();
    renderOptions();
    render();
  });
});

state.level = clampLevel(state.level);
renderClasses();
renderSpecs();
renderFactions();
renderOptions();
render();


