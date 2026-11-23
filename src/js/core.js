import { DATA } from "./data.js";

const runtime = { lastGear: null, lastEquip: null, render: null };
const STORE = { cls: "wotlk-gear-class", spec: "wotlk-gear-spec", level: "wotlk-gear-level", faction: "wotlk-gear-faction", lang: "wotlk-gear-lang", scope: "wotlk-gear-scope", phase: "wotlk-gear-phase", pvp: "wotlk-gear-pvp", alts: "wotlk-gear-alts", dungeon: "wotlk-gear-dungeon", gear: "wotlk-gear-equipped", onlyUp: "wotlk-gear-onlyup", showOffspec: "wotlk-gear-show-offspec", showHeirlooms: "wotlk-gear-show-heirlooms", fresh: "wotlk-gear-fresh", lootSlot: "wotlk-gear-loot-slot", lootSort: "wotlk-gear-loot-sort", bisPhase: "wotlk-gear-bis-phase", weights: "wotlk-gear-weights", bisGuide: "wotlk-gear-bis-guide" };


const I18N = {
  es: {
    brandTitle: "Equipo óptimo", reset: "Reiniciar",
    eyebrow: "El mejor objeto disponible hasta tu nivel",
    h1: "Qué llevar en cada slot, sin adivinar.",
    intro: "Elige clase, especialidad, facción y nivel. Cada slot muestra el mejor objeto que puedes usar en ese punto, cómo conseguirlo, por qué se recomienda y varias alternativas. Activa «Con bandas» para ver el mejor equipo de raid, o consulta abajo qué te puede tocar en cada mazmorra.",
    classLabel: "Clase", specLabel: "Especialidad", factionLabel: "Facción", levelWord: "NIVEL",
    statusPhase: "Fase de subida", statusArmor: "Armadura", statusNext: "Siguiente hito",
    statusSources: "Fuentes incluidas", sourcesValue: "Misiones, mazmorras, vendedores y drops",
    sheetTitle: "Equipamiento recomendado", statsTitle: "Prioridad de estadísticas",
    dungeonsTitle: "Mazmorras del tramo", heirloomTitle: "Reliquias de subida (heirlooms)",
    calcTitle: "Cómo se calcula",
    calcText: "Se puntúa cada objeto según la estadística principal de tu especialidad y se elige el de mayor valor disponible a tu nivel. Se priorizan misiones, mazmorras, vendedores y drops; el equipo PvP y las fuentes no registradas solo se usan si no hay una alternativa de subida. Se excluyen los objetos de banda detectados por la fuente; algunas cadenas de misión de banda pueden aparecer como Misión.",
    footer: "Las ventanas de objeto se cargan desde EVOWOW. Pasa el cursor sobre un objeto para ver su ficha completa.",
    horde: "Horda", alliance: "Alianza",
    levelMax: "Nivel máximo", nextBiS: "Revisa el BiS de nivel 80",
    sheetIntro: "El mejor objeto usable en cada slot para nivel ",
    sheetIntro80: "Referencia de nivel 80. El botín de banda no está incluido.",
    slots: " ranuras", alt: "Alt: ", noAlts: "Sin alternativas claras en este nivel.",
    emptyItem: "Sin objeto", emptyMeta: "No hay un objeto válido para este nivel.",
    offhandNote: "Con un arma de dos manos, ignora este slot.",
    offhandBlocked: "No aplica con un arma a dos manos",
    now: " · ahora", next: " · próxima", noReq: "Sin requisito", level: "Nivel ",
    shoulders: "Hombros", chest: "Pecho", weapons: "Armas", trinkets: "Abalorios"
  },
  en: {
    brandTitle: "Optimal gear", reset: "Reset",
    eyebrow: "The best item available at your level",
    h1: "What to wear in every slot, without guessing.",
    intro: "Choose class, spec, faction, and level. Each slot shows the strongest item you can use at this point, how to get it, why it is recommended, and several alternatives. Turn on \"With raids\" to see the best raid gear, or check below what each dungeon can drop for you.",
    classLabel: "Class", specLabel: "Spec", factionLabel: "Faction", levelWord: "LEVEL",
    statusPhase: "Leveling phase", statusArmor: "Armor", statusNext: "Next milestone",
    statusSources: "Sources included", sourcesValue: "Quests, dungeons, vendors, and drops",
    sheetTitle: "Recommended gear", statsTitle: "Stat priority",
    dungeonsTitle: "Dungeons in this range", heirloomTitle: "Leveling heirlooms",
    calcTitle: "How it is calculated",
    calcText: "Each item is scored using your spec's primary stats and the highest-value item available at your level is chosen. Quests, dungeons, vendors, and drops are prioritized; PvP gear and unregistered sources are only used when no leveling alternative exists. Raid items detected by source are excluded; some raid quest chains may still appear as Quest.",
    footer: "Item tooltips load from EVOWOW. Hover over an item to see its full card.",
    horde: "Horde", alliance: "Alliance",
    levelMax: "Max level", nextBiS: "Check level 80 BiS",
    sheetIntro: "The best usable item in every slot for level ",
    sheetIntro80: "Level 80 reference. Raid loot is not included.",
    slots: " slots", alt: "Alt: ", noAlts: "No clear alternatives at this level.",
    emptyItem: "No item", emptyMeta: "No valid item for this level.",
    offhandNote: "With a two-handed weapon, ignore this slot.",
    offhandBlocked: "Not used with a two-handed weapon",
    now: " · now", next: " · next", noReq: "No requirement", level: "Level ",
    shoulders: "Shoulders", chest: "Chest", weapons: "Weapons", trinkets: "Trinkets"
  }
};


