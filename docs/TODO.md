# Roadmap

Status: under development. Read-only. Items here are open work, not promises. See [CHANGELOG.md](CHANGELOG.md) for what is done.

## Next
- [x] HACS integration installed in Home Assistant and running on a live controller (0.0.9 and 0.0.10). Verified: English names and entity ids, live values, options, energy under load.
- [x] Controller misses no longer flip the whole integration to unavailable: the coordinator retries once after 2 seconds and keeps the last values until 3 polls in a row have failed. The slow counter keeps its last value when its query fails.
- [ ] Per-entity availability for a key that goes missing from the data. Open until it is seen in practice.
- [ ] Energy total when moving from the bridge to HACS: the procedure is in [runbook.md](runbook.md). Decide whether to carry the old total forward.
- [ ] Value audit: [values.md](values.md) lists every value. Still to confirm: units of `pressure`, `feed_*`, `fan_speed`, `milli_ampere`; the `state` text mapping.
- [x] Pellet counter unit confirmed as kg: it matches the display's "Magasinindhold" (rise of 97 against 97.3) and the burner energy (4.63 kWh per kg). Optional extra check when the silo next runs dry (about 2026-11-08, after the 144 kg refill on 2026-10-30): the counter should then read about 46859.
- [ ] Pellet magazine level: calibrate from the logged raw counter against manual refill records. First record: 144 kg (9 bags of 16 kg) added on 2026-10-30 at 14:29 local time, counter 46715.3, after the no-fuel alarm. Level = refilled kg minus (counter minus counter at refill).
- [ ] Verify the multi-arch image on real arm64 hardware. CI already imports the arm64 image under QEMU.

## Blocked on the controller vendor
- [ ] Operating state text (`state` codes). Known from observation: 20 = no-fuel alarm, 2 = start-up, 7 = burning, 9 = standby. The rest need the vendor.
- [ ] `event_log` decoder: event codes are not documented.
- [ ] `off_on_alarm` is a three-way flag (off, on, alarm). Show it as a sensor with all three values instead of a binary sensor. Needs the raw value during an alarm.
- [ ] Controller firmware fix for DHCP (some controllers send DHCP requests to UDP port 53 instead of 67).

## Write support (not started)
- [ ] Burner on/off, setpoints, zone regulation.
- [ ] Requirements before building: confirmation on every command, min/max limits, audit log, `NBE_ALLOW_WRITE=true`, and agreement with the vendor.
