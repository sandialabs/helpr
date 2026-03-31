# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import numpy as np
import pandas as pd
import numpy.random as npr

from helpr.physics.inspection_mitigation import InspectionMitigation


class InspectionMitigationTestCase(unittest.TestCase):
    """
    Class for unit tests of Inspection Mitigation module.
    
    Attributes
    ----------
    probability_of_detection : float
        Probability of detection for the inspection.
    detection_resolution : float
        Detection resolution for the inspection.
    inspection_frequency : int
        Frequency of the inspection.
    inspection_mitigation : InspectionMitigation
        InspectionMitigation object.
    """
    
    def setUp(self):
        """Set up the test case with initial parameters."""
        self.probability_of_detection = 0.8
        self.detection_resolution = 0.1
        self.inspection_frequency = 50
        self.inspection_mitigation = InspectionMitigation(
            self.probability_of_detection,
            self.detection_resolution,
            self.inspection_frequency
        )

    def test_initialization(self):
        """Test the initialization of the InspectionMitigation class."""
        self.assertEqual(self.inspection_mitigation.probability_of_detection,
                         self.probability_of_detection)
        self.assertEqual(self.inspection_mitigation.detection_resolution,
                         self.detection_resolution)
        self.assertEqual(self.inspection_mitigation.inspection_frequency,
                         self.inspection_frequency)

    def test_determine_inspection_schedule(self):
        """Test the determine_inspection_schedule method."""
        cycle_count = [0, 100, 200, 300]
        expected_schedule = np.array([50, 100, 150, 200, 250, 300])
        result = self.inspection_mitigation.determine_inspection_schedule(cycle_count,
                                                                          self.inspection_frequency)
        np.testing.assert_array_equal(result, expected_schedule)

    def test_inspect_crack(self):
        """Test the inspect_crack method."""
        inspection_schedule = [5, 100, 200, 250]
        crack_sizes = [0.05, 0.15, 0.2, 0.25]
        failure_criteria = 0.2
        cycle_count = [0, 100, 200, 300]

        expected_state = np.array(['Not Detectable', 'Detectable', 'Failed', 'Failed'], dtype=object)
        result = self.inspection_mitigation.inspect_crack(inspection_schedule,
                                                          crack_sizes,
                                                          failure_criteria,
                                                          self.detection_resolution,
                                                          cycle_count)
        np.testing.assert_array_equal(result, expected_state)

    def test_mitigate_crack(self):
        """Test the mitigate_crack method."""
        state_array = np.array(['Not Detectable', 'Detectable', 'Detectable', 'Not Detectable'],
                               dtype=object)
        random_state = npr.default_rng(seed=42)  # Set seed for reproducibility
        result = self.inspection_mitigation.mitigate_crack(state_array,
                                                           random_state,
                                                           self.probability_of_detection)

        # Check that the result is modified correctly
        self.assertIn('Mitigated', result)

        # Use np.where to find indices of 'Detected'
        detected_indices = np.where(result == 'Detected')[0]
        if detected_indices.size > 0:
            self.assertTrue(np.all(result[detected_indices[0]:] == 'Mitigated'))
        else:
            self.assertTrue(True)  # If there are no 'Detected', we can assert True

    def test_count_inspections_until_mitigated(self):
        """Test the count_inspections_until_mitigated method."""
        mitigation_state = np.array(['Not Detectable', 'Detectable', 'Mitigated', 'Detectable'],
                                    dtype=object)
        inspection_schedule = [50, 100, 150, 200]

        result = self.inspection_mitigation.count_inspections_until_mitigated(mitigation_state,
                                                                              inspection_schedule)
        self.assertEqual(result, 150)  # The inspection cycle corresponding to 'Mitigated'

        # Test with no mitigated state
        mitigation_state_no_mitigation = np.array(['Not Detecteable', 'Detectable', 'Detectable'],
                                                  dtype=object)
        result_no_mitigation = \
            self.inspection_mitigation.count_inspections_until_mitigated(mitigation_state_no_mitigation,
                                                                         inspection_schedule)
        self.assertTrue(np.isnan(result_no_mitigation))  # Should return np.nan

    def test_inspect_then_mitigate(self):
        """Test the inspect_then_mitigate method."""
        load_cycling = [
            {'Total cycles': [0, 100, 200, 300], 'a/t': [0.05, 0.15, 0.25, 0.35]},
            {'Total cycles': [0, 150, 250, 350], 'a/t': [0.02, 0.12, 0.22, 0.32]}
        ]
        failure_criteria = np.array([0.2, 0.3])
        random_state = npr.default_rng(seed=42)  # Set seed for reproducibility

        result = self.inspection_mitigation.inspect_then_mitigate(load_cycling,
                                                                  failure_criteria,
                                                                  random_state)
        # Should return a list of the same length as load_cycling
        self.assertEqual(len(result), len(load_cycling))

if __name__ == '__main__':
    unittest.main()
