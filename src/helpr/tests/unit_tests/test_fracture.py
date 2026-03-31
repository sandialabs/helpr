# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

from helpr.physics.fracture import FailureAssessment, determine_fad_values, process_fatigue_instance


class MockStressState:
    """
    Mock class to simulate the stress state behavior.
    
    Attributes
    ----------
    stress_intensity_method : str
        Method used for calculating stress intensity.
    """

    def __init__(self, method='anderson'):
        """
        Initialize the MockStressState object.

        Parameters
        ----------
        method : str, optional
            Method used for calculating stress intensity (default is 'anderson').
        """
        self.stress_intensity_method = method

    def calc_stress_solution(self, crack_depth):
        """
        Calculate the reference stress for the API method.

        Parameters
        ----------
        crack_depth : float
            Depth of the crack.

        Returns
        -------
        float
            Reference stress for the API method.
        """
        return 50.0  # Mock return value for Anderson method

    def calc_ref_stress_api(self, crack_depth):
        """
        Calculate the reference stress for the API method.

        Parameters
        ----------
        crack_depth : float
            Depth of the crack.

        Returns
        -------
        float
            Reference stress for the API method.
        """
        return 60.0  # Mock return value for API method


class TestFailureAssessment(unittest.TestCase):
    """
    Class for unit tests of fracture module.
    
    Attributes
    ----------
    fracture_resistance : float
        Fracture resistance of the material.
    yield_stress : float
        Yield stress of the material.
    failure_assessment : FailureAssessment
        Failure assessment object.
    """

    def setUp(self):
        """Set up test cases."""
        self.fracture_resistance = 50.0
        self.yield_stress = 100.0
        self.fad_type = 'simple'
        self.failure_assessment = FailureAssessment(self.fracture_resistance,
                                                    self.yield_stress,
                                                    self.fad_type)
        self.api_failure_assessment = FailureAssessment(self.fracture_resistance,
                                                        self.yield_stress,
                                                        'API 579-1 Level 2')

    def test_assess_failure_state(self):
        """Test the assess_failure_state method."""
        stress_intensity_factor = 30.0
        reference_stress_solution = 80.0

        toughness_ratio, load_ratio = self.failure_assessment.assess_failure_state(
            stress_intensity_factor, reference_stress_solution
        )

        # Check expected values
        self.assertAlmostEqual(toughness_ratio, stress_intensity_factor / self.fracture_resistance)
        self.assertAlmostEqual(load_ratio, reference_stress_solution / self.yield_stress)

    def test_determine_fad_values_anderson(self):
        """Test the determine_fad_values function for Anderson method."""
        fatigue_instance = {
            'Kmax (MPa m^1/2)': [30.0],
            'Kres (MPa m^1/2)': [10.0],
            'a (m)': [0.01],
            'c (m)': [0.02]
        }

        stress_state = MockStressState(method='anderson')

        toughness_ratio, load_ratio = determine_fad_values(fatigue_instance,
                                                           stress_state,
                                                           self.failure_assessment)

        # Check expected values
        self.assertIsInstance(toughness_ratio[0], float)
        self.assertIsInstance(toughness_ratio, list)
        self.assertIsInstance(load_ratio[0], float)
        self.assertIsInstance(load_ratio, list)

    def test_determine_fad_values_api(self):
        """Test the determine_fad_values function for API method."""
        fatigue_instance = {
            'Kmax (MPa m^1/2)': [30.0],
            'Kres (MPa m^1/2)': [10.0],
            'a (m)': [0.01],
            'c (m)': [0.02]
        }

        stress_state = MockStressState(method='api')

        toughness_ratio, load_ratio = determine_fad_values(fatigue_instance,
                                                           stress_state,
                                                           self.api_failure_assessment)

        # Check expected values
        self.assertIsInstance(toughness_ratio[0], float)
        self.assertIsInstance(toughness_ratio, list)
        self.assertIsInstance(load_ratio[0], float)
        self.assertIsInstance(load_ratio, list)

        fatigue_instance = {
            'Kmax (MPa m^1/2)': [30.0],
            'Kres (MPa m^1/2)': [0.0],
            'a (m)': [0.01],
            'c (m)': [0.02]
        }

        toughness_ratio, load_ratio = determine_fad_values(fatigue_instance,
                                                           stress_state,
                                                           self.api_failure_assessment)
        # Check expected values
        self.assertIsInstance(toughness_ratio[0], float)
        self.assertIsInstance(toughness_ratio, list)
        self.assertIsInstance(load_ratio[0], float)
        self.assertIsInstance(load_ratio, list)


    def test_process_fatigue_instance(self):
        """Test the process_fatigue_instance function."""
        fatigue_instance = {
            'Kmax (MPa m^1/2)': [30.0],
            'Kres (MPa m^1/2)': [10.0],
            'a (m)': [0.01],
            'c (m)': [0.02]
        }

        stress_state = MockStressState(method='anderson')

        updated_instance = process_fatigue_instance(fatigue_instance,
                                                    self.fracture_resistance,
                                                    self.yield_stress,
                                                    stress_state,
                                                    self.fad_type)

        # Check if the toughness and load ratios are added
        self.assertIn('Toughness ratio', updated_instance)
        self.assertIn('Load ratio', updated_instance)

    def test_determine_fad_values_invalid_type(self):
        """Test the determine_fad_values function with an invalid FAD type."""
        fatigue_instance = {
            'Kmax (MPa m^1/2)': [30.0],
            'Kres (MPa m^1/2)': [10.0],
            'a (m)': [0.01],
            'c (m)': [0.02]
        }

        stress_state = MockStressState(method='anderson')
        invalid_fad_instance = FailureAssessment(self.fracture_resistance, self.yield_stress, 'invalid FAD type')

        with self.assertRaises(ValueError):
            determine_fad_values(fatigue_instance, stress_state, invalid_fad_instance)

if __name__ == '__main__':
    unittest.main()
