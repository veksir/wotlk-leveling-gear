import { DATA } from "./data.js";
import { state, L, esc, t, STAT_LABEL, SLOT_LABEL, currentSpec, zoneOf, pctDiff } from "./core.js";
import { heroicRequirement, averageItemLevel, fmtIlvl } from "./heroic.js";
function partLabel(k) {
  if (k === "armor") return L("Armadura", "Armor");
  if (k === "dps") return L("DPS del arma", "Weapon DPS");
  if (k === "gems") return L("Gemas", "Gems");
  if (k === "meta") return L("Meta-gema (activada)", "Meta gem (activated)");
  if (k === "sbonus") return L("Bonus de socket", "Socket bonus");
  if (k === "feralap") return L("Poder de ataque (feral)", "Attack power (feral)");
  return (STAT_LABEL[state.lang] || STAT_LABEL.es)[k] || k;
}

function reasonText(e) {
  const out = [];
  if (e.reasons.includes("fresh")) out.push(L("requiere Frost o una ficha de raid", "requires Frost or a raid token"));
  if (e.reasons.includes("raid")) out.push(L("es de banda y estás en «Sin bandas»", "is a raid item and you are in \"No raids\""));
  if (e.reasons.includes("pvp")) out.push(L("es de PvP, que se ve en el modo «Solo PvP»", "is PvP gear, shown in \"PvP only\" mode"));
  if (e.reasons.includes("phase")) out.push(L("es de la fase " + e.it.ph + ", posterior a la fase " + state.phase, "is from phase " + e.it.ph + ", later than phase " + state.phase));
  if (e.reasons.includes("heroic")) {
    const req = heroicRequirement((e.it.src || {}).zid), avg = averageItemLevel(currentSpec());
    out.push(L("es de una heroica que pide iLvl medio " + req + (avg == null ? "" : " (tienes " + fmtIlvl(avg) + ")"), "is from a heroic that requires average item level " + req + (avg == null ? "" : " (you have " + fmtIlvl(avg) + ")")));
  }
  return out.join(L(" y ", " and "));
}

function rivalNote(best, inf) {
  const r = inf && inf.top;
  if (!r || r.id === best.id || r.it.ilvl - best.it.ilvl < 5) return "";
  const head = L("Hay un objeto de mayor nivel (", "A higher item level option (") + r.it.n + ", iLvl " + r.it.ilvl + ")";
  if (r.reasons && r.score > best.score) return head + L(" oculto: ", " is hidden: ") + reasonText(r) + ".";
  if (r.af < best.af && r.it.at) return head + L(" es de armadura ", " is ") + r.it.at + L(" y tiene penalización ×", " armor and gets a penalty of ×") + r.af.toFixed(2) + ".";
  if (r.af < best.af) return head + L(" no es de la familia de arma que prefiere la especialidad (penalización ×", " is not a weapon family the spec prefers (penalty ×") + r.af.toFixed(2) + ").";
  let key = null, gain = 0;
  best.parts.forEach((p) => {
    const other = (r.parts.find((q) => q.k === p.k) || { c: 0 }).c;
    if (p.c - other > gain) { gain = p.c - other; key = p.k; }
  });
  return L("Tiene menos nivel de objeto que ", "It has a lower item level than ") + r.it.n + L(", pero más ", ", but more ") + (key ? partLabel(key) : L("valor", "value")) + L(" y mejor mezcla de estadísticas.", " and a better stat mix.");
}

