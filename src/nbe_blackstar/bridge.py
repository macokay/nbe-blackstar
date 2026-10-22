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
import signal
import time

import paho.mqtt.client as paho

from . import ha_classes, settings
from .names import display_name
from .protocol import Proxy
from .reader import NON_NEGATIVE, NbeReader, clean_value

log = logging.getLogger("nbe_blackstar")

# until the configuration is loaded the device uses the Black Star default; start() replaces it
device = ha_classes.Device("nbe_kedel", "NBE Black Star", "unknown", "Black Star 1016 (V7)", "Mac O Kay")
DataEntries = []


def binary_value(raw):
    return {"1": "ON", "0": "OFF"}.get(raw, "")


def configure_will(client):
    # retained offline if the process dies, so HA does not show stale values
    client.will_set(device.getUid() + "/bridge/state", "offline", 0, True)


def make_device(config):
    return ha_classes.Device(config["device_id"], config["device_name"], "unknown", "Black Star 1016 (V7)", "Mac O Kay")


def populate_resources(client):
    # schema columns: RESOURCE,METHOD,TYPE,NAME,ICON,STATE-CLASS,DEVICE-CLASS,UNIT,OBJECT_ID
    DataEntries.clear()  # discovery is republished on reconnect and on a late firmware read
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


# raw pellet readings kept for calibration; one row per slow cycle (about 10 minutes)
TIMESERIES_FILE = os.environ.get("NBE_TIMESERIES_FILE", "/var/lib/nbe/timeseries.csv")
ENERGY_FILE = os.environ.get("NBE_ENERGY_FILE", "/var/lib/nbe/energy.json")

_reader = None


def get_reader():
    global _reader
    if _reader is None:
        c = settings.config
        _reader = NbeReader(c["nbe_ip"], c["nbe_serial"], c["nbe_pass"], c["nbe_port"], ENERGY_FILE, proxy_factory=Proxy)
    return _reader


def fetch_sw_version():
    return get_reader().read_firmware()


def nbe_query():
    log.debug("Querying controller")
    for attempt in (1, 2):
        try:
            return get_reader().poll()
        except Exception as e:
            log.warning("Unable to query controller (attempt %d): %s: %s", attempt, type(e).__name__, e)
            if attempt == 1:
                time.sleep(2)
    return {}


def slow_refreshed():
    return _reader is not None and _reader.slow_refreshed


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


OFFLINE_AFTER_FAILED_CYCLES = 3
_failed_cycles = 0


def refresh_statuses(client):
    global _failed_cycles
    raw_data = nbe_query()
    if not raw_data:
        # a single missed cycle must not flip availability; Home Assistant re-applies stale states on return
        _failed_cycles += 1
        if _failed_cycles == OFFLINE_AFTER_FAILED_CYCLES:
            client.publish(device.getUid() + "/bridge/state", "offline", 0, True)
        return
    _failed_cycles = 0
    client.publish(device.getUid() + "/bridge/state", "online", 0, True)
    touch_heartbeat()
    if device.sw_version == "unknown":
        firmware = fetch_sw_version()
        if firmware:
            device.sw_version = firmware
            populate_resources(client)
    if slow_refreshed():
        log_timeseries(raw_data)
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
    if _reader is not None:
        _reader.close()
    client.publish(device.getUid() + "/bridge/state", "offline", 0, True)
    client.loop_stop()
    client.disconnect()
    return 0


def install_sigterm_handler():
    # Docker and systemd stop with SIGTERM; route it through the KeyboardInterrupt path so shutdown() runs
    def handler(signum, frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, handler)
    return lambda: signal.signal(signal.SIGTERM, previous)


def start():
    settings.init()
    global device
    device = make_device(settings.config)
    logging.basicConfig(level=logging.DEBUG if settings.config["debug"] else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    get_reader()
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
    restore_sigterm = install_sigterm_handler()
    try:
        while True:
            safe_refresh(client)
            log.debug("Cycle done")
            time.sleep(settings.config["refresh_rate"])
    except KeyboardInterrupt:
        return shutdown(client)
    finally:
        restore_sigterm()
