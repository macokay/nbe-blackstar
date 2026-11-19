# Controller values

Every value the controller returned on a test controller (firmware 7.0680), read through `get()` only. Each row says whether the bridge exposes it, and how sure we are of the meaning.

Status:
- **exposed**: published to Home Assistant.
- **candidate**: worth an entity, not yet added.
- **skip**: constant, unused, or a duplicate.
- **unknown**: meaning not confirmed. Do not use it in automations until it is.

Confidence:
- **confirmed**: the value matches a display reading or a setting we set ourselves.
- **inferred**: the name and value point to a meaning, not yet checked against the display or the vendor manual.
- **unknown**: no basis for a meaning.

## operating_data

| Key | Inferred meaning | Unit | Confidence | Status |
|---|---|---|---|---|
| `time` | Controller clock | text | confirmed | skip (timestamp, not a sensor) |
| `boiler_temp` | Boiler temperature | °C | confirmed | exposed as `boiler_temperature` |
| `boiler_ref` | Boiler target (setpoint) | °C | confirmed (matches `settings/boiler/temp`) | exposed as `boiler_target` |
| `dhw_temp` | Hot water temperature | °C | confirmed | exposed as `hot_water` |
| `dhw_ref` | Hot water target | °C | confirmed (matches `settings/hot_water/temp`) | exposed as `hot_water_target` |
| `forward_temp` | Floor heating flow | °C | inferred | exposed as `floor_heating_flow`; reads 999.9 when not connected |
| `forward_ref` | Floor heating target | °C | inferred | exposed as `floor_heating_target` |
| `return_temp` | Return temperature | °C | inferred | candidate; 999.9 when not connected |
| `shaft_temp` | Shaft temperature | °C | inferred | exposed as `shaft_temperature` |
| `smoke_temp` | Flue gas temperature | °C | inferred | candidate; 999.9 when not connected |
| `external_temp` | Outdoor sensor | °C | inferred | exposed as `outdoor_temperature`; 999.9 when not connected |
| `mean_out_temp` | Mean outdoor temperature (weather) | °C | inferred | candidate |
| `chill_out` | Outdoor temperature used for regulation | °C | inferred | candidate; often equals `mean_out_temp` |
| `t6_temp`, `t7_temp` | Extra temperature sensors | °C | unknown | skip until connected |
| `sun_temp`, `sun2_temp`, `sun_dhw_temp`, `sun_surplus_temp` | Solar circuit | °C | inferred | skip (solar not installed; always 999.9) |
| `sun_power_kw`, `sun_pumpspeed`, `sun_pump_state`, `sun_surplus_state` | Solar circuit | mixed | inferred | skip (solar not installed) |
| `power_kw` | Burner power | kW | confirmed (6.9 kW at 65 %) | exposed as `burner_power`; integrated to `burner_energy` |
| `power_pct` | Burner load | % | confirmed | exposed as `burner_load` |
| `oxygen` | Flue oxygen | % | inferred | exposed as `oxygen` |
| `oxygen_ref` | Oxygen target | % | inferred | exposed as `oxygen_target` |
| `milli_ampere` | Flame sensor current | mA | inferred | candidate; useful to see whether the flame is lit |
| `pressure` | Water pressure | bar | unknown | candidate after checking the unit |
| `air_flow` | Combustion air flow | unknown | unknown | candidate after checking the unit |
| `fan_speed`, `exhaust_speed` | Fan and exhaust speed | unknown | inferred | candidate |
| `distance` | Pellet level distance | unknown | unknown | candidate, but meaning unknown |
| `photo_level` | Flame light (photo cell) | % | inferred | exposed as `light_level`. Reads 0 in daylight, so it may be the flame cell, not room light |
| `content` | Pellet magazine level | kg | inferred | exposed as `pellets_in_hopper`; negative values, so unreliable until calibrated |
| `state` | Operating state code | code | inferred | exposed as `operating_state`. Observed on 2026-10-30: `20` = the display alarm "ALARM INGEN ILD - BRÆNDSEL?" (confirmed by photo and history), `2` = start-up, about 3 minutes before `7`, `7` = burning, `9` = standby between cycles, `0` = seen once for one minute. Only `20` is confirmed against the display |
| `substate`, `substate_sec` | Sub-state and seconds in it | code, s | inferred | candidate |
| `boiler_pump_state` | Boiler pump on | 0/1 | confirmed (pump on while burning) | exposed as `boiler_pump` |
| `house_pump_state` | Floor pump on | 0/1 | inferred | exposed as `floor_pump` |
| `dhw_valve_state` | Hot water valve | 0/1 | inferred | candidate |
| `house_valve_state` | Floor valve position | % | inferred | exposed as `floor_valve` |
| `off_on_alarm` | Three-way flag: off, on, alarm | 0/1/other | inferred | The raw flag reads `1` (on) while the burner runs, and during the no-fuel alarm (state `20`, 2026-10-30) it was neither 0 nor 1. The V7 manual does not define it. Since 0.0.13 the `alarm` binary sensor is decoded from the operating state and this flag: on in state `20`, off while burning or on standby. The raw flag is kept in the `raw` attribute |
| `feed_low`, `feed_medium`, `feed_high` | Feed rate per power level | unknown | unknown | candidate after checking the unit |
| `corr_low`, `corr_medium`, `corr_high` | Correction factor per power level | % | unknown | skip until understood |
| `ash_clean`, `compressor_clean` | Time since cleaning | unknown | inferred | candidate; useful for maintenance |
| `output_std`, `output_ext`, `output_wireless` | Output bit masks | bits | unknown | skip |
| `contact1`, `contact2` | External contacts | 0/1 | unknown | candidate once wired |
| `cloud_level` | Cloud cover | % | unknown | skip |
| `internet_uptime` | Controller internet uptime | % | unknown | skip |
| `dl_progress` | Download progress | % | unknown | skip |
| `NA` | Unknown | - | unknown | skip |

