# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import math

from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.stress_state import InternalAxialHoopStress
from helpr.physics.residual_stress import CircumferentialWeld
from helpr.physics.life_assessment import LifeAssessment
from helpr.physics.crack_growth import CrackGrowth

class LifeAssessmentTestCase(unittest.TestCase):
    """
    Class for unit tests of cycle evolution module.
    
    Attributes
    ----------
    initial_flaw_length : float
        Initial flaw length.
    pipe_det : Pipe
        Pipe object.
    defect_det : DefectSpecification
        Defect specification object.
    material_det : MaterialSpecification
        Material specification object.
    environment_det : EnvironmentSpecification
        Environment specification object.
    stress_state_anderson_det : InternalAxialHoopStress
        Stress state object using Anderson method.
    stress_state_api_det : InternalAxialHoopStress
        Stress state object using API method.
    crack_growth_det : CrackGrowth
        Crack growth object.
    delta_c_rule : str
        Delta c rule.
    max_cycles : float
        Maximum number of cycles.
    cycle_step : float
        Cycle step.
    """

    def setUp(self):
        """Function to specify common cycle evolution inputs."""
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
                                                        temperature=300,
                                                        volume_fraction_h2=1.0)

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
        self.delta_c_rule = 'proportional'
        self.max_cycles = math.inf
        self.cycle_step = None


    def tearDown(self):
        """Teardown function."""

    def test_default(self):
        """Test default functionality of cycle evolution class."""
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule=self.delta_c_rule)

        load_cycling = test_crack.calc_life_assessment(max_cycles=self.max_cycles,
                                                       cycle_step=self.cycle_step)
        self.assertTrue(load_cycling['a/t'][-1] > 0.8)

    def test_calc_life_assessment_w_cycle_step(self):
        """Test to confirm the life assessment behaves properly when a cycle step is provided."""
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule=self.delta_c_rule)
        load_cycling = test_crack.calc_life_assessment(max_cycles=self.max_cycles,
                                                       cycle_step=2.3)

        self.assertTrue(load_cycling['a/t'][-1] > 0.8)
        # Calculate the differences between consecutive elements
        differences = [load_cycling['Total cycles'][i] - load_cycling['Total cycles'][i - 1] 
                       for i in range(1, len(load_cycling['Total cycles']))]
        # Check if all differences are close to 2.3
        self.assertTrue(all(abs(diff - 2.3) < 1e-9 for diff in differences))

    def test_calc_life_assessment_w_max(self):
        """Test to confirm the life assessment behaves properly when a 
           max number of cycles is provided."""
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule=self.delta_c_rule)
        load_cycling = test_crack.calc_life_assessment(max_cycles=2000,
                                                       cycle_step=self.cycle_step)

        self.assertTrue(load_cycling['a/t'][-1] < 0.8)
        self.assertTrue(load_cycling['Total cycles'][-1] >= 2000)
        self.assertTrue(load_cycling['Total cycles'][-2] < 2000)

    def test_calc_life_assessment_w_max_overridden(self):
        """Test to confirm the life assessment behaves properly when a
           max number of cycles is provided but a/t > 0.8 is reached before
           that number of cycles."""
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule=self.delta_c_rule)
        load_cycling = test_crack.calc_life_assessment(max_cycles=5000,
                                                       cycle_step=self.cycle_step)

        # a/t = 0.8 around n=4000
        self.assertTrue(load_cycling['a/t'][-1] > 0.8)
        self.assertTrue(load_cycling['Total cycles'][-1] < 5000)

    def test_calc_life_assessment_w_other_stress_weld(self):
        """Test that the life assessment behaves properly when 
           a weld is specified as another stress state."""
        weld = CircumferentialWeld(pipe=self.pipe_det,
                                   environment=self.environment_det,
                                   material=self.material_det,
                                   defect=self.defect_det,
                                   weld_thickness=0.02,
                                   flaw_direction='perpendicular',
                                   heat_input=384)
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule=self.delta_c_rule,
                                    other_stress_state=weld)

        load_cycling = test_crack.calc_life_assessment(max_cycles=self.max_cycles,
                                                       cycle_step=self.cycle_step)
        self.assertTrue(load_cycling['a/t'][-1] > 0.8)

    def test_calc_life_assessment_w_other_stress_float(self):
        """Test that the life assessment behaves properly when 
           a float is specified as another stress state."""
        k_res = 12.
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule=self.delta_c_rule,
                                    other_stress_state=k_res)

        load_cycling = test_crack.calc_life_assessment(max_cycles=self.max_cycles,
                                                       cycle_step=self.cycle_step)
        self.assertTrue(load_cycling['a/t'][-1] > 0.8)

    def test_calc_life_assessment_w_other_stress_badtype(self):
        """
        Test that the life assessment returns an error when
        other_stress_state is an invalid type.

        Raises
        ------
        TypeError
            If other_stress_state is not of type float, Weld, or None.
        """
        other_stress_state = 'bad type'
        with self.assertRaises(TypeError) as error_msg:
            _ = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule=self.delta_c_rule,
                                    other_stress_state=other_stress_state)
            exp_msg = ('other_stress_state must be of type float, Weld, or None.')
            self.assertEqual(str(error_msg.exception), exp_msg)

    def test_fixed_c(self):
        """Test to check crack length remains unchanged when specified even if
           the cycling still works properly."""
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule='fixed')
        load_cycling = test_crack.calc_life_assessment(max_cycles=self.max_cycles,
                                                       cycle_step=self.cycle_step)
        self.assertTrue(load_cycling['a/t'][-1] > 0.8)
        self.assertTrue(load_cycling['c (m)'][-1] == self.initial_flaw_length/2)

    def test_proportional_c(self):
        """Test to check crack length ratio to a remains unchanged when specified even if
           the cycling still works properly."""
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule='proportional')
        load_cycling = test_crack.calc_life_assessment(max_cycles=self.max_cycles,
                                                       cycle_step=self.cycle_step)
        self.assertTrue(load_cycling['a/t'][-1] > 0.8)
        self.assertTrue(load_cycling['a (m)'][-1]/
                        load_cycling['c (m)'][-1] ==
                        self.stress_state_anderson_det.initial_a_over_c)

    def test_bad_delta_c_rule_specification(self):
        """
        Test to check that improper delta_c_rule specifications fail.
        
        Raises
        ------
        ValueError
            If delta_c_rule is not specified as 'proportional', 'fixed', or 'independent'.
        """
        with self.assertRaises(ValueError) as error_msg:
            _ = LifeAssessment(pipe_specification=self.pipe_det,
                               stress_state=self.stress_state_anderson_det,
                               crack_growth=self.crack_growth_det,
                               delta_c_rule='bad specification')
            exp_msg = ('delta_c_rule must be specified as proportional, fixed,' +
                        'or independent')
            self.assertEqual(str(error_msg.exception), exp_msg)

    def test_independent_c(self):
        """Test to check crack length independently propagates when specified."""
        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule='independent')
        load_cycling = test_crack.calc_life_assessment(max_cycles=self.max_cycles,
                                                       cycle_step=self.cycle_step)
        self.assertTrue(load_cycling['a/t'][-1] > 0.8)
        self.assertTrue(load_cycling['c (m)'][-1] > self.initial_flaw_length/2)
        self.assertTrue(load_cycling['c (m)'][-1] !=
                        (load_cycling['a (m)'][-1]
                         / test_crack.stress_state.initial_a_over_c))

    def test_life_assessment_early_exit_due_to_stopping(self):
        """Test that life assessment exits early if settings.is_stopping() is True."""
        import types
        from helpr import settings

        test_crack = LifeAssessment(pipe_specification=self.pipe_det,
                                    stress_state=self.stress_state_anderson_det,
                                    crack_growth=self.crack_growth_det,
                                    delta_c_rule=self.delta_c_rule)

        # Temporarily patch is_stopping to force early exit
        original_is_stopping = settings.is_stopping
        settings.is_stopping = types.MethodType(lambda *args, **kwargs: True, settings)

        result = test_crack.calc_life_assessment(max_cycles=1, cycle_step=1.0)

        # Restore the original method
        settings.is_stopping = original_is_stopping

        # If it exited early, there should only be one data point in the result
        self.assertEqual(len(result['a/t']), 1)

    def test_change_a_over_t_step_size_logic(self):
        """Test change_a_over_t_step_size returns correct adjusted step sizes."""
        from helpr.physics.life_assessment import LifeAssessment

        # Increase
        smaller_change = 0.05  # < 0.1 → increase
        self.assertAlmostEqual(
            LifeAssessment.change_a_over_t_step_size(1.0, smaller_change), 1.005)

        # Decrease
        larger_change = 0.6  # > 0.5 → decrease
        self.assertAlmostEqual(
            LifeAssessment.change_a_over_t_step_size(1.0, larger_change), 0.995)

        # No change
        mid_change = 0.2  # between 0.1 and 0.5 → same
        self.assertAlmostEqual(
            LifeAssessment.change_a_over_t_step_size(1.0, mid_change), 1.0)


if __name__ == '__main__':
    unittest.main()
