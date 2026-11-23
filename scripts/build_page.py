import argparse
import base64
import gzip
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "index.html"
DESKTOP = Path.home() / "Desktop" / "tolltip.html"
DATA_PATH = ROOT / "data" / "gear_data.json"

ap = argparse.ArgumentParser(description="Construye tolltip.html con Vite y comprime el módulo principal.")
ap.add_argument("--plain", action="store_true", help="sin comprimir")
ap.add_argument("--out", type=Path, default=None, help="archivo de salida (por defecto tolltip.html)")
ap.add_argument("--icons", type=Path, default=None, help="carpeta con iconos .jpg para incrustarlos")
ARGS = ap.parse_args()
PLAIN = ARGS.plain
OUT = ARGS.out or ROOT / "tolltip.html"
icon_js = ""
if ARGS.icons:
    icons = {f.stem: base64.b64encode(f.read_bytes()).decode("ascii") for f in sorted(ARGS.icons.glob("*.jpg"))}
    icon_js = "const ICON_DATA = " + json.dumps(icons, separators=(",", ":")) + ";\n"

command = ["npm", "run", "build"]
if os.name == "nt":
    command = ["cmd", "/c"] + command
subprocess.run(command, cwd=ROOT, check=True)

if not DIST.exists():
    raise SystemExit("Vite no generó dist/index.html")
html = DIST.read_text(encoding="utf-8")

if not PLAIN:
    match = re.search(r'<script type="module"(?: crossorigin)?>(.*?)</script>', html, re.S)
    if not match:
        raise SystemExit("No se encontró el módulo principal en dist/index.html")
    code = (icon_js + match.group(1)).encode("utf-8")
    packed = base64.b64encode(gzip.compress(code, compresslevel=9, mtime=0)).decode("ascii")
    boot = (
        "<script>\n"
        "(function(){\n"
        '  function boot(){\n'
        f'    const B64="{packed}";\n'
        '    const bin=atob(B64), bytes=new Uint8Array(bin.length);\n'
        '    for(let i=0;i<bin.length;i++) bytes[i]=bin.charCodeAt(i);\n'
        '    const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));\n'
        '    new Response(stream).text().then(function(code){\n'
        '      const s=document.createElement("script");\n'
        '      s.type="module"; s.textContent=code; document.body.appendChild(s);\n'
        '    }).catch(function(err){\n'
        '      document.body.insertAdjacentHTML("beforeend","<pre>Error al descomprimir la página: "+err+"</pre>");\n'
        '    });\n'
        '  }\n'
        '  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);\n'
        '  else boot();\n'
        '})();\n'
        "</script>"
    )
    html = html[:match.start()] + boot + html[match.end():]
elif icon_js:
    match = re.search(r'<script type="module"(?: crossorigin)?>', html)
    if not match:
        raise SystemExit("No se encontró el módulo principal en dist/index.html")
    html = html[:match.end()] + "\n" + icon_js + html[match.end():]

outputs = [OUT]
if ARGS.out is None and DESKTOP.parent.exists():
    outputs.append(DESKTOP)
for path in outputs:
    path.write_text(html, encoding="utf-8")
print(
    "escrito "
    + " y ".join(str(path) for path in outputs)
    + f" ({len(html.encode('utf-8'))} bytes, datos {DATA_PATH.stat().st_size} bytes)"
)
