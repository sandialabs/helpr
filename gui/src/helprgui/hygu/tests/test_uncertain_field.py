"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import unittest
import importlib

from ..utils.units_of_measurement import Distance, Temperature, Pressure, SmallDistance
from ..utils.distributions import Distributions, Uncertainties
from ..models.fields_probabilistic import UncertainField


DELTA = 1e-4


class UncertainFieldInitTestCase(unittest.TestCase):
    """
    Verify creation of Parameter model with standard and non-standard units.
    Note: don't test unit conversions here.
    """

    def test_distance_init_det_std(self):
        """ Distance parameter with standard unit is initialized and displayed accurately. """
        val_m = 0.609
        par = UncertainField('Outer diameter', value=val_m, unit_type=Distance)
        self.assertAlmostEqual(par._value, val_m, delta=DELTA)
        self.assertEqual(par._mean, 0)
        self.assertEqual(par._std, 1)
        self.assertEqual(par._mu, 0)
        self.assertEqual(par._sigma, 1)
        self.assertEqual(par.unit, Distance.m)
        self.assertTrue(par.unit_type, Distance)
        self.assertEqual(par.distr, 'det')

        # display values
        self.assertAlmostEqual(par.value, val_m)

    def test_distance_init_det_inch(self):
        """ Distance parameter with non-standard unit is initialized accurately. """
        val_inch = 24
        val_m = 0.6095
        par = UncertainField('Outer diameter', value=val_inch, unit=Distance.inch)
        self.assertAlmostEqual(par._value, val_m, delta=DELTA)
        self.assertEqual(par._mean, 0)
        self.assertAlmostEqual(par._std, 0.0254, delta=DELTA)  # Default std=1 inch converted to meters

        self.assertAlmostEqual(par._mu, -3.673, delta=DELTA)
        self.assertEqual(par._sigma, 1)  # sigma is dimensionless, no conversion

        self.assertAlmostEqual(par.value, val_inch, delta=DELTA)

        self.assertEqual(par.unit, Distance.inch)
        self.assertTrue(par.unit_type, Distance)
        self.assertEqual(par.distr, 'det')

    def test_temp_init_det_k(self):
        """ Temperature parameter with standard unit is initialized and displayed accurately. """
        val_k = 301
        par = UncertainField('Temperature', value=val_k, unit_type=Temperature)
        self.assertAlmostEqual(par._value, val_k, delta=DELTA)
        self.assertEqual(par._mean, 0)
        self.assertEqual(par._std, 1)
        self.assertEqual(par._mu, 0)
        self.assertEqual(par._sigma, 1)
        self.assertTrue(par.unit_type, Temperature)
        self.assertEqual(par.unit, Temperature.k)
        self.assertEqual(par.distr, 'det')

        # display values
        self.assertAlmostEqual(par.value, val_k)

    def test_temp_init_det_c(self):
        """ Temperature parameter with non-standard unit is initialized accurately. """
        val_c = 35
        val_k = 308.15
        par = UncertainField('Temperature', value=val_c, unit=Temperature.c)
        self.assertAlmostEqual(par._value, val_k, delta=DELTA)
        self.assertEqual(par._mean, 273.15)
        self.assertEqual(par._std, 1)

        self.assertAlmostEqual(par._mu, 5.6137, delta=DELTA)
        self.assertEqual(par._sigma, 1)

        self.assertTrue(par.unit_type, Temperature)
        self.assertEqual(par.unit, Temperature.c)
        self.assertAlmostEqual(par.value, val_c, delta=DELTA)
        self.assertEqual(par.distr, 'det')

    def test_param_slug_from_label(self):
        """ Parameter slug value accurately determined from label. """
        val = 35
        par = UncertainField('Temperature', value=val, unit=Temperature.c)
        self.assertEqual(par.slug, 'temperature')

        par = UncertainField('Outer Diameter', value=val, unit=Distance.inch)
        self.assertEqual(par.slug, 'outer_diameter')


