# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

from helpr.physics.pipe import Pipe


class PipeTestCase(unittest.TestCase):
    """Class for pipe module unit tests."""

    def setUp(self):
        """Function to specify common inputs to pipe module."""

    def tearDown(self):
        """Teardown function."""

    def test_bad_pipe_size(self):
        """
        Unit tests of bad pipe size specification.
        
        Raises
        ------
        ValueError
            If the wall thickness is greater than or equal to the outer diameter.
        """
        outer_diameter = 10
        wall_thickness = 11
        with self.assertRaises(ValueError):
            Pipe(outer_diameter=outer_diameter,
                 wall_thickness=wall_thickness)

    def test_simple_calcs(self):
        """Unit test to check simple pipe calculations"""
        wall_thickness = 0.5
        outer_diameter = 5
        test_pipe = Pipe(outer_diameter=outer_diameter,
                         wall_thickness=wall_thickness)
        self.assertEqual(test_pipe.calc_average_radius(), 2.25)
        self.assertEqual(test_pipe.calc_inner_diameter(), 4)
        self.assertEqual(test_pipe.calc_t_over_r(), 0.25)

if __name__ == '__main__':
    unittest.main()
