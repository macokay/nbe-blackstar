import json
import logging

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
    monkeypatch.setattr(nbe, "energy_meter", EnergyMeter(None))
    client = type("C", (), {"published": [], "subscribe": lambda self, t, qos=0: None})()
    client.publish = lambda topic, payload, qos=0, retain=False: client.published.append((topic, payload))
    nbe.populate_resources(client)
    client.published.clear()
    monkeypatch.setattr(nbe, "nbe_query", lambda: {"operating_data/power_kw": "6.9"})
    nbe.refresh_statuses(client)
    published = dict(client.published)
    energy_topics = [t for t in published if "energi" in t or "energy" in t]
    assert len(energy_topics) == 1
    assert published[energy_topics[0]] == "0.000"
