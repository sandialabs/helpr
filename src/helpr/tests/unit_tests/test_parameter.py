# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np

from helpr.utilities.parameter import Parameter


class ParameterTestCase(unittest.TestCase):
    """class for unit test of parameter module"""
    def setUp(self) -> None:
        self.lower_bound = 0
        self.upper_bound = 3
        self.size = 3
        self.name = 'test_parameter'

    def tearDown(self) -> None:
        """teardown function"""

    def test_default(self):
        """unit tests of default behavior of parameter module"""
        parameter_value = 1
        test_parameter = Parameter(self.name,
                                   parameter_value,
                                   self.lower_bound,
                                   self.upper_bound)
        self.assertEqual(np.array([parameter_value]), test_parameter)
        self.assertEqual(len(test_parameter), 1)

    def test_make_array(self):
        """unit test of specifying size of parameter object"""
        parameter_value = 2
        test_parameter = Parameter(self.name,
                                   parameter_value,
                                   self.lower_bound,
                                   self.upper_bound,
                                   self.size)
        self.assertEqual(len(test_parameter), 3)

    def test_below_bounds(self):
        """unit test of specifying parameter value below lower bound"""
        parameter_value = -1
        with self.assertRaises(ValueError):
            Parameter(self.name, parameter_value, self.lower_bound, self.upper_bound, self.size)

    def test_above_bounds(self):
        """unit test of specifying parameter value above upper bound"""
        parameter_value = 4
        with self.assertRaises(ValueError):
            Parameter(self.name, parameter_value, self.lower_bound, self.upper_bound, self.size)

    def test_passed_list(self):
        """unit test of passing list of parameter values to parameter module"""
        parameter_value = [1, 2, 1.5]
        test_parameter = Parameter(self.name,
                                   parameter_value,
                                   self.lower_bound,
                                   self.upper_bound,
                                   self.size)
        self.assertEqual(len(test_parameter), 3)

    def test_list_below_bounds(self):
        """unit test of passing list of inputs with one value below parameter lower bounds"""
        parameter_value = [1, 2, -0.5]
        with self.assertRaises(ValueError):
            Parameter(self.name, parameter_value, self.lower_bound, self.upper_bound, self.size)

    def test_list_above_bounds(self):
        """unit test of passing list of inputs with one value above parameter upper bounds"""
        parameter_value = [1, 2, 3.1]
        with self.assertRaises(ValueError):
            Parameter(self.name, parameter_value, self.lower_bound, self.upper_bound, self.size)

    def test_bad_size_specification(self):
        """unit test to check that bad size specification does not work"""
        parameter_value = [1, 2, 3.1]
        with self.assertRaises(ValueError):
            Parameter(self.name, parameter_value, self.lower_bound, self.upper_bound, 4)

if __name__ == '__main__':
    unittest.main()
