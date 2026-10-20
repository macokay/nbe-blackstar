# Changelog

## Unreleased
- `protocol.py`: the discovery socket now binds an ephemeral port chosen by the OS (`('', 0)`) instead of searching for a free port. No behaviour change for the controller, which replies to the source port of the request.
- Hash-pinned installs: `requirements.lock` and `requirements-dev.lock` (pip-compile, `--require-hashes`) are used by CI and the Docker image; the Docker base image is pinned by digest.
- Release workflow also checks that `manifest.json` `version` matches the tag.

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
