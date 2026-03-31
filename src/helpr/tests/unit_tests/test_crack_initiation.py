# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

from helpr.physics.crack_initiation import DefectSpecification


class CrackInitiationTestCase(unittest.TestCase):
    """
    Class for units test of crack initiation module
    
    Attributes
    ----------
    location_factor : float
        Location factor for the defect.
    flaw_depth : float
        Depth of the flaw.
    flaw_length : float
        Length of the flaw.
    surface : str
        Surface of the defect (inside or outside).
    """

    def setUp(self):
        """Function for specifying common inputs to crack initiation module."""
        self.location_factor = 1
        self.flaw_depth = 5
        self.flaw_length = 0.001
        self.surface = 'inside'

    def tearDown(self):
        """Teardown function."""

    def test_default(self):
        """Unit test of default functionality of crack initiation module."""
        defect = DefectSpecification(flaw_depth=self.flaw_depth,
                                     flaw_length=self.flaw_length,
                                     location_factor=self.location_factor)
        self.assertTrue(defect.flaw_depth == self.flaw_depth)
        self.assertTrue(defect.flaw_length == self.flaw_length)

    def test_bad_surface_specification(self):
        """
        Unit test of check that bad specifications of defect surface are caught.
        
        Raises
        ------
        ValueError
            If the surface specification is invalid.
        """
        bad_surface_spec = 'inner'
        with self.assertRaises(ValueError):
            _ = DefectSpecification(
                self.flaw_depth, self.flaw_length, bad_surface_spec)


if __name__ == '__main__':
    unittest.main()
