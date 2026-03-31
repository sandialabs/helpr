"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Regression tests for UncertainField validation behavior.
Tests ensure validation rules are applied correctly for all distribution types.
"""
import unittest

from ...models.fields_probabilistic import UncertainField
from ...utils.distributions import Distributions
from ...utils.units_of_measurement import Pressure, Temperature
from ...utils.helpers import InputStatus


class TestValueBoundsValidation(unittest.TestCase):
    """Tests for min/max value validation."""

    def test_value_below_minimum_fails(self):
        """Value below min_value should fail validation."""
        field = UncertainField('Test', value=5, min_value=10, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_value_above_maximum_fails(self):
        """Value above max_value should fail validation."""
        field = UncertainField('Test', value=150, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_value_at_minimum_passes(self):
        """Value exactly at min_value should pass validation."""
        field = UncertainField('Test', value=10, min_value=10, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.GOOD)

    def test_value_at_maximum_passes(self):
        """Value exactly at max_value should pass validation."""
        field = UncertainField('Test', value=100, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.GOOD)

    def test_value_in_range_passes(self):
        """Value within min/max range should pass validation."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.GOOD)


class TestNormalDistributionValidation(unittest.TestCase):
    """Tests for normal distribution parameter validation."""

    def test_negative_std_fails_validation(self):
        """Negative standard deviation should be accepted by setter but fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        field.std = -5
        self.assertEqual(field.std, -5)
        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_zero_std_fails_validation(self):
        """Zero standard deviation should be accepted by setter but fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        field.std = 0
        self.assertEqual(field.std, 0)
        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_valid_normal_passes(self):
        """Valid normal distribution should pass validation."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.GOOD)

    def test_mean_below_min_fails(self):
        """Mean below min_value should fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=-5, std=10, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_mean_above_max_fails(self):
        """Mean above max_value should fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=150, std=10, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)


class TestTruncatedDistributionValidation(unittest.TestCase):
    """Tests for truncated distribution bounds validation."""

    def test_lower_above_upper_fails(self):
        """Lower bound above upper bound should fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               lower=80, upper=20, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_lower_equal_upper_passes(self):
        """Lower bound equal to upper bound may pass (degenerate but valid)."""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               lower=50, upper=50, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertIn(result.status, [InputStatus.GOOD, InputStatus.WARN])

    def test_valid_uniform_passes(self):
        """Valid uniform distribution should pass validation."""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               lower=20, upper=80, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.GOOD)

    def test_lower_below_min_fails(self):
        """Lower bound below min_value should fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               lower=-10, upper=80, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_upper_above_max_fails(self):
        """Upper bound above max_value should fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               lower=20, upper=150, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_truncated_normal_valid(self):
        """Valid truncated normal should pass validation."""
        field = UncertainField('Test', value=50, distr=Distributions.tnor,
                               mean=50, std=10, lower=20, upper=80,
                               min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.GOOD)

    def test_truncated_normal_bounds_reversed_fails(self):
        """Truncated normal with reversed bounds should fail."""
        field = UncertainField('Test', value=50, distr=Distributions.tnor,
                               mean=50, std=10, lower=80, upper=20,
                               min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)