function whyHtml(e, next, inf) {
  const rows = e.parts.slice().sort((a, b) => b.c - a.c).map((p) =>
    "<tr><td>" + esc(partLabel(p.k)) + " " + (p.k === "armor" || p.k === "dps" ? p.v : (p.fx ? "≈+" : "+") + p.v) + (p.fx ? " " + (e.it.est ? L("(estimado, sufijo aleatorio)", "(estimated, random suffix)") : L("(proc/uso)", "(proc/use)")) : "") + "</td><td>" + p.c.toFixed(1) + "</td></tr>").join("") +
    "<tr><td>" + t("ilvlTie") + "</td><td>" + (e.it.ilvl * 0.01).toFixed(1) + "</td></tr>";
  let extra = "";
  if (e.cur) extra += "<p>" + L("Recomendado por las guías (Icy Veins y Wowhead) para esta especialidad: puesto ", "Recommended by the guides (Icy Veins and Wowhead) for this spec: rank ") + e.curRank + L(" de su lista, que manda en este slot.", " in their list, which rules this slot.") + "</p>";
  if (e.setBonus > 0.05) extra += "<p>" + L("Bonus de set T10 (valor estimado del bonus repartido entre sus piezas recomendadas): +", "Tier 10 set bonus (estimated bonus value shared among its recommended pieces): +") + e.setBonus.toFixed(1) + "</p>";
  if (e.capPen > 0.05) extra += "<p>" + L("Penalización por exceder el tope de golpe o pericia: −", "Penalty for exceeding the hit or expertise cap: −") + e.capPen.toFixed(1) + "</p>";
  if (e.af < 1 && e.it.at) extra += "<p>" + L("Penalización por tipo de armadura (", "Armor type penalty (") + esc(e.it.at) + "): ×" + e.af.toFixed(2) + "</p>";
  else if (e.af < 1) extra += "<p>" + L("Familia de arma que la especialidad no prefiere: ×", "Weapon family the spec does not prefer: ×") + e.af.toFixed(2) + "</p>";
  if (next) extra += "<p>" + L("Frente a «", "Versus \"") + esc(next.it.n) + L("»: ", "\": ") + (pctDiff(e.score, next.score) >= 0 ? "+" : "") + pctDiff(e.score, next.score) + L("% de puntuación.", "% score.") + "</p>";
  const b = inf && inf.blocked;
  if (b && b.score > e.score) extra += "<p>" + L("Oculto por tus filtros: «", "Hidden by your filters: \"") + esc(b.it.n) + L("» (+", "\" (+") + pctDiff(b.score, e.score) + L("% de puntuación): ", "% score): ") + esc(reasonText(b)) + ".</p>";
  return '<details class="why"><summary>' + t("whyTitle") + "</summary><table>" + rows + "</table><p><b>" + t("scoreWord") + ": " + e.score.toFixed(1) + "</b></p>" + extra + "</details>";
}

const CURRENCY_LABEL = {
  heroism: ["Emblema de Heroísmo", "Emblem of Heroism"],
  valor: ["Emblema de Valor", "Emblem of Valor"],
  conquest: ["Emblema de Conquista", "Emblem of Conquest"],
  triumph: ["Emblema de Triunfo", "Emblem of Triumph"],
  frost: ["Emblema de Escarcha", "Emblem of Frost"],
  "frost-token": ["Escarcha + marca de raid", "Frost + raid mark"],
  gold: ["Oro", "Gold"],
  reputation: ["Reputación", "Reputation"],
  honor: ["Honor", "Honor"],
  arena: ["Arena", "Arena"]
};

function currencyLabel(cur) {
  const v = CURRENCY_LABEL[cur];
  return v ? v[state.lang === "en" ? 1 : 0] : cur;
}

function goldLabel(copper) {
  return Math.round((copper || 0) / 10000).toLocaleString(state.lang === "en" ? "en-US" : "es-ES") + " g";
}

