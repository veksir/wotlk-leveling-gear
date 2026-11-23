"""Prueba del importador de listas BiS por fase y de su uso en la página (guía de referencia, plan de meta-gema, enlaces de encantamientos)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()
errors = []


def main():
    data = json.loads((ROOT / "data" / "gear_data.json").read_text(encoding="utf-8"))
    ref = data["engine"]["refBis"]["Paladin|Protection"]
    name = lambda i: data["items"][i]["n"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        lista = tmp / "lista.txt"
        lista.write_text(f"# comentario\nCabeza: {name(ref['head'][0])}; {name(ref['head'][1])}\nAnillos: {name(ref['ring'][0])}; {name(ref['ring'][1])}\nPecho: {name(ref['chest'][0])}\n", encoding="utf-8")
        out = tmp / "fases.json"
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "import_bis_list.py"), "Paladin|Protection", "PR", str(lista), "--out", str(out)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        saved = json.loads(out.read_text(encoding="utf-8"))["Paladin|Protection"]["PR"]
        assert saved["head"][:2] == ref["head"][:2] and saved["chest"][0] == ref["chest"][0] and len(saved["ring"]) == 2, saved
        # fusiona otra fase sin perder la anterior
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "import_bis_list.py"), "Paladin|Protection", "T8", str(lista), "--out", str(out)], capture_output=True, text=True)
        assert r.returncode == 0 and set(json.loads(out.read_text(encoding="utf-8"))["Paladin|Protection"]) == {"PR", "T8"}
        # nombres desconocidos: error salvo --allow-missing
        lista.write_text("Cabeza: Objeto que no existe\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "import_bis_list.py"), "Paladin|Protection", "PR", str(lista), "--out", str(out)], capture_output=True, text=True)
        assert r.returncode != 0 and "No encontrado" in r.stdout

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1500)
        page.evaluate("document.getElementById('rankDetails').open = true")
        page.get_by_role("button", name="Paladin", exact=True).click()
        page.get_by_role("button", name="Protection", exact=True).click()

        # La página usa una guía de fase cuando existe (se simula inyectándola) y la casilla aparece solo entonces
        res = page.evaluate("""(ref) => {
          const pr = BIS_PHASES[0];
          const before = bisData(pr).rows.some((r) => r.list.some((e) => e.curated));
          ENG.refBisPhases = { 'Paladin|Protection': { PR: { chest: ref.chest, head: ref.head } } };
          bisCache.clear(); state.bisPhase = 'PR'; renderBis(currentSpec());
          const d = bisData(pr);
          return { before, chest: d.rows.find((r) => r.slot === 'chest').list[0].id, head: d.rows.find((r) => r.slot === 'head').list[0].id,
                   boxHidden: document.getElementById('bisGuideBox').hidden, t8: bisData(BIS_PHASES[2]).rows.some((r) => r.list.some((e) => e.curated)) };
        }""", ref)
        assert not res["before"] and res["chest"] == ref["chest"][0] and res["head"] == ref["head"][0] and not res["boxHidden"] and not res["t8"], res
        page.evaluate("ENG.refBisPhases = {}; bisCache.clear(); state.bisPhase = 'F80'; renderBis(currentSpec());")
        assert page.locator("#bisGuideBox").is_hidden()

        # Enlaces de encantamientos: hechizos (id < 30000) u objetos
        res = page.evaluate("""() => ({ spell: enchLink({ id: 25080, name: 'A' }), item: enchLink({ id: 44494, name: 'B' }) })""")
        assert "?spell=25080" in res["spell"] and "?item=44494" in res["item"], res

        # Plan de meta-gema para todas las especialidades y pestañas: siempre hay plan y siempre cubre el requisito
        res = page.evaluate("""() => {
          const bad = [];
          for (const key of Object.keys(DATA.specs)) {
            const [c, s] = key.split('|'); state.cls = c; state.spec = s;
            for (const ph of BIS_TABS) {
              const m = metaPlan(bisData(ph));
              if (!m) bad.push(key + ' ' + ph.key + ' sin plan');
              else if (/no llega|cannot cover/.test(m)) bad.push(key + ' ' + ph.key + ' incompleto');
            }
          }
          return bad;
        }""")
        assert not res, res[:6]
        page.evaluate("state.cls = 'Paladin'; state.spec = 'Protection';")
        plan = page.evaluate("metaPlan(bisData(BIS_PHASES[3]))")
        assert "Austere Earthsiege Diamond" in plan and "Dreadstone" in plan, plan
        plan = page.evaluate("state.cls = 'Rogue'; state.spec = 'Combat'; metaPlan(bisData(BIS_PHASES[3]))")
        assert "Nightmare Tear" in plan, plan
        browser.close()
    assert not errors, errors
    print("import_bis OK")


if __name__ == "__main__":
    main()
