"""Descarga las tablas de botín de WotLK (por jefe y dificultad) de AtlasLootClassic.

Rellena lo que el dataset principal no trae (Ulduar, Trial of the Crusader, Icecrown Citadel,
Vault of Archavon, Ruby Sanctum...) y distingue mazmorra normal de heroica."""
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/Hoizame/AtlasLootClassic/master/AtlasLootClassic_DungeonsAndRaids/data-wrath.lua"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw_atlasloot_wrath.lua"


def main():
    OUT.write_bytes(urllib.request.urlopen(URL, timeout=60).read())
    print("escrito", OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
