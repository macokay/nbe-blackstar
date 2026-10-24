# Roadmap

Status: under development. Read-only. Items here are open work, not promises. See [CHANGELOG.md](CHANGELOG.md) for what is done.

## Next
- [x] HACS integration installed in Home Assistant and running on a live controller (0.0.9 and 0.0.10). Verified: English names and entity ids, live values, options, energy under load.
- [x] Controller misses no longer flip the whole integration to unavailable: the coordinator retries once after 2 seconds and keeps the last values until 3 polls in a row have failed. The slow counter keeps its last value when its query fails.
- [ ] Per-entity availability for a key that goes missing from the data. Open until it is seen in practice.
- [ ] Energy total when moving from the bridge to HACS: the procedure is in [runbook.md](runbook.md). Decide whether to carry the old total forward.
- [ ] Value audit: [values.md](values.md) lists every value. Still to confirm: units of `pressure`, `feed_*`, `fan_speed`, `milli_ampere`; the `state` text mapping.
- [ ] **Waiting:** pellet counter unit. It is shown as kg, inferred from the burner energy (about 4.7 kWh per unit) and from the controller counting pellets in kg for cleaning. The V7 manual has no consumption counter. Refill test pending: note the counter before and after the next pellet delivery and compare with the delivered kg.
- [ ] Pellet magazine level: calibrate from the logged raw counter against manual refill records.
- [ ] Verify the multi-arch image on real arm64 hardware. CI already imports the arm64 image under QEMU.

## Blocked on the controller vendor
- [ ] Operating state text (`state` codes).
- [ ] `event_log` decoder: event codes are not documented.
- [ ] Meaning of the `off_on_alarm` flag (alarm or on/off state).
- [ ] Controller firmware fix for DHCP (some controllers send DHCP requests to UDP port 53 instead of 67).

## Write support (not started)
- [ ] Burner on/off, setpoints, zone regulation.
- [ ] Requirements before building: confirmation on every command, min/max limits, audit log, `NBE_ALLOW_WRITE=true`, and agreement with the vendor.
