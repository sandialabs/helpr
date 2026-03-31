"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Regression tests for UncertainField serialization (to_dict/from_dict).
Ensures data can be saved and restored correctly across all distribution types.
"""
import unittest

from ...models.fields_probabilistic import UncertainField
from ...utils.distributions import Distributions, Uncertainties
from ...utils.units_of_measurement import Pressure, Temperature, Distance


DELTA = 1e-4


class TestSerializationRoundTrip(unittest.TestCase):
    """Tests for to_dict/from_dict round-trip for all distribution types."""

    def _assert_field_equal(self, field1: UncertainField, field2: UncertainField):
        """Assert two UncertainField instances have equivalent values."""
        self.assertEqual(field1.distr, field2.distr)
        self.assertAlmostEqual(field1.value, field2.value, delta=DELTA)

        # Check distribution-specific params
        if field1.distr in [Distributions.nor, Distributions.tnor]:
            self.assertAlmostEqual(field1.mean, field2.mean, delta=DELTA)
            self.assertAlmostEqual(field1.std, field2.std, delta=DELTA)

        if field1.distr in [Distributions.log, Distributions.tlog]:
            self.assertAlmostEqual(field1.mu, field2.mu, delta=DELTA)
            self.assertAlmostEqual(field1.sigma, field2.sigma, delta=DELTA)

        if field1.distr in [Distributions.tnor, Distributions.tlog, Distributions.uni]:
            self.assertAlmostEqual(field1.lower, field2.lower, delta=DELTA)
            self.assertAlmostEqual(field1.upper, field2.upper, delta=DELTA)

        if field1.distr == Distributions.beta:
            self.assertAlmostEqual(field1.alpha, field2.alpha, delta=DELTA)
            self.assertAlmostEqual(field1.beta, field2.beta, delta=DELTA)

    def test_round_trip_deterministic(self):
        """Deterministic distribution round-trips correctly."""
        field = UncertainField('Test Pressure', value=50.0, distr=Distributions.det,
                               min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        field2 = UncertainField('Restored', value=0, unit_type=Pressure, unit='mpa')
        field2.from_dict(data)

        self._assert_field_equal(field, field2)
        self.assertEqual(field2.distr, Distributions.det)

    def test_round_trip_normal(self):
        """Normal distribution round-trips correctly."""
        field = UncertainField('Test Pressure', value=50.0, distr=Distributions.nor,
                               mean=50.0, std=10.0,
                               min_value=0, max_value=100,
                               uncertainty=Uncertainties.ale,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        field2 = UncertainField('Restored', value=0, unit_type=Pressure, unit='mpa')
        field2.from_dict(data)

        self._assert_field_equal(field, field2)
        self.assertEqual(field2.distr, Distributions.nor)
        self.assertAlmostEqual(field2.mean, 50.0, delta=DELTA)
        self.assertAlmostEqual(field2.std, 10.0, delta=DELTA)

    def test_round_trip_lognormal(self):
        """Lognormal distribution round-trips correctly."""
        field = UncertainField('Test Pressure', value=50.0, distr=Distributions.log,
                               mu=3.912, sigma=0.2,
                               min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        field2 = UncertainField('Restored', value=0, unit_type=Pressure, unit='mpa')
        field2.from_dict(data)

        self._assert_field_equal(field, field2)
        self.assertEqual(field2.distr, Distributions.log)
        self.assertAlmostEqual(field2.mu, 3.912, delta=DELTA)
        self.assertAlmostEqual(field2.sigma, 0.2, delta=DELTA)

    def test_round_trip_truncated_normal(self):
        """Truncated normal distribution round-trips correctly."""
        field = UncertainField('Test Pressure', value=50.0, distr=Distributions.tnor,
                               mean=50.0, std=10.0, lower=20.0, upper=80.0,
                               min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        field2 = UncertainField('Restored', value=0, unit_type=Pressure, unit='mpa')
        field2.from_dict(data)

        self._assert_field_equal(field, field2)
        self.assertEqual(field2.distr, Distributions.tnor)
        self.assertAlmostEqual(field2.mean, 50.0, delta=DELTA)
        self.assertAlmostEqual(field2.std, 10.0, delta=DELTA)
        self.assertAlmostEqual(field2.lower, 20.0, delta=DELTA)
        self.assertAlmostEqual(field2.upper, 80.0, delta=DELTA)

    def test_round_trip_truncated_lognormal(self):
        """Truncated lognormal distribution round-trips correctly."""
        field = UncertainField('Test Pressure', value=50.0, distr=Distributions.tlog,
                               mu=3.912, sigma=0.2, lower=30.0, upper=70.0,
                               min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        field2 = UncertainField('Restored', value=0, unit_type=Pressure, unit='mpa')
        field2.from_dict(data)

        self._assert_field_equal(field, field2)
        self.assertEqual(field2.distr, Distributions.tlog)
        self.assertAlmostEqual(field2.mu, 3.912, delta=DELTA)
        self.assertAlmostEqual(field2.sigma, 0.2, delta=DELTA)
        self.assertAlmostEqual(field2.lower, 30.0, delta=DELTA)
        self.assertAlmostEqual(field2.upper, 70.0, delta=DELTA)

    def test_round_trip_uniform(self):
        """Uniform distribution round-trips correctly."""
        field = UncertainField('Test Pressure', value=50.0, distr=Distributions.uni,
                               lower=20.0, upper=80.0,
                               min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        field2 = UncertainField('Restored', value=0, unit_type=Pressure, unit='mpa')
        field2.from_dict(data)

        self._assert_field_equal(field, field2)
        self.assertEqual(field2.distr, Distributions.uni)
        self.assertAlmostEqual(field2.lower, 20.0, delta=DELTA)
        self.assertAlmostEqual(field2.upper, 80.0, delta=DELTA)

    def test_round_trip_beta(self):
        """Beta distribution round-trips correctly."""
        field = UncertainField('Test Fraction', value=0.5, distr=Distributions.beta,
                               alpha=2.0, beta=5.0,
                               min_value=0, max_value=1,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        field2 = UncertainField('Restored', value=0, unit_type=Pressure, unit='mpa')
        field2.from_dict(data)

        self._assert_field_equal(field, field2)
        self.assertEqual(field2.distr, Distributions.beta)
        self.assertAlmostEqual(field2.alpha, 2.0, delta=DELTA)
        self.assertAlmostEqual(field2.beta, 5.0, delta=DELTA)


class TestSerializationContents(unittest.TestCase):
    """Tests for the contents of serialized data."""

    def test_deterministic_has_no_distribution_params(self):
        """Deterministic serialization excludes distribution parameters."""
        field = UncertainField('Test', value=50, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        # Should not have distribution-specific keys
        self.assertNotIn('mean', data)
        self.assertNotIn('std', data)
        self.assertNotIn('mu', data)
        self.assertNotIn('sigma', data)
        self.assertNotIn('lower', data)
        self.assertNotIn('upper', data)
        self.assertNotIn('alpha', data)
        # 'beta' key may exist in data dict as 'beta' distribution param

    def test_normal_has_mean_std(self):
        """Normal serialization includes mean and std."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        self.assertIn('mean', data)
        self.assertIn('std', data)
        self.assertAlmostEqual(data['mean'], 50, delta=DELTA)
        self.assertAlmostEqual(data['std'], 10, delta=DELTA)

    def test_lognormal_has_mu_sigma(self):
        """Lognormal serialization includes mu and sigma."""
        field = UncertainField('Test', value=50, distr=Distributions.log,
                               mu=3.912, sigma=0.2, unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        self.assertIn('mu', data)
        self.assertIn('sigma', data)
        self.assertAlmostEqual(data['mu'], 3.912, delta=DELTA)
        self.assertAlmostEqual(data['sigma'], 0.2, delta=DELTA)

    def test_truncated_has_bounds(self):
        """Truncated distributions include lower and upper bounds."""
        field = UncertainField('Test', value=50, distr=Distributions.tnor,
                               mean=50, std=10, lower=20, upper=80,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        self.assertIn('lower', data)
        self.assertIn('upper', data)
        self.assertAlmostEqual(data['lower'], 20, delta=DELTA)
        self.assertAlmostEqual(data['upper'], 80, delta=DELTA)

    def test_serialization_stores_in_standard_units(self):
        """Values are stored in standard units (SI)."""
        # Create field in psi (non-standard)
        field = UncertainField('Test', value=145.038, distr=Distributions.det,
                               unit=Pressure.psi)

        data = field.to_dict()

        # Value should be stored in MPa (standard), approximately 1.0
        self.assertAlmostEqual(data['value'], 1.0, delta=0.01)

    def test_distribution_params_stored_in_standard_units(self):
        """Distribution parameters (mean, std, bounds) are stored in SI units."""
        # Create normal distribution field in psi (non-standard)
        # 1000 psi ≈ 6.89 MPa
        field = UncertainField('Test', value=1000.0, distr=Distributions.nor,
                               mean=1000.0, std=100.0,
                               unit=Pressure.psi)

        data = field.to_dict()

        # All values should be stored in MPa (SI)
        self.assertAlmostEqual(data['value'], 6.89, delta=0.1)
        self.assertAlmostEqual(data['mean'], 6.89, delta=0.1)
        self.assertAlmostEqual(data['std'], 0.689, delta=0.01)

    def test_bounds_stored_in_standard_units(self):
        """Truncation bounds are stored in SI units."""
        # Create uniform distribution field in psi
        # 500 psi ≈ 3.45 MPa, 1500 psi ≈ 10.34 MPa
        field = UncertainField('Test', value=1000.0, distr=Distributions.uni,
                               lower=500.0, upper=1500.0,
                               unit=Pressure.psi)

        data = field.to_dict()

        # Bounds should be stored in MPa (SI)
        self.assertAlmostEqual(data['lower'], 3.45, delta=0.1)
        self.assertAlmostEqual(data['upper'], 10.34, delta=0.1)

    def test_required_keys_present(self):
        """All required keys are present in serialized data."""
        field = UncertainField('Test Parameter', value=50, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')

        data = field.to_dict()

        required_keys = ['label', 'slug', 'unit_type', 'unit', 'value', 'min_value', 'max_value', 'distr']

        for key in required_keys:
            self.assertIn(key, data, f"Missing required key: {key}")


class TestLoadFromSavedFormat(unittest.TestCase):
    """Tests for loading from saved .hpr file format."""

    def test_load_deterministic_from_saved_format(self):
        """Can load deterministic field from saved file format."""
        saved_data = {
            'label': 'Outer Diameter',
            'slug': 'outer_diameter',
            'value': 0.5,
            'min_value': '0',
            'max_value': '10',
            'unit_type': 'dist_sm',
            'unit': 'm',
            'distr': 'det',
            'uncertainty': 'ale',  # Required key even for deterministic
        }

        field = UncertainField('Test', value=0, unit_type=Distance, unit='m')
        field.from_dict(saved_data)

        self.assertEqual(field.distr, Distributions.det)
        self.assertAlmostEqual(field.value, 0.5, delta=DELTA)

    def test_load_normal_from_saved_format(self):
        """Can load normal distribution from saved file format."""
        saved_data = {
            'label': 'Pressure',
            'slug': 'pressure',
            'value': 50.0,
            'min_value': '0',
            'max_value': '100',
            'unit_type': 'pres',
            'unit': 'mpa',
            'distr': 'nor',
            'uncertainty': 'ale',
            'mean': 50.0,
            'std': 10.0,
        }

        field = UncertainField('Test', value=0, unit_type=Pressure, unit='mpa')
        field.from_dict(saved_data)

        self.assertEqual(field.distr, Distributions.nor)
        self.assertAlmostEqual(field.value, 50.0, delta=DELTA)
        self.assertAlmostEqual(field.mean, 50.0, delta=DELTA)
        self.assertAlmostEqual(field.std, 10.0, delta=DELTA)
        self.assertEqual(field.uncertainty, Uncertainties.ale)

    def test_load_truncated_lognormal_from_saved_format(self):
        """Can load truncated lognormal from saved file format."""
        saved_data = {
            'label': 'Test Param',
            'slug': 'test_param',
            'value': 50.0,
            'min_value': '0',
            'max_value': '100',
            'unit_type': 'pres',
            'unit': 'mpa',
            'distr': 'tlog',
            'uncertainty': 'epi',
            'mu': 3.912,
            'sigma': 0.2,
            'lower': 30.0,
            'upper': 70.0,
        }

        field = UncertainField('Test', value=0, unit_type=Pressure, unit='mpa')
        field.from_dict(saved_data)

        self.assertEqual(field.distr, Distributions.tlog)
        self.assertAlmostEqual(field.mu, 3.912, delta=DELTA)
        self.assertAlmostEqual(field.sigma, 0.2, delta=DELTA)
        self.assertAlmostEqual(field.lower, 30.0, delta=DELTA)
        self.assertAlmostEqual(field.upper, 70.0, delta=DELTA)
        self.assertEqual(field.uncertainty, Uncertainties.epi)

    def test_load_uniform_from_saved_format(self):
        """Can load uniform distribution from saved file format."""
        saved_data = {
            'label': 'Test Param',
            'slug': 'test_param',
            'value': 50.0,
            'min_value': '0',
            'max_value': '100',
            'unit_type': 'pres',
            'unit': 'mpa',
            'distr': 'uni',
            'uncertainty': 'ale',
            'lower': 20.0,
            'upper': 80.0,
        }

        field = UncertainField('Test', value=0, unit_type=Pressure, unit='mpa')
        field.from_dict(saved_data)

        self.assertEqual(field.distr, Distributions.uni)
        self.assertAlmostEqual(field.lower, 20.0, delta=DELTA)
        self.assertAlmostEqual(field.upper, 80.0, delta=DELTA)

    def test_load_beta_from_saved_format(self):
        """Can load beta distribution from saved file format."""
        saved_data = {
            'label': 'Test Param',
            'slug': 'test_param',
            'value': 0.5,
            'min_value': '0',
            'max_value': '1',
            'unit_type': 'pres',
            'unit': 'mpa',
            'distr': 'beta',
            'uncertainty': 'ale',
            'alpha': 2.0,
            'beta': 5.0,
        }

        field = UncertainField('Test', value=0, unit_type=Pressure, unit='mpa')
        field.from_dict(saved_data)

        self.assertEqual(field.distr, Distributions.beta)
        self.assertAlmostEqual(field.alpha, 2.0, delta=DELTA)
        self.assertAlmostEqual(field.beta, 5.0, delta=DELTA)


if __name__ == '__main__':
    unittest.main()
