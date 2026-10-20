# Roadmap

Status: under development. Read-only. Items here are open work, not promises. See [CHANGELOG.md](CHANGELOG.md) for what is done.

## Next
- [ ] Language switch (`NBE_LANG=da|en`) with entity names in the schema.
- [ ] Native Home Assistant integration (HACS) in this repository, sharing the protocol code, for users without MQTT.
- [ ] Per-entity availability, so a single sensor can be unavailable without affecting the others.
- [ ] Energy: integrate burner power (kW) to kWh for the Home Assistant Energy dashboard.
- [ ] Value audit: document every value the controller exposes (`operating_data`, `settings/*`, `consumption_data`, `sw_versions`) with meaning, unit and whether it is worth an entity. Check each used value against the display and the vendor manual.
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