const SLOT_LABEL = {
  es: { head: "Cabeza", neck: "Cuello", shoulder: "Hombros", back: "Espalda", chest: "Pecho", wrist: "Muñecas", hands: "Manos", waist: "Cintura", legs: "Piernas", feet: "Pies", ring1: "Anillo 1", ring2: "Anillo 2", trinket1: "Abalorio 1", trinket2: "Abalorio 2", mainhand: "Mano principal", offhand: "Mano secundaria", ranged: "A distancia", relic: "Reliquia de clase" },
  en: { head: "Head", neck: "Neck", shoulder: "Shoulders", back: "Back", chest: "Chest", wrist: "Wrists", hands: "Hands", waist: "Waist", legs: "Legs", feet: "Feet", ring1: "Ring 1", ring2: "Ring 2", trinket1: "Trinket 1", trinket2: "Trinket 2", mainhand: "Main hand", offhand: "Off hand", ranged: "Ranged", relic: "Class relic" }
};


const STAT_LABEL = {
  es: { hs: "Mejor estadística", str: "Fuerza", agi: "Agilidad", int: "Intelecto", sta: "Aguante", spi: "Espíritu", sp: "Poder de hechizos", ap: "Poder de ataque", heal: "Sanación", hit: "Golpe", crit: "Crítico", haste: "Celeridad", exp: "Pericia", arp: "Pen. armadura", def: "Defensa", dodge: "Esquiva", parry: "Parada", block: "Bloqueo", blockval: "Valor de bloqueo", mp5: "Maná/5s", res: "Resiliencia", spen: "Pen. hechizos" },
  en: { hs: "Highest stat", str: "Strength", agi: "Agility", int: "Intellect", sta: "Stamina", spi: "Spirit", sp: "Spell power", ap: "Attack power", heal: "Healing", hit: "Hit", crit: "Crit", haste: "Haste", exp: "Expertise", arp: "Armor pen.", def: "Defense", dodge: "Dodge", parry: "Parry", block: "Block", blockval: "Block value", mp5: "Mana/5s", res: "Resilience", spen: "Spell pen." }
};


const STATS_EN = {
  caster: ["Intellect", "Spell power", "Spell hit", "Crit", "Haste"],
  healer: ["Intellect", "Spirit", "Spell power", "Haste", "Crit"],
  str: ["Strength", "Hit", "Expertise", "Crit", "Haste"],
  agi: ["Agility", "Hit", "Expertise", "Crit", "Haste"],
  tank: ["Stamina", "Defense", "Dodge", "Parry", "Hit and expertise"],
  bear: ["Stamina", "Agility", "Dodge", "Expertise", "Hit"],
  hunter: ["Agility", "Hit", "Crit", "Attack power", "Stamina"]
};


