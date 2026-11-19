from .reader import ENERGY_RESOURCE  # noqa: F401  (re-exported)

DOMAIN = "nbe_blackstar"

CONF_SERIAL = "serial"
CONF_PINCODE = "pincode"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_HOPPER_CAPACITY = "hopper_capacity_kg"
CONF_COUNTER_FACTOR = "counter_factor"

CONF_DEVICE_NAME = "device_name"
DEFAULT_DEVICE_NAME = "NBE Black Star"
DEFAULT_PORT = 8483
DEFAULT_SCAN_INTERVAL = 60

ENERGY_FILE = "nbe_blackstar_energy_{serial}.json"
HOPPER_STORE = "nbe_blackstar_hopper_{serial}"
HOPPER_SAVE_DELAY = 5
HOPPER_SAVE_EVERY = 600
COUNTER_RESOURCE = "consumption_data/counter"
STATE_RESOURCE = "operating_data/state"
# operating state 20 = no-fuel alarm ("ALARM INGEN ILD - BRÆNDSEL?")
STATE_NO_FUEL = 20

# (resource, type, object_id, name, icon, state_class, device_class, unit); mirrors src/nbe_blackstar/nbe_schema
ENTITIES = (
    ("operating_data/boiler_temp", "sensor", "boiler_temperature", "Boiler temperature", "none", "measurement", "temperature", "°C"),
    ("operating_data/boiler_ref", "sensor", "boiler_target", "Boiler target", "none", "measurement", "temperature", "°C"),
    ("operating_data/dhw_temp", "sensor", "hot_water", "Hot water", "mdi:water-boiler", "measurement", "temperature", "°C"),
    ("operating_data/dhw_ref", "sensor", "hot_water_target", "Hot water target", "mdi:water-boiler", "measurement", "temperature", "°C"),
    ("operating_data/forward_temp", "sensor", "floor_heating_flow", "Floor heating flow", "mdi:heating-coil", "measurement", "temperature", "°C"),
    ("operating_data/forward_ref", "sensor", "floor_heating_target", "Floor heating target", "mdi:heating-coil", "measurement", "temperature", "°C"),
    ("operating_data/shaft_temp", "sensor", "shaft_temperature", "Shaft temperature", "none", "measurement", "temperature", "°C"),
    ("operating_data/return_temp", "sensor", "return_temperature", "Return temperature", "none", "measurement", "temperature", "°C"),
    ("operating_data/smoke_temp", "sensor", "flue_gas_temperature", "Flue gas temperature", "none", "measurement", "temperature", "°C"),
    ("operating_data/milli_ampere", "sensor", "current_draw", "Current draw", "mdi:current-ac", "measurement", "current", "mA"),
    ("operating_data/external_temp", "sensor", "outdoor_temperature", "Outdoor temperature", "none", "measurement", "temperature", "°C"),
    ("operating_data/power_kw", "sensor", "burner_power", "Burner power", "mdi:flash", "measurement", "power", "kW"),
    ("operating_data/power_pct", "sensor", "burner_load", "Burner load", "mdi:percent", "measurement", "none", "%"),
    ("operating_data/oxygen", "sensor", "oxygen", "Oxygen", "mdi:percent", "measurement", "none", "%"),
    ("operating_data/oxygen_ref", "sensor", "oxygen_target", "Oxygen target", "mdi:percent", "measurement", "none", "%"),
    ("operating_data/house_valve_state", "sensor", "floor_valve", "Floor valve", "mdi:heating-coil", "measurement", "none", "%"),
    ("operating_data/content", "sensor", "pellets_in_hopper", "Pellets in hopper", "mdi:weight-kilogram", "measurement", "none", "kg"),
    ("operating_data/ashbox_minutes", "sensor", "ash_box_minutes", "Ash box minutes", "mdi:timer-outline", "measurement", "duration", "min"),
    ("operating_data/state", "sensor", "operating_state", "Operating state", "mdi:fire", "measurement", "none", "none"),
    ("operating_data/photo_level", "sensor", "light_level", "Light level", "mdi:brightness-6", "measurement", "none", "%"),
    ("operating_data/boiler_pump_state", "binary_sensor", "boiler_pump", "Boiler pump", "mdi:pump", "none", "running", "none"),
    ("operating_data/house_pump_state", "binary_sensor", "floor_pump", "Floor pump", "mdi:pump", "none", "running", "none"),
    ("operating_data/off_on_alarm", "binary_sensor", "alarm", "Alarm", "mdi:alert", "none", "none", "none"),
    ("consumption_data/counter", "sensor", "pellet_consumption_counter", "Pellet consumption counter", "mdi:counter", "total_increasing", "weight", "kg"),
    ("energy/burner_kwh", "sensor", "burner_energy", "Burner energy", "mdi:lightning-bolt", "total_increasing", "energy", "kWh"),
)

# Danish object ids from versions up to 0.0.13 -> the English ids. unique_id and the default entity id follow the object id,
# so setup renames existing registry entries (see _migrate_object_ids in __init__.py).
LEGACY_OBJECT_IDS = {
    "kedel_temperatur": "boiler_temperature",
    "kedel_maal": "boiler_target",
    "varmtvand": "hot_water",
    "varmtvand_maal": "hot_water_target",
    "gulv_fremloeb": "floor_heating_flow",
    "gulv_oensket": "floor_heating_target",
    "skakt_temperatur": "shaft_temperature",
    "retur_temperatur": "return_temperature",
    "rog_temperatur": "flue_gas_temperature",
    "stromforbrug_ma": "current_draw",
    "udetemperatur": "outdoor_temperature",
    "braendereffekt_kw": "burner_power",
    "braenderbelastning": "burner_load",
    "ilt": "oxygen",
    "ilt_maal": "oxygen_target",
    "gulv_ventil": "floor_valve",
    "pellets_magasin": "pellets_in_hopper",
    "askeskuffe_minutter": "ash_box_minutes",
    "driftstilstand": "operating_state",
    "lysniveau": "light_level",
    "kedelpumpe": "boiler_pump",
    "gulvpumpe": "floor_pump",
    "forbrug_teller": "pellet_consumption_counter",
    "braender_energi_kwh": "burner_energy",
    "pellets_tilbage": "pellets_left",
    "dage_tilbage": "days_left",
    "fyld_snart_paa": "refill_soon",
    "kalibrer_silo_niveau": "calibrate_silo_level",
    "paafyldt_kg": "refill_amount",
    "registrer_paafyldning": "register_refill",
}
