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

import time
import sys
import paho.mqtt.client as paho
import ha_classes
import subprocess
import json
import settings
import random
import csv
import os
from protocol import Proxy

device = ha_classes.Device("nbe_kedel","NBE kedel","NBE Black Star 1016 (V7)","NBE Black Star 1016","NBE")
DataEntries = []

# controller reports 999.9 for sensors that are not connected
NOT_CONNECTED = 999.9
# resources that can never be negative (pellet count counts down and is not calibrated below zero)
NON_NEGATIVE = {"operating_data/content"}
# discovery topics published by the upstream build (device "nbeblackstar"); cleared with an empty retained payload
LEGACY_TOPICS = [
    "homeassistant/sensor/nbeblackstar/%s/config" % uid for uid in (
        "core", "core_target", "boiler_target", "boiler_temperature", "burned_total", "burning_power",
        "burning_power_kw", "floor_wanted", "floor_flowing", "floor_valve", "outside_clouds",
        "outside_temperature", "oxygen_level", "photo_sensor")
] + [
    "homeassistant/climate/nbeblackstar/%s/config" % uid for uid in ("core_temp_regulation", "water_regulation")
]

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

# read nbe schema file with declared device resources, group by specific device type and populate them in home assistant mqtt prefix topics
def configure_will(client):
    # retained offline if the process dies, so HA does not show stale values
    client.will_set(device.getUid()+"/bridge/state","offline",0,True)

def populate_resources(client):
    curr_path = os.path.dirname(os.path.realpath(__file__))
    fp = open(curr_path+'/nbe_schema')
    csv_reader = csv.reader(fp)
    for row in csv_reader:
        if row[0][0] != '#':  # skip comments
           # Column order for sensor
           # RESOURCE,METHOD,TYPE,NAME,ICON,STATE-CLASS,DEVICE-CLASS,UNIT-OF-MEASUREMENT,OBJECT_ID
           if row[1] == "get" and row[2] == "sensor":
              item = ha_classes.Sensor(row[4],row[6],row[7],row[5],row[3],device,row[8])
              DataEntries.append(ha_classes.Resource(item,row[2],row[0]))
           # Column order for binary sensor
           # RESOURCE,METHOD,TYPE,NAME,ICON,STATE-CLASS,DEVICE-CLASS,UNIT-OF-MEASUREMENT,OBJECT_ID
           if row[1] == "get" and row[2] == "binary_sensor":
              item = ha_classes.BinarySensor(row[4],row[6],row[3],device,row[8])
              DataEntries.append(ha_classes.Resource(item,row[2],row[0]))
           # Column order for climate control
           # RESOURCE,METHOD,TYPE,NAME,ICON,CURRENT-TEMP-TOPIC,MAX-TEMP
           if row[1] == "set" and row[2] == "climate":
              item = ha_classes.Climate(row[3],row[4],row[5],row[6],device)
              DataEntries.append(ha_classes.Resource(item,row[2],row[0]))
              client.subscribe(item.temperature_command_topic,0)
           # Column order for switch control
           # RESOURCE,METHOD,TYPE,NAME,ICON,... TO be continued...
           if row[1] == "set" and row[2] == "switch":
              item = ha_classes.Switch(row[4],row[3],device)
              DataEntries.append(ha_classes.Resource(item,row[2],row[0]))
              client.subscribe(item.command_topic,0)
    # cycle for entries and add them to mqtt
    for row in DataEntries:
        if settings.config["debug"]:
           print("Publishing: "+row.getHaTopic())
        client.publish(row.getHaTopic(),row.component.toJSON(),0,True)
    # remove entities from the upstream build so only the current ones remain in Home Assistant
    for topic in LEGACY_TOPICS:
        client.publish(topic,"",0,True)

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

def nbe_query():
    if settings.config["debug"]:
       print ("Making query to the pellet burner...")
    for attempt in (1, 2):
        items = {}
        try:
           proxy = get_proxy()
           for query in [ "operating_data", "settings/boiler", "settings/hot_water" ]:
              response = proxy.get(query)
              for item in response:
                 val = item.split("=",1)
                 items[val[0]] = val[1]
           return items
        except Exception as e:
           drop_proxy()
           print("Unable to query nbe (attempt %d): %s: %s" % (attempt, type(e).__name__, e))
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
       with Proxy(settings.config["nbe_pass"], settings.config["nbe_port"], settings.config["nbe_ip"], settings.config["nbe_serial"]) as proxy:
            for query in SLOW_QUERIES:
               for item in proxy.get(query):
                  key,val = item.split("=",1)
                  items[key] = val
    except Exception as e:
        print("Unable to query nbe consumption: %s: %s" % (type(e).__name__, e))
    return items

# raw pellet readings kept for calibration; one row per slow cycle (about 10 minutes)
TIMESERIES_FILE = os.environ.get("NBE_TIMESERIES_FILE", "/var/lib/nbe/timeseries.csv")

