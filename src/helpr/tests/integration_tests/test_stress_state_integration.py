# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import math
from copy import deepcopy

import numpy as np
import xarray as xr

from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.fracture import calc_combined_stress_intensity_factor
from helpr.physics.stress_state import (GenericStressState,
                                        InternalAxialHoopStress,
                                        InternalCircumferentialLongitudinalStress,
                                        calc_r_ratio,
                                        open_nc_table)


class StressStateTestCase(unittest.TestCase):
    """
    Class for unit tests of stress state module.
    
    Attributes
    ----------
    max_pressure : float
        Maximum pressure value used in the tests.
    min_pressure : float
        Minimum pressure value used in the tests.
    temperature : float
        Temperature value used in the tests.
    flaw_depth : float
        Depth of the flaw used in the tests.
    flaw_length : float
        Length of the flaw used in the tests.
    fracture_resistance : float
        Fracture resistance value used in the tests.
    yield_strength : float
        Yield strength value used in the tests.
    stress_intensity_method : str
        Stress intensity method used in the tests.
    pipe : Pipe
        Pipe object used in the tests.
    internal_defect : DefectSpecification
        Internal defect specification used in the tests.
    external_defect : DefectSpecification
        External defect specification used in the tests.
    material : MaterialSpecification
        Material specification used in the tests.
    environment : EnvironmentSpecification
        Environment specification used in the tests.
    """

    def setUp(self):
        """Sets up the test case by initializing the attributes."""
        self.max_pressure = 13
        self.min_pressure = 1
        temperature = 300
        self.flaw_depth = 5
        self.flaw_length = 0.01
        self.fracture_resistance = 44
        self.yield_strength = 670
        self.stress_intensity_method = 'anderson'
        self.pipe = Pipe(outer_diameter=3,
                         wall_thickness=0.1)
        self.internal_defect = DefectSpecification(flaw_depth=self.flaw_depth,
                                                   flaw_length=self.flaw_length,
                                                   surface='inside')
        self.external_defect = DefectSpecification(flaw_depth=self.flaw_depth,
                                                   flaw_length=self.flaw_length,
                                                   surface='outside')
        self.material = MaterialSpecification(yield_strength=self.yield_strength,
                                              fracture_resistance=self.fracture_resistance)
        self.environment = EnvironmentSpecification(max_pressure=self.max_pressure,
                                                    min_pressure=self.min_pressure,
                                                    temperature=temperature,
                                                    volume_fraction_h2=1.0)

    def test_generic_stress_state_specification(self):
        """
        Unit test of generic stress state state specification.
        
        Raises
        ------
        ValueError
            If the generic stress state specification is invalid.
        """
        with self.assertRaises(ValueError):
            GenericStressState(self.pipe,
                               self.environment,
                               self.material,
                               self.internal_defect,
                               self.stress_intensity_method)

    def test_circumferential_longitudinal_stress_state_specification(self):
        """Unit test of longitudinal stress states specification."""
        stress_state = InternalCircumferentialLongitudinalStress(self.pipe,
                                                                 self.environment,
                                                                 self.material,
                                                                 self.internal_defect,
                                                                 self.stress_intensity_method)
        self.assertTrue(stress_state.initial_crack_depth > 0)

    def test_circumferential_longitudinal_stress_check(self):
        """
        Unit test of check of axial longitudinal stress exceeding yield strength.
        
        Raises
        ------
        Warning
            If the axial longitudinal stress exceeds the yield strength.
        """
        material = MaterialSpecification(yield_strength=1.03E1,
                                            fracture_resistance=self.fracture_resistance)
        with self.assertWarns(Warning):
            InternalCircumferentialLongitudinalStress(self.pipe,
                                                      self.environment,
                                                      material,
                                                      self.internal_defect,
                                                      self.stress_intensity_method)

    def test_circumferential_longitudinal_stress_intensity_factor(self):
        """Unit test of check of axial longitudinal stress exceeding yield strength."""
        stress_example = InternalCircumferentialLongitudinalStress(self.pipe,
                                                                   self.environment,
                                                                   self.material,
                                                                   self.internal_defect,
                                                                   self.stress_intensity_method)
        stress_example.calc_stress_intensity_factor(crack_depth=0.04,
                                                    crack_length=0.05)
        
    def test_calc_combined_stress_intensity_factor(self):
        """Unit test that the combined K solution returns the correct
           value for spot-checked values."""
        k_prim = [40, 40, 40, -1, 25 ]
        k_res = [4, 8, 4, 10, -1]
        ref_stress = [250, 250, 1000, 250, 250]
        crack_depth = self.flaw_length * self.flaw_depth
        test_k_comb = [calc_combined_stress_intensity_factor(
            k_p, k_r, self.yield_strength, rs, crack_depth, self.flaw_length)
            for k_p, k_r, rs in zip(k_prim, k_res, ref_stress)]
        exp_k_comb = [44.1834, 48.4113, 41.3428, 10.0236, 25]

        self.assertTrue(np.allclose(test_k_comb, exp_k_comb, rtol=1e-4))

    def test_calc_r_ratio(self):
        """Unit test of r ratio calculation."""
        max_pressure = 100
        min_pressure = 10
        resid_stress = 5
        test_r_ratio = calc_r_ratio(min_pressure, max_pressure, resid_stress)
        exp_r_ratio = 15 / 105

        self.assertEqual(test_r_ratio, exp_r_ratio)

    def test_open_nc_table(self):
        """Unit test to check that the NetCDF4 tables successfully
           generate a DataArray object."""
        nc_table = open_nc_table('Table_9B10.nc')

        self.assertTrue(isinstance(nc_table, xr.DataArray))


