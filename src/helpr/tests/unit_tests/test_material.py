# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

from helpr.physics.material import MaterialSpecification


class MaterialTestCase(unittest.TestCase):
    """
    Class for unit tests of material module.
    
    Attributes
    ----------
    yield_strength : float
        Yield strength of the material.
    fracture_resistance : float
        Fracture resistance of the material.
    """
    
    def setUp(self):
        """Function for specifying common material module inputs."""
        self.yield_strength = 100
        self.fracture_resistance = 55

    def tearDown(self):
        """Teardown function."""

    def test_default(self):
        """Unit test of default behavior for material module."""
        test_material = MaterialSpecification(yield_strength=self.yield_strength,
                                              fracture_resistance=self.fracture_resistance)
        self.assertEqual(self.yield_strength, test_material.yield_strength)
        self.assertEqual(self.fracture_resistance, test_material.fracture_resistance)

if __name__ == '__main__':
    unittest.main()
