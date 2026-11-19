import base64
import gzip
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "index.html"
OUT = ROOT / "tolltip.html"
DESKTOP = Path.home() / "Desktop" / "tolltip.html"
DATA = ROOT / "data" / "gear_data.json"
PLAIN = "--plain" in sys.argv

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
    code = match.group(1).encode("utf-8")
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

outputs = [OUT]
if DESKTOP.parent.exists():
    outputs.append(DESKTOP)
for path in outputs:
    path.write_text(html, encoding="utf-8")
print(
    "escrito "
    + " y ".join(str(path) for path in outputs)
    + f" ({len(html.encode('utf-8'))} bytes, datos {DATA.stat().st_size} bytes)"
)
