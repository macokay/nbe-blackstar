import os
import json

# Secrets never live in a file; they come from the environment and must be set.
SECRET_ENV = {"nbe_pass": "NBE_PASS", "mqtt_pass": "MQTT_PASS"}

# Non-secret settings: config key -> (environment variable, converter, default). Default None means required.
ENV_SETTINGS = {
    "nbe_serial": ("NBE_SERIAL", str, None),
    "nbe_ip": ("NBE_IP", str, None),
    "nbe_port": ("NBE_PORT", int, 8483),
    "mqtt_server": ("MQTT_IP", str, None),
    "mqtt_port": ("MQTT_PORT", int, 1883),
    "mqtt_user": ("MQTT_USER", str, ""),
    "mqtt_client_name": ("MQTT_CLIENT_NAME", str, "nbe-blackstar"),
    "refresh_rate": ("REFRESH_RATE", int, 60),
    "debug": ("NBE_DEBUG", lambda v: v.lower() in ("1", "true", "yes"), False),
    "ha_prefix": ("HA_PREFIX", str, "homeassistant"),
    "device_id": ("NBE_DEVICE_ID", str, ""),
    "device_name": ("NBE_DEVICE_NAME", str, "NBE Black Star"),
}


def load(config_file, environ):
    config = {}
    if os.path.exists(config_file):
        with open(config_file) as f:
            config = json.load(f)
    leaked = [key for key in SECRET_ENV if key in config]
    if leaked:
        raise SystemExit("Secrets in config file are not allowed (%s), use env vars" % ", ".join(leaked))
    for key, env in SECRET_ENV.items():
        value = environ.get(env)
        if not value:
            raise SystemExit("%s environment variable is required" % env)
        config[key] = value
    for key, (env, convert, default) in ENV_SETTINGS.items():
        if env in environ:
            config[key] = convert(environ[env])
        elif key not in config:
            if default is None:
                raise SystemExit("%s environment variable is required" % env)
            config[key] = default
    if not config.get("device_id"):
        config["device_id"] = "nbe_" + str(config["nbe_serial"])
    return config


def init():
    global config
    curr_path = os.path.dirname(os.path.realpath(__file__))
    config = load(os.path.join(curr_path, "config.json"), os.environ)
