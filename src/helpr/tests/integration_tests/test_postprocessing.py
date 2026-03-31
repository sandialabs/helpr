# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import pandas as pd
import numpy as np
import math
import warnings

from unittest.mock import patch

from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.stress_state import InternalAxialHoopStress
from helpr.physics.crack_growth import CrackGrowth
from helpr.physics.life_assessment import LifeAssessment
from helpr.physics.fracture import calculate_failure_assessment

from helpr.utilities.unit_conversion import convert_psi_to_mpa, convert_in_to_m
from helpr.utilities.postprocessing import (calc_pipe_life_criteria,
                                            report_single_pipe_life_criteria_results,
                                            report_single_cycle_evolution,
                                            find_intersection,
                                            failure_assessment_diagram_equation)
from helpr.utilities.plots import generate_pipe_life_assessment_plot


class PostProcessingTestCase(unittest.TestCase):
    """
    Unit test for postprocessing module.

    Attributes
    ----------
    yield_strength : float
        The yield strength of the material, in MPa.
    delta_c_rule : str
        The delta c rule used for crack growth.
    pipe : Pipe
        An instance of the Pipe class, representing the pipe being analyzed.
    load_cycling : dict
        The result of the calc_life_assessment method, representing the load cycling data for the pipe.
    life_criteria : dict
        The result of the calc_pipe_life_criteria method, representing the life criteria for the pipe.
    """

    def setUp(self):
        """Function to specify common postprocessing inputs."""
        max_pressure = convert_psi_to_mpa(840)
        min_pressure = convert_psi_to_mpa(638)
        temperature = 293
        flaw_depth = 25
        flaw_length = 0.04
        fracture_resistance = 55
        volume_fraction_h2 = 1.0
        self.yield_strength = convert_psi_to_mpa(52_000)
        crack_growth_model = {'model_name': 'code_case_2938'}
        stress_intensity_method = 'anderson'
        self.delta_c_rule = 'proportional'
        self.fad_type = 'simple'
        self.pipe = Pipe(outer_diameter=convert_in_to_m(36),
                    wall_thickness=convert_in_to_m(0.406))
        defect = DefectSpecification(flaw_depth=flaw_depth,
                                     flaw_length=flaw_length)
        material = MaterialSpecification(yield_strength=self.yield_strength,
                                         fracture_resistance=fracture_resistance)
        environment = EnvironmentSpecification(max_pressure=max_pressure,
                                               min_pressure=min_pressure,
                                               temperature=temperature,
                                               volume_fraction_h2=volume_fraction_h2)
        stress_state = InternalAxialHoopStress(pipe=self.pipe,
                                               environment=environment,
                                               material=material,
                                               defect=defect,
                                               stress_intensity_method=stress_intensity_method)
        crack_growth = CrackGrowth(environment=environment,
                                   growth_model_specification=crack_growth_model)
        test_crack = LifeAssessment(stress_state=stress_state,
                                    pipe_specification=self.pipe,
                                    crack_growth=crack_growth,
                                    delta_c_rule=self.delta_c_rule)
        self.load_cycling = test_crack.calc_life_assessment(max_cycles=math.inf,
                                                            cycle_step=None)
        input_parameters = {}
        input_parameters['fracture_resistance'] = [fracture_resistance]
        input_parameters['yield_strength'] = [self.yield_strength]
        calculate_failure_assessment(input_parameters,
                                     [self.load_cycling],
                                     [stress_state],
                                     self.fad_type)
        self.life_criteria = calc_pipe_life_criteria(cycle_results=self.load_cycling,
                                                     pipe=self.pipe,
                                                     material=material)

    def tearDown(self):
        """Tear down function."""

    def test_calc_pipe_life_criteria_hydrogen_impact(self):
        """Test that a(crit) and associated number of cycles match expected values from
           internal development notebook varying amount of hydrogen."""
        exp_a_crit_over_t = [0.53063173, 0.32865063, 0.32865063, 0.32865063]
        exp_cycles_to_a_crit = [247289.6438559, 121416.22306752, 41125.82605381, 13005.12809859]

        max_pressure = convert_psi_to_mpa(850)
        min_pressure = convert_psi_to_mpa(850*.8)
        temperature = 293
        flaw_depth = 25
        flaw_length = 0.04
        fracture_resistance = 55
        yield_strength = convert_psi_to_mpa(52_000)
        crack_growth_model = {'model_name': 'code_case_2938'}
        stress_intensity_method = 'anderson'
        fad_type = 'simple'
        pipe = Pipe(outer_diameter=convert_in_to_m(36),
                    wall_thickness=convert_in_to_m(0.4))
        defect = DefectSpecification(flaw_depth=flaw_depth,
                                     flaw_length=flaw_length)

        calc_a_crit_over_t = []
        calc_cycles_to_a_crit = []

        for vf, fr in zip([0, 0.01, 0.1, 1.0], [100, 55, 55, 55]):
            environment = EnvironmentSpecification(max_pressure=max_pressure,
                                        min_pressure=min_pressure,
                                        temperature=temperature,
                                        volume_fraction_h2=vf)
            material = MaterialSpecification(yield_strength=yield_strength,
                                            fracture_resistance=fr)
            stress_state = InternalAxialHoopStress(pipe=pipe,
                                                environment=environment,
                                                material=material,
                                                defect=defect,
                                                stress_intensity_method=stress_intensity_method)
            crack_growth = CrackGrowth(environment=environment,
                                    growth_model_specification=crack_growth_model)            
            analysis = LifeAssessment(stress_state=stress_state,
                                    pipe_specification=pipe,
                                    crack_growth=crack_growth,
                                    delta_c_rule=self.delta_c_rule)
            load_cycling = analysis.calc_life_assessment(max_cycles=math.inf,
                                                         cycle_step=None)
            input_parameters = {}
            input_parameters['fracture_resistance'] = [fracture_resistance]
            input_parameters['yield_strength'] = [self.yield_strength]
            calculate_failure_assessment(input_parameters,
                                        [load_cycling],
                                        [stress_state],
                                        fad_type)
            life_criteria = calc_pipe_life_criteria(cycle_results=load_cycling,
                                                    pipe=pipe,
                                                    material=material)
            calc_a_crit_over_t.append(life_criteria['Cycles to a(crit)'][1][0])
            calc_cycles_to_a_crit.append(life_criteria['Cycles to a(crit)'][0][0])

        for a, b in zip(calc_a_crit_over_t, exp_a_crit_over_t):
            self.assertTrue(np.allclose(a, b, rtol=1E-3))

        for a, b in zip(calc_cycles_to_a_crit, exp_cycles_to_a_crit):
            self.assertTrue(np.allclose(a, b, rtol=1E-3))

    def test_calc_pipe_life_criteria_typical(self):
        """Test that a(crit) and associated number of cycles match expected values
        from the `examples/demo_deterministic.ipynb` notebook."""
        exp_a_crit = np.array([3.43928e-3])
        exp_cycles_to_a_crit = [np.array([5669.414]), np.array([0.3335])]
        exp_cycles_to_25pct_a_crit = [np.array([1.0]), np.array([8.3377e-2])]
        exp_cycles_to_half_nc = [np.array([2834.707]), np.array([2.708e-1])]

        self.assertTrue(np.allclose(self.life_criteria['a(crit)'],
                                    exp_a_crit,
                                    rtol=1e-3))
        self.assertTrue(np.allclose(self.life_criteria['Cycles to a(crit)'],
                                    exp_cycles_to_a_crit,
                                    rtol=1e-3))
        self.assertTrue(np.allclose(self.life_criteria['Cycles to 25% a(crit)'],
                                    exp_cycles_to_25pct_a_crit,
                                    rtol=1e-3))
        self.assertTrue(np.allclose(self.life_criteria['Cycles to 1/2 Nc'],
                                    exp_cycles_to_half_nc,
                                    rtol=1e-3))

    def test_calc_pipe_life_criteria_default_a_crit(self):
        """Test that a(crit)/t defaults to 0.8 if the pipe fracture resistance
        is never met."""
        # set unrealistically high so will be higher than Kmax
        material = MaterialSpecification(yield_strength=self.yield_strength,
                                         fracture_resistance=9999)
        test_life_criteria = calc_pipe_life_criteria(cycle_results=self.load_cycling,
                                                     pipe=self.pipe,
                                                     material=material)
        exp_a_crit = np.array(0.8*self.pipe.wall_thickness)
        self.assertEqual(test_life_criteria['a(crit)'], exp_a_crit)

    def test_crack_evolution_plotting(self):
        """Test for generating crack evolution plot."""
        single_pipe_index = 0
        specific_life_criteria_result = report_single_pipe_life_criteria_results(self.life_criteria,
                                                                                 single_pipe_index)
        specific_load_cycling = report_single_cycle_evolution(self.load_cycling,
                                                             single_pipe_index)
        generate_pipe_life_assessment_plot(life_assessment=specific_load_cycling,
                                           postprocessed_criteria=specific_life_criteria_result,
                                           criteria=['Cycles to a(crit)'],
                                           pipe_name='test pipe')
        assert True

    def test_warn_cycles_to_a_crit_not_reached(self):
        """Test that a warning is raised when a_crit is not reached and a/t is small."""
        material = MaterialSpecification(yield_strength=self.yield_strength,
                                        fracture_resistance=1e5)  # Unreachably high

        cycle_results = [{
            'Kmax (MPa m^1/2)': pd.Series([1, 2, 3]),  # Always low
            'Kres (MPa m^1/2)': pd.Series([0.5, 0.5, 0.5]),  # Also low
            'a (m)': pd.Series([0.001, 0.0012, 0.0014]),  # Always below 0.8*t
            'Total cycles': pd.Series([1, 2, 3]),
            'a/t': pd.Series([0.01, 0.02, 0.03]),
            'Load ratio': pd.Series([0.1, 0.3, 0.6]),
            'Toughness ratio': pd.Series([0.1, 0.3, 0.6])
        }]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = calc_pipe_life_criteria(cycle_results=cycle_results,
                                        pipe=self.pipe,
                                        material=material)

            # Check that correct warning is triggered 
            self.assertTrue(any("Cycles to a_crit not reached" in str(warn.message) for warn in w))

    def test_fad_exceedence(self):
        # Create test data where all toughness ratio values exceed the FAD values
        load_ratio_data = np.array([0.5, 0.6, 0.7])
        toughness_ratio_data = np.array([0.8, 0.9, 1.0])
        cycles = np.array([1, 2, 3])
        a_over_t = np.array([0.1, 0.2, 0.3])

        # Mock the failure_assessment_diagram_equation function to return FAD values
        def mock_failure_assessment_diagram_equation(load_ratio_data):
            return np.array([0.4, 0.5, 0.6])

        # Call the find_intersection function with the mock function
        with patch('helpr.utilities.postprocessing.failure_assessment_diagram_equation',
                   mock_failure_assessment_diagram_equation):
            result = find_intersection(load_ratio_data,
                                       toughness_ratio_data,
                                       cycles,
                                       a_over_t)

        # Assert that the result indicates FAD exceedence
        self.assertEqual(result, {
            'load_intersection': np.nan,
            'toughness_intersection': np.nan,
            'cycles_fad_criteria': 1,
            'a_over_t_fad_criteria': a_over_t[0]
        })


if __name__ == '__main__':
    unittest.main()
