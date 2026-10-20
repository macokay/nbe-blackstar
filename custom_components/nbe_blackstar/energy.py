# Burner energy: integrates the controller's power (kW) into kWh for the Home Assistant Energy dashboard.
import json
import logging

log = logging.getLogger("nbe_blackstar")

# a gap longer than this (bridge or controller down) adds nothing, so an outage does not count as burning
MAX_GAP_S = 3600


class EnergyMeter:
    def __init__(self, path):
        self.path = path
        self.kwh = 0.0
        self.last = None
        self._load()

    def _load(self):
        if self.path is None:
            return
        try:
            with open(self.path) as f:
                self.kwh = float(json.load(f)["kwh"])
        except FileNotFoundError:
            return
        except (OSError, ValueError, KeyError) as e:
            log.warning("Unable to read energy total %s, starting at 0: %s", self.path, e)

    def _save(self):
        if self.path is None:
            return
        try:
            with open(self.path, "w") as f:
                json.dump({"kwh": round(self.kwh, 4)}, f)
        except OSError as e:
            log.warning("Unable to write energy total %s: %s", self.path, e)

    def update(self, power_kw, now):
        if self.last is not None and power_kw is not None:
            gap = now - self.last
            if 0 < gap <= MAX_GAP_S:
                self.kwh += max(power_kw, 0.0) * gap / 3600
        self.last = now
        self._save()
        return self.kwh
