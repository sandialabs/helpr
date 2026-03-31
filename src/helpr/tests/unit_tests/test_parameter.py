# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np

from helpr.utilities.parameter import Parameter


class ParameterTestCase(unittest.TestCase):
    """
    Class for unit test of parameter module.
    
    Attributes
    ----------
    lower_bound : float
        Lower bound for the parameter.
    upper_bound : float
        Upper bound for the parameter.
    name : str
        Name of the parameter.
    """

    def setUp(self) -> None:
        """Set up the test case."""
        self.lower_bound = 0
        self.upper_bound = 3
        self.name = 'test_parameter'

    def tearDown(self) -> None:
        """Teardown function."""

    def test_default(self):
        """Unit tests of default behavior of parameter module."""
        parameter_value = 1
        test_parameter = Parameter(self.name,
                                   parameter_value,
                                   self.lower_bound,
                                   self.upper_bound)
        self.assertEqual(float(parameter_value), test_parameter)
        self.assertTrue(isinstance(test_parameter, float))

    def test_make_array(self):
        """
        Unit test of specifying size of parameter object.
        
        Raises
        ------
        ValueError
            If the size of the parameter value is not valid.
        """
        parameter_value = [1, 2]
        with self.assertRaises(ValueError):
            Parameter(self.name,
                      parameter_value,
                      self.lower_bound,
                      self.upper_bound)

    def test_below_bounds(self):
        """
        Unit test of specifying parameter value below lower bound.
        
        Raises
        ------
        ValueError
            If the parameter value is below the lower bound.
        """
        parameter_value = -1
        with self.assertRaises(ValueError):
            Parameter(self.name, parameter_value, self.lower_bound, self.upper_bound)

    def test_above_bounds(self):
        """
        Unit test of specifying parameter value above upper bound.
        
        Raises
        ------
        ValueError
            If the parameter value is above the upper bound.
        """
        parameter_value = 4
        with self.assertRaises(ValueError):
            Parameter(self.name, parameter_value, self.lower_bound, self.upper_bound)

    def test_passed_list(self):
        """Unit test of passing of parameter values in single element list to parameter module."""
        parameter_value = [1]
        test_parameter = Parameter(self.name,
                                   parameter_value,
                                   self.lower_bound,
                                   self.upper_bound)
        self.assertEqual(float(parameter_value[0]), test_parameter)
        self.assertTrue(isinstance(test_parameter, float))

    def test_passed_array(self):
        """Unit test of passing of parameter value in single element array to parameter module."""
        parameter_value = np.array([1])
        test_parameter = Parameter(self.name,
                                   parameter_value,
                                   self.lower_bound,
                                   self.upper_bound)
        self.assertEqual(float(parameter_value[0]), test_parameter)
        self.assertTrue(isinstance(test_parameter, float))

    def test_get_length_list_and_array(self):
        """Test get_length with list and array inputs."""
        from helpr.utilities.parameter import get_length

        self.assertEqual(get_length([1, 2, 3]), 3)
        self.assertEqual(get_length(np.array([10, 20])), 2)

    def test_get_length_scalar(self):
        """Test get_length with scalar float and int."""
        from helpr.utilities.parameter import get_length

        self.assertEqual(get_length(5), 1)
        self.assertEqual(get_length(3.14), 1)

    def test_get_length_invalid_type(self):
        """
        Test get_length with unsupported type to trigger ValueError.
        
        Raises
        ------
        ValueError
            If the input type is not supported.
        """
        from helpr.utilities.parameter import get_length

        with self.assertRaises(ValueError):
            get_length("invalid")
        with self.assertRaises(ValueError):
            get_length({'a': 1})

if __name__ == '__main__':
    unittest.main()
