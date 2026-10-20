import ast
import csv
import json
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENT = os.path.join(ROOT, "custom_components", "nbe_blackstar")

# register the package without running its __init__, which needs Home Assistant
_parent = types.ModuleType("custom_components")
_parent.__path__ = [os.path.join(ROOT, "custom_components")]
_package = types.ModuleType("custom_components.nbe_blackstar")
_package.__path__ = [COMPONENT]
sys.modules.setdefault("custom_components", _parent)
sys.modules.setdefault("custom_components.nbe_blackstar", _package)

from custom_components.nbe_blackstar import api, const  # noqa: E402
from custom_components.nbe_blackstar.api import NbeReader  # noqa: E402
from custom_components.nbe_blackstar.protocol import Proxy  # noqa: E402


class FakeSocket:
    closed = False

    def close(self):
        self.closed = True


class FakeProxy:
    instances = []
    responses = {}
    fail = False

    def __init__(self, password, port, addr, serial):
        self.args = (password, port, addr, serial)
        self.s = FakeSocket()
        self.calls = []
        FakeProxy.instances.append(self)

    def get(self, query):
        self.calls.append(query)
        if FakeProxy.fail:
            raise TimeoutError("controller did not answer")
        return FakeProxy.responses[query]


@pytest.fixture(autouse=True)
def fake_controller():
    FakeProxy.instances = []
    FakeProxy.fail = False
    FakeProxy.responses = {
        "operating_data": [
            "operating_data/boiler_temp=65.2",
            "operating_data/external_temp=999.9",
            "operating_data/power_kw=6.0",
            "operating_data/content=-3",
            "operating_data/boiler_pump_state=1",
            "operating_data/state=5",
        ],
        "settings/boiler": ["settings/boiler/temp=70"],
        "settings/hot_water": ["settings/hot_water/temp=55"],
        "consumption_data/counter": ["consumption_data/counter=1234"],
        "sw_versions": ["20240101,1.2.3,0", "20230101,1.0.0,0"],
    }


def make_reader(tmp_path=None, clock=lambda: 0):
    path = str(tmp_path / "energy.json") if tmp_path else None
    return NbeReader("192.0.2.10", "123456", "123456", 8483, path, proxy_factory=FakeProxy, clock=clock)


def test_validate_input_accepts_placeholders():
    assert api.validate_input("192.0.2.10", "123456", "123456", 8483) == {}


@pytest.mark.parametrize(
    "args,field",
    [
        (("not-an-ip", "123456", "123456", 8483), "host"),
        (("192.0.2.10", "abc", "123456", 8483), "serial"),
        (("192.0.2.10", "1234567", "123456", 8483), "serial"),
        (("192.0.2.10", "123456", "", 8483), "pincode"),
        (("192.0.2.10", "123456", "12345678901", 8483), "pincode"),
        (("192.0.2.10", "123456", "123456", 0), "port"),
        (("192.0.2.10", "123456", "123456", 70000), "port"),
    ],
)
def test_validate_input_rejects(args, field):
    assert field in api.validate_input(*args)


def test_not_connected_999_9_is_unknown_never_the_number():
    data = make_reader().poll()
    assert data["operating_data/external_temp"] == "999.9"
    assert api.sensor_value("operating_data/external_temp", "999.9") is None
    assert api.sensor_value("operating_data/boiler_temp", data["operating_data/boiler_temp"]) == 65.2


def test_negative_pellet_content_is_unknown():
    assert api.sensor_value("operating_data/content", "-3") is None
    assert api.sensor_value("operating_data/boiler_temp", "-3") == -3.0


def test_binary_values():
    assert api.binary_value("1") is True
    assert api.binary_value("0") is False
    assert api.binary_value("") is None


def test_poll_merges_queries_and_proxy_gets_credentials():
    data = make_reader().poll()
    assert data["settings/boiler/temp"] == "70"
    assert data["consumption_data/counter"] == "1234"
    assert FakeProxy.instances[0].args == ("123456", 8483, "192.0.2.10", "123456")


def test_slow_counter_read_every_tenth_cycle_only():
    reader = make_reader()
    for _ in range(11):
        reader.poll()
    proxy = FakeProxy.instances[0]
    assert proxy.calls.count("consumption_data/counter") == 2
    assert proxy.calls.count("operating_data") == 11


