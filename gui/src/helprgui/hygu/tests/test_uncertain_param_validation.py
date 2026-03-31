"""
 Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
 Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

 You should have received a copy of the BSD License along with HELPR.

 """
import unittest
import numpy as np

from ..utils.units_of_measurement import Distance, Temperature, Pressure
from ..utils.distributions import Distributions, DistributionParam as DP
from ..utils.helpers import InputStatus, MathSymbol
from ..models.fields_probabilistic import UncertainField

DELTA = 1e-4


class UncertainFieldTooltipTestCase(unittest.TestCase):
    """Test tooltips for all distribution types and parameters"""

    def test_deterministic_tooltips(self):
        """Test tooltips for deterministic distribution"""
        field = UncertainField('Test', value=10, distr=Distributions.det, tooltip_nominal="Test nominal tooltip")

        nominal_tooltip = field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("Test nominal tooltip", nominal_tooltip)

        # Check validation context
        field = UncertainField('Test', value=10, distr=Distributions.det, min_value=0, max_value=100)
        tooltip = field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("Must be ≥ 0", tooltip)
        self.assertIn("Must be ≤ 100", tooltip)

    def test_normal_tooltips(self):
        """Test tooltips for normal distribution parameters"""
        field = UncertainField('Test', value=10, distr=Distributions.nor,
                               tooltip_mean="Mean tooltip",
                               tooltip_std="Std tooltip")

        mean_tooltip = field.get_sub_tooltip(DP.MEAN)
        self.assertIn("Mean tooltip", mean_tooltip)

        std_tooltip = field.get_sub_tooltip(DP.STD)
        self.assertIn("Std tooltip", std_tooltip)
        self.assertIn("Must be positive (> 0)", std_tooltip)

    def test_lognormal_tooltips(self):
        """Test tooltips for lognormal distribution parameters"""
        field = UncertainField('Test', value=10, distr=Distributions.log,
                               tooltip_mean="Mu tooltip",
                               tooltip_std="Sigma tooltip")

        mean_tooltip = field.get_sub_tooltip(DP.MU)
        self.assertIn(f"{MathSymbol.MU}", mean_tooltip)

        std_tooltip = field.get_sub_tooltip(DP.SIGMA)
        self.assertIn(f"{MathSymbol.SIGMA}", std_tooltip)

    def test_uniform_tooltips(self):
        """Test tooltips for uniform distribution parameters"""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               tooltip_nominal="Nominal tooltip",
                               tooltip_lower="Lower bound tooltip",
                               tooltip_upper="Upper bound tooltip")

        nominal_tooltip = field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("Nominal tooltip", nominal_tooltip)

        lower_tooltip = field.get_sub_tooltip(DP.LOWER)
        self.assertIn("Lower bound tooltip", lower_tooltip)

        upper_tooltip = field.get_sub_tooltip(DP.UPPER)
        self.assertIn("Upper bound tooltip", upper_tooltip)

    def test_truncated_tooltips(self):
        """Test tooltips for truncated normal/lognormal distributions"""
        field = UncertainField('Test', value=50, distr=Distributions.tnor,
                               tooltip_nominal="Nominal tooltip",
                               tooltip_mean="Mean tooltip",
                               tooltip_std="Std tooltip",
                               tooltip_lower="Lower bound tooltip",
                               tooltip_upper="Upper bound tooltip")

        # Check all tooltips exist
        self.assertIn("Nominal tooltip", field.get_sub_tooltip(DP.NOMINAL))
        self.assertIn("Mean tooltip", field.get_sub_tooltip(DP.MEAN))
        self.assertIn("Std tooltip", field.get_sub_tooltip(DP.STD))
        self.assertIn("Lower bound tooltip", field.get_sub_tooltip(DP.LOWER))
        self.assertIn("Upper bound tooltip", field.get_sub_tooltip(DP.UPPER))

    def test_tooltip_content_customization(self):
        """Test that custom tooltip content is properly used"""
        custom_tooltips = {
            "nominal": "Custom nominal tooltip",
            "mean": "Custom mean tooltip",
            "std": "Custom std tooltip",
            "lower": "Custom lower tooltip",
            "upper": "Custom upper tooltip"
        }

        field = UncertainField('Test', value=10,
                               tooltip_nominal=custom_tooltips["nominal"],
                               tooltip_mean=custom_tooltips["mean"],
                               tooltip_std=custom_tooltips["std"],
                               tooltip_lower=custom_tooltips["lower"],
                               tooltip_upper=custom_tooltips["upper"])

        self.assertIn(custom_tooltips["nominal"], field.get_sub_tooltip(DP.NOMINAL))

        field.distr = Distributions.nor
        self.assertIn(custom_tooltips["mean"], field.get_sub_tooltip(DP.MEAN))
        self.assertIn(custom_tooltips["std"], field.get_sub_tooltip(DP.STD))

        field.distr = Distributions.uni
        self.assertIn(custom_tooltips["lower"], field.get_sub_tooltip(DP.LOWER))
        self.assertIn(custom_tooltips["upper"], field.get_sub_tooltip(DP.UPPER))

    def test_tooltip_validation_context_by_distribution(self):
        """Test validation context in tooltips changes based on distribution"""
        field = UncertainField('Test', value=50, min_value=0, max_value=100)

        det_tooltip = field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("Must be ≥ 0", det_tooltip)
        self.assertIn("Must be ≤ 100", det_tooltip)

        field.distr = Distributions.nor
        field.mean = 50
        field.std = 10

        mean_tooltip = field.get_sub_tooltip(DP.MEAN)
        self.assertIn("Must be ≥ 0", mean_tooltip)
        self.assertIn("Must be ≤ 100", mean_tooltip)

        std_tooltip = field.get_sub_tooltip(DP.STD)
        self.assertIn("Must be positive (> 0)", std_tooltip)

        # Check uniform distribution validation context
        field.distr = Distributions.uni
        field.lower = 20
        field.upper = 80

        lower_tooltip = field.get_sub_tooltip(DP.LOWER)
        self.assertIn("Must be ≥ 0", lower_tooltip)

        upper_tooltip = field.get_sub_tooltip(DP.UPPER)
        self.assertIn("Must be ≤ 100", upper_tooltip)

        # Check truncated normal validation context
        field.distr = Distributions.tnor
        field.mean = 50
        field.std = 10
        field.lower = 20
        field.upper = 80

        lower_tooltip = field.get_sub_tooltip(DP.LOWER)
        self.assertIn("Must be ≥ 0", lower_tooltip)
        self.assertIn("Must be ≤ upper bound 80", lower_tooltip)

        upper_tooltip = field.get_sub_tooltip(DP.UPPER)
        self.assertIn("Must be ≥ lower bound 20", upper_tooltip)
        self.assertIn("Must be ≤ 100", upper_tooltip)

    def test_unit_in_tooltips(self):
        """Test that units are correctly added to tooltips"""
        field = UncertainField('Test', value=10, unit=Distance.m,
                               tooltip_nominal="Value")

        tooltip = field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("Value (m)", tooltip)

        # Change unit and check tooltip updates
        field.unit = Distance.mm
        tooltip = field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("Value (mm)", tooltip)

    def test_tooltip_unit_display(self):
        """Test that units are correctly formatted in tooltips for different unit types"""
        # Test Distance units
        dist_field = UncertainField('Length', value=10, unit_type=Distance, unit=Distance.m)
        tooltip = dist_field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("(m)", tooltip)

        dist_field.unit = Distance.mm
        tooltip = dist_field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("(mm)", tooltip)

        # Test Temperature units (special case for scale units)
        temp_field = UncertainField('Temperature', value=20, unit_type=Temperature, unit=Temperature.c)
        tooltip = temp_field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("C)", tooltip)

        temp_field.unit = Temperature.k
        tooltip = temp_field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("(K)", tooltip)

        # Test Pressure units
        press_field = UncertainField('Pressure', value=10, unit_type=Pressure, unit=Pressure.mpa)
        tooltip = press_field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("(MPa)", tooltip)

        press_field.unit = Pressure.psi
        tooltip = press_field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("(psi)", tooltip)

    def test_tooltip_parameter_dependency_context(self):
        """Test that tooltips reflect parameter dependencies"""
        # Uniform distribution with dependencies between parameters
        field = UncertainField('Test', value=50, distr=Distributions.uni, lower=20, upper=80)

        # Nominal value tooltip should reflect bounds
        nominal_tooltip = field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("Must be ≥ lower bound 20", nominal_tooltip)
        self.assertIn("Must be ≤ upper bound 80", nominal_tooltip)

        # Change bounds and check tooltip updates
        field.lower = 30
        field.upper = 70

        nominal_tooltip = field.get_sub_tooltip(DP.NOMINAL)
        self.assertIn("Must be ≥ lower bound 30", nominal_tooltip)
        self.assertIn("Must be ≤ upper bound 70", nominal_tooltip)


