"""Valida los datos de sockets por color en data/gear_data.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    items = json.loads((ROOT / "data" / "gear_data.json").read_text(encoding="utf-8"))["items"]
    expected = {"50694": {"red", "blue", "yellow"}, "51258": {"blue", "yellow"}, "50656": {"red", "blue", "yellow"}}
    for iid, colors in expected.items():
        assert set(items[iid]["sg"]) == colors and items[iid]["sc"] == len(colors), (iid, items[iid].get("sg"))
    # Tooltip con el socket meta seguido de durabilidad: el color debe seguir detectándose.
    odd = items["23232"]
    assert odd["mt"] and odd["sg"] == ["prismatic", "prismatic"] and odd["sc"] == 2, odd
    with_sockets = [v for v in items.values() if v.get("sc")]
    assert with_sockets, "no hay objetos con sockets"
    # cada objeto con socket conserva el color de todos sus sockets y estos son válidos
    assert all(len(v["sg"]) == v["sc"] for v in with_sockets), "sc y sg no coinciden"
    assert all(c in ("red", "yellow", "blue", "prismatic") for v in with_sockets for c in v["sg"]), "color inválido"
    meta = [v for v in items.values() if v.get("mt")]
    assert len(meta) > 800, f"pocos objetos con socket meta: {len(meta)}"
    non_head = [(v["n"], v["s"]) for v in meta if v["s"] != "head"]
    assert non_head == [("Huge Sword of Sockety Goodness", "onehand")], non_head
    print(f"sockets ok: {len(with_sockets)} objetos con sockets, {len(meta)} con meta")


if __name__ == "__main__":
    main()
