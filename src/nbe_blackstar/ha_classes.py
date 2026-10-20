import json
import re

from . import __version__, settings

ORIGIN = {
    "name": "nbe-blackstar",
    "sw_version": __version__,
    "support_url": "https://github.com/macokay/nbe-blackstar",
}


def strip_invalid(text):
    text = re.sub(r'[^A-Za-z0-9 ]+', '', text)
    return re.sub(r"\s+", '_', text).lower()


class Resource:
    def __init__(self, component, type, resource):
        self.component = component
        self.type = type
        self.resource = resource

    def getHaTopic(self):
        return settings.config["ha_prefix"] + "/" + self.type + "/" + self.component.device.getUid() + "/" + self.component.getUid() + "/config"


class Device:
    def __init__(self, identifiers, name, sw_version, model, manufacturer):
        self.identifiers = identifiers
        self.name = name
        self.sw_version = sw_version
        self.model = model
        self.manufacturer = manufacturer

    def getName(self):
        return self.name

    def getUid(self):
        # topic prefix follows the device id so existing installs keep their topics
        return self.identifiers

    def getId(self):
        return self.identifiers

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=5)


class Sensor:
    def __init__(self, icon, device_class, unit_of_measurement, state_class, name, device, object_id):
        if icon != "none":
            self.icon = icon
        if device_class != "none":
            self.device_class = device_class
        if unit_of_measurement != "none":
            self.unit_of_measurement = unit_of_measurement
        if state_class != "none":
            self.state_class = state_class
        self.name = name
        self.state_topic = device.getUid() + "/sensor/" + strip_invalid(name) + "/state"
        self.availability_topic = device.getUid() + "/bridge/state"
        self.unique_id = device.getId() + "_" + object_id
        self.default_entity_id = "sensor.nbe_" + object_id
        self.device = device
        self.origin = ORIGIN

    def getUid(self):
        return strip_invalid(self.name)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=8)


class BinarySensor:
    def __init__(self, icon, device_class, name, device, object_id):
        if icon != "none":
            self.icon = icon
        if device_class != "none":
            self.device_class = device_class
        self.name = name
        self.state_topic = device.getUid() + "/binary_sensor/" + strip_invalid(name) + "/state"
        self.availability_topic = device.getUid() + "/bridge/state"
        self.payload_on = "ON"
        self.payload_off = "OFF"
        self.unique_id = device.getId() + "_" + object_id
        self.default_entity_id = "binary_sensor.nbe_" + object_id
        self.device = device
        self.origin = ORIGIN

    def getUid(self):
        return strip_invalid(self.name)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=8)
