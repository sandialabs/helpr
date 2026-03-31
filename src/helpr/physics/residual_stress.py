# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from abc import ABC, abstractmethod
import warnings
import math

import numpy as np

from helpr.utilities.parameter import Parameter


class HeatInput(ABC):
    """
    Abstract class for calculating heat input for welding processeses
    based on different known inputs.
    """

    @abstractmethod
    def calc_heat_input(self):
        """Calculates the heat input in J/mm."""


class HeatInputFromPower(HeatInput):
    """
    Class for calculating heat input for welding processes based
    on known current, voltage, and weld travel speed.
    
    Attributes
    ----------
    current
    voltage
    speed
    """

    def __init__(self,
                 current,
                 voltage,
                 travel_speed):
        """
        Initialize the HeatInputFromPower instance.

        Parameters
        ----------
        current : float
            Current of weld electrode, in amps.
        voltage : float
            Voltage of weld electrode, in volts.
        travel_speed : float
            Travel speed of welding, in mm/s.
        """
        super().__init__()
        self.current = current
        self.voltage = voltage
        self.speed = travel_speed

    def calc_heat_input(self):
        """
        Calculate the heat input.

        Returns
        -------
        float
            The calculated heat input in J/mm.
        """
        return self.current * self.voltage / self.speed


class HeatInputFromProcess(HeatInput):
    """
    Class for calculating heat input for welding processes based
    on known type of welding process and weld material, estimating
    based on values in Table 9D.1M of API 579-1.
    
    Attributes
    ----------
    process
    weld_steel
    """

    def __init__(self,
                 process,
                 weld_steel):
        """
        Initializes a HeatInputFromProcess instance with the specified
        welding process and steel type

        Parameters
        ----------
        process : str
            Weld process used.
            Valid options are 'SMAW', 'SAW', 'GTAW', and 'GMAW'.
        weld_steel : str
            Weld steel used.
            Valid options are 'ferritic' or 'austenitic'.

        Raises
        ------
        ValueError
            If the process or weld_steel is not recognized.
        """
        super().__init__()
        if process.lower() in ['smaw', 'saw', 'gtaw', 'gmaw']:
            self.process = process.lower()
        else:
            raise ValueError('Weld process not recognized. ' +
                             "Valid options are 'SMAW', 'SAW', " +
                             "'GTAW', and 'GMAW'.")
        if weld_steel.lower() in ['ferritic', 'austenitic']:
            self.weld_steel = weld_steel.lower()
        else:
            raise ValueError('Weld steel not recognized. Valid ' +
                             "options are 'ferritic' and 'austenitic'")

    def calc_heat_input(self):
        """
        Returns a representative heat input value based on the given
        welding process and steel type.

        Returns
        -------
        float
            Heat input in J/mm, based on empirical values from
            API 579-1 Table 9D.1M.
        """
        if self.weld_steel == 'ferritic':
            if self.process == 'smaw':
                return 1130.0
            elif self.process == 'saw':
                return 1220.0
            elif self.process == 'gtaw':
                return 500.0
            elif self.process == 'gmaw':
                return 390.0
        elif self.weld_steel == 'austenitic':
            if self.process == 'smaw':
                return 940.0
            elif self.process == 'saw':
                return 1080.0
            elif self.process == 'gtaw':
                return 500.0
            elif self.process == 'gmaw':
                return 390.0


