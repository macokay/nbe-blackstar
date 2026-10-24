# Docker / MQTT bridge

Use the bridge if you want MQTT, or a system other than Home Assistant (OpenHAB, ioBroker, Node-RED). For Home Assistant, the HACS integration in the [README](../README.md) is the recommended install.

**Use one, never both against the same controller.** The controller answers one client at a time. Two clients cause request errors and duplicate entities.

## Requirements

- An MQTT broker, for example the Mosquitto add-on in Home Assistant.
- Docker, or Python 3.14 with `paho-mqtt` 2.1.0 and `pycryptodome` 4.0.0.

## Run with Docker

```
cp .env.local.example .env.local   # fill in NBE_PASS and MQTT_PASS
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml logs -f nbe
```

The image runs as a non-root user and has a healthcheck. It is unhealthy if the controller has not answered for 5 minutes. Compose builds the image for your machine (amd64 or arm64). Release images for both architectures are published to `ghcr.io/macokay/nbe-blackstar`.

Entities appear through MQTT discovery under the device name from your configuration (default `NBE Black Star`). Sensors use `sensor.nbe_<object_id>`, pumps and alarm use `binary_sensor.nbe_*`.

## Configuration

Every setting comes from an environment variable. `config.json` is optional and may hold non-secret overrides (see [config.json-example](config.json-example)). Secrets are environment-only.

| Variable | Required | Default | Notes |
|---|---|---|---|
| `NBE_SERIAL` | yes | | Controller serial number (menu 18). |
| `NBE_IP` | yes | | Controller IP (use a fixed address). |
| `NBE_PORT` | no | `8483` | Controller UDP port. |
| `NBE_PASS` | yes | | Controller pincode, shown on the burner display (menu 18). Secret. |
| `MQTT_IP` | yes | | MQTT broker host. |
| `MQTT_PORT` | no | `1883` | MQTT broker port. |
| `MQTT_USER` | no | | MQTT user. |
| `MQTT_PASS` | yes | | MQTT password. Secret. |
| `MQTT_CLIENT_NAME` | no | `nbe-blackstar` | MQTT client id. |
| `REFRESH_RATE` | no | `60` | Seconds between reads. |
| `HA_PREFIX` | no | `homeassistant` | Home Assistant discovery prefix. |
| `NBE_DEVICE_ID` | no | `nbe_<serial>` | Device id. Keeps entity topics stable when changed. |
| `NBE_DEVICE_NAME` | no | `NBE Black Star` | Device name in Home Assistant. |
| `NBE_LANG` | no | `da` | Entity names: `da` or `en`. Topics and entity ids do not change with the language. |
| `NBE_DEBUG` | no | `false` | Debug logging. |
| `NBE_ALLOW_WRITE` | no | unset | Leave unset. Writes are not implemented in this build. |

Copy `.env.local.example` to `.env.local`, fill in the secrets, and keep it out of git (it is gitignored).

## Run as a systemd service (without Docker)

1. Create a system user `nbe`.
2. Copy `src/nbe_blackstar/` to `/opt/nbe/nbe_blackstar`.
3. Put all variables from the table in `/etc/nbe/nbe.env` (mode 600).
4. Install the runtime: `python3 -m venv /opt/nbe/venv && /opt/nbe/venv/bin/pip install -r requirements.txt`
5. Copy `deploy/nbe.service` to `/etc/systemd/system/`, then `systemctl enable --now nbe`.

Operations, rollback and moving to the HACS integration: [runbook.md](runbook.md).
