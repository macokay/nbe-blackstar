# Roadmap

Status: under development. Read-only. Items here are open work, not promises. See [CHANGELOG.md](CHANGELOG.md) for what is done.

## Next
- [ ] HACS integration, still open: install through the HACS UI, a real Home Assistant restart (the energy restart is verified with a simulated one), and English names on a live controller (English is covered by the offline HA test only). Verified so far: loads and renders the config flow, reads live values, entity ids match the bridge, reload keeps entities, energy integrates under load (8.5 kW gave 0.071 kWh in 30 s) and survives a restart. Run the live tests with NBE_LIVE_HOST, NBE_LIVE_SERIAL and NBE_LIVE_PIN set.
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