Object.assign(I18N.es, {

  eqTitle: "Mi equipo actual", eqUseRec: "Usar el recomendado", eqClear: "Vaciar",
  eqHint: "Cada campo corresponde a una parte: escribe el objeto que llevas y elige la sugerencia. Al enfocar un slot, el botín se filtra a esa parte. Usa «Usar el recomendado» para comparar el botín contra la recomendación.",
  eqPlaceholder: "Buscar objeto…", eqRemove: "Quitar", eqNone: "Sin resultados", eqEmpty: "Slot vacío",
  eqHintNone: "Aún no indicaste tu equipo: mientras tanto, todo objeto cuenta como mejora.", lootUps: " mejoras para ti",
  sheetIntroPvp: "Equipo útil para PvP en cada slot, nivel ", sourcesPvpOnly: "Solo equipo PvP",
  capsTitle: "Topes (nivel 80):", capsOver: "excede en", capsMissing: "faltan", capsEq: "justo en el tope",
  capsNote: "Solo cuentan los objetos: sin gemas, encantamientos ni talentos, que bajan el tope. Lo que excede el tope vale un 15 %.",
  lootDungeons: "Mazmorras", lootRaids: "Bandas",
  modeLabel: "Contenido", modeNoRaid: "Sin bandas", modeRaid: "Con bandas",
  phaseLabel: "Fase", phaseAll: "Todas",
  bisTitle: "BiS por fase", bisIntro: "Ranking de objetos por slot y fase, como el addon BiS-Tooltip: empieza por «Recién 80» y avanza por las pestañas. Se calcula siempre para nivel 80 con tu clase, especialidad y facción. ¿Te salió un objeto? Búscalo abajo para ver si te sirve.",
  bisLegendBis: "mejor objeto de la fase", bisLegendBis2: "segundo mejor (anillos y abalorios, se llevan dos)", bisLegendAlt: "siguientes alternativas, de mejor a peor",
  bisHint: "Es una guía general: un objeto ALT puede rendirte más que el BiS si te ayuda a completar golpe o pericia. Los objetos marcados con «completa…» aportan a un tope que el equipo BiS de esta fase todavía no alcanza.",
  bisEmptySlot: "Sin objeto en este slot", bisSpecWord: "Especialidad",
  gemTitle: "Gemas y encantamientos", gemIntro: "Qué gemar y encantar según tu especialidad (guías de Icy Veins y Wowhead). En cada slot del BiS verás los sockets de la pieza con la gema que conviene según su bonus de socket, y su encantamiento.",
  gemSockets: "Sockets", gemEnchant: "Encantamiento", gemMeta: "Meta-gema", gemEnchants: "Encantamientos por slot", gemRule: "Cómo gemar:",
  bisHave: "Lo llevas", bisOwnedPre: "Con tu equipo actual llevas piezas de este ranking en ", bisOwnedPost: " slots. Marca lo que ya tienes en «Mi equipo actual».", bisOwnedNone: "Indica tu equipo en «Mi equipo actual» y aquí se marcarán las piezas que ya tienes.", bisPairRing: "Anillos", bisPairTrinket: "Abalorios", bisAltTitle: "Alternativa", bisBisTitle: "Mejor objeto", pvpLabel: "Tipo de equipo", pvpOff: "PvE", pvpOn: "Solo PvP",
  altsLabel: "Alternativas por slot",
  optsHint: "«Sin bandas» sirve para subir de nivel o jugar sin raid; «Con bandas» muestra el mejor equipo de raid; «Solo PvP» muestra únicamente equipo útil para PvP, sin mezclarlo con el PvE. La fase limita el contenido disponible hasta esa fase del juego. «Recién 80» oculta Frost, T10 y fichas de raid, y deja el equipo comprable con Triunfo o inferior.",
  fresh80: "Modo recién 80 (sin Frost ni fichas de raid)",
  fresh80Hint: "Oculta Frost, T10 y fichas de raid; incluye Triunfo y monedas inferiores.",
  sourcesRaid: "Misiones, mazmorras, vendedores, drops y bandas", sourcesPvp: " + PvP",
  sheetIntro80Raid: "Referencia de nivel 80 con botín de banda incluido.",
  sheetIntro80Fresh: "Referencia de nivel 80 recién llegado: equipo accesible sin Frost, T10 ni fichas de raid.",
  sourcesFresh: "Misiones, mazmorras, reputación, oro, subasta, crafting y emblemas hasta Triunfo",
  freshRouteTitle: "Ruta recién 80 (sin Frost ni fichas de raid)",
  freshRouteIntro: "El modo filtra el equipo que puedes conseguir con Triunfo o inferior. Esta es la ruta recomendada:",
  freshRouteStep1: "Nivel 80 y reputaciones: misiones de Icecrown y Storm Peaks; Kirin Tor, Wyrmrest, Ebon Blade, Cruzada Argenta y Kalu'ak.",
  freshRouteStep2: "Mazmorras: normales 80, ToC5 e ICC5; después heroicas y la diaria de Triunfo.",
  freshRouteStep3: "Emblemas de Triunfo: T9 232 (Dubin Clay, Horace Hunderland, Rueben Lauren, Rafael Langrom) y complementos 245 (Ninsianna, Debbi Moore, Jarold Puller, Abra Cadabra).",
  freshRouteStep4: "Oro, subasta, reputación y crafting: anillos de Kirin Tor de Harold Winston, capas crafteadas, reliquias y complementos.",
  freshRouteStep5: "Arma: cadena de Quel'Delar (251) en mazmorras de 5 si puedes completarla.",
  freshRouteConvert: "Puedes convertir Triunfo en Conquista, Valor y Heroísmo 1:1; por eso el modo incluye equipo de emblemas anteriores.",
  freshRouteAvoid: "Evita hasta tener Frost: T10 251/264/277, capas 264 de Norvin Alderman y T9 245 (requiere Trophy of the Crusade de raid).",
  calcText: "Cada objeto se puntúa con las estadísticas que importan a tu especialidad (más el DPS del arma y la armadura) y se ordena por esa puntuación; el nivel de objeto solo desempata. Desde nivel 40 solo se recomienda el tipo de armadura de tu clase (placa, malla, cuero o tela); por debajo se penalizan los tipos inferiores. «Sin bandas» oculta el botín y las cadenas de misión de banda, el equipo PvP se ve aparte en el modo «Solo PvP» (con peso a la resiliencia) y la fase limita el contenido disponible. Los procs y efectos de uso de los abalorios se promedian según su duración y enfriamiento (≈). Las gemas se eligen por color y el bonus de socket solo se activa si se respetan los colores. El bonus de set T10 se reparte solo entre las piezas que recomienda la guía, y los abalorios y reliquias de clase curados mandan en su slot. A nivel 80 el golpe y la pericia por encima del tope valen un 15 %, y para las especialidades de «cualquier arma» se compara dos manos contra una mano + secundaria. Los épicos sin fuente registrada de nivel 213 o más se tratan como de banda. Las reliquias de subida (heirlooms) quedan fuera del ranking salvo que marques «Incluir reliquias de subida (heirlooms) que ya tengo»; las reliquias de clase son equipo normal. Aún no se calculan encantamientos ni objetos con encantamiento aleatorio. A nivel 80 la armadura y los anillos se eligen a la vez (búsqueda en haz): bonus de set exacto, topes de golpe y pericia, gemas por color y meta-gema solo si compensa su coste; armas, abalorios y reliquias mantienen sus reglas. Al subir de nivel, los objetos con encantamiento aleatorio («of the Bear»…) se estiman con el mejor sufijo para tu especialidad (≈), los objetos blancos solo con armadura rellenan slots sin nada mejor, y si un slot no tiene ningún objeto útil se muestra la mejor opción disponible con un aviso.",
  whyTitle: "¿Por qué este objeto?", scoreWord: "Puntuación", ilvlTie: "Nivel de objeto (desempate)",
  howTo: "Cómo conseguirlo ↗", moreAlts: "Alternativas",
  lootTitle: "Botín de mazmorra según tu equipo", lootIntro: "Indica tu equipo actual —o pulsa «Usar el recomendado» para comparar contra la recomendación— y verás qué objetos de cada mazmorra mejoran cada parte y cuánto.",
  lootPick: "Mazmorra", lootSlot: "Parte", lootSlotAll: "Todas las partes", lootAuto: "Según tu nivel", lootOnlyUp: "Solo mejoras",
  lootSort: "Ordenar", lootSortBoss: "Jefe", lootSortUpgrade: "Mejora", lootSortIlvl: "iLvl",
  lootEquip: "Equipar", lootEquipped: "Equipado", lootUndo: "Deshacer",
  lootHeroicNeedGear: "Acceso a heroicas: introduce tu equipo actual para calcular tu iLvl medio. Esta heroica pide {req}.",
  lootHeroicLocked: "Heroica por Buscador: pide iLvl medio {req} y tienes {avg}. Se ocultan los objetos exclusivos de heroica; sigue con normales, misiones y emblemas hasta llegar.",
  lootHeroicOpen: "Heroica por Buscador: desbloqueada (iLvl medio {avg} ≥ {req}).",
  lootHeroicNote: "Cálculo tipo Buscador: los slots vacíos cuentan 0 y las reliquias de subida cuentan iLvl 1.",
  lootHeroicHidden: " objetos heroicos ocultos",
  lootHeroicEmpty: "Los objetos exclusivos de esta heroica están ocultos hasta que alcances iLvl medio {req}.",
  heroicGeneralNeedGear: "Heroicas: introduce tu equipo actual para comprobar el acceso por iLvl medio.",
  heroicGeneralLocked: "Heroicas: bloqueadas con iLvl medio {avg}; todas piden al menos 180.",
  heroicGeneralPartial: "Heroicas: acceso parcial con iLvl medio {avg}; ToC5, FoS y PoS piden 200, HoR pide 219.",
  heroicGeneralOpen: "Heroicas: desbloqueadas con iLvl medio {avg}.",
  lootWhy: "Ver desglose", lootThis: "Este objeto", lootWearing: "Tu equipo", lootDiff: "Diferencia",
  lootNoteGems: "Incluye gemas y bonus de socket; no encantamientos.", lootNoteCaps: "El porcentaje no descuenta topes de golpe o pericia; se avisa si este objeto te pasaría.",
  lootSetNote: "El bonus de set T10 no se suma a este porcentaje.", lootCapsWarn: "Con este objeto superarías el tope de ", lootCapsSuffix: " (sin gemas ni encantamientos).",
  lootEmptyFiltered: "Ningún objeto coincide con estos filtros.", lootClearSlotFilter: "Ver todas las partes", lootClearOnlyUp: "Quitar Solo mejoras",
  lootShowOffspec: "Mostrar fuera de especialidad", lootClearSlot: "Limpiar este slot",
  showOffspec: "Mostrar fuera de especialidad", offspecTag: "Off-spec",
  showHeirlooms: "Incluir reliquias de subida (heirlooms) que ya tengo",
  heirloomNote: "Las reliquias de subida (heirlooms) se compran con Emblemas de Heroísmo o Marcas de la Conquista del Invierno, que se obtienen a nivel 80. No entran en las recomendaciones salvo que marques «Incluir reliquias de subida (heirlooms) que ya tengo». Las reliquias de clase (sigilo, tótem, ídolo y libram) son equipo normal y sí entran en el ranking.",
  lootHidden: " fuera de especialidad", offspecGear: "Fuera de especialidad",
  lootEmpty: "Ningún objeto útil para tu especialidad en esta mazmorra.", zoneDrops: "Botín de la zona"
});
Object.assign(I18N.en, {

  eqTitle: "My current gear", eqUseRec: "Use recommended", eqClear: "Clear all",
  eqHint: "Each field is one slot: type the item you are wearing and pick a suggestion. Focusing a slot filters the loot to that slot. Use \"Use recommended\" to compare loot against the recommendation.",
  eqPlaceholder: "Search item…", eqRemove: "Remove", eqNone: "No results", eqEmpty: "Empty slot",
  eqHintNone: "You have not entered your gear yet: until then every item counts as an upgrade.", lootUps: " upgrades for you",
  sheetIntroPvp: "PvP-useful gear for each slot, level ", sourcesPvpOnly: "PvP gear only",
  capsTitle: "Caps (level 80):", capsOver: "over by", capsMissing: "missing", capsEq: "exactly at the cap",
  capsNote: "Items only: no gems, enchants, or talents, which lower the cap. Anything above the cap counts for 15 %.",
  lootDungeons: "Dungeons", lootRaids: "Raids",
  modeLabel: "Content", modeNoRaid: "No raids", modeRaid: "With raids",
  phaseLabel: "Phase", phaseAll: "All",
  bisTitle: "BiS by phase", bisIntro: "Item ranking per slot and phase, like the BiS-Tooltip addon: start with \"Fresh 80\" and move along the tabs. It is always computed for level 80 with your class, spec and faction. Got a drop? Search it below to see if it suits you.",
  bisLegendBis: "best item of the phase", bisLegendBis2: "second best (rings and trinkets, you wear two)", bisLegendAlt: "next alternatives, best to worst",
  bisHint: "This is a general guide: an ALT item can perform better than the BiS if it helps you reach hit or expertise. Items tagged «fills…» add to a cap that this phase's BiS gear does not reach yet.",
  bisEmptySlot: "No item in this slot", bisSpecWord: "Spec",
  gemTitle: "Gems and enchants", gemIntro: "What to gem and enchant for your spec (Icy Veins and Wowhead guides). Each BiS slot shows the piece's sockets with the gem that fits its socket bonus, and its enchant.",
  gemSockets: "Sockets", gemEnchant: "Enchant", gemMeta: "Meta gem", gemEnchants: "Enchants by slot", gemRule: "Gemming notes:",
  bisHave: "Equipped", bisOwnedPre: "With your current gear you wear pieces from this ranking in ", bisOwnedPost: " slots. Set what you own in \"My current gear\".", bisOwnedNone: "Enter your gear in \"My current gear\" and the pieces you already own will be marked here.", bisPairRing: "Rings", bisPairTrinket: "Trinkets", bisAltTitle: "Alternative", bisBisTitle: "Best item", pvpLabel: "Gear type", pvpOff: "PvE", pvpOn: "PvP only",
  altsLabel: "Alternatives per slot",
  optsHint: "\"No raids\" is for leveling or playing without raiding; \"With raids\" shows the best raid gear; \"PvP only\" shows only PvP-useful gear, never mixed with PvE. The phase limits content to what is available up to that game phase. \"Fresh 80\" hides Frost, Tier 10, and raid tokens, leaving gear buyable with Triumph or lower.",
  fresh80: "Fresh 80 mode (no Frost or raid tokens)",
  fresh80Hint: "Hides Frost, Tier 10, and raid tokens; includes Triumph and lower emblems.",
  sourcesRaid: "Quests, dungeons, vendors, drops, and raids", sourcesPvp: " + PvP",
  sheetIntro80Raid: "Level 80 reference with raid loot included.",
  sheetIntro80Fresh: "Fresh level 80 reference: gear accessible without Frost, Tier 10, or raid tokens.",
  sourcesFresh: "Quests, dungeons, reputation, gold, auction house, crafting, and emblems up to Triumph",
  freshRouteTitle: "Fresh 80 route (no Frost or raid tokens)",
  freshRouteIntro: "The mode filters gear you can get with Triumph or lower emblems. This is the recommended route:",
  freshRouteStep1: "Level 80 and reputations: Icecrown and Storm Peaks quests; Kirin Tor, Wyrmrest, Ebon Blade, Argent Crusade, and Kalu'ak.",
  freshRouteStep2: "Dungeons: level-80 normals, ToC5, and ICC5; then heroics and the Triumph daily.",
  freshRouteStep3: "Emblems of Triumph: Tier 9 232 (Dubin Clay, Horace Hunderland, Rueben Lauren, Rafael Langrom) and item level 245 offsets (Ninsianna, Debbi Moore, Jarold Puller, Abra Cadabra).",
  freshRouteStep4: "Gold, auction house, reputation, and crafting: Harold Winston's Kirin Tor rings, crafted cloaks, relics, and offsets.",
  freshRouteStep5: "Weapon: the Quel'Delar chain (251) in five-player dungeons if you can complete it.",
  freshRouteConvert: "You can downgrade Triumph into Conquest, Valor, and Heroism 1:1, which is why the mode includes older emblem gear.",
  freshRouteAvoid: "Avoid until you have Frost: Tier 10 251/264/277, Norvin Alderman's 264 cloaks, and Tier 9 245 (requires a raid Trophy of the Crusade).",
  calcText: "Each item is scored with the stats that matter to your spec (plus weapon DPS and armor) and sorted by that score; item level only breaks ties. From level 40 only your class's armor type is recommended (plate, mail, leather, or cloth); below that, lower types are penalized. \"No raids\" hides raid loot and raid quest chains, PvP gear is shown separately in \"PvP only\" mode (resilience is weighted), and the phase limits available content. Proc and on-use effects of trinkets are averaged by duration and cooldown (≈). Gems are chosen by color and the socket bonus only activates when the colors are respected. The Tier 10 set bonus is shared only among the pieces recommended by the guide, and curated trinkets and class relics rule their slot. At level 80, hit and expertise above the cap count for 15 %, and for \"any weapon\" specs a two-hander is compared against one-hand + off hand. Epics with no recorded source at item level 213 or higher are treated as raid loot. Leveling heirlooms stay out of the ranking unless you check «Include leveling heirlooms I already own»; class relics are normal gear. Enchants and random-enchant items are not scored yet. At level 80 armor and rings are chosen together (beam search): exact set bonus, hit and expertise caps, gems by socket color, and a meta gem only when it pays for its activation; weapons, trinkets, and relics keep their curated/greedy rules. While leveling, random-enchant items (\"of the Bear\"...) are estimated with the best suffix for your spec (≈), white armor-only items fill slots with nothing better, and if a slot has no useful item the best available option is shown with a notice.",
  whyTitle: "Why this item?", scoreWord: "Score", ilvlTie: "Item level (tiebreaker)",
  howTo: "How to get it ↗", moreAlts: "Alternatives",
  lootTitle: "Dungeon loot for your gear", lootIntro: "Enter your current gear —or press \"Use recommended\" to compare against the recommendation— and see which items in each dungeon improve each slot and by how much.",
  lootPick: "Dungeon", lootSlot: "Slot", lootSlotAll: "All slots", lootAuto: "By your level", lootOnlyUp: "Upgrades only",
  lootSort: "Sort", lootSortBoss: "Boss", lootSortUpgrade: "Upgrade", lootSortIlvl: "iLvl",
  lootEquip: "Equip", lootEquipped: "Equipped", lootUndo: "Undo",
  lootHeroicNeedGear: "Heroic access: enter your current gear to calculate your average item level. This heroic requires {req}.",
  lootHeroicLocked: "Heroic Dungeon Finder: requires average item level {req}; you have {avg}. Heroic-only items are hidden; keep gearing through normals, quests, and emblems.",
  lootHeroicOpen: "Heroic Dungeon Finder: unlocked (average item level {avg} ≥ {req}).",
  lootHeroicNote: "Dungeon Finder-style calculation: empty slots count as 0 and leveling heirlooms count as item level 1.",
  lootHeroicHidden: " heroic items hidden",
  lootHeroicEmpty: "Heroic-only items for this dungeon are hidden until you reach average item level {req}.",
  heroicGeneralNeedGear: "Heroics: enter your current gear to check access by average item level.",
  heroicGeneralLocked: "Heroics: locked at average item level {avg}; all require at least 180.",
  heroicGeneralPartial: "Heroics: partial access at average item level {avg}; ToC5, FoS, and PoS require 200, HoR requires 219.",
  heroicGeneralOpen: "Heroics: unlocked at average item level {avg}.",
  lootWhy: "Show breakdown", lootThis: "This item", lootWearing: "Your gear", lootDiff: "Difference",
  lootNoteGems: "Includes gems and socket bonuses; not enchants.", lootNoteCaps: "The percentage does not subtract hit or expertise caps; you are warned if this item would exceed one.",
  lootSetNote: "The Tier 10 set bonus is not added to this percentage.", lootCapsWarn: "This item would put you over the ", lootCapsSuffix: " cap (before gems or enchants).",
  lootEmptyFiltered: "No item matches these filters.", lootClearSlotFilter: "Show all slots", lootClearOnlyUp: "Turn off Upgrades only",
  lootShowOffspec: "Show off-spec items", lootClearSlot: "Clear this slot",
  showOffspec: "Show off-spec items", offspecTag: "Off-spec",
  showHeirlooms: "Include leveling heirlooms I already own",
  heirloomNote: "Leveling heirlooms cost Emblems of Heroism or Wintergrasp Marks, which are earned at level 80. They stay out of recommendations unless you check «Include leveling heirlooms I already own». Class relics (sigil, totem, idol, and libram) are normal gear and do appear in the ranking.",
  lootHidden: " off-spec", offspecGear: "Off-spec",
  lootEmpty: "No useful item for your spec in this dungeon.", zoneDrops: "Zone loot"
});


