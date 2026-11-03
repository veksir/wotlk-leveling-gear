import json
from pathlib import Path

names = json.loads(Path(r"C:\Users\user\AppData\Local\Temp\heirloom_names.json").read_text(encoding="utf-8"))

heirlooms = {
    "42985": {"name": names["42985"], "slot": "Hombros", "source": "Emblemas"},
    "44107": {"name": names["44107"], "slot": "Hombros", "source": "PvP"},
    "42984": {"name": names["42984"], "slot": "Hombros", "source": "Emblemas"},
    "44105": {"name": names["44105"], "slot": "Hombros", "source": "PvP"},
    "42952": {"name": names["42952"], "slot": "Hombros", "source": "Emblemas"},
    "44103": {"name": names["44103"], "slot": "Hombros", "source": "PvP"},
    "42951": {"name": names["42951"], "slot": "Hombros", "source": "Emblemas"},
    "44102": {"name": names["44102"], "slot": "Hombros", "source": "PvP"},
    "42950": {"name": names["42950"], "slot": "Hombros", "source": "Emblemas"},
    "44101": {"name": names["44101"], "slot": "Hombros", "source": "PvP"},
    "42949": {"name": names["42949"], "slot": "Hombros", "source": "Emblemas"},
    "44099": {"name": names["44099"], "slot": "Hombros", "source": "PvP"},
    "44100": {"name": names["44100"], "slot": "Hombros", "source": "PvP"},
    "48691": {"name": names["48691"], "slot": "Pecho", "source": "Emblemas"},
    "48687": {"name": names["48687"], "slot": "Pecho", "source": "Emblemas"},
    "48689": {"name": names["48689"], "slot": "Pecho", "source": "Emblemas"},
    "48683": {"name": names["48683"], "slot": "Pecho", "source": "Emblemas"},
    "48677": {"name": names["48677"], "slot": "Pecho", "source": "Emblemas"},
    "48685": {"name": names["48685"], "slot": "Pecho", "source": "Emblemas"},
    "42943": {"name": names["42943"], "slot": "Arma", "source": "Emblemas"},
    "44092": {"name": names["44092"], "slot": "Arma", "source": "PvP"},
    "48718": {"name": names["48718"], "slot": "Arma", "source": "Emblemas"},
    "42947": {"name": names["42947"], "slot": "Arma", "source": "Emblemas"},
    "44095": {"name": names["44095"], "slot": "Arma", "source": "PvP"},
    "42948": {"name": names["42948"], "slot": "Arma", "source": "Emblemas"},
    "44094": {"name": names["44094"], "slot": "Arma", "source": "PvP"},
    "48716": {"name": names["48716"], "slot": "Arma", "source": "Emblemas"},
    "42944": {"name": names["42944"], "slot": "Arma", "source": "Emblemas"},
    "44091": {"name": names["44091"], "slot": "Arma", "source": "PvP"},
    "42945": {"name": names["42945"], "slot": "Arma", "source": "Emblemas"},
    "44096": {"name": names["44096"], "slot": "Arma", "source": "PvP"},
    "42946": {"name": names["42946"], "slot": "A distancia", "source": "Emblemas"},
    "44093": {"name": names["44093"], "slot": "A distancia", "source": "PvP"},
    "42991": {"name": names["42991"], "slot": "Abalorios", "source": "Emblemas"},
    "42992": {"name": names["42992"], "slot": "Abalorios", "source": "Emblemas"},
}

