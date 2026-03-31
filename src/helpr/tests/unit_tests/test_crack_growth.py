# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import math

from unittest.mock import patch

from helpr.physics.crack_growth import CrackGrowth, get_design_curve
from helpr.physics.environment import EnvironmentSpecification


class CrackGrowthTestCase(unittest.TestCase):
    """
    Class for units tests of crack growth module.
    
    Attributes
    ----------
    max_pressure : float
        Maximum pressure in MPa.
    min_pressure : float
        Minimum pressure in MPa.
    r_ratio : float
        Load ratio (minimum load / maximum load), must be between 0 and 1.
    temperature : float
        Temperature in Kelvin.
    volume_fraction_h2 : float
        Volume fraction of hydrogen in gas.
    delta_k : float
        Stress intensity factor range.
    delta_a : float
        Change in crack size.
    delta_n : float
        Number of load cycles.
    growth_model_specification : dict
        Specify whether ASME Code Case 2938 w/ fugacity correction (code_case_2938) 
        or a generic Paris Law (paris_law) will be used.
    environment : EnvironmentSpecification
        Specification of the gaseous environment within the pipeline.
    """

    def setUp(self):
        """Function to specify common inputs to crack growth module."""
        self.max_pressure = 13
        self.min_pressure = 11
        self.r_ratio = self.min_pressure / self.max_pressure
        self.temperature = 300
        self.volume_fraction_h2 = 1.0
        self.delta_k = 0.1
        self.delta_a = 0.1
        self.delta_n = 10
        self.growth_model_specification = {'model_name': 'code_case_2938'}
        self.environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                                    min_pressure=self.min_pressure,
                                                    temperature=self.temperature,
                                                    volume_fraction_h2=self.volume_fraction_h2)

    def tearDown(self):
        """Teardown function."""
        pass

    def test_default(self):
        """Unit test of default behavior of crack growth module."""
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification=self.growth_model_specification)
        self.assertGreater(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                   delta_k=self.delta_k,
                                                   r_ratio=self.r_ratio), 0)
        # goes to inf due to dividing by 0
        self.assertEqual(test_crack.calc_delta_n(delta_a=0,
                                                 delta_k=0,
                                                 r_ratio=self.r_ratio), math.inf)
        self.assertGreater(test_crack.calc_change_in_crack_size(delta_n=self.delta_n, 
                                                                delta_k=self.delta_k,
                                                                r_ratio=self.r_ratio), 0)
        self.assertEqual(test_crack.calc_change_in_crack_size(delta_n=0, 
                                                              delta_k=0,
                                                              r_ratio=self.r_ratio), 0)

    def test_0pct_h2(self):
        """Unit test for having no hydrogen in crack growth calculations."""
        environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                               min_pressure=self.min_pressure,
                                               temperature=self.temperature,
                                               volume_fraction_h2=0)
        test_crack = CrackGrowth(environment=environment,
                                 growth_model_specification=self.growth_model_specification)

        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=self.delta_k,
                                                 r_ratio=self.r_ratio),
                                                 test_crack.calc_air_curve_dn())

    def test_100pct_h2(self):
        """Unit test that crack growth following ASME curve."""
        environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                               min_pressure=self.min_pressure,
                                               temperature=self.temperature,
                                               volume_fraction_h2=1)
        test_crack = CrackGrowth(environment=environment,
                                 growth_model_specification=self.growth_model_specification)

        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=1,
                                                 r_ratio=self.r_ratio), test_crack.calc_air_curve_dn())
        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=10,
                                                 r_ratio=self.r_ratio),
                                                 test_crack.calc_code_case_2938_dn_lower_k())
        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=100,
                                                 r_ratio=self.r_ratio),
                                                 test_crack.calc_code_case_2938_dn_higher_k())

    def test_invalid_fugacity_correction_case(self):
        """
        Unit test of passing invalid input to fugacity correction.
        
        Raises
        ------
        ValueError
            If the case is not specified or is invalid.
        """
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification=self.growth_model_specification)

        with self.assertRaises(ValueError):
            test_crack.calc_fugacity_correction(p=1.5E-11, multiplier=3.66, case='')

    def test_specify_paris_law_crack_growth(self):
        """Unit test of specifying inputs for a paris law crack growth model."""
        c_parameter = 1
        m_parameter = 2
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification={'model_name': 'paris_law',
                                                              'c': c_parameter,
                                                              'm': m_parameter})

        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=self.delta_k,
                                                 r_ratio=self.r_ratio),
                         self.delta_a/(c_parameter*self.delta_k**m_parameter))
        self.assertEqual(test_crack.calc_change_in_crack_size(delta_n=self.delta_n,
                                                              delta_k=self.delta_k,
                                                              r_ratio=self.r_ratio),
                         self.delta_n*(c_parameter*self.delta_k**m_parameter))

    def test_bad_crack_growth_model_specifications(self):
        """
        Unit test for passing invalid crack growth rate model.

        Raises
        ------
        ValueError
            If the growth model specification is invalid or missing required parameters.
        """
        test_crack = CrackGrowth(environment=self.environment,
                         growth_model_specification={'model_name': 'paris_law'})

        with self.assertRaises(ValueError):
            test_crack.calc_delta_n(delta_a=self.delta_a,
                                    delta_k=self.delta_k,
                                    r_ratio=self.r_ratio)
        with self.assertRaises(ValueError):
            test_crack.calc_change_in_crack_size(delta_n=self.delta_n,
                                                  delta_k=self.delta_k,
                                                  r_ratio=self.r_ratio)

        test_crack2 = CrackGrowth(environment=self.environment,
                                  growth_model_specification={'model_name': 'something_else'})

        with self.assertRaises(ValueError):
            test_crack2.calc_delta_n(delta_a=self.delta_a,
                                     delta_k=self.delta_k,
                                     r_ratio=self.r_ratio)
        with self.assertRaises(ValueError):
            test_crack2.calc_change_in_crack_size(delta_n=self.delta_n,
                                                  delta_k=self.delta_k,
                                                  r_ratio=self.r_ratio)

    def test_design_curve_function(self):
        """Unit test to check that design curve calculation function performs as expected."""
        specified_r = 0.7

        crack_growth_model = {'model_name': 'code_case_2938'}
        delta_k_1, delta_a_over_delta_n_1 = \
            get_design_curve(specified_r=specified_r,
            temperature=self.temperature,
            volume_fraction_h2=self.volume_fraction_h2,
            max_pressure=1,
            min_pressure=1,
            crack_growth_model=crack_growth_model)

        delta_k_2, delta_a_over_delta_n_2 = \
            get_design_curve(specified_r=specified_r,
            temperature=self.temperature,
            max_pressure=1,
            min_pressure=1,
            volume_fraction_h2=self.volume_fraction_h2)

        self.assertListEqual(delta_k_1, delta_k_2)
        self.assertListEqual(delta_a_over_delta_n_1, delta_a_over_delta_n_2)

    def test_calc_delta_n_missing_inputs(self):
        """
        Test calc_delta_n triggers error if delta_a or delta_k is None.
        
        Raises
        ------
        ValueError
            If delta_a or delta_k is None.
        """
        test_crack = CrackGrowth(environment=self.environment,
                                growth_model_specification=self.growth_model_specification)

        with patch('helpr.physics.crack_growth.Parameter'):
            with self.assertRaises(ValueError) as context:
                test_crack.calc_delta_n(delta_a=None, delta_k=0.1, r_ratio=self.r_ratio)
            self.assertIn("delta_k or delta_a must be specified", str(context.exception))

            with self.assertRaises(ValueError) as context:
                test_crack.calc_delta_n(delta_a=0.1, delta_k=None, r_ratio=self.r_ratio)
            self.assertIn("delta_k or delta_a must be specified", str(context.exception))

    def test_calc_change_in_crack_size_missing_inputs(self):
        """
        Test calc_change_in_crack_size triggers error if delta_n or delta_k is None.
        
        Raises
        ------
        ValueError
            If delta_n or delta_k is None.
        """
        test_crack = CrackGrowth(environment=self.environment,
                                growth_model_specification=self.growth_model_specification)

        with patch('helpr.physics.crack_growth.Parameter'):
            with self.assertRaises(ValueError) as context:
                test_crack.calc_change_in_crack_size(delta_n=None, delta_k=0.1, r_ratio=self.r_ratio)
            self.assertIn("delta_k or delta_n must be specified", str(context.exception))

            with self.assertRaises(ValueError) as context:
                test_crack.calc_change_in_crack_size(delta_n=10, delta_k=None, r_ratio=self.r_ratio)
            self.assertIn("delta_k or delta_n must be specified", str(context.exception))

    def test_calc_dn_g202006_path(self):
        """Test G 202006 model path for delta_n."""
        model_spec = {'model_name': 'g_202006'}
        test_crack = CrackGrowth(environment=self.environment, growth_model_specification=model_spec)
        result = test_crack.calc_delta_n(delta_a=0.01, delta_k=0.5, r_ratio=self.r_ratio)
        self.assertIsInstance(result, float)

    def test_calc_da_g202006_path(self):
        """Test G 202006 model path for delta_a."""
        model_spec = {'model_name': 'g_202006'}
        test_crack = CrackGrowth(environment=self.environment, growth_model_specification=model_spec)
        result = test_crack.calc_change_in_crack_size(delta_n=10, delta_k=0.5, r_ratio=self.r_ratio)
        self.assertIsInstance(result, float)

    def test_calc_delta_n_paris_law_missing_c_m(self):
        """
        Test error raised when Paris Law is selected without 'c' and 'm'.
        
        Raises
        ------
        ValueError
            If 'c' and 'm' are not specified for Paris Law.
        """
        model_spec = {'model_name': 'paris_law'}  # Missing c and m
        test_crack = CrackGrowth(environment=self.environment, growth_model_specification=model_spec)
        with self.assertRaises(ValueError) as context:
            test_crack.calc_delta_n(delta_a=0.01, delta_k=0.5, r_ratio=self.r_ratio)
        self.assertIn("c and m must be specified", str(context.exception))

    def test_calc_dn_g202006_air_case(self):
        """Test delta_n from G202006 model when partial pressure is 0 (air curve path)."""
        environment = EnvironmentSpecification(
            max_pressure=1, min_pressure=1, temperature=300, volume_fraction_h2=0
        )
        test_crack = CrackGrowth(
            environment=environment,
            growth_model_specification={'model_name': 'g_202006'}
        )
        result = test_crack.calc_delta_n(delta_a=0.01, delta_k=0.5, r_ratio=0.5)
        self.assertIsInstance(result, float)  # Hits line 164

    def test_calc_da_g202006_air_case(self):
        """Test delta_a from G202006 model when partial pressure is 0 (air curve path)."""
        environment = EnvironmentSpecification(
            max_pressure=1, min_pressure=1, temperature=300, volume_fraction_h2=0
        )
        test_crack = CrackGrowth(
            environment=environment,
            growth_model_specification={'model_name': 'g_202006'}
        )
        result = test_crack.calc_change_in_crack_size(delta_n=10, delta_k=0.5, r_ratio=0.5)
        self.assertIsInstance(result, float)  # Hits line 188

    def test_partial_pressure_correction_high_case(self):
        """Test partial pressure correction explicitly with 'high' case."""
        test_crack = CrackGrowth(environment=self.environment,
                                growth_model_specification={'model_name': 'g_202006'})
        test_crack.r_ratio = 0.5  # simulate it already being set
        result = test_crack.calc_partial_pressure_correction(
            p=1e-12, multiplier=2, case='high'
        )
        self.assertGreater(result, 0)  # Covers lines 503–506

    def test_get_design_curve_raises_value_error_without_inputs(self):
        """
        Test get_design_curve raises error when neither env_obj nor full inputs are passed.
        
        Raises
        ------
        ValueError
            If neither env_obj nor full inputs are provided.
        """
        with self.assertRaises(ValueError) as context:
            get_design_curve(specified_r=0.5)
        self.assertIn("must be specified or environment_obj must be provided", str(context.exception))  # Line 644

    def test_calc_g202006_dn_higher_k_path(self):
        """Ensure calc_g202006_dn_higher_k return path executes."""
        crack = CrackGrowth(environment=self.environment,
                            growth_model_specification={'model_name': 'g_202006'})
        crack.delta_k = 100  # Higher than threshold to trigger this path
        crack.delta_a = 0.01
        crack.r_ratio = 0.5
        result = crack.calc_g202006_dn_higher_k()
        self.assertIsInstance(result, float)

    def test_calc_g202006_da_higher_k_path(self):
        """Ensure calc_g202006_da_higher_k return path executes."""
        crack = CrackGrowth(environment=self.environment,
                            growth_model_specification={'model_name': 'g_202006'})
        crack.delta_k = 100
        crack.delta_n = 10
        crack.r_ratio = 0.5
        result = crack.calc_g202006_da_higher_k()
        self.assertIsInstance(result, float)

    def test_calc_code_case_2938_dn_higher_k_direct(self):
        """Test calculation of delta N for Code Case 2938 at higher K values."""
        crack = CrackGrowth(environment=self.environment,
                            growth_model_specification=self.growth_model_specification)
        crack.delta_k = 1
        crack.delta_a = 0.01
        crack.r_ratio = 0.5
        result = crack.calc_code_case_2938_dn_higher_k()
        self.assertIsInstance(result, float)

    def test_calc_code_case_2938_da_higher_k_direct(self):
        """Test calculation of delta A for Code Case 2938 at higher K values."""
        crack = CrackGrowth(environment=self.environment,
                            growth_model_specification=self.growth_model_specification)
        crack.delta_k = 1
        crack.delta_n = 10
        crack.r_ratio = 0.5
        result = crack.calc_code_case_2938_da_higher_k()
        self.assertIsInstance(result, float)

    def test_calc_dn_g202006_higher_k(self):
        """Trigger calc_g202006_dn_higher_k."""
        crack = CrackGrowth(environment=self.environment, growth_model_specification={'model_name': 'g_202006'})
        crack.delta_k = 100
        crack.delta_a = 0.01
        crack.r_ratio = 0.5
        result = crack.calc_dn_g202006()
        self.assertIsInstance(result, float)

    def test_calc_da_g202006_higher_k(self):
        """Trigger calc_g202006_da_higher_k."""
        crack = CrackGrowth(environment=self.environment, growth_model_specification={'model_name': 'g_202006'})
        crack.delta_k = 100
        crack.delta_n = 10
        crack.r_ratio = 0.5
        result = crack.calc_da_g202006()
        self.assertIsInstance(result, float)

    def test_invalid_partial_pressure_correction_case(self):
        """Ensure ValueError raised for invalid 'case​' in partial pressure correction."""

    def setUp(self):
        """Function to specify common inputs to crack growth module."""
        self.max_pressure = 13
        self.min_pressure = 11
        self.r_ratio = self.min_pressure / self.max_pressure
        self.temperature = 300
        self.volume_fraction_h2 = 1.0
        self.delta_k = 0.1
        self.delta_a = 0.1
        self.delta_n = 10
        self.growth_model_specification = {'model_name': 'code_case_2938'}
        self.environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                                    min_pressure=self.min_pressure,
                                                    temperature=self.temperature,
                                                    volume_fraction_h2=self.volume_fraction_h2)

    def tearDown(self):
        """Teardown function."""

    def test_default(self):
        """Unit test of default behavior of crack growth module."""
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification=self.growth_model_specification)
        self.assertGreater(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                   delta_k=self.delta_k,
                                                   r_ratio=self.r_ratio), 0)
        # goes to inf due to dividing by 0
        self.assertEqual(test_crack.calc_delta_n(delta_a=0,
                                                 delta_k=0,
                                                 r_ratio=self.r_ratio), math.inf)
        self.assertGreater(test_crack.calc_change_in_crack_size(delta_n=self.delta_n, 
                                                                delta_k=self.delta_k,
                                                                r_ratio=self.r_ratio), 0)
        self.assertEqual(test_crack.calc_change_in_crack_size(delta_n=0, 
                                                              delta_k=0,
                                                              r_ratio=self.r_ratio), 0)

    def test_0pct_h2(self):
        """Unit test for having no hydrogen in crack growth calculations."""
        environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                               min_pressure=self.min_pressure,
                                               temperature=self.temperature,
                                               volume_fraction_h2=0)
        test_crack = CrackGrowth(environment=environment,
                                 growth_model_specification=self.growth_model_specification)

        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=self.delta_k,
                                                 r_ratio=self.r_ratio),
                                                 test_crack.calc_air_curve_dn())

    def test_100pct_h2(self):
        """Unit test that crack growth following ASME curve."""
        environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                               min_pressure=self.min_pressure,
                                               temperature=self.temperature,
                                               volume_fraction_h2=1)
        test_crack = CrackGrowth(environment=environment,
                                 growth_model_specification=self.growth_model_specification)

        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=1,
                                                 r_ratio=self.r_ratio), test_crack.calc_air_curve_dn())
        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=10,
                                                 r_ratio=self.r_ratio),
                                                 test_crack.calc_code_case_2938_dn_lower_k())
        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=100,
                                                 r_ratio=self.r_ratio),
                                                 test_crack.calc_code_case_2938_dn_higher_k())


    def test_invalid_fugacity_correction_case(self):
        """
        Unit test of passing invalid input to fugacity correction.
        
        Raises
        ------
        ValueError
            If the case is not specified or is invalid.
        """
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification=self.growth_model_specification)

        with self.assertRaises(ValueError):
            test_crack.calc_fugacity_correction(p=1.5E-11, multiplier=3.66, case='')

    def test_specify_paris_law_crack_growth(self):
        """Unit test of specifying inputs for a paris law crack growth model."""
        c_parameter = 1
        m_parameter = 2
        test_crack = CrackGrowth(environment=self.environment,
                                 growth_model_specification={'model_name': 'paris_law',
                                                              'c': c_parameter,
                                                              'm': m_parameter})

        self.assertEqual(test_crack.calc_delta_n(delta_a=self.delta_a,
                                                 delta_k=self.delta_k,
                                                 r_ratio=self.r_ratio),
                         self.delta_a/(c_parameter*self.delta_k**m_parameter))
        self.assertEqual(test_crack.calc_change_in_crack_size(delta_n=self.delta_n,
                                                              delta_k=self.delta_k,
                                                              r_ratio=self.r_ratio),
                         self.delta_n*(c_parameter*self.delta_k**m_parameter))

    def test_bad_crack_growth_model_specifications(self):
        """
        Unit test for passing invalid crack growth rate model.
        
        Raises
        ------
        ValueError
            If the growth model specification is invalid or missing required parameters.
        """
        test_crack = CrackGrowth(environment=self.environment,
                         growth_model_specification={'model_name': 'paris_law'})

        with self.assertRaises(ValueError):
            test_crack.calc_delta_n(delta_a=self.delta_a,
                                    delta_k=self.delta_k,
                                    r_ratio=self.r_ratio)
        with self.assertRaises(ValueError):
            test_crack.calc_change_in_crack_size(delta_n=self.delta_n,
                                                 delta_k=self.delta_k,
                                                 r_ratio=self.r_ratio)

        test_crack2 = CrackGrowth(environment=self.environment,
                                  growth_model_specification={'model_name': 'something_else'})

        with self.assertRaises(ValueError):
            test_crack2.calc_delta_n(delta_a=self.delta_a,
                                     delta_k=self.delta_k,
                                     r_ratio=self.r_ratio)
        with self.assertRaises(ValueError):
            test_crack2.calc_change_in_crack_size(delta_n=self.delta_n,
                                                  delta_k=self.delta_k,
                                                  r_ratio=self.r_ratio)

    def test_calc_delta_n_missing_inputs(self):
        """
        Test calc_delta_n triggers error if delta_a or delta_k is None.
        
        Raises
        ------
        ValueError
            If delta_a or delta_k is None.
        """
        test_crack = CrackGrowth(environment=self.environment,
                                growth_model_specification=self.growth_model_specification)

        with patch('helpr.physics.crack_growth.Parameter'):
            with self.assertRaises(ValueError) as context:
                test_crack.calc_delta_n(delta_a=None, delta_k=0.1, r_ratio=self.r_ratio)
            self.assertIn("delta_k or delta_a must be specified", str(context.exception))

            with self.assertRaises(ValueError) as context:
                test_crack.calc_delta_n(delta_a=0.1, delta_k=None, r_ratio=self.r_ratio)
            self.assertIn("delta_k or delta_a must be specified", str(context.exception))

    def test_calc_change_in_crack_size_missing_inputs(self):
        """
        Test calc_change_in_crack_size triggers error if delta_n or delta_k is None.
        
        Raises
        ------
        ValueError
            If delta_n or delta_k is None.
        """
        test_crack = CrackGrowth(environment=self.environment,
                                growth_model_specification=self.growth_model_specification)

        with patch('helpr.physics.crack_growth.Parameter'):
            with self.assertRaises(ValueError) as context:
                test_crack.calc_change_in_crack_size(delta_n=None, delta_k=0.1, r_ratio=self.r_ratio)
            self.assertIn("delta_k or delta_n must be specified", str(context.exception))

            with self.assertRaises(ValueError) as context:
                test_crack.calc_change_in_crack_size(delta_n=10, delta_k=None, r_ratio=self.r_ratio)
            self.assertIn("delta_k or delta_n must be specified", str(context.exception))

    def test_calc_dn_g202006_path(self):
        """Test G 202006 model path for delta_n."""
        model_spec = {'model_name': 'g_202006'}
        test_crack = CrackGrowth(environment=self.environment, growth_model_specification=model_spec)
        result = test_crack.calc_delta_n(delta_a=0.01, delta_k=0.5, r_ratio=self.r_ratio)
        self.assertIsInstance(result, float)

    def test_calc_da_g202006_path(self):
        """Test G 202006 model path for delta_a."""
        model_spec = {'model_name': 'g_202006'}
        test_crack = CrackGrowth(environment=self.environment, growth_model_specification=model_spec)
        result = test_crack.calc_change_in_crack_size(delta_n=10, delta_k=0.5, r_ratio=self.r_ratio)
        self.assertIsInstance(result, float)

    def test_calc_delta_n_paris_law_missing_c_m(self):
        """
        Test error raised when Paris Law is selected without 'c' and 'm'.
        
        Raises
        ------
        ValueError
            If 'c' and 'm' are not specified for Paris Law.
        """
        model_spec = {'model_name': 'paris_law'}  # Missing c and m
        test_crack = CrackGrowth(environment=self.environment, growth_model_specification=model_spec)
        with self.assertRaises(ValueError) as context:
            test_crack.calc_delta_n(delta_a=0.01, delta_k=0.5, r_ratio=self.r_ratio)
        self.assertIn("c and m must be specified", str(context.exception))

    def test_calc_dn_g202006_air_case(self):
        """Test delta_n from G202006 model when partial pressure is 0 (air curve path)."""
        environment = EnvironmentSpecification(
            max_pressure=1, min_pressure=1, temperature=300, volume_fraction_h2=0
        )
        test_crack = CrackGrowth(
            environment=environment,
            growth_model_specification={'model_name': 'g_202006'}
        )
        result = test_crack.calc_delta_n(delta_a=0.01, delta_k=0.5, r_ratio=0.5)
        self.assertIsInstance(result, float)  # Hits line 164

    def test_calc_da_g202006_air_case(self):
        """Test delta_a from G202006 model when partial pressure is 0 (air curve path)."""
        environment = EnvironmentSpecification(
            max_pressure=1, min_pressure=1, temperature=300, volume_fraction_h2=0
        )
        test_crack = CrackGrowth(
            environment=environment,
            growth_model_specification={'model_name': 'g_202006'}
        )
        result = test_crack.calc_change_in_crack_size(delta_n=10, delta_k=0.5, r_ratio=0.5)
        self.assertIsInstance(result, float) 

    def test_partial_pressure_correction_high_case(self):
        """Test partial pressure correction explicitly with 'high' case."""
        test_crack = CrackGrowth(environment=self.environment,
                                growth_model_specification={'model_name': 'g_202006'})
        test_crack.r_ratio = 0.5  # simulate it already being set
        result = test_crack.calc_partial_pressure_correction(
            p=1e-12, multiplier=2, case='high'
        )
        self.assertGreater(result, 0) 

    def test_get_design_curve_raises_value_error_without_inputs(self):
        """
        Test get_design_curve raises error when neither env_obj nor full inputs are passed.
        
        Raises
        ------
        ValueError
            If neither env_obj nor full inputs are provided.
        """
        with self.assertRaises(ValueError) as context:
            get_design_curve(specified_r=0.5)
        self.assertIn("must be specified or environment_obj must be provided", str(context.exception))  # Line 644

    def test_calc_g202006_dn_higher_k_path(self):
        """Ensure calc_g202006_dn_higher_k return path executes."""
        crack = CrackGrowth(environment=self.environment,
                            growth_model_specification={'model_name': 'g_202006'})
        crack.delta_k = 100  # Higher than threshold to trigger this path
        crack.delta_a = 0.01
        crack.r_ratio = 0.5
        result = crack.calc_g202006_dn_higher_k()
        self.assertIsInstance(result, float)

    def test_calc_g202006_da_higher_k_path(self):
        """Ensure calc_g202006_da_higher_k return path executes."""
        crack = CrackGrowth(environment=self.environment,
                            growth_model_specification={'model_name': 'g_202006'})
        crack.delta_k = 100
        crack.delta_n = 10
        crack.r_ratio = 0.5
        result = crack.calc_g202006_da_higher_k()
        self.assertIsInstance(result, float)

    def test_calc_code_case_2938_dn_higher_k_direct(self):
        """Test calculation of delta N for Code Case 2938 at higher K values."""
        crack = CrackGrowth(environment=self.environment,
                            growth_model_specification=self.growth_model_specification)
        crack.delta_k = 1
        crack.delta_a = 0.01
        crack.r_ratio = 0.5
        result = crack.calc_code_case_2938_dn_higher_k()
        self.assertIsInstance(result, float)

    def test_calc_code_case_2938_da_higher_k_direct(self):
        """Test calculation of delta A for Code Case 2938 at higher K values."""
        crack = CrackGrowth(environment=self.environment,
                            growth_model_specification=self.growth_model_specification)
        crack.delta_k = 1
        crack.delta_n = 10
        crack.r_ratio = 0.5
        result = crack.calc_code_case_2938_da_higher_k()
        self.assertIsInstance(result, float)

    def test_calc_dn_g202006_higher_k(self):
        """Trigger calc_g202006_dn_higher_k."""
        crack = CrackGrowth(environment=self.environment, growth_model_specification={'model_name': 'g_202006'})
        crack.delta_k = 100
        crack.delta_a = 0.01
        crack.r_ratio = 0.5
        result = crack.calc_dn_g202006()
        self.assertIsInstance(result, float)

    def test_calc_da_g202006_higher_k(self):
        """Trigger calc_g202006_da_higher_k."""
        crack = CrackGrowth(environment=self.environment, growth_model_specification={'model_name': 'g_202006'})
        crack.delta_k = 100
        crack.delta_n = 10
        crack.r_ratio = 0.5
        result = crack.calc_da_g202006()
        self.assertIsInstance(result, float)

    def test_invalid_partial_pressure_correction_case(self):
        """
        Ensure ValueError raised for invalid 'case' in partial pressure correction.
        
        Raises
        ------
        ValueError
            If the 'case' is not a valid value.
        """
        crack = CrackGrowth(environment=self.environment, growth_model_specification=self.growth_model_specification)
        crack.r_ratio = 0.5
        with self.assertRaises(ValueError):
            crack.calc_partial_pressure_correction(p=1e-11, multiplier=2, case='invalid')


if __name__ == '__main__':
    unittest.main()
