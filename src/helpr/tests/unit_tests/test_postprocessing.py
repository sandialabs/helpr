# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.stress_state import InternalAxialHoopStress
from helpr.physics.cycle_evolution import CycleEvolution
from helpr.physics.crack_growth import CrackGrowth

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
        max_pressure = 13
        min_pressure = 1
        temperature = 300
        flaw_depth = 5
        flaw_length = 0.001
        fracture_resistance = 1
        yield_strength = 670
        pipe = Pipe(outer_diameter=4,
                    wall_thickness=0.1)
        defect = DefectSpecification(flaw_depth=flaw_depth,
                                     flaw_length=flaw_length)
        material = MaterialSpecification(yield_strength=yield_strength,
                                         fracture_resistance=fracture_resistance)
        environment = EnvironmentSpecification(max_pressure=max_pressure,
                                               min_pressure=min_pressure,
                                               temperature=temperature)
        stress_state = InternalAxialHoopStress(pipe=pipe,
                                               environment=environment,
                                               material=material,
                                               defect=defect)
        crack_growth = CrackGrowth(environment=environment,
                                   growth_model_specification={'model_name': 'code_case_2938'})
        test_crack = CycleEvolution(pipe=pipe,
                                    stress_state=stress_state,
                                    defect=defect,
                                    environment=environment,
                                    crack_growth_model=crack_growth,
                                    material=material)
        self.load_cycling = test_crack.calc_life_assessment()
        self.life_criteria = calc_pipe_life_criteria(cycle_results=self.load_cycling,
                                                     pipe=pipe,
                                                     stress_state=stress_state)

    def tearDown(self):
        """
        tear down function
        """

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
