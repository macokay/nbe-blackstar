import json

import pytest

import settings


def _write(tmp_path, data):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_secrets_come_from_env(tmp_path):
    path = _write(tmp_path, {"nbe_serial": "123456", "nbe_ip": "192.0.2.10", "nbe_port": 8483})
    cfg = settings.load(path, {"NBE_PASS": "p1", "MQTT_PASS": "p2"})
    assert cfg["nbe_pass"] == "p1"
    assert cfg["mqtt_pass"] == "p2"
    assert cfg["nbe_ip"] == "192.0.2.10"


def test_missing_env_secret_fails_loud(tmp_path):
    path = _write(tmp_path, {"nbe_serial": "123456"})
    with pytest.raises(SystemExit, match="NBE_PASS"):
        settings.load(path, {"MQTT_PASS": "p2"})


def test_secret_in_config_file_is_rejected(tmp_path):
    path = _write(tmp_path, {"nbe_pass": "test-only"})
    with pytest.raises(SystemExit, match="nbe_pass"):
        settings.load(path, {"NBE_PASS": "p1", "MQTT_PASS": "p2"})


def test_missing_config_file_fails_loud(tmp_path):
    with pytest.raises(SystemExit, match="does not exist"):
        settings.load(str(tmp_path / "nope.json"), {"NBE_PASS": "p1", "MQTT_PASS": "p2"})