class Weld:
    """
    Parent class for types of pipe welds included in API 579-1
    residual stress calculations.

    Attributes
    ----------
    pipe_specification
    environment_specification
    material_specification
    defect_specification
    weld_thickness
    flaw_direction
    flaw_distance
    weld_yield_strength
    """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
                 weld_thickness,
                 flaw_direction,
                 flaw_distance=0,
                 weld_yield_strength=None):
        """
        Initializes a Weld object for use in residual stress calculations
        per API 579-1.

        Parameters
        ----------
        pipe : Pipe
            Pipe specification
        environment : EnvironmentSpecification
            Environment specification.
        material : MaterialSpecification
            Material specification.
        defect : DefectSpecification
            Defect specification.
        weld_thickness : float
            Weld thickness, in meters.
        flaw_direction : str
            Direction of flaw relative to the weld seam.
            Valid options are 'perpendicular' and 'parallel'.
        flaw_distance : float, optional
            Distance from the weld that the flaw is located, in meters.
            Default is zero.
        weld_yield_strength : float or None, optional
            Yield strength of the weld material, in MPa.
            If `None`, the yield strength is estimated using the
            yield strength of the base material using Equation 9D.1
            from API 579-1. Default is `None`.

        Raises
        ------
        ValueError
            If `flaw_direction` is not one of 'perpendicular' or 'parallel'.
        """
        self.pipe_specification = pipe
        self.environment_specification = environment
        self.material_specification = material
        self.defect_specification = defect
        self.weld_thickness = Parameter('weld_thickness',
                                        value=weld_thickness,
                                        lower_bound=0)
        if flaw_direction.lower() in ['perpendicular',
                                      'parallel']:
            self.flaw_direction = flaw_direction.lower()
        else:
            raise ValueError('Weld flaw direction not recognized.' +
                             "Valid options are 'parallel' and " +
                             "'perpendicular'.")
        self.flaw_distance = Parameter(
            'flaw_distance',
            value=flaw_distance,
            lower_bound=0)
        if weld_yield_strength is None:
            self.weld_yield_strength = Parameter(
                'weld_yield_strength',
                value=self.material_specification.yield_strength + 69.0,
                lower_bound=0)
        else:
            self.weld_yield_strength = Parameter(
                'weld_yield_strength',
                value=weld_yield_strength,
                lower_bound=0)

    def calc_resid_stress(self, x):
        """
        Calculates the residual stress resulting from the weld
        affecting a flaw.

        Parameters
        ----------
        x : float
            The distance through the wall to measure at, in meters.
            Relative to the side opposite of the widest weld groove
            width or last weld pass (typically the inside surface).

        Returns
        -------
        resid_stress : float
            The residual stress from the weld at the selected location,
            in MPa.

        Raises
        ------
        ValueError
            If `x` is greater than or equal to the wall thickness.
        """
        if x >= self.pipe_specification.wall_thickness:
            raise ValueError(
                '`x` must be less than the pipe wall thickness.')

        if self.flaw_direction == 'perpendicular':
            return self.calc_perp_resid_stress(x)
        elif self.flaw_direction == 'parallel':
            return self.calc_par_resid_stress(x)

    @abstractmethod
    def calc_perp_resid_stress(self, x):
        """
        Calculates the residual stress perpendicular to the weld.
        
        Parameters
        ----------
        x : float
            Distance from the inside surface of the pipe wall, in meters.

        Returns
        -------
        float
            Perpendicular residual stress in MPa.
        """

    @abstractmethod
    def calc_par_resid_stress(self, x):
        """
        Calculates the residual stress parallel to the weld.
        
        Parameters
        ----------
        x : float
            Distance from the inside surface of the pipe wall, in meters.

        Returns
        -------
        float
            Parallel residual stress in MPa.
        """

    @abstractmethod
    def calc_perp_stress_attenuation(self, stress):
        """
        Calculates the attenuation from the perpendicular residual
        stress based on the distance between the flaw and the weld.

        Parameters
        ----------
        stress : float
            Initial residual stress in MPa.

        Returns
        -------
        float
            Attenuated residual stress in MPa.
        """

    @abstractmethod
    def calc_par_stress_attenuation(self, stress):
        """
        Calculates the attenuation from the parallel residual
        stress based on the distance between the flaw and the weld.

        Parameters
        ----------
        stress : float
            Initial residual stress in MPa.

        Returns
        -------
        float
            Attenuated residual stress in MPa.
        """

    # Should this be in stress_state.py instead? It's less clunky to use
    # it from here, but is a stress state calculation in every other way
    # Also, I'm not sure whether the API residual stress calculations
    # account for the geometry factor or not. If they do not,
    # this calculation is incomplete.
    # TODO
    def calc_resid_stress_intensity_factor(self, crack_depth):
        """
        Calculates stress intensity factor (k) from the residual
        stress of the weld.

        Parameters
        ----------
        crack_depth : float
            Depth of the crack through the wall, in meters.

        Returns
        -------
        float
            Stress intensity factor in MPa√m.
        """
        stress = self.calc_resid_stress(crack_depth)
        return stress * math.sqrt(math.pi * crack_depth)


