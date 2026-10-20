# TODO

Read-only fork of the upstream NBE Black Star bridge. Writes to the controller are off by default.

## Bugs (from Home Assistant error log)
- [ ] Narrow the 999 filter in `clean_value`: only `999.9` means "not connected". Large valid counters are currently hidden.
- [ ] Do not publish the text `unknown` on numeric sensors. Use availability or an empty value so HA does not log `Value error` every minute.
- [ ] `Lysniveau`: unit `lm` is invalid with device class `illuminance`. Drop the device class or change the unit.
- [x] MQTT Last Will: `offline` retained. Verified live 2026-10-19: SIGKILL gave retained `offline` after ~2 s, restart gave retained `online`.
- [ ] Reuse one UDP session per cycle. Unit-tested only; verify live over several cycles.
- [x] `TimeoutError` path: verified live via discovery timeout (`TimeoutError: timed out`, retry once, returns `{}`). The custom `controller did not answer` message from `make_request` is still not triggered live.
- [x] Session reuse: pcap on pve, 0 discovery packets during 2 cycles.
- [x] Crash on missing state dir: container crashed with FileNotFoundError at first slow cycle (RestartCount 1). Fixed: state dir in image, volume `nbe-data`, safe write and cycle wrapper. Verified live 17:13 UTC: timeseries row written, RestartCount 0.

## Public release
- [ ] Device id from the controller serial number, not hardcoded. Two controllers must not collide.
- [ ] Language switch via env (`NBE_LANG=da|en`), names in the schema.
- [ ] `sw_version` from the controller (`sw_versions`), not hardcoded text.
- [ ] CI: GitHub Actions running `pytest`, with `permissions: { contents: read }`. Add `requirements.txt` for runtime.
- [ ] Migrate `paho-mqtt` 1.6.1 to 2.x with `CallbackAPIVersion`.
- [ ] Remove dead code (`Climate`, `Switch`, `on_message`) and unused imports. Replace `print` with `logging`.

## Features
- [ ] Energy: integrate burner power (kW) to kWh so it shows in the Home Assistant Energy dashboard.
- [ ] Pellet magazine level: calibrate from raw counter logs against manual refill records.
- [ ] Pellet counter: verify unit and that it is monotonic.
- [x] Move the bridge to Docker in a second LXC (LXC 106, Docker 26.1.5 from Debian, nesting+keyctl). Container healthy and publishing 2026-10-19. Systemd service on LXC 105 is stopped and disabled, unit file kept as fallback.
  - [x] Add `ENV PYTHONUNBUFFERED=1` to the Dockerfile. Verified live: `Started up!` shows in `docker logs` at once.
  - [x] Verify the Last Will live in the container: retained `offline` 3 s after kill, `online` after restart.
  - [x] Restart policy: a container that exits on bad MQTT login restarts (`restarts=8` in 30 s).
  - [x] `docker compose config` and `docker compose build` valid on LXC 106.
  - [x] Verify the 10-minute slow cycle in the container: `Forbrug teller` gets a value (46542.4) and `RestartCount` stays 0 (verified 2026-10-19 17:13 UTC).
  - [ ] Build multi-arch on LXC 106 when needed.
  - Feasibility checked 2026-10-19: host kernel 7.0.2 has overlay and cgroup2. The current LXC has `nesting=0`, so Docker cannot run there. A new unprivileged LXC needs `features: nesting=1,keyctl=1`.
  - Multi-arch build needs a Docker host. The Mac has none, so build happens on the LXC.

## Value audit (every value the controller exposes)
- [ ] Go through all `operating_data` keys (64 seen), `settings/*`, `consumption_data`, and `sw_versions`. For each: meaning, unit, whether it is connected, and whether it is worth an entity.
- [ ] Record the result in a table (key, meaning, unit, status: used / skipped / unknown). Mark unknown meanings for the vendor question.
- [ ] Check each used value against the controller display and the vendor manual before treating it as correct.

## Blocked on controller vendor (NBE)
- [ ] `state` code mapping (operating state text).
- [ ] `event_log` decoder: event codes are not documented.
- [ ] Verify the `off_on_alarm` flag (alarm vs on/off state).
- [ ] Confirm the DHCP fix in firmware (controller used UDP 53 instead of 67).

## Write support (not started)
- [ ] Burner on/off, setpoints, zone regulation, climate control.
- [ ] Requirements before building: confirmation on every command, min/max limits, audit log, `NBE_ALLOW_WRITE=true`, and explicit agreement from the site owner and NBE.
