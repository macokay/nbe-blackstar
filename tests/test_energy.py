import json
import logging
import os

from nbe_blackstar import bridge as nbe
from nbe_blackstar.energy import EnergyMeter


def test_integrates_power_over_time(tmp_path):
    meter = EnergyMeter(str(tmp_path / "energy.json"))
    assert meter.update(2.0, 1000) == 0.0
    assert round(meter.update(2.0, 1900), 3) == 0.5


def test_gap_longer_than_an_hour_adds_nothing(tmp_path):
    meter = EnergyMeter(str(tmp_path / "energy.json"))
    meter.update(5.0, 0)
    assert meter.update(5.0, 7200) == 0.0


def test_missing_power_adds_nothing_and_negative_power_is_clamped(tmp_path):
    meter = EnergyMeter(str(tmp_path / "energy.json"))
    meter.update(4.0, 0)
    assert meter.update(None, 3600) == 0.0
    assert meter.update(-3.0, 7200) == 0.0


def test_total_survives_restart(tmp_path):
    path = str(tmp_path / "energy.json")
    meter = EnergyMeter(path)
    meter.update(3.0, 0)
    meter.update(3.0, 1200)
    meter.flush()
    assert json.load(open(path))["kwh"] == 1.0
    assert EnergyMeter(path).kwh == 1.0


def test_corrupt_file_starts_at_zero_with_warning(tmp_path, caplog):
    path = tmp_path / "energy.json"
    path.write_text("not json")
    with caplog.at_level(logging.WARNING):
        meter = EnergyMeter(str(path))
    assert meter.kwh == 0.0
    assert "Unable to read energy total" in caplog.text


def test_refresh_publishes_burner_energy(monkeypatch):
    monkeypatch.setattr(nbe, "DataEntries", [])
    monkeypatch.setattr(nbe.settings, "config", {"ha_prefix": "homeassistant", "debug": False, "lang": "en"}, raising=False)
    monkeypatch.setattr(nbe, "_reader", None)
    client = type("C", (), {"published": [], "subscribe": lambda self, t, qos=0: None})()
    client.publish = lambda topic, payload, qos=0, retain=False: client.published.append((topic, payload))
    nbe.populate_resources(client)
    client.published.clear()
    monkeypatch.setattr(nbe, "nbe_query", lambda: {"operating_data/power_kw": "6.9", "energy/burner_kwh": "0.000"})
    monkeypatch.setattr(nbe, "fetch_sw_version", lambda: None)
    nbe.refresh_statuses(client)
    published = dict(client.published)
    energy_topics = [t for t in published if "energi" in t or "energy" in t]
    assert len(energy_topics) == 1
    assert published[energy_topics[0]] == "0.000"


def test_non_object_json_starts_at_zero(tmp_path):
    path = tmp_path / "energy.json"
    path.write_text("[]")
    assert EnergyMeter(str(path)).kwh == 0.0


def test_non_finite_total_starts_at_zero(tmp_path):
    path = tmp_path / "energy.json"
    path.write_text('{"kwh": NaN}')
    assert EnergyMeter(str(path)).kwh == 0.0


def test_save_replaces_file_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "energy.json"
    meter = EnergyMeter(str(path))
    meter.update(3.0, 0)
    meter.update(3.0, 1200)
    meter.flush()
    assert json.load(open(path))["kwh"] == 1.0
    assert not (tmp_path / "energy.json.tmp").exists()


def _saved(path):
    return json.load(open(path))["kwh"] if os.path.exists(path) else None


def test_total_is_written_every_tenth_update(tmp_path):
    path = str(tmp_path / "energy.json")
    meter = EnergyMeter(path)
    for i in range(9):
        meter.update(6.0, i * 60)
    assert _saved(path) is None
    meter.update(6.0, 9 * 60)
    assert _saved(path) == round(meter.kwh, 4)
    assert meter.kwh > 0


def test_flush_writes_total_before_ten_updates(tmp_path):
    path = str(tmp_path / "energy.json")
    meter = EnergyMeter(path)
    meter.update(6.0, 0)
    meter.update(6.0, 600)
    assert _saved(path) is None
    meter.flush()
    assert _saved(path) == 1.0


def test_reopen_after_flush_returns_flushed_total(tmp_path):
    path = str(tmp_path / "energy.json")
    meter = EnergyMeter(path)
    meter.update(3.0, 0)
    meter.update(3.0, 1200)
    meter.flush()
    assert EnergyMeter(path).kwh == 1.0


def test_failed_save_keeps_total_and_retries(tmp_path, monkeypatch):
    path = str(tmp_path / "energy.json")
    meter = EnergyMeter(path)
    meter.update(6.0, 0)
    meter.update(6.0, 600)
    real_replace = os.replace

    def broken(*args):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", broken)
    meter.flush()
    assert meter.kwh == 1.0
    monkeypatch.setattr(os, "replace", real_replace)
    meter.flush()
    assert _saved(path) == 1.0


def test_shutdown_flushes_energy_total(tmp_path, monkeypatch):
    path = str(tmp_path / "energy.json")
    meter = EnergyMeter(path)
    meter.update(6.0, 0)
    meter.update(6.0, 600)
    reader = nbe.NbeReader("192.0.2.10", "123456", "123456", 8483)
    reader.meter = meter
    monkeypatch.setattr(nbe, "_reader", reader)
    monkeypatch.setattr(nbe, "device", type("D", (), {"getUid": lambda self: "uid"})(), raising=False)
    client = type("C", (), {"published": [], "loop_stop": lambda self: None, "disconnect": lambda self: None})()
    client.publish = lambda *a: client.published.append(a)
    assert nbe.shutdown(client) == 0
    assert _saved(path) == 1.0
    assert client.published == [("uid/bridge/state", "offline", 0, True)]
