import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "index.html"
OUT = ROOT / "tolltip.html"
DESKTOP = Path.home() / "Desktop" / "tolltip.html"
DATA = ROOT / "data" / "gear_data.json"

command = ["npm", "run", "build"]
if os.name == "nt":
    command = ["cmd", "/c"] + command
subprocess.run(command, cwd=ROOT, check=True)

if not DIST.exists():
    raise SystemExit("Vite no generó dist/index.html")
html = DIST.read_text(encoding="utf-8")
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
