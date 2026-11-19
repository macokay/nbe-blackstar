import ipaddress
import re

from .const import STATE_NO_FUEL
from .reader import NON_NEGATIVE, NbeReader, as_number, clean_value

__all__ = ["NbeReader", "alarm_value", "as_number", "binary_value", "clean_value", "sensor_value", "validate_input"]


def binary_value(raw):
    return {"1": True, "0": False}.get(raw)


def alarm_value(raw, state):
    # off_on_alarm reads 1 while burning and 0 in standby. In the no-fuel alarm it reads neither
    # (seen 2026-10-30 and 2026-11-18), so the operating state 20 decides the alarm; any other
    # unexpected value stays unknown rather than raising a false alarm.
    if as_number(state) == STATE_NO_FUEL:
        return True
    if raw in ("0", "1"):
        return False
    return None


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