class UncertainFieldValidationDeterministicTestCase(unittest.TestCase):
    """Test validation for deterministic distribution values"""

    def setUp(self):
        """Set up test case with deterministic parameter"""
        self.field = UncertainField(
            'Test Parameter',
            value=50,
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

    def test_valid_numeric_values(self):
        """Test validation with various valid numeric values"""
        # Test valid integer
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)
        self.assertEqual(response.message, "")

        # Test valid float
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 50.5)
        self.assertEqual(response.status, InputStatus.GOOD)
        self.assertEqual(response.message, "")

        # Test valid string representation of number
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, "75")
        self.assertEqual(response.status, InputStatus.GOOD)
        self.assertEqual(response.message, "")

        # Test boundary values
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 0)  # min boundary
        self.assertEqual(response.status, InputStatus.GOOD)

        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 100)  # max boundary
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_values(self):
        """Test validation with various invalid values"""
        # Test value below minimum
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below minimum", response.message)

        # Test value above maximum
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 150)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above maximum", response.message)

        # Test non-numeric strings
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, "test")
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)

        # Test complex value
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, "50+5j")
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)

        # Test empty value
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, "")
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)

        # Test None value
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, None)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)

    def test_validation_with_no_limits(self):
        """Test validation when no min/max limits are set"""
        unlimited_field = UncertainField(
            'Unlimited Parameter',
            value=50,
            min_value=-np.inf,
            max_value=np.inf
        )

        # Any numeric value should be valid
        response = unlimited_field.validate_subparam_incoming_value(DP.NOMINAL, -1000)
        self.assertEqual(response.status, InputStatus.GOOD)

        response = unlimited_field.validate_subparam_incoming_value(DP.NOMINAL, 1000)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Still validate type
        response = unlimited_field.validate_subparam_incoming_value(DP.NOMINAL, "text")
        self.assertEqual(response.status, InputStatus.ERROR)

    def test_unit_conversion_in_validation(self):
        """Test that validation correctly handles unit conversions"""
        distance_field = UncertainField(
            'Length',
            value=50,
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

        response = distance_field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        distance_field.unit = Distance.mm

        # Valid: 50 mm is within 0-100000 mm range
        response = distance_field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Invalid: 150_000 mm exceeds 100_000 mm (converted from 100 m)
        response = distance_field.validate_subparam_incoming_value(DP.NOMINAL, 150000)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above maximum", response.message)

    def test_check_valid_method(self):
        """Test the full check_valid method"""
        self.field.value = 50
        valid_response = self.field.check_valid()
        self.assertEqual(valid_response.status, InputStatus.GOOD)

        # Set invalid value, which will be ignored
        self.field.value = 150
        self.assertEqual(self.field.value, 50)
        valid_response = self.field.check_valid()
        self.assertEqual(valid_response.status, InputStatus.GOOD)

        # Change units and test values
        self.field.unit = Distance.mm
        self.field.value = 150
        self.assertEqual(self.field.value, 150)
        valid_response = self.field.check_valid()
        self.assertEqual(valid_response.status, InputStatus.GOOD)

        self.field.value = 6_000
        self.assertEqual(self.field.value, 6_000)
        self.assertEqual(self.field.value_raw, 6)
        valid_response = self.field.check_valid()
        self.assertEqual(valid_response.status, InputStatus.GOOD)

        # Invalid mm value ignored
        self.field.value = 200_000
        self.assertEqual(self.field.value, 6_000)
        self.assertEqual(self.field.value_raw, 6)
        valid_response = self.field.check_valid()
        self.assertEqual(valid_response.status, InputStatus.GOOD)


class UncertainFieldValidationNormalTestCase(unittest.TestCase):
    """Test validation for normal distribution parameters"""

    def setUp(self):
        """Set up test case with normal distribution field"""
        self.field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.nor,
            mean=50,
            std=10,
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

    def test_valid_nominal_value(self):
        """Test validation with valid nominal value"""
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Edge cases: min and max values
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 0)
        self.assertEqual(response.status, InputStatus.GOOD)

        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 100)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_nominal_value(self):
        """Test validation with invalid nominal value"""
        # Below minimum
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below minimum", response.message)

        # Above maximum
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 110)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above maximum", response.message)

        # Non-numeric
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, "text")
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)

    def test_valid_mean(self):
        """Test validation with valid mean value"""
        response = self.field.validate_subparam_incoming_value(DP.MEAN, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Edge cases: min and max values
        response = self.field.validate_subparam_incoming_value(DP.MEAN, 0)
        self.assertEqual(response.status, InputStatus.GOOD)

        response = self.field.validate_subparam_incoming_value(DP.MEAN, 100)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_mean(self):
        """Test validation with invalid mean value"""
        # Below minimum
        response = self.field.validate_subparam_incoming_value(DP.MEAN, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("Mean below minimum", response.message)

        # Above maximum
        response = self.field.validate_subparam_incoming_value(DP.MEAN, 110)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("Mean above maximum", response.message)

    def test_valid_standard_deviation(self):
        """Test validation with valid standard deviation"""
        response = self.field.validate_subparam_incoming_value(DP.STD, 10)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Small positive std is valid
        response = self.field.validate_subparam_incoming_value(DP.STD, 0.001)
        self.assertEqual(response.status, InputStatus.GOOD)

        response = self.field.validate_subparam_incoming_value(DP.STD, 100)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_standard_deviation(self):
        """Test validation with invalid standard deviation"""
        # Negative std dev
        response = self.field.validate_subparam_incoming_value(DP.STD, -5)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)

        # Zero std dev (must be > 0)
        response = self.field.validate_subparam_incoming_value(DP.STD, 0)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)

        # Non-numeric
        response = self.field.validate_subparam_incoming_value(DP.STD, "text")
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)