sets = {
    "clothCaster": {"shoulders": ["42985", "44107"], "chest": ["48691"], "weapons": ["42947", "44095"], "trinkets": ["42992"]},
    "leatherCaster": {"shoulders": ["42984", "44105"], "chest": ["48687"], "weapons": ["42947", "44095"], "trinkets": ["42992"]},
    "leatherPhysical": {"shoulders": ["42952", "44103"], "chest": ["48689"], "weapons": ["42944", "44091"], "trinkets": ["42991"]},
    "mailCaster": {"shoulders": ["42951", "44102"], "chest": ["48683"], "weapons": ["42947", "44095"], "trinkets": ["42992"]},
    "mailPhysical": {"shoulders": ["42950", "44101"], "chest": ["48677"], "weapons": ["42946", "44093"], "trinkets": ["42991"]},
    "plateDps": {"shoulders": ["42949"], "chest": ["48685"], "weapons": ["42943", "44092"], "trinkets": ["42991"]},
    "plateTank": {"shoulders": ["44099"], "chest": ["48685"], "weapons": ["42943", "44092"], "trinkets": ["42991"]},
    "plateHealer": {"shoulders": ["44100"], "chest": [], "weapons": ["42948", "44094"], "trinkets": ["42992"]},
}

specs = {
    "Death Knight": {
        "Blood Tank": {"set": "plateTank", "role": "tank", "primary": "str", "weapons": ["42943", "44092"], "offhand": "none", "ranged": "relic"},
        "Frost DPS": {"set": "plateDps", "role": "physical", "primary": "str", "weapons": ["42943", "44092"], "offhand": "none", "ranged": "relic"},
        "Unholy DPS": {"set": "plateDps", "role": "physical", "primary": "str", "weapons": ["42943", "44092"], "offhand": "none", "ranged": "relic"},
    },
    "Druid": {
        "Balance": {"set": "leatherCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095"], "offhand": "none", "ranged": "relic"},
        "Feral DPS": {"set": "leatherPhysical", "role": "physical", "primary": "agi", "weapons": ["48718"], "offhand": "none", "ranged": "relic"},
        "Feral Tank": {"set": "leatherPhysical", "role": "tank", "primary": "agi", "weapons": ["48718"], "offhand": "none", "ranged": "relic"},
        "Restoration": {"set": "leatherCaster", "role": "healer", "primary": "int", "weapons": ["42947", "44095", "42948"], "offhand": "none", "ranged": "relic"},
    },
    "Hunter": {
        "Beast Mastery": {"set": "mailPhysical", "role": "hunter", "primary": "agi", "weapons": [], "rangedItems": ["42946", "44093"], "offhand": "none", "ranged": "ranged"},
        "Marksmanship": {"set": "mailPhysical", "role": "hunter", "primary": "agi", "weapons": [], "rangedItems": ["42946", "44093"], "offhand": "none", "ranged": "ranged"},
        "Survival": {"set": "mailPhysical", "role": "hunter", "primary": "agi", "weapons": [], "rangedItems": ["42946", "44093"], "offhand": "none", "ranged": "ranged"},
    },
    "Mage": {
        "Arcane": {"set": "clothCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095"], "offhand": "held", "ranged": "wand"},
        "Fire": {"set": "clothCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095"], "offhand": "held", "ranged": "wand"},
        "Frost": {"set": "clothCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095"], "offhand": "held", "ranged": "wand"},
    },
    "Paladin": {
        "Holy": {"set": "plateHealer", "role": "healer", "primary": "int", "weapons": ["42948", "44094"], "offhand": "shield", "ranged": "relic"},
        "Protection": {"set": "plateTank", "role": "tank", "primary": "str", "weapons": ["42945", "44096"], "offhand": "shield", "ranged": "relic"},
        "Retribution": {"set": "plateDps", "role": "physical", "primary": "str", "weapons": ["44092"], "offhand": "none", "ranged": "relic"},
    },
    "Priest": {
        "Discipline": {"set": "clothCaster", "role": "healer", "primary": "int", "weapons": ["42947", "42948", "44094"], "offhand": "held", "ranged": "wand"},
        "Holy": {"set": "clothCaster", "role": "healer", "primary": "int", "weapons": ["42947", "42948", "44094"], "offhand": "held", "ranged": "wand"},
        "Shadow": {"set": "clothCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095", "42948"], "offhand": "held", "ranged": "wand"},
    },
    "Rogue": {
        "Assassination": {"set": "leatherPhysical", "role": "physical", "primary": "agi", "weapons": ["42944", "44091"], "offhand": "dual", "ranged": "thrown"},
        "Combat": {"set": "leatherPhysical", "role": "physical", "primary": "agi", "weapons": ["42945", "44096"], "offhand": "dual", "ranged": "thrown"},
        "Subtlety": {"set": "leatherPhysical", "role": "physical", "primary": "agi", "weapons": ["42944", "44091"], "offhand": "dual", "ranged": "thrown"},
    },
    "Shaman": {
        "Elemental": {"set": "mailCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095", "42948", "44094"], "offhand": "shield", "ranged": "relic"},
        "Enhancement": {"set": "mailPhysical", "role": "physical", "primary": "agi", "weapons": ["48716"], "offhand": "dual", "ranged": "relic"},
        "Restoration": {"set": "mailCaster", "role": "healer", "primary": "int", "weapons": ["42948", "44094", "42947"], "offhand": "shield", "ranged": "relic"},
    },
    "Warlock": {
        "Affliction": {"set": "clothCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095"], "offhand": "held", "ranged": "wand"},
        "Demonology": {"set": "clothCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095"], "offhand": "held", "ranged": "wand"},
        "Destruction": {"set": "clothCaster", "role": "caster", "primary": "int", "weapons": ["42947", "44095"], "offhand": "held", "ranged": "wand"},
    },
    "Warrior": {
        "Arms": {"set": "plateDps", "role": "physical", "primary": "str", "weapons": ["42943", "44092"], "offhand": "none", "ranged": "thrown"},
        "Fury": {"set": "plateDps", "role": "physical", "primary": "str", "weapons": ["42945", "44096"], "offhand": "dual", "ranged": "thrown"},
        "Protection": {"set": "plateTank", "role": "tank", "primary": "str", "weapons": ["42945", "44096"], "offhand": "shield", "ranged": "thrown"},
    },
}