class CircumferentialWeld(Weld):
    """
    Full penetration circumferential weld for straight pipe.
    
    Attributes
    ----------
    heat_input : float
        Supplied heat input in J/mm.
    norm_heat_input : float
        Normalized heat input (J/mm per mm of wall thickness).
    """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
                 weld_thickness,
                 flaw_direction,
                 heat_input,
                 flaw_distance=0,
                 weld_yield_strength=None):
        """
        Initializes a CircumferentialWeld object used to model residual
        stress behavior in a pipe weld, based on heat input and geometry
        following API 579-1.

        Parameters
        ----------
        pipe : Pipe
            Pipe specification
        environment : EnvironmentSpecification
            Environment specification.
        material : MaterialSpecification
            Material specification.
        defect : DefectSpecification
            Defect specification.
        weld_thickness : float
            Weld thickness, in meters.
        flaw_direction : str
            Direction of weld flaw relative to the weld seam.
            Valid options are 'perpendicular' and 'parallel'.
        heat_input : float
            Heat input used to create the weld, in J/mm.
        flaw_distance : float, optional
            Distance from the flaw to the weld centerline in meters. Default is 0.
        weld_yield_strength : float or None, optional
            Yield strength of the weld material, in MPa.
            If `None`, the yield strength is estimated using the
            yield strength of the base material using Equation 9D.1
            from API 579-1. Default is `None`.
        
        Raises
        ------
        ValueError
            If `heat_input` is negative or `flaw_direction` is invalid.
        """
        if heat_input >= 0:
            self.heat_input = heat_input
        else:
            raise ValueError('Weld heat input cannot be negative.')
        self.norm_heat_input = heat_input / (pipe.wall_thickness*1000.0)
        super().__init__(pipe,
                         environment,
                         material,
                         defect,
                         weld_thickness,
                         flaw_direction,
                         flaw_distance,
                         weld_yield_strength)

    def calc_perp_resid_stress(self, x):
        """
        Calculates perpendicular residual stress at depth `x` in the wall,
        based on normalized heat input and API 579-1 residual stress models.

        Parameters
        ----------
        x : float
            Distance through the pipe wall from the inside surface, in meters.

        Returns
        -------
        float
            Attenuated perpendicular residual stress at depth `x`, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if self.norm_heat_input > 120:
            resid_stress = self.weld_yield_strength * (
                1.00 - 0.22*(x/t) - 3.06*(x/t)**2
              + 1.88*(x/t)**3)
        elif ((self.norm_heat_input > 50) and
              (self.norm_heat_input <= 120)):
            resid_stress = self.weld_yield_strength * (
                1.00 - 4.33*(x/t) + 13.53*(x/t)**2
              - 16.93*(x/t)**3 + 7.03*(x/t)**4)
        elif self.norm_heat_input < 50:
            resid_stress = self.weld_yield_strength * (
                1.00 - 6.80*(x/t) + 24.30*(x/t)**2
              - 28.68*(x/t)**3 + 11.18*(x/t)**4)
        return self.calc_perp_stress_attenuation(resid_stress)

    def calc_par_resid_stress(self, x):
        """
        Calculates parallel residual stress at depth `x` in the wall,
        based on weld thickness and pipe geometry per API 579-1.

        Parameters
        ----------
        x : float
            Distance through the pipe wall from the inside surface, in meters.

        Returns
        -------
        float
            Attenuated parallel residual stress at depth `x`, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if t <= 0.015:
            inner_resid_stress = self.weld_yield_strength
        elif t > 0.015 and t <= 0.085:
            inner_resid_stress = self.weld_yield_strength * (
                1.0 - 14.3*(t - 0.015))
        else:
            inner_resid_stress = 0.0
        resid_stress =  inner_resid_stress + (
            self.weld_yield_strength - inner_resid_stress) * (x/t)
        return self.calc_par_stress_attenuation(resid_stress)

    def calc_perp_stress_attenuation(self, stress):
        """
        Calculates attenuation of perpendicular residual stress
        based on flaw distance and pipe geometry.

        Parameters
        ----------
        stress : float
            Unattenuated residual stress, in MPa.

        Returns
        -------
        float
            Attenuated perpendicular residual stress, in MPa.
        """
        if self.flaw_distance <= self.weld_thickness:
            atten_stress = stress
        else:
            w = self.weld_thickness
            t = self.pipe_specification.wall_thickness
            r = self.pipe_specification.inner_diameter / 2
            if t <= 0.009525:
                if (self.flaw_distance > 2*w and
                    self.flaw_distance <= 4*w):
                    atten_stress = np.interp(
                        x=self.flaw_distance,
                        xp=[2*w, 4*w],
                        fp=[stress, -stress/2])
                else:
                    atten_stress = np.interp(
                        x=self.flaw_distance,
                        xp=[4*w, 4*math.sqrt(r*t)],
                        fp=[-stress/2, 0])
            else:
                atten_stress = np.interp(
                    x=self.flaw_distance,
                    xp=[2*w, 4*math.sqrt(r*t)],
                    fp=[stress, 0])
        return float(atten_stress)

    def calc_par_stress_attenuation(self, stress):
        """
        Calculates attenuation of parallel residual stress
        based on flaw distance.

        Parameters
        ----------
        stress : float
            Unattenuated residual stress, in MPa.

        Returns
        -------
        float
            Attenuated parallel residual stress, in MPa.
        """
        w = self.weld_thickness
        if self.flaw_distance <= w:
            atten_stress = stress
        elif self.flaw_distance > w:
            atten_stress = np.interp(
                x=self.flaw_distance,
                xp=[w, 1.5*w],
                fp=[stress, 0])
        return float(atten_stress)