function obtainInfo(it) {
  const s = it.src || {};
  if (s.t === "Quest") {
    const v = s.q || [];
    const m = v.find((q) => { const f = String(q.f || "Both").toLowerCase(); return f === "both" || f === state.faction; }) || v[0] || {};
    return { cls: s.rq ? "rquest" : "quest", kind: s.rq ? L("Misión de banda", "Raid quest") : L("Misión", "Quest"), detail: m.n || L("Desconocida", "Unknown") };
  }
  if (s.t === "Vendor") {
    const parts = [s.n || L("Desconocido", "Unknown")];
    if (s.cur === "gold") parts.push(s.cost ? goldLabel(s.cost) : L("Oro", "Gold"));
    else if (s.cur === "reputation") {
      parts.push(L("Reputación", "Reputation"));
      if (s.cost) parts.push(goldLabel(s.cost));
    } else if (s.cur) parts.push(currencyLabel(s.cur));
    else if (s.cost) parts.push(goldLabel(s.cost));
    return { cls: "vendor", kind: L("Vendedor", "Vendor"), detail: parts.join(" · ") };
  }
  if (s.t === "Drop") {
    const raid = s.zc === "Raid", dungeon = s.zc === "Dungeon", z = zoneOf(s.zid);
    const parts = [];
    if (s.z) parts.push(s.z + (z ? " (" + z.lv[0] + "–" + z.lv[1] + ")" : ""));
    parts.push(s.n || L("drop de la zona", "zone drop"));
    if (s.df) parts.push(diffLabel(s.df));
    if (s.dc) parts.push(s.dc + "%");
    return { cls: raid ? "raid" : dungeon ? "dungeon" : "zone", kind: raid ? L("Banda", "Raid") : dungeon ? L("Mazmorra", "Dungeon") : L("Zona", "Zone"), detail: parts.join(" · ") };
  }
  if (s.t === "RaidProb") return { cls: "raid", kind: L("Banda (prob.)", "Raid (likely)"), detail: L("fuente no registrada: probablemente botín o ficha de banda", "unrecorded source: most likely raid loot or a raid token") };
  if (s.t === "PvP") return { cls: "rare", kind: "PvP", detail: L("honor o arena (fuente no registrada)", "honor or arena (unrecorded source)") };
  if (s.t === "Rare") return { cls: "rare", kind: L("Drop raro", "Rare drop"), detail: s.dc ? "~" + s.dc + "%" : L("monstruos raros o élite", "rare or elite mobs") };
  return { cls: "other", kind: L("Otra fuente", "Other source"), detail: L("profesión, evento o fuente no registrada", "profession, event, or unrecorded source") };
}

const badgeHtml = (o) => '<span class="src-badge src-' + o.cls + '">' + esc(o.kind) + "</span>" + esc(o.detail);

/* ---------- Botín de mazmorra ---------- */

const DIFF_LABEL = { N: ["Normal", "Normal"], H: ["Heroica", "Heroic"], "10": ["10", "10"], "25": ["25", "25"], "10H": ["10 heroica", "10 heroic"], "25H": ["25 heroica", "25 heroic"] };

const diffLabel = (df) => String(df).split("/").map((d) => (DIFF_LABEL[d] ? DIFF_LABEL[d][state.lang === "en" ? 1 : 0] : d)).join(" / ");

const normName = (n) => String(n).toLowerCase().replace(/^the /, "").replace(/[^a-z0-9]/g, "");

const dungeonByName = (n) => DATA.dungeons.find((d) => normName(d.n) === normName(n));

const bisLabel = (i, pair) => (i === 0 ? "BiS" : pair && i === 1 ? "BiS²" : "ALT" + (i - (pair ? 1 : 0)));

const rankClass = (lab) => (lab === "BiS" ? "rank-bis" : lab === "BiS²" ? "rank-bis2" : "rank-alt");

const rankPill = (lab, title) => '<span class="rank ' + rankClass(lab) + '"' + (title ? ' title="' + esc(title) + '"' : "") + ">" + lab + "</span>";

export { partLabel, reasonText, rivalNote, whyHtml, CURRENCY_LABEL, currencyLabel, goldLabel, obtainInfo, badgeHtml, DIFF_LABEL, diffLabel, normName, dungeonByName, bisLabel, rankClass, rankPill };
