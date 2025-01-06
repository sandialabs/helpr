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

from helpr.utilities.unit_conversion import convert_psi_to_mpa, convert_in_to_m
from helpr.utilities.postprocessing import (calc_pipe_life_criteria,
                                            report_single_pipe_life_criteria_results,
                                            report_single_cycle_evolution)
from helpr.utilities.plots import generate_pipe_life_assessment_plot


class PostProcessingTestCase(unittest.TestCase):
    """
    unit test for postprocessing module
    """
    def setUp(self):
        """
        function to specify common postprocessing inputs
        """
        max_pressure = convert_psi_to_mpa(840)
        min_pressure = convert_psi_to_mpa(638)
        temperature = 293
        flaw_depth = 25
        flaw_length = 0.04
        fracture_resistance = 55
        self.yield_strength = convert_psi_to_mpa(52_000)
        crack_growth_model = {'model_name': 'code_case_2938'}
        stress_intensity_method = 'anderson'
        self.pipe = Pipe(outer_diameter=convert_in_to_m(36),
                    wall_thickness=convert_in_to_m(0.406))
        defect = DefectSpecification(flaw_depth=flaw_depth,
                                     flaw_length=flaw_length)
        material = MaterialSpecification(yield_strength=self.yield_strength,
                                         fracture_resistance=fracture_resistance)
        environment = EnvironmentSpecification(max_pressure=max_pressure,
                                               min_pressure=min_pressure,
                                               temperature=temperature)
        stress_state = InternalAxialHoopStress(pipe=self.pipe,
                                               environment=environment,
                                               material=material,
                                               defect=defect,
                                               stress_intensity_method=stress_intensity_method)
        crack_growth = CrackGrowth(environment=environment,
                                   growth_model_specification=crack_growth_model)
        test_crack = CycleEvolution(pipe=self.pipe,
                                    stress_state=stress_state,
                                    defect=defect,
                                    environment=environment,
                                    crack_growth_model=crack_growth,
                                    material=material)
        self.load_cycling = test_crack.calc_life_assessment()
        self.life_criteria = calc_pipe_life_criteria(cycle_results=self.load_cycling,
                                                     pipe=self.pipe,
                                                     material=material)

    def tearDown(self):
        """
        tear down function
        """

    def test_calc_pipe_life_criteria_hydrogen_impact(self):
        """
        test that a(crit) and associated number of cycles match expected values from
        internal development notebook varying amount of hydrogen
        """
        exp_a_crit_over_t = [0.53063173, 0.32865063, 0.32865063, 0.32865063]
        exp_cycles_to_a_crit = [247289.6438559, 121416.22306752, 41125.82605381, 13005.12809859]

        max_pressure = convert_psi_to_mpa(850)
        min_pressure = convert_psi_to_mpa(850*.8)
        temperature = 293
        flaw_depth = 25
        flaw_length = 0.04
        yield_strength = convert_psi_to_mpa(52_000)
        crack_growth_model = {'model_name': 'code_case_2938'}
        stress_intensity_method = 'anderson'
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
            analysis = CycleEvolution(pipe=pipe,
                                      stress_state=stress_state,
                                      defect=defect,
                                      environment=environment,
                                      crack_growth_model=crack_growth,
                                      material=material)
            load_cycling = analysis.calc_life_assessment()
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
        """
        test that a(crit) and associated number of cycles match expected values
        from the `examples/demo_deterministic.ipynb` notebook
        """
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
        """
        test that a(crit)/t defaults to 0.8 if the pipe fracture resistance
        is never met.
        """
        material = MaterialSpecification(yield_strength=self.yield_strength,
                                         fracture_resistance=9999) # set unrealistically high so will be higher than Kmax
        test_life_criteria = calc_pipe_life_criteria(cycle_results=self.load_cycling,
                                                     pipe=self.pipe,
                                                     material=material)
        exp_a_crit = np.array(0.8*self.pipe.wall_thickness)
        self.assertEqual(test_life_criteria['a(crit)'], exp_a_crit)
    
    def test_crack_evolution_plotting(self):
        """"
        test for generating crack evolution plot
        """
        single_pipe_index = 0
        specific_life_criteria_result = report_single_pipe_life_criteria_results(self.life_criteria,
                                                                                 single_pipe_index)
        specific_load_cycling = report_single_cycle_evolution(self.load_cycling,
                                                             single_pipe_index)
        generate_pipe_life_assessment_plot(specific_load_cycling,
                                           specific_life_criteria_result,
                                           'test pipe')
        assert True

if __name__ == '__main__':
    unittest.main()
