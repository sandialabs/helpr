"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import unittest

from utils.units_of_measurement import Distance, Pressure, Temperature, Fracture, SmallDistance, Percent, Unitless

DELTA = 1e-5


class DistanceConversionTestCase(unittest.TestCase):
    def test_m(self):
        """ Tests conversions from m to other distance units. """
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.m, new=Distance.mm), 50, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.m, new=Distance.mm), 1000, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.m, new=Distance.m), 0.05, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.m, new=Distance.m), 1, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.m, new=Distance.km), 5e-5, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.m, new=Distance.km), 1e-3, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.m, new=Distance.inch), 1.9685, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.m, new=Distance.inch), 39.37008, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.m, new=Distance.ft), 0.16404, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.m, new=Distance.ft), 3.28084, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.m, new=Distance.mi), 3.11e-5, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.m, new=Distance.mi), 6.21e-4, delta=DELTA)

    def test_mm(self):
        """ Tests conversions from mm. """
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mm, new=Distance.mm), 0.05, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mm, new=Distance.mm), 1, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mm, new=Distance.m), 5e-5, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mm, new=Distance.m), 1e-3, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mm, new=Distance.km), 5e-8, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mm, new=Distance.km), 1e-6, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mm, new=Distance.inch), 1.9685e-3, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mm, new=Distance.inch), 3.937e-2, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mm, new=Distance.ft), 1.6404e-4, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mm, new=Distance.ft), 3.28084e-3, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mm, new=Distance.mi), 3.11e-8, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mm, new=Distance.mi), 6.21e-7, delta=DELTA)

    def test_km(self):
        """ Tests conversions from km. """
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.km, new=Distance.mm), 5e4, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.km, new=Distance.mm), 1e6, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.km, new=Distance.m), 50, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.km, new=Distance.m), 1e3, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.km, new=Distance.km), 0.05, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.km, new=Distance.km), 1.0, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.km, new=Distance.inch), 1968.5, places=1)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.km, new=Distance.inch), 39370.1, places=1)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.km, new=Distance.ft), 164.04, places=2)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.km, new=Distance.ft), 3280.84, places=2)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.km, new=Distance.mi), 3.11e-2, places=0)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.km, new=Distance.mi), 0.62137, delta=DELTA)

    def test_inch(self):
        """ Tests conversions from inches. """
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.inch, new=Distance.mm), 1.27, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.inch, new=Distance.mm), 25.4, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.inch, new=Distance.m), 1.27e-3, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.inch, new=Distance.m), 2.54e-2, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.inch, new=Distance.km), 1.27e-6, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.inch, new=Distance.km), 2.54e-5, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.inch, new=Distance.inch), 0.05, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.inch, new=Distance.inch), 1, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.inch, new=Distance.ft), 4.1667e-3, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.inch, new=Distance.ft), 8.333e-2, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.inch, new=Distance.mi), 7.89e-7, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.inch, new=Distance.mi), 1.58e-5, delta=DELTA)

    def test_ft(self):
        """ Tests conversions from ft. """
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.ft, new=Distance.mm), 15.24, places=0)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.ft, new=Distance.mm), 304.8, places=0)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.ft, new=Distance.m), 1.524e-2, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.ft, new=Distance.m), 0.3048, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.ft, new=Distance.km), 1.524e-5, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.ft, new=Distance.km), 3.048e-4, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.ft, new=Distance.inch), 0.6, places=2)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.ft, new=Distance.inch), 12, places=2)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.ft, new=Distance.ft), 0.05, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.ft, new=Distance.ft), 1, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.ft, new=Distance.mi), 9.47e-6, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.ft, new=Distance.mi), 1.89e-4, delta=DELTA)

    def test_mi(self):
        """ Tests conversions from mi. """
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mi, new=Distance.mm), 80467, places=1)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mi, new=Distance.mm), 1609340, places=1)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mi, new=Distance.m), 80.47, places=1)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mi, new=Distance.m), 1609.34, places=1)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mi, new=Distance.km), 8.0467e-2, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mi, new=Distance.km), 1.60934, delta=DELTA)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mi, new=Distance.inch), 3167.99, places=2)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mi, new=Distance.inch), 63359.84, places=2)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mi, new=Distance.ft), 264, places=1)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mi, new=Distance.ft), 5280, places=1)
        self.assertAlmostEqual(Distance.convert(val=0.05,   old=Distance.mi, new=Distance.mi), 0.05, places=2)
        self.assertAlmostEqual(Distance.convert(val=1.0,    old=Distance.mi, new=Distance.mi), 1.00, places=2)


