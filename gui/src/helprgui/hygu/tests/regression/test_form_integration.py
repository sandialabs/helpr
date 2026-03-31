"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Regression tests for UncertainFormField Qt integration.
Verifies Python-QML binding behavior and signal emission.
"""
import unittest

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from ...models.fields_probabilistic import UncertainField
from ...forms.fields_probabilistic import UncertainFormField
from ...utils.distributions import Distributions, DistributionParam as DP
from ...utils.units_of_measurement import Pressure


# Qt Application fixture - needed for signal/slot testing
_app = None


def setUpModule():
    """Create QApplication once for all tests in this module."""
    global _app
    if QCoreApplication.instance() is None:
        _app = QApplication([])


def tearDownModule():
    """Clean up QApplication."""
    global _app
    _app = None


class TestFormFieldSignals(unittest.TestCase):
    """Tests for Qt signal emission from UncertainFormField."""

    def test_value_change_emits_signal(self):
        """Changing value emits valueChanged signal."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        signal_received = []
        form_field.valueChanged.connect(lambda v: signal_received.append(v))

        form_field.value = 75

        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], 75)

    def test_distribution_change_emits_signal(self):
        """Changing distribution emits inputTypeChanged signal."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        signal_received = []
        form_field.inputTypeChanged.connect(lambda v: signal_received.append(v))

        # Distribution order: ['det', 'tnor', 'tlog', 'uni', 'nor', 'log', 'beta']
        # Index 4 is 'nor' (Normal distribution)
        form_field.set_input_type_from_index(4)

        # Signal may be emitted multiple times (once from form, once from model notification)
        self.assertGreaterEqual(len(signal_received), 1)
        # Last signal value should be the new distribution
        self.assertEqual(signal_received[-1], Distributions.nor)

    def test_mean_change_emits_signal(self):
        """Changing mean emits meanChanged signal."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.nor, mean=50, std=10,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        signal_received = []
        form_field.meanChanged.connect(lambda v: signal_received.append(v))

        form_field.mean = 60

        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], 60)

    def test_std_change_emits_signal(self):
        """Changing std emits stdChanged signal."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.nor, mean=50, std=10,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        signal_received = []
        form_field.stdChanged.connect(lambda v: signal_received.append(v))

        form_field.std = 15

        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], 15)

    def test_unit_change_emits_signal(self):
        """Changing unit emits unitChanged signal."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.det, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        signal_received = []
        form_field.unitChanged.connect(lambda v: signal_received.append(v))

        form_field.unit = 'psi'

        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], 'psi')

    def test_validation_change_emits_signal(self):
        """Validation state change emits subparamValidationChanged signal."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               distr=Distributions.nor, mean=50, std=10,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        signal_received = []
        form_field.subparamValidationChanged.connect(
            lambda name, status, msg: signal_received.append((name, status, msg))
        )

        # Trigger validation by changing distribution
        # (this causes update_all_validation_states to be called)
        form_field.set_input_type_from_index(0)  # Switch to deterministic

        # Should have received at least one validation signal
        self.assertGreater(len(signal_received), 0)


class TestFormFieldProperties(unittest.TestCase):
    """Tests for QML-exposed properties of UncertainFormField."""

    def test_is_param_visible_for_deterministic(self):
        """is_param_visible returns correct values for deterministic distribution."""
        field = UncertainField('Test', value=50, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Deterministic only shows nominal
        self.assertTrue(form_field.is_param_visible(DP.NOMINAL))
        self.assertFalse(form_field.is_param_visible(DP.MEAN))
        self.assertFalse(form_field.is_param_visible(DP.STD))
        self.assertFalse(form_field.is_param_visible(DP.MU))
        self.assertFalse(form_field.is_param_visible(DP.SIGMA))
        self.assertFalse(form_field.is_param_visible(DP.LOWER))
        self.assertFalse(form_field.is_param_visible(DP.UPPER))

    def test_is_param_visible_for_normal(self):
        """is_param_visible returns correct values for normal distribution."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Normal shows nominal, mean, std
        self.assertTrue(form_field.is_param_visible(DP.NOMINAL))
        self.assertTrue(form_field.is_param_visible(DP.MEAN))
        self.assertTrue(form_field.is_param_visible(DP.STD))
        self.assertFalse(form_field.is_param_visible(DP.MU))
        self.assertFalse(form_field.is_param_visible(DP.SIGMA))
        self.assertFalse(form_field.is_param_visible(DP.LOWER))
        self.assertFalse(form_field.is_param_visible(DP.UPPER))

    def test_is_param_visible_for_lognormal(self):
        """is_param_visible returns correct values for lognormal distribution."""
        field = UncertainField('Test', value=50, distr=Distributions.log,
                               mu=3.9, sigma=0.2, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Lognormal shows nominal, mu, sigma
        self.assertTrue(form_field.is_param_visible(DP.NOMINAL))
        self.assertFalse(form_field.is_param_visible(DP.MEAN))
        self.assertFalse(form_field.is_param_visible(DP.STD))
        self.assertTrue(form_field.is_param_visible(DP.MU))
        self.assertTrue(form_field.is_param_visible(DP.SIGMA))
        self.assertFalse(form_field.is_param_visible(DP.LOWER))
        self.assertFalse(form_field.is_param_visible(DP.UPPER))

    def test_is_param_visible_for_uniform(self):
        """is_param_visible returns correct values for uniform distribution."""
        field = UncertainField('Test', value=50, distr=Distributions.uni,
                               lower=20, upper=80, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Uniform shows nominal, lower, upper
        self.assertTrue(form_field.is_param_visible(DP.NOMINAL))
        self.assertFalse(form_field.is_param_visible(DP.MEAN))
        self.assertFalse(form_field.is_param_visible(DP.STD))
        self.assertTrue(form_field.is_param_visible(DP.LOWER))
        self.assertTrue(form_field.is_param_visible(DP.UPPER))

    def test_is_param_visible_for_truncated_normal(self):
        """is_param_visible returns correct values for truncated normal."""
        field = UncertainField('Test', value=50, distr=Distributions.tnor,
                               mean=50, std=10, lower=20, upper=80,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Truncated normal shows nominal, mean, std, lower, upper
        self.assertTrue(form_field.is_param_visible(DP.NOMINAL))
        self.assertTrue(form_field.is_param_visible(DP.MEAN))
        self.assertTrue(form_field.is_param_visible(DP.STD))
        self.assertTrue(form_field.is_param_visible(DP.LOWER))
        self.assertTrue(form_field.is_param_visible(DP.UPPER))

    def test_visibility_updates_after_distribution_change(self):
        """Parameter visibility updates when distribution changes."""
        field = UncertainField('Test', value=50, distr=Distributions.det,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Initially deterministic - mean not visible
        self.assertFalse(form_field.is_param_visible(DP.MEAN))

        # Change to normal (index 4 in distribution order)
        # Distribution order: ['det', 'tnor', 'tlog', 'uni', 'nor', 'log', 'beta']
        form_field.set_input_type_from_index(4)  # Normal

        # Now mean should be visible
        self.assertTrue(form_field.is_param_visible(DP.MEAN))

    def test_tooltip_properties_exist(self):
        """Tooltip properties are accessible and return strings."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # All tooltip properties should return strings
        self.assertIsInstance(form_field.nominal_tooltip, str)
        self.assertIsInstance(form_field.mean_tooltip, str)
        self.assertIsInstance(form_field.std_tooltip, str)
        self.assertIsInstance(form_field.mu_tooltip, str)
        self.assertIsInstance(form_field.sigma_tooltip, str)
        self.assertIsInstance(form_field.lower_tooltip, str)
        self.assertIsInstance(form_field.upper_tooltip, str)

    def test_unit_change_keeps_displayed_values_constant(self):
        """Unit change keeps displayed values constant (UI convenience design).

        NOTE: This documents the actual unit conversion behavior:
        - Displayed values stay the same after unit change
        - Internal values change to represent the displayed value in new units
        - This is designed for UI convenience when user switches units
        """
        field = UncertainField('Test', value=1.0, distr=Distributions.nor,
                               mean=0.5, std=0.1, min_value=0, max_value=200,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Record original values
        original_value = form_field.value
        original_mean = form_field.mean

        # Change unit to psi via form field
        form_field.unit = 'psi'

        # Displayed values stay the same (this is the intended behavior)
        # Use almostEqual for floating point comparison
        self.assertAlmostEqual(form_field.value, original_value, delta=0.001)
        self.assertAlmostEqual(form_field.mean, original_mean, delta=0.001)

        # But the unit has changed
        self.assertEqual(form_field.unit, 'psi')


class TestFormFieldValueSync(unittest.TestCase):
    """Tests for value synchronization between model and form field."""

    def test_form_value_reflects_model(self):
        """Form field value matches model value."""
        field = UncertainField('Test', value=50, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        self.assertEqual(form_field.value, 50)

    def test_model_change_reflected_in_form(self):
        """Model value change is reflected in form field."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Change model directly
        field.value = 75

        # Form should reflect the change
        self.assertEqual(form_field.value, 75)

    def test_form_change_reflected_in_model(self):
        """Form field value change is reflected in model."""
        field = UncertainField('Test', value=50, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)
        form_field.value = 75
        self.assertEqual(field.value, 75)

    def test_distribution_params_sync(self):
        """Distribution parameters sync between model and form."""
        field = UncertainField('Test', value=50, distr=Distributions.nor,
                               mean=50, std=10, min_value=0, max_value=100,
                               unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        form_field.mean = 60
        self.assertEqual(field.mean, 60)

        field.std = 15

        # Form should reflect
        self.assertEqual(form_field.std, 15)


class TestFormFieldChoices(unittest.TestCase):
    """Tests for choice list properties (units, distributions)."""

    def test_unit_choices_available(self):
        """Unit choices are available and non-empty."""
        field = UncertainField('Test', value=50, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Should have unit choices
        unit_model = form_field.unit_choices
        self.assertIsNotNone(unit_model)
        self.assertGreater(unit_model.rowCount(), 0)

    def test_distribution_choices_available(self):
        """Distribution choices are available and non-empty."""
        field = UncertainField('Test', value=50, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        # Should have distribution choices
        distr_model = form_field.distr_choices
        self.assertIsNotNone(distr_model)
        self.assertGreater(distr_model.rowCount(), 0)

    def test_get_unit_index_reflects_current_unit(self):
        """get_unit_index() returns correct index for current unit selection."""
        field = UncertainField('Test', value=50, unit_type=Pressure, unit='mpa')
        form_field = UncertainFormField(field)

        initial_index = form_field.get_unit_index()

        # Change unit
        form_field.unit = 'psi'

        # Index should have changed
        self.assertNotEqual(form_field.get_unit_index(), initial_index)


if __name__ == '__main__':
    unittest.main()