class UncertainFieldValidationLognormalTestCase(unittest.TestCase):
    """Test validation for lognormal distribution parameters"""

    def setUp(self):
        """Set up test case with lognormal distribution field"""
        self.field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.log,
            mu=3.5,
            sigma=0.5,  # sigma (log-standard deviation)
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

    def test_valid_nominal_value(self):
        """Test validation with valid nominal value for lognormal"""
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Edge cases: min and max values
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 0)
        self.assertEqual(response.status, InputStatus.GOOD)

        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 100)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_nominal_value(self):
        """Test validation with invalid nominal value for lognormal"""
        # Below minimum
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below minimum", response.message)

        # Above maximum
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 150)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above maximum", response.message)

    def test_valid_mu(self):
        """Test validation with valid mu parameter"""
        response = self.field.validate_subparam_incoming_value(DP.MU, 3.5)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Very large mu value
        response = self.field.validate_subparam_incoming_value(DP.MU, 10)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_valid_sigma(self):
        """Test validation with valid sigma parameter"""
        # Positive
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, 0.5)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Very small positive sigma
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, 0.001)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Very large
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, 10)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_sigma(self):
        """Test validation with invalid sigma parameter"""
        # Zero sigma (must be > 0)
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, 0)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)

        # Negative sigma
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, -0.5)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)

        # Non-numeric
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, "text")
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)

    def test_scale_unit_handling(self):
        """Test handling of scale units like temperature for sigma"""
        temp_field = UncertainField(
            'Temperature',
            value=25,
            distr=Distributions.log,
            mu=3.0,
            sigma=0.5,
            min_value=0,
            max_value=100,
            unit_type=Temperature,
            unit=Temperature.c
        )

        # Positive sigma is valid
        response = temp_field.validate_subparam_incoming_value(DP.SIGMA, 0.5)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Negative sigma is invalid (must be > 0)
        response = temp_field.validate_subparam_incoming_value(DP.SIGMA, -0.5)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)