class SmallDistanceConversionTestCase(unittest.TestCase):
    def test_m(self):
        """ Tests conversions from m to other units. """
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.m, new=SmallDistance.mm), 50, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.m, new=SmallDistance.mm), 1000, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.m, new=SmallDistance.m), 0.05, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.m, new=SmallDistance.m), 1, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.m, new=SmallDistance.inch), 1.9685, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.m, new=SmallDistance.inch), 39.37008, delta=DELTA)

    def test_mm(self):
        """ Tests conversions from mm. """
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.mm, new=SmallDistance.mm), 0.05, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.mm, new=SmallDistance.mm), 1, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.mm, new=SmallDistance.m), 5e-5, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.mm, new=SmallDistance.m), 1e-3, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.mm, new=SmallDistance.inch), 1.9685e-3, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.mm, new=SmallDistance.inch), 3.937e-2, delta=DELTA)

    def test_inch(self):
        """ Tests conversions from inches. """
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.inch, new=SmallDistance.mm), 1.27, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.inch, new=SmallDistance.mm), 25.4, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.inch, new=SmallDistance.m), 1.27e-3, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.inch, new=SmallDistance.m), 2.54e-2, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=0.05,   old=SmallDistance.inch, new=SmallDistance.inch), 0.05, delta=DELTA)
        self.assertAlmostEqual(SmallDistance.convert(val=1.0,    old=SmallDistance.inch, new=SmallDistance.inch), 1, delta=DELTA)


class PressureConversionTestCase(unittest.TestCase):
    def test_mpa(self):
        """ Tests conversions from mpa. """
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.mpa, new=Pressure.mpa), 0.05, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.mpa, new=Pressure.mpa), 1, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.mpa, new=Pressure.psi), 7.25189, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.mpa, new=Pressure.psi), 145.03768, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.mpa, new=Pressure.bar), 0.5, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.mpa, new=Pressure.bar), 10, delta=DELTA)

    def test_psi(self):
        """ Tests conversions from psi. """
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.psi, new=Pressure.mpa), 3.45e-4, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.psi, new=Pressure.mpa), 6.895e-3, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.psi, new=Pressure.psi), 0.05, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.psi, new=Pressure.psi), 1.00, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.psi, new=Pressure.bar), 3.45e-3, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.psi, new=Pressure.bar), 6.895e-2, delta=DELTA)

    def test_bar(self):
        """ Tests conversions from bar. """
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.bar, new=Pressure.mpa), 0.005, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.bar, new=Pressure.mpa), 0.1, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.bar, new=Pressure.psi), 0.725189, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.bar, new=Pressure.psi), 14.503768, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=0.05,   old=Pressure.bar, new=Pressure.bar), 0.05, delta=DELTA)
        self.assertAlmostEqual(Pressure.convert(val=1.00,   old=Pressure.bar, new=Pressure.bar), 1.00, delta=DELTA)