class TestLognormalDistributionValidation(unittest.TestCase):
    """Tests for lognormal distribution parameter validation."""

    def test_negative_sigma_fails_validation(self):
        """Negative sigma should be accepted by setter but fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.log,
                               mu=3.9, sigma=0.2, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        field.sigma = -0.5
        self.assertEqual(field.sigma, -0.5)
        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_zero_sigma_fails_validation(self):
        """Zero sigma should be accepted by setter but fail validation."""
        field = UncertainField('Test', value=50, distr=Distributions.log,
                               mu=3.9, sigma=0.2, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        field.sigma = 0.0
        self.assertEqual(field.sigma, 0.0)
        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)

    def test_valid_lognormal_passes(self):
        """Valid lognormal distribution should pass validation."""
        field = UncertainField('Test', value=50, distr=Distributions.log,
                               mu=3.9, sigma=0.2, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.GOOD)


class TestBetaDistributionValidation(unittest.TestCase):
    """Tests for beta distribution parameter validation.

    Alpha and beta are shape parameters that must be positive (> 0).
    They are dimensionless and independent of the field's value range.
    """

    def test_alpha_rejects_non_positive(self):
        """Alpha setter rejects non-positive values."""
        field = UncertainField('Test', value=0.5, distr=Distributions.beta,
                               alpha=2.0, beta=5.0, min_value=0, max_value=1,
                               unit_type=Pressure, unit='mpa')

        original_alpha = field.alpha

        field.alpha = 0.0
        self.assertEqual(field.alpha, original_alpha)

        field.alpha = -1.0
        self.assertEqual(field.alpha, original_alpha)

    def test_beta_rejects_non_positive(self):
        """Beta setter rejects non-positive values."""
        field = UncertainField('Test', value=0.5, distr=Distributions.beta,
                               alpha=2.0, beta=5.0, min_value=0, max_value=1,
                               unit_type=Pressure, unit='mpa')

        original_beta = field.beta

        field.beta = 0.0
        self.assertEqual(field.beta, original_beta)

        field.beta = -1.0
        self.assertEqual(field.beta, original_beta)

    def test_alpha_beta_independent_of_value_range(self):
        """Alpha/beta are dimensionless shape params, not constrained by value range."""
        # Even with max_value=1, alpha/beta can be > 1
        field = UncertainField('Test', value=0.5, distr=Distributions.beta,
                               alpha=2.0, beta=5.0, min_value=0, max_value=1,
                               unit_type=Pressure, unit='mpa')

        # Shape parameters can exceed the value range
        self.assertAlmostEqual(field.alpha, 2.0, delta=0.01)
        self.assertAlmostEqual(field.beta, 5.0, delta=0.01)

    def test_valid_beta_passes(self):
        """Valid beta distribution should pass validation."""
        field = UncertainField('Test', value=0.5, distr=Distributions.beta,
                               alpha=2.0, beta=5.0, min_value=0, max_value=1,
                               unit_type=Pressure, unit='mpa')

        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.GOOD)

    def test_small_positive_alpha_beta_accepted(self):
        """Small positive alpha/beta values are accepted."""
        field = UncertainField('Test', value=0.5, distr=Distributions.beta,
                               alpha=0.5, beta=0.5, min_value=0, max_value=1,
                               unit_type=Pressure, unit='mpa')

        field.alpha = 0.1
        field.beta = 0.1

        self.assertAlmostEqual(field.alpha, 0.1, delta=0.01)
        self.assertAlmostEqual(field.beta, 0.1, delta=0.01)


class TestValidationStateTransitions(unittest.TestCase):
    """Tests for validation state changes when parameters change."""

    def test_value_setter_rejects_out_of_range(self):
        """Value setter silently rejects out-of-range values.

        NOTE: The setter checks in_range_raw() and only updates if value is valid.
        This means setting an invalid value has no effect - the old value is retained.
        """
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')

        # Initially valid
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)
        self.assertEqual(field.value, 50)

        field.value = 150

        # Value remains unchanged
        self.assertEqual(field.value, 50)
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

    def test_valid_value_change_is_accepted(self):
        """Value setter accepts valid values within range."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')

        field.value = 75
        self.assertEqual(field.value, 75)
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

    def test_validation_updates_on_distribution_change(self):
        """Validation state updates when distribution changes."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')

        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        # Change to normal with invalid mean (set internal value directly to bypass setter check)
        field.distr = Distributions.nor
        field._mean = 150

        # Should be invalid due to mean
        result = field.check_valid()
        self.assertEqual(result.status, InputStatus.ERROR)


if __name__ == '__main__':
    unittest.main()
