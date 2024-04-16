# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np
import xarray as xr
import os
import warnings as wr

from helpr.utilities.parameter import Parameter, divide_by_dataframe, subtract_dataframe

"""Module defining stress state information"""


class GenericStressState:
    """Parent Class for generic Stress State capabilities.
    
    Attributes
    ----------
    pipe_specification
    environment_specification
    material_specification
    defect_specification
    stress_intensity_method
    initial_crack_depth
    a_crit

    """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
                 stress_intensity_method=None,
                 sample_size=1):
        """
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
        stress_intensity_method : str
            Stress intensity factor method
        sample_size : int
            Analysis sample size, defaults to 1

        """
        self.pipe_specification = pipe
        self.environment_specification = environment
        self.material_specification = material
        self.defect_specification = defect
        self.stress_intensity_method = stress_intensity_method
        self.initial_crack_depth = self.calc_initial_crack_depth()
        self.a_crit = Parameter('a_crit_guess',
                                (self.pipe_specification.wall_thickness +
                                 self.initial_crack_depth)/2,
                                size=sample_size,
                                lower_bound=0)
        self.defect_specification.set_a_over_c(flaw_depth=self.initial_crack_depth)

        self.check_initial_stress_criteria()

    def get_single_stress_state(self, sample_index):
        """Returns single stress state instance.

        Parameters
        ----------
        sample_index : int
            Index of requested pipe instance.

        Returns
        -------
        GenericStressState
            Specification for the stress state instance.
        
        """
        single_pipe = self.pipe_specification.get_single_pipe(sample_index)
        single_environment = self.environment_specification.get_single_environment(sample_index)
        single_material = self.material_specification.get_single_material(sample_index)
        single_defect = self.defect_specification.get_single_defect(sample_index)
        return type(self)(pipe=single_pipe,
                          environment=single_environment,
                          material=single_material,
                          defect=single_defect,
                          stress_intensity_method=self.stress_intensity_method,
                          sample_size=1)

    def calc_stress_solution(self, crack_depth):
        """Calculates stress solution. """
        error_msg = 'Default stress calculation not specified for generic stress class'
        raise ValueError(error_msg)

    def calc_remaining_wall_thickness(self, crack_depth):
        """Calculates the remaining (non-cracked) pipe wall thickness. """
        return subtract_dataframe(self.pipe_specification.wall_thickness,
                                  crack_depth)

    def calc_hoop_stress(self, remaining_thickness):
        """Calculates hoop stress. """
        gas_pressure = self.environment_specification.max_pressure
        # Using outer radius to be consistent with ASME B31.12
        return divide_by_dataframe(gas_pressure*self.pipe_specification.outer_diameter,
                                   2*remaining_thickness)

    def calc_longitudinal_stress(self, remaining_thickness):
        """Calculates longitudinal stress. """
        hoop_stress = self.calc_hoop_stress(remaining_thickness)
        return hoop_stress/2

    def calc_allowable_stress(self):
        """Calculates the pipe's total allowable stress. """
        yield_strength = self.material_specification.yield_strength
        location_factor = self.defect_specification.location_factor
        return yield_strength*location_factor

    def check_initial_stress_criteria(self):
        """Checks the initial stress state of the pipe. """
        allowable_stress = self.calc_allowable_stress()
        # initial stress criteria solution does not consider crack
        stress_solution = \
            self.calc_stress_solution(crack_depth=np.zeros_like(self.initial_crack_depth))
        self.percent_smys = stress_solution/allowable_stress*100
        if (self.percent_smys > 72).any():
            exceeding_indices = stress_solution > allowable_stress
            num_exceeding_stresses = len(exceeding_indices)
            if num_exceeding_stresses == 1:
                max_smys = max(self.percent_smys)
                # print(f'{max_smys:.2f}% SMYS exceeds 72% SMYS' )
            wr.warn('Stress state exceeding 72% SMYS', UserWarning)

    def calc_initial_crack_depth(self):
        """Calculates initial crack depth. """
        return self.pipe_specification.wall_thickness*self.defect_specification.flaw_depth/100

    def determine_a(self, a_value, optimize=False):
        """Determines either the critical or current value of a. """
        if optimize:
            return self.a_crit

        return a_value

    def calc_stress_intensity_factor(self, crack_depth, crack_length, optimize=False):
        """Calculates stress intensity factor (k). """

    def calc_f(self):
        """Calculates the current f values. """

    def calc_q(self, a_over_c, optimize=False):
        """Calculates Q variable from Equation (9B.95) in API 579-1."""
        ## TODO : Q may evolve in the future, currently static
        if optimize:
            a_over_c = np.copy(self.defect_specification.a_over_c)

        if isinstance(a_over_c, float):
            a_over_c = np.array([a_over_c])

        if self.stress_intensity_method == 'API':
            q = np.zeros(len(a_over_c))
            q[a_over_c <= 1.0] = 1 + 1.464 * a_over_c[a_over_c <= 1.0]**1.65
            q[a_over_c > 1.0] = 1 + 1.464 * (1/a_over_c[a_over_c > 1.0])**1.65
        else:
            q = 1 + 1.464 * a_over_c**1.65

        return q


