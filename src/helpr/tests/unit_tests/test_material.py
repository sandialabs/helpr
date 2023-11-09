# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
from helpr.physics.material import MaterialSpecification


class MaterialTestCase(unittest.TestCase):
    """class for unit tests of material module"""
    def setUp(self):
        """function for specifying common material module inputs"""
        self.yield_strength = 100
        self.fracture_resistance = 55

    def tearDown(self):
        """teardown function"""

    def test_default(self):
        """unit test of default behavior for material module"""
        test_material = MaterialSpecification(yield_strength=self.yield_strength,
                                              fracture_resistance=self.fracture_resistance)
        self.assertEqual(self.yield_strength, test_material.yield_strength)
        self.assertEqual(self.fracture_resistance, test_material.fracture_resistance)

    def test_single_instance(self):
        """unit test of accessing single instance of material specification object"""
        yield_strength_list = [100, 200]
        fracture_resistance_list = [55, 52]
        test_materials = MaterialSpecification(yield_strength=yield_strength_list,
                                               fracture_resistance=fracture_resistance_list,
                                               sample_size=2)
        self.assertEqual(yield_strength_list[0],
                         test_materials.get_single_material(0).yield_strength)
        self.assertEqual(yield_strength_list[1],
                         test_materials.get_single_material(1).yield_strength)
        self.assertEqual(fracture_resistance_list[0],
                         test_materials.get_single_material(0).fracture_resistance)
        self.assertEqual(fracture_resistance_list[1],
                         test_materials.get_single_material(1).fracture_resistance)

if __name__ == '__main__':
    unittest.main()
