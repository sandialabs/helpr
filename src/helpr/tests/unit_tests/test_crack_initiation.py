# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

from helpr.physics.crack_initiation import DefectSpecification


class CrackInitiationTestCase(unittest.TestCase):
    """Class for units test of crack initiation module"""
    def setUp(self):
        """function for specifying common inputs to crack initiation module"""
        self.location_factor = 1
        self.flaw_depth = 5
        self.flaw_length = 0.001

    def tearDown(self):
        """teardown function"""


    def test_default(self):
        """unit test of default functionality of crack initiation module"""
        defect = DefectSpecification(flaw_depth=self.flaw_depth,
                                     flaw_length=self.flaw_length,
                                     location_factor=self.location_factor)
        self.assertTrue(len(defect.flaw_depth) == 1)

    def test_array_inputs(self):
        """unit test of passing input arrays to crack initiation module"""
        flaw_depth = [self.flaw_depth, 10]
        flaw_length = [self.flaw_length, 0.01]
        defects = DefectSpecification(flaw_depth=flaw_depth,
                                      flaw_length=flaw_length,
                                      location_factor=self.location_factor,
                                      sample_size=2)
        self.assertTrue(len(defects.flaw_depth) == 2)
        second_defect = defects.get_single_defect(1)
        self.assertTrue(defects.flaw_depth[1] == second_defect.flaw_depth)

if __name__ == '__main__':
    unittest.main()