class LongitudinalWeld(Weld):
    """Full penetration longitudinal weld for straight pipe."""

    def calc_perp_resid_stress(self, x):
        """
        Calculates the residual stress perpendicular to the weld
        at a given depth `x` through the pipe wall.

        Parameters
        ----------
        x : float
            Distance from the inside surface through the pipe wall, in meters.

        Returns
        -------
        float
            Attenuated perpendicular residual stress at depth `x`, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        resid_stress =  self.weld_yield_strength * (1.230
            - 9.269 * (x/t) + 17.641 * (x/t)**2 - 8.660 * (x/t)**3)
        return self.calc_perp_stress_attenuation(resid_stress)

    def calc_par_resid_stress(self, x):
        """
        Calculates the residual stress parallel to the weld
        at a given depth `x` through the pipe wall.

        Parameters
        ----------
        x : float
            Distance from the inside surface through the pipe wall, in meters.

        Returns
        -------
        float
            Attenuated parallel residual stress at depth `x`, in MPa.
        """
        return self.calc_par_stress_attenuation(
            self.weld_yield_strength)

    def calc_perp_stress_attenuation(self, stress):
        """
        Applies attenuation to the perpendicular residual stress based
        on the flaw's distance from the weld.

        Parameters
        ----------
        stress : float
            Initial perpendicular residual stress, in MPa.

        Returns
        -------
        float
            Attenuated perpendicular residual stress, in MPa.
        """
        w = self.weld_thickness
        if self.flaw_distance <= w:
            atten_stress = stress
        elif self.flaw_distance > w:
            atten_stress = np.interp(
                x=self.flaw_distance,
                xp=[w, 2*w],
                fp=[stress, 0])
        return float(atten_stress)

    def calc_par_stress_attenuation(self, stress):
        """
        Applies attenuation to the parallel residual stress based
        on the flaw's distance from the weld.

        Parameters
        ----------
        stress : float
            Initial parallel residual stress, in MPa.

        Returns
        -------
        float
            Attenuated parallel residual stress, in MPa.
        """
        w = self.weld_thickness
        if self.flaw_distance <= w:
            atten_stress = stress
        elif self.flaw_distance > w: 
            atten_stress = np.interp(
                x=self.flaw_distance,
                xp=[w, 1.5*w],
                fp=[stress, 0])
        return float(atten_stress)


class FilletWeld(Weld):
    """
    Full penetration fillet weld for pipe joint connections.
    
    Attributes
    ----------
    pipe_specification
    environment_specification
    material_specification
    defect_specification
    weld_thickness
    flaw_direction
    flaw_distance
    weld_yield_strength
    joint
    surface
    weld_material
    """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
                 weld_thickness,
                 flaw_direction,
                 joint,
                 surface,
                 flaw_distance=0,
                 weld_material=None,
                 weld_yield_strength=None):
        """
        Initializes a FilletWeld object with joint and surface geometry
        information, as well as optional weld material.

        Parameters
        ----------
        pipe : Pipe
            Pipe specification
        environment : EnvironmentSpecification
            Environment specification.
        material : MaterialSpecification
            Material specification.
        defect : DefectSpecification
            Defect specification.
        weld_thickness : float
            Weld thickness, in millimeters.
        flaw_direction : str
            Direction of weld flaw relative to the weld seam.
            Valid options are 'perpendicular' and 'parallel'.
        joint : str
            Joint connection the fillet weld is applied at.
            HELPR currently supports full penetration welds at corner
            joints (`'corner'`) and tee joints (`'tee'`).
        surface : str
            The surface level of the connection that the fillet weld is
            applied on. HELPR currently supports set-in nozzle welds,
            (`'set-in'`), set-on nozzle welds, (`'set-on'`),
            reinforcing pad shell welds (`'pad'`), and piping branch
            connection welds (`'branch'`) for corner joints; and main
            plate (`'mainplate'`) or stay plate (`'stayplate'`) surface
            welds for tee joints.
        flaw_distance : float, optional
            Distance from the weld center to the flaw, in meters.
            Default is 0.
        weld_material : str or None, optional
            Type of metal the weld material is made from.
            Valid options are `None`, ferritic stainless steel
            (`'ferritic'`), and austenitic stainless steel
            (`'austenitic'`). Only used if `joint = corner` and
            `surface = branch`.
            If `None` is specified under these conditions,
            ferritic weld metal is assumed.
            Default is `None`.
        weld_yield_strength : float or None, optional
            Yield strength of the weld material, in MPa.
            If `None`, the yield strength is estimated using the
            yield strength of the base material using Equation 9D.1
            from API 579-1. Default is `None`.

        Raises
        ------
        ValueError
            If joint, surface, or weld_material values are invalid.
        """
        if joint.lower() in ['corner', 'tee']:
            self.joint = joint.lower()
        else:
            raise ValueError('Joint type not recognized. ' +
                             "Valid options are 'corner' and 'tee'.")
        if self.joint == 'corner':
            if surface.lower() in ['set-in', 'set-on', 'pad', 'branch']:
                self.surface = surface.lower()
            else:
                raise ValueError('Surface type invalid for corner ' +
                                 "joint. Valid options are 'set-in', " +
                                 "'set-on', 'pad', and 'branch'.")
        elif self.joint == 'tee':
            if surface.lower() in ['mainplate', 'stayplate']:
                self.surface = surface.lower()
            else:
                raise ValueError('Surface type invalid for tee ' +
                                 'joint. Valid options are ' +
                                 "'mainplate' and 'stayplate'.")
        if weld_material is None:
            if self.surface == 'branch':
                warnings.warn(
                    'Weld material not specified for a piping branch ' +
                    'connection. Assuming ferritic stainless steel ' +
                    'weld metal.')
                self.weld_material = 'ferritic'
        else:
            if weld_material.lower() in ['ferritic', 'austenitic']:
                self.weld_material = weld_material.lower()
            else:
                raise ValueError(
                    'Weld material invalid. Valid options are ' + 
                    "'ferritic' and 'austenitic'.")

        super().__init__(pipe,
                         environment,
                         material,
                         defect,
                         weld_thickness,
                         flaw_direction,
                         flaw_distance,
                         weld_yield_strength)

    def calc_perp_resid_stress(self, x):
        """
        Calculates perpendicular residual stress at depth `x`
        based on joint and surface configuration.

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Attenuated perpendicular residual stress, in MPa.
        """
        if self.joint == 'corner':
            return self.calc_corner_perp_resid_stress(x)
        elif self.joint == 'tee':
            return self.calc_tee_perp_resid_stress(x)

    def calc_par_resid_stress(self, x):
        """
        Calculates parallel residual stress at depth `x`
        based on joint and surface configuration.

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Attenuated parallel residual stress, in MPa.
        """
        if self.joint == 'corner':
            return self.calc_corner_par_resid_stress(x)
        elif self.joint == 'tee':
            return self.calc_tee_par_resid_stress(x)

    def calc_corner_perp_resid_stress(self, x):
        """
        Calculates perpendicular residual stress for a corner joint
        using surface-specific formula.

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Raw perpendicular residual stress, in MPa.
        """
        if self.surface == 'set-in':
            resid_stress = self.calc_corner_setin_perp_resid_stress(x)
        elif self.surface == 'set-on':
            resid_stress = self. calc_corner_seton_perp_resid_stress(x)
        elif self.surface == 'pad':
            resid_stress = self.calc_corner_pad_perp_resid_stress(x)
        elif self.surface == 'branch':
            resid_stress = self.calc_corner_branch_perp_resid_stress(x)
        return self.calc_perp_stress_attenuation(resid_stress)

    def calc_tee_perp_resid_stress(self, x):
        """
        Calculates perpendicular residual stress for a tee joint
        using surface-specific formula.

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Attenuated perpendicular residual stress, in MPa.
        """
        if self.surface == 'mainplate':
            resid_stress = self.calc_tee_mainplate_resid_stress(x)
        elif self.surface == 'stayplate':
            resid_stress = self.calc_tee_stayplate_resid_stress(x)
        return self.calc_perp_stress_attenuation(resid_stress)

    def calc_corner_par_resid_stress(self, x):
        """
        Calculates parallel residual stress for a corner joint
        using surface-specific formula.

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Attenuated parallel residual stress, in MPa.
        """
        if self.surface == 'set-in':
            resid_stress = self.calc_corner_setin_par_resid_stress(x)
        elif self.surface == 'set-on':
            resid_stress = self. calc_corner_seton_par_resid_stress(x)
        elif self.surface == 'pad':
            resid_stress = self.calc_corner_pad_par_resid_stress(x)
        elif self.surface == 'branch':
            resid_stress = self.calc_corner_branch_par_resid_stress(x)
        return self.calc_par_stress_attenuation(resid_stress)

    def calc_tee_par_resid_stress(self, x):
        """
        Calculates parallel residual stress for a tee joint
        using surface-specific formula.

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Attenuated parallel residual stress, in MPa.
        """
        if self.surface == 'mainplate':
            resid_stress = self.calc_tee_mainplate_resid_stress(x)
        elif self.surface == 'stayplate':
            resid_stress = self.calc_tee_stayplate_resid_stress(x)
        return self.calc_par_stress_attenuation(resid_stress)

    def calc_corner_setin_perp_resid_stress(self, x):
        """
        Calculates residual stress perpendicular to the weld seam
        for a set-in nozzle weld at a corner joint,
        as per API 579-1 Section 9D.10.1.1(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Unattenuated residual stress, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        resid_stress = self.weld_yield_strength * (1.00
            - 16.0 * (x/t)**2 + 32.0 * (x/t)**3 - 16.0 * (x/t)**4)
        return resid_stress

    def calc_corner_seton_perp_resid_stress(self, x):
        """
        Calculates residual stress perpendicular to the weld seam
        for a set-on nozzle weld at a corner joint,
        as per API 579-1 Section 9D.10.2.1(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Unattenuated residual stress, in MPa.
        """
        return self.calc_corner_setin_perp_resid_stress(x)

    def calc_corner_pad_perp_resid_stress(self, x):
        """
        Calculate residual stress perpendicular to the weld seam
        for a reinforcing pad shell fillet weld on a corner joint,
        as per API 579-1 Section 9D.10.3.1(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Unattenuated residual stress, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if t <= .0254:
            resid_stress =self.calc_corner_setin_perp_resid_stress(x)
        else:
            resid_stress = self.calc_tee_mainplate_resid_stress(x)
        return resid_stress

    def calc_corner_branch_perp_resid_stress(self, x):
        """
        Calculate residual stress perpendicular to the weld seam
        for a piping branch connection weld on a corner joint,
        as per API 579-1 Section 9D.10.4.1(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Unattenuated residual stress, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if self.weld_material == 'ferritic':
            resid_stress = self.weld_yield_strength * (0.97
                +  2.327 * (x/t) - 24.125 * (x/t)**2
                + 42.485 * (x/t)**3 - 21.087 * (x/t)**4)
        elif self.weld_material == 'austenitic':
            resid_stress = self.weld_yield_strength
        return resid_stress

    def calc_tee_mainplate_resid_stress(self, x):
        """
        Calculate residual stress for a tee joint weld connecting
        to a main plate, as per API 579-1 Section 9D.11.1.1(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Residual stress at the specified depth, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if t <= .00635:
            resid_m = self.weld_yield_strength
            resid_o = self.weld_yield_strength
        elif t > .00635 and t <= .025:
            resid_m = self.weld_yield_strength * (1.340 - 53.6 * t)
            resid_o = self.weld_yield_strength * (1.170 - 26.8 * t)
        else:
            resid_m = 0
            resid_o = self.weld_yield_strength * 0.5
        if x/t <= 0.275:
            resid_stress = self.weld_yield_strength - 3.636 * (
                self.weld_yield_strength - resid_m) * (x/t)
        else:
            resid_stress = resid_m + (resid_o - resid_m) * (1.379
              * (x/t) - 0.379)
        return resid_stress

    def calc_tee_stayplate_resid_stress(self, x):
        """
        Calculate residual stress for a tee joint weld connecting
        to a stay plate, as per API 579-1 Section 9D.11.2.1(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Residual stress at the specified depth, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if t <= 0.00635:
            beta = 0.0
        elif t > 0.00635 and t <= 0.025:
            beta = 53.6*t - 0.340
        else:
            beta = 1.0
        resid_stress = self.weld_yield_strength * (1.00 - beta * (
            16.0 * (x/t)**2 - 32 * (x/t)**3 + 16 * (x/t)**4))
        return resid_stress

    def calc_corner_setin_par_resid_stress(self, x):
        """
        Calculate residual stress parallel to the weld seam
        for a set-in nozzle weld at a corner joint,
        as per API 579-1 Section 9D.10.1.2(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Residual stress at the specified depth, in MPa.
        """
        return self.weld_yield_strength

    def calc_corner_seton_par_resid_stress(self, x):
        """
        Calculate residual stress parallel to the weld seam
        for a set-on nozzle weld at a corner joint,
        as per API 579-1 Section 9D.10.2.2(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Residual stress at the specified depth, in MPa.
        """
        return self.calc_corner_setin_par_resid_stress(x)

    def calc_corner_pad_par_resid_stress(self, x):
        """
        Calculate residual stress parallel to the weld seam
        for a reinforcing pad shell fillet weld on a corner joint,
        as per API 579-1 Section 9D.10.3.2(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Residual stress at the specified depth, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if t <= .0254:
            resid_stress = self.calc_corner_setin_par_resid_stress(x)
        else:
            resid_stress = self.calc_tee_mainplate_resid_stress(x)
        return resid_stress

    def calc_corner_branch_par_resid_stress(self, x):
        """
        Calculate residual stress parallel to the weld seam
        for a piping branch connection weld on a corner joint,
        as per API 579-1 Section 9D.10.4.2(a).

        Parameters
        ----------
        x : float
            Distance through the pipe wall, in meters.

        Returns
        -------
        float
            Residual stress at the specified depth, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if self.weld_material == 'ferritic':
            resid_stress = self.weld_yield_strength * (1.025
                +  3.478 * (x/t) - 27.861 * (x/t)**2
                + 45.788 * (x/t)**3 - 21.799 * (x/t)**4)
        elif self.weld_material == 'austenitic':
            resid_stress = self.weld_yield_strength
        return resid_stress

    def calc_perp_stress_attenuation(self, stress):
        """
        Calculate stress attenuation perpendicular to the weld seam
        for a full penetration fillet weld.

        Parameters
        ----------
        stress : float
            Initial residual stress, in MPa.

        Returns
        -------
        float
            Attenuated residual stress, in MPa.
        """
        if self.joint == 'corner':
            if self.surface == 'pad':
                return self.calc_corner_pad_perp_stress_attenuation(
                    stress)
            else:
                return self.calc_corner_setin_perp_stress_attenuation(
                    stress)
        elif self.joint == 'tee':
            return self.calc_tee_stress_attenuation(stress)

    def calc_corner_setin_perp_stress_attenuation(self, stress):
        """
        Calculate stress attenuation perpendicular to the weld seam
        for a corner joint set-in nozzle weld,
        as per API 579-1 Section 9D.10.1.1(b).
        This same guidance is used for perpendicular stress
        attenuation for set-on and piping branch connection welds,
        as per Sections 9D.10.2.1(b) and 9D.10.4.1(b).

        Parameters
        ----------
        stress : float
            Initial residual stress, in MPa.

        Returns
        -------
        float
            Attenuated residual stress, in MPa.
        """
        t_s = self.pipe_specification.wall_thickness
        if self.flaw_distance <= t_s:
            atten_stress = stress
        else:
            r_s = self.pipe_specification.inner_diameter / 2
            if r_s / t_s <= 5:
                l_s = 6 * t_s
            elif r_s / t_s > 5 and r_s / t_s <= 100:
                l_s = t_s * (6.237 - 0.0474 * (r_s / t_s))
            else:
                l_s = 1.5 * t_s
            atten_stress = np.interp(
                x=self.flaw_distance,
                xp=[t_s, l_s],
                fp=[stress, 0])
        return float(atten_stress)

    def calc_corner_pad_perp_stress_attenuation(self, stress):
        """
        Calculate stress attenuation perpendicular to the weld seam
        for a coner joint reinforcing pad shell fillet weld,
        as per API 579-1 Section 9D.10.3.1(b).

        Parameters
        ----------
        stress : float
            Initial residual stress, in MPa.

        Returns
        -------
        float
            Attenuated residual stress, in MPa.
        """
        w = self.weld_thickness
        if self.flaw_distance <= w:
            atten_stress = stress
        else: 
            atten_stress = np.interp(
                x=self.flaw_distance,
                xp=[w, 2*w],
                fp=[stress, 0])
        return float(atten_stress)

    def calc_par_stress_attenuation(self, stress):
        """
        Calculate stress attenuation parallel to the weld seam
        for a full penetration fillet weld.
        
        Parameters
        ----------
        stress : float
            Initial residual stress, in MPa.

        Returns
        -------
        float
            Attenuated residual stress, in MPa.
        """
        if self.joint == 'corner':
            return self.calc_corner_setin_par_stress_attenuation(
                stress)
        elif self.joint == 'tee':
            return self.calc_tee_stress_attenuation(stress)

    def calc_corner_setin_par_stress_attenuation(self, stress):
        """
        Calculate stress attenuation parallel to the weld seam
        for a corner joint set-in nozzle weld,
        as per API 579-1 Section 9D.10.1.2(b).
        This same guidance is used for the parallel stress attenuation
        for all other corner joint welds given in API 579-1, as per
        Sections 9D.10.2.2(b), 9D.10.3.2(b), and 9D.10.4.2(b).

        Parameters
        ----------
        stress : float
            Initial residual stress, in MPa.

        Returns
        -------
        float
            Attenuated residual stress, in MPa.
        """
        t_s = self.pipe_specification.wall_thickness
        if self.flaw_distance <= t_s:
            atten_stress = stress
        else:
            atten_stress = np.interp(
                x=self.flaw_distance,
                xp=[t_s, 1.5*t_s],
                fp=[stress, 0])
        return float(atten_stress)

    def calc_tee_stress_attenuation(self, stress):
        """
        Calculate stress attenuation for a tee joint fillet weld,
        as per API 579-1 Sections 9D.11.1.1(b), 9D.11.1.2(b),
        9D.11.2.1(b), and 9D.11.2.2(b).

        Parameters
        ----------
        stress : float
            Initial residual stress, in MPa.

        Returns
        -------
        float
            Attenuated residual stress, in MPa.
        """
        t = self.pipe_specification.wall_thickness
        if self.flaw_distance <= 1.5*t:
            atten_stress = stress
        else:
            atten_stress = np.interp(
                x=self.flaw_distance,
                xp=[1.5*t, 2*t],
                fp=[stress, 0])
        return float(atten_stress)
