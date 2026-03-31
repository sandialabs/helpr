# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.residual_stress import (HeatInputFromPower,
                                           HeatInputFromProcess,
                                           CircumferentialWeld,
                                           LongitudinalWeld,
                                           FilletWeld)


class HeatInputTestCase(unittest.TestCase):
    """Class for unit tests of heat input objects."""

    def test_heat_input_from_power(self):
        """Check that the heat input math works correctly within the
           HeatInputFromPower class."""
        current = 0.2
        voltage = 10
        speed = 25
        test_heat_obj = HeatInputFromPower(current, voltage, speed)
        test_heat_input = test_heat_obj.calc_heat_input()
        exp_heat_input = current * voltage / speed

        self.assertEqual(test_heat_input, exp_heat_input)

    def test_heat_input_from_process(self):
        """Check that the heat input logic works correctly within the
           HeatInputFromProcess class."""
        processes = ['SMAW', 'SAW', 'GTAW', 'GMAW']
        steels = ['Ferritic', 'Austenitic']
        exp_heat_inputs = [1130, 1220, 500, 390,
                           940, 1080, 500, 390]
        test_heat_inputs = []
        i = 0
        for steel in steels:
            for process in processes:
                i += 1
                test_heat_obj = HeatInputFromProcess(process, steel)
                test_heat_inputs.append(test_heat_obj.calc_heat_input())

        self.assertListEqual(test_heat_inputs, exp_heat_inputs)

    def test_heat_input_from_process_bad_process(self):
        """
        Check that the proper error is raised if an invalid process is given.
           
        Raises
        ------
        ValueError
            If the weld process is not recognized.   
        """
        bad_process = 'SLAW'
        steel = 'Ferritic'
        with self.assertRaises(ValueError) as error_msg:
            HeatInputFromProcess(bad_process, steel)
        exp_msg = ('Weld process not recognized. Valid options are ' +
                   "'SMAW', 'SAW', 'GTAW', and 'GMAW'.")
        
        self.assertEqual(str(error_msg.exception), exp_msg)

    def test_heat_input_from_process_bad_steel(self):
        """
        Check that the proper error is raised if an invalid weld
        steel is given.
        
        Raises
        ------
        ValueError
            If the weld steel is not recognized.
        """
        bad_steel = 'Carbon'
        process = 'SMAW'
        with self.assertRaises(ValueError) as error_msg:
            HeatInputFromProcess(process, bad_steel)
        exp_msg = ('Weld steel not recognized. Valid options are ' +
                   "'ferritic' and 'austenitic'")
        
        self.assertEqual(str(error_msg.exception), exp_msg)