const FACTION_HEIRLOOM = { "44097": "horde", "44098": "alliance" };


const $ = (id) => document.getElementById(id);

const classesEl = $("classes");

const specsEl = $("specs");

const factionsEl = $("factions");

const slotsEl = $("slots");

const levelInput = $("levelInput");

const levelRange = $("levelRange");

const levelNumber = $("levelNumber");

const bracketLabel = $("bracketLabel");

const classNote = $("classNote");

const statList = $("statList");

const statsHint = $("statsHint");

const dungeonList = $("dungeonList");

const heirloomPanel = $("heirloomPanel");

const heirloomList = $("heirloomList");

const slotCount = $("slotCount");


function load(key, fallback) {
  try { return localStorage.getItem(key) || fallback; } catch (err) { return fallback; }
}

function save(key, value) {
  try { localStorage.setItem(key, value); } catch (err) { /* sin almacenamiento */ }
}

function esc(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}


let state = {
  cls: load(STORE.cls, "Warrior"),
  spec: load(STORE.spec, "Arms"),
  level: Number(load(STORE.level, 20)) || 20,
  faction: load(STORE.faction, "horde"),
  lang: load(STORE.lang, "es"),
  scope: load(STORE.scope, "noraid"),
  phase: Number(load(STORE.phase, 0)) || 0,
  pvp: load(STORE.pvp, "0") === "1",
  alts: Number(load(STORE.alts, 2)) || 2,
  dungeon: Number(load(STORE.dungeon, 0)) || 0,
  lootSlot: load(STORE.lootSlot, ""),
  lootSort: load(STORE.lootSort, "boss"),
  onlyUp: load(STORE.onlyUp, "0") === "1",
  showOffspec: load(STORE.showOffspec, "0") === "1",
  showHeirlooms: load(STORE.showHeirlooms, "0") === "1",
  fresh: load(STORE.fresh, "0") === "1",
  bisPhase: load(STORE.bisPhase, "F80"),
  bisGuide: load(STORE.bisGuide, "1") === "1",
  wOverride: (() => { try { return JSON.parse(load(STORE.weights, "{}")) || {}; } catch (e) { return {}; } })(),
  gear: (() => { try { return JSON.parse(load(STORE.gear, "{}")) || {}; } catch (e) { return {}; } })()
};
if (state.scope !== "raid") state.scope = "noraid";
if (state.level !== 80 || state.pvp || state.scope === "raid") state.fresh = false;
if (![0, 1, 2, 3, 4].includes(state.phase)) state.phase = 0;
if (![2, 5, 10].includes(state.alts)) state.alts = 2;
if (!["F80", "PR", "T7", "T8", "T9", "T10"].includes(state.bisPhase)) state.bisPhase = "F80";
if (!DATA.factions.includes(state.faction)) state.faction = "horde";
if (!["boss", "upgrade", "ilvl"].includes(state.lootSort)) state.lootSort = "boss";
if (!I18N[state.lang]) state.lang = "es";
if (!DATA.specs[state.cls + "|" + state.spec]) {
  state.cls = "Warrior";
  state.spec = "Arms";
}
if (!DATA.classMeta[state.cls]) state.cls = "Warrior";