class UncertainFieldValidationUniformTestCase(unittest.TestCase):
    """Test validation for uniform distribution parameters"""

    def setUp(self):
        """Set up test case with uniform distribution field"""
        self.field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.uni,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

    def test_valid_nominal_value(self):
        """Test validation with valid nominal value within bounds"""
        # Middle of range
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        # At lower bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 20)
        self.assertEqual(response.status, InputStatus.GOOD)

        # At upper bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 80)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_nominal_value(self):
        """Test validation with invalid nominal value outside bounds"""
        # Below lower bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Above upper bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 90)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

        # Below min_value
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower", response.message)

        # Above max_value
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 110)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper", response.message)

    def test_valid_lower_bound(self):
        """Test validation with valid lower bound"""
        # Common case
        response = self.field.validate_subparam_incoming_value(DP.LOWER, 10)
        self.assertEqual(response.status, InputStatus.GOOD)

        # At min_value
        response = self.field.validate_subparam_incoming_value(DP.LOWER, 0)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Just below upper bound
        response = self.field.validate_subparam_incoming_value(DP.LOWER, 79)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_lower_bound(self):
        """Test validation with invalid lower bound"""
        # Below min_value
        response = self.field.validate_subparam_incoming_value(DP.LOWER, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below minimum", response.message)

        # Above upper bound
        response = self.field.validate_subparam_incoming_value(DP.LOWER, 90)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

        # Above max_value
        response = self.field.validate_subparam_incoming_value(DP.LOWER, 110)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper", response.message)

        # Non-numeric
        response = self.field.validate_subparam_incoming_value(DP.LOWER, "text")
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)

    def test_valid_upper_bound(self):
        """Test validation with valid upper bound"""
        # Common case
        response = self.field.validate_subparam_incoming_value(DP.UPPER, 90)
        self.assertEqual(response.status, InputStatus.GOOD)

        # At max_value
        response = self.field.validate_subparam_incoming_value(DP.UPPER, 100)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Just above lower bound
        response = self.field.validate_subparam_incoming_value(DP.UPPER, 21)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_upper_bound(self):
        """Test validation with invalid upper bound"""
        # Below lower bound
        response = self.field.validate_subparam_incoming_value(DP.UPPER, 10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Below min_value
        response = self.field.validate_subparam_incoming_value(DP.UPPER, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Above max_value
        response = self.field.validate_subparam_incoming_value(DP.UPPER, 110)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above maximum", response.message)

        # Non-numeric
        response = self.field.validate_subparam_incoming_value(DP.UPPER, "text")
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("valid number", response.message)

    def test_bounds_relationship(self):
        """Test validation when changing bounds relationship"""
        # Set up field with bounds initially far apart
        field = UncertainField(
            'Test',
            value=50,
            distr=Distributions.uni,
            lower=10,
            upper=90,
            min_value=0,
            max_value=100
        )

        response = field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Change lower bound to be above nominal value
        field.lower = 60
        response = field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Reset lower bound
        field.lower = 10

        # Change upper bound to be below nominal value
        field.upper = 40
        response = field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

        # Test with conflicting bounds
        field.lower = 70
        field.upper = 60

        # Both bounds should show validation errors
        response = field.validate_subparam_incoming_value(DP.LOWER, 70)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

        response = field.validate_subparam_incoming_value(DP.UPPER, 60)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

    def test_unit_conversion_in_validation(self):
        """Test that unit conversions are correctly handled in validation"""
        field = UncertainField(
            'Length',
            value=50,
            distr=Distributions.uni,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

        field.unit = Distance.mm

        # Now all values should be in mm
        self.assertAlmostEqual(field.value, 50_000, delta=1)
        self.assertAlmostEqual(field.lower, 20_000, delta=1)
        self.assertAlmostEqual(field.upper, 80_000, delta=1)

        response = field.validate_subparam_incoming_value(DP.NOMINAL, 30)
        self.assertEqual(response.status, InputStatus.GOOD)

        response = field.validate_subparam_incoming_value(DP.NOMINAL, 15)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        response = field.validate_subparam_incoming_value(DP.NOMINAL, 90)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)


class UncertainFieldValidationTruncatedNormalTestCase(unittest.TestCase):
    """Test validation for truncated normal distribution parameters"""

    def setUp(self):
        """Set up test case with truncated normal distribution field"""
        self.field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.tnor,
            mean=50,
            std=10,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

    def test_valid_nominal_value(self):
        """Test validation with valid nominal value within truncation bounds"""
        # Middle of range
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        # At lower truncation bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 20)
        self.assertEqual(response.status, InputStatus.GOOD)

        # At upper truncation bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 80)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_nominal_value(self):
        """Test validation with invalid nominal value outside bounds"""
        # Below lower truncation bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 15)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Above upper truncation bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 85)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

    def test_valid_mean(self):
        """Test validation with valid mean value"""
        response = self.field.validate_subparam_incoming_value(DP.MEAN, 20)
        self.assertEqual(response.status, InputStatus.GOOD)

        response = self.field.validate_subparam_incoming_value(DP.MEAN, 70)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_mean(self):
        """Test validation with invalid mean value"""
        response = self.field.validate_subparam_incoming_value(DP.MEAN, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower", response.message)

        response = self.field.validate_subparam_incoming_value(DP.MEAN, 110)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper", response.message)

    def test_valid_std(self):
        """Test validation with valid standard deviation"""
        response = self.field.validate_subparam_incoming_value(DP.STD, 10)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Small positive is valid
        response = self.field.validate_subparam_incoming_value(DP.STD, 0.001)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_std(self):
        """Test validation with invalid standard deviation"""
        response = self.field.validate_subparam_incoming_value(DP.STD, 0)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)

        # Negative std dev
        response = self.field.validate_subparam_incoming_value(DP.STD, -5)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)

    def test_valid_truncation_bounds(self):
        """Test validation with valid truncation bounds"""
        response = self.field.validate_subparam_incoming_value(DP.LOWER, 10)
        self.assertEqual(response.status, InputStatus.GOOD)

        response = self.field.validate_subparam_incoming_value(DP.UPPER, 90)
        self.assertEqual(response.status, InputStatus.GOOD)

        this_field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.tnor,
            mean=50,
            std=10,
            lower=20,
            upper=90,
            min_value=0,
            max_value=100
        )
        response = this_field.validate_subparam_incoming_value(DP.UPPER, 95)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_truncation_bounds(self):
        """Test validation with invalid truncation bounds"""
        # Lower bound below min_value
        response = self.field.validate_subparam_incoming_value(DP.LOWER, -10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below minimum", response.message)

        # Lower bound above upper bound
        response = self.field.validate_subparam_incoming_value(DP.LOWER, 90)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

        # Upper bound below lower bound
        response = self.field.validate_subparam_incoming_value(DP.UPPER, 10)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Upper bound above max_value
        response = self.field.validate_subparam_incoming_value(DP.UPPER, None)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("must be below maximum", response.message)


class UncertainFieldValidationTruncatedLognormalTestCase(unittest.TestCase):
    """Test validation for truncated lognormal distribution parameters"""

    def setUp(self):
        """Set up test case with truncated lognormal distribution field"""
        self.field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.tlog,
            mu=3.5,
            sigma=0.5,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

    def test_valid_nominal_value(self):
        """Test validation with valid nominal value within truncation bounds"""
        # Middle of range
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.GOOD)

        # At lower truncation bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 20)
        self.assertEqual(response.status, InputStatus.GOOD)

        # At upper truncation bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 80)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_nominal_value(self):
        """Test validation with invalid nominal value outside bounds"""
        # Below lower truncation bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 15)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Above upper truncation bound
        response = self.field.validate_subparam_incoming_value(DP.NOMINAL, 85)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

    def test_valid_mu_sigma(self):
        """Test validation with valid mu and sigma parameters"""
        response = self.field.validate_subparam_incoming_value(DP.MU, 25.0)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Positive sigma is valid
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, 0.5)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Small positive sigma is valid
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, 0.001)
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_invalid_sigma_tlog(self):
        """Test validation with invalid sigma for truncated lognormal"""
        # Zero sigma (must be > 0)
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, 0)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)

        # Negative sigma
        response = self.field.validate_subparam_incoming_value(DP.SIGMA, -0.5)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("positive", response.message)

    def test_truncation_bounds_with_null_upper(self):
        """Test validation with null upper truncation bound (infinity)"""
        field_with_inf = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.tlog,
            mu=3.5,
            sigma=0.5,
            lower=20,
            upper=None,
            min_value=0,
            max_value=100
        )

        # Nominal value only needs to be above lower bound with no upper bound
        response = field_with_inf.validate_subparam_incoming_value(DP.NOMINAL, 90)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Still must be above lower bound
        response = field_with_inf.validate_subparam_incoming_value(DP.NOMINAL, 15)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # And within max_value
        response = field_with_inf.validate_subparam_incoming_value(DP.NOMINAL, 110)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above maximum", response.message)

    def test_null_upper_validation(self):
        """Test validation handling with null (infinity) upper bound"""
        field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.tlog,
            mu=3.5,
            sigma=0.5,
            lower=20,
            upper=None,
            min_value=0
        )

        # Setting upper bound to numeric value should be valid
        response = field.validate_subparam_incoming_value(DP.UPPER, 90)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Setting back to None (infinity) should be valid
        response = field.validate_subparam_incoming_value(DP.UPPER, None)
        print('error')
        print(response)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Setting empty string should convert to None and be valid
        response = field.validate_subparam_incoming_value(DP.UPPER, "")
        print('error')
        print(response)
        self.assertEqual(response.status, InputStatus.GOOD)