class InternalAxialHoopStress(GenericStressState):
    """Stress State Class for Internal Axial Hoop Stress Cases. """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
                 stress_intensity_method,
                 sample_size=1):
        """
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
        stress_intensity_method : str
            Stress intensity factor method, either Anderson or API
        sample_size : int
            Analysis sample size, defaults to 1

        """
        super().__init__(pipe=pipe,
                         environment=environment,
                         material=material,
                         defect=defect,
                         stress_intensity_method=stress_intensity_method,
                         sample_size=sample_size)

    def calc_stress_solution(self, crack_depth):
        """Calculates stress solution.

        Parameters
        ----------
        crack_depth : float
            Crack depth (m).
            
        """
        remaining_thickness = self.calc_remaining_wall_thickness(crack_depth)
        return self.calc_hoop_stress(remaining_thickness)

    def calc_stress_intensity_factor(self,
                                     crack_depth,
                                     crack_length,
                                     optimize=False,
                                     method='Anderson'):
        """Calculates the stress intensity factor. For finite length
        flaws, either the Anderson analytical method
        (:python:`method='Anderson'`) or the API 579-1 method
        (:python:`method='API'`) can be used.

        Parameters
        ----------
        crack_depth : float
            Current crack depth (m).
        crack_length : float
            Current crack length (m).
        optimize : bool, optional
            Flag for a_crit optimization.
        """
        if self.stress_intensity_method == 'Anderson':
            finite_length_internal_flaw, f_value, q_value = \
                self.calc_k_solution_finite_length_part_through_internal_flaw(crack_depth,
                                                                              crack_length,
                                                                              optimize=optimize)
            infinite_length_internal_flaw, _, _ = \
                self.calc_k_solution_long_part_through_internal_flaw(crack_depth,
                                                                     crack_length,
                                                                     optimize)
        elif self.stress_intensity_method == 'API':
            finite_length_internal_flaw, f_value, q_value = \
                self.calc_k_solution_finite_length_long_direction_internal_flaw_api(crack_depth,
                                                                                    crack_length,
                                                                                    optimize=optimize)
            infinite_length_internal_flaw, _, _ = \
                self.calc_k_solution_infinite_length_long_direction_internal_flaw_api(crack_depth,
                                                                                      crack_length,
                                                                                      optimize=optimize)
            if infinite_length_internal_flaw.ndim == finite_length_internal_flaw.ndim - 1: # TODO: is this robust?
                infinite_length_internal_flaw = infinite_length_internal_flaw[:, np.newaxis]

        return np.minimum(finite_length_internal_flaw,
                          infinite_length_internal_flaw), f_value, q_value

    def calc_k_solution_long_part_through_internal_flaw(self,
                                                        crack_depth,
                                                        crack_length,
                                                        optimize=False):
        """Calculates k solution for long part-through internal flaws. """
        def calc_a(ratio_inner_radius_wall_thickness):
            return np.where((ratio_inner_radius_wall_thickness >= 5) &
                            (ratio_inner_radius_wall_thickness <= 10),
                             calc_a_small_radius_thickness_ratio(ratio_inner_radius_wall_thickness),
                             calc_a_large_radius_thickness_ratio(ratio_inner_radius_wall_thickness))

        def calc_a_small_radius_thickness_ratio(ratio_inner_radius_thickness):
            """
            Calculates a solutions for small radius to thickness ratios
            for long part k solutions.
            """
            return (0.125*ratio_inner_radius_thickness - 0.25)**0.25

        def calc_a_large_radius_thickness_ratio(ratio_inner_radius_thickness):
            """
            Calculates a solutions for larger radius to thickness ratios
            for long part k solutions.
            """
            return (0.2*ratio_inner_radius_thickness - 1)**0.25

        def calc_f(parameter_a, a_over_t):
            """Calculates f solutions for long part k solutions. """
            return 1.1 + parameter_a*(4.951*a_over_t**2 + 1.092*a_over_t**4)

        crack_depth = self.determine_a(crack_depth, optimize=optimize)
        gas_pressure = self.environment_specification.max_pressure
        inner_radius = self.pipe_specification.inner_diameter/2
        outer_radius = self.pipe_specification.outer_diameter/2
        wall_thickness = self.pipe_specification.wall_thickness
        parameter_a = calc_a(inner_radius/wall_thickness)
        parameter_f = calc_f(parameter_a, crack_depth/wall_thickness)
        parameter_q = self.calc_q(crack_depth/(crack_length/2), optimize=optimize)
        first_term = 2*gas_pressure*outer_radius**2/(outer_radius**2 - inner_radius**2)
        return first_term*np.sqrt(np.pi*crack_depth)*parameter_f, parameter_f, parameter_q

    def calc_k_solution_finite_length_part_through_internal_flaw(self,
                                                                 crack_depth,
                                                                 crack_length,
                                                                 optimize=False):
        """Calculates stress intensity factor for finite length part-through internal flaws. """

        def calc_xi(crack_length, pipe_wall_thickness):
            return crack_length/pipe_wall_thickness

        def calc_f(radius_thickness_ratio, xi):
            """
            Calculates current f value
            for finite length part-through internal flaws.
            """
            term1 = 1.12 + 0.053*xi + 0.0055*xi**2
            term2 = 1 + 0.02*xi + 0.0191*xi**2
            term3 = (20 - radius_thickness_ratio)**2/1400
            return term1 + term2*term3

        crack_depth = self.determine_a(crack_depth, optimize=optimize)
        gas_pressure = self.environment_specification.max_pressure
        radius_thickness_ratio = \
            self.pipe_specification.pipe_avg_radius/self.pipe_specification.wall_thickness
        
        xi = calc_xi(crack_length, self.pipe_specification.wall_thickness)
        scaled_pressure = gas_pressure*radius_thickness_ratio
        f_value = calc_f(radius_thickness_ratio, xi)
        q_value = self.calc_q(crack_depth/(crack_length/2), optimize=optimize)
        return scaled_pressure*np.sqrt((np.pi*crack_depth)/q_value)*f_value, f_value, q_value


    def calc_k_solution_finite_length_long_direction_internal_flaw_api(self,
                                                                   crack_depth,
                                                                   crack_length,
                                                                   A_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/Table_9B12.nc'),
                                                                   phi=np.pi/2,
                                                                   optimize=False):
        """Calculates stress intensity factor for longitudinal
        direction surface cracks with semi-elliptical shape,
        internal pressure (KCSCLE1), given in Equation (9B.186) in API 579-1
        Section 9B.5.10.
        
        Dimensional limits:
    
        1. 0.0 <= a/t <= 0.8
        2. 0.03125 <= a/c <= 2.0
        3. phi <= pi/2; for pi/2 < phi <= pi, K_I(phi) = K_I(pi - phi)
        4. 0.0 <= t/inner_radius <= 1.0
    """

        def open_A_table(nc_file):
            """Opens a saved NetCDF file of influence coefficient values from
            API 579-1.
            """
            return xr.open_dataset(nc_file).to_array().squeeze()
        
        def calc_A_parameters(A_table, t_over_R, a_over_c, a_over_t):
            """Interpolates values for the influence coefficients based on
            Table 9B.12 provided in API 579-1. Returns a 7x2 NumPy array, with
            each row indexing A and each column indexing G.
            """
            return A_table.interp(
                toR=t_over_R,
                aoc=a_over_c,
                aot=a_over_t)

        def calc_G_parameters(A, Q, phi):
            """Calculates influence coefficients based on equations in
            API 579-1 Section 9B.5.10.
            """
            def A_val(A_num, G_num):
                return np.atleast_1d(A.sel(A=A_num, G=G_num).values.squeeze())

            beta = 2*phi / np.pi
            z = np.sin(phi)
            delta = np.sqrt(1 + z)
            omega = np.sqrt(1 - z)
            eta = np.sqrt(1/z - 1)
            G0 = (A_val(0,0) + A_val(1,0)*beta + A_val(2,0)*beta**2 + A_val(3,0)*beta**3
                  + A_val(4,0)*beta**4 + A_val(5,0)*beta**5 + A_val(6,0)*beta**6)
            G1 = (A_val(0,1) + A_val(1,1)*beta + A_val(2,1)*beta**2 + A_val(3,1)*beta**3
                  + A_val(4,1)*beta**4 + A_val(5,1)*beta**5 + A_val(6,1)*beta**6)

            if phi == np.pi/2:
                M1 = 2 * np.pi / np.sqrt(2*Q) * (3*G1 - G0) - 24/5
                M2 = 3
                M3 = 6 * np.pi / np.sqrt(2*Q) * (G0 - 2*G1) + 8/5
                G2 = ((np.sqrt(2*Q) / np.pi)
                        * (16/15 + 1/3*M1 + 16/105*M2 + 1/12*M3))
                G3 =((np.sqrt(2*Q) / np.pi)
                    * (32/35 + 1/4*M1 + 32/315*M2 + 1/20*M3))
                G4 = ((np.sqrt(2*Q) / np.pi)
                        * (256/315 + 1/5*M1 + 256/3465*M2 + 1/30*M3))
            elif phi == 0:
                N1 = 3*np.pi / np.sqrt(Q) * (2*G0 - 5*G1) - 8
                N2 = 15*np.pi / np.sqrt(Q) * (3*G1 - G0) + 15
                N3 = 3*np.pi / np.sqrt(Q) * (3*G0 - 10*G1) - 8
                G2 = (np.sqrt(Q)/np.pi) * (4/5 + 2/3*N1 + 4/7*N2 + 1/2*N3)
                G3 = (np.sqrt(Q)/np.pi) * (4/7 + 1/2*N1 + 4/9*N2 + 2/5*N3)
                G4 = (np.sqrt(Q)/np.pi) * (4/9 + 2/5*N1 + 4/11*N2 + 1/3*N3) 
            else:
                M1 = ((-1050*np.pi*G1 + 105*np.pi*G0*(3+7*z)
                     - 4*np.sqrt(Q)*(35 - 70*z+35*z**2 + 189*delta*z**0.5 + 61*delta*z**1.5))
                     / (np.sqrt(Q)*(168 + 152*z) * z**0.5*delta))
                M2 = 1/3 * (M1 - 3)
                M3 = (2 * (-105*np.pi*G1 + 45*np.pi*G0 + np.sqrt(Q)
                    * (28 + 24*z - 52*z**2 + 44*delta*z**1.5))
                    / (np.sqrt(Q)) * (-21 + 2*z + 19*z**2) * delta)
                G2_1 = (108 + 180*z + 576*z**2 - 864*z**3
                     + (1056+128*M1)*delta*z**2.5)
                G2_2 = M3 * (45*eta + 54*eta*z + 72*eta*z**2
                           - 315*omega*z**2.5 + 144*eta*z**3)
                G2 = np.sqrt(Q) / 945*np.pi * (G2_1 + G2_2)
                G3_1 = (880 + 1232*z + 2112*z**2 + 7040*z**3
                      - 11264*z**4 + (13056+1280*M1)*delta*z**3.5)
                G3_2 = M3 * (385*eta + 440*eta*z + 528*eta*z**2
                           + 704*eta*z**3 - 3465*omega*z**3.5 + 1408*eta*z**4)
                G3 = np.sqrt(Q) / (13860*np.pi) * (G3_1 + G3_2)
                G4_1 = (1820 + 2340*z + 3328*z**2 + 5824*z**3 + 19968*z**4
                      - 33280*z**5 + (37376+3072*M1)*delta*z**4.5)
                G4_2 = M3 * (819*eta + 909*eta*z + 1040*eta*z**2
                           + 1248*eta*z**3 + 1665*eta*z**4
                           - 9009*omega*z**4.5 + 3328*eta*z**5)
                G4 = np.sqrt(Q) / (45045*np.pi) * (G4_1 + G4_2)

            return G0, G1, G2, G3, G4

        crack_depth = self.determine_a(crack_depth, optimize=optimize)
        gas_pressure = self.environment_specification.max_pressure
        outer_radius = self.pipe_specification.outer_diameter/2 
        inner_radius = self.pipe_specification.inner_diameter/2
        # note this uses inner radius for R/t instead of average radius
        radius_thickness_ratio = (inner_radius / self.pipe_specification.wall_thickness)
        A_table = open_A_table(A_file)
        A = calc_A_parameters(A_table,
                              1/radius_thickness_ratio,
                              crack_depth/(crack_length/2),
                              crack_depth/self.pipe_specification.wall_thickness)
        q_value = self.calc_q(crack_depth/(crack_length/2), optimize=optimize)
        G0, G1, G2, G3, G4 = calc_G_parameters(A, q_value, phi)
        aoR = crack_depth/inner_radius

        term1 = gas_pressure*outer_radius**2/(outer_radius**2 - inner_radius**2)
        term3 = np.sqrt(np.pi*crack_depth/q_value)
        if G1.ndim > 1:
            aoR = aoR[:, np.newaxis]
            term3 = term3[:, np.newaxis]
        term2 = (2*G0 - 2*G1*aoR
                + 3*G2*aoR**2 - 4*G3*aoR**3
                + 5*G4*aoR**4)

        stress_intensity = (term1 * term2 * term3)
        f_value = np.nan # not used for API method TODO
        return stress_intensity, f_value, q_value

    def calc_k_solution_infinite_length_long_direction_internal_flaw_api(self,
                                                                   crack_depth,
                                                                   crack_length,
                                                                   G_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/Table_9B10.nc'),
                                                                   optimize=False):
        """Calculates stress intensity factor for longitudinal
        direction surface cracks with infinite length,
        internal pressure (KCSCLL1), given in Equation (9B.176) in API 579-1
        Section 9B.5.4.
        
        Dimensional limits:
    
        1. 0.0 <= a/t <= 0.8
        2. 0.0 <= t/inner_radius <= 1.0
    """
        def open_G_table(nc_file):
            """Opens a saved NetCDF file of influence coefficient values from
            API 579-1.
            """
            return xr.open_dataset(nc_file).to_array().squeeze()

        def calc_G_parameters(G_table, t_over_R, a_over_t):
            """Interpolates values for the influence coefficients based on
            Table 9B.10 provided in API 579-1. Returns a tuple of length 5,
            denoting G0, G1, G2, G3, G4 in order.
            """
            Gs = G_table.sel(surface='inside').interp(
                toR=t_over_R,
                aot=a_over_t).values.squeeze()
            G0, G1, G2, G3, G4 = np.split(Gs, 5, axis=-1)
            return G0.squeeze(), G1.squeeze(), G2.squeeze(), G3.squeeze(), G4.squeeze()

        crack_depth = self.determine_a(crack_depth, optimize=optimize)
        gas_pressure = self.environment_specification.max_pressure
        outer_radius = self.pipe_specification.outer_diameter/2 
        inner_radius = self.pipe_specification.inner_diameter/2
        # note this uses inner radius for R/t instead of average radius
        radius_thickness_ratio = (inner_radius/self.pipe_specification.wall_thickness)
        G_table = open_G_table(G_file)
        G0, G1, G2, G3, G4 = calc_G_parameters(G_table,
                              1/radius_thickness_ratio,
                              crack_depth/self.pipe_specification.wall_thickness)

        stress_intensity = (gas_pressure*outer_radius**2/(outer_radius**2 - inner_radius**2)
             * (2*G0 - 2*G1*(crack_depth/inner_radius)
                + 3*G2*(crack_depth/inner_radius)**2 - 4*G3*(crack_depth/inner_radius)**3
                + 5*G4*(crack_depth/inner_radius)**4)*np.sqrt(np.pi*crack_depth))
        f_value = np.nan # not used for API method TODO
        q_value = self.calc_q(crack_depth/(crack_length/2), optimize=optimize)
        return stress_intensity, f_value, q_value


