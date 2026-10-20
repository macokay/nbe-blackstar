import ipaddress
import logging
import re
import time

from .const import (
    ENERGY_RESOURCE,
    FAST_QUERIES,
    NON_NEGATIVE,
    NOT_CONNECTED,
    POWER_RESOURCE,
    SLOW_EVERY,
    SLOW_QUERIES,
)
from .energy import EnergyMeter
from .protocol import Proxy

log = logging.getLogger(__name__)


def clean_value(raw, nonnegative=False):
    try:
        value = float(raw)
    except ValueError:
        return raw
    if abs(value - NOT_CONNECTED) < 1e-6 or (nonnegative and value < 0):
        return ""
    return raw


def as_number(raw):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return None if abs(value - NOT_CONNECTED) < 1e-6 else value


def binary_value(raw):
    return {"1": True, "0": False}.get(raw)


def sensor_value(resource, raw):
    cleaned = clean_value(raw, nonnegative=resource in NON_NEGATIVE)
    if cleaned == "":
        return None
    number = as_number(cleaned)
    return cleaned if number is None else number


def validate_input(host, serial, pincode, port):
    errors = {}
    try:
        ipaddress.ip_address(host)
    except ValueError:
        errors["host"] = "invalid_ip"
    if not re.fullmatch(r"\d{1,6}", serial or ""):
        errors["serial"] = "invalid_serial"
    if not re.fullmatch(r"\d{1,10}", pincode or ""):
        errors["pincode"] = "invalid_pincode"
    if not isinstance(port, int) or not 1 <= port <= 65535:
        errors["port"] = "invalid_port"
    return errors


class NbeReader:
    def __init__(self, ip, serial, pincode, port, energy_path=None, proxy_factory=Proxy, clock=time.time):
        self._args = (pincode, port, ip, serial)
        self._factory = proxy_factory
        self._clock = clock
        self._proxy = None
        self._cycles = 0
        self._slow = {}
        self.meter = EnergyMeter(energy_path)

    def _get_proxy(self):
        if self._proxy is None:
            self._proxy = self._factory(*self._args)
        return self._proxy

    def close(self):
        try:
            self.meter.flush()
        except Exception:
            log.warning("Unable to flush energy total", exc_info=True)
        if self._proxy is not None:
            try:
                self._proxy.s.close()
            except Exception:
                pass
        self._proxy = None

    def _query(self, queries):
        items = {}
        proxy = self._get_proxy()
        for query in queries:
            for item in proxy.get(query):
                key, val = item.split("=", 1)
                items[key] = val
        return items

    def read_firmware(self):
        # sw_versions lists newest first: "<date>,<version>,<flag>"
        try:
            return self._get_proxy().get("sw_versions")[0].split(",")[1]
        except Exception as e:
            log.warning("Unable to read controller firmware version: %s", type(e).__name__)
            self.close()
            return None

    def poll(self):
        try:
            raw = self._query(FAST_QUERIES)
        except Exception:
            self.close()
            raise
        if not raw:
            raise ConnectionError("controller returned no data")
        if self._cycles % SLOW_EVERY == 0:
            self._slow = {}
            try:
                self._slow = self._query(SLOW_QUERIES)
            except Exception as e:
                self.close()
                log.warning("Unable to query controller counters: %s", type(e).__name__)
        self._cycles += 1
        raw.update(self._slow)
        kwh = self.meter.update(as_number(raw.get(POWER_RESOURCE)), self._clock())
        raw[ENERGY_RESOURCE] = "%.3f" % kwh
        return raw
