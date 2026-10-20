import os
import json

# Secrets never live in config.json; they come from the environment and must be set.
SECRET_ENV = {"nbe_pass": "NBE_PASS", "mqtt_pass": "MQTT_PASS"}

def load(config_file, environ):
    if not os.path.exists(config_file):
        raise SystemExit("Settings file " + config_file + " does not exist!")
    with open(config_file) as f:
        config = json.load(f)
    leaked = [key for key in SECRET_ENV if key in config]
    if leaked:
        raise SystemExit("Secrets in config.json are not allowed (%s), use env vars" % ", ".join(leaked))
    for key, env in SECRET_ENV.items():
        value = environ.get(env)
        if not value:
            raise SystemExit("%s environment variable is required" % env)
        config[key] = value
    return config

def init():
    global config
    curr_path = os.path.dirname(os.path.realpath(__file__))
    config = load(curr_path + "/config.json", os.environ)
