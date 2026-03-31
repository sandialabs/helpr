"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import unittest

import numpy as np

from ..utils.helpers import (get_num_str, hround, convert_to_float_list,
                             count_decimal_places, ValidationResponse, InputStatus)


class GetNumStrTestCase(unittest.TestCase):
    """Tests for get_num_str formatting function."""

    def test_zero(self):
        self.assertEqual(get_num_str(0), "0")
        self.assertEqual(get_num_str(0.0), "0")

    def test_negative_zero(self):
        self.assertEqual(get_num_str(-0.0), "0")

    def test_positive_infinity(self):
        self.assertEqual(get_num_str(np.inf), "+infinity")

    def test_negative_infinity(self):
        self.assertEqual(get_num_str(-np.inf), "-infinity")

    def test_none(self):
        self.assertEqual(get_num_str(None), "")

    def test_large_value(self):
        result = get_num_str(5000)
        self.assertIn("e", result)

    def test_medium_value(self):
        result = get_num_str(42.7)
        self.assertEqual(result, "42.7")

    def test_small_value(self):
        result = get_num_str(0.05)
        self.assertEqual(result, "0.050")

    def test_very_small_value(self):
        result = get_num_str(0.001)
        self.assertIn("e", result)

    def test_negative_medium_value(self):
        result = get_num_str(-10.5)
        self.assertEqual(result, "-10.5")

    def test_value_at_boundary_1000(self):
        result = get_num_str(1000)
        self.assertEqual(result, "1000.0")

    def test_value_above_1000(self):
        result = get_num_str(1001)
        self.assertIn("e", result)


class HroundTestCase(unittest.TestCase):
    """Tests for hround utility."""

    def test_non_decimal_value(self):
        """Values >= 1 round to p decimal places."""
        result = hround(3.14159, p=3)
        self.assertAlmostEqual(result, 3.142, places=3)

    def test_decimal_value(self):
        """Values < 1 round to p significant digits."""
        result = hround(0.001234, p=3)
        self.assertAlmostEqual(result, 0.00123, places=5)

    def test_zero(self):
        result = hround(0.0)
        self.assertEqual(result, 0.0)

    def test_negative_decimal(self):
        result = hround(-0.005678, p=3)
        self.assertAlmostEqual(result, -0.00568, places=5)


class ConvertToFloatListTestCase(unittest.TestCase):
    """Tests for convert_to_float_list."""

    def test_string_input(self):
        result = convert_to_float_list("1.0 2.5 3.0")
        self.assertEqual(result, [1.0, 2.5, 3.0])

    def test_float_input(self):
        result = convert_to_float_list(5.0)
        self.assertEqual(result, [5.0])

    def test_list_passthrough(self):
        result = convert_to_float_list([1.0, 2.0])
        self.assertEqual(result, [1.0, 2.0])

    def test_string_with_extra_spaces(self):
        result = convert_to_float_list("  1.0  2.0  ")
        self.assertEqual(result, [1.0, 2.0])

    def test_invalid_string_raises(self):
        with self.assertRaises(ValueError):
            convert_to_float_list("1.0 abc 3.0")


class CountDecimalPlacesTestCase(unittest.TestCase):
    """Tests for count_decimal_places."""

    def test_no_decimals(self):
        self.assertEqual(count_decimal_places(42), 0)

    def test_with_decimals(self):
        self.assertEqual(count_decimal_places(3.14), 2)

    def test_trailing_zeros(self):
        self.assertEqual(count_decimal_places(1.0), 1)


class ValidationResponseTestCase(unittest.TestCase):
    """Tests for ValidationResponse."""

    def test_default_values(self):
        resp = ValidationResponse()
        self.assertEqual(resp.status, InputStatus.GOOD)
        self.assertEqual(resp.message, "")

    def test_custom_values(self):
        resp = ValidationResponse(InputStatus.ERROR, "bad value")
        self.assertEqual(resp.status, InputStatus.ERROR)
        self.assertEqual(resp.message, "bad value")

    def test_str_representation(self):
        resp = ValidationResponse(InputStatus.WARN, "caution")
        self.assertIn("caution", str(resp))
