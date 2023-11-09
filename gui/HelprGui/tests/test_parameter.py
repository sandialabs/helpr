"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import unittest
from utils.distributions import Distributions
from utils.units_of_measurement import Distance, SmallDistance, Pressure, Fracture, Temperature
from parameters.models import Parameter as Param

DELTA = 1e-4


class ParameterInitializationTestCase(unittest.TestCase):
    """
    Verify creation of Parameter model with standard and non-standard units.
    Note: don't test unit conversions here.
    """

    def test_distance_init_det_std(self):
        """ Distance parameter with standard unit is initialized and displayed accurately. """
        val_m = 0.609
        par = Param('Outer diameter', value=val_m, unit_type=Distance)
        self.assertAlmostEqual(par._value, val_m, delta=DELTA)
        self.assertEqual(par._a, 0)
        self.assertEqual(par._b, 0)
        self.assertEqual(par.unit, Distance.m)
        self.assertTrue(par.unit_type, Distance)
        self.assertEqual(par.distr, 'det')

        # display values
        self.assertAlmostEqual(par.value, val_m)

    def test_distance_init_det_inch(self):
        """ Distance parameter with non-standard unit is initialized accurately. """
        val_inch = 24
        val_m = 0.6095
        par = Param('Outer diameter', value=val_inch, unit=Distance.inch)
        self.assertAlmostEqual(par._value, val_m, delta=DELTA)
        self.assertEqual(par._a, 0)
        self.assertEqual(par._b, 0)
        self.assertAlmostEqual(par.value, val_inch, delta=DELTA)
        self.assertEqual(par.unit, Distance.inch)
        self.assertTrue(par.unit_type, Distance)
        self.assertEqual(par.distr, 'det')

    def test_temp_init_det_k(self):
        """ Temperature parameter with standard unit is initialized and displayed accurately. """
        val_k = 301
        par = Param('Temperature', value=val_k, unit_type=Temperature)
        self.assertAlmostEqual(par._value, val_k, delta=DELTA)
        self.assertEqual(par._a, 0)
        self.assertEqual(par._b, 0)
        self.assertTrue(par.unit_type, Temperature)
        self.assertEqual(par.unit, Temperature.k)
        self.assertEqual(par.distr, 'det')

        # display values
        self.assertAlmostEqual(par.value, val_k)

    def test_temp_init_det_c(self):
        """ Temperature parameter with non-standard unit is initialized accurately. """
        val_c = 35
        val_k = 308.15
        par = Param('Temperature', value=val_c, unit=Temperature.c)
        self.assertAlmostEqual(par._value, val_k, delta=DELTA)
        self.assertEqual(par._a, 273.15)
        self.assertEqual(par._b, 273.15)
        self.assertTrue(par.unit_type, Temperature)
        self.assertEqual(par.unit, Temperature.c)
        self.assertAlmostEqual(par.value, val_c, delta=DELTA)
        self.assertEqual(par.distr, 'det')

    def test_param_slug_from_label(self):
        """ Parameter slug value accurately determined from label. """
        val = 35
        par = Param('Temperature', value=val, unit=Temperature.c)
        self.assertEqual(par.slug, 'temperature')

        par = Param('Outer Diameter', value=val, unit=Distance.inch)
        self.assertEqual(par.slug, 'outer_diameter')


class ParameterUnitChangeTestCase(unittest.TestCase):
    """
    Verify handling of unit changes within Parameter.

    """

    def test_change_unit_from_m_to_inch(self):
        """ Changing unit from std to non-std is reflected in parameter but displayed value is unchanged. """
        orig = 2
        disp = 2
        par = Param('Outer diameter', value=orig, unit=Distance.m)
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
        par = Param('Outer diameter', value=orig, unit=Distance.mm)
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
        par = Param('Outer diameter', value=orig, unit=Distance.inch)
        self.assertAlmostEqual(par.value, orig, delta=DELTA)
        self.assertAlmostEqual(par._value, raw, delta=DELTA)

        par.set_unit_from_display(Distance.mm)
        new_disp = 5.443
        new_raw = 5.443 / 1000
        self.assertAlmostEqual(par.value, new_disp, delta=DELTA)
        self.assertAlmostEqual(par._value, new_raw, delta=DELTA)
        self.assertEqual(par.unit, Distance.mm)


