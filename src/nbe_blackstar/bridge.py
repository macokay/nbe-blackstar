#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
    Copyright (C) 2021-2022 e1z0 https://github.com/e1z0
    NBE Protocol reverse engineering and python adaptation - Copyright (C) 2013 Anders Nylund

    Redistribution and use in source and binary forms,
    with or without modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the
       above copyright notice, this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its contributors
       may be used to endorse or promote products derived from this software
       without specific prior written permission.

      THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS
      OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
      AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
      CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
      DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
      DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
      IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
      OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import csv
import logging
import os
import time

import paho.mqtt.client as paho

from . import ha_classes, settings
from .energy import EnergyMeter
from .names import display_name
from .protocol import Proxy

log = logging.getLogger("nbe_blackstar")

# until the configuration is loaded the device uses the Black Star default; start() replaces it
device = ha_classes.Device("nbe_kedel", "NBE Black Star", "unknown", "Black Star 1016 (V7)", "NBE")
DataEntries = []

# controller reports 999.9 for sensors that are not connected
NOT_CONNECTED = 999.9
# resources that can never be negative (pellet count counts down and is not calibrated below zero)
NON_NEGATIVE = {"operating_data/content"}


def clean_value(raw, nonnegative=False):
    try:
        value = float(raw)
    except ValueError:
        return raw
    if abs(value - NOT_CONNECTED) < 1e-6 or (nonnegative and value < 0):
        return ""
    return raw


def binary_value(raw):
    return {"1": "ON", "0": "OFF"}.get(raw, "")


def configure_will(client):
    # retained offline if the process dies, so HA does not show stale values
    client.will_set(device.getUid() + "/bridge/state", "offline", 0, True)


def make_device(config):
    return ha_classes.Device(config["device_id"], config["device_name"], "unknown", "Black Star 1016 (V7)", "NBE")


def populate_resources(client):
    # schema columns: RESOURCE,METHOD,TYPE,NAME,ICON,STATE-CLASS,DEVICE-CLASS,UNIT,OBJECT_ID
    curr_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(curr_path, "nbe_schema")) as fp:
        for row in csv.reader(fp):
            if not row or row[0].startswith("#"):
                continue
            # topics stay keyed on the schema (Danish) name so switching language never moves an entity
            key = ha_classes.strip_invalid(row[3])
            name = display_name(row[8], row[3], settings.config["lang"])
            if row[1] == "get" and row[2] == "sensor":
                item = ha_classes.Sensor(row[4], row[6], row[7], row[5], name, device, row[8], key)
                DataEntries.append(ha_classes.Resource(item, row[2], row[0]))
            if row[1] == "get" and row[2] == "binary_sensor":
                item = ha_classes.BinarySensor(row[4], row[6], name, device, row[8], key)
                DataEntries.append(ha_classes.Resource(item, row[2], row[0]))
    for row in DataEntries:
        log.debug("Publishing discovery: %s", row.getHaTopic())
        client.publish(row.getHaTopic(), row.component.toJSON(), 0, True)


_proxy = None


def get_proxy():
    global _proxy
    if _proxy is None:
        _proxy = Proxy(settings.config["nbe_pass"], settings.config["nbe_port"], settings.config["nbe_ip"], settings.config["nbe_serial"])
    return _proxy


def drop_proxy():
    global _proxy
    if _proxy is not None:
        try:
            _proxy.s.close()
        except Exception:
            pass
    _proxy = None


def fetch_sw_version():
    # sw_versions lists newest first: "<date>,<version>,<flag>"
    try:
        first = get_proxy().get("sw_versions")[0]
        return first.split(",")[1]
    except Exception as e:
        log.warning("Unable to read controller firmware version: %s: %s", type(e).__name__, e)
        drop_proxy()
        return None


def nbe_query():
    log.debug("Querying controller")
    for attempt in (1, 2):
        items = {}
        try:
            proxy = get_proxy()
            for query in ["operating_data", "settings/boiler", "settings/hot_water"]:
                for item in proxy.get(query):
                    key, val = item.split("=", 1)
                    items[key] = val
            return items
        except Exception as e:
            drop_proxy()
            log.warning("Unable to query controller (attempt %d): %s: %s", attempt, type(e).__name__, e)
            if attempt == 1:
                time.sleep(2)
    return {}


# slow-changing counters, read every SLOW_EVERY refresh cycles (about 10 minutes at the default rate)
SLOW_QUERIES = ["consumption_data/counter"]
SLOW_EVERY = 10
slow_cache = {}
slow_cycles = 0


