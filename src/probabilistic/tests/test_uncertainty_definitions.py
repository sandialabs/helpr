# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np

from probabilistic.capabilities import uncertainty_definitions as Uncertainty


class UncertaintyDefinitionTestCase(unittest.TestCase):
    """class for unit tests of uncertainty definition module"""
    def setUp(self) -> None:
        """function to specify common inputs for uncertainty definition module"""
        self.random_state = np.random.default_rng()

    def tearDown(self) -> None:
        """teardown function"""

    def test_distribution_specification_function(self):
        """unit test for distribution specification function"""
        dist1 = Uncertainty.specify_distribution({'distribution_type': 'normal',
                                      'name': 'specified',
                                      'uncertainty_type': 'aleatory',
                                      'nominal_value': 1,
                                      'mean': .5,
                                      'std_deviation': .3})
        dist2 = Uncertainty.NormalDistribution(name='test var1',
                                               uncertainty_type='aleatory',
                                               nominal_value=1,
                                               mean=.5,
                                               std_deviation=.3)
        self.assertEqual(dist1.distribution.dist.name, dist2.distribution.dist.name)

    def test_parameter_information_extraction(self):
        """unit test of printing out distribution information"""
        uncertain_var1 = Uncertainty.NormalDistribution(name='test var1',
                                                        uncertainty_type='aleatory',
                                                        nominal_value=1,
                                                        mean=.5,
                                                        std_deviation=.3)
        deterministic_var2 = Uncertainty.DeterministicCharacterization(name='test var2',
                                                                       value=4)

        var1_string = "test var1 is a probabilistic variable represented with a norm distribution and parameters {'loc': 0.5, 'scale': 0.3}"
        var2_string = 'test var2 is a deterministic variable with value 4'
        self.assertEqual(var1_string, str(uncertain_var1))
        self.assertEqual(var2_string, str(deterministic_var2))

        var1_repr = 'test var1, norm, 1, aleatory, 0.5, 0.3'
        var2_repr = 'test var2, deterministic, 4'
        self.assertEqual(var1_repr, repr(uncertain_var1))
        self.assertEqual(var2_repr, repr(deterministic_var2))

    def test_sample_uncertainty_definition(self):
        """unit test of sampling from uncertainty definitions"""
        num_samples1 = 10
        uncertain_var1 = Uncertainty.NormalDistribution(name='test var1',
                                                        uncertainty_type='aleatory',
                                                        nominal_value=1,
                                                        mean=.5,
                                                        std_deviation=.3)
        self.assertEqual(len(uncertain_var1.generate_samples(num_samples1,
                                                             self.random_state)),
                                                             num_samples1)
        self.assertEqual(uncertain_var1.distribution.mean(), .5)
        self.assertEqual(uncertain_var1.distribution.std(), .3)

        uncertain_var1b = Uncertainty.NormalDistribution(name='test var1b',
                                                        uncertainty_type='aleatory',
                                                        nominal_value=1,
                                                        mean=.5,
                                                        std_deviation=.3)
        self.assertEqual(len(uncertain_var1b.generate_samples(num_samples1,
                                                              self.random_state)),
                                                              num_samples1)
        self.assertEqual(uncertain_var1b.distribution.mean(), .5)
        self.assertEqual(uncertain_var1b.distribution.std(), .3)

        num_samples2 = 7
        uncertain_var2 = Uncertainty.LognormalDistribution(name='test var2',
                                                        uncertainty_type='epistemic',
                                                        nominal_value=1,
                                                        mu=.5,
                                                        sigma=.3)
        self.assertEqual(len(uncertain_var2.generate_samples(num_samples2,
                                                             self.random_state)),
                                                             num_samples2)
        self.assertEqual(uncertain_var2.distribution.median(), np.exp(.5))
        self.assertAlmostEqual(uncertain_var2.distribution.var(),
                               (np.exp(.3**2) - 1)*(np.exp(2*.5 + .3**2)))

        num_samples3 = 13
        uncertain_var3 = Uncertainty.UniformDistribution(name='test var3',
                                                        nominal_value=1,
                                                        lower_bound=-1,
                                                        upper_bound=3,
                                                        uncertainty_type='epistemic')
        self.assertEqual(len(uncertain_var3.generate_samples(num_samples3,
                                                             self.random_state)),
                                                             num_samples3)
        self.assertEqual(uncertain_var3.distribution.mean(), 1)
        self.assertEqual(uncertain_var3.distribution.std(), np.sqrt(4/3))

    def test_distribution_pdf_plotting(self):
        """unit test to ensure pdf plotting of distributions does not error"""
        uncertain_var1 = Uncertainty.NormalDistribution(name='test var1',
                                                uncertainty_type='aleatory',
                                                nominal_value=1,
                                                mean=.5,
                                                std_deviation=.3)
        uncertain_var1.plot_distribution()
        assert True

if __name__ == '__main__':
    unittest.main()
