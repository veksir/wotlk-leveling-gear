import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tolltip.html"
DESKTOP = Path.home() / "Desktop" / "tolltip.html"

template = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "data" / "gear_data.json").read_text(encoding="utf-8"))
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
html = template.replace("/*__DATA__*/", payload).replace("<!--__BODY__-->", "")
if "/*__DATA__*/" in html or "<!--__BODY__-->" in html:
    raise SystemExit("quedaron marcadores sin reemplazar")
outputs = [OUT]
if DESKTOP.parent.exists():
    outputs.append(DESKTOP)
for path in outputs:
    path.write_text(html, encoding="utf-8")
print("escrito " + " y ".join(str(path) for path in outputs) + f" ({len(html)} bytes, datos {len(payload)} bytes)")
