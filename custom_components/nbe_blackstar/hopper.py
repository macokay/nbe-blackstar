# Pellet silo estimate: turns the controller's pellet counter into kg left in the silo.
# The controller counts about 1.35 counter units per kg fed (its auger calibration), so the estimate
# learns that factor from each alarm: the counter rise since the previous no-fuel alarm, divided by
# the kg refilled in between. Plain Python, no Home Assistant imports, so it can be tested directly.
import math
import statistics

DEFAULT_FACTOR = 1.35
DEFAULT_REFILL_KG = 144
FACTOR_RANGE = (0.8, 2.0)
FACTOR_SAMPLES = 3
# counter rise after a refill below this is a failed ignition, not an empty silo
MIN_COUNTER_RISE_FOR_EMPTY = 5.0
# burn rate is taken from the last 72 hours, at least 6 hours of data
RATE_WINDOW_S = 72 * 3600
RATE_MIN_SPAN_S = 6 * 3600
SAMPLE_EVERY_S = 600
MIN_KG_PER_DAY = 0.05


class Hopper:
    def __init__(self, data=None, capacity_kg=None, factor_override=None):
        data = data or {}
        self.capacity_kg = capacity_kg
        self.factor_override = factor_override
        self.level_kg = _opt_float(data.get("level_kg"))
        self.counter_last = _opt_float(data.get("counter_last"))
        self.counter_refill = _opt_float(data.get("counter_refill"))
        self.counter_at_empty = _opt_float(data.get("counter_at_empty"))
        self.kg_since_empty = float(data.get("kg_since_empty", 0.0))
        self.factor_samples = [float(x) for x in data.get("factor_samples", [])][-FACTOR_SAMPLES:]
        self.samples = [(float(t), float(c)) for t, c in data.get("samples", [])]
        self.last_sample_ts = _opt_float(data.get("last_sample_ts"))
        self.last_refill = data.get("last_refill")
        self.in_alarm = bool(data.get("in_alarm", False))
        self.refill_kg = _opt_float(data.get("refill_kg")) or DEFAULT_REFILL_KG

    @property
    def factor(self):
        if self.factor_override is not None:
            return self.factor_override
        if not self.factor_samples:
            return DEFAULT_FACTOR
        return statistics.median(self.factor_samples)

    def update(self, counter, alarm, now):
        if counter is None:
            return
        self._advance(counter)
        if alarm and not self.in_alarm:
            self._on_alarm(counter)
        self.in_alarm = alarm
        self._sample(counter, now)

    def refill(self, kg, counter, now):
        if counter is None:
            raise ValueError("no pellet counter reading yet")
        self._advance(counter)
        level = (self.level_kg or 0.0) + kg
        if self.capacity_kg:
            level = min(level, self.capacity_kg)
        self.level_kg = level
        self.counter_refill = counter
        self.kg_since_empty += kg
        self.last_refill = {"ts": now, "kg": kg}
        self._sample(counter, now, force=True)

    def set_level(self, kg, counter, now):
        if counter is None:
            raise ValueError("no pellet counter reading yet")
        self.level_kg = max(0.0, float(kg))
        self.counter_last = counter
        self._sample(counter, now, force=True)

    def days_left(self):
        if self.level_kg is None or len(self.samples) < 2:
            return None
        (t0, c0), (t1, c1) = self.samples[0], self.samples[-1]
        span = t1 - t0
        if span < RATE_MIN_SPAN_S or c1 <= c0:
            return None
        kg_per_day = (c1 - c0) / span * 86400 / self.factor
        if kg_per_day < MIN_KG_PER_DAY:
            return None
        return self.level_kg / kg_per_day

    def low(self, threshold_days=2.0):
        if self.level_kg is None:
            return None
        if self.level_kg <= 0:
            return True
        days = self.days_left()
        return days is not None and days < threshold_days

    def to_dict(self):
        return {
            "level_kg": self.level_kg,
            "counter_last": self.counter_last,
            "counter_refill": self.counter_refill,
            "counter_at_empty": self.counter_at_empty,
            "kg_since_empty": self.kg_since_empty,
            "factor_samples": self.factor_samples,
            "samples": self.samples,
            "last_sample_ts": self.last_sample_ts,
            "last_refill": self.last_refill,
            "in_alarm": self.in_alarm,
            "refill_kg": self.refill_kg,
        }

    def _advance(self, counter):
        if self.level_kg is not None and self.counter_last is not None:
            rise = counter - self.counter_last
            if rise > 0:
                self.level_kg = max(0.0, self.level_kg - rise / self.factor)
        self.counter_last = counter

    def _on_alarm(self, counter):
        ignition_failed = self.counter_refill is not None and counter - self.counter_refill < MIN_COUNTER_RISE_FOR_EMPTY
        if ignition_failed:
            return
        if self.counter_at_empty is not None and self.kg_since_empty > 0 and counter > self.counter_at_empty:
            sample = (counter - self.counter_at_empty) / self.kg_since_empty
            if FACTOR_RANGE[0] <= sample <= FACTOR_RANGE[1]:
                self.factor_samples = (self.factor_samples + [sample])[-FACTOR_SAMPLES:]
        self.level_kg = 0.0
        self.counter_last = counter
        self.counter_at_empty = counter
        self.kg_since_empty = 0.0

    def _sample(self, counter, now, force=False):
        if not force and self.last_sample_ts is not None and now - self.last_sample_ts < SAMPLE_EVERY_S:
            return
        self.samples = [(t, c) for t, c in self.samples if now - t <= RATE_WINDOW_S]
        self.samples.append((now, counter))
        self.last_sample_ts = now


def _opt_float(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