class InternalAxialHoopStressTestCase(StressStateTestCase):
    """
    Class for unit tests of internal axial hoop stress class.
    
    Attributes
    ----------
    stress_state_anderson : InternalAxialHoopStress
        Internal axial hoop stress state object using the Anderson method.
    stress_state_api_internal : InternalAxialHoopStress
        Internal axial hoop stress state object using the API method for internal defects.
    stress_state_api_external : InternalAxialHoopStress
        Internal axial hoop stress state object using the API method for external defects.
    """

    def setUp(self):
        """Sets up the test case by initializing the attributes."""
        super(InternalAxialHoopStressTestCase, self).setUp()
        self.stress_state_anderson = InternalAxialHoopStress(self.pipe,
                                                self.environment,
                                                self.material,
                                                self.internal_defect,
                                                'anderson')
        self.stress_state_api_internal = InternalAxialHoopStress(self.pipe,
                                                self.environment,
                                                self.material,
                                                self.internal_defect,
                                                'api')
        self.stress_state_api_external = InternalAxialHoopStress(self.pipe,
                                                self.environment,
                                                self.material,
                                                self.external_defect,
                                                'api')

    def test_axial_hoop_stress_state_specification(self):
        """Unit test of internal axial hoop stress state specification."""
        self.assertTrue(self.stress_state_anderson.initial_crack_depth > 0)
        self.assertTrue(self.stress_state_api_internal.initial_crack_depth > 0)
        self.assertTrue(self.stress_state_api_external.initial_crack_depth > 0)

    def test_check_api_solution_assumptions_a_over_t_violation(self):
        """
        Unit test for function checking for catching violations of
           a/t <= 0.8 assumption in API 579-1 method.
           
        Raises
        ------
        UserWarning
            If the a/t ratio exceeds 0.8.
        """
        bad_defect = DefectSpecification(flaw_depth=85.0,
                                         flaw_length=0.1,
                                         surface='inside')
        with self.assertWarns(UserWarning):
            _ = InternalAxialHoopStress(self.pipe,
                                        self.environment,
                                        self.material,
                                        bad_defect,
                                        'api')

    def test_check_anderson_solution_assumptions_a_over_t_violation(self):
        """
        Unit test for function checking for catching violations of
           a/t <= 0.8 assumption in Anderson method.
           
        Raises
        ------
        UserWarning
            If the a/t ratio exceeds 0.8.   
        """
        bad_defect = DefectSpecification(flaw_depth=85.0,
                                         flaw_length=0.1,
                                         surface='inside')
        with self.assertWarns(UserWarning):
            _ = InternalAxialHoopStress(self.pipe,
                                        self.environment,
                                        self.material,
                                        bad_defect,
                                        'anderson')

    def test_check_anderson_solution_assumptions_r_i_over_t_violation(self):
        """
        Unit test for function checking for catching violation of 
        5 <= R_i/t <= 20 assumption in Anderson method.

        Raises
        ------
        UserWarning
            If the R_i/t ratio is outside the range [5, 20].
        """
        too_large_ri_t = Pipe(outer_diameter=5,
                              wall_thickness=0.1)

        with self.assertWarns(UserWarning):
            _ = InternalAxialHoopStress(too_large_ri_t,
                                        self.environment,
                                        self.material,
                                        self.internal_defect,
                                        'anderson')

        too_small_ri_t = Pipe(outer_diameter=4,
                               wall_thickness=0.4)

        with self.assertWarns(UserWarning):
            _ = InternalAxialHoopStress(too_small_ri_t,
                                        self.environment,
                                        self.material,
                                        self.internal_defect,
                                        'anderson')

    def test_axial_hoop_stress_check(self):
        """
        Unit test of check of axial hoop stress exceeding yield strength.
        
        Raises
        ------
        Warning
            If the axial hoop stress exceeds the yield strength.
        """
        material = MaterialSpecification(yield_strength=2.03E1,
                                         fracture_resistance=self.fracture_resistance)
        with self.assertWarns(Warning):
            InternalAxialHoopStress(self.pipe,
                                    self.environment,
                                    material,
                                    self.internal_defect,
                                    self.stress_intensity_method)

    def test_ref_stress_api(self):
        """Unit test to check default behavior of API reference stress
           solution method for typical inputs."""
        test_ref_stress = self.stress_state_api_internal.calc_ref_stress_api(
            crack_depth=0.04)
        exp_ref_stress = 184.84676
        self.assertAlmostEqual(test_ref_stress, exp_ref_stress, places=4)

    def test_interp_table_parameters_Table_9B10_single_inputs_internal(self):
        """Unit test to check that interpolation of Table 9B10 produces expected values
           (hand calc) for single internal crack."""
        tbl = open_nc_table('Table_9B10.nc').sel(surface='inside')
        toR = 0.1
        aot = 0.4
        test_Gs = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aot=aot).values
        exp_Gs = [1.957764, 1.002123, 0.702473, 0.556857, 0.467621]

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_interp_table_parameters_Table_9B10_single_inputs_external(self):
        """Unit test to check that interpolation of Table 9B10 produces expected G values
           (hand calc) for single external crack."""
        tbl = open_nc_table('Table_9B10.nc').sel(surface='outside')
        toR = 0.1
        aot = 0.4
        test_Gs = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aot=aot).values
        exp_Gs = [1.964321, 1.004607, 0.703748, 0.557628, 0.468296]

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_interp_table_parameters_Table_9B12_single_inputs(self):
        """Unit test to check that interpolation of Table 9B12 produces expected A values
           (hand calc) for single crack."""
        tbl = open_nc_table('Table_9B12.nc')
        toR = 0.1
        aoc = 0.25
        aot = 0.4
        test_As = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aoc=aoc,
            aot=aot)
        exp_As = np.array(
            [[0.726924, 0.03314, 4.054108, -7.67588, 5.625477, -1.15881, -0.31802],
             [0.114139, 0.228272, 1.90943, -2.05718, 0.7745, -0.34252, 0.12233]])

        self.assertTrue(np.allclose(test_As, exp_As, rtol=1e-4))

    def test_interp_table_parameters_Table_9B13_single_inputs(self):
        """Unit test to check that interpolation of Table 9B13 produces expected A values
           (hand calc) for single crack."""
        tbl = open_nc_table('Table_9B13.nc')
        toR = 0.1
        aoc = 0.25
        aot = 0.4
        test_As = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aoc=aoc,
            aot=aot)
        exp_As = np.array(
            [[0.747485, 0.042511, 4.371798, -8.19448, 6.253803, -1.68987, -0.14273],
             [0.118095, 0.248488, 1.906422, -1.90573, 0.552677, -0.24484, 0.11074]])

        self.assertTrue(np.allclose(test_As, exp_As, rtol=1e-4))

    def test_calc_G_parameters_finite_length_full_depth(self):
        """Unit test to check that interpolation of Table 9B12 produces expected G values
           (hand calc) for single of crack at full depth."""
        tbl = open_nc_table('Table_9B12.nc')
        toR = 0.1
        aoc = 0.25
        aot = 0.4
        As = self.stress_state_api_internal.interp_table_parameters(
                    table=tbl,
                    toR=toR,
                    aoc=aoc,
                    aot=aot)
        q = 1.
        phi = math.pi/2
        test_Gs = self.stress_state_api_internal.calc_G_parameters_finite_length(
            As, q, phi)
        exp_Gs = (1.28694, 0.74897, 0.56020, 0.46127, 0.39926)

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_calc_G_parameters_finite_length_surface(self):
        """Unit test to check that interpolation of Table 9B12 produces expected G values
           (hand calc) for single of crack at surface."""
        tbl = open_nc_table('Table_9B12.nc')
        toR = 0.1
        aoc = 0.25
        aot = 0.4
        As = self.stress_state_api_internal.interp_table_parameters(
                    table=tbl,
                    toR=toR,
                    aoc=aoc,
                    aot=aot)
        q = 1.
        phi = 0
        test_Gs = self.stress_state_api_internal.calc_G_parameters_finite_length(
            As, q, phi)
        exp_Gs = (0.72692, 0.11414, 0.04173, 0.020734, 0.012144)

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_calc_G_parameters_finite_length_other_point(self):
        """Unit test to check that interpolation of Table 9B12 produces expected G values
           (hand calc) for single of crack at specified point."""
        tbl = open_nc_table('Table_9B12.nc')
        toR = 0.1
        aoc = 0.25
        aot = 0.4
        As = self.stress_state_api_internal.interp_table_parameters(
                    table=tbl,
                    toR=toR,
                    aoc=aoc,
                    aot=aot)
        q = 1.
        phi = math.pi / 3
        test_Gs = self.stress_state_api_internal.calc_G_parameters_finite_length(
            As, q, phi)
        exp_Gs = (1.20719, 0.62404, 0.41802, 0.30771, 0.23752)

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_stress_intensity_factor_anderson_internal(self):
        """Unit test to check that axial hoop stress intensity factor calculated with Anderson's
           equation produces expected values (hand calc) for internal crack."""
        crack_depth = 0.04
        crack_length = 0.05
        test_k_max, test_k_min, test_f, test_q = \
            self.stress_state_anderson.calc_stress_intensity_factor(crack_depth,
                                                                    crack_length)
        exp_k = 38.23612
        exp_f = 1.16980
        exp_q = 4.17936
        self.assertAlmostEqual(test_k_max, exp_k, 4)
        self.assertAlmostEqual(test_f, exp_f, 4)
        self.assertAlmostEqual(test_q, exp_q, 4)

    def test_stress_intensity_factor_anderson_external(self):
        """
        Unit test to check that axial hoop stress intensity factor calculated with Anderson's
        equation produces error message for external crack.
           
        Raises
        ------
        ValueError
            If the Anderson stress intensity method is used for an external crack.   
        """
        crack_depth = 0.04
        crack_length = 0.05
        stress_state = deepcopy(self.stress_state_anderson)
        stress_state.defect_specification = self.external_defect
        with self.assertRaises(ValueError) as error_msg:
            _, _, _, _= (
                stress_state.calc_stress_intensity_factor(
                crack_depth, crack_length))
        exp_msg = ('Anderson stress intensity method is only valid for ' +
                   'interior cracks. Set ' +
                   "InternalAxialHoopStress.stress_intensity_method to 'api'")
        self.assertEqual(str(error_msg.exception), exp_msg)

    def test_stress_intensity_factor_api_internal(self):
        """Unit test to check that axial hoop stress intensity factor calculated with API
           method produces expected value (hand calc) for internal crack."""
        crack_depth = 0.04
        crack_length = 0.05
        test_k_max, test_k_min, test_f, test_q =  \
            self.stress_state_api_internal.calc_stress_intensity_factor(crack_depth,
                                                                        crack_length)
        exp_k = 39.61475
        exp_q = 1.67413
        self.assertTrue(math.isnan(test_f))
        self.assertAlmostEqual(test_k_max, exp_k, places=4)
        self.assertAlmostEqual(test_q, exp_q, places=4)

    def test_stress_intensity_factor_api_external(self):
        """Unit test to check that axial hoop stress intensity factor calculated with API
           method produces expected value (hand calc) for external crack."""
        crack_depth = 0.04
        crack_length = 0.05
        test_k_max, test_k_min, test_f, test_q = \
            self.stress_state_api_external.calc_stress_intensity_factor(crack_depth,
                                                                        crack_length)
        exp_k = 36.67007
        exp_q = 1.67413
        self.assertTrue(math.isnan(test_f))
        self.assertAlmostEqual(test_k_max, exp_k, places=4)
        self.assertAlmostEqual(test_q, exp_q, places=4)

if __name__ == '__main__':
    unittest.main()