class ParameterOutputTestCase(unittest.TestCase):

    def test_prepped_values(self):
        pass

    def test_dist_to_dict_contents(self):
        par = Param('Outer diameter', value=30, unit=Distance.inch)
        out = par.to_dict()
        keys = out.keys()
        self.assertIs(type(out), dict)

        actual_keys = ['label', 'slug', 'unit_type', 'unit', 'uncertainty',
                       'value', 'min_value', 'max_value', 'distr', 'a', 'b']
        self.assertIs(len(keys), len(actual_keys))
        for key in actual_keys:
            self.assertTrue(key in keys)

    def test_to_dict_data_types(self):
        par = Param('Outer diameter', value=30, unit=Distance.inch)
        out = par.to_dict()
        str_keys = ['label', 'slug', 'unit_type', 'unit', 'uncertainty',
                    'min_value', 'max_value', 'distr', ]
        float_keys = ['value', 'a', 'b']

        for key in str_keys:
            self.assertIs(type(out[key]), str)

        for key in float_keys:
            self.assertIs(type(out[key]), float)

    def test_to_dict_prob_data_when_deterministic(self):
        par = Param('Outer diameter', value=30, unit=Distance.inch)
        out = par.to_dict()
        self.assertAlmostEqual(out['a'], 0., delta=DELTA)
        self.assertAlmostEqual(out['b'], 0., delta=DELTA)
        self.assertIs(out['distr'], 'det')

    def test_to_dict_saves_in_std_units(self):
        par = Param('Outer diameter', value=30, unit=Distance.inch)
        out = par.to_dict()
        self.assertAlmostEqual(out['value'], 0.762, delta=DELTA)
        self.assertIs(out['unit'], 'in')
        self.assertIs(out['unit_type'], 'dist')

    def test_dist_from_dict(self):
        pass


class UnitDisplayTestCase(unittest.TestCase):
    def test_distance_display_inch(self):
        """ Tests that non-standard unit is stored in standard units and displayed in selected unit. """
        par = Param('Outer diameter', unit=Distance.inch, distr=Distributions.uni, value=22, a=21.9, b=22.1)
        self.assertAlmostEqual(par._value, 0.5588, delta=DELTA)
        self.assertAlmostEqual(par._a, 0.55626, delta=DELTA)
        self.assertAlmostEqual(par._b, 0.56134, delta=DELTA)
        self.assertAlmostEqual(par.value, 22, delta=DELTA)
        self.assertAlmostEqual(par.a, 21.9, delta=DELTA)
        self.assertAlmostEqual(par.b, 22.1, delta=DELTA)

    def test_distance_display_m(self):
        par = Param('Outer diameter', unit=Distance.m, distr=Distributions.uni, value=22, a=21.9, b=22.1)
        self.assertAlmostEqual(par._value, 22, delta=DELTA)
        self.assertAlmostEqual(par._a, 21.9, delta=DELTA)
        self.assertAlmostEqual(par._b, 22.1, delta=DELTA)
        self.assertAlmostEqual(par.value, 22, delta=DELTA)
        self.assertAlmostEqual(par.a, 21.9, delta=DELTA)
        self.assertAlmostEqual(par.b, 22.1, delta=DELTA)

    def test_pressure_display_psi(self):
        """ Ensure user-input pressure value is displayed accurately. """
        par = Param('Max pressure', unit=Pressure.psi, distr=Distributions.nor, value=0.85, a=0.85, b=0.02)
        self.assertAlmostEqual(par._value, 0.00586, delta=DELTA)
        self.assertAlmostEqual(par._a, 0.005861, delta=DELTA)
        self.assertAlmostEqual(par._b, 0.000138, delta=DELTA)
        self.assertAlmostEqual(par.value, 0.85, delta=DELTA)
        self.assertAlmostEqual(par.a, 0.85, delta=DELTA)
        self.assertAlmostEqual(par.b, 0.02, delta=DELTA)

    def test_pressure_display_mpa(self):
        """ Ensure user-input pressure std value is displayed accurately. """
        par = Param('Max pressure', unit=Pressure.mpa, distr=Distributions.nor, value=0.85, a=0.85, b=0.02)
        self.assertAlmostEqual(par._value, 0.85, delta=DELTA)
        self.assertAlmostEqual(par._a, 0.85, delta=DELTA)
        self.assertAlmostEqual(par._b, 0.02, delta=DELTA)
        self.assertAlmostEqual(par.value, 0.85, delta=DELTA)
        self.assertAlmostEqual(par.a, 0.85, delta=DELTA)
        self.assertAlmostEqual(par.b, 0.02, delta=DELTA)

    def test_temperature_display_c(self):
        """ Ensure user-input temperature value is displayed correctly. """
        par = Param('Temperature', unit=Temperature.c, distr=Distributions.nor, value=15, a=13.5, b=21)
        self.assertAlmostEqual(par._value, 288.15, delta=DELTA)
        self.assertAlmostEqual(par._a, 286.65, delta=DELTA)
        self.assertAlmostEqual(par._b, 294.15, delta=DELTA)
        self.assertAlmostEqual(par.value, 15, delta=DELTA)
        self.assertAlmostEqual(par.a, 13.5, delta=DELTA)
        self.assertAlmostEqual(par.b, 21, delta=DELTA)

    def test_temperature_display_k(self):
        """ Ensure user-input temperature std value is displayed accurately. """
        par = Param('Temperature', unit=Temperature.k, distr=Distributions.nor, value=15, a=13.5, b=21)
        self.assertAlmostEqual(par._value, 15, delta=DELTA)
        self.assertAlmostEqual(par._a, 13.5, delta=DELTA)
        self.assertAlmostEqual(par._b, 21, delta=DELTA)
        self.assertAlmostEqual(par.value, 15, delta=DELTA)
        self.assertAlmostEqual(par.a, 13.5, delta=DELTA)
        self.assertAlmostEqual(par.b, 21, delta=DELTA)


if __name__ == '__main__':
    unittest.main()
