# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

import numpy as np

from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.stress_state import InternalAxialHoopStress
from helpr.physics.cycle_evolution import CycleEvolution
from helpr.physics.crack_growth import CrackGrowth


class CycleEvolutionTestCase(unittest.TestCase):
    """ class for unit tests of cycle evolution module """
    def setUp(self):
        """ function to specify common cycle evolution inputs """
        crack_growth_model = {'model_name': 'code_case_2938'}
        self.initial_flaw_length = 0.01

        self.pipe_det = Pipe(outer_diameter=4,
                         wall_thickness=0.1)
        self.defect_det = DefectSpecification(flaw_depth=5,
                                          flaw_length=self.initial_flaw_length)
        self.material_det = MaterialSpecification(yield_strength=670,
                                              fracture_resistance=40)
        self.environment_det = EnvironmentSpecification(max_pressure=13,
                                                    min_pressure=1,
                                                    temperature=300)
        self.pipe_prob = Pipe(outer_diameter=[4, 6],
                         wall_thickness=[0.1, 0.1],
                         sample_size=2)
        self.defect_prob = DefectSpecification(flaw_depth=[5, 6],
                                               flaw_length=self.initial_flaw_length,
                                               sample_size=2)
        self.material_prob = MaterialSpecification(yield_strength=670,
                                                   fracture_resistance=[40, 50],
                                                   sample_size=2)
        self.environment_prob = EnvironmentSpecification(max_pressure=[13, 14],
                                                    min_pressure=[1, 2],
                                                    temperature=[300, 301],
                                                    sample_size=2)

        self.stress_state_anderson_det = InternalAxialHoopStress(pipe=self.pipe_det,
                                                                 environment=self.environment_det,
                                                                 material=self.material_det,
                                                                 defect=self.defect_det,
                                                                 stress_intensity_method='anderson')
        self.stress_state_api_det = InternalAxialHoopStress(pipe=self.pipe_det,
                                                            environment=self.environment_det,
                                                            material=self.material_det,
                                                            defect=self.defect_det,
                                                            stress_intensity_method='api')
        self.crack_growth_det = CrackGrowth(environment=self.environment_det,
                                            growth_model_specification=crack_growth_model)

        self.stress_state_anderson_prob = \
            InternalAxialHoopStress(pipe=self.pipe_prob,
                                    environment=self.environment_prob,
                                    material=self.material_prob,
                                    defect=self.defect_prob,
                                    stress_intensity_method='anderson')
        self.stress_state_api_prob = InternalAxialHoopStress(pipe=self.pipe_prob,
                                                             environment=self.environment_prob,
                                                             material=self.material_prob,
                                                             defect=self.defect_prob,
                                                             stress_intensity_method='api')
        self.crack_growth_prob = CrackGrowth(environment=self.environment_prob,
                                             growth_model_specification=crack_growth_model,
                                             sample_size=2)

    def tearDown(self):
        """teardown function"""

    def test_default(self):
        """test default functionality of cycle evolution class"""
        test_crack = CycleEvolution(pipe=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    defect=self.defect_det,
                                    environment=self.environment_det,
                                    material=self.material_det,
                                    crack_growth_model=self.crack_growth_det)
        self.assertAlmostEqual(test_crack.material_specification.fracture_resistance[0], 40, 4)

        test_crack.calc_life_assessment()
        self.assertTrue(test_crack.cycle_dict['a/t'].values[-1] > 0.8)

    def test_array_input(self):
        """test array input for cycle evolution class"""
        test_crack = CycleEvolution(pipe=self.pipe_prob,
                                    stress_state=self.stress_state_anderson_prob,
                                    defect=self.defect_prob,
                                    environment=self.environment_prob,
                                    material=self.material_prob,
                                    crack_growth_model=self.crack_growth_prob)

        test_crack.calc_life_assessment()
        self.assertTrue((test_crack.cycle_dict['a/t'].values[-1] > 0.8).all())

    def test_calc_life_assessment_w_cycle_step(self):
        """test to confirm the life assessment behaves properly when a
        cycle step is provided
        """
        test_crack = CycleEvolution(pipe=self.pipe_det,
                            stress_state=self.stress_state_anderson_det,
                            defect=self.defect_det,
                            environment=self.environment_det,
                            material=self.material_det,
                            crack_growth_model=self.crack_growth_det)
        test_results = test_crack.calc_life_assessment(cycle_step=2.3)

        self.assertTrue(test_results['a/t'].values[-1] > 0.8)
        self.assertTrue(np.allclose(
            np.diff(test_crack.cycle_dict['Total cycles'].values.flatten()),
            [2.3]))

    def test_calc_life_assessment_w_max(self):
        """test to confirm the life assessment behaves properly when a
        max number of cycles is provided
        """
        test_crack = CycleEvolution(pipe=self.pipe_det,
                            stress_state=self.stress_state_anderson_det,
                            defect=self.defect_det,
                            environment=self.environment_det,
                            material=self.material_det,
                            crack_growth_model=self.crack_growth_det)
        test_results = test_crack.calc_life_assessment(max_cycles=2000)

        self.assertTrue(test_results['a/t'].values[-1] < 0.8)
        self.assertTrue(test_results['Total cycles'].values[-1] >= 2000)
        self.assertTrue(test_results['Total cycles'].values[-2] < 2000)

    def test_calc_life_assessment_w_max_overridden(self):
        """test to confirm the life assessment behaves properly when a
        max number of cycles is provided but a/t > 0.8 is reached before
        that number of cycles
        """
        test_crack = CycleEvolution(pipe=self.pipe_det,
                            stress_state=self.stress_state_anderson_det,
                            defect=self.defect_det,
                            environment=self.environment_det,
                            material=self.material_det,
                            crack_growth_model=self.crack_growth_det)
        test_results = test_crack.calc_life_assessment(max_cycles=5000)

        # a/t = 0.8 around n=4000
        self.assertTrue(test_results['a/t'].values[-1] > 0.8)
        self.assertTrue(test_results['Total cycles'].values[-1] < 5000)

    def test_fixed_c(self):
        """test to check crack length remains unchanged when specified even if
        the cycling still works properly
        """
        test_crack = CycleEvolution(pipe=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    defect=self.defect_det,
                                    environment=self.environment_det,
                                    material=self.material_det,
                                    crack_growth_model=self.crack_growth_det,
                                    delta_c_rule='fixed')
        test_crack.calc_life_assessment()
        self.assertTrue(test_crack.cycle_dict['a/t'].values[-1] > 0.8)
        self.assertTrue(test_crack.cycle_dict['c (m)'].values[-1] == self.initial_flaw_length/2)

    def test_proportional_c(self):
        """test to check crack length ratio to a remains unchanged when specified even if
        the cycling still works properly
        """
        test_crack = CycleEvolution(pipe=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    defect=self.defect_det,
                                    environment=self.environment_det,
                                    material=self.material_det,
                                    crack_growth_model=self.crack_growth_det,
                                    delta_c_rule='proportional')
        test_crack.calc_life_assessment()
        self.assertTrue(test_crack.cycle_dict['a/t'].values[-1] > 0.8)
        self.assertTrue(test_crack.cycle_dict['a (m)'].values[-1]/
                        test_crack.cycle_dict['c (m)'].values[-1] == self.stress_state_anderson_det.initial_a_over_c)

    def test_proportional_c_list(self):
        """test to check crack length ratio to a remains unchanged when specified even if
        the cycling still works properly with list inputs
        """
        test_crack = CycleEvolution(pipe=self.pipe_prob,
                                    stress_state=self.stress_state_anderson_prob,
                                    defect=self.defect_prob,
                                    environment=self.environment_prob,
                                    material=self.material_prob,
                                    crack_growth_model=self.crack_growth_prob,
                                    delta_c_rule='proportional')
        test_crack.calc_life_assessment()
        self.assertTrue((test_crack.cycle_dict['a/t'].values[-1] > 0.8).all())
        self.assertTrue((test_crack.cycle_dict['a (m)'].values[-1]/
                        test_crack.cycle_dict['c (m)'].values[-1]
                        == self.stress_state_anderson_prob.initial_a_over_c).all())

    def test_bad_delta_c_rule_specification(self):
        """test to check that improper delta_c_rule specifications fail"""
        with self.assertRaises(ValueError) as error_msg:
            _ = CycleEvolution(pipe=self.pipe_det,
                              stress_state=self.stress_state_anderson_det,
                               defect=self.defect_det,
                               environment=self.environment_det,
                               material=self.material_det,
                               crack_growth_model=self.crack_growth_det,
                               delta_c_rule='bad specification')
            exp_msg = ('delta_c_rule must be specified as proportional, fixed,' +
                        'or independent')
            self.assertEqual(str(error_msg.exception), exp_msg)

    def test_bad_delta_c_rule_specification_list(self):
        """test to check that improper delta_c_rule specifications fail with list inputs"""
        with self.assertRaises(ValueError) as error_msg:
            _ = CycleEvolution(pipe=self.pipe_prob,
                              stress_state=self.stress_state_anderson_prob,
                               defect=self.defect_prob,
                               environment=self.environment_prob,
                               material=self.material_prob,
                               crack_growth_model=self.crack_growth_prob,
                               delta_c_rule='bad specification')
            exp_msg = ('delta_c_rule must be specified as proportional, fixed,' +
                        'or independent')
            self.assertEqual(str(error_msg.exception), exp_msg)

    def test_independent_c(self):
        """test to check crack length independently propagates when specified"""
        test_crack = CycleEvolution(pipe=self.pipe_det,
                                    stress_state=self.stress_state_api_det,
                                    defect=self.defect_det,
                                    environment=self.environment_det,
                                    material=self.material_det,
                                    crack_growth_model=self.crack_growth_det,
                                    delta_c_rule='independent')
        test_crack.calc_life_assessment()
        self.assertTrue(test_crack.cycle_dict['a/t'].values[-1] > 0.8)
        self.assertTrue(test_crack.cycle_dict['c (m)'].values[-1] > self.initial_flaw_length/2)
        self.assertTrue(test_crack.cycle_dict['c (m)'].values[-1] !=
                        (test_crack.cycle_dict['a (m)'].values[-1]
                         / test_crack.stress_state.initial_a_over_c))

    def test_independent_c_list(self):
        """test to check crack length independently propagates when specified with list inputs"""
        test_crack = CycleEvolution(pipe=self.pipe_prob,
                                    stress_state=self.stress_state_api_prob,
                                    defect=self.defect_prob,
                                    environment=self.environment_prob,
                                    material=self.material_prob,
                                    crack_growth_model=self.crack_growth_prob,
                                    delta_c_rule='independent')
        test_crack.calc_life_assessment()
        self.assertTrue((test_crack.cycle_dict['a/t'].values[-1] > 0.8).all())
        self.assertTrue((test_crack.cycle_dict['c (m)'].values[-1] > self.initial_flaw_length/2).all())
        self.assertTrue((test_crack.cycle_dict['c (m)'].values[-1] !=
                        (test_crack.cycle_dict['a (m)'].values[-1]
                         / test_crack.stress_state.initial_a_over_c)).all())

if __name__ == '__main__':
    unittest.main()
