import pytest
from unittest.mock import MagicMock

from core.app import App


class FakeEntry:
    """Minimal fake for tkinter Entry/Spinbox widgets."""
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


def make_app_stub(**overrides):
    """Create a stub object with Entry-like attributes for _validate_settings.

    Default values are all valid so tests can override only what they need.
    """
    defaults = {
        "ent_max_safety_cars": "5",
        "ent_start_minute": "10",
        "ent_end_minute": "60",
        "ent_min_time_between": "5",
        "ent_laps_under_sc": "3",
        "ent_laps_before_wave_arounds": "1",
        "ent_random_prob": "0.5",
    }
    defaults.update(overrides)

    stub = MagicMock(spec=[])
    for attr, value in defaults.items():
        setattr(stub, attr, FakeEntry(value))
    return stub


class TestValidateSettings:
    """Tests for App._validate_settings validation logic."""

    def _validate(self, **overrides):
        stub = make_app_stub(**overrides)
        return App._validate_settings(stub)

    # --- Valid inputs produce no errors or warnings ---

    def test_all_valid_defaults(self):
        results = self._validate()
        assert results == {}

    # --- Non-numeric input errors ---

    def test_max_safety_cars_non_numeric(self):
        results = self._validate(ent_max_safety_cars="abc")
        assert results["ent_max_safety_cars"][0] == "error"
        assert "whole number" in results["ent_max_safety_cars"][1]

    def test_start_minute_non_numeric(self):
        results = self._validate(ent_start_minute="abc")
        assert results["ent_start_minute"][0] == "error"
        assert "Earliest Minute" in results["ent_start_minute"][1]

    def test_end_minute_non_numeric(self):
        results = self._validate(ent_end_minute="abc")
        assert results["ent_end_minute"][0] == "error"
        assert "Latest Minute" in results["ent_end_minute"][1]

    def test_min_time_between_non_numeric(self):
        results = self._validate(ent_min_time_between="abc")
        assert results["ent_min_time_between"][0] == "error"
        assert "Min Time Between" in results["ent_min_time_between"][1]

    def test_laps_under_sc_non_numeric(self):
        results = self._validate(ent_laps_under_sc="abc")
        assert results["ent_laps_under_sc"][0] == "error"
        assert "Laps Under SC" in results["ent_laps_under_sc"][1]

    def test_laps_before_wave_arounds_non_numeric(self):
        results = self._validate(ent_laps_before_wave_arounds="abc")
        assert results["ent_laps_before_wave_arounds"][0] == "error"
        assert "Laps Before Wave Arounds" in results["ent_laps_before_wave_arounds"][1]

    def test_random_prob_non_numeric(self):
        results = self._validate(ent_random_prob="abc")
        assert results["ent_random_prob"][0] == "error"
        assert "Random Probability" in results["ent_random_prob"][1]

    # --- Negative max safety cars is an error ---

    def test_max_safety_cars_negative(self):
        results = self._validate(ent_max_safety_cars="-1")
        assert results["ent_max_safety_cars"][0] == "error"
        assert "negative" in results["ent_max_safety_cars"][1]

    # --- Max safety cars = 0 is valid (infinite) ---

    def test_max_safety_cars_zero_valid(self):
        results = self._validate(ent_max_safety_cars="0")
        assert results.get("ent_max_safety_cars") is None

    # --- End minute <= start minute is an error ---

    def test_end_minute_equals_start_minute(self):
        results = self._validate(ent_start_minute="10", ent_end_minute="10")
        assert results["ent_end_minute"][0] == "error"
        assert "greater than" in results["ent_end_minute"][1]

    def test_end_minute_less_than_start_minute(self):
        results = self._validate(ent_start_minute="20", ent_end_minute="10")
        assert results["ent_end_minute"][0] == "error"
        assert "greater than" in results["ent_end_minute"][1]

    # --- Negative start minute is a warning ---

    def test_start_minute_negative_warning(self):
        results = self._validate(ent_start_minute="-5", ent_end_minute="60")
        assert results["ent_start_minute"][0] == "warning"
        assert "Negative" in results["ent_start_minute"][1]
        assert results.get("ent_end_minute") is None  # no error since end > start

    # --- Negative min time between is a warning ---

    def test_min_time_between_negative_warning(self):
        results = self._validate(ent_min_time_between="-1")
        assert results["ent_min_time_between"][0] == "warning"
        assert "Negative" in results["ent_min_time_between"][1]

    # --- Laps under SC < 1 is a warning ---

    def test_laps_under_sc_zero_warning(self):
        results = self._validate(ent_laps_under_sc="0")
        assert results["ent_laps_under_sc"][0] == "warning"
        assert "Less than 1" in results["ent_laps_under_sc"][1]

    # --- Laps before wave arounds negative is a warning ---

    def test_laps_before_wave_arounds_negative_warning(self):
        results = self._validate(ent_laps_before_wave_arounds="-1")
        assert results["ent_laps_before_wave_arounds"][0] == "warning"
        assert "Negative" in results["ent_laps_before_wave_arounds"][1]

    # --- Laps before wave arounds >= laps under SC is a warning ---

    def test_laps_before_wave_arounds_gte_laps_under_sc(self):
        results = self._validate(ent_laps_under_sc="3", ent_laps_before_wave_arounds="3")
        assert results["ent_laps_before_wave_arounds"][0] == "warning"
        assert "Wave arounds will never happen" in results["ent_laps_before_wave_arounds"][1]

    def test_laps_before_wave_arounds_greater_than_laps_under_sc(self):
        results = self._validate(ent_laps_under_sc="3", ent_laps_before_wave_arounds="5")
        assert results["ent_laps_before_wave_arounds"][0] == "warning"
        assert "Wave arounds will never happen" in results["ent_laps_before_wave_arounds"][1]

    # --- Random probability outside 0-1 is a warning ---

    def test_random_prob_greater_than_1(self):
        results = self._validate(ent_random_prob="1.5")
        assert results["ent_random_prob"][0] == "warning"
        assert "Outside 0-1 range" in results["ent_random_prob"][1]

    def test_random_prob_negative(self):
        results = self._validate(ent_random_prob="-0.1")
        assert results["ent_random_prob"][0] == "warning"
        assert "Outside 0-1 range" in results["ent_random_prob"][1]

    def test_random_prob_boundary_0_valid(self):
        results = self._validate(ent_random_prob="0")
        assert results.get("ent_random_prob") is None

    def test_random_prob_boundary_1_valid(self):
        results = self._validate(ent_random_prob="1")
        assert results.get("ent_random_prob") is None

    # --- Multiple errors at once ---

    def test_multiple_errors(self):
        results = self._validate(
            ent_max_safety_cars="abc",
            ent_start_minute="xyz",
            ent_random_prob="bad",
        )
        error_count = sum(1 for r in results.values() if r[0] == "error")
        assert error_count >= 3

    # --- Float input for int field is an error ---

    def test_max_safety_cars_float_input(self):
        results = self._validate(ent_max_safety_cars="2.5")
        assert results["ent_max_safety_cars"][0] == "error"
        assert "whole number" in results["ent_max_safety_cars"][1]

    def test_laps_under_sc_float_input(self):
        results = self._validate(ent_laps_under_sc="2.5")
        assert results["ent_laps_under_sc"][0] == "error"
        assert "whole number" in results["ent_laps_under_sc"][1]