const STAT_ORDER = [
  "str", "agi", "int", "sta", "sp", "ap", "hit", "crit", "haste", "exp",
  "arp", "def", "dodge", "parry", "block", "mp5", "spi", "heal", "blockval", "res", "spen"
];


const QUALITY_COLOR = { 2: "#1eff00", 3: "#2f9bff", 4: "#b45cff", 7: "#32d6ff" };


function allSpecsFor(cls) {
  const prefix = cls + "|";
  return Object.keys(DATA.specs)
    .filter((key) => key.indexOf(prefix) === 0)
    .map((key) => key.slice(prefix.length));
}


function specFor(cls, name) {
  return DATA.specs[cls + "|" + name];
}


function clampLevel(value) {
  const min = DATA.classMeta[state.cls].min;
  return Math.max(min, Math.min(80, Number(value) || min));
}


function t(key) { return (I18N[state.lang] && I18N[state.lang][key]) || key; }


function applyLanguage() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const value = I18N[state.lang] && I18N[state.lang][el.dataset.i18n];
    if (value) el.textContent = value;
  });
  document.querySelectorAll(".lang-switch button").forEach((btn) => {
    btn.setAttribute("aria-pressed", String(btn.dataset.lang === state.lang));
    btn.classList.toggle("active", btn.dataset.lang === state.lang);
  });
}


