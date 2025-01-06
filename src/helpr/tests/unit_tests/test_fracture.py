# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np

from helpr.physics.fracture import FailureAssessment


class FractureTestCase(unittest.TestCase):
    """class for fracture module unit tests"""
    def setUp(self):
        """function for specifying common fracture module inputs"""
        self.fracture_resistance = np.array([1])
        self.yield_stress = np.array([1])
        self.prim_stress_intensity_factor = np.array([0.5])
        self.sec_stress_intensity_factor = np.array([0.45])
        self.reference_stress_solution = np.array([0.5])
        self.crack_depth = 1
        self.crack_length = 1

    def tearDown(self):
        """teardown function"""

    def test_assessment_primaryOnly(self):
        """unit test of failure assessment with only primary stress."""
        failure_assessment = FailureAssessment(self.fracture_resistance ,
                                               self.yield_stress)
        toughness_ratio, load_ratio = \
            failure_assessment.assess_failure_state(self.prim_stress_intensity_factor,
                                                    self.reference_stress_solution,
                                                    self.crack_depth,
                                                    self.crack_length)

        self.assertEqual(load_ratio, 0.5)
        self.assertEqual(toughness_ratio, 0.5)

    def test_assessment_withSecondary(self):
        """unit test of failure assessment with
        primary and secondary/residual stress."""
        # TODO: this is giving a numpy warning, "ndarray size changed"

        failure_assessment = FailureAssessment(self.fracture_resistance ,
                                               self.yield_stress)
        load_ratio, toughness_ratio = \
            failure_assessment.assess_failure_state(
                self.prim_stress_intensity_factor,
                self.reference_stress_solution,
                self.crack_depth,
                self.crack_length,
                secondary_stress_intensity_factor=self.sec_stress_intensity_factor)

        
        assert np.allclose(load_ratio, 1, atol=1e-2)
        self.assertEqual(toughness_ratio, 0.5)
        
if __name__ == '__main__':
    unittest.main()
