# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import os
import pathlib
from copy import deepcopy
from unittest.mock import patch
from unittest.mock import MagicMock
import numpy as np

from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.stress_state import (GenericStressState,
                                        InternalAxialHoopStress,
                                        InternalCircumferentialLongitudinalStress)

from helpr.tests.integration_tests.test_stress_state_integration import StressStateTestCase

path = pathlib.Path(__file__).parent.resolve()
data_dir = os.path.join(path, '../../data')

class InternalAxialHoopStressTestCase(StressStateTestCase):
    """
    Class for unit tests of internal axial hoop stress class.
    
    Attributes
    ----------
    stress_state_anderson : InternalAxialHoopStress
        Instance of InternalAxialHoopStress class using Anderson's method.
    stress_state_api_internal : InternalAxialHoopStress
        Instance of InternalAxialHoopStress class using API method for internal cracks.
    stress_state_api_external : InternalAxialHoopStress
        Instance of InternalAxialHoopStress class using API method for external cracks.
    """

    def setUp(self):
        """Set up the test case."""
        super(InternalAxialHoopStressTestCase, self).setUp()
        self.stress_state_anderson = InternalAxialHoopStress(self.pipe,
                                                self.environment,
                                                self.material,
                                                self.internal_defect,
                                                'anderson')
        self.stress_state_api_internal = InternalAxialHoopStress(self.pipe,
                                                self.environment,
                                                self.material,
                                                self.internal_defect,
                                                'api')
        self.stress_state_api_external = InternalAxialHoopStress(self.pipe,
                                                self.environment,
                                                self.material,
                                                self.external_defect,
                                                'api')


    def test_ref_stress_api(self):
        """Unit test to check default behavior of API reference stress
           solution method for typical inputs."""
        test_ref_stress = self.stress_state_api_internal.calc_ref_stress_api(
            crack_depth=0.04)
        exp_ref_stress = 184.84676
        self.assertAlmostEqual(test_ref_stress, exp_ref_stress, places=4)


    def test_stress_intensity_factor_anderson_internal(self):
        """Unit test to check that axial hoop stress intensity factor calculated with Anderson's
           equation produces expected values (hand calc) for internal crack."""
        crack_depth = 0.04
        crack_length = 0.05
        test_k_max, test_k_min, test_f, test_q = \
            self.stress_state_anderson.calc_stress_intensity_factor(crack_depth,
                                                                    crack_length)
        exp_k = 38.23612
        exp_f = 1.16980
        exp_q = 4.17936
        self.assertAlmostEqual(test_k_max, exp_k, 4)
        self.assertAlmostEqual(test_f, exp_f, 4)
        self.assertAlmostEqual(test_q, exp_q, 4)

    def test_stress_intensity_factor_anderson_external(self):
        """
        Unit test to check that axial hoop stress intensity factor calculated with Anderson's
        equation produces error message for external crack.
        
        Raises
        ------
        ValueError
            If the Anderson stress intensity method is used for an external crack.
        """
        crack_depth = 0.04
        crack_length = 0.05
        stress_state = deepcopy(self.stress_state_anderson)
        stress_state.defect_specification = self.external_defect
        with self.assertRaises(ValueError) as error_msg:
            _, _, _, _= (
                stress_state.calc_stress_intensity_factor(
                crack_depth, crack_length))
        exp_msg = ('Anderson stress intensity method is only valid for ' +
                   'interior cracks. Set ' +
                   "InternalAxialHoopStress.stress_intensity_method to 'api'")
        self.assertEqual(str(error_msg.exception), exp_msg)

    def test_stress_intensity_factor_invalid_method(self):
        """
        Unit test to check an exception is raised when a method
        other than Anderson or API is specified.
        
        Raises
        ------
        ValueError
            If the stress_intensity_method is not 'anderson' or 'api'.
        """
        with self.assertRaises(ValueError) as error_msg:
            _ = InternalAxialHoopStress(self.pipe,
                                        self.environment,
                                        self.material,
                                        self.internal_defect,
                                        'bad_method')
        exp_msg = ("stress_intensity_method must be specified as 'anderson' " +
                   "or 'api', currently is bad_method")
        self.assertEqual(str(error_msg.exception), exp_msg)


    def test_load_api_table_invalid_surface(self):
        """
        Unit test to check an exception is raised when an invalid
        surface is specified when loading API table.
        
        Raises
        ------
        ValueError
            If the surface is not 'inside' or 'outside'.
        """
        with self.assertRaises(ValueError) as error_msg:
            table = InternalAxialHoopStress.load_api_tables('bad surface')
        exp_msg = ('surface must be specified as inside or ' + 
                   'outside, currently bad surface')
        self.assertEqual(str(error_msg.exception), exp_msg)

    def test_ref_stress_api_with_zero_crack(self):
        """Test calc_ref_stress_api triggers fallback for zero crack depth."""
        stress_state = self.stress_state_api_internal
        stress = stress_state.calc_ref_stress_api(crack_depth=0.0)
        self.assertIsNotNone(stress)  # No crash expected

    def test_calc_k_solution_finite_length_api_reshapes(self):
        """Test reshaping in calc_k_solution_finite_length_part_through_flaw_api."""
        state = deepcopy(self.stress_state_api_internal)
        # force internal crack
        state.defect_specification.surface = 'inside'

        # Mock the G parameters to have ndim > 1
        state.calc_G_parameters_finite_length = MagicMock(return_value=(
            np.array([[1.0]]),  # G0
            np.array([[0.5]]),  # G1 (ndim = 2)
            np.array([[0.1]]),
            np.array([[0.05]]),
            np.array([[0.02]])
        ))
        state.interp_table_parameters = MagicMock(return_value=np.zeros((1, 2)))
        crack_depth = np.array([0.04])
        crack_length = np.array([0.05])
        state.calc_q = MagicMock(return_value=np.array([1.]))
        k, _, _ = state.calc_k_solution_finite_length_part_through_flaw_api(crack_depth,
                                                                            crack_length)
        self.assertIsNotNone(k)


if __name__ == '__main__':
    unittest.main()