class UncertainFieldUnitChangeTestCase(unittest.TestCase):
    """ Verify handling of unit changes within Parameter. """

    def test_change_unit_from_m_to_inch(self):
        """ Changing unit from std to non-std is reflected in parameter but displayed value is unchanged. """
        orig = 2
        disp = 2
        par = UncertainField('Outer diameter', value=orig, unit=Distance.m)
        self.assertAlmostEqual(par._value, orig, delta=DELTA)
        self.assertAlmostEqual(par.value, disp, delta=DELTA)
        par.set_unit_from_display(Distance.inch)

        raw = 0.0508  # 2 inches in meters
        self.assertAlmostEqual(par.value, disp, delta=DELTA)
        self.assertAlmostEqual(par._value, raw, delta=DELTA)
        self.assertEqual(par.unit, Distance.inch)

    def test_change_unit_from_mm_to_m(self):
        """ Changing unit from non-std to std is reflected in parameter display. """
        orig = 20.4
        raw = orig / 1000
        par = UncertainField('Outer diameter', value=orig, unit=Distance.mm)
        self.assertAlmostEqual(par._value, raw, delta=DELTA)
        self.assertAlmostEqual(par.value, orig, delta=DELTA)

        par.set_unit_from_display(Distance.m)
        new_raw = 20.4
        new_disp = 20.4
        self.assertAlmostEqual(par.value, new_disp, delta=DELTA)
        self.assertAlmostEqual(par._value, new_raw, delta=DELTA)
        self.assertEqual(par.unit, Distance.m)

    def test_change_unit_from_inch_to_mm(self):
        """ Changing unit from non-std to non-std is reflected in parameter but displayed value is unchanged. """
        orig = 5.443
        raw = 0.1383
        par = UncertainField('Outer diameter', value=orig, unit=Distance.inch)
        self.assertAlmostEqual(par.value, orig, delta=DELTA)
        self.assertAlmostEqual(par._value, raw, delta=DELTA)

        par.set_unit_from_display(Distance.mm)
        new_disp = 5.443
        new_raw = 5.443 / 1000
        self.assertAlmostEqual(par.value, new_disp, delta=DELTA)
        self.assertAlmostEqual(par._value, new_raw, delta=DELTA)
        self.assertEqual(par.unit, Distance.mm)


class FieldOutputTestCase(unittest.TestCase):

    def test_prepped_values(self):
        pass

    def test_dist_to_dict_contents(self):
        par = UncertainField('Outer diameter', value=30, unit=Distance.inch)
        out = par.to_dict()
        keys = out.keys()
        self.assertIs(type(out), dict)

        actual_keys = ['label', 'slug', 'unit_type', 'unit', 'uncertainty',
                       'value', 'min_value', 'max_value', 'distr']
        self.assertIs(len(keys), len(actual_keys))
        for key in actual_keys:
            self.assertTrue(key in keys)

    def test_to_dict_data_types(self):
        par = UncertainField('Outer diameter', value=30, unit=Distance.inch)
        out = par.to_dict()
        str_keys = ['label', 'slug', 'unit_type', 'unit', 'uncertainty',
                    'min_value', 'max_value', 'distr', ]
        float_keys = ['value']

        for key in str_keys:
            self.assertIs(type(out[key]), str)

        for key in float_keys:
            self.assertIs(type(out[key]), float)

    def test_to_dict_prob_data_when_deterministic(self):
        par = UncertainField('Outer diameter', value=30, unit=Distance.inch)
        out = par.to_dict()
        self.assertTrue('mean' not in out)
        self.assertTrue('std' not in out)
        self.assertTrue('mu' not in out)
        self.assertTrue('lower' not in out)
        self.assertIs(out['distr'], 'det')

    def test_to_dict_saves_in_std_units(self):
        par = UncertainField('Outer diameter', value=30, unit=Distance.inch)
        out = par.to_dict()
        self.assertAlmostEqual(out['value'], 0.762, delta=DELTA)
        self.assertIs(out['unit'], 'in')
        self.assertIs(out['unit_type'], 'dist_sm')

    def test_dist_from_dict(self):
        pass


