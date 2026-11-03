from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://raw.githubusercontent.com/nexus-devs/wow-classic-items/master/data/json/"
FILES = {
    "raw_items.json": "data.json",
    "raw_zones.json": "zones.json",
}


def main():
    ROOT.joinpath("data").mkdir(parents=True, exist_ok=True)
    for target, remote in FILES.items():
        url = BASE + remote
        req = Request(url, headers={"User-Agent": "tolltip-guide/1.0"})
        data = urlopen(req, timeout=120).read()
        path = ROOT / "data" / target
        path.write_bytes(data)
        print(f"{target}: {len(data)} bytes")


if __name__ == "__main__":
    main()
