from .reader import ENERGY_RESOURCE  # noqa: F401  (re-exported)

DOMAIN = "nbe_blackstar"

CONF_SERIAL = "serial"
CONF_PINCODE = "pincode"
CONF_PORT = "port"
CONF_LANG = "lang"
CONF_SCAN_INTERVAL = "scan_interval"

CONF_DEVICE_NAME = "device_name"
DEFAULT_DEVICE_NAME = "NBE Black Star"
DEFAULT_PORT = 8483
DEFAULT_LANG = "da"
DEFAULT_SCAN_INTERVAL = 60
LANGS = ("da", "en")

ENERGY_FILE = "nbe_blackstar_energy_{serial}.json"

# (resource, type, object_id, name_da, name_en, icon, state_class, device_class, unit); mirrors src/nbe_blackstar/nbe_schema
ENTITIES = (
    ("operating_data/boiler_temp", "sensor", "kedel_temperatur", "Kedeltemperatur", "Boiler temperature", "none", "measurement", "temperature", "°C"),
    ("operating_data/boiler_ref", "sensor", "kedel_maal", "Kedel mål", "Boiler target", "none", "measurement", "temperature", "°C"),
    ("operating_data/dhw_temp", "sensor", "varmtvand", "Varmtvand", "Hot water", "mdi:water-boiler", "measurement", "temperature", "°C"),
    ("operating_data/dhw_ref", "sensor", "varmtvand_maal", "Varmtvand mål", "Hot water target", "mdi:water-boiler", "measurement", "temperature", "°C"),
    ("operating_data/forward_temp", "sensor", "gulv_fremloeb", "Gulvvarme fremløb", "Floor heating flow", "mdi:heating-coil", "measurement", "temperature", "°C"),
    ("operating_data/forward_ref", "sensor", "gulv_oensket", "Gulvvarme ønsket", "Floor heating target", "mdi:heating-coil", "measurement", "temperature", "°C"),
    ("operating_data/shaft_temp", "sensor", "skakt_temperatur", "Skakttemperatur", "Shaft temperature", "none", "measurement", "temperature", "°C"),
    ("operating_data/external_temp", "sensor", "udetemperatur", "Udetemperatur", "Outdoor temperature", "none", "measurement", "temperature", "°C"),
    ("operating_data/power_kw", "sensor", "braendereffekt_kw", "Brændereffekt", "Burner power", "mdi:flash", "measurement", "power", "kW"),
    ("operating_data/power_pct", "sensor", "braenderbelastning", "Brænderbelastning", "Burner load", "mdi:percent", "measurement", "none", "%"),
    ("operating_data/oxygen", "sensor", "ilt", "Ilt", "Oxygen", "mdi:percent", "measurement", "none", "%"),
    ("operating_data/oxygen_ref", "sensor", "ilt_maal", "Ilt mål", "Oxygen target", "mdi:percent", "measurement", "none", "%"),
    ("operating_data/house_valve_state", "sensor", "gulv_ventil", "Gulvventil", "Floor valve", "mdi:heating-coil", "measurement", "none", "%"),
    ("operating_data/content", "sensor", "pellets_magasin", "Pellets i magasin", "Pellets in hopper", "mdi:weight-kilogram", "measurement", "none", "kg"),
    ("operating_data/ashbox_minutes", "sensor", "askeskuffe_minutter", "Askeskuffe minutter", "Ash box minutes", "mdi:timer-outline", "measurement", "duration", "min"),
    ("operating_data/state", "sensor", "driftstilstand", "Driftstilstand", "Operating state", "mdi:fire", "measurement", "none", "none"),
    ("operating_data/photo_level", "sensor", "lysniveau", "Lysniveau", "Light level", "mdi:brightness-6", "measurement", "none", "%"),
    ("operating_data/boiler_pump_state", "binary_sensor", "kedelpumpe", "Kedelpumpe", "Boiler pump", "mdi:pump", "none", "running", "none"),
    ("operating_data/house_pump_state", "binary_sensor", "gulvpumpe", "Gulvpumpe", "Floor pump", "mdi:pump", "none", "running", "none"),
    ("operating_data/off_on_alarm", "binary_sensor", "alarm", "Alarm", "Alarm", "mdi:alert", "none", "problem", "none"),
    ("consumption_data/counter", "sensor", "forbrug_teller", "Pellet forbrug teller", "Pellet consumption counter", "mdi:counter", "total_increasing", "none", "none"),
    ("energy/burner_kwh", "sensor", "braender_energi_kwh", "Brænderenergi", "Burner energy", "mdi:lightning-bolt", "total_increasing", "energy", "kWh"),
)