def test_firmware_read_takes_newest_version():
    assert make_reader().read_firmware() == "1.2.3"


def test_firmware_failure_returns_none_and_drops_proxy():
    reader = make_reader()
    FakeProxy.fail = True
    assert reader.read_firmware() is None
    assert FakeProxy.instances[0].s.closed


def test_poll_failure_raises_and_next_poll_reconnects():
    reader = make_reader()
    FakeProxy.fail = True
    with pytest.raises(TimeoutError):
        reader.poll()
    FakeProxy.fail = False
    reader.poll()
    assert len(FakeProxy.instances) == 2


def test_energy_total_integrates_and_persists(tmp_path):
    now = [0]
    reader = make_reader(tmp_path, clock=lambda: now[0])
    assert reader.poll()[const.ENERGY_RESOURCE] == "0.000"
    now[0] = 1800
    assert reader.poll()[const.ENERGY_RESOURCE] == "3.000"
    reader.close()
    assert json.load(open(tmp_path / "energy.json"))["kwh"] == 3.0
    assert make_reader(tmp_path).meter.kwh == 3.0


def test_close_flushes_total_and_survives_flush_error(tmp_path, caplog):
    now = [0]
    reader = make_reader(tmp_path, clock=lambda: now[0])
    reader.poll()
    now[0] = 1800
    reader.poll()
    assert not (tmp_path / "energy.json").exists()
    reader.close()
    assert json.load(open(tmp_path / "energy.json"))["kwh"] == 3.0
    assert FakeProxy.instances[0].s.closed

    reader = make_reader(tmp_path)
    reader.poll()

    def broken():
        raise RuntimeError("boom")

    reader.meter.flush = broken
    reader.close()
    assert FakeProxy.instances[-1].s.closed
    assert "Unable to flush energy total" in caplog.text


def test_entities_match_bridge_schema():
    from nbe_blackstar.names import EN

    rows = [r for r in csv.reader(open(os.path.join(ROOT, "src", "nbe_blackstar", "nbe_schema"))) if r and not r[0].startswith("#")]
    expected = [(r[0], r[2], r[8], r[3], EN[r[8]], r[4], r[5], r[6], r[7]) for r in rows]
    assert list(const.ENTITIES) == expected


def test_energy_entity_attributes():
    row = next(r for r in const.ENTITIES if r[0] == const.ENERGY_RESOURCE)
    assert row[2] == "braender_energi_kwh"
    assert row[6:] == ("total_increasing", "energy", "kWh")


def _component_trees():
    for name in sorted(os.listdir(COMPONENT)):
        if name.endswith(".py"):
            yield name, ast.parse(open(os.path.join(COMPONENT, name)).read())


def test_no_write_call_path_in_component_code():
    # protocol.py is the unchanged upstream copy and keeps its own guarded set(); nothing else may call it
    for name, tree in _component_trees():
        if name in ("protocol.py", "frames.py"):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in ("set", "make_request"), f"{name}:{node.lineno}"
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "NBE_ALLOW_WRITE" not in node.value, name


def test_protocol_copy_still_refuses_writes(monkeypatch):
    monkeypatch.delenv("NBE_ALLOW_WRITE", raising=False)
    with pytest.raises(PermissionError):
        Proxy.__new__(Proxy).set("settings/boiler/temp", "70")


def test_copied_modules_match_bridge_sources():
    for name in ("protocol.py", "frames.py", "energy.py", "reader.py"):
        assert open(os.path.join(COMPONENT, name)).read() == open(os.path.join(ROOT, "src", "nbe_blackstar", name)).read()


def test_manifest_hacs_and_translations():
    manifest = json.load(open(os.path.join(COMPONENT, "manifest.json")))
    assert manifest["domain"] == "nbe_blackstar"
    assert manifest["config_flow"] is True
    assert manifest["iot_class"] == "local_polling"
    assert manifest["requirements"] == ["pycryptodome==4.0.0"]
    strings = json.load(open(os.path.join(COMPONENT, "strings.json")))
    for lang in ("en", "da"):
        translated = json.load(open(os.path.join(COMPONENT, "translations", lang + ".json")))
        assert translated.keys() == strings.keys()
        assert translated["config"]["error"].keys() == strings["config"]["error"].keys()
    assert json.load(open(os.path.join(ROOT, "hacs.json")))["render_readme"] is True
