import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tolltip.html"
DESKTOP = Path(r"C:\Users\user\Desktop\tolltip.html")

template = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "data" / "gear_data.json").read_text(encoding="utf-8"))
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
html = template.replace("/*__DATA__*/", payload).replace("<!--__BODY__-->", "")
if "/*__DATA__*/" in html or "<!--__BODY__-->" in html:
    raise SystemExit("quedaron marcadores sin reemplazar")
OUT.write_text(html, encoding="utf-8")
DESKTOP.write_text(html, encoding="utf-8")
print(f"escrito {OUT} y {DESKTOP} ({len(html)} bytes, datos {len(payload)} bytes)")
