# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import os
import pathlib
from copy import deepcopy

import numpy as np

from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.stress_state import (GenericStressState,
                                        InternalAxialHoopStress,
                                        InternalCircumferentialLongitudinalStress)


path = pathlib.Path(__file__).parent.resolve()
data_dir = os.path.join(path, '../../data')

class StressStateTestCase(unittest.TestCase):
    """class for unit tests of stress state module"""
    def setUp(self):
        max_pressure = [13, 12]
        min_pressure = [1, 2]
        temperature = [300, 311]
        flaw_depth = [5, 10]
        flaw_length = [0.01, 0.02]
        self.fracture_resistance = [44, 55]
        yield_strength = 670
        self.stress_intensity_method = 'anderson'
        self.pipe = Pipe(outer_diameter=[3, 4],
                         wall_thickness=[0.1, 0.11],
                         sample_size=2)
        self.internal_defect = DefectSpecification(flaw_depth=flaw_depth,
                                                   flaw_length=flaw_length,
                                                   surface='inside',
                                                   sample_size=2)
        self.external_defect = DefectSpecification(flaw_depth=flaw_depth,
                                                   flaw_length=flaw_length,
                                                   surface='outside',
                                                   sample_size=2)
        self.material = MaterialSpecification(yield_strength=yield_strength,
                                              fracture_resistance=self.fracture_resistance,
                                              sample_size=2)
        self.environment = EnvironmentSpecification(max_pressure=max_pressure,
                                                    min_pressure=min_pressure,
                                                    temperature=temperature,
                                                    sample_size=2)

    def test_generic_stress_state_specification(self):
        """unit test of generic stress state state specification"""
        with self.assertRaises(ValueError):
            GenericStressState(self.pipe,
                               self.environment,
                               self.material,
                               self.internal_defect,
                               self.stress_intensity_method)

    def test_circumferential_longitudinal_stress_state_specification(self):
        """unit test of longitudinal stress states specification"""
        stress_state = InternalCircumferentialLongitudinalStress(self.pipe,
                                                                 self.environment,
                                                                 self.material,
                                                                 self.internal_defect,
                                                                 self.stress_intensity_method)
        self.assertTrue((stress_state.initial_crack_depth > 0).all())

    def test_circumferential_longitudinal_stress_check(self):
        """unit test of check of axial longitudinal stress exceeding yield strength"""
        material = MaterialSpecification(yield_strength=[1.02E1, 1.03E1],
                                            fracture_resistance=self.fracture_resistance,
                                            sample_size=2)
        with self.assertWarns(Warning):
            InternalCircumferentialLongitudinalStress(self.pipe,
                                                        self.environment,
                                                        material,
                                                        self.internal_defect,
                                                        self.stress_intensity_method)

    def test_circumferential_longitudinal_stress_intensity_factor(self):
        """unit test of check of axial longitudinal stress exceeding yield strength"""
        stress_example = InternalCircumferentialLongitudinalStress(self.pipe,
                                                                   self.environment,
                                                                   self.material,
                                                                   self.internal_defect,
                                                                   self.stress_intensity_method)
        stress_example.calc_stress_intensity_factor(crack_depth=0.04,
                                                    crack_length=0.05)

