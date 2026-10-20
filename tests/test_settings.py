import json

import pytest

from nbe_blackstar import settings

ENV = {"NBE_PASS": "p1", "MQTT_PASS": "p2", "NBE_SERIAL": "123456", "NBE_IP": "192.0.2.10", "MQTT_IP": "192.0.2.20"}


def _write(tmp_path, data):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_secrets_come_from_env(tmp_path):
    cfg = settings.load(str(tmp_path / "none.json"), ENV)
    assert cfg["nbe_pass"] == "p1"
    assert cfg["mqtt_pass"] == "p2"
    assert cfg["nbe_ip"] == "192.0.2.10"


def test_missing_env_secret_fails_loud(tmp_path):
    env = {k: v for k, v in ENV.items() if k != "NBE_PASS"}
    with pytest.raises(SystemExit, match="NBE_PASS"):
        settings.load(str(tmp_path / "none.json"), env)


def test_secret_in_config_file_is_rejected(tmp_path):
    path = _write(tmp_path, {"nbe_pass": "test-only"})
    with pytest.raises(SystemExit, match="nbe_pass"):
        settings.load(path, ENV)


def test_missing_required_setting_fails_loud(tmp_path):
    env = {k: v for k, v in ENV.items() if k != "NBE_IP"}
    with pytest.raises(SystemExit, match="NBE_IP"):
        settings.load(str(tmp_path / "none.json"), env)


def test_env_overrides_file_and_defaults_apply(tmp_path):
    path = _write(tmp_path, {"nbe_ip": "192.0.2.99", "refresh_rate": 30})
    cfg = settings.load(path, dict(ENV, NBE_REFRESH="1"))
    assert cfg["nbe_ip"] == "192.0.2.10"
    assert cfg["refresh_rate"] == 30
    assert cfg["nbe_port"] == 8483
    assert cfg["device_name"] == "NBE Black Star"


def test_device_id_defaults_to_serial_and_can_be_set(tmp_path):
    cfg = settings.load(str(tmp_path / "none.json"), ENV)
    assert cfg["device_id"] == "nbe_123456"
    cfg = settings.load(str(tmp_path / "none.json"), dict(ENV, NBE_DEVICE_ID="nbe_kedel"))
    assert cfg["device_id"] == "nbe_kedel"
