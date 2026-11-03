import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from data_leveling import payload

base = Path(__file__).parent
html = (base / "template.html").read_text(encoding="utf-8")
data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
html = html.replace("/*__DATA__*/", data)
html = html.replace("<!--__BODY__-->", "")
out = Path(r"C:\Users\user\Desktop\tolltip.html")
out.write_text(html, encoding="utf-8")
print(f"escrito {out} ({out.stat().st_size} bytes, {len(data)} bytes de datos)")