function armorText(cls, level) {
  if (state.lang === "en") {
    if (cls === "Hunter" || cls === "Shaman") return level < 40 ? "Leather (mail at 40)" : "Mail";
    if (cls === "Paladin" || cls === "Warrior") return level < 40 ? "Mail (plate at 40)" : "Plate";
    return DATA.classMetaEn[cls].armor;
  }
  if (cls === "Hunter" || cls === "Shaman") return level < 40 ? "Cuero (malla al 40)" : "Malla";
  if (cls === "Paladin" || cls === "Warrior") return level < 40 ? "Malla (placa al 40)" : "Placa";
  return DATA.classMeta[cls].armor;
}


function bracketName(bracket) {
  return state.lang === "en" ? (bracket.nameEn || bracket.name) : bracket.name;
}


function bracketAdvice(bracket) {
  return state.lang === "en" ? (bracket.adviceEn || bracket.advice) : bracket.advice;
}


function bracketFor(level) {
  return DATA.brackets.find((b) => level >= b.min && level <= b.max) || DATA.brackets[0];
}


function qColor(q) { return QUALITY_COLOR[q] || "#9fb9c8"; }


const ICON_LOCAL = typeof ICON_DATA !== "undefined" ? ICON_DATA : {};

const iconSrc = (name) => (ICON_LOCAL[name] ? "data:image/jpeg;base64," + ICON_LOCAL[name] : "https://wotlk.evowow.com/static/images/wow/icons/medium/" + name + ".jpg");