def nbe_query_slow():
    items = {}
    try:
        proxy = get_proxy()
        for query in SLOW_QUERIES:
            for item in proxy.get(query):
                key, val = item.split("=", 1)
                items[key] = val
    except Exception as e:
        drop_proxy()
        log.warning("Unable to query controller counters: %s: %s", type(e).__name__, e)
    return items


# raw pellet readings kept for calibration; one row per slow cycle (about 10 minutes)
TIMESERIES_FILE = os.environ.get("NBE_TIMESERIES_FILE", "/var/lib/nbe/timeseries.csv")
ENERGY_FILE = os.environ.get("NBE_ENERGY_FILE", "/var/lib/nbe/energy.json")
energy_meter = EnergyMeter(None)


def as_number(raw):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return None if abs(value - NOT_CONNECTED) < 1e-6 else value


def log_timeseries(values):
    try:
        new_file = not os.path.exists(TIMESERIES_FILE)
        with open(TIMESERIES_FILE, "a") as f:
            if new_file:
                f.write("timestamp,content_raw,counter_raw\n")
            f.write("%s,%s,%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"),
                values.get("operating_data/content", ""), values.get("consumption_data/counter", "")))
    except OSError as e:
        log.warning("Unable to write timeseries %s: %s", TIMESERIES_FILE, e)


def safe_refresh(client):
    # one bad cycle must not stop the bridge; the next cycle retries
    try:
        refresh_statuses(client)
        return True
    except Exception as e:
        log.error("Refresh cycle failed: %s: %s", type(e).__name__, e)
        return False


HEARTBEAT_FILE = "/tmp/nbe-alive"


def touch_heartbeat():
    with open(HEARTBEAT_FILE, "w"):
        pass


def search_query(data, search):
    for key, value in data.items():
        if key == search:
            return key, value
    return "none", "none"


def refresh_statuses(client):
    global slow_cycles
    raw_data = nbe_query()
    state = "online" if raw_data else "offline"
    client.publish(device.getUid() + "/bridge/state", state, 0, True)
    if not raw_data:
        return
    touch_heartbeat()
    slow_cycles += 1
    if slow_cycles >= SLOW_EVERY:
        slow_cycles = 0
        slow_cache.clear()
        slow_cache.update(nbe_query_slow())
        log_timeseries(dict(raw_data, **slow_cache))
    raw_data = dict(raw_data)
    raw_data.update(slow_cache)
    kwh = energy_meter.update(as_number(raw_data.get("operating_data/power_kw")), time.time())
    raw_data["energy/burner_kwh"] = "%.3f" % kwh
    for row in DataEntries:
        key, val = search_query(raw_data, row.resource)
        if key == "none" or val == "none":
            continue
        if row.type == "sensor":
            val = clean_value(val, nonnegative=row.resource in NON_NEGATIVE)
            client.publish(row.component.state_topic, val, 0, True)
        elif row.type == "binary_sensor":
            client.publish(row.component.state_topic, binary_value(val), 0, True)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        log.error("Broker refused connection: %s", reason_code)
        client.bad_connection_flag = True
        return
    log.info("Connected to MQTT broker")
    client.connected_flag = True
    client.publish(device.getUid() + "/bridge/state", "online", 0, True)
    firmware = fetch_sw_version()
    if firmware:
        device.sw_version = firmware
    populate_resources(client)


def shutdown(client):
    log.info("Stopping")
    energy_meter.flush()
    client.publish(device.getUid() + "/bridge/state", "offline", 0, True)
    client.loop_stop()
    client.disconnect()
    return 0


def start():
    settings.init()
    global device
    device = make_device(settings.config)
    logging.basicConfig(level=logging.DEBUG if settings.config["debug"] else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    global energy_meter
    energy_meter = EnergyMeter(ENERGY_FILE)
    log.info("Starting NBE Black Star bridge for %s", device.getId())

    client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=settings.config["mqtt_client_name"])
    client.connected_flag = False
    client.bad_connection_flag = False
    client.username_pw_set(settings.config["mqtt_user"], settings.config["mqtt_pass"])
    configure_will(client)
    client.on_connect = on_connect
    log.info("Connecting to broker %s", settings.config["mqtt_server"])
    client.connect(settings.config["mqtt_server"], settings.config["mqtt_port"])
    client.loop_start()
    while not client.connected_flag and not client.bad_connection_flag:
        time.sleep(0.1)
    if client.bad_connection_flag:
        client.loop_stop()
        return 1
    try:
        while True:
            safe_refresh(client)
            log.debug("Cycle done")
            time.sleep(settings.config["refresh_rate"])
    except KeyboardInterrupt:
        return shutdown(client)
