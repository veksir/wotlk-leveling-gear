# Contribuir

[English](CONTRIBUTING.md) | **Español**

Gracias por tomarte el tiempo de mejorar WotLK Leveling Gear. El proyecto es una página estática con un pipeline de datos en Python, así que la mayoría de cambios caen en tres áreas: datos de objetos, lógica de ranking o interfaz.

## Formas de contribuir

- Reportar errores de objetos (objeto incorrecto, nivel incorrecto, fuente incorrecta, facción incorrecta).
- Mejorar los pesos de estadísticas o el filtrado de armadura/armas.
- Añadir o corregir traducciones.
- Mejorar el diseño, la accesibilidad o el comportamiento móvil.
- Corregir errores o mejorar los scripts de generación.

## Antes de empezar

Para cambios pequeños, abre directamente un pull request. Para cambios grandes (nuevas funciones, cambio de fuente de datos, rediseño del ranking), abre primero un issue para acordar el enfoque.

## Preparar el entorno

Requisitos:

- Python 3.10+
- Playwright con Chromium para la prueba de humo

```bash
git clone https://github.com/veksir/wotlk-leveling-gear.git
cd wotlk-leveling-gear
python -m pip install playwright
python -m playwright install chromium
```

Genera los datos y la página:

```bash
python scripts/fetch_raw.py
python scripts/fetch_heirloom_stats.py
python scripts/fetch_atlasloot.py
python scripts/build_loot.py
python scripts/build_item_db.py
python scripts/build_recommendations.py
python scripts/build_page.py
```

Ejecuta las pruebas de humo y regresión:

```bash
python tests/smoke.py
python tests/check_reference.py
python tests/check_reference.py --ref=reference_bis_ids.json
python tests/heirlooms.py
python tests/spec_weights.py
python tests/features.py
python tests/reference_ids.py
```

## Dónde hacer los cambios

- `src/template.html`: HTML, CSS y JavaScript del cliente. Es la fuente de la página.
- `scripts/build_item_db.py`: parseo de objetos, estadísticas, niveles requeridos, armadura/armas y fuentes.
- `scripts/build_recommendations.py`: reglas por clase/especialidad, filtro de facción, elegibilidad de armadura/armas, puntuación y ranking. Las prioridades de nivel 80 están en `data/spec_weights.json`.
- `scripts/fetch_heirloom_stats.py`: estadísticas de reliquias nivel a nivel desde WoWWiki archive y Wowhead.
- `scripts/build_page.py`: inyecta los datos en la plantilla y escribe `tolltip.html`.
- `tests/smoke.py`: prueba de humo en navegador.
- `tests/check_reference.py`: auditoría de aciertos contra las listas BiS de Icy Veins para las 31 especialidades a nivel 80; `--ref=reference_bis_ids.json` usa la referencia por ID.
- `tests/reference_bis.json`: listas BiS de referencia por nombre que usa la auditoría.
- `tests/reference_bis_ids.json`: referencia por ID con alternativas; la valida `reference_ids.py`.
- `tests/heirlooms.py`: escalado de reliquias de subida, filtro fuera de especialidad, reglas de mano secundaria con 2H y búsqueda de reliquias.
- `tests/features.py`: gemas/sockets, bonus de set T10 y abalorios/reliquias curados.
- `tests/reference_ids.py`: comprueba que cada ID de referencia existe, tiene el nombre correcto y pertenece a una ranura compatible.
- `tests/spec_weights.py`: las 31 especialidades a nivel 80.

**No** edites `tolltip.html` a mano. Es generado. Después de cambiar la plantilla o los datos, vuelve a ejecutar la generación.

## Reglas de datos

- No subas `data/raw_items.json`, `data/raw_zones.json` ni `data/items.json`. Están ignorados a propósito.
- Incluye `data/gear_data.json` cuando cambien las recomendaciones.
- Incluye `data/heirloom_stats.json` cuando cambien las reliquias y `data/spec_weights.json` cuando cambien las prioridades. Cada especialidad conserva su fuente (Icy Veins y, si aplica, WowSims) y su prioridad; `data/reference_spec_stats.json` guarda los valores de calibración en bruto.
- Mantén las fuentes y la disponibilidad por facción con la mayor precisión posible. Si una fuente es desconocida, usa “Otra fuente” en vez de adivinar.
- Al actualizar `tests/reference_bis.json` o `tests/reference_bis_ids.json`, comprueba que todos los objetos existan en el dataset y pertenezcan al slot que indica la guía. Ejecuta `python tests/reference_ids.py`.
- Las gemas, bonus de set T10, abalorios y reliquias de clase recomendados por las guías están en `data/reference_gems.json`, `data/reference_sets.json` y `data/reference_trinkets.json`. Conserva sus campos `source`/`contrast_source` y actualiza `data/gear_data.json`.
- No añadas botín de banda al ranking principal de subida salvo que cambie el alcance del proyecto.

## Reglas de interfaz

- Añade los textos nuevos al objeto `I18N` de `src/template.html` para **español e inglés**.
- Mantén coherentes las etiquetas de slots, estadísticas, fuentes y tramos entre idiomas.
- Revisa la página en escritorio y en móvil.
- Conserva el comportamiento de los tooltips (`rel="lvl=N noopener"` para reliquias, `rel="noopener"` para objetos normales).

## Estilo de commits

Usa commits cortos y atómicos. Se prefieren Conventional Commits:

```text
feat(ui): add faction selector
feat(engine): filter quests by faction
fix(data): correct required level for item 52572
test: cover English language toggle
docs: update build instructions
```

Evita mezclar cambios no relacionados en un mismo commit.

## Lista de comprobación para pull requests

- [ ] La página se genera con `python scripts/build_page.py`.
- [ ] Pasan `python tests/smoke.py`, `tests/check_reference.py`, `tests/check_reference.py --ref=reference_bis_ids.json`, `tests/heirlooms.py`, `tests/spec_weights.py`, `tests/features.py` y `tests/reference_ids.py`.
- [ ] `data/gear_data.json` y `tolltip.html` están regenerados si hace falta.
- [ ] Los textos en español e inglés están actualizados.
- [ ] No se incluyen datos crudos, cachés ni `__pycache__`.
- [ ] Se adjuntan capturas si hay cambios visuales.

## Reportar un problema de objeto

Incluye:

```text
Clase/Especialidad:
Nivel:
Facción:
Slot:
Objeto esperado:
Objeto actual:
Por qué es incorrecto:
Captura (opcional):
```

Los problemas de objetos se corrigen mucho más rápido con clase, especialidad, nivel y facción exactos.

## Licencia

Al contribuir, aceptas que tus cambios se publiquen bajo la [licencia MIT](LICENSE).
