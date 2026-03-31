"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Regression tests for unit conversion across all UncertainField parameters.

NOTE: The unit conversion behavior in this system is designed for UI convenience:
- When you call set_unit_from_display(), the DISPLAYED value stays the same
- The INTERNAL (_value) value changes to represent the displayed value in new units
- Example: If you enter "2" in meters, then switch to inches, you still see "2"
           but the internal value changes from 2.0m to 0.0508m (2 inches in meters)
"""
import unittest

from ...models.fields_probabilistic import UncertainField
from ...utils.distributions import Distributions
from ...utils.units_of_measurement import Pressure, Temperature, Distance


DELTA = 1e-3


class TestUnitConversionBehavior(unittest.TestCase):
    """
    Tests that unit conversion behaves correctly.

    Key behavior: set_unit_from_display() keeps displayed value constant,
    but changes internal storage to match the new unit interpretation.
    """

    def test_pressure_display_unchanged_internal_changes(self):
        """When changing units, displayed value stays same, internal changes."""
        field = UncertainField('Test', value=1.0, distr=Distributions.det, unit_type=Pressure, unit='mpa')

        # Initial: 1.0 MPa displayed, 1.0 MPa internal
        self.assertAlmostEqual(field.value, 1.0, delta=DELTA)
        self.assertAlmostEqual(field._value, 1.0, delta=DELTA)

        # Change to psi display
        field.set_unit_from_display('psi')

        # Displayed value stays 1.0 (now interpreted as 1.0 psi)
        self.assertAlmostEqual(field.value, 1.0, delta=DELTA)

        # Internal value changed: 1.0 psi = 0.00689 MPa
        self.assertAlmostEqual(field._value, 0.00689, delta=0.0001)

    def test_distance_display_unchanged_internal_changes(self):
        """Distance unit change keeps display constant."""
        field = UncertainField('Test', value=2.0, distr=Distributions.det,
                               unit_type=Distance, unit='m')

        # Initial: 2.0 m displayed and internal
        self.assertAlmostEqual(field.value, 2.0, delta=DELTA)
        self.assertAlmostEqual(field._value, 2.0, delta=DELTA)

        field.set_unit_from_display('in')

        self.assertAlmostEqual(field.value, 2.0, delta=DELTA)
        self.assertAlmostEqual(field._value, 0.0508, delta=DELTA)

    def test_temperature_display_unchanged_internal_changes(self):
        """Temperature (scale) unit change keeps display constant."""
        field = UncertainField('Test', value=300.0, distr=Distributions.det,
                               unit_type=Temperature, unit='k')

        # Initial: 300 K displayed and internal
        self.assertAlmostEqual(field.value, 300.0, delta=DELTA)
        self.assertAlmostEqual(field._value, 300.0, delta=DELTA)

        field.set_unit_from_display('&deg;C')

        self.assertAlmostEqual(field.value, 300.0, delta=DELTA)
        self.assertAlmostEqual(field._value, 573.15, delta=0.01)


class TestUnitConversionWithDistributionParams(unittest.TestCase):
    """Tests that distribution parameters follow same unit conversion rules."""

    def test_normal_mean_std_follow_unit_change(self):
        """Mean and std display values stay constant on unit change."""
        field = UncertainField('Test', value=10.0, distr=Distributions.nor,
                               mean=5.0, std=1.0, unit_type=Pressure, unit='mpa')

        self.assertAlmostEqual(field.mean, 5.0, delta=DELTA)
        self.assertAlmostEqual(field.std, 1.0, delta=DELTA)

        field.set_unit_from_display('psi')

        self.assertAlmostEqual(field.mean, 5.0, delta=DELTA)
        self.assertAlmostEqual(field.std, 1.0, delta=DELTA)

        self.assertAlmostEqual(field._mean, 0.0345, delta=0.001)
        self.assertAlmostEqual(field._std, 0.00689, delta=0.0001)

    def test_uniform_bounds_follow_unit_change(self):
        """Lower/upper bounds display values stay constant on unit change."""
        field = UncertainField('Test', value=50.0, distr=Distributions.uni,
                               lower=10.0, upper=100.0, unit_type=Pressure, unit='mpa')

        self.assertAlmostEqual(field.lower, 10.0, delta=DELTA)
        self.assertAlmostEqual(field.upper, 100.0, delta=DELTA)

        field.set_unit_from_display('psi')

        self.assertAlmostEqual(field.lower, 10.0, delta=DELTA)
        self.assertAlmostEqual(field.upper, 100.0, delta=DELTA)

        self.assertAlmostEqual(field._lower, 0.0689, delta=0.001)
        self.assertAlmostEqual(field._upper, 0.689, delta=0.001)

    def test_truncated_normal_all_params_follow_unit_change(self):
        """All truncated normal params display values stay constant."""
        field = UncertainField('Test', value=50.0, distr=Distributions.tnor,
                               mean=50.0, std=10.0, lower=20.0, upper=80.0,
                               unit_type=Pressure, unit='mpa')

        field.set_unit_from_display('psi')

        self.assertAlmostEqual(field.value, 50.0, delta=DELTA)
        self.assertAlmostEqual(field.mean, 50.0, delta=DELTA)
        self.assertAlmostEqual(field.std, 10.0, delta=DELTA)
        self.assertAlmostEqual(field.lower, 20.0, delta=DELTA)
        self.assertAlmostEqual(field.upper, 80.0, delta=DELTA)

        # Internal values changed (now in MPa equivalent of psi values)
        self.assertAlmostEqual(field._value, 0.345, delta=0.01)
        self.assertAlmostEqual(field._mean, 0.345, delta=0.01)
        self.assertAlmostEqual(field._std, 0.0689, delta=0.001)
        self.assertAlmostEqual(field._lower, 0.138, delta=0.01)
        self.assertAlmostEqual(field._upper, 0.551, delta=0.01)


class TestTemperatureSpecialBehavior(unittest.TestCase):
    """Tests for temperature's special handling (scale vs difference)."""

    def test_temperature_mean_is_scale_value(self):
        """Temperature mean is treated as absolute scale value."""
        field = UncertainField('Test', value=300.0, distr=Distributions.nor,
                               mean=300.0, std=10.0, unit_type=Temperature, unit='k')

        field.set_unit_from_display('&deg;C')

        self.assertAlmostEqual(field.mean, 300.0, delta=DELTA)
        self.assertAlmostEqual(field._mean, 573.15, delta=0.01)

    def test_temperature_std_uses_scale_only(self):
        """Temperature std uses scale factor only, no offset.

        Standard deviation is a difference value, not an absolute temperature.
        A 10K spread equals a 10C spread (same scale size).
        """
        field = UncertainField('Test', value=300.0, distr=Distributions.nor,
                               mean=300.0, std=10.0, unit_type=Temperature, unit='k')

        field.set_unit_from_display('&deg;C')

        # Displayed std stays 10.0 (like other unit types)
        self.assertAlmostEqual(field.std, 10.0, delta=DELTA)

        # Internal std also stays 10.0 (K and C have same scale: 1K = 1C for differences)
        self.assertAlmostEqual(field._std, 10.0, delta=DELTA)