class UnitDisplayTestCase(unittest.TestCase):
    def test_distance_display_inch(self):
        """ Tests that non-standard unit is stored in standard units and displayed in selected unit. """
        par = UncertainField('Outer diameter', unit=Distance.inch, distr=Distributions.uni, value=22, lower=21.9, upper=22.1)
        self.assertAlmostEqual(par._value, 0.5588, delta=DELTA)
        self.assertAlmostEqual(par._lower, 0.55626, delta=DELTA)
        self.assertAlmostEqual(par._upper, 0.56134, delta=DELTA)
        self.assertAlmostEqual(par.value, 22, delta=DELTA)
        self.assertAlmostEqual(par.lower, 21.9, delta=DELTA)
        self.assertAlmostEqual(par.upper, 22.1, delta=DELTA)

    def test_distance_display_m(self):
        par = UncertainField('Outer diameter', unit=Distance.m, distr=Distributions.uni, value=22, lower=21.9, upper=22.1)
        self.assertAlmostEqual(par._value, 22, delta=DELTA)
        self.assertAlmostEqual(par._lower, 21.9, delta=DELTA)
        self.assertAlmostEqual(par._upper, 22.1, delta=DELTA)
        self.assertAlmostEqual(par.value, 22, delta=DELTA)
        self.assertAlmostEqual(par.lower, 21.9, delta=DELTA)
        self.assertAlmostEqual(par.upper, 22.1, delta=DELTA)

    def test_pressure_display_psi(self):
        """ Ensure user-input pressure value is displayed accurately. """
        par = UncertainField('Max pressure', unit=Pressure.psi, distr=Distributions.nor, value=0.85, mean=0.85, std=0.02)
        self.assertAlmostEqual(par._value, 0.00586, delta=DELTA)
        self.assertAlmostEqual(par._mean, 0.005861, delta=DELTA)
        self.assertAlmostEqual(par._std, 0.000138, delta=DELTA)
        self.assertAlmostEqual(par.value, 0.85, delta=DELTA)
        self.assertAlmostEqual(par.mean, 0.85, delta=DELTA)
        self.assertAlmostEqual(par.std, 0.02, delta=DELTA)

    def test_pressure_display_mpa(self):
        """ Ensure user-input pressure std value is displayed accurately. """
        par = UncertainField('Max pressure', unit=Pressure.mpa, distr=Distributions.nor, value=0.85, mean=0.85, std=0.02)
        self.assertAlmostEqual(par._value, 0.85, delta=DELTA)
        self.assertAlmostEqual(par._mean, 0.85, delta=DELTA)
        self.assertAlmostEqual(par._std, 0.02, delta=DELTA)
        self.assertAlmostEqual(par.value, 0.85, delta=DELTA)
        self.assertAlmostEqual(par.mean, 0.85, delta=DELTA)
        self.assertAlmostEqual(par.std, 0.02, delta=DELTA)

    def test_temperature_display_c(self):
        """ Ensure user-input temperature value is displayed correctly. """
        par = UncertainField('Temperature', unit=Temperature.c, distr=Distributions.nor, value=15, mean=13.5, std=21)
        self.assertAlmostEqual(par._value, 288.15, delta=DELTA)

        self.assertAlmostEqual(par._mean, 286.65, delta=DELTA)
        self.assertAlmostEqual(par._std, 21, delta=DELTA)

        self.assertAlmostEqual(par.value, 15, delta=DELTA)
        self.assertAlmostEqual(par.mean, 13.5, delta=DELTA)
        self.assertAlmostEqual(par.std, 21, delta=DELTA)

    def test_temperature_display_k(self):
        """ Ensure user-input temperature std value is displayed accurately. """
        par = UncertainField('Temperature', unit=Temperature.k, distr=Distributions.nor, value=15, mean=13.5, std=21)
        self.assertAlmostEqual(par._value, 15, delta=DELTA)
        self.assertAlmostEqual(par._mean, 13.5, delta=DELTA)
        self.assertAlmostEqual(par._std, 21, delta=DELTA)
        self.assertAlmostEqual(par.value, 15, delta=DELTA)
        self.assertAlmostEqual(par.mean, 13.5, delta=DELTA)
        self.assertAlmostEqual(par.std, 21, delta=DELTA)