class InternalAxialHoopStressTestCase(StressStateTestCase):
    """class for unit tests of internal axial hoop stress class"""
    def setUp(self):
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

    def test_get_single_stress_state(self):
        """unit test of single stress state function"""
        idx = 1
        test_state = self.stress_state_anderson.get_single_stress_state(idx)
        exp_pipe_od = 4
        exp_flaw_depth = 10

        self.assertIsInstance(test_state, InternalAxialHoopStress)
        self.assertEqual(
            test_state.pipe_specification.outer_diameter, exp_pipe_od)
        self.assertEqual(
            test_state.defect_specification.flaw_depth, exp_flaw_depth)

    def test_axial_hoop_stress_state_specification(self):
        """unit test of internal axial hoop stress state specification"""
        self.assertTrue(
            (self.stress_state_anderson.initial_crack_depth > 0).all())
        self.assertTrue(
            (self.stress_state_api_internal.initial_crack_depth > 0).all())
        self.assertTrue(
            (self.stress_state_api_external.initial_crack_depth > 0).all())

    def test_check_api_solution_assumptions_a_over_t_violation(self):
        """unit test for function checking for catching violations of
          a/t <= 0.8 assumption in API 579-1 method"""
        bad_defect = DefectSpecification(flaw_depth=[85., 85.],
                                         flaw_length=[0.1, 0.1],
                                         surface='inside',
                                         sample_size=2)
        with self.assertWarns(UserWarning):
            _ = InternalAxialHoopStress(self.pipe,
                                        self.environment,
                                        self.material,
                                        bad_defect,
                                        'api')

    def test_check_anderson_solution_assumptions_a_over_t_violation(self):
        """unit test for function checking for catching violations of
          a/t <= 0.8 assumption in Anderson method"""
        bad_defect = DefectSpecification(flaw_depth=[85., 85.],
                                         flaw_length=[0.1, 0.1],
                                         surface='inside',
                                         sample_size=2)
        with self.assertWarns(UserWarning):
            _ = InternalAxialHoopStress(self.pipe,
                                        self.environment,
                                        self.material,
                                        bad_defect,
                                        'anderson')

    def test_check_anderson_solution_assumptions_r_i_over_t_violation(self):
        """unit test for function checking for catching violation of 
           5 <= R_i/t <= 20 assumption in Anderson method"""
        too_large_ri_t = Pipe(outer_diameter=[4, 5],
                              wall_thickness=[0.01, 0.1],
                              sample_size=2)

        with self.assertWarns(UserWarning):
            _ = InternalAxialHoopStress(too_large_ri_t,
                                        self.environment,
                                        self.material,
                                        self.internal_defect,
                                        'anderson')

        too_small_ri_t = Pipe(outer_diameter=[4, 5],
                               wall_thickness=[0.4, 0.2],
                               sample_size=2)

        with self.assertWarns(UserWarning):
            _ = InternalAxialHoopStress(too_small_ri_t,
                                        self.environment,
                                        self.material,
                                        self.internal_defect,
                                        'anderson')

    def test_axial_hoop_stress_check(self):
        """unit test of check of axial hoop stress exceeding yield strength"""
        material = MaterialSpecification(yield_strength=[2.02E1, 2.03E1],
                                         fracture_resistance=self.fracture_resistance,
                                         sample_size=2)
        with self.assertWarns(Warning):
            InternalAxialHoopStress(self.pipe,
                                    self.environment,
                                    material,
                                    self.internal_defect,
                                    self.stress_intensity_method)

    def test_ref_stress_api(self):
        """unit test to check default behavior of API reference stress
        solution method for typical inputs."""
        test_ref_stress = self.stress_state_api_internal.calc_ref_stress_api(
            crack_depth=0.04)
        exp_ref_stress = np.array([[27.34169, 47.37052]])

        self.assertTrue(np.allclose(
            test_ref_stress, exp_ref_stress, rtol=1e-4))

    def test_interp_table_parameters_Table_9B10_single_inputs_internal(self):
        """unit test to check that interpolation of Table 9B10 produces expected values
           (hand calc) for single internal crack"""
        tbl_file = os.path.join(data_dir, 'Table_9B10.nc')
        tbl = self.stress_state_api_internal.open_nc_table(
            tbl_file).sel(surface='inside')
        toR = np.array([0.1])
        aot = np.array([0.4])
        test_Gs = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aot=aot).values
        exp_Gs = np.array([1.957764, 1.002123, 0.702473, 0.556857, 0.467621])

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_interp_table_parameters_Table_9B10_single_inputs_external(self):
        """unit test to check that interpolation of Table 9B10 produces expected G values
           (hand calc) for single external crack"""
        tbl_file = os.path.join(data_dir, 'Table_9B10.nc')
        tbl = self.stress_state_api_internal.open_nc_table(
            tbl_file).sel(surface='outside')
        toR = np.array([0.1])
        aot = np.array([0.4])
        test_Gs = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aot=aot).values
        exp_Gs = np.array([1.964321, 1.004607, 0.703748, 0.557628, 0.468296])

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_interp_table_parameters_Table_9B10_matrix_inputs(self):
        """unit test to check that interpolation of Table 9B10 produces expected G values
           (hand calc) for vector of internal cracks"""
        tbl_file = os.path.join(data_dir, 'Table_9B10.nc')
        tbl = self.stress_state_api_internal.open_nc_table(
            tbl_file).sel(surface='inside')
        toR = np.array([0.1, 0.1, 0.15])
        aot = np.array([0.4, 0.7, 0.4])
        test_Gs = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aot=aot).values.squeeze()
        exp_Gs = np.array([[1.957764, 1.002123, 0.702473, 0.556857, 0.467621],
                           [4.383611, 1.883355, 1.1763065, 0.859365, 0.6874365],
                           [1.895482, 0.9785305, 0.6894405, 0.5483655, 0.46120]])

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_interp_table_parameters_Table_9B12_single_inputs(self):
        """unit test to check that interpolation of Table 9B12 produces expected A values
           (hand calc) for single crack"""
        tbl_file = os.path.join(data_dir, 'Table_9B12.nc')
        tbl = self.stress_state_api_internal.open_nc_table(tbl_file)
        toR = np.array([0.1])
        aoc = np.array([0.25])
        aot = np.array([0.4])
        test_As = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aoc=aoc,
            aot=aot).values.squeeze()
        exp_As = np.array(
            [[0.726924, 0.03314, 4.054108, -7.67588, 5.625477, -1.15881, -0.31802],
             [0.114139, 0.228272, 1.90943, -2.05718, 0.7745, -0.34252, 0.12233]])

        self.assertTrue(np.allclose(test_As, exp_As, rtol=1e-4))

    def test_interp_table_parameters_Table_9B12_matrix_inputs(self):
        """unit test to check that interpolation of Table 9B12 produces expected A values
           (hand calc) for vector of cracks"""
        tbl_file = os.path.join(data_dir, 'Table_9B12.nc')
        tbl = self.stress_state_api_internal.open_nc_table(tbl_file)
        toR = np.array([0.1, 0.1, 0.1, 0.15])
        aoc = np.array([0.25, 0.25, 0.375, 0.25])
        aot = np.array([0.4, 0.5, 0.4, 0.4])
        test_As = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aoc=aoc,
            aot=aot).values.squeeze()
        exp_As = np.array(
            [[[0.726924, 0.03314, 4.054108, -7.67588, 5.625477, -1.15881, -0.31802],
              [0.114139, 0.228272, 1.90943, -2.05718, 0.7745, -0.34252, 0.12233]],
             [[0.820309, -0.03984, 4.4155725, -7.72214, 4.4005455, 0.4868155, -0.963035],
              [0.14159, 0.232535, 1.843506, -1.48957, -0.533755, 0.9002245, -0.306275]],
             [[0.85334, -0.3126, 3.322352, -4.32829, 0.5615935, 2.404436, -1.28464],
              [0.1412335, 0.2653885, 1.557997, -1.38012, -0.109015, 0.3705795, -0.11187]],
             [[0.7242455, 0.035315, 3.9883995, -7.54906, 5.489814, -1.06871, -0.34455],
              [0.11720855, 0.1678761, 2.20324115, -2.8825652, 1.8979346, -1.07235145, 0.30769575]]])

        self.assertTrue(np.allclose(test_As, exp_As, rtol=1e-4))

    def test_interp_table_parameters_Table_9B13_single_inputs(self):
        """unit test to check that interpolation of Table 9B13 produces expected A values
           (hand calc) for single crack"""
        tbl_file = os.path.join(data_dir, 'Table_9B13.nc')
        tbl = self.stress_state_api_internal.open_nc_table(tbl_file)
        toR = np.array([0.1])
        aoc = np.array([0.25])
        aot = np.array([0.4])
        test_As = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aoc=aoc,
            aot=aot).values.squeeze()
        exp_As = np.array(
            [[0.747485, 0.042511, 4.371798, -8.19448, 6.253803, -1.68987, -0.14273],
             [0.118095, 0.248488, 1.906422, -1.90573, 0.552677, -0.24484, 0.11074]])

        self.assertTrue(np.allclose(test_As, exp_As, rtol=1e-4))

    def test_interp_table_parameters_Table_9B13_matrix_inputs(self):
        """unit test to check that interpolation of Table 9B13 produces expected A values
           (hand calc) for vector of cracks"""
        tbl_file = os.path.join(data_dir, 'Table_9B13.nc')
        tbl = self.stress_state_api_internal.open_nc_table(tbl_file)
        toR = np.array([0.1, 0.1, 0.1, 0.15])
        aoc = np.array([0.25, 0.25, 0.375, 0.25])
        aot = np.array([0.4, 0.5, 0.4, 0.4])
        test_As = self.stress_state_api_internal.interp_table_parameters(
            table=tbl,
            toR=toR,
            aoc=aoc,
            aot=aot).values.squeeze()
        exp_As = np.array(
            [[[0.747485, 0.042511, 4.371798, -8.19448, 6.253803, -1.68987, -0.14273],
              [0.118095, 0.248488, 1.906422, -1.90573, 0.552677, -0.24484, 0.11074]],
             [[0.8568195, -0.0464045, 5.0592235, -8.7785, 5.5808155, -0.4655105, -0.64091],
              [0.150561, 0.2446415, 1.9698945, -1.597035, -0.4093815, 0.7027585, -0.21447]],
             [[0.887768, -0.3605995, 3.7812385, -5.25651, 1.7002565, 1.6006605, -1.0551],
              [0.148889, 0.280632, 1.532635, -1.155975, -0.5286865, 0.695177, -0.209275]],
             [[0.7452245, 0.040171, 4.436625, -8.340735, 6.5403195, -1.97687, -0.042425],
              [0.1166365, 0.2570615, 1.8489835, -1.66638, 0.1482485, 0.0774415, 0.009075]]])

        self.assertTrue(np.allclose(test_As, exp_As, rtol=1e-4))

    def test_interp_table_parameters_vector_lengths_not_matching(self):
        """unit test to check that API table interpolation raises an error
        if input arguments are not 1 or all the same"""
        tbl_file = os.path.join(data_dir, 'Table_9B10.nc')
        tbl = self.stress_state_api_internal.open_nc_table(
            tbl_file).sel(surface='inside')
        toR = np.array([0.1, 0.1])
        aot = np.array([0.4, 0.7, 0.4])
        with self.assertRaises(ValueError):
            _ = self.stress_state_api_internal.interp_table_parameters(
                table=tbl,
                toR=toR,
                aot=aot).values.squeeze()

    def test_calc_G_parameters_finite_length_full_depth(self):
        """unit test to check that interpolation of Table 9B12 produces expected G values
           (hand calc) for single of crack at full depth"""
        tbl_file = os.path.join(data_dir, 'Table_9B12.nc')
        tbl = self.stress_state_api_internal.open_nc_table(tbl_file)
        toR = np.array([0.1])
        aoc = np.array([0.25])
        aot = np.array([0.4])
        As = self.stress_state_api_internal.interp_table_parameters(
                    table=tbl,
                    toR=toR,
                    aoc=aoc,
                    aot=aot)
        q = np.array([1.])
        phi = np.pi/2
        test_Gs = self.stress_state_api_internal.calc_G_parameters_finite_length(
            As, q, phi)
        exp_Gs = (np.array([1.28694]),
                  np.array([0.74897]),
                  np.array([0.56020]),
                  np.array([0.46127]),
                  np.array([0.39926]))

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_calc_G_parameters_finite_length_surface(self):
        """unit test to check that interpolation of Table 9B12 produces expected G values
           (hand calc) for single of crack at surface"""
        tbl_file = os.path.join(data_dir, 'Table_9B12.nc')
        tbl = self.stress_state_api_internal.open_nc_table(tbl_file)
        toR = np.array([0.1])
        aoc = np.array([0.25])
        aot = np.array([0.4])
        As = self.stress_state_api_internal.interp_table_parameters(
                    table=tbl,
                    toR=toR,
                    aoc=aoc,
                    aot=aot)
        q = np.array([1.])
        phi = 0
        test_Gs = self.stress_state_api_internal.calc_G_parameters_finite_length(
            As, q, phi)
        exp_Gs = (np.array([0.72692]),
                  np.array([0.11414]),
                  np.array([0.04173]),
                  np.array([0.020734]),
                  np.array([0.012144]))

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_calc_G_parameters_finite_length_other_point(self):
        """unit test to check that interpolation of Table 9B12 produces expected G values
           (hand calc) for single of crack at specified point"""
        tbl_file = os.path.join(data_dir, 'Table_9B12.nc')
        tbl = self.stress_state_api_internal.open_nc_table(tbl_file)
        toR = np.array([0.1])
        aoc = np.array([0.25])
        aot = np.array([0.4])
        As = self.stress_state_api_internal.interp_table_parameters(
                    table=tbl,
                    toR=toR,
                    aoc=aoc,
                    aot=aot)
        q = np.array([1.])
        phi = np.pi / 3
        test_Gs = self.stress_state_api_internal.calc_G_parameters_finite_length(
            As, q, phi)
        exp_Gs = (np.array([1.20719]),
                  np.array([0.62404]),
                  np.array([-10.19486]),
                  np.array([-1.01026]),
                  np.array([-0.96081]))

        self.assertTrue(np.allclose(test_Gs, exp_Gs, rtol=1e-4))

    def test_stress_intensity_factor_anderson_internal(self):
        """unit test to check that axial hoop stress intensity factor calculated with Anderson's
           equation produces expected values (hand calc) for internal crack"""
        crack_depth = 0.04
        crack_length = 0.05
        test_k, test_f, test_q = (
            self.stress_state_anderson.calc_stress_intensity_factor(
            crack_depth, crack_length))
        exp_k = np.array([38.23612, 42.27876])
        exp_f = np.array([1.16980, 1.14912])
        exp_q = np.array([4.17936])

        self.assertTrue(np.allclose(test_k, exp_k, rtol=1e-4))
        self.assertTrue(np.allclose(test_f, exp_f, rtol=1e-4))
        self.assertTrue(np.allclose(test_q, exp_q, rtol=1e-4))

    def test_stress_intensity_factor_anderson_external(self):
        """unit test to check that axial hoop stress intensity factor calculated with Anderson's
           equation produces error message for external crack"""
        crack_depth = 0.04
        crack_length = 0.05
        stress_state = deepcopy(self.stress_state_anderson)
        stress_state.defect_specification = self.external_defect
        with self.assertRaises(ValueError) as error_msg:
            _, _, _= (
                stress_state.calc_stress_intensity_factor(
                crack_depth, crack_length))
        exp_msg = ('Anderson stress intensity method is only valid for ' +
                   'interior cracks. Set ' +
                   "InternalAxialHoopStress.stress_intensity_method to 'api'")
        self.assertEqual(str(error_msg.exception), exp_msg)

    def test_stress_intensity_factor_api_internal(self):
        """unit test to check that axial hoop stress intensity factor calculated with API
           method produces expected value (hand calc) for internal crack"""
        crack_depth = 0.04
        crack_length = 0.05
        test_k, test_f, test_q = (
            self.stress_state_api_internal.calc_stress_intensity_factor(
            crack_depth, crack_length))
        exp_k = np.array([39.61475, 44.37855])
        exp_q = np.array([1.67413])

        self.assertTrue(np.allclose(test_k, exp_k, rtol=1e-4))
        self.assertTrue(np.isnan(test_f))
        self.assertTrue(np.allclose(test_q, exp_q, rtol=1e-4))

    def test_stress_intensity_factor_api_external(self):
        """unit test to check that axial hoop stress intensity factor calculated with API
           method produces expected value (hand calc) for external crack"""
        crack_depth = 0.04
        crack_length = 0.05
        test_k, test_f, test_q = (
            self.stress_state_api_external.calc_stress_intensity_factor(
            crack_depth, crack_length))
        exp_k = np.array([36.67007, 41.44689])
        exp_q = np.array([1.67413])

        self.assertTrue(np.allclose(test_k, exp_k, rtol=1e-4))
        self.assertTrue(np.isnan(test_f))
        self.assertTrue(np.allclose(test_q, exp_q, rtol=1e-4))

    def test_stress_intensity_factor_invalid_method(self):
        """unit test to check an exception is raised when a method
        other than Anderson or API is raised"""
        with self.assertRaises(ValueError) as error_msg:
            _ = InternalAxialHoopStress(self.pipe,
                                        self.environment,
                                        self.material,
                                        self.internal_defect,
                                        'bad_method')
        exp_msg = ("stress_intensity_method must be specified as 'anderson' " +
                   "or 'api', currently is bad_method")
        self.assertEqual(str(error_msg.exception), exp_msg)


if __name__ == '__main__':
    unittest.main()