class TestUnitRoundTrip(unittest.TestCase):
    """Tests that changing unit and back preserves values."""

    def test_unit_round_trip_preserves_value(self):
        """Changing unit and back preserves the displayed value."""
        field = UncertainField('Test', value=50.0, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')

        original_value = field.value
        original_internal = field._value

        # Change to psi
        field.set_unit_from_display('psi')
        # Change back to MPa
        field.set_unit_from_display('MPa')

        # Displayed value should be back to original
        self.assertAlmostEqual(field.value, original_value, delta=DELTA)

        # Internal value should also be back (with potential small floating point error)
        self.assertAlmostEqual(field._value, original_internal, delta=DELTA)

    def test_distribution_params_round_trip(self):
        """Distribution params survive unit round trip."""
        field = UncertainField('Test', value=50.0, distr=Distributions.nor,
                               mean=50.0, std=10.0, unit_type=Pressure, unit='mpa')

        original_mean = field.mean
        original_std = field.std

        # Round trip
        field.set_unit_from_display('psi')
        field.set_unit_from_display('MPa')

        self.assertAlmostEqual(field.mean, original_mean, delta=DELTA)
        self.assertAlmostEqual(field.std, original_std, delta=DELTA)


class TestInternalStorageIsAlwaysSI(unittest.TestCase):
    """Tests that internal storage uses SI units regardless of display.

    NOTE: These tests use `unit=Pressure.psi` (enum only) rather than
    `unit_type=Pressure, unit='mpa'` (type + string) to test the alternate
    field creation path where unit_type is inferred from the unit enum.
    """

    def test_pressure_internal_is_mpa(self):
        """Internal pressure is always in MPa (SI) regardless of display unit."""
        # Create in psi
        field = UncertainField('Test', value=1000.0, distr=Distributions.det,
                               unit=Pressure.psi)

        # Internal should be in MPa: 1000 psi = 6.89 MPa
        self.assertAlmostEqual(field._value, 6.89, delta=0.1)

        # Displayed should be 1000 (psi)
        self.assertAlmostEqual(field.value, 1000.0, delta=DELTA)

    def test_distance_internal_is_meters(self):
        """Internal distance is always in meters (SI) regardless of display unit."""
        # Create in inches
        field = UncertainField('Test', value=24.0, distr=Distributions.det,
                               unit=Distance.inch)

        # Internal should be in meters: 24 inches = 0.6096 m
        self.assertAlmostEqual(field._value, 0.6096, delta=DELTA)

        # Displayed should be 24 (inches)
        self.assertAlmostEqual(field.value, 24.0, delta=DELTA)

    def test_temperature_internal_is_kelvin(self):
        """Internal temperature is always in Kelvin (SI) regardless of display unit."""
        # Create in Celsius
        field = UncertainField('Test', value=25.0, distr=Distributions.det,
                               unit=Temperature.c)

        # Internal should be in Kelvin: 25 C = 298.15 K
        self.assertAlmostEqual(field._value, 298.15, delta=0.01)

        # Displayed should be 25 (Celsius)
        self.assertAlmostEqual(field.value, 25.0, delta=DELTA)


if __name__ == '__main__':
    unittest.main()