function iconHtml(item) {
  if (!item || !item.i) return '<div class="item-icon placeholder">?</div>';
  return '<img class="item-icon" src="' + esc(iconSrc(item.i)) + '" alt="" loading="lazy" onerror="this.style.visibility=\'hidden\'">';
}


function itemLink(id, scaled, className) {
  const item = DATA.items[id] || DATA.heirlooms[id];
  if (!item) return "";
  const rel = scaled ? ' rel="lvl=' + state.level + ' noopener"' : ' rel="noopener"';
  return '<a class="' + (className || "") + '" style="color:' + qColor(item.q) + '" href="https://wotlk.evowow.com/?item=' + id + '" target="_blank"' + rel + '>' + esc(item.n) + "</a>";
}



function statLine(item) {
  const stats = item.st || {}, px = item.px || {};
  const lab = (key) => (STAT_LABEL[state.lang] || STAT_LABEL.es)[key] || key;
  const keys = STAT_ORDER.filter((key) => stats[key]);
  const fx = Object.keys(px).map((key) => '<span class="fx" title="' + (state.lang === "en" ? "Average value of the proc or on-use effect" : "Valor promedio del proc o efecto de uso") + '"><b>≈+' + px[key] + "</b> " + lab(key) + "</span>");
  if (!keys.length && !fx.length) return item.ar ? "<span>" + (state.lang === "en" ? "Armor " : "Armadura ") + item.ar + "</span>" : "<span>" + (state.lang === "en" ? "No stats" : "Sin estadísticas") + "</span>";
  return keys.slice(0, 6).map((key) => "<span><b>+" + stats[key] + "</b> " + lab(key) + "</span>").join("") + fx.join("");
}


/* ---------- Motor de recomendaciones (se calcula en el navegador) ---------- */

const ITEM_URL = "https://wotlk.evowow.com/?item=";

const L = (es, en) => (state.lang === "en" ? en : es);

const gearItem = (id) => DATA.items[id] || DATA.heirlooms[id];

const itemHands = (it) => (it.s === "twohand" ? 2 : (it.s === "onehand" || it.s === "mainhand" || it.s === "offhand" ? 1 : 0));
// Las reliquias escalan con el nivel y las de malla/placa cambian de tipo antes del 40.

