"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Regression tests for runtime distribution switching behavior.
This is a critical user workflow - users change distribution types via dropdown
and expect their previously-entered values to be preserved.
"""
import unittest

from ...models.fields_probabilistic import UncertainField
from ...utils.distributions import Distributions, DistributionParam as DP
from ...utils.units_of_measurement import Pressure, Temperature, Distance


DELTA = 1e-4


class TestDistributionSwitchingPreservesValues(unittest.TestCase):
    """
    Tests that switching distribution types preserves parameter values.

    Critical user workflow:
    1. User sets Normal distribution with mean=50, std=10
    2. User switches to Lognormal, enters mu=3, sigma=0.5
    3. User switches back to Normal
    4. Original mean=50, std=10 should still be there
    """

    def test_switch_normal_to_lognormal_and_back_preserves_normal_params(self):
        """Switching Normal → Lognormal → Normal preserves mean/std values."""
        field = UncertainField('Test', value=100, distr=Distributions.nor,
                               mean=50, std=10, unit_type=Pressure, unit='mpa')

        # Verify initial state
        self.assertEqual(field.distr, Distributions.nor)
        self.assertAlmostEqual(field.mean, 50, delta=DELTA)
        self.assertAlmostEqual(field.std, 10, delta=DELTA)

        # Switch to lognormal
        field.distr = Distributions.log
        field.mu = 3.0
        field.sigma = 0.5

        self.assertEqual(field.distr, Distributions.log)
        self.assertAlmostEqual(field.mu, 3.0, delta=DELTA)
        self.assertAlmostEqual(field.sigma, 0.5, delta=DELTA)

        # Switch back to normal
        field.distr = Distributions.nor

        self.assertEqual(field.distr, Distributions.nor)
        self.assertAlmostEqual(field.mean, 50, delta=DELTA)
        self.assertAlmostEqual(field.std, 10, delta=DELTA)

    def test_switch_lognormal_to_normal_and_back_preserves_lognormal_params(self):
        """Switching Lognormal → Normal → Lognormal preserves mu/sigma values."""
        field = UncertainField('Test', value=100, distr=Distributions.log,
                               mu=3.0, sigma=0.5, unit_type=Pressure, unit='mpa')

        # Verify initial state
        self.assertEqual(field.distr, Distributions.log)
        self.assertAlmostEqual(field.mu, 3.0, delta=DELTA)
        self.assertAlmostEqual(field.sigma, 0.5, delta=DELTA)

        # Switch to normal
        field.distr = Distributions.nor
        field.mean = 50
        field.std = 10

        self.assertEqual(field.distr, Distributions.nor)
        self.assertAlmostEqual(field.mean, 50, delta=DELTA)

        # Switch back
        field.distr = Distributions.log

        self.assertEqual(field.distr, Distributions.log)
        self.assertAlmostEqual(field.mu, 3.0, delta=DELTA)
        self.assertAlmostEqual(field.sigma, 0.5, delta=DELTA)

    def test_switch_truncated_normal_preserves_bounds(self):
        """Switching preserves lower/upper bounds for truncated distributions."""
        field = UncertainField('Test', value=50, distr=Distributions.tnor,
                               mean=50, std=10, lower=20, upper=80,
                               unit_type=Pressure, unit='mpa')

        self.assertAlmostEqual(field.lower, 20, delta=DELTA)
        self.assertAlmostEqual(field.upper, 80, delta=DELTA)

        field.distr = Distributions.det

        # Switch back to truncated normal
        field.distr = Distributions.tnor

        # Bounds should be preserved
        self.assertAlmostEqual(field.lower, 20, delta=DELTA)
        self.assertAlmostEqual(field.upper, 80, delta=DELTA)

    def test_switch_uniform_preserves_bounds(self):
        """Switching preserves lower/upper bounds for uniform distribution."""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               lower=20, upper=80,
                               unit_type=Pressure, unit='mpa')

        # Verify initial state
        self.assertAlmostEqual(field.lower, 20, delta=DELTA)
        self.assertAlmostEqual(field.upper, 80, delta=DELTA)

        field.distr = Distributions.nor
        field.mean = 50
        field.std = 10

        field.distr = Distributions.uni

        self.assertAlmostEqual(field.lower, 20, delta=DELTA)
        self.assertAlmostEqual(field.upper, 80, delta=DELTA)

    def test_switch_beta_preserves_alpha_beta(self):
        """Switching preserves alpha/beta parameters for beta distribution."""
        field = UncertainField('Test', value=0.5, distr=Distributions.beta,
                               alpha=2.0, beta=5.0,
                               unit_type=Pressure, unit='mpa')

        # Verify initial state
        self.assertAlmostEqual(field.alpha, 2.0, delta=DELTA)
        self.assertAlmostEqual(field.beta, 5.0, delta=DELTA)

        # Switch to and from
        field.distr = Distributions.det

        field.distr = Distributions.beta

        # Alpha/beta should be preserved
        self.assertAlmostEqual(field.alpha, 2.0, delta=DELTA)
        self.assertAlmostEqual(field.beta, 5.0, delta=DELTA)

    def test_switch_deterministic_to_probabilistic_and_back(self):
        """Common workflow: switch from deterministic to probabilistic and back."""
        field = UncertainField('Test', value=100, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')

        self.assertEqual(field.distr, Distributions.det)
        self.assertFalse(field.is_probabilistic)

        field.distr = Distributions.nor
        field.mean = 50
        field.std = 10

        self.assertTrue(field.is_probabilistic)
        self.assertAlmostEqual(field.mean, 50, delta=DELTA)
        self.assertAlmostEqual(field.std, 10, delta=DELTA)

        field.distr = Distributions.det

        self.assertFalse(field.is_probabilistic)

        # Switch to normal again, params preserved
        field.distr = Distributions.nor

        self.assertTrue(field.is_probabilistic)
        self.assertAlmostEqual(field.mean, 50, delta=DELTA)
        self.assertAlmostEqual(field.std, 10, delta=DELTA)


class TestAllDistributionTransitions(unittest.TestCase):
    """Test that all distribution type transitions work without error."""

    def test_det_to_all_other_distributions(self):
        """Deterministic can transition to all other distribution types."""
        for target in [Distributions.nor, Distributions.log, Distributions.tnor,
                       Distributions.tlog, Distributions.uni, Distributions.beta]:
            with self.subTest(target=target):
                field = UncertainField('Test', value=50, distr=Distributions.det,
                                       unit_type=Pressure, unit='mpa')
                field.distr = target
                self.assertEqual(field.distr, target)

    def test_nor_to_all_other_distributions(self):
        """Normal can transition to all other distribution types."""
        for target in [Distributions.det, Distributions.log, Distributions.tnor,
                       Distributions.tlog, Distributions.uni, Distributions.beta]:
            with self.subTest(target=target):
                field = UncertainField('Test', value=50, distr=Distributions.nor,
                                       mean=50, std=10, unit_type=Pressure, unit='mpa')
                field.distr = target
                self.assertEqual(field.distr, target)

    def test_log_to_all_other_distributions(self):
        """Lognormal can transition to all other distribution types."""
        for target in [Distributions.det, Distributions.nor, Distributions.tnor,
                       Distributions.tlog, Distributions.uni, Distributions.beta]:
            with self.subTest(target=target):
                field = UncertainField('Test', value=50, distr=Distributions.log,
                                       mu=3.0, sigma=0.5, unit_type=Pressure, unit='mpa')
                field.distr = target
                self.assertEqual(field.distr, target)

    def test_tnor_to_all_other_distributions(self):
        """Truncated normal can transition to all other distribution types."""
        for target in [Distributions.det, Distributions.nor, Distributions.log,
                       Distributions.tlog, Distributions.uni, Distributions.beta]:
            with self.subTest(target=target):
                field = UncertainField('Test', value=50, distr=Distributions.tnor,
                                       mean=50, std=10, lower=20, upper=80,
                                       unit_type=Pressure, unit='mpa')
                field.distr = target
                self.assertEqual(field.distr, target)

    def test_tlog_to_all_other_distributions(self):
        """Truncated lognormal can transition to all other distribution types."""
        for target in [Distributions.det, Distributions.nor, Distributions.log,
                       Distributions.tnor, Distributions.uni, Distributions.beta]:
            with self.subTest(target=target):
                field = UncertainField('Test', value=50, distr=Distributions.tlog,
                                       mu=3.0, sigma=0.5, lower=20, upper=80,
                                       unit_type=Pressure, unit='mpa')
                field.distr = target
                self.assertEqual(field.distr, target)

    def test_uni_to_all_other_distributions(self):
        """Uniform can transition to all other distribution types."""
        for target in [Distributions.det, Distributions.nor, Distributions.log,
                       Distributions.tnor, Distributions.tlog, Distributions.beta]:
            with self.subTest(target=target):
                field = UncertainField('Test', value=50, distr=Distributions.uni,
                                       lower=20, upper=80, unit_type=Pressure, unit='mpa')
                field.distr = target
                self.assertEqual(field.distr, target)

    def test_beta_to_all_other_distributions(self):
        """Beta can transition to all other distribution types."""
        for target in [Distributions.det, Distributions.nor, Distributions.log,
                       Distributions.tnor, Distributions.tlog, Distributions.uni]:
            with self.subTest(target=target):
                field = UncertainField('Test', value=0.5, distr=Distributions.beta,
                                       alpha=2.0, beta=5.0, unit_type=Pressure, unit='mpa')
                field.distr = target
                self.assertEqual(field.distr, target)

    def test_full_cycle_through_all_distributions(self):
        """Field can cycle through all distribution types and return to original."""
        field = UncertainField('Test', value=50, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')

        distribution_sequence = [
            Distributions.nor,
            Distributions.log,
            Distributions.tnor,
            Distributions.tlog,
            Distributions.uni,
            Distributions.beta,
            Distributions.det,  # Back to start
        ]

        for distr in distribution_sequence:
            field.distr = distr
            self.assertEqual(field.distr, distr)


class TestParameterVisibility(unittest.TestCase):
    """Tests for parameter visibility based on distribution type."""

    def test_deterministic_shows_only_nominal(self):
        """Deterministic distribution only shows nominal value."""
        field = UncertainField('Test', value=50, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')

        self.assertTrue(field.is_param_visible(DP.NOMINAL))
        self.assertFalse(field.is_param_visible(DP.MEAN))
        self.assertFalse(field.is_param_visible(DP.STD))
        self.assertFalse(field.is_param_visible(DP.MU))
        self.assertFalse(field.is_param_visible(DP.SIGMA))
        self.assertFalse(field.is_param_visible(DP.LOWER))
        self.assertFalse(field.is_param_visible(DP.UPPER))
        self.assertFalse(field.is_param_visible(DP.ALPHA))
        self.assertFalse(field.is_param_visible(DP.BETA))

    def test_normal_shows_nominal_mean_std(self):
        """Normal distribution shows nominal, mean, std."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, unit_type=Pressure, unit='mpa')

        self.assertTrue(field.is_param_visible(DP.NOMINAL))
        self.assertTrue(field.is_param_visible(DP.MEAN))
        self.assertTrue(field.is_param_visible(DP.STD))
        self.assertFalse(field.is_param_visible(DP.MU))
        self.assertFalse(field.is_param_visible(DP.SIGMA))
        self.assertFalse(field.is_param_visible(DP.LOWER))
        self.assertFalse(field.is_param_visible(DP.UPPER))

    def test_lognormal_shows_nominal_mu_sigma(self):
        """Lognormal distribution shows nominal, mu, sigma."""
        field = UncertainField('Test', value=50, distr=Distributions.log,
                               mu=3.0, sigma=0.5, unit_type=Pressure, unit='mpa')

        self.assertTrue(field.is_param_visible(DP.NOMINAL))
        self.assertFalse(field.is_param_visible(DP.MEAN))
        self.assertFalse(field.is_param_visible(DP.STD))
        self.assertTrue(field.is_param_visible(DP.MU))
        self.assertTrue(field.is_param_visible(DP.SIGMA))
        self.assertFalse(field.is_param_visible(DP.LOWER))
        self.assertFalse(field.is_param_visible(DP.UPPER))

    def test_truncated_normal_shows_nominal_mean_std_bounds(self):
        """Truncated normal shows nominal, mean, std, lower, upper."""
        field = UncertainField('Test', value=50, distr=Distributions.tnor,
                               mean=50, std=10, lower=20, upper=80,
                               unit_type=Pressure, unit='mpa')

        self.assertTrue(field.is_param_visible(DP.NOMINAL))
        self.assertTrue(field.is_param_visible(DP.MEAN))
        self.assertTrue(field.is_param_visible(DP.STD))
        self.assertFalse(field.is_param_visible(DP.MU))
        self.assertFalse(field.is_param_visible(DP.SIGMA))
        self.assertTrue(field.is_param_visible(DP.LOWER))
        self.assertTrue(field.is_param_visible(DP.UPPER))

    def test_truncated_lognormal_shows_nominal_mu_sigma_bounds(self):
        """Truncated lognormal shows nominal, mu, sigma, lower, upper."""
        field = UncertainField('Test', value=50, distr=Distributions.tlog,
                               mu=3.0, sigma=0.5, lower=20, upper=80,
                               unit_type=Pressure, unit='mpa')

        self.assertTrue(field.is_param_visible(DP.NOMINAL))
        self.assertFalse(field.is_param_visible(DP.MEAN))
        self.assertFalse(field.is_param_visible(DP.STD))
        self.assertTrue(field.is_param_visible(DP.MU))
        self.assertTrue(field.is_param_visible(DP.SIGMA))
        self.assertTrue(field.is_param_visible(DP.LOWER))
        self.assertTrue(field.is_param_visible(DP.UPPER))

    def test_uniform_shows_nominal_bounds(self):
        """Uniform distribution shows nominal, lower, upper."""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               lower=20, upper=80, unit_type=Pressure, unit='mpa')

        self.assertTrue(field.is_param_visible(DP.NOMINAL))
        self.assertFalse(field.is_param_visible(DP.MEAN))
        self.assertFalse(field.is_param_visible(DP.STD))
        self.assertFalse(field.is_param_visible(DP.MU))
        self.assertFalse(field.is_param_visible(DP.SIGMA))
        self.assertTrue(field.is_param_visible(DP.LOWER))
        self.assertTrue(field.is_param_visible(DP.UPPER))

    def test_beta_shows_nominal_alpha_beta(self):
        """Beta distribution shows nominal, alpha, beta."""
        field = UncertainField('Test', value=0.5, distr=Distributions.beta,
                               alpha=2.0, beta=5.0, unit_type=Pressure, unit='mpa')

        self.assertTrue(field.is_param_visible(DP.NOMINAL))
        self.assertFalse(field.is_param_visible(DP.MEAN))
        self.assertFalse(field.is_param_visible(DP.STD))
        self.assertFalse(field.is_param_visible(DP.MU))
        self.assertFalse(field.is_param_visible(DP.SIGMA))
        self.assertFalse(field.is_param_visible(DP.LOWER))
        self.assertFalse(field.is_param_visible(DP.UPPER))
        self.assertTrue(field.is_param_visible(DP.ALPHA))
        self.assertTrue(field.is_param_visible(DP.BETA))

    def test_nominal_hidden_when_use_nominal_false(self):
        """Nominal parameter hidden when use_nominal=False."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, use_nominal=False,
                               unit_type=Pressure, unit='mpa')

        self.assertFalse(field.is_param_visible(DP.NOMINAL))
        self.assertTrue(field.is_param_visible(DP.MEAN))
        self.assertTrue(field.is_param_visible(DP.STD))

    def test_visibility_updates_when_distribution_changes(self):
        """Parameter visibility updates correctly when distribution changes."""
        field = UncertainField('Test', value=50, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')

        # Initially deterministic
        self.assertFalse(field.is_param_visible(DP.MEAN))

        # Switch to normal
        field.distr = Distributions.nor
        self.assertTrue(field.is_param_visible(DP.MEAN))
        self.assertTrue(field.is_param_visible(DP.STD))
        self.assertFalse(field.is_param_visible(DP.MU))

        # Switch to lognormal
        field.distr = Distributions.log
        self.assertFalse(field.is_param_visible(DP.MEAN))
        self.assertFalse(field.is_param_visible(DP.STD))
        self.assertTrue(field.is_param_visible(DP.MU))
        self.assertTrue(field.is_param_visible(DP.SIGMA))


if __name__ == '__main__':
    unittest.main()