class UncertainFieldTestCase(unittest.TestCase):
    def setUp(self):
        self.field = UncertainField(
            label='Test Parameter',
            value=10.0,
            unit_type=Distance,
            distr=Distributions.det,
            uncertainty=Uncertainties.ale,
            min_value=0, max_value=100
        )

    def test_initial_values(self):
        self.assertEqual(self.field.distr, Distributions.det)
        self.assertEqual(self.field.uncertainty, Uncertainties.ale)
        # TODO: for deterministic distribution, the descriptive properties should not be accessible
        # with self.assertRaises(AttributeError):
        #     _ = self.field.mean
        # with self.assertRaises(AttributeError):
        #     _ = self.field.std
        # with self.assertRaises(AttributeError):
        #     _ = self.field.mu
        # with self.assertRaises(AttributeError):
        #     _ = self.field.sigma
        # with self.assertRaises(AttributeError):
        #     _ = self.field.lower
        # with self.assertRaises(AttributeError):
        #     _ = self.field.upper

    def test_set_distr_invalid(self):
        with self.assertRaises(ValueError):
            self.field.distr = 'invalid_distr'

    def test_set_uncertainty_invalid(self):
        with self.assertRaises(ValueError):
            self.field.uncertainty = 'invalid_uncertainty'

    def test_is_normal(self):
        self.field.distr = Distributions.nor
        self.assertTrue(self.field.is_normal)

        self.field.distr = Distributions.log
        self.assertTrue(self.field.is_normal)

        self.field.distr = Distributions.det
        self.assertFalse(self.field.is_normal)

    def test_is_scale_unit(self):
        self.unit_type = Temperature
        self.field.unit_type = Temperature
        self.assertTrue(self.field.is_scale_unit)

        # Reset to a non-scale unit type
        self.field.unit_type = None
        self.assertFalse(self.field.is_scale_unit)

    def test_set_values_ignore_lims(self):
        # Test with normal distribution
        self.field.distr = Distributions.nor
        self.field.set_values_ignore_lims(20.0, mean=25.0, std=5.0)
        self.assertEqual(self.field._value, 20.0)
        self.assertEqual(self.field._mean, 25.0)
        self.assertEqual(self.field._std, 5.0)
        
        # Test with uniform distribution
        self.field.distr = Distributions.uni
        self.field.set_values_ignore_lims(30.0, lower=10.0, upper=50.0)
        self.assertEqual(self.field._value, 30.0)
        self.assertEqual(self.field._lower, 10.0)
        self.assertEqual(self.field._upper, 50.0)

    def test_str_display(self):
        self.field.unit = 'm'
        self.field.value = 10.0

        # Deterministic distribution
        display_str = self.field.str_display
        self.assertIn('Test Parameter: 10.0 m', display_str)

        # Normal distribution
        self.field.distr = Distributions.nor
        self.field.mean = 2.0
        self.field.std = 3.0
        display_str = self.field.str_display
        self.assertIn("Normal", display_str)
        self.assertIn("Mean 2.0", display_str)
        self.assertIn("Std 3.0", display_str)

    def test_property_setters(self):
        self.field.distr = Distributions.nor
        self.field.mean = 5.0
        self.assertEqual(self.field.mean, 5.0)

        self.field.std = 6.0
        self.assertEqual(self.field.std, 6.0)
        
        self.field.distr = Distributions.uni
        self.field.lower = 7.0
        self.assertEqual(self.field.lower, 7.0)

        self.field.upper = 8.0
        self.assertEqual(self.field.upper, 8.0)

    def test_setters_with_out_of_bounds(self):
        self.field.distr = Distributions.nor
        old_mean = 50.0
        self.field.mean = old_mean
        # Try to set mean out of bounds
        self.field.mean = -5.0  # Below min_value
        self.assertEqual(self.field.mean, old_mean)  # Should not change

        old_std = 10.0
        self.field.std = old_std
        self.field.std = 200.0  # Above max_value
        self.assertEqual(self.field.std, 200)  # SHOULD change because std is relative to input


class UnitChoiceTestCase(unittest.TestCase):
    def test_limited_pressure_units(self):
        yield_str = UncertainField('Yield strength', unit=Pressure.psi, value=52_000, unit_choices=['mpa', 'psi'])
        self.assertEqual(yield_str.unit_choices_display, ['MPa', 'psi'])
        self.assertEqual(yield_str._unit_choices, ['mpa', 'psi'])

    def test_excluded_last_unit_still_indexes_correctly(self):
        yield_str = UncertainField('Yield strength', unit=Pressure.psi, value=52_000, unit_choices=['mpa', 'psi'])
        self.assertEqual(yield_str.get_unit_index(), 1)
        yield_str.set_unit_from_display('MPa')
        self.assertEqual(yield_str.get_unit_index(), 0)

    def test_excluded_2nd_unit_still_indexes_correctly(self):
        out_diam = UncertainField('Outer diameter', unit=SmallDistance.inch, distr=Distributions.uni,
                                  unit_choices=['m', 'in'],
                                  value=22, lower=21.9, upper=22.1)
        self.assertEqual(out_diam.get_unit_index(), 1)
        self.assertEqual(out_diam.value, 22)
        self.assertEqual(out_diam.value_raw, 0.5588)

        out_diam.set_unit_from_display('m')
        self.assertEqual(out_diam.get_unit_index(), 0)
        self.assertEqual(out_diam.value, 22)
        self.assertEqual(out_diam.value_raw, 22)
