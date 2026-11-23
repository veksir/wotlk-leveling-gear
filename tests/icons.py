"""Prueba de scripts/fetch_icons.py (contra un servidor local simulado) y de la incrustación de iconos con build_page.py --icons."""
import io
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def fake_jpeg():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (36, 36), (200, 40, 40)).save(buf, "JPEG")
    return buf.getvalue()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        served, out = tmp / "served", tmp / "icons"
        served.mkdir()
        # El servidor simulado responde a cualquier icono con la misma imagen: se crean copias de los que se pidan
        listing = subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_icons.py"), "--list-only", "--out", str(out)], capture_output=True, text=True)
        assert listing.returncode == 0 and "iconos necesarios" in listing.stdout, listing.stdout + listing.stderr
        needed = int(listing.stdout.split()[0])
        assert needed > 300, needed
        # Prepara 6 iconos servibles: los 6 primeros que pedirá el script (orden alfabético)
        from playwright.sync_api import sync_playwright as sp
        with sp() as p:
            b = p.chromium.launch(); pg = b.new_page(); pg.goto((ROOT / "tolltip.html").as_uri(), wait_until="load")
            pg.wait_for_function("typeof bisData === 'function' && document.querySelectorAll('#slots .slot').length > 0", timeout=30000)
            names = pg.evaluate("""() => { const s = new Set(); for (const key of Object.keys(DATA.specs)) { const [c, sp] = key.split('|'); state.cls = c; state.spec = sp;
              for (const ph of BIS_TABS) bisData(ph).rows.forEach((r) => r.list.forEach((e) => { if (e.it.i) s.add(e.it.i); })); } return [...s].sort().slice(0, 6); }""")
            b.close()
        for n in names:
            (served / f"{n}.jpg").write_bytes(fake_jpeg())
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(served)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_address[1]}/"
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_icons.py"), "--base", base, "--out", str(out), "--limit", "6"], capture_output=True, text=True)
        server.shutdown()
        assert r.returncode == 0 and "descargados 6" in r.stdout, r.stdout + r.stderr
        assert sorted(f.stem for f in out.glob("*.jpg")) == sorted(names)

        built = tmp / "con_iconos.html"
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_page.py"), "--icons", str(out), "--out", str(built)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(built.as_uri(), wait_until="load")
            pg.wait_for_function("typeof iconSrc === 'function'", timeout=30000)
            res = pg.evaluate("(n) => ({ local: iconSrc(n[0]).startsWith('data:image/jpeg;base64,'), remote: iconSrc('no_existe').startsWith('https://wotlk.evowow.com/') })", names)
            assert res["local"] and res["remote"], res
            b.close()
            assert not errs, errs
    print("icons OK")


if __name__ == "__main__":
    main()
