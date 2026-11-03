# Equipo óptimo por nivel — WotLK 3.3.5

Página estática que muestra el mejor objeto disponible en cada slot para una clase, especialidad y nivel de 1 a 80.

## Alcance

- 31 especialidades de las 10 clases.
- Selector de facción Horda/Alianza para misiones y vendedores.
- Interfaz en español e inglés.
- 18 slots posibles: armadura, anillos, abalorios, armas, escudo/offhand y reliquia.
- Mejor objeto + 2 alternativas por slot.
- Se priorizan misiones, mazmorras, vendedores y drops. El equipo PvP y las fuentes no registradas solo se usan si no hay una alternativa de subida.
- No incluye botín de banda.
- Las reliquias de herencia quedan en un panel aparte y mantienen sus tooltips escalados al nivel.
- Tooltips de EVOWOW para todos los objetos.

## Generar la página

```bash
python scripts/fetch_raw.py
python scripts/build_item_db.py
python scripts/build_recommendations.py
python scripts/build_page.py
```

El resultado se escribe en `tolltip.html` y en `C:\Users\user\Desktop\tolltip.html`.

## Probar

```bash
python tests/smoke.py
```

## Datos

La base de objetos se construye a partir de `wow-classic-items`:

- https://github.com/nexus-devs/wow-classic-items
- `data/json/data.json`
- `data/json/zones.json`

El repositorio no versiona los JSON crudos ni la base intermedia; se pueden recuperar con `scripts/fetch_raw.py`.
