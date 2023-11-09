# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.stress_state import (GenericStressState,
                                        InternalAxialHoopStress,
                                        InternalCircumferentialLongitudinalStress)


class StressStateTestCase(unittest.TestCase):
    """class for unit tests of stress state module"""
    def setUp(self):
        max_pressure = [13, 12]
        min_pressure = [1, 2]
        temperature = [300, 311]
        flaw_depth = [5, 10]
        flaw_length = [0.001, 0.002]
        self.fracture_resistance = [44, 55]
        yield_strength = 670
        self.pipe = Pipe(outer_diameter=[4, 5],
                         wall_thickness=[0.1, 0.11],
                         sample_size=2)
        self.defect = DefectSpecification(flaw_depth=flaw_depth,
                                          flaw_length=flaw_length,
                                          sample_size=2)
        self.material = MaterialSpecification(yield_strength=yield_strength,
                                              fracture_resistance=self.fracture_resistance,
                                              sample_size=2)
        self.environment = EnvironmentSpecification(max_pressure=max_pressure,
                                                    min_pressure=min_pressure,
                                                    temperature=temperature,
                                                    sample_size=2)

    def tearDown(self):
        """tear down function"""

    def test_generic_stress_state_specification(self):
        """unit test of generic stress state state specification"""
        with self.assertRaises(ValueError):
            GenericStressState(self.pipe,
                               self.environment,
                               self.material,
                               self.defect,
                               sample_size=2)

    def test_axial_hoop_stress_state_specification(self):
        """unit test of internal axial hoop stress state specification"""
        stress_state = InternalAxialHoopStress(self.pipe,
                                               self.environment,
                                               self.material,
                                               self.defect,
                                               sample_size=2)
        self.assertTrue((stress_state.initial_crack_depth > 0).all())

    def test_circumferential_longitudinal_stress_state_specification(self):
        """unit test of longitudinal stress states specification"""
        stress_state = InternalCircumferentialLongitudinalStress(self.pipe,
                                                                 self.environment,
                                                                 self.material,
                                                                 self.defect,
                                                                 sample_size=2)
        self.assertTrue((stress_state.initial_crack_depth > 0).all())

    def test_axial_hoop_stress_check(self):
        """unit test of check of axial hoop stress exceeding yield strength"""
        material = MaterialSpecification(yield_strength=[2.02E1, 2.03E1],
                                         fracture_resistance=self.fracture_resistance,
                                         sample_size=2)
        with self.assertRaises(ValueError):
            InternalAxialHoopStress(self.pipe,
                                    self.environment,
                                    material,
                                    self.defect,
                                    sample_size=2)

    def test_circumferential_longitudinal_stress_check(self):
        """unit test of check of axial longitudinal stress exceeding yield strength"""
        material = MaterialSpecification(yield_strength=[1.02E1, 1.03E1],
                                         fracture_resistance=self.fracture_resistance,
                                         sample_size=2)
        with self.assertRaises(ValueError):
            InternalCircumferentialLongitudinalStress(self.pipe,
                                                      self.environment,
                                                      material,
                                                      self.defect,
                                                      sample_size=2)

    def test_axial_hoop_stress_intensity_factor(self):
        """unit test of check of axial longitudinal stress exceeding yield strength"""
        stress_example = InternalAxialHoopStress(self.pipe,
                                                 self.environment,
                                                 self.material,
                                                 self.defect,
                                                 sample_size=2)
        stress_example.calc_stress_intensity_factor(crack_depth=1, eta=0.5)

    def test_circumferential_longitudinal_stress_intensity_factor(self):
        """unit test of check of axial longitudinal stress exceeding yield strength"""
        stress_example = InternalCircumferentialLongitudinalStress(self.pipe,
                                                                   self.environment,
                                                                   self.material,
                                                                   self.defect,
                                                                   sample_size=2)
        stress_example.calc_stress_intensity_factor(crack_depth=1, eta=0.5)

if __name__ == '__main__':
    unittest.main()
