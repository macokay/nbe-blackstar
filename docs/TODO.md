# Roadmap

Status: under development. Read-only. Items here are open work, not promises. See [CHANGELOG.md](CHANGELOG.md) for what is done.

## Next
- [x] HACS integration installed in Home Assistant and running on a live controller (0.0.9 and 0.0.10). Verified: English names and entity ids, live values, options, energy under load.
- [ ] HACS friendly names carry the device prefix ("NBE Black Star Boiler temperature"), while the bridge shows "NBE kedel ...". Decide whether to change the device name. Run the live tests with NBE_LIVE_HOST, NBE_LIVE_SERIAL and NBE_LIVE_PIN set.
- [ ] Energy total when moving from the bridge to HACS. The HACS sensor starts at 0 kWh, and the bridge total is on a separate entity. Decide whether the two are merged.
- [ ] Per-entity availability, so a single sensor can be unavailable without affecting the others.
- [ ] Value audit: [values.md](values.md) lists every value. Still to confirm: units of `pressure`, `feed_*`, `fan_speed`, `milli_ampere`; the `state` text mapping.
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