class CircumferentialWeldTestCase(unittest.TestCase):
    """
    Class for unit tests of CircumferentialWeld objects and
       accompanying residual stress calculations.
       
    Attributes
    ----------
    pipe : Pipe
        Pipe object with outer diameter and wall thickness.
    thin_pipe : Pipe
        Pipe object with thin wall thickness.
    thick_pipe : Pipe
        Pipe object with thick wall thickness.
    very_thick_pipe : Pipe
        Pipe object with very thick wall thickness.
    environment : EnvironmentSpecification
        Environment specification object with max pressure, min pressure, temperature, and volume fraction of hydrogen.
    material : MaterialSpecification
        Material specification object with yield strength and fracture resistance.
    defect : DefectSpecification
        Defect specification object with flaw depth, flaw length, and surface.
    weld_thickness : float
        Thickness of the weld.
    heat : int
        Heat for the test case.
    x : float
        Value of x for the test case.   
    """

    def setUp(self):
        """Set uo the test cases with the required parameters."""
        max_pressure = 13
        min_pressure = 1
        temperature = 300
        volume_fraction_h2 = 1
        flaw_depth = 10
        flaw_length = 0.01
        fracture_resistance = 55
        yield_strength = 670
        self.pipe = Pipe(outer_diameter=4, wall_thickness=0.1)
        self.thin_pipe = Pipe(outer_diameter=4, wall_thickness=0.008)
        self.thick_pipe = Pipe(outer_diameter=4, wall_thickness=0.5)
        self.very_thick_pipe = Pipe(outer_diameter=4, wall_thickness=1)
        self.environment = EnvironmentSpecification(
            max_pressure=max_pressure,
            min_pressure=min_pressure,
            temperature=temperature,
            volume_fraction_h2=volume_fraction_h2)
        self.material = MaterialSpecification(
            yield_strength=yield_strength,
            fracture_resistance=fracture_resistance)
        self.defect = DefectSpecification(
            flaw_depth=flaw_depth,
            flaw_length=flaw_length,
            surface='inside')
        self.weld_thickness = 0.02
        self.heat = 10000
        self.x = 0.05 * flaw_depth / 100

    def test_circumferentialweld_bad_heat_input(self):
        """
        Unit test to check proper error handling if the heat input
        is negative.
        
        Raises
        ------
        ValueError
            If the heat input is negative.
        """
        bad_heat = -1
        with self.assertRaises(ValueError) as error_msg:
            test_weld = CircumferentialWeld(
                        pipe=self.pipe,
                        environment=self.environment,
                        material=self.material,
                        defect=self.defect,
                        weld_thickness=self.weld_thickness,
                        flaw_direction='perpendicular',
                        heat_input=bad_heat)
        exp_msg = ('Weld heat input cannot be negative.')
        
        self.assertEqual(str(error_msg.exception), exp_msg)

    def test_calc_resid_stress(self):
        """Unit test to check residual stress for various configurations
        of a circumferential weld."""
        w = self.weld_thickness
        test_cases = [
            {'flaw_direction': 'perpendicular', 'y': 0, 'pipe': self.thin_pipe, 'exp_resid_stress': 93.2410},
            {'flaw_direction': 'perpendicular', 'y': 0, 'pipe': self.pipe, 'exp_resid_stress': 602.4717},
            {'flaw_direction': 'perpendicular', 'y': 0, 'pipe': self.thick_pipe, 'exp_resid_stress': 690.5227},
            {'flaw_direction': 'perpendicular', 'y': 0, 'pipe': self.very_thick_pipe, 'exp_resid_stress': 714.3203},
            {'flaw_direction': 'parallel', 'y': 0, 'pipe': self.thin_pipe, 'exp_resid_stress': 739.0000},
            {'flaw_direction': 'parallel', 'y': 0, 'pipe': self.pipe, 'exp_resid_stress': 36.9500},
            {'flaw_direction': 'parallel', 'y': 0, 'pipe': self.thick_pipe, 'exp_resid_stress': 7.3900},
            {'flaw_direction': 'parallel', 'y': 0, 'pipe': self.very_thick_pipe, 'exp_resid_stress': 3.6950},
            {'flaw_direction': 'perpendicular', 'y': 3 * w, 'pipe': self.thin_pipe, 'exp_resid_stress': 23.3103},
            {'flaw_direction': 'perpendicular', 'y': 3 * w, 'pipe': self.pipe, 'exp_resid_stress': 595.3986},
            {'flaw_direction': 'perpendicular', 'y': 3 * w, 'pipe': self.thick_pipe, 'exp_resid_stress': 686.4894},
            {'flaw_direction': 'perpendicular', 'y': 3 * w, 'pipe': self.very_thick_pipe, 'exp_resid_stress': 710.7126},
            {'flaw_direction': 'parallel', 'y': 3 * w, 'pipe': self.thin_pipe, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'parallel', 'y': 3 * w, 'pipe': self.pipe, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'parallel', 'y': 3 * w, 'pipe': self.thick_pipe, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'parallel', 'y': 3 * w, 'pipe': self.very_thick_pipe, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'perpendicular', 'y': 5 * w, 'pipe': self.thin_pipe, 'exp_resid_stress': -44.4264},
            {'flaw_direction': 'perpendicular', 'y': 5 * w, 'pipe': self.pipe, 'exp_resid_stress': 581.2525},
            {'flaw_direction': 'perpendicular', 'y': 5 * w, 'pipe': self.thick_pipe, 'exp_resid_stress': 678.4227},
            {'flaw_direction': 'perpendicular', 'y': 5 * w, 'pipe': self.very_thick_pipe, 'exp_resid_stress': 703.4973},
            {'flaw_direction': 'parallel', 'y': 5 * w, 'pipe': self.thin_pipe, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'parallel', 'y': 5 * w, 'pipe': self.pipe, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'parallel', 'y': 5 * w, 'pipe': self.thick_pipe, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'parallel', 'y': 5 * w, 'pipe': self.very_thick_pipe, 'exp_resid_stress': 0.0000}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                test_weld = CircumferentialWeld(
                    pipe=case['pipe'],
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction=case['flaw_direction'],
                    flaw_distance=case['y'],
                    heat_input=self.heat)
                test_resid_stress = test_weld.calc_resid_stress(self.x)
                
                self.assertAlmostEqual(
                    test_resid_stress, case['exp_resid_stress'], places=4)

    def test_calc_resid_stress_bad_x(self):
        """
        Unit test to check proper error handling if x is not less
        than the pipe wall thickness.
           
        Raises
        ------
        ValueError
            If x is not less than the pipe wall thickness.   
        """
        bad_x = self.pipe.wall_thickness * 1.1
        test_weld = CircumferentialWeld(
                        pipe=self.pipe,
                        environment=self.environment,
                        material=self.material,
                        defect=self.defect,
                        weld_thickness=self.weld_thickness,
                        flaw_direction='perpendicular',
                        heat_input=self.heat)
        with self.assertRaises(ValueError) as error_msg:
            test_resid_stress = test_weld.calc_resid_stress(bad_x)
        exp_msg = ('`x` must be less than the pipe wall thickness.')
        
        self.assertEqual(str(error_msg.exception), exp_msg)


class LongitudinalWeldTestCase(unittest.TestCase):
    """
    Class for unit tests of LongitudinalWeld objects and
    accompanying residual stress calculations.
       
    Attributes
    ----------
    pipe : Pipe
        Pipe object with outer diameter and wall thickness.
    environment : EnvironmentSpecification
        Environment specification object with max pressure, min pressure, temperature, and volume fraction of hydrogen.
    material : MaterialSpecification
        Material specification object with yield strength and fracture resistance.
    defect : DefectSpecification
        Defect specification object with flaw depth, flaw length, and surface.
    weld_thickness : float
        Thickness of the weld.
    x : float
        Value of x for the test case.
    """

    def setUp(self):
        max_pressure = 13
        min_pressure = 1
        temperature = 300
        volume_fraction_h2 = 1
        flaw_depth = 10
        flaw_length = 0.01
        fracture_resistance = 55
        yield_strength = 670
        self.pipe = Pipe(outer_diameter=4,
            wall_thickness=0.1)
        self.environment = EnvironmentSpecification(
            max_pressure=max_pressure,
            min_pressure=min_pressure,
            temperature=temperature,
            volume_fraction_h2=volume_fraction_h2)
        self.material = MaterialSpecification(
            yield_strength=yield_strength,
            fracture_resistance=fracture_resistance)
        self.defect = DefectSpecification(
            flaw_depth=flaw_depth,
            flaw_length=flaw_length,
            surface='inside')
        self.weld_thickness = 0.02
        self.x = 0.1 * flaw_depth / 100

    def test_calc_resid_stress(self):
        """Unit test to check residual stress for various configurations
           of a longitudinal weld."""
        w = self.weld_thickness
        test_cases = [
            {'flaw_direction': 'perpendicular', 'y': 0, 'exp_resid_stress': 347.9582},
            {'flaw_direction': 'parallel', 'y': 0, 'exp_resid_stress': 739.0000},
            {'flaw_direction': 'perpendicular', 'y': 1.25*w, 'exp_resid_stress': 260.9686},
            {'flaw_direction': 'parallel', 'y': 1.25*w, 'exp_resid_stress': 369.5000},
            {'flaw_direction': 'perpendicular', 'y': 1.75*w, 'exp_resid_stress': 86.9895},
            {'flaw_direction': 'parallel', 'y': 1.75*w, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'perpendicular', 'y': 2*w, 'exp_resid_stress': 0.0000},
            {'flaw_direction': 'parallel', 'y': 2*w, 'exp_resid_stress': 0.0000}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                test_weld = LongitudinalWeld(
                    pipe=self.pipe,
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction=case['flaw_direction'],
                    flaw_distance= case['y'])
                test_resid_stress = test_weld.calc_resid_stress(self.x)
                
                self.assertAlmostEqual(
                    test_resid_stress, case['exp_resid_stress'], places=4)

class FilletWeldTestCase(unittest.TestCase):
    """
    Class for unit tests of FilletWeld objects and
    accompanying residual stress calculations.
       
    Attributes
    ----------
    pipe : Pipe
        Pipe object with outer diameter and wall thickness.
    environment : EnvironmentSpecification
        Environment specification object with max pressure, min pressure, temperature, and volume fraction of hydrogen.
    material : MaterialSpecification
        Material specification object with yield strength and fracture resistance.
    defect : DefectSpecification
        Defect specification object with flaw depth, flaw length, and surface.
    weld_thickness : float
        Thickness of the weld.
    x : float
        Value of x for the test case.
    weld_material : str
        Material of the weld   
    """

    def setUp(self):
        """Set up the test case with the required parameters."""
        max_pressure = 13
        min_pressure = 1
        temperature = 300
        volume_fraction_h2 = 1
        flaw_depth = 10
        flaw_length = 0.01
        fracture_resistance = 55
        yield_strength = 670
        self.pipe = Pipe(outer_diameter=4, wall_thickness=0.1)
        self.environment = EnvironmentSpecification(
            max_pressure=max_pressure,
            min_pressure=min_pressure,
            temperature=temperature,
            volume_fraction_h2=volume_fraction_h2)
        self.material = MaterialSpecification(
            yield_strength=yield_strength,
            fracture_resistance=fracture_resistance)
        self.defect = DefectSpecification(
            flaw_depth=flaw_depth,
            flaw_length=flaw_length,
            surface='inside')
        self.weld_thickness = 0.02
        self.x = 0.1 * flaw_depth / 100
        self.weld_material = 'ferritic'

    def test_filletweld_bad_joint(self):
        """
        Unit test to check proper error handling if the joint type
        is invalid.
        
        Raises
        ------
        ValueError
            If the joint type is not recognized.
        """
        bad_joint = 'invalid'
        surface = 'set-in'
        with self.assertRaises(ValueError) as error_msg:
            test_weld = FilletWeld(
                    pipe=self.pipe,
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction='perpendicular',
                    joint=bad_joint,
                    surface=surface)
        exp_msg = ('Joint type not recognized. Valid options are '+
                   "'corner' and 'tee'.")
        
        self.assertEqual(str(error_msg.exception), exp_msg)
        
    def test_filletweld_bad_surface(self):
        """
        Unit test to check proper error handling if the surface type
        is invalid.
           
        Raises
        ------
        ValueError
            If the surface type is invalid for the given joint type.   
        """
        joint = 'corner'
        bad_surface = 'invalid'
        with self.assertRaises(ValueError) as error_msg:
            test_weld = FilletWeld(
                    pipe=self.pipe,
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction='perpendicular',
                    joint=joint,
                    surface=bad_surface)
        exp_msg = ('Surface type invalid for corner joint. ' +
                   "Valid options are 'set-in', 'set-on', 'pad', and " +
                   "'branch'.")
        
        self.assertEqual(str(error_msg.exception), exp_msg)
        
    def test_filletweld_bad_weld_material(self):
        """
        Unit test to check proper error handling if the weld material
        type is invalid.
           
        Raises
        ------
        ValueError
            If the weld material type is not recognized.   
        """
        joint = 'corner'
        surface = 'set-in'
        bad_weld_material = 'invalid'
        with self.assertRaises(ValueError) as error_msg:
            test_weld = FilletWeld(
                    pipe=self.pipe,
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction='perpendicular',
                    joint=joint,
                    surface=surface,
                    weld_material=bad_weld_material)
        exp_msg = ('Weld material invalid. Valid options are ' +
                   "'ferritic' and 'austenitic'.")
        
        self.assertEqual(str(error_msg.exception), exp_msg)
        
    def test_filletweld_joint_surface_mismatch(self):
        """
        Unit test to check proper error handling if a corner joint
        surface is used for tee joint and vice versa.
           
        Raises
        ------
        ValueError
            If the surface type is not valid for the given joint type.
        """
        corner_joint = 'corner'
        tee_joint = 'tee'
        corner_surface = 'set-in'
        tee_surface = 'mainplate'
        with self.assertRaises(ValueError) as error_msg_corner:
            test_weld = FilletWeld(
                    pipe=self.pipe,
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction='perpendicular',
                    joint=corner_joint,
                    surface=tee_surface)
        with self.assertRaises(ValueError) as error_msg_tee:
            test_weld = FilletWeld(
                    pipe=self.pipe,
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction='perpendicular',
                    joint=tee_joint,
                    surface=corner_surface)
        exp_msg_corner = ('Surface type invalid for corner joint. ' +
                   "Valid options are 'set-in', 'set-on', 'pad', and " +
                   "'branch'.")
        exp_msg_tee = ('Surface type invalid for tee joint. ' +
                       "Valid options are 'mainplate' and " +
                       "'stayplate'.")
        
        self.assertEqual(
            str(error_msg_corner.exception), exp_msg_corner)
        self.assertEqual(
            str(error_msg_tee.exception), exp_msg_tee)
    
    def test_filletweld_material_not_specified(self):
        """
        Unit test to check that FilletWeld warns and defaults if
        `weld_material` is not specified for a piping branch corner weld.
           
        Raises
        ------
        UserWarning
            If `weld_material` is not specified for a piping branch corner weld.   
        """
        joint = 'corner'
        surface = 'branch'
        weld_material = None
        with self.assertWarns(UserWarning) as warning_msg:
            test_weld = FilletWeld(
                    pipe=self.pipe,
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction='perpendicular',
                    joint=joint,
                    surface=surface,
                    weld_material=weld_material)
        exp_msg = ('Weld material not specified for a piping ' +
                   'branch connection. Assuming ferritic ' +
                   'stainless steel weld metal.')
        exp_default_weld_material = 'ferritic'

        self.assertEqual(
            str(warning_msg.warning), exp_msg)
        self.assertEqual(
            test_weld.weld_material, exp_default_weld_material)

    def test_calc_resid_stress_corner(self):
        """Unit test to check residual stress for various configurations
           of a corner joint fillet weld."""
        t = self.pipe.wall_thickness
        w = self.weld_thickness
        test_cases = [
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'set-in', 'y': 0, 'exp_resid_stress': 643.2256},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'set-on', 'y': 0, 'exp_resid_stress': 643.2256},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'pad', 'y': 0, 'exp_resid_stress': 470.2996},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'branch', 'y': 0, 'exp_resid_stress': 740.3496},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'set-in', 'y': 0, 'exp_resid_stress': 739.0},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'set-on', 'y': 0, 'exp_resid_stress': 739.0},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'pad', 'y': 0, 'exp_resid_stress': 470.2996},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'branch', 'y': 0, 'exp_resid_stress': 840.8328},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'set-in', 'y': t * 1.25, 'exp_resid_stress': 606.1427},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'set-on', 'y': t * 1.25, 'exp_resid_stress': 606.1427},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'pad', 'y': w * 1.5, 'exp_resid_stress': 235.1498},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'branch', 'y': t * 1.25, 'exp_resid_stress': 697.6674},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'set-in', 'y': t * 1.25, 'exp_resid_stress': 369.5},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'set-on', 'y': t * 1.25, 'exp_resid_stress': 369.5},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'pad', 'y': t * 1.25, 'exp_resid_stress': 235.1498},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'branch', 'y': t * 1.25, 'exp_resid_stress': 420.4164},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'set-in', 'y': t * 5, 'exp_resid_stress': 49.8988},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'set-on', 'y': t * 5, 'exp_resid_stress': 49.8988},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'pad', 'y': t * 5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'branch', 'y': t * 5, 'exp_resid_stress': 57.4333},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'set-in', 'y': t * 5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'set-on', 'y': t * 5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'pad', 'y': t * 5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'branch', 'y': t * 5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'set-in', 'y': t * 7.5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'set-on', 'y': t * 7.5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'branch', 'y': t * 7.5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'branch', 'weld_material': 'austenitic', 'y': 0, 'exp_resid_stress': 739.0},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'branch', 'weld_material': 'austenitic', 'y': 0, 'exp_resid_stress': 739.0},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'branch', 'weld_material': 'austenitic', 'y': t * 1.25, 'exp_resid_stress': 696.3955},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'branch', 'weld_material': 'austenitic', 'y': t * 1.25, 'exp_resid_stress': 369.5},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'branch', 'weld_material': 'austenitic', 'y': t * 5, 'exp_resid_stress': 57.3286},
            {'flaw_direction': 'parallel', 'joint': 'corner', 'surface': 'branch', 'weld_material': 'austenitic', 'y': t * 5, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'perpendicular', 'joint': 'corner', 'surface': 'branch', 'weld_material': 'austenitic', 'y': t * 7.5, 'exp_resid_stress': 0.0}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                if 'weld_material' in case.keys():
                    test_weld = FilletWeld(
                        pipe=self.pipe,
                        environment=self.environment,
                        material=self.material,
                        defect=self.defect,
                        weld_thickness=self.weld_thickness,
                        flaw_direction=case['flaw_direction'],
                        flaw_distance=case['y'],
                        joint=case['joint'],
                        surface=case['surface'],
                        weld_material=case['weld_material'])
                else:
                    test_weld = FilletWeld(
                        pipe=self.pipe,
                        environment=self.environment,
                        material=self.material,
                        defect=self.defect,
                        weld_thickness=self.weld_thickness,
                        flaw_direction=case['flaw_direction'],
                        flaw_distance=case['y'],
                        joint=case['joint'],
                        surface=case['surface'])
                test_resid_stress = test_weld.calc_resid_stress(self.x)
                
                self.assertAlmostEqual(
                    test_resid_stress, case['exp_resid_stress'], places=4)

    def test_calc_resid_stress_tee(self):
        """Unit test to check residual stress for various configurations
           of a tee joint fillet weld."""
        t = self.pipe.wall_thickness
        test_cases = [
            {'flaw_direction': 'perpendicular', 'joint': 'tee', 'surface': 'mainplate', 'y': 0, 'exp_resid_stress': 470.2996},
            {'flaw_direction': 'perpendicular', 'joint': 'tee', 'surface': 'stayplate', 'y': 0, 'exp_resid_stress': 643.2256},
            {'flaw_direction': 'parallel', 'joint': 'tee', 'surface': 'mainplate', 'y': 0, 'exp_resid_stress': 470.2996},
            {'flaw_direction': 'parallel', 'joint': 'tee', 'surface': 'stayplate', 'y': 0, 'exp_resid_stress': 643.2256},
            {'flaw_direction': 'perpendicular', 'joint': 'tee', 'surface': 'mainplate', 'y': t * 1.75, 'exp_resid_stress': 235.1498},
            {'flaw_direction': 'perpendicular', 'joint': 'tee', 'surface': 'stayplate', 'y': t * 1.75, 'exp_resid_stress': 321.6128},
            {'flaw_direction': 'parallel', 'joint': 'tee', 'surface': 'mainplate', 'y': t * 1.75, 'exp_resid_stress': 235.1498},
            {'flaw_direction': 'parallel', 'joint': 'tee', 'surface': 'stayplate', 'y': t * 1.75, 'exp_resid_stress': 321.6128},
            {'flaw_direction': 'perpendicular', 'joint': 'tee', 'surface': 'mainplate', 'y': t * 2, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'perpendicular', 'joint': 'tee', 'surface': 'stayplate', 'y': t * 2, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'parallel', 'joint': 'tee', 'surface': 'mainplate', 'y': t * 2, 'exp_resid_stress': 0.0},
            {'flaw_direction': 'parallel', 'joint': 'tee', 'surface': 'stayplate', 'y': t * 2, 'exp_resid_stress': 0.0}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                test_weld = FilletWeld(
                    pipe=self.pipe,
                    environment=self.environment,
                    material=self.material,
                    defect=self.defect,
                    weld_thickness=self.weld_thickness,
                    flaw_direction=case['flaw_direction'],
                    flaw_distance=case['y'],
                    joint=case['joint'],
                    surface=case['surface'])
                test_resid_stress = test_weld.calc_resid_stress(self.x)
                
                self.assertAlmostEqual(
                    test_resid_stress, case['exp_resid_stress'], places=4)

    def test_invalid_flaw_direction_in_base_class(self):
        """
        Unit test to check proper error handling if the flaw direction is invalid.
        
        Raises
        ------
        ValueError
            If the flaw direction is not recognized.
        """
        from helpr.physics.residual_stress import Weld
        from abc import ABCMeta
        # Define dummy subclass since Weld is abstract
        class DummyWeld(Weld, metaclass=ABCMeta):
            def calc_perp_resid_stress(self, x): pass
            def calc_par_resid_stress(self, x): pass
            def calc_perp_stress_attenuation(self, stress): pass
            def calc_par_stress_attenuation(self, stress): pass

        with self.assertRaises(ValueError) as context:
            DummyWeld(self.pipe, self.environment, self.material, self.defect,
                    weld_thickness=0.02, flaw_direction='invalid')
        self.assertIn('Weld flaw direction not recognized.', str(context.exception))

    def test_calc_tee_mainplate_high_x(self):
        """Unit test to check residual stress calculation for a tee joint 
           with a mainplate surface."""
        weld = FilletWeld(
            pipe=self.pipe,
            environment=self.environment,
            material=self.material,
            defect=self.defect,
            weld_thickness=self.weld_thickness,
            flaw_direction='perpendicular',
            joint='tee',
            surface='mainplate'
        )
        x = 0.03  # with t=0.1 → x/t = 0.3
        stress = weld.calc_resid_stress(x)
        self.assertIsInstance(stress, float)

    def test_calc_tee_stayplate_low_t(self):
        """Unit test to check residual stress calculation for a tee joint 
           with a stayplate surface and low wall thickness."""
        pipe = Pipe(outer_diameter=4, wall_thickness=0.005)
        weld = FilletWeld(
            pipe=pipe,
            environment=self.environment,
            material=self.material,
            defect=self.defect,
            weld_thickness=0.01,
            flaw_direction='perpendicular',
            joint='tee',
            surface='stayplate'
        )
        stress = weld.calc_resid_stress(0.001)
        self.assertIsInstance(stress, float)

    def test_calc_tee_stayplate_mid_t(self):
        """Unit test to check residual stress calculation for a tee joint 
           with a stayplate surface and medium wall thickness."""
        pipe = Pipe(outer_diameter=4, wall_thickness=0.02)
        weld = FilletWeld(
            pipe=pipe,
            environment=self.environment,
            material=self.material,
            defect=self.defect,
            weld_thickness=0.01,
            flaw_direction='perpendicular',
            joint='tee',
            surface='stayplate'
        )
        stress = weld.calc_resid_stress(0.005)
        self.assertIsInstance(stress, float)

    def test_calc_corner_setin_perp_stress_attenuation_extremes(self):
        """Unit test to check stress attenuation calculation for a corner joint 
           with a set-in surface."""
        # r/t = 1.9 / 0.5 = 3.8 → triggers l_s = 6 * t_s
        thick_pipe = Pipe(outer_diameter=4, wall_thickness=0.5)
        weld1 = FilletWeld(
            pipe=thick_pipe,
            environment=self.environment,
            material=self.material,
            defect=self.defect,
            weld_thickness=0.01,
            flaw_direction='perpendicular',
            joint='corner',
            surface='set-in'
        )
        weld1.flaw_distance = 1.0
        _ = weld1.calc_corner_setin_perp_stress_attenuation(100)

        # r/t = 1.9 / 0.01 = 190 → triggers l_s = 1.5 * t_s
        thin_pipe = Pipe(outer_diameter=4, wall_thickness=0.01)
        weld2 = FilletWeld(
            pipe=thin_pipe,
            environment=self.environment,
            material=self.material,
            defect=self.defect,
            weld_thickness=0.01,
            flaw_direction='perpendicular',
            joint='corner',
            surface='set-in'
        )
        weld2.flaw_distance = 1.0
        _ = weld2.calc_corner_setin_perp_stress_attenuation(100)

    def test_tee_mainplate_resid_stress_small_t(self):
        """Unit test to check residual stress calculation for a tee joint 
           with a mainplate surface and small wall thickness."""
        tiny_pipe = Pipe(outer_diameter=4, wall_thickness=0.006)
        weld = FilletWeld(
            pipe=tiny_pipe,
            environment=self.environment,
            material=self.material,
            defect=self.defect,
            weld_thickness=0.005,
            flaw_direction='perpendicular',
            joint='tee',
            surface='mainplate'
        )
        _ = weld.calc_resid_stress(0.001)


class AdditionalResidualStressCoverage(unittest.TestCase):
    """
    Class for additional unit tests of residual stress calculations.

    Attributes
    ----------
    pipe_005 : Pipe
        Pipe object with outer diameter 4 and wall thickness 0.05.
    pipe_002 : Pipe
        Pipe object with outer diameter 4 and wall thickness 0.02.
    pipe_001 : Pipe
        Pipe object with outer diameter 4 and wall thickness 0.01.
    environment : EnvironmentSpecification
        Environment specification object with max pressure, min pressure, temperature, and volume fraction of hydrogen.
    material : MaterialSpecification
        Material specification object with yield strength and fracture resistance.
    defect : DefectSpecification
        Defect specification object with flaw depth, flaw length, and surface.
    weld_thickness : float
        Thickness of the weld.
    x : float
        Value of x for the test case.
    """

    def setUp(self):
        """Set up the test cases with the required parameters."""
        self.pipe_005 = Pipe(outer_diameter=4, wall_thickness=0.05)  # t = 0.05
        self.pipe_002 = Pipe(outer_diameter=4, wall_thickness=0.02)  # t = 0.02 (for 1014-1015)
        self.pipe_001 = Pipe(outer_diameter=4, wall_thickness=0.01)  # t = 0.01 (for 1011-1012)

        self.environment = EnvironmentSpecification(13, 1, 300, 1)
        self.material = MaterialSpecification(670, 55)
        self.defect = DefectSpecification(10, 0.01, surface='inside')
        self.weld_thickness = 0.01
        self.x = 0.001

    def test_circumferential_weld(self):
        """Unit test to check residual stress calculation for a circumferential weld."""
        weld = CircumferentialWeld(
            pipe=self.pipe_005,  # t = 0.05 
            environment=self.environment,
            material=self.material,
            defect=self.defect,
            weld_thickness=self.weld_thickness,
            flaw_direction='parallel',
            heat_input=10000
        )
        stress = weld.calc_resid_stress(self.x)
        self.assertIsInstance(stress, float)

    def test_fillet_weld(self):
        """Unit test to check residual stress calculation for a fillet weld."""
        weld = FilletWeld(
            pipe=self.pipe_002,  # t = 0.02
            environment=self.environment,
            material=self.material,
            defect=self.defect,
            weld_thickness=self.weld_thickness,
            flaw_direction='perpendicular',
            joint='tee',
            surface='mainplate'
        )
        stress = weld.calc_resid_stress(self.x)
        self.assertIsInstance(stress, float)


if __name__ == '__main__':
    unittest.main()