def log_timeseries(values):
    try:
        new_file = not os.path.exists(TIMESERIES_FILE)
        with open(TIMESERIES_FILE, "a") as f:
            if new_file:
                f.write("timestamp,content_raw,counter_raw\n")
            f.write("%s,%s,%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"),
                values.get("operating_data/content", ""), values.get("consumption_data/counter", "")))
    except OSError as e:
        print("Unable to write timeseries %s: %s" % (TIMESERIES_FILE, e))

def safe_refresh(client):
    # one bad cycle must not stop the bridge; the next cycle retries
    try:
        refresh_statuses(client)
        return True
    except Exception as e:
        print("Refresh cycle failed: %s: %s" % (type(e).__name__, e))
        return False

def nbe_update(command,value):
    try:
        with Proxy(settings.config["nbe_pass"], settings.config["nbe_port"], settings.config["nbe_ip"], settings.config["nbe_serial"]) as proxy:
           res = proxy.set(command,value)
           if settings.config["debug"]:
              print("NBE SET DEBUG RETURN: " + str(res))
           if str(res) == "('OK',)":
              return True
    except Exception as e:
        print("Unable to send update to the nbe controller: %s" % e)
    return False

HEARTBEAT_FILE = "/tmp/nbe-alive"

def touch_heartbeat():
    with open(HEARTBEAT_FILE, "w"):
        pass

def search_query(data,search):
    for Key,Value in data.items():
       if Key == search:
             return Key,Value
    return "none","none"

# refresh device's resources => values
def refresh_statuses(client):
    # make one big query to nbe to get all possible data
    global slow_cycles
    raw_data = nbe_query()
    state = "online" if raw_data else "offline"
    client.publish(device.getUid()+"/bridge/state",state,0,True)
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
    # parse and update only required data
    for row in DataEntries:
        if row.type == "climate":
           key,val = search_query(raw_data,row.resource)
           if key != "none" and val != "none":
              if settings.config["debug"]:
                 print("climate: "+row.component.temperature_state_topic+" with value: "+str(val))
              client.publish(row.component.temperature_state_topic,val,0,True)
        if row.type == "sensor":
           key,val = search_query(raw_data,row.resource)
           if key != "none" and val != "none":
              val = clean_value(val, nonnegative=row.resource in NON_NEGATIVE)
              if settings.config["debug"]:
                 print("sensor: "+row.component.state_topic+" with value: "+str(val))
              client.publish(row.component.state_topic,val,0,True)
        if row.type == "binary_sensor":
           key,val = search_query(raw_data,row.resource)
           if key != "none" and val != "none":
              client.publish(row.component.state_topic,binary_value(val),0,True)

# mqtt callback when connection success
def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True
        print("connected OK")
        # set availability when connected
        client.publish(device.getUid()+"/bridge/state","online",0,True)
        # a hacky trick to always show auto on thermostats (for now, just for eyes to be happy)
        client.publish(device.getUid()+"/bridge/static_auto_state","auto",0,True)
        # populate device resources
        populate_resources(client)
    else:
        print("Bad connection Returned code=",rc)
        client.bad_connection_flag=True


# mqtt callback for subscribed topics
def on_message(client, userdata, message):
    data = str(message.payload,'utf-8')
    if settings.config["debug"]:
       print("got message payload: " + data)
    for row in DataEntries:
        if row.type == "climate" and message.topic == row.getTempCommandTopic():
           if settings.config["debug"]:
              print ("Climate command triggered: "+ row.resource + " set data to: "+data)
           stat = nbe_update(row.resource,data)
           if stat == True:
              client.publish(row.getTempStateTopic(),data,0,True)
        if row.type == "switch" and message.topic == row.getCommandTopic():
           if settings.config["debug"]:
              print ("Triggered topic: "+ row.getCommandTopic())
           # DO SOME WORK WIT TEH DEV
           # set the status to the requested one
           client.publish(row.getStateTopic(),data,0,True)

# main function
def start():
    settings.init()
    # connection
    print("Started up!")
    paho.Client.connected_flag=False
    paho.Client.bad_connection_flag=False
    client= paho.Client()
    client.username_pw_set(settings.config["mqtt_user"],settings.config["mqtt_pass"])
    configure_will(client)
    client.on_connect=on_connect   #bind connect call back function
    client.on_message=on_message    #attach function to callback for subscriptions on the topics
    print("Connecting to broker ",settings.config["mqtt_server"])
    client.connect(settings.config["mqtt_server"],settings.config["mqtt_port"])	#establish connection
    client.loop_start() #start network loop
    while not client.connected_flag and not client.bad_connection_flag: #wait in loop
        time.sleep(0.1)
    if client.bad_connection_flag:
        client.loop_stop()    #Stop loop
        sys.exit()
    #the main loop starts here
    while True:
        try:
            # refresh device's resources to assigned topics
            safe_refresh(client)
            if settings.config["debug"]:
               print("still running")
            time.sleep(settings.config["refresh_rate"])
        except KeyboardInterrupt:
            print("Received kill signal, stopping the processes...")
            # set availability to offline
            client.publish(device.getUid()+"/bridge/state","offline",0,True)
            client.publish(device.getUid()+"/bridge/static_auto_state","off",0,True)
            client.loop_stop()
            client.disconnect()
            client.connected_flag=False
            print("Ending program")
            exit()

if __name__ == "__main__":
    start()