## content vs counter

- `content` (`operating_data/content`) is the magazine level estimate. It is negative on the test controller, so it stays unreliable until calibrated.
- `consumption_data/counter` is the pellet counter. It is monotonic and is exposed as `pellet_consumption_counter`, in **kg (confirmed)**. The same quantity is shown on the burner display as "Magasinindhold" (main screen silo graphic and menu 8), with a constant offset of 17200: the display read 29418 kg on 2026-10-24 and 29515 kg on 2026-10-30, a rise of 97, while the counter rose 97.3 (46618.0 to 46715.3). Cross-check: 586 kWh of burner energy over 7.7 days against a counter rise of 126.6 gives 4.63 kWh per kg, close to the energy content of pellets (about 4.8 kWh/kg). Despite its name and the V7 manual, the displayed "Magasinindhold" rose with consumption on firmware 7.0680. It does not count down.

## settings

| Key | Meaning | Status |
|---|---|---|
| `settings/boiler/temp` | Boiler target | used as reference for `boiler_target` |
| `settings/boiler/diff_over`, `diff_under` | Hysteresis for the boiler | candidate (configuration) |
| `settings/boiler/monday`…`sunday` | Weekly schedule bit pattern | skip (not a sensor) |
| `settings/boiler/min_return` | Minimum return temperature | candidate |
| `settings/hot_water/temp` | Hot water target | used as reference for `hot_water_target` |
| `settings/hot_water/diff_under` | Hot water hysteresis | candidate |
| `settings/regulation/*` | Regulation gains and power limits | skip (configuration, change only with the vendor) |

Settings are read only. Writing is not implemented, see [TODO.md](TODO.md).

## consumption_data

| Key | Meaning | Status |
|---|---|---|
| `counter` | Pellet counter | exposed as `pellet_consumption_counter` |
| `total_hours`, `total_days`, `total_months`, `total_years`, `dhw_*` | Operating time totals and hot water share | candidate; the bridge reads them only through `get()` and returns empty values on the test controller |

## sw_versions

Newest first, `date,version,flag`. The bridge uses the first line as firmware version, shown as `sw_version` on the Home Assistant device.

## Next steps

1. Check the unit and meaning of `pressure`, `feed_*`, `fan_speed` and `milli_ampere` against the display.
2. Confirm `off_on_alarm` with a deliberate test (for example, the burner in alarm state).
3. Decode `state` into text with the vendor's table.
