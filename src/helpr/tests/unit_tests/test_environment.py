# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np

from helpr.physics.environment import EnvironmentSpecification


class EnvironmentTestCase(unittest.TestCase):
    """Class for unit tests of environment module"""
    def setUp(self):
        """function to specify common inputs to environment module"""

    def tearDown(self):
        """teardown function"""

    def test_r_ratio(self):
        """unit test of r ratio calculation"""
        max_pressure = 100
        min_pressure = 10
        example_environment = EnvironmentSpecification(max_pressure=max_pressure,
                                                       min_pressure=min_pressure)
        self.assertTrue(min_pressure/max_pressure == example_environment.r_ratio)

    def test_fugacity_ratio(self):
        """unit test of fugacity ratio calculation"""
        max_pressure = 300
        min_pressure = 10
        reference_pressure = 300
        example_environment = EnvironmentSpecification(max_pressure=max_pressure,
                                                       min_pressure=min_pressure,
                                                       reference_pressure=reference_pressure)
        self.assertTrue(1 == example_environment.fugacity_ratio)

    def test_h2_volume_fraction(self):
        """unit test of changing h2 mvolume fraction in environment"""
        max_pressure = 300
        min_pressure = 10
        volume_fraction_h2 = 1
        example_environment_mf1 = EnvironmentSpecification(max_pressure=max_pressure,
                                                           min_pressure=min_pressure,
                                                           volume_fraction_h2=volume_fraction_h2)
        volume_fraction_h2 = 1/2
        example_environment_mf2 = EnvironmentSpecification(max_pressure=max_pressure,
                                                           min_pressure=min_pressure,
                                                           volume_fraction_h2=volume_fraction_h2)
        self.assertTrue(example_environment_mf2.fugacity == 1/2*example_environment_mf1.fugacity)

        volume_fraction_h2 = 0
        example_environment_mf2 = EnvironmentSpecification(max_pressure=max_pressure,
                                                           min_pressure=min_pressure,
                                                           volume_fraction_h2=volume_fraction_h2)
        self.assertTrue(example_environment_mf2.fugacity == 0)

    def test_array_input(self):
        """unit test of passing array of pressure values to environment module"""
        max_pressure = np.array([300, 301])
        min_pressure = np.array([10, 9])
        reference_pressure = 300
        example_environment = EnvironmentSpecification(max_pressure=max_pressure,
                                                       min_pressure=min_pressure,
                                                       reference_pressure=reference_pressure,
                                                       sample_size=2)
        self.assertTrue(len(example_environment.fugacity_ratio) == 2)
        self.assertTrue(len(example_environment.r_ratio) == 2)
        second_environment = example_environment.get_single_environment(1)
        self.assertTrue(example_environment.max_pressure[1] == second_environment.max_pressure)
        self.assertTrue(example_environment.min_pressure[1] == second_environment.min_pressure)

if __name__ == '__main__':
    unittest.main()
