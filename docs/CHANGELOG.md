# Changelog

## 0.0.12
- Brand icon for the integration (shown in Home Assistant and HACS).
- The alarm entity (`binary_sensor.nbe_alarm`) is a plain on/off sensor without the "problem" class. The controller flag behind it is not defined in the V7 manual and reads on during normal operation, so it should not be used for notifications.
- README rewritten in the same format as the other integrations. Docker/MQTT bridge details moved to `docs/docker.md`.
- Docs: `Pellets in hopper` is the controller's magazine content in kg (menu 8), which you set and which only counts down. The pellet counter unit (kg) is still inferred and waits for a refill test.

## 0.0.11
- Home Assistant integration: a missed controller poll no longer makes every entity unavailable. The integration retries once after 2 seconds and keeps the last values until 3 polls in a row have failed.
- Pellet counter (`sensor.nbe_forbrug_teller`) is reported in kg with device class weight. The unit is inferred from the burner energy and is not yet confirmed on the display. Home Assistant may show a unit change in the statistics for this sensor.
- The slow pellet counter keeps its last value when its query fails, instead of dropping out for that cycle.
- Runbook: moving from the Docker/MQTT bridge to the HACS integration.
- CI: the image is also built for arm64 and imports the bridge module there.

## 0.0.10
- The device is shown as made by Mac O Kay in Home Assistant, in both the HACS integration and the Docker/MQTT bridge. The model is still Black Star 1016 (V7).
- README rewritten: the HACS integration is the recommended install, the Docker/MQTT bridge is the alternative, and the two must not run against the same controller.

## 0.0.9
- Controller requests: the sequence number now wraps at 100 instead of growing to three digits. Fixes the recurring `response sequence number 10 != request 100` errors and the reconnect each one caused.

## 0.0.7
- New readings from the controller manual (menu 15 and 18): return temperature (`retur_temperatur`), flue gas temperature (`rog_temperatur`) and current draw in mA (`stromforbrug_ma`). Not connected sensors show unknown.

## 0.0.6
- Bridge: SIGTERM (Docker and systemd stop) now runs the same shutdown path as Ctrl+C, so the energy total is flushed and the bridge publishes offline.
- Bridge: availability goes offline only after 3 consecutive failed cycles, so a single missed poll no longer flips every entity to unavailable and back.
- Bridge: the firmware version read is retried on later cycles if it failed at connect, and discovery is republished once when it succeeds. Discovery no longer accumulates duplicate entries on reconnect.
- README: runtime requirements corrected to Python 3.14, `paho-mqtt` 2.1.0 and `pycryptodome` 4.0.0.
- Home Assistant integration: the energy total is flushed when Home Assistant stops, so up to ten updates are no longer lost on restart.
- Frame errors: every `IOError` raised while encoding or decoding a frame now carries a message naming the failed check (start/end byte, short frame, frame length, sequence number, and so on) with the observed values, so the previously empty `OSError:` log lines can be traced. Accepted and rejected frames are unchanged.
- Dependencies: `requirements.in` and `requirements-dev.in` are the source; the hash-pinned `requirements.txt` and `requirements-dev.txt` are generated with pip-compile and used by CI and the Docker image, so Dependabot bumps reach the image. The `.lock` files are removed.
- Home Assistant integration: the firmware version read is retried on later polls if it failed at setup, and the device is updated when it succeeds.

## 0.0.5
- `protocol.py`: the discovery socket is no longer bound explicitly; the OS picks an ephemeral port on first send. This removes the CodeQL bind-all-interfaces alert. No behaviour change for the controller.
- Hash-pinned installs: `requirements.lock` and `requirements-dev.lock` (pip-compile, `--require-hashes`) are used by CI and the Docker image; the Docker base image is pinned by digest.
- Release workflow also checks that `manifest.json` `version` matches the tag.
- The bridge and the Home Assistant integration now share one reader implementation (`reader.py`, copied into the component like `protocol.py`).
- Bridge: the slow counter is read on the first cycle after start, not after ten cycles. An empty controller answer is retried once, like an error.
- Energy total is written every 10th update and on shutdown, reducing SD card writes.

## 0.0.4
- Native Home Assistant integration (HACS) in `custom_components/nbe_blackstar/`: config flow (IP, serial, pincode, port), polling coordinator, the same sensors and binary sensors as the bridge, burner energy total. Read-only. Use it instead of the Docker/MQTT bridge, not together with it.
- `pyproject.toml`: repository root added to the pytest path for `tests/ha`.

## 0.0.3
- Burner energy: `energy/burner_kwh` (`sensor.nbe_braender_energi_kwh`, kWh, total_increasing) integrates the burner power over time. Total kept in `/var/lib/nbe/energy.json` (`NBE_ENERGY_FILE`), so it survives restarts. Gaps over an hour add nothing.

