# NBE Black Star (Blackstar+, RTB) for Home Assistant

Reads an NBE pellet burner controller (V7 / v13) over the local network and publishes its values to Home Assistant through MQTT discovery. Read-only by default: the bridge does not change the burner.

> **Status: under development.** Tested with one Black Star 1016 (V7 controller). Entity names and settings may change before 1.0. Read-only. Feedback and testers with other models are welcome.

Based on [e1z0/nbe-blackstar-homeassistant](https://github.com/e1z0/nbe-blackstar-homeassistant) and the protocol work of Anders Nylund (see [CREDITS.md](CREDITS.md)). Changes: [CHANGELOG.md](CHANGELOG.md). Security: [SECURITY.md](SECURITY.md). Roadmap: [TODO.md](TODO.md). Contributing: [CONTRIBUTING.md](CONTRIBUTING.md). Operations: [docs/runbook.md](docs/runbook.md).

<img src="https://github.com/e1z0/nbe-blackstar-homeassistant/raw/master/pics/nbe_blackstar_plus.png" width=45% height=45%><img src="https://github.com/e1z0/nbe-blackstar-homeassistant/raw/master/pics/nbe1.png" width=45% height=45%>

## Requirements

* An NBE controller on the local network, with a fixed IP address.
* An MQTT broker, for example the Mosquitto add-on in Home Assistant.
* Home Assistant, or another MQTT-capable system (OpenHAB, ioBroker, Node-RED).
* Docker, or Python 3.13 with `paho-mqtt` 1.6.1 and `pycryptodome`.

## Compatible burners

* NBE RTB 10, 10 VAC, 16, 16 VAC, 30, 30 VAC, 50, 50 VAC, 80 (v13 controller)
* NBE BS+ (Blackstar+) 10, 16, 25 (v13 controller)

Tested with a Black Star 1016 and a V7 controller. Other models are not verified. If you do not know your model, open the burner door and compare with the [NBE manual](https://www.nbe.dk/wp-content/uploads/2017/07/RTB-BS-Manual-V13-ENG-08.03.2017.pdf).

## Configuration

Every setting comes from an environment variable. `config.json` is optional and may hold non-secret overrides (see `config.json-example`). Secrets are environment-only.

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

## Run with Docker (recommended)

```
cp .env.local.example .env.local   # fill in NBE_PASS and MQTT_PASS
docker compose up -d --build
docker compose logs -f nbe
```

The image runs as a non-root user and has a healthcheck. It is unhealthy if the controller has not answered for 5 minutes.

Compose builds the image from this repository for your machine (amd64 or arm64). Release images for both architectures are published to `ghcr.io/macokay/nbe-blackstar`.

## Run as a systemd service (without Docker)

1. Create a system user `nbe`.
2. Copy `src/nbe_blackstar/` to `/opt/nbe/nbe_blackstar`.
3. Put all variables from the table in `/etc/nbe/nbe.env` (mode 600).
4. Install the runtime: `python3 -m venv /opt/nbe/venv && /opt/nbe/venv/bin/pip install -r requirements.txt`
5. Copy `nbe.service` to `/etc/systemd/system/`, then `systemctl enable --now nbe`.

## Home Assistant

Entities appear automatically through MQTT discovery under the device `NBE kedel` (or the name from your configuration). Sensors use `sensor.nbe_<object_id>`, pumps and alarm use `binary_sensor.nbe_*`.

Known gaps:
* `Pellets i magasin` (`operating_data/content`) reports negative values on the test controller. It is shown as unavailable until the meaning is confirmed.
* `binary_sensor.nbe_alarm` is the controller flag `off_on_alarm`. Its meaning is not confirmed, so do not use it for notifications yet.
* The text state of the operating mode and the event log are not decoded yet.

## Development

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

The tests run offline. They cover the write guard, schema, secrets, frame decoding, entity discovery, query retry and the MQTT last will.

## Customization

The sensors and their names are defined in `src/nbe_blackstar/nbe_schema`. Columns: `RESOURCE, METHOD, TYPE, NAME, ICON, STATE-CLASS, DEVICE-CLASS, UNIT, OBJECT_ID`.

## Credits

Protocol reverse engineering: Anders Nylund (2013). Original integration: e1z0. Fork: see CHANGELOG.

## License

This project is licensed under the GNU General Public License v3.0 or later (see [LICENSE](LICENSE)).

Some files keep their original notices:
* `src/nbe_blackstar/protocol.py`, `src/nbe_blackstar/frames.py`: GPL-2.0 or later (Anders Nylund, 2013). Compatible with GPL-3.0.
* `src/nbe_blackstar/bridge.py`, `src/nbe_blackstar/ha_classes.py`, `src/nbe_blackstar/settings.py`: BSD-3-Clause (e1z0, 2021-2022). Compatible with GPL-3.0.

Credits and contributors: [CREDITS.md](CREDITS.md).