function levelItem(it, level) {
  if (!it.hl) return it;
  let stage = it.hl[0];
  for (const row of it.hl) { if (row[0] <= level) stage = row; else break; }
  const data = (stage && stage[1]) || {};
  const at = level < 40 ? (it.at === "Plate" ? "Mail" : it.at === "Mail" ? "Leather" : it.at) : it.at;
  return Object.assign({}, it, { ar: data.ar || 0, dps: data.dps || 0, st: data.st || {}, at, ilvl: level });
}

const zoneOf = (id) => DATA.dungeons.find((d) => d.id === id) || (DATA.raids || []).find((d) => d.id === id);


function specSlots(spec) {
  return DATA.slotOrder.filter((s) => (s === "offhand" ? !!spec.off : s === "ranged" ? !!spec.ranged : s === "relic" ? !!spec.relic : true));
}

// La armadura de un tipo inferior se penaliza por completo en físicos y tanques; en casters, sanadores, cazadores y
// pícaros/chamanes de agilidad pesa menos, porque las guías usan a menudo tela o cuero en slots sin set.

const poolOfSlot = (s) => (s.startsWith("ring") ? "ring" : s.startsWith("trinket") ? "trinket" : s);

const gearKey = () => state.cls + "|" + state.spec;

const equippedMap = () => state.gear[gearKey()] || {};

function currentSpec() {
  return DATA.specs[state.cls + "|" + state.spec];
}

function titanGrip(spec, level) {
  return !!spec && spec.mode === "tg" && level >= 60;
}

function equippedMainTwoHand(spec) {
  const id = equippedMap().mainhand, it = id && gearItem(id);
  return !!(it && itemHands(it) === 2 && !titanGrip(spec || currentSpec(), state.level));
}
/* El equipo que ya llevas puesto puede ser cualquier cosa que tu clase pueda equipar,
   aunque no sea ideal para la especialidad (armas de dos manos, otro tipo de armadura, etc.). */

function clearLootUndo() {
  runtime.lastEquip = null;
  const box = $("lootUndo");
  if (box) box.hidden = true;
}

function renderLootUndo() {
  const box = $("lootUndo");
  if (!box) return;
  if (!runtime.lastEquip || runtime.lastEquip.key !== gearKey()) { box.hidden = true; return; }
  $("lootUndoText").textContent = t("lootEquipped") + ": " + runtime.lastEquip.name;
  box.hidden = false;
}

const pctDiff = (a, b) => (b > 0 ? Math.round((a / b - 1) * 100) : 0);

function renderSeg(el, options, current, onPick) {
  el.innerHTML = "";
  options.forEach((o) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "seg-btn";
    btn.textContent = o.label;
    btn.setAttribute("aria-pressed", String(o.value === current));
    btn.addEventListener("click", () => onPick(o.value));
    el.appendChild(btn);
  });
}


function persist() {
  save(STORE.cls, state.cls);
  save(STORE.spec, state.spec);
  save(STORE.level, String(state.level));
  save(STORE.faction, state.faction);
  save(STORE.lang, state.lang);
  save(STORE.scope, state.scope);
  save(STORE.phase, String(state.phase));
  save(STORE.pvp, state.pvp ? "1" : "0");
  save(STORE.alts, String(state.alts));
  save(STORE.dungeon, String(state.dungeon));
  save(STORE.lootSlot, state.lootSlot || "");
  save(STORE.lootSort, state.lootSort || "boss");
  save(STORE.onlyUp, state.onlyUp ? "1" : "0");
  save(STORE.showOffspec, state.showOffspec ? "1" : "0");
  save(STORE.showHeirlooms, state.showHeirlooms ? "1" : "0");
  save(STORE.fresh, state.fresh ? "1" : "0");
  save(STORE.bisPhase, state.bisPhase || "F80");
  save(STORE.bisGuide, state.bisGuide ? "1" : "0");
  save(STORE.weights, JSON.stringify(state.wOverride || {}));
  save(STORE.gear, JSON.stringify(state.gear));
}


const eqNorm = (n) => String(n || "").replace(/[\u2018\u2019]/g, "'").trim().toLowerCase();

let refreshTimer = null;

function scheduleRefresh() {
  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(() => {
    try {
      if (window.$WowheadPower && window.$WowheadPower.refreshLinks) window.$WowheadPower.refreshLinks();
    } catch (err) { /* widget no listo */ }
    setTimeout(() => {
      try {
        if (window.$WowheadPower && window.$WowheadPower.refreshLinks) window.$WowheadPower.refreshLinks();
      } catch (err) { /* widget no listo */ }
    }, 900);
  }, 600);
}

export { runtime, STORE, I18N, SLOT_LABEL, STAT_LABEL, STATS_EN, FACTION_HEIRLOOM, $, classesEl, specsEl, factionsEl, slotsEl, levelInput, levelRange, levelNumber, bracketLabel, classNote, statList, statsHint, dungeonList, heirloomPanel, heirloomList, slotCount, load, save, esc, state, STAT_ORDER, QUALITY_COLOR, allSpecsFor, specFor, clampLevel, t, applyLanguage, armorText, bracketName, bracketAdvice, bracketFor, qColor, ICON_LOCAL, iconSrc, iconHtml, itemLink, statLine, ITEM_URL, L, gearItem, itemHands, levelItem, zoneOf, specSlots, poolOfSlot, gearKey, equippedMap, currentSpec, titanGrip, equippedMainTwoHand, clearLootUndo, renderLootUndo, pctDiff, renderSeg, persist, eqNorm, refreshTimer, scheduleRefresh };