class TemperatureConversionTestCase(unittest.TestCase):
    def test_k(self):
        """ Tests conversions from k. """
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.k, new=Temperature.k), 0.05, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.k, new=Temperature.k), 1, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=273,     old=Temperature.k, new=Temperature.k), 273, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=315,     old=Temperature.k, new=Temperature.k), 315, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.k, new=Temperature.c), -273.10, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.k, new=Temperature.c), -272.15, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=273,     old=Temperature.k, new=Temperature.c), -0.15, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=315,     old=Temperature.k, new=Temperature.c), 41.85, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.k, new=Temperature.f), -459.58, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.k, new=Temperature.f), -457.87, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=273,     old=Temperature.k, new=Temperature.f), 31.73, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=315,     old=Temperature.k, new=Temperature.f), 107.33, delta=DELTA)

    def test_c(self):
        """ Tests conversions from c. """
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.c, new=Temperature.k), 273.2, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.c, new=Temperature.k), 274.15, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=-273,    old=Temperature.c, new=Temperature.k), 0.15, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=41,      old=Temperature.c, new=Temperature.k), 314.15, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=100,     old=Temperature.c, new=Temperature.k), 373.15, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.c, new=Temperature.c), 0.05, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.c, new=Temperature.c), 1.00, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=-273,    old=Temperature.c, new=Temperature.c), -273, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=41,      old=Temperature.c, new=Temperature.c), 41.0, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=100,     old=Temperature.c, new=Temperature.c), 100, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.c, new=Temperature.f), 32.09, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.c, new=Temperature.f), 33.8, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=-273,    old=Temperature.c, new=Temperature.f), -459.4, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=41,      old=Temperature.c, new=Temperature.f), 105.8, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=100,     old=Temperature.c, new=Temperature.f), 212, delta=DELTA)

    def test_f(self):
        """ Tests conversions from f. """
        self.assertAlmostEqual(Temperature.convert(val=-460,    old=Temperature.f, new=Temperature.k), -0.183333, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.f, new=Temperature.k), 255.4, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.f, new=Temperature.k), 255.92777, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=41,      old=Temperature.f, new=Temperature.k), 278.15, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=100,     old=Temperature.f, new=Temperature.k), 310.92777, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=212,     old=Temperature.f, new=Temperature.k), 373.15, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=-460,    old=Temperature.f, new=Temperature.c), -273.33333, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.f, new=Temperature.c), -17.75, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.f, new=Temperature.c), -17.22222, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=41,      old=Temperature.f, new=Temperature.c), 5, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=100,     old=Temperature.f, new=Temperature.c), 37.77777, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=212,     old=Temperature.f, new=Temperature.c), 100, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=-460,    old=Temperature.f, new=Temperature.f), -460, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=0.05,    old=Temperature.f, new=Temperature.f), 0.05, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=1,       old=Temperature.f, new=Temperature.f), 1, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=41,      old=Temperature.f, new=Temperature.f), 41, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=100,     old=Temperature.f, new=Temperature.f), 100, delta=DELTA)
        self.assertAlmostEqual(Temperature.convert(val=212,     old=Temperature.f, new=Temperature.f), 212, delta=DELTA)


class FractureConversionTestCase(unittest.TestCase):
    def test_mpm(self):
        """ Tests conversions from mpm. """
        self.assertAlmostEqual(Fracture.convert(val=0.05,   old=Fracture.mpm, new=Fracture.mpm), 0.05, delta=DELTA)
        self.assertAlmostEqual(Fracture.convert(val=1.00,   old=Fracture.mpm, new=Fracture.mpm), 1.00, delta=DELTA)
        self.assertAlmostEqual(Fracture.convert(val=100,   old=Fracture.mpm, new=Fracture.mpm), 100, delta=DELTA)


class UnitlessConversionTestCase(unittest.TestCase):
    def test_unitless(self):
        """ Tests conversion attempts with unitless. """
        self.assertAlmostEqual(Unitless.convert(val=0.05), 0.05, delta=DELTA)
        self.assertAlmostEqual(Unitless.convert(val=1.00), 1, delta=DELTA)
        self.assertAlmostEqual(Unitless.convert(val=100), 100, delta=DELTA)
        self.assertAlmostEqual(Unitless.convert(val=0.05, old=Unitless.std_unit), 0.05, delta=DELTA)
        self.assertAlmostEqual(Unitless.convert(val=1.00, new=Unitless.std_unit), 1, delta=DELTA)
        self.assertAlmostEqual(Unitless.convert(val=100, old=Unitless.std_unit, new=Unitless.std_unit), 100, delta=DELTA)


class PercentConversionTestCase(unittest.TestCase):
    def test_percent(self):
        """ Tests conversions attempts with percents. """
        self.assertAlmostEqual(Percent.convert(val=0.05), 0.05, delta=DELTA)
        self.assertAlmostEqual(Percent.convert(val=1), 1, delta=DELTA)
        self.assertAlmostEqual(Percent.convert(val=0.05, old=Percent.p), 0.05, delta=DELTA)
        self.assertAlmostEqual(Percent.convert(val=1, old=Percent.p, new=Percent.p), 1, delta=DELTA)
        self.assertAlmostEqual(Percent.convert(val=1, new=Percent.p), 1, delta=DELTA)
        self.assertAlmostEqual(Percent.convert(val=10, old=Percent.p, new=Percent.p), 10, delta=DELTA)
        self.assertAlmostEqual(Percent.convert(val=100, new=Percent.p), 100, delta=DELTA)


if __name__ == '__main__':
    unittest.main()