class UncertainFieldParameterInteractionsTestCase(unittest.TestCase):
    """Test validation interactions between parameters across different distributions"""

    def test_changing_distribution_type(self):
        """Test validation when changing distribution type"""
        # Start with deterministic distribution
        field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.det,
            min_value=0,
            max_value=100
        )

        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        # Change to uniform distribution - should fail without proper bounds
        field.distr = Distributions.uni
        # Default bounds are both 0 which is invalid for uniform (a should be < b)
        self.assertEqual(field.check_valid().status, InputStatus.ERROR)

        # Set proper bounds for uniform
        field.lower = 20
        field.upper = 80
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        # Change to normal distribution; mean and std should be valid by default
        field.distr = Distributions.nor
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        # Change to truncated normal; prev sub-param values still valid but now mean (0) is below lower bound
        field.distr = Distributions.tnor
        self.assertEqual(field.lower, 20)
        self.assertEqual(field.upper, 80)
        response = field.check_valid()
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("Mean below lower bound", response.message)

        # Enter a compatible mean
        field.mean = 30
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

    def test_cascade_validation_uniform(self):
        """Test cascading validation effects in uniform distribution"""
        field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.uni,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100
        )

        # All parameters valid initially
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        # Raising lower bound above nominal
        field.lower = 60
        # Now nominal is invalid
        response = field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Entire field should be invalid
        self.assertEqual(field.check_valid().status, InputStatus.ERROR)

        # Fix by updating nominal value
        field.value = 70
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        # Now lower upper bound below nominal
        field.upper = 65
        # Now nominal is invalid
        response = field.validate_subparam_incoming_value(DP.NOMINAL, 70)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

        # Overall validation fails
        self.assertEqual(field.check_valid().status, InputStatus.ERROR)

        # Fix by lowering upper bound
        field.value = 62
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

    def test_cascade_validation_truncated(self):
        """Test cascading validation effects in truncated distributions"""
        field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.tnor,
            mean=50,
            std=10,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100
        )

        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        # Change lower bound above nominal
        field.lower = 60
        response = field.validate_subparam_incoming_value(DP.NOMINAL, 50)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("below lower bound", response.message)

        # Entire field should be invalid
        self.assertEqual(field.check_valid().status, InputStatus.ERROR)

        # Fix by updating nominal value and mean
        field.value = 70
        field.mean = 68
        response = field.check_valid()
        print(response)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Now set upper bound below nominal
        field.upper = 65
        response = field.validate_subparam_incoming_value(DP.NOMINAL, 70)
        self.assertEqual(response.status, InputStatus.ERROR)
        self.assertIn("above upper bound", response.message)

        # Overall validation fails
        self.assertEqual(field.check_valid().status, InputStatus.ERROR)

        # Fix by lowering nominal value and mean
        field.value = 62
        field.mean = 63
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

    def test_changing_unit_validation(self):
        """Test validation when changing units"""
        # Create field with distance in meters
        field = UncertainField(
            'Length',
            value=50,
            distr=Distributions.uni,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100,
            unit_type=Distance,
            unit=Distance.m
        )

        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        field.unit = Distance.mm
        # Should still be valid after conversion
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        # Now we're working in mm, so min_value=0, max_value=100_000
        field.value = 79_000
        response = field.check_valid()
        self.assertEqual(response.status, InputStatus.GOOD)

        # Attempting to set above range will fail
        field.value = 110_000
        response = field.check_valid()
        self.assertEqual(response.status, InputStatus.GOOD)
        self.assertEqual(field.value, 79_000)

        # Reset to valid value
        field.value = 50_000
        response = field.check_valid()
        self.assertEqual(response.status, InputStatus.GOOD)

        # Set bounds at edge of limits
        field.lower = 5_000
        field.upper = 95_000
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

    def test_cross_distribution_parameter_reuse(self):
        """Test validation when parameters are reused/repurposed between distributions"""
        field = UncertainField(
            'Test Parameter',
            value=50,
            distr=Distributions.uni,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100
        )

        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        field.distr = Distributions.nor
        self.assertEqual(field.check_valid().status, InputStatus.GOOD)

        field.distr = Distributions.tnor
        field.mean = 20
        response = field.check_valid()
        print('HERE')
        print(response)
        self.assertEqual(response.status, InputStatus.GOOD)

        # Set proper truncation bounds
        field.lower = 20
        field.upper = 80
        response = field.check_valid()
        self.assertEqual(response.status, InputStatus.GOOD)

    def test_check_valid_method_across_distributions(self):
        """Test the check_valid method with different distributions"""
        det_field = UncertainField(
            'Deterministic',
            value=50,
            distr=Distributions.det,
            min_value=0,
            max_value=100
        )

        uni_field = UncertainField(
            'Uniform',
            value=50,
            distr=Distributions.uni,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100
        )

        nor_field = UncertainField(
            'Normal',
            value=50,
            distr=Distributions.nor,
            mean=50,
            std=10,
            min_value=0,
            max_value=100
        )

        tnor_field = UncertainField(
            'Truncated Normal',
            value=50,
            distr=Distributions.tnor,
            mean=50,
            std=10,
            lower=20,
            upper=80,
            min_value=0,
            max_value=100
        )

        # All should be valid
        self.assertEqual(det_field.check_valid().status, InputStatus.GOOD)
        self.assertEqual(uni_field.check_valid().status, InputStatus.GOOD)
        self.assertEqual(nor_field.check_valid().status, InputStatus.GOOD)
        self.assertEqual(tnor_field.check_valid().status, InputStatus.GOOD)

        # std value <= 0 is accepted by setter but fails validation
        nor_field.std = -10
        self.assertEqual(nor_field.std, -10)
        self.assertEqual(nor_field.check_valid().status, InputStatus.ERROR)

        # Enter erroneous values. Invalid values (e.g. outside min/max range) are ignored, and incompatible values show error
        det_field.value = 150
        self.assertEqual(det_field.value, 50)
        self.assertEqual(det_field.check_valid().status, InputStatus.GOOD)

        uni_field.lower = 90
        tnor_field.lower = 90
        self.assertEqual(uni_field.check_valid().status, InputStatus.ERROR)
        self.assertEqual(tnor_field.check_valid().status, InputStatus.ERROR)


if __name__ == '__main__':
    unittest.main()