class_order = ["Death Knight", "Druid", "Hunter", "Mage", "Paladin", "Priest", "Rogue", "Shaman", "Warlock", "Warrior"]

class_meta = {
    "Death Knight": {"min": 55, "color": "#c41e3a", "armor": "Placa", "weapons": "Espadas, hachas, mazas y lanzas"},
    "Druid": {"min": 1, "color": "#ff7c0a", "armor": "Cuero", "weapons": "Bastones, mazas a dos manos, lanzas y dagas"},
    "Hunter": {"min": 1, "color": "#aad372", "armor": "Malla al 40", "weapons": "Espadas, hachas, lanzas, arcos y armas de fuego"},
    "Mage": {"min": 1, "color": "#3fc7eb", "armor": "Tela", "weapons": "Bastones, espadas, dagas y varitas"},
    "Paladin": {"min": 1, "color": "#f48cba", "armor": "Placa al 40", "weapons": "Espadas, mazas y hachas, escudos"},
    "Priest": {"min": 1, "color": "#f0f0f0", "armor": "Tela", "weapons": "Bastones, mazas de una mano, dagas y varitas"},
    "Rogue": {"min": 1, "color": "#fff468", "armor": "Cuero", "weapons": "Dagas, espadas, mazas de una mano y armas de puño"},
    "Shaman": {"min": 1, "color": "#0070dd", "armor": "Malla al 40", "weapons": "Mazas, hachas de una mano, bastones, dagas y escudos"},
    "Warlock": {"min": 1, "color": "#8788ee", "armor": "Tela", "weapons": "Bastones, espadas, dagas y varitas"},
    "Warrior": {"min": 1, "color": "#c69b6d", "armor": "Placa al 40", "weapons": "Todas las armas cuerpo a cuerpo, arcos, armas de fuego y escudos"},
}

