import importlib.util
import os

import pytest

_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "custom_components",
    "nbe_blackstar",
    "hopper.py",
)
_spec = importlib.util.spec_from_file_location("hopper", _PATH)
hopper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hopper)
Hopper = hopper.Hopper


def _two_cycles():
    # the 2026 dry runs: 144 kg refilled after each empty alarm, counter rise 192.4 and 196.9
    h = Hopper()
    # the 30 Oct no-fuel alarm anchors the first cycle, then 144 kg refilled
    h.update(46715.3, alarm=True, now=0)
    h.refill(144, counter=46715.3, now=1)
    h.update(46715.3, alarm=False, now=2)  # burner back in start-up/burning
    h.update(46907.7, alarm=True, now=3)
    h.refill(144, counter=46907.7, now=4)
    h.update(46907.7, alarm=False, now=5)
    h.update(47104.6, alarm=True, now=6)
    return h


def test_learns_counter_factor_from_dry_runs():
    h = _two_cycles()
    assert h.factor_samples == pytest.approx([192.4 / 144, 196.9 / 144])
    assert 1.33 <= h.factor <= 1.37


def test_alarm_empties_the_silo_estimate():
    h = _two_cycles()
    assert h.level_kg == 0
    assert h.low() is True


def test_level_falls_with_counter_rise():
    h = Hopper()
    h.refill(144, counter=1000.0, now=0)
    h.update(1050.0, alarm=False, now=1)
    assert h.level_kg == pytest.approx(144 - 50 / hopper.DEFAULT_FACTOR)


def test_counter_reset_does_not_raise_level():
    h = Hopper()
    h.refill(100, counter=1000.0, now=0)
    h.update(900.0, alarm=False, now=1)
    assert h.level_kg == pytest.approx(100)


def test_ignition_failure_right_after_refill_is_not_empty():
    h = Hopper()
    h.refill(144, counter=5000.0, now=0)
    h.update(5001.0, alarm=True, now=1)
    assert h.level_kg == pytest.approx(144 - 1 / hopper.DEFAULT_FACTOR)
    assert h.factor_samples == []


def test_alarm_only_counts_once_while_it_lasts():
    h = _two_cycles()
    before = list(h.factor_samples)
    h.update(47104.6, alarm=True, now=5)
    h.update(47104.6, alarm=True, now=6)
    assert h.factor_samples == before


def test_capacity_caps_the_estimate():
    h = Hopper(capacity_kg=150)
    h.refill(144, counter=0.0, now=0)
    h.refill(144, counter=0.0, now=1)
    assert h.level_kg == 150


def test_factor_override_wins_over_learned_value():
    h = _two_cycles()
    h.factor_override = 1.0
    assert h.factor == 1.0


def test_days_left_uses_recent_burn_rate():
    h = Hopper()
    h.refill(100, counter=0.0, now=0)
    # 16 kg/day in silo terms = 16 * 1.35 counter units per day
    for hour in range(0, 25):
        now = hour * 3600
        h.update(hour * 16 * 1.35 / 24, alarm=False, now=now)
    assert h.days_left() == pytest.approx((100 - 16) / 16, rel=0.05)


def test_days_left_needs_six_hours_of_data():
    h = Hopper()
    h.refill(100, counter=0.0, now=0)
    h.update(10.0, alarm=False, now=3600)
    assert h.days_left() is None


def test_low_triggers_under_two_days():
    h = Hopper()
    h.refill(30, counter=0.0, now=0)
    for hour in range(0, 25):
        h.update(hour * 16 * 1.35 / 24, alarm=False, now=hour * 3600)
    assert h.low() is True


def test_low_is_unknown_without_a_level():
    assert Hopper().low() is None


def test_set_level_for_calibration():
    h = Hopper()
    h.set_level(132.7, counter=47120.0, now=0)
    assert h.level_kg == pytest.approx(132.7)
    h.update(47120.0 + 1.35 * 10, alarm=False, now=1)
    assert h.level_kg == pytest.approx(122.7)


def test_round_trip_keeps_state():
    h = _two_cycles()
    again = Hopper(h.to_dict())
    assert again.factor_samples == h.factor_samples
    assert again.level_kg == h.level_kg
    assert again.counter_at_empty == h.counter_at_empty
    assert again.in_alarm is True


def test_bad_stored_values_are_ignored():
    h = Hopper({"level_kg": "nan", "counter_last": None, "samples": []})
    assert h.level_kg is None
    assert h.counter_last is None


def test_refill_without_counter_is_refused():
    with pytest.raises(ValueError):
        Hopper().refill(144, counter=None, now=0)
