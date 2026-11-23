"""Descarga los iconos de los objetos que muestra la página «BiS por fase» para poder incrustarlos y verlos sin internet.

Uso:
    python scripts/build_page.py                 # la página debe estar construida (se usa para saber qué iconos hacen falta)
    python scripts/fetch_icons.py                # descarga a assets/icons/  (omite los que ya existen)
    python scripts/build_page.py --icons assets/icons

Opciones: --base URL (origen de los iconos), --out DIR, --limit N, --list-only (solo muestra cuántos hacen falta).
Requiere acceso a internet (EVOWOW) y Playwright (ya usado por las pruebas)."""
import argparse
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://wotlk.evowow.com/static/images/wow/icons/medium/"


def needed_icons(page_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(Path(page_path).resolve().as_uri(), wait_until="load")
        page.wait_for_function("typeof bisData === 'function' && document.querySelectorAll('#slots .slot').length > 0", timeout=30000)
        icons = page.evaluate("""() => { const set = new Set();
          for (const key of Object.keys(DATA.specs)) { const [c, s] = key.split('|'); state.cls = c; state.spec = s;
            for (const ph of BIS_TABS) bisData(ph).rows.forEach((r) => r.list.forEach((e) => { if (e.it.i) set.add(e.it.i); })); }
          return [...set].sort(); }""")
        browser.close()
    return icons


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--out", type=Path, default=ROOT / "assets" / "icons")
    ap.add_argument("--page", type=Path, default=ROOT / "tolltip.html")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--list-only", action="store_true")
    a = ap.parse_args(argv)
    icons = needed_icons(a.page)
    todo = [i for i in icons if not (a.out / f"{i}.jpg").exists()]
    print(f"{len(icons)} iconos necesarios, {len(todo)} por descargar")
    if a.list_only:
        return
    a.out.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    for name in (todo[: a.limit] if a.limit else todo):
        try:
            with urllib.request.urlopen(urllib.request.Request(a.base + name + ".jpg", headers={"User-Agent": "wotlk-leveling-gear"}), timeout=20) as r:
                body = r.read()
            if len(body) < 100:
                raise ValueError("respuesta demasiado corta")
            (a.out / f"{name}.jpg").write_bytes(body)
            ok += 1
        except (urllib.error.URLError, ValueError, OSError) as e:
            fail += 1
            print("  fallo", name, e)
        time.sleep(0.02)
    print(f"descargados {ok}, fallidos {fail} -> {a.out}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