brackets = [
    {"min": 1, "max": 19, "name": "Aprendizaje", "advice": "No gastes oro en equipo: las misiones dan más que suficiente. Guarda las piezas con la estadística principal de tu especialización.", "dungeons": [["Ragefire Chasm", 13, 18], ["The Deadmines", 15, 20], ["Wailing Caverns", 15, 25]]},
    {"min": 20, "max": 39, "name": "Primeras mazmorras", "advice": "Empiezan las mazmorras. Haz cada una una vez por las recompensas y sigue subiendo; no farmees equipo que vas a reemplazar en pocos niveles.", "dungeons": [["Shadowfang Keep", 18, 25], ["Blackfathom Deeps", 20, 30], ["Gnomeregan", 24, 34], ["Razorfen Kraul", 25, 35], ["Scarlet Monastery", 26, 45], ["Razorfen Downs", 35, 45], ["Uldaman", 35, 45]]},
    {"min": 40, "max": 59, "name": "Especialización", "advice": "Se desbloquea la armadura superior: malla para cazadores y chamanes, placa para guerreros y paladines. Renueva las piezas cada 5 u 8 niveles.", "dungeons": [["Zul'Farrak", 44, 54], ["Maraudon", 45, 55], ["Temple of Atal'Hakkar", 50, 60], ["Blackrock Depths", 48, 60], ["Dire Maul", 55, 60], ["Stratholme", 58, 60], ["Scholomance", 58, 60]]},
    {"min": 60, "max": 69, "name": "Outland", "advice": "El equipo de misión de nivel 60 o más supera casi todo lo anterior. Coge las piezas azules que te salgan en mazmorras y no te quedes a farmear.", "dungeons": [["Hellfire Ramparts", 60, 62], ["The Blood Furnace", 61, 63], ["The Slave Pens", 62, 64], ["The Underbog", 63, 65], ["Mana-Tombs", 64, 66], ["Auchenai Crypts", 65, 67], ["Sethekk Halls", 67, 69], ["Old Hillsbrad Foothills", 66, 68], ["The Shattered Halls", 68, 70], ["The Steamvault", 68, 70], ["Shadow Labyrinth", 68, 70], ["The Botanica", 69, 72], ["The Mechanar", 69, 72], ["The Arcatraz", 70, 72], ["Magisters' Terrace", 70, 70]]},
    {"min": 70, "max": 79, "name": "Northrend", "advice": "El equipo de misión de nivel 70 o más es la base. Las mazmorras de Northrend dan las piezas que te faltan para llegar al 80 sin sufrir.", "dungeons": [["Utgarde Keep", 70, 72], ["The Nexus", 71, 73], ["Azjol-Nerub", 72, 74], ["Ahn'kahet", 73, 75], ["Drak'Tharon Keep", 74, 76], ["Violet Hold", 75, 77], ["Gundrak", 76, 78], ["Halls of Stone", 77, 79], ["Halls of Lightning", 78, 80], ["The Oculus", 78, 80], ["Culling of Stratholme", 78, 80]]},
    {"min": 80, "max": 80, "name": "Nivel máximo", "advice": "Ya no necesitas equipo de subida. A partir de aquí toca elegir el BiS de nivel 80 según tu especialización y la fase de contenido.", "dungeons": [["Trial of the Champion", 80, 80], ["Forge of Souls", 80, 80], ["Pit of Saron", 80, 80], ["Halls of Reflection", 80, 80], ["Icecrown Citadel", 80, 80]]},
]

stats = {
    "caster": ["Intelecto", "Poder de hechizos", "Golpe de hechizos", "Crítico", "Celeridad"],
    "healer": ["Intelecto", "Espíritu", "Poder de hechizos", "Celeridad", "Crítico"],
    "str": ["Fuerza", "Golpe", "Pericia", "Crítico", "Celeridad"],
    "agi": ["Agilidad", "Golpe", "Pericia", "Crítico", "Celeridad"],
    "tank": ["Aguante", "Defensa", "Esquiva", "Parada", "Golpe y pericia"],
    "bear": ["Aguante", "Agilidad", "Esquiva", "Pericia", "Golpe"],
    "hunter": ["Agilidad", "Golpe", "Crítico", "Poder de ataque", "Aguante"],
}

payload = {
    "heirlooms": heirlooms,
    "sets": sets,
    "specs": specs,
    "classOrder": class_order,
    "classMeta": class_meta,
    "brackets": brackets,
    "stats": stats,
}
