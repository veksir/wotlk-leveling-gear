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
python scripts/fetch_atlasloot.py
python scripts/build_loot.py
python scripts/build_item_db.py
python scripts/build_recommendations.py
python scripts/build_page.py
```

Ejecuta la prueba de humo:

```bash
python tests/smoke.py
```

## Dónde hacer los cambios

- `src/template.html`: HTML, CSS y JavaScript del cliente. Es la fuente de la página.
- `scripts/build_item_db.py`: parseo de objetos, estadísticas, niveles requeridos, armadura/armas y fuentes.
- `scripts/build_recommendations.py`: reglas por clase/especialidad, filtro de facción, elegibilidad de armadura/armas, puntuación y ranking.
- `scripts/build_page.py`: inyecta los datos en la plantilla y escribe `tolltip.html`.
- `tests/smoke.py`: prueba de humo en navegador.

**No** edites `tolltip.html` a mano. Es generado. Después de cambiar la plantilla o los datos, vuelve a ejecutar la generación.

## Reglas de datos

- No subas `data/raw_items.json`, `data/raw_zones.json` ni `data/items.json`. Están ignorados a propósito.
- Incluye `data/gear_data.json` cuando cambien las recomendaciones.
- Mantén las fuentes y la disponibilidad por facción con la mayor precisión posible. Si una fuente es desconocida, usa “Otra fuente” en vez de adivinar.
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
- [ ] `python tests/smoke.py` pasa.
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