class InternalCircumferentialLongitudinalStress(GenericStressState):
    """Stress State Class for Internal Circumferential Longitudinal Stress Cases. """

    def calc_stress_solution(self, crack_depth):
        """Calculates stress solution.

        Parameters
        ----------
        crack_depth : float
            Crack depth (m).
            
        """
        remaining_thickness = self.calc_remaining_wall_thickness(crack_depth)
        return self.calc_longitudinal_stress(remaining_thickness)

    def calc_stress_intensity_factor(self,
                                     crack_depth,
                                     crack_length,
                                     optimize=False):
        """Calculates stress intensity factor.
        
        Parameters
        ----------
        crack_depth : float
            Current crack depth (m).
        eta : float
            Current eta value.
        optimize : bool, optional
            Flag for a_crit optimization.

        """
        crack_depth = self.determine_a(crack_depth, optimize=optimize)
        radius_thickness_ratio = \
            self.pipe_specification.pipe_avg_radius/self.pipe_specification.wall_thickness
        xi = crack_length / self.pipe_specification.wall_thickness
        q_value = self.calc_q(crack_depth/(crack_length/2), optimize=optimize)
        f_value = self.calc_f(q_value, radius_thickness_ratio, xi)
        longitudinal_stress = self.calc_stress_solution(crack_depth)
        return longitudinal_stress*np.sqrt((np.pi*crack_depth)/q_value)*f_value, f_value, q_value

    def calc_f(self, q_value, radius_thickness_ratio, xi):
        """Calculates current f value. """
        term1 = xi*(0.0103 + 0.00617*xi)
        term2 = 1 + 0.7*xi
        term3 = (radius_thickness_ratio - 5)**0.7
        return 1 + (0.02 + term1 + 0.0035*term2*term3)*q_value**2