## 0.0.2
- `NBE_LANG=da|en` selects the entity names (default `da`). MQTT topics and entity ids stay the same in both languages.
- `pycryptodome` 4.0.0 (verified against a live controller) and Python 3.14 in the Docker image.

## 0.0.1 (first release)
- Package `nbe_blackstar` (`python -m nbe_blackstar`). Modules: `bridge`, `protocol`, `frames`, `ha_classes`, `settings`.
- Configuration from environment variables; `config.json` optional. Secrets are environment-only.
- `paho-mqtt` 2.x with the VERSION2 callback API. Pinned in `requirements.txt`.
- `logging` replaces `print`. Level from `NBE_DEBUG`.
- Device id from `NBE_DEVICE_ID` (default `nbe_<serial>`). Topic prefix follows the device id.
- Device name from `NBE_DEVICE_NAME`. Firmware version read from the controller (`sw_versions`).
- Discovery payloads carry an `origin` block (name, version, support URL).
- Removed unused climate and switch code, the command path, and the legacy-topic migration (done on existing installs).
- Docker image runs `python -m nbe_blackstar`; `docker_init` removed.

## Before the first release (changes on top of the upstream project, included in 0.0.1)

### Security
- Read-only by default. `Proxy.set()` raises `PermissionError` unless `NBE_ALLOW_WRITE=true`. The two climate `set` rows are removed from `src/nbe_schema`, so no writable entities are published to Home Assistant.
- Secrets come from the environment only: `NBE_PASS` and `MQTT_PASS` are required. A secret found in `config.json` aborts startup.
- Docker image runs as non-root user `nbe`. The service unit runs as `nbe` with `ProtectSystem=strict` and `NoNewPrivileges`.
- `.env.local` holds secrets for compose and is gitignored. `docker-compose*.yml` no longer contain passwords.

### Fixed
- `advanced_data` crashed with `UnicodeDecodeError` on non-ASCII payloads. Decoding now tries UTF-8 and falls back to latin-1. Verified live against the V7 controller: 53 items.
- `DataEntries.Append` typo (crashed switch resources).
- Missing `import sys` in `nbe.py`.
- `lock` flag was local to `nbe_update` and never blocked anything. Removed.
- Bare `except:` replaced with logged `Exception`.
- Availability: `bridge/state` now publishes `offline` when the controller query fails and `online` when it succeeds.

### Changed
- `refresh_rate` default 60 s (was 10 s), to avoid loading the controller.
- `settings.init()` runs in `start()`, and `nbe.py` only starts the loop under `__main__`. Modules can be imported in tests.
- Docker base image `python:3.13-alpine` (was `alpine:3.10`, EOL). `paho-mqtt` pinned to 1.6.1 because the code uses the v1 callback API. `pycryptodome` replaces `py3-crypto`.
- Healthcheck: the container is unhealthy if `/tmp/nbe-alive` is older than 5 minutes.

### Entities (Home Assistant)
- Danish entity names and ASCII entity ids (`sensor.nbe_<object_id>`), device `NBE kedel` (Black Star 1016, V7). `unique_id` is `<device-id>_<object_id>`.
- Corrected sources: `Varmtvand` now reads `dhw_temp` (was `sun_dhw_temp`, solar sensor). `Pellets i magasin` replaces the mislabelled `Burned total`.
- Not-connected sensors (999.9) publish `unknown`. Negative pellet count publishes `unknown`.
- Binary sensors for pumps and alarm (`off_on_alarm` is not yet verified to mean alarm).
- Upstream entities (`nbeblackstar`) removed with empty retained payloads on startup.
- Pellet counter `consumption_data/counter` (unit not verified, `total_increasing`), read every ~10 minutes.
- Calibration log: raw `content` and `counter` appended every ~10 minutes to `/var/lib/nbe/timeseries.csv` (StateDirectory).
- Removed the writable climate entities and unconnected solar/floor-tracking sensors.

### Fixed (Home Assistant error log)
- 999 filter only hides exactly 999.9, so large valid counters are shown.
- Not-connected and negative values publish an empty state instead of the text `unknown`, which HA rejected on numeric sensors.
- `Lysniveau` uses unit `%` without device class (`lm` is invalid with `illuminance`).
- MQTT Last Will: `offline` retained, so a crashed bridge does not show stale values.
- One controller session is reused across cycles and recreated only after an error.
- A silent controller raises `TimeoutError` instead of returning `None`.

### Docs and deployment
- README rewritten for public use: requirements, configuration table, Docker and systemd install, Home Assistant entities, known gaps.
- Compose files build from this repository (`build: docker/Dockerfile`) instead of pulling upstream images.
- The bridge runs in Docker, with a systemd unit as an alternative.

### Tests
- `tests/`: 15 offline tests (write guard, schema, secrets, frame decoding, query and availability). Run with `pytest` from a venv that has `requirements-dev.txt`.
