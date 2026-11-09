# WotLK Leveling Gear

[English](README.md) | **Español**

[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-yellow.svg)](LICENSE)
![World of Warcraft](https://img.shields.io/badge/WotLK-3.3.5-0b2230)
![Sitio estático](https://img.shields.io/badge/est%C3%A1tico-HTML%20%2B%20JS-75d7ef)

Guía estática que responde una pregunta:

> ¿Cuál es el objeto más fuerte que puedo equipar en cada slot a mi nivel actual?

Incluye las 10 clases de WotLK, 31 especialidades, niveles 1–80, Horda/Alianza y español/inglés.

![Interfaz en español](docs/screenshot-es.png)

## Características

- **Ficha de equipamiento completa**: cabeza, cuello, hombros, espalda, pecho, muñecas, manos, cintura, piernas, pies, anillos, abalorios, mano principal, mano secundaria, a distancia y reliquia de clase.
- **Mejor objeto por slot** con 2, 5 o 10 alternativas, ordenadas por puntuación (no por fuente).
- **Cómo conseguirlo**: cada objeto muestra su fuente (misión, vendedor, jefe de mazmorra con probabilidad de drop, banda, drop raro) y enlaza a su ficha de EVOWOW.
- **«¿Por qué este objeto?»** por slot: desglose de la puntuación por estadística, penalización por tipo de armadura, comparación con la siguiente alternativa y aviso cuando una opción de mayor nivel está oculta o es peor.
- **Modos de contenido**: «Sin bandas» (por defecto) o «Con bandas», fase de raid 1–4 o Todas y un modo aparte «Solo PvP» (el PvE es el predeterminado; el equipo PvP nunca se mezcla en la recomendación PvE).
- **Legendarios incluidos**: los legendarios se puntúan como cualquier otro objeto y aparecen cuando son la mejor opción; los de banda requieren «Con bandas». La página muestra el top por slot, no un catálogo completo de legendarios.
- **Abalorios con procs**: los efectos de uso y los procs se promedian según duración y enfriamiento (≈). Las listas curadas de abalorios de las guías mandan en su slot.
- **Gemas por color y meta-gemas**: cada socket usa la mejor gema de su color; el bonus de socket solo se activa si se respetan los colores y la meta-gema solo cuenta si cumple sus requisitos y compensa su coste de activación.
- **Bonus de set T10**: el valor estimado del bonus de 2 o 4 piezas se reparte solo entre las piezas que recomienda la guía, no entre todo el set.
- **Reliquias de clase**: sigilos, tótems, ídolos y librams son equipo normal y se recomiendan cuando la guía los incluye. Son distintas de las reliquias de subida (heirlooms).
- **Topes de nivel 80**: se muestran los totales de golpe y pericia; lo que excede el tope vale un 15 %.
- **Buscador de botín**: indica lo que lleva puesto tu personaje (o carga el recomendado), elige una mazmorra o banda y mira todo lo que puede soltar para tu clase y especialidad, con el % de cambio frente a tu pieza equipada. El botín fuera de especialidad queda oculto por defecto y se puede mostrar con un interruptor.
- **Filtro de facción**: las misiones y vendedores se ajustan a Horda o Alianza.
- **Interfaz bilingüe**: español e inglés.
- **Detalle de cada objeto**: icono, calidad, nivel de objeto, nivel requerido, estadísticas relevantes y fuente.
- **Reliquias de subida (heirlooms) opcionales**: las 35 reliquias de subida tienen estadísticas exactas por nivel y cambio de tipo de armadura antes del nivel 40. Quedan fuera de las recomendaciones salvo que marques «Incluir reliquias de subida (heirlooms) que ya tengo», porque sus vendedores requieren moneda de nivel 80.
- **Tooltips de EVOWOW** para todos los objetos.
- **Diseño responsive** y selección guardada en `localStorage`.
- **Sin backend** y sin compilación para ver la página.

## Cómo funciona

1. `scripts/fetch_raw.py` descarga los datos crudos de objetos y zonas, `scripts/fetch_heirloom_stats.py` añade las estadísticas de las reliquias nivel a nivel, y `scripts/fetch_atlasloot.py` + `scripts/build_loot.py` añaden las tablas de botín por jefe de WotLK (Ulduar, Trial of the Crusader, Icecrown Citadel, mazmorras heroicas, 10/25) desde AtlasLootClassic.
2. `scripts/build_item_db.py` normaliza objetos, estadísticas (incluidos los procs y efectos de uso de abalorios, promediados, colores de socket y socket meta), niveles requeridos, armadura/armas y fuentes.
3. `scripts/build_recommendations.py` genera la base de objetos, las definiciones de especialidad, los pesos de estadísticas, las gemas de referencia y meta-gemas, los bonus de set T10, los abalorios y reliquias curados y la lista de mazmorras. A nivel 80 se usa la prioridad de Icy Veins de cada especialidad, calibrada con WowSims cuando hay datos; por debajo de 80, los pesos por rol mantienen el equipo de subida coherente. Las reliquias de subida solo se rankean si activas «Incluir reliquias de subida (heirlooms) que ya tengo»; las reliquias de clase son equipo normal. El ranking se calcula en el navegador, así que los filtros de modo, fase, PvP y facción se aplican al instante. A nivel 80 el navegador elige a la vez armadura y anillos con una búsqueda en haz; armas, abalorios y reliquias mantienen sus reglas.
4. `scripts/build_page.py` inyecta el JSON generado en `src/template.html` y escribe `tolltip.html`.

El ranking es una heurística práctica, no un simulador de combate: ordena por una puntuación ponderada de estadísticas (el nivel de objeto solo desempata), usa prioridades por especialidad a nivel 80 y pesos por rol durante la subida, penaliza los tipos de armadura que no son ideales para la clase, promedia los procs y efectos de uso de los abalorios según duración y enfriamiento, elige gemas por color, activa el bonus de socket solo si se respetan los colores, usa la meta-gema solo si cumple sus requisitos y compensa su coste, reparte el bonus de set T10 solo entre las piezas recomendadas, aplica los topes de golpe/pericia a nivel 80 y compara dos manos contra una mano + secundaria. Un arma a dos manos bloquea la mano secundaria salvo en especialidades con Titan's Grip. Los épicos sin fuente registrada de nivel de objeto 213 o más se tratan como botín de banda («banda probable»). Aún no se puntúan encantamientos ni objetos con encantamiento aleatorio.

## Inicio rápido

Clona el repositorio y abre `tolltip.html` en el navegador.

Necesitas conexión a internet para las fuentes de Google y los tooltips de EVOWOW. La página funciona sin servidor local.

## Generar desde el código

Requisitos:

- Python 3.10+
- Playwright + Chromium para la prueba de humo

```bash
python -m pip install playwright
python -m playwright install chromium

python scripts/fetch_raw.py
python scripts/fetch_heirloom_stats.py
python scripts/fetch_atlasloot.py
python scripts/build_loot.py
python scripts/build_item_db.py
python scripts/build_recommendations.py
python scripts/build_page.py

python tests/smoke.py
python tests/sockets.py
python tests/gems.py
python tests/optimizer.py
python tests/check_reference.py
python tests/check_reference.py --ref=reference_bis_ids.json
python tests/check_reference.py --min=487
python tests/heirlooms.py
python tests/spec_weights.py
python tests/features.py
python tests/reference_sets.py
python tests/reference_ids.py
```

`build_page.py` escribe `tolltip.html` en el repositorio y, si existe, también en `~/Desktop/tolltip.html`. `check_reference.py` audita las 31 especialidades a nivel 80 contra las listas BiS de Icy Veins en `tests/reference_bis_ids.json` (por ID, Icy Veins + Wowhead) e informa de aciertos y coincidencias exactas; `--min=487` exige el gate actual y `--strict` es el objetivo final de 518/518. `sockets.py` comprueba los colores y el socket meta, `gems.py` la activación de la meta-gema y el bonus de socket, y `optimizer.py` la búsqueda en haz, el rendimiento (<750 ms) y que el nivel 79 no la use. `heirlooms.py` cubre el escalado por nivel, el filtro fuera de especialidad, las armas a dos manos y la búsqueda de reliquias; `features.py` cubre gemas/sockets, bonus de set y reliquias curadas; `reference_sets.py` valida las piezas de los sets T10; `reference_ids.py` valida la referencia por ID; `spec_weights.py` comprueba las 31 especialidades a nivel 80.

## Estructura del proyecto

```text
.
├── data/                  # gear_data.json generado (los datos crudos se ignoran)
├── docs/                  # capturas para el README
├── legacy/                # implementación anterior, solo reliquias
├── scripts/               # pipeline de datos, ranking y generador de página
├── src/                   # plantilla HTML/CSS/JS
├── tests/                 # pruebas de humo y regresión con Playwright
├── tolltip.html           # página final autocontenida
├── README.md              # README en inglés
├── CONTRIBUTING.md        # guía de contribución en inglés
├── CONTRIBUTING.es.md     # guía de contribución en español
└── LICENSE
```

## Datos y atribución

La base de objetos se construye a partir de [wow-classic-items](https://github.com/nexus-devs/wow-classic-items):

- `data/json/data.json`
- `data/json/zones.json`

Las tablas de botín por jefe vienen de [AtlasLootClassic](https://github.com/Hoizame/AtlasLootClassic).

Los tooltips e iconos se cargan desde [EVOWOW](https://wotlk.evowow.com/).

Las estadísticas de las reliquias vienen de las tablas por nivel de [WoWWiki archive](https://wowwiki-archive.fandom.com/) y de la [API de tooltips de Wowhead WotLK](https://www.wowhead.com/wotlk). Las prioridades de estadísticas a nivel 80 siguen [Icy Veins WotLK Classic](https://www.icy-veins.com/wotlk-classic/) y, cuando hay datos, se calibran con los valores EP de [WowSims](https://wowsims.github.io/wotlk/); `data/spec_weights.json` guarda la fuente y la prioridad de cada especialidad, y `data/reference_spec_stats.json` conserva los valores de referencia en bruto. Las gemas, bonus de set T10, abalorios y reliquias de clase recomendados por las guías se guardan en `data/reference_gems.json`, `data/reference_sets.json` y `data/reference_trinkets.json`, con sus fuentes en cada archivo; las meta-gemas y su coste de activación están en `data/reference_meta_gems.json`.

Este proyecto no está afiliado a Blizzard Entertainment. World of Warcraft y Wrath of the Lich King son marcas de Blizzard Entertainment.

## Limitaciones

- La base está basada en WotLK Classic; algunas fuentes originales de 3.3.5 pueden faltar o aparecer como “Otra fuente”.
- En «Sin bandas» se excluyen el botín de banda y las cadenas de misión de banda; en «Con bandas» aparecen.
- Los pesos de estadísticas son aproximaciones por rol durante la subida y siguen las prioridades de Icy Veins, calibradas con WowSims cuando hay datos, a nivel 80. Sirven para orientar, no sustituyen a un simulador de BiS; los topes suaves de celeridad y las interacciones de talentos no se modelan.
- Las gemas se eligen por color y el bonus de socket solo se activa si se respetan los colores; la meta-gema usa un coste EP heurístico documentado en `data/reference_meta_gems.json` y no modela todos los efectos de activación. Los encantamientos, los encantamientos aleatorios y algunas interacciones de abalorios/sets siguen simplificados.
- Por debajo de nivel 80 se mantiene la aproximación anterior: una gema recomendada por socket y el bonus de socket cuenta la mitad.
- La búsqueda en haz de nivel 80 solo recorre armadura y anillos; armas, mano secundaria, ranged, abalorios y reliquias siguen el cálculo greedy o curado.
- El bonus de set T10 es una estimación que se reparte solo entre las piezas recomendadas por la guía; no simula por completo el uptime de 2 o 4 piezas.
- El botín fuera de especialidad está oculto por defecto. El interruptor lo muestra atenuado para valorar mejoras cruzadas sin mezclarlo con la recomendación.
- Las reliquias de subida (heirlooms) no se recomiendan por defecto: los Emblemas de Heroísmo y las Marcas de la Conquista del Invierno se obtienen a nivel 80. Activa «Incluir reliquias de subida (heirlooms) que ya tengo» solo si realmente las tienes. Las reliquias de clase son distintas y sí aparecen en el ranking.
- Algunos slots de niveles muy bajos pueden no tener objetos con estadísticas conocidas.
- La página muestra el mejor objeto y alternativas por slot, no todos los objetos. Un legendario solo aparece si puntúa para la especialidad, nivel, facción, modo, fase y filtro PvP seleccionados. Los legendarios de nivel bajo o que dependen de una combinación no modelada pueden no aparecer.
- Las combinaciones de armas cubren Frost Death Knight con dos armas de una mano y Titan's Grip de Fury (dos armas a dos manos). Otros setups especiales siguen simplificados, así que aún pueden faltar algunos objetos BiS.
- La página final incluye los datos incrustados, así que `tolltip.html` pesa alrededor de 5,1 MB.

## Contribuir

Se aceptan correcciones de objetos, traducciones, mejoras de UI y reportes de errores. Consulta [CONTRIBUTING.es.md](CONTRIBUTING.es.md).

## Licencia

[MIT](LICENSE) © 2026 veksir
