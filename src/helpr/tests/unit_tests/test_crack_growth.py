# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np

from helpr.physics.crack_growth import CrackGrowth, get_design_curve
from helpr.physics.environment import EnvironmentSpecification


class CrackGrowthTestCase(unittest.TestCase):
    """Class for units tests of crack growth module"""
    def setUp(self):
        """function to specify common inputs to crack growth module"""
        self.max_pressure = 13
        self.min_pressure = 11
        self.temperature = 300
        self.delta_k = 0.1
        self.delta_a = 0.1
        self.delta_n = 10
        self.growth_model_specification = {'model_name': 'code_case_2938'}
        self.environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                                    min_pressure=self.min_pressure,
                                                    temperature=self.temperature)

    def tearDown(self):
        """teardown function"""

    def test_default(self):
        """unit test of default behavior of crack growth module"""
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification=self.growth_model_specification)
        with self.assertRaises(ValueError):
            test_crack.calc_delta_n()

        test_crack.update_delta_k_delta_a(self.delta_k, self.delta_a)
        self.assertGreater(test_crack.calc_delta_n(), 0)
        test_crack.update_delta_k_delta_a(0, 0)
        self.assertEqual(test_crack.calc_delta_n(), 0)
        test_crack.update_delta_k_delta_n(self.delta_k, self.delta_n)
        self.assertGreater(test_crack.calc_delta_a(), 0)
        test_crack.update_delta_k_delta_n(0, 0)
        self.assertEqual(test_crack.calc_delta_a(), 0)

    def test_input_types(self):
        """unit test for passing lists of inputs to crack growth module"""
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification=self.growth_model_specification)
        test_crack.update_delta_k_delta_a(.1, .1)
        delta_n_scalar = test_crack.calc_delta_n()

        environment = EnvironmentSpecification(max_pressure=[5, self.max_pressure],
                                               min_pressure=[1, self.min_pressure],
                                               temperature=[300, self.temperature],
                                               sample_size=2)
        test_crack = CrackGrowth(environment=environment,
                                 growth_model_specification=self.growth_model_specification,
                                 sample_size=2)
        test_crack.update_delta_k_delta_a(np.array([0.5, self.delta_k]),
                                        np.array([0.2, self.delta_a]))
        delta_array = test_crack.calc_delta_n()

        self.assertNotEqual(delta_n_scalar, delta_array[0])
        self.assertEqual(delta_n_scalar, delta_array[1])

    def test_0pct_h2(self):
        """unit test for having no hydrogen in crack growth calculations"""
        environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                               min_pressure=self.min_pressure,
                                               temperature=self.temperature,
                                               volume_fraction_h2=0)
        test_crack = CrackGrowth(environment=environment,
                                 growth_model_specification=self.growth_model_specification)
        test_crack.update_delta_k_delta_a(self.delta_k, self.delta_a)

        self.assertEqual(test_crack.calc_delta_n(), test_crack.calc_air_curve_dn())

    def test_100pct_h2(self):
        """unit test that crack growth following ASME curve"""
        environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                               min_pressure=self.min_pressure,
                                               temperature=self.temperature,
                                               volume_fraction_h2=1)
        test_crack = CrackGrowth(environment=environment,
                                 growth_model_specification=self.growth_model_specification)
        
        test_crack.update_delta_k_delta_a(delta_k=1, delta_a=self.delta_a)
        self.assertEqual(test_crack.calc_delta_n(), test_crack.calc_air_curve_dn())
        test_crack.update_delta_k_delta_a(delta_k=10, delta_a=self.delta_a)
        self.assertEqual(test_crack.calc_delta_n(), test_crack.calc_code_case_2938_dn_lower_k())
        test_crack.update_delta_k_delta_a(delta_k=100, delta_a=self.delta_a)
        self.assertEqual(test_crack.calc_delta_n(), test_crack.calc_code_case_2938_dn_higher_k())


    def test_invalid_fugacity_correction_case(self):
        """unit test of passing invalid input to fugacity correction"""
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification=self.growth_model_specification)

        with self.assertRaises(ValueError):
            test_crack.calc_fugacity_correction(p=1.5E-11, multiplier=3.66, case='')

    def test_specify_paris_law_crack_growth(self):
        """unit test of specifying inputs for a paris law crack growth model"""
        c_parameter = 1
        m_parameter = 2
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification={'model_name': 'paris_law',
                                                              'c': c_parameter,
                                                              'm': m_parameter})

        test_crack.update_delta_k_delta_a(self.delta_k, self.delta_a)
        self.assertEqual(test_crack.calc_delta_n(),
                         self.delta_a/(c_parameter*self.delta_k**m_parameter))

    def test_bad_crack_growth_model_specifications(self):
        """unit test for passing invalid crack growth rate model"""
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification={'model_name': 'paris_law'})

        test_crack.update_delta_k_delta_a(self.delta_k, self.delta_a)
        with self.assertRaises(ValueError):
            test_crack.calc_delta_n()

        test_crack2 = CrackGrowth(environment=self.environment,
                                  growth_model_specification={'model_name': 'something_else'})
        test_crack2.update_delta_k_delta_a(self.delta_k, self.delta_a)
        with self.assertRaises(ValueError):
            test_crack2.calc_delta_n()

    def test_design_curve_function(self):
        """unit test to check that design curve calculation function performs as expected"""
        specified_r = 0.7
        specified_fugacity = 100
        crack_growth_model = {'model_name': 'code_case_2938'}
        delta_k_1, delta_a_over_delta_n_1 = \
            get_design_curve(specified_r, specified_fugacity, crack_growth_model)

        delta_k_2, delta_a_over_delta_n_2 = \
            get_design_curve(specified_r, specified_fugacity)

        self.assertIsNone(np.testing.assert_array_equal(delta_k_1, delta_k_2))
        self.assertIsNone(np.testing.assert_array_equal(delta_a_over_delta_n_1,
                                                        delta_a_over_delta_n_2))

if __name__ == '__main__':
    unittest.main()
