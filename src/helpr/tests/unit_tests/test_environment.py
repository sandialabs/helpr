# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np

from helpr.physics.environment import EnvironmentSpecification, EnvironmentSpecificationRandomLoad
from helpr.utilities.parameter import Parameter


class EnvironmentTestCase(unittest.TestCase):
    """Class for unit tests of environment module."""
    
    def setUp(self):
        """Function to specify common inputs to environment module."""

    def tearDown(self):
        """Teardown function."""

    def test_fugacity_ratio(self):
        """Unit test of fugacity ratio calculation."""
        max_pressure = 300
        min_pressure = 10
        reference_pressure = 300
        example_environment = EnvironmentSpecification(max_pressure=max_pressure,
                                                       min_pressure=min_pressure,
                                                       temperature=293,
                                                       volume_fraction_h2=1.0,
                                                       reference_pressure=reference_pressure)
        self.assertTrue(1 == example_environment.fugacity_ratio)

    def test_h2_volume_fraction(self):
        """Unit test of changing h2 volume fraction in environment."""
        max_pressure = 300
        min_pressure = 10
        volume_fraction_h2 = 1
        temperature = 293
        example_environment_mf1 = EnvironmentSpecification(max_pressure=max_pressure,
                                                           min_pressure=min_pressure,
                                                           temperature=temperature,
                                                           volume_fraction_h2=volume_fraction_h2)
        volume_fraction_h2 = 1/2
        example_environment_mf2 = EnvironmentSpecification(max_pressure=max_pressure,
                                                           min_pressure=min_pressure,
                                                           temperature=temperature,
                                                           volume_fraction_h2=volume_fraction_h2)
        self.assertTrue(example_environment_mf2.fugacity == 1/2*example_environment_mf1.fugacity)

        volume_fraction_h2 = 0
        example_environment_mf2 = EnvironmentSpecification(max_pressure=max_pressure,
                                                           min_pressure=min_pressure,
                                                           temperature=temperature,
                                                           volume_fraction_h2=volume_fraction_h2)
        self.assertTrue(example_environment_mf2.fugacity == 0)

    def test_calc_fugacity_numpy_path(self):
        """Test calc_fugacity triggers np.exp path with numpy input."""
        from helpr.physics.environment import EnvironmentSpecification
        import numpy as np

        env = EnvironmentSpecification(
            max_pressure=300,
            min_pressure=10,
            temperature=293,
            volume_fraction_h2=1.0
        )

        # Fake a vectorized pressure input to force np.exp path
        pressure = np.array([300])  # numpy array triggers np.exp
        temp = env.temperature
        vf = env.volume_fraction_h2

        fugacity = env.calc_fugacity(pressure=pressure,
                                    temperature=temp,
                                    volume_fraction_h2=vf)

        self.assertTrue(np.allclose(fugacity, pressure * vf * np.exp(
            env.calc_fugacity_coefficient(pressure, temp))))

    def test_init_valid_inputs(self):
        max_pressure = [10, 20, 30]
        min_pressure = [5, 10, 15]
        temperature = 293.15
        volume_fraction_h2 = 0.1
        reference_pressure = 106.0

        env_spec = EnvironmentSpecificationRandomLoad(max_pressure, 
                                                      min_pressure,
                                                      temperature,
                                                      volume_fraction_h2,
                                                      reference_pressure)

        self.assertIsInstance(env_spec.max_pressure, np.ndarray)
        self.assertIsInstance(env_spec.min_pressure, np.ndarray)

    def test_init_invalid_inputs(self):
        max_pressure = 'invalid'
        min_pressure = [5, 10, 15]
        temperature = 293.15
        volume_fraction_h2 = 0.1
        reference_pressure = 106.0

        with self.assertRaises(TypeError):
            EnvironmentSpecificationRandomLoad(max_pressure,
                                               min_pressure,
                                               temperature,
                                               volume_fraction_h2,
                                               reference_pressure)

    def test_calc_derived_quantities(self):
        max_pressure = [10, 20, 30]
        min_pressure = [5, 10, 15]
        temperature = 293.15
        volume_fraction_h2 = 0.1
        reference_pressure = 106.0

        env_spec = EnvironmentSpecificationRandomLoad(max_pressure,
                                                      min_pressure,
                                                      temperature,
                                                      volume_fraction_h2,
                                                      reference_pressure)

        self.assertIsNotNone(env_spec.fugacity)
        self.assertIsNotNone(env_spec.reference_fugacity)
        self.assertIsNotNone(env_spec.fugacity_ratio)
        self.assertIsNotNone(env_spec.partial_pressure)

    def test_get_max_pressure(self):
        max_pressure = [10, 20, 30]
        min_pressure = [5, 10, 15]
        temperature = 293.15
        volume_fraction_h2 = 0.1
        reference_pressure = 106.0

        env_spec = EnvironmentSpecificationRandomLoad(max_pressure,
                                                      min_pressure,
                                                      temperature,
                                                      volume_fraction_h2,
                                                      reference_pressure)

        self.assertEqual(env_spec._get_max_pressure(0), max_pressure[0])
        self.assertEqual(env_spec._get_max_pressure(1), max_pressure[1])
        self.assertEqual(env_spec._get_max_pressure(2), max_pressure[2])

    def test_get_min_pressure(self):
        max_pressure = [10, 20, 30]
        min_pressure = [5, 10, 15]
        temperature = 293.15
        volume_fraction_h2 = 0.1
        reference_pressure = 106.0

        env_spec = EnvironmentSpecificationRandomLoad(max_pressure,
                                                      min_pressure,
                                                      temperature,
                                                      volume_fraction_h2,
                                                      reference_pressure)

        self.assertEqual(env_spec._get_min_pressure(0), min_pressure[0])
        self.assertEqual(env_spec._get_min_pressure(1), min_pressure[1])
        self.assertEqual(env_spec._get_min_pressure(2), min_pressure[2])

    def test_get_partial_pressure(self):
        max_pressure = [10, 20, 30]
        min_pressure = [5, 10, 15]
        temperature = 293.15
        volume_fraction_h2 = 0.1
        reference_pressure = 106.0

        env_spec = EnvironmentSpecificationRandomLoad(max_pressure,
                                                      min_pressure,
                                                      temperature,
                                                      volume_fraction_h2,
                                                      reference_pressure)

        self.assertEqual(env_spec._get_partial_pressure(0), max_pressure[0] * volume_fraction_h2)
        self.assertEqual(env_spec._get_partial_pressure(1), max_pressure[1] * volume_fraction_h2)
        self.assertEqual(env_spec._get_partial_pressure(2), max_pressure[2] * volume_fraction_h2)

    def test_get_fugacity_ratio(self):
        max_pressure = [10, 20, 30]
        min_pressure = [5, 10, 15]
        temperature = 293.15
        volume_fraction_h2 = 0.1
        reference_pressure = 106.0

        env_spec = EnvironmentSpecificationRandomLoad(max_pressure,
                                                      min_pressure,
                                                      temperature,
                                                      volume_fraction_h2,
                                                      reference_pressure)

        self.assertIsNotNone(env_spec._get_fugacity_ratio(0))
        self.assertIsNotNone(env_spec._get_fugacity_ratio(1))
        self.assertIsNotNone(env_spec._get_fugacity_ratio(2))

if __name__ == '__main__':
    unittest.main()
