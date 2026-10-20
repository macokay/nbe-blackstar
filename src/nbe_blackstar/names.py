# English entity names by OBJECT_ID. The schema file holds the Danish names, which stay the default.
EN = {
    "kedel_temperatur": "Boiler temperature",
    "kedel_maal": "Boiler target",
    "varmtvand": "Hot water",
    "varmtvand_maal": "Hot water target",
    "gulv_fremloeb": "Floor heating flow",
    "gulv_oensket": "Floor heating target",
    "skakt_temperatur": "Shaft temperature",
    "udetemperatur": "Outdoor temperature",
    "braendereffekt_kw": "Burner power",
    "braenderbelastning": "Burner load",
    "ilt": "Oxygen",
    "ilt_maal": "Oxygen target",
    "gulv_ventil": "Floor valve",
    "pellets_magasin": "Pellets in hopper",
    "askeskuffe_minutter": "Ash box minutes",
    "driftstilstand": "Operating state",
    "lysniveau": "Light level",
    "kedelpumpe": "Boiler pump",
    "gulvpumpe": "Floor pump",
    "alarm": "Alarm",
    "forbrug_teller": "Pellet consumption counter",
}


def display_name(object_id, schema_name, lang):
    return EN[object_id] if lang == "en" else schema_name
