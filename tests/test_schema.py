import csv
import os

SCHEMA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "nbe_blackstar", "nbe_schema")


def _rows():
    with open(SCHEMA) as fp:
        return [row for row in csv.reader(fp) if row and not row[0].startswith("#")]


def test_schema_has_no_write_rows():
    writes = [row[0] for row in _rows() if row[1] == "set"]
    assert writes == [], "read-only build must not declare writable resources: %s" % writes


def test_schema_still_has_sensors():
    sensors = [row for row in _rows() if row[1] == "get" and row[2] == "sensor"]
    assert len(sensors) > 0
