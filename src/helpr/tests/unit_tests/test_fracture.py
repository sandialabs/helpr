# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
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
        self.stress_intensity_factor = np.array([0.5])
        self.reference_stress_solution = np.array([0.5])

    def tearDown(self):
        """teardown function"""

    def test_default(self):
        """unit test of default behavior of fracture module"""
        failure_assessment = FailureAssessment(self.fracture_resistance ,
                                               self.yield_stress)
        toughness_ratio, load_ratio = \
            failure_assessment.assess_failure_state(self.stress_intensity_factor,
                                                    self.reference_stress_solution)

        self.assertEqual(toughness_ratio, 0.5)
        self.assertEqual(load_ratio, 0.5)

if __name__ == '__main__':
    unittest.main()
