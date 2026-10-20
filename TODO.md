# Roadmap

Status: under development. Read-only. Items here are open work, not promises. See [CHANGELOG.md](CHANGELOG.md) for what is done.

## Next
- [ ] HACS integration: loads and renders its config flow in a real Home Assistant test instance (pytest-homeassistant-custom-component 0.13.368, scratch only, not a repo dependency). Setup without a controller ends in SETUP_RETRY, as intended. Still to verify with a live controller: entity registration and ids, Danish/English names, unload and reload, restart keeps the energy total, install through HACS.
- [ ] Add `validate.yml` (HACS) and `hassfest.yml` workflows, and extend CI lint to `custom_components`.
- [ ] Per-entity availability, so a single sensor can be unavailable without affecting the others.
- [ ] Value audit: [docs/values.md](docs/values.md) lists every value. Still to confirm: units of `pressure`, `feed_*`, `fan_speed`, `milli_ampere`; the `state` text mapping.
- [ ] Pellet counter: verify unit and that it is monotonic.
- [ ] Pellet magazine level: calibrate from the logged raw counter against manual refill records.
- [ ] Verify the multi-arch image on real arm64 hardware.

## Blocked on the controller vendor
- [ ] Operating state text (`state` codes).
- [ ] `event_log` decoder: event codes are not documented.
- [ ] Meaning of the `off_on_alarm` flag (alarm or on/off state).
- [ ] Controller firmware fix for DHCP (some controllers send DHCP requests to UDP port 53 instead of 67).

## Write support (not started)
- [ ] Burner on/off, setpoints, zone regulation.
- [ ] Requirements before building: confirmation on every command, min/max limits, audit log, `NBE_ALLOW_WRITE=true`, and agreement with the vendor.

## Project
- [ ] Reach out to Anders Nylund about relicensing the protocol code (GPL-2.0-or-later) under a more permissive license. The project is GPL-3.0-or-later until then.
