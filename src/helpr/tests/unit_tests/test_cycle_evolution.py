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
from helpr.physics.cycle_evolution import CycleEvolution, OptimizeACrit
from helpr.physics.crack_growth import CrackGrowth


class CycleEvolutionTestCase(unittest.TestCase):
    """ class for unit tests of cycle evolution module """
    def setUp(self):
        """ function to specify common cycle evolution inputs """
        max_pressure = 13
        min_pressure = 1
        temperature = 300
        flaw_depth = 5
        flaw_length = 0.001
        yield_strength = 670
        fracture_resistance = 40
        self.pipe = Pipe(outer_diameter=4,
                         wall_thickness=0.1)
        self.defect = DefectSpecification(flaw_depth=flaw_depth,
                                          flaw_length=flaw_length)
        self.material = MaterialSpecification(yield_strength=yield_strength,
                                              fracture_resistance=fracture_resistance)
        self.environment = EnvironmentSpecification(max_pressure=max_pressure,
                                                    min_pressure=min_pressure,
                                                    temperature=temperature)
        self.stress_state = InternalAxialHoopStress(pipe=self.pipe,
                                                    environment=self.environment,
                                                    material=self.material,
                                                    defect=self.defect)
        self.crack_growth = CrackGrowth(environment=self.environment,
                                        growth_model_specification={'model_name': 'code_case_2938'})

    def tearDown(self):
        """teardown function"""

    def test_default(self):
        """test default functionality of cycle evolution class"""
        test_crack = CycleEvolution(pipe=self.pipe,
                                    stress_state=self.stress_state,
                                    defect=self.defect,
                                    environment=self.environment,
                                    material=self.material,
                                    crack_growth_model=self.crack_growth)
        self.assertTrue(test_crack.stress_state.a_crit > 0)
        self.assertAlmostEqual(test_crack.material_specification.fracture_resistance[0], 40, 4)

        test_crack.calc_life_assessment()
        self.assertTrue(test_crack.cycle_dict['a/t'].values[-1] > 1)

    def test_array_input(self):
        """test array input for cycle evolution class"""
        pipes = Pipe(outer_diameter=[4, 6],
                     wall_thickness=[.1, .1],
                     sample_size=2)
        defects = DefectSpecification(flaw_depth=[5, 6],
                                      flaw_length=[0.001],
                                      sample_size=2)
        fracture_resistance = [40, 50]
        environments = EnvironmentSpecification(max_pressure=[13, 14],
                                                min_pressure=[1, 2],
                                                temperature=[300, 301],
                                                sample_size=2)
        stress_states = InternalAxialHoopStress(pipe=pipes,
                                                environment=environments,
                                                material=self.material,
                                                defect=defects,
                                                sample_size=2)
        self.material = MaterialSpecification(yield_strength=670,
                                              fracture_resistance=fracture_resistance,
                                              sample_size=2)
        crack_growth = CrackGrowth(environment=self.environment,
                                        growth_model_specification={'model_name': 'code_case_2938'},
                                        sample_size=2)
        test_crack = CycleEvolution(pipe=pipes,
                                    stress_state=stress_states,
                                    defect=defects,
                                    environment=environments,
                                    material=self.material,
                                    crack_growth_model=crack_growth)

        test_crack.calc_life_assessment()
        self.assertTrue((test_crack.cycle_dict['a/t'].values[-1] > 1).all())

    def test_a_crit_optimization(self):
        """test optimization of a critical for cycle evolution class"""
        test_optimize = OptimizeACrit(pipe=self.pipe,
                                      stress_state=self.stress_state,
                                      defect=self.defect,
                                      environment=self.environment,
                                      material=self.material,
                                      crack_growth_model=self.crack_growth)

        with self.assertRaises(ValueError):
            test_optimize.setup_a_crit_solve(parallel=True)


if __name__ == '__main__':
    unittest.main()
