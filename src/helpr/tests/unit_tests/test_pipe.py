# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

from helpr.physics.pipe import Pipe


class PipeTestCase(unittest.TestCase):
    """class for pipe module unit tests"""
    def setUp(self):
        """function to specify common inputs to pipe module"""

    def tearDown(self):
        """teardown function"""

    def test_bad_pipe_size(self):
        """unit tests of bad pipe size specification"""
        outer_diameter = 10
        wall_thickness = 11
        with self.assertRaises(ValueError):
            Pipe(outer_diameter=outer_diameter,
                 wall_thickness=wall_thickness)

    def test_array_input(self):
        """unit test of passing array of inputs to pipe module"""
        wall_thickness = [1, 3, 2]
        outer_diameter = [8, 10, 6]
        test_pipe = Pipe(outer_diameter=outer_diameter,
                         wall_thickness=wall_thickness,
                         sample_size=3)
        self.assertEqual(len(test_pipe.pipe_avg_radius), 3)

        second_pipe = test_pipe.get_single_pipe(1)
        self.assertEqual(second_pipe.wall_thickness,
                         test_pipe.wall_thickness[1])
        self.assertEqual(second_pipe.outer_diameter,
                         test_pipe.outer_diameter[1])

        wall_thickness = [1, 3, 7]
        outer_diameter = [8, 10, 6]
        with self.assertRaises(ValueError):
            Pipe(outer_diameter=outer_diameter,
                 wall_thickness=wall_thickness,
                 sample_size=3)

    def test_simple_calcs(self):
        """unit test to check simple pipe calculations"""
        wall_thickness = 0.5
        outer_diameter = 5
        test_pipe = Pipe(outer_diameter=outer_diameter,
                         wall_thickness=wall_thickness)
        self.assertEqual(test_pipe.calc_average_radius(), 2.25)
        self.assertEqual(test_pipe.calc_inner_diameter(), 4)
        self.assertEqual(test_pipe.calc_t_over_r(), 0.25)

if __name__ == '__main__':
    unittest.main()
