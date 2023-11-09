# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import pandas as pd
import numpy as np
import numpy.random as npr

from helpr.physics.inspection_mitigation import (InspectionMitigation,
                                                 inspect_crack,
                                                 mitigate_crack)


class InspectionMitigationTestCase(unittest.TestCase):
    """
    unit tests for inspection and mitigation module
    """
    def setUp(self):
        """
        function for specifying common inspection mitigation module inputs
        """
        self.probability_of_detection = 0.5
        self.detection_resolution = 0.1
        self.inspection_frequency = 2
        self.inspection_mitigation = InspectionMitigation(self.probability_of_detection,
                                                          self.detection_resolution,
                                                          self.inspection_frequency)
        self.random_state = npr.default_rng(123)

    def tearDown(self):
        """"
        teardown function
        """

    def test_determine_inspection_schedule(self):
        '''test of determining inspection schedule function'''
        cycle_1 = [1, 2, 3, 4, 5]
        cycle_2 = [2, 4, 6, 8, 10]
        cycle_3 = [0, 3, 6, 9, 12]
        cycle_count = pd.DataFrame({1: cycle_1, 2: cycle_2, 3: cycle_3})
        number_of_inspections, inspection_array = \
            self.inspection_mitigation.determine_inspection_schedule(cycle_count)
        self.assertEqual(number_of_inspections, 6)
        self.assertIsNone(np.testing.assert_array_equal(inspection_array,
                                                        np.array([2, 4, 6, 8, 10, 12])))

    def test_inspection_indices(self):
        '''test of inspection indices function'''
        cycle_1 = [1, 4, 7, 10, 13, 16, 19]
        cycle_2 = [0, 3, 6, 9, 12, 15, 18]
        cycle_count = pd.DataFrame({1: cycle_1, 2: cycle_2})
        number_of_inspections = 3
        inspection_array = np.array([5, 10, 19])
        inspection_indices = \
            self.inspection_mitigation.determine_inspection_indices(cycle_count,
                                                                    number_of_inspections,
                                                                    inspection_array)
        expected_response = pd.DataFrame({1: [2, 3, 6],
                                          2: [2, 4, np.nan]})
        self.assertIsNone(pd.testing.assert_frame_equal(inspection_indices,
                                                        expected_response))

    def test_crack_inspection(self):
        '''unit test for crack inspection function'''
        inspection_indices = pd.Series([1, 2, 5, 6, 7])
        crack_size = pd.Series([0.01, 0.05, 0.1, 0.15, 0.2, 0.22, 0.25])
        cycle_count = pd.Series([1, 2, 3, 4, 5, 6, 7])
        inspection_array = np.array([1, 2, 5, 6, 7])
        failure_criteria = 0.24
        detectable = inspect_crack(inspection_indices,
                                   crack_size,
                                   failure_criteria,
                                   self.detection_resolution,
                                   inspection_array,
                                   cycle_count)
        self.assertEqual(detectable.tolist(), [False, False, True, True, False])

    def test_crack_mitigation(self):
        '''unit test for crack mitigation function'''
        detectable = pd.Series([True, False, True, True])
        mitigation = mitigate_crack(detectable,
                                    self.random_state,
                                    self.probability_of_detection)
        self.assertEqual(mitigation.tolist(), [False, False, True, True])

if __name__ == '__main__':
    unittest.main()
