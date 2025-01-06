# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import os
import warnings as wr
import numpy as np
import xarray as xr

from helpr.utilities.parameter import divide_by_dataframe, subtract_dataframe


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

    """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
                 stress_intensity_method=None):
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

        """
        self.pipe_specification = pipe
        self.environment_specification = environment
        self.material_specification = material
        self.defect_specification = defect
        self.stress_intensity_method = stress_intensity_method
        self.initial_crack_depth = self.calc_initial_crack_depth()
        self.initial_a_over_c = self.initial_crack_depth / (self.defect_specification.flaw_length/2)
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
        single_pipe = \
            self.pipe_specification.get_single_pipe(sample_index)
        single_environment = \
            self.environment_specification.get_single_environment(sample_index)
        single_material = \
            self.material_specification.get_single_material(sample_index)
        single_defect = \
            self.defect_specification.get_single_defect(sample_index)
        return type(self)(pipe=single_pipe,
                          environment=single_environment,
                          material=single_material,
                          defect=single_defect,
                          stress_intensity_method=self.stress_intensity_method)

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
        return divide_by_dataframe(
            gas_pressure * self.pipe_specification.outer_diameter,
            2 * remaining_thickness)

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
            self.calc_stress_solution(
                crack_depth=np.zeros_like(self.initial_crack_depth))
        self.percent_smys = stress_solution/allowable_stress*100
        if (self.percent_smys > 72).any():
            #exceeding_indices = stress_solution > allowable_stress
            #num_exceeding_stresses = len(exceeding_indices)
            #if num_exceeding_stresses == 1:
            #    max_smys = max(self.percent_smys)
            wr.warn('Stress state exceeding 72% SMYS', UserWarning)

    def calc_initial_crack_depth(self):
        """Calculates initial crack depth. """
        return (self.pipe_specification.wall_thickness
              * self.defect_specification.flaw_depth / 100)

    def calc_stress_intensity_factor(self, crack_depth, crack_length):
        """Calculates stress intensity factor (k). """

    def calc_f(self):
        """Calculates the current f values. """

    def calc_q(self, current_a_over_c):
        """Calculates Q variable from Equation (9B.95) in API 579-1."""

        if isinstance(current_a_over_c, float):
            current_a_over_c = np.array([current_a_over_c])

        if self.stress_intensity_method == 'api':
            q = np.zeros(np.size(current_a_over_c))
            q[current_a_over_c <= 1.0] = 1 + 1.464 * current_a_over_c[current_a_over_c <= 1.0]**1.65
            q[current_a_over_c > 1.0] = 1 + 1.464 * (1/current_a_over_c[current_a_over_c > 1.0])**1.65
        else:
            q = 1 + 1.464 * current_a_over_c**1.65

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
            Stress intensity factor method, either anderson or api
        sample_size : int
            Analysis sample size, defaults to 1

        """
        if stress_intensity_method.lower() not in ['anderson', 'api']:
            raise ValueError(
                "stress_intensity_method must be specified as 'anderson' " +
               f"or 'api', currently is {stress_intensity_method}")
        super().__init__(
            pipe=pipe,
            environment=environment,
            material=material,
            defect=defect,
            stress_intensity_method=stress_intensity_method.lower())

        if self.stress_intensity_method == 'api':
            self.check_api_solution_assumptions()
            self.load_api_tables()
        elif stress_intensity_method == 'anderson':
            self.check_anderson_solution_assumptions()

    def calc_stress_solution(self, crack_depth):
        """Calculates stress solution.

        Parameters
        ----------
        crack_depth : float
            Crack depth (m).
        """
        remaining_thickness = self.calc_remaining_wall_thickness(crack_depth)
        return self.calc_hoop_stress(remaining_thickness)

    def open_nc_table(self, nc_file):
        """Opens a saved NetCDF file of lookup table values from
        API 579-1.
        """
        data = xr.load_dataset(nc_file, engine='netcdf4')
        arr = data.to_dataarray()
        res = arr.squeeze()
        return res

    def interp_table_parameters(self, table, **table_args):
        """Interpolates values for the influence coefficients based on
        provided in API 579-1. The `table_args` provided should match the
        dimensions in the provided table.
        """
        input_len = np.array(
            [np.size(arg) for arg in table_args.values()])
        max_len = np.max(input_len)
        if np.count_nonzero(input_len > 1) <= 1:
            return table.interp(
                **table_args,
                kwargs={'fill_value': 'extrapolate'})
        elif np.isin(input_len, [1, max_len]).all():
            for key, val in table_args.items():
                table_args[key] = (
                    'param', np.repeat(val, max_len/np.size(val)))
            return table.interp(
                **table_args,
                kwargs={'fill_value': None})
        else:
            raise ValueError(
                'Inconsistent vector lengths of crack properties')

    def calc_ref_stress_api(self, crack_depth):
        """Calculates the reference stress as per the API 579-1 methodology
        included in Annex 9C.5.10, using the net section collapse criteria.
        """
        p = self.environment_specification.max_pressure
        a = crack_depth
        c = self.defect_specification.flaw_length / 2
        t = self.pipe_specification.wall_thickness
        r = self.pipe_specification.inner_diameter / 2

        if (np.any(a <= 0)) or (np.any(c <= 0)):
            print('Crack length or depth of zero found. ' +
                  'Reverting to standard stress solution calculation.')
            return self.calc_stress_solution(a)

        a_over_t = a / t
        p_m = p * r / t
        p_b = p / 2
        alpha = a_over_t / (1 + (t / c))
        g = 1 - 20 * (a / (2*c))**0.75 * alpha**3
        lmbda = 1.818 * c / np.sqrt(r * t)
        lmbda_a = 1.818 * c / np.sqrt(r * a)
        avg_area = a_over_t * (np.pi/4)

        m_t = np.sqrt(
            1.02 + 0.4411*lmbda**2 + 0.006124*lmbda**4
            / 1.0 + 0.02642*lmbda**2 + 1.533e-6*lmbda**4)
        m_s = 1 / (1 - avg_area + avg_area*(1 / (m_t*lmbda_a)))

        return (g * p_b
            + np.sqrt((g * p_b)**2 + 9 * (m_s * p_m * (1-alpha)**2)**2)
            / (3 * (1 - alpha)**2))

    def calc_stress_intensity_factor(self,
                                     crack_depth,
                                     crack_length,
                                     phi=np.pi/2):
        """Calculates the stress intensity factor. For finite length
        flaws, either the Anderson analytical method
        (:python:`method='anderson'`) or the API 579-1 method
        (:python:`method='api'`) can be used.

        Parameters
        ----------
        crack_depth : float
            Current crack depth (m).
        crack_length : float
            Current crack length (m).
        phi : float, optional
            Angle to crack tip (rad). Only used for API finite length solution.
        """
        if self.stress_intensity_method == 'anderson':
            if self.defect_specification.surface != 'inside':
                raise ValueError(
                    'Anderson stress intensity method is only valid for ' +
                    'interior cracks. Set ' +
                    "InternalAxialHoopStress.stress_intensity_method to 'api'")
            finite_length_internal_flaw, f_value, q_value = \
                self.calc_k_solution_finite_length_part_through_internal_flaw(
                    crack_depth,
                    crack_length)
            infinite_length_internal_flaw, _, _ = \
                self.calc_k_solution_long_part_through_internal_flaw(
                    crack_depth,
                    crack_length)

        if self.stress_intensity_method == 'api':
            finite_length_internal_flaw, f_value, q_value = \
                self.calc_k_solution_finite_length_part_through_flaw_api(
                    crack_depth,
                    crack_length,
                    phi=phi)
            infinite_length_internal_flaw, _, _ = \
                self.calc_k_solution_long_part_through_flaw_api(
                    crack_depth,
                    crack_length)

            # TODO: is this robust?
            if (infinite_length_internal_flaw.ndim ==
                finite_length_internal_flaw.ndim - 1):
                infinite_length_internal_flaw = (
                    infinite_length_internal_flaw[:, np.newaxis])

        return (np.minimum(finite_length_internal_flaw,
                           infinite_length_internal_flaw),
                f_value,
                q_value)

    def check_anderson_solution_assumptions(self):
        """Checks that the inputs do not violate the
        Anderson solution dimensional limits
        """
        inner_radius = self.pipe_specification.inner_diameter/2
        wall_thickness = self.pipe_specification.wall_thickness
        initial_crack_depth = self.initial_crack_depth

        r_i_over_t = inner_radius/wall_thickness
        if np.any(5 > r_i_over_t):
            wr.warn('Inner Radius / wall thickness below bounds ' +
                    f'5 <= R_i/t <= 20, min R_i/t = {r_i_over_t.min()}, violating ' +
                    'Anderson solution limits.', UserWarning)

        if np.any(r_i_over_t > 20):
            wr.warn('Inner Radius / wall thickness exceeds bounds ' +
                    f'5 <= R_i/t <= 20, max R_i/t = {r_i_over_t.max()}, violating ' +
                    'Anderson solution limits.', UserWarning)


        a_over_t = initial_crack_depth/wall_thickness
        if np.any(a_over_t > 0.8):
            wr.warn('Crack depth / wall thickness exceeds ' +
                   f'a/t = 0.8 (max value = {a_over_t.max()}), violating ' +
                    'Anderson solution limits.', UserWarning)

    def calc_k_solution_long_part_through_internal_flaw(self,
                                                        crack_depth,
                                                        crack_length):
        """Calculates k solution for long part-through internal flaws."""
        def calc_a(ratio_inner_radius_wall_thickness):
            return np.where(
                (ratio_inner_radius_wall_thickness >= 5) &
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

        def calc_f(a_value, a_over_t):
            """Calculates f solutions for long part k solutions. """
            return 1.1 + a_value*(4.951*a_over_t**2 + 1.092*a_over_t**4)

        gas_pressure = self.environment_specification.max_pressure
        inner_radius = self.pipe_specification.inner_diameter/2
        outer_radius = self.pipe_specification.outer_diameter/2
        wall_thickness = self.pipe_specification.wall_thickness
        a_value = calc_a(inner_radius/wall_thickness)
        f_value = calc_f(a_value, crack_depth/wall_thickness)
        q_value = self.calc_q(crack_depth/(crack_length/2))
        term1 = (2 * gas_pressure * outer_radius**2
              / (outer_radius**2 - inner_radius**2))
        return (term1*np.sqrt(np.pi*crack_depth)*f_value,
                f_value,
                q_value)

    def calc_k_solution_finite_length_part_through_internal_flaw(
            self,
            crack_depth,
            crack_length):
        """Calculates stress intensity factor for finite length
        part-through internal flaws.
        """

        def calc_xi(crack_length, pipe_wall_thickness):
            return crack_length / pipe_wall_thickness

        def calc_f(radius_thickness_ratio, xi):
            """Calculates current f value for finite length
            part-through internal flaws.
            """
            term1 = 1.12 + 0.053*xi + 0.0055*xi**2
            term2 = 1 + 0.02*xi + 0.0191*xi**2
            term3 = (20 - radius_thickness_ratio)**2/1400
            return term1 + term2*term3

        gas_pressure = self.environment_specification.max_pressure
        radius_thickness_ratio = (self.pipe_specification.pipe_avg_radius
                                / self.pipe_specification.wall_thickness)

        xi = calc_xi(crack_length, self.pipe_specification.wall_thickness)
        scaled_pressure = gas_pressure*radius_thickness_ratio
        f_value = calc_f(radius_thickness_ratio, xi)
        q_value = self.calc_q(crack_depth/(crack_length/2))
        return (scaled_pressure*np.sqrt((np.pi*crack_depth)/q_value)*f_value,
                f_value,
                q_value)

    def check_api_solution_assumptions(self):
        """Checks that the inputs do not violate the
        API 579-1 dimensional limits
        """
        a_over_t = (self.initial_crack_depth
                  / self.pipe_specification.wall_thickness)
        if np.any(a_over_t > 0.8):
            wr.warn('Crack depth / wall thickness exceeds ' +
                   f'a/t = 0.8 (max value = {a_over_t.max()}), violating ' +
                    'API 579-1 limits.', UserWarning)
            
    def load_api_tables(self):
        """Loads the data from the necessary lookup tables from API 579-1."""
        surface = self.defect_specification.surface

        file_dir = os.path.dirname(os.path.realpath(__file__))
        # go one dir higher if data dir not found (i.e. using GUI)
        data_dir = os.path.join(file_dir, '../data')
        if not os.path.isdir(data_dir):
            data_dir = os.path.join(file_dir, '../../data')

        G_file = os.path.join(data_dir, 'Table_9B10.nc')
        G_table = self.open_nc_table(G_file)
        self.api_infinite_crack_G_table = G_table.sel(surface=surface)

        if surface == 'inside':
            filename = 'Table_9B12.nc'
        elif surface == 'outside':
            filename = 'Table_9B13.nc'
        else:
            raise ValueError('surface must be specified as inside or ' +
                             f'outside, currently {surface}')
        datafile = os.path.join(data_dir, filename)
        self.api_finite_crack_A_table = self.open_nc_table(datafile)

    def calc_G_parameters_finite_length(self, A, Q, phi):
        """Calculates influence coefficients for a finite length
        surface cracks based on equations in
        API 579-1 Section 9B.5.10.
        """
        def A_val(A_num, G_num):
            return np.atleast_1d(A.sel(A=A_num, G=G_num).values.squeeze())

        beta = 2*phi / np.pi
        G0 = (A_val(0,0) + A_val(1,0)*beta + A_val(2,0)*beta**2
            + A_val(3,0)*beta**3 + A_val(4,0)*beta**4 + A_val(5,0)*beta**5
            + A_val(6,0)*beta**6)
        G1 = (A_val(0,1) + A_val(1,1)*beta + A_val(2,1)*beta**2
            + A_val(3,1)*beta**3 + A_val(4,1)*beta**4 + A_val(5,1)*beta**5
            + A_val(6,1)*beta**6)

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
            z = np.sin(phi)
            delta = np.sqrt(1 + z)
            omega = np.sqrt(1 - z)
            eta = np.sqrt(1/z - 1)
            M1 = ((-1050*np.pi*G1 + 105*np.pi*G0*(3+7*z)
                - 4*np.sqrt(Q)*(35 - 70*z+35*z**2 + 189*delta*z**0.5
                                + 61*delta*z**1.5))
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

    def calc_k_solution_finite_length_part_through_flaw_api(self,
                                                            crack_depth,
                                                            crack_length,
                                                            phi=np.pi/2):
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
        gas_pressure = self.environment_specification.max_pressure
        outer_radius = self.pipe_specification.outer_diameter/2
        inner_radius = self.pipe_specification.inner_diameter/2
        # note this uses inner radius for R/t instead of average radius
        radius_thickness_ratio = (
            inner_radius / self.pipe_specification.wall_thickness)
        surface = self.defect_specification.surface
        if surface == 'inside':
            aoR = crack_depth / inner_radius
        elif surface == 'outside':
            aoR = crack_depth / outer_radius

        As = self.interp_table_parameters(
            self.api_finite_crack_A_table,
            toR=1/radius_thickness_ratio,
            aoc=crack_depth/(crack_length/2),
            aot=crack_depth/self.pipe_specification.wall_thickness)
        q_value = self.calc_q(crack_depth/(crack_length/2))
        G0, G1, G2, G3, G4 = self.calc_G_parameters_finite_length(
            As, q_value, phi)

        term3 = np.sqrt(np.pi*crack_depth/q_value)
        if G1.ndim > 1:
            aoR = aoR[:, np.newaxis]
            term3 = term3[:, np.newaxis]

        if surface == 'inside':
            term1 = (gas_pressure*outer_radius**2
                   / (outer_radius**2 - inner_radius**2))
            term2 = (2*G0 - 2*G1*aoR
                + 3*G2*aoR**2 - 4*G3*aoR**3
                + 5*G4*aoR**4)
        elif surface == 'outside':
            term1 = (gas_pressure*inner_radius**2
                   / (outer_radius**2 - inner_radius**2))
            term2 = (2*G0 + 2*G1*aoR
                + 3*G2*aoR**2 + 4*G3*aoR**3
                + 5*G4*aoR**4)

        stress_intensity = (term1 * term2 * term3)
        f_value = [np.nan]*len(q_value) # not used for API method TODO
        return stress_intensity, f_value, q_value

    def calc_k_solution_long_part_through_flaw_api(self,
                                                   crack_depth,
                                                   crack_length):
        """Calculates stress intensity factor for longitudinal
        direction surface cracks with infinite length,
        internal pressure (KCSCLL1), given in Equation (9B.176) in API 579-1
        Section 9B.5.4.
        
        Dimensional limits:
    
        1. 0.0 <= a/t <= 0.8
        2. 0.0 <= t/inner_radius <= 1.0
    """
        def split_G_parameters(Gs):
            Gs = Gs.values.squeeze()
            if Gs.ndim == 1:
                return Gs
            else:
                return np.column_stack(Gs)

        gas_pressure = self.environment_specification.max_pressure
        outer_radius = self.pipe_specification.outer_diameter/2 
        inner_radius = self.pipe_specification.inner_diameter/2
        # note this uses inner radius for R/t instead of average radius
        radius_thickness_ratio = (inner_radius
                                / self.pipe_specification.wall_thickness)
        surface = self.defect_specification.surface
        Gs = self.interp_table_parameters(
            self.api_infinite_crack_G_table,
            toR=1/radius_thickness_ratio,
            aot=crack_depth/self.pipe_specification.wall_thickness)
        G0, G1, G2, G3, G4 = split_G_parameters(Gs)
        term3 = np.sqrt(np.pi * crack_depth)
        if surface == 'inside':
            term1 = (gas_pressure*outer_radius**2
                   / (outer_radius**2 - inner_radius**2))
            term2 = ((2*G0 - 2*G1*(crack_depth/inner_radius)
                + 3*G2*(crack_depth/inner_radius)**2
                - 4*G3*(crack_depth/inner_radius)**3
                + 5*G4*(crack_depth/inner_radius)**4))
        elif surface == 'outside':
            term1 = (gas_pressure*inner_radius**2
                   / (outer_radius**2 - inner_radius**2))
            term2 = ((2*G0 + 2*G1*(crack_depth/outer_radius)
                + 3*G2*(crack_depth/outer_radius)**2
                + 4*G3*(crack_depth/outer_radius)**3
                + 5*G4*(crack_depth/outer_radius)**4))

        stress_intensity = term1 * term2 * term3
        q_value = self.calc_q(crack_depth/(crack_length/2))
        f_value = [np.nan]*len(q_value) # not used for API method
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
                                     crack_length):
        """Calculates stress intensity factor.
        
        Parameters
        ----------
        crack_depth : float
            Current crack depth, a (m).
        crack_length : float
            Current crack length, 2c (m)

        """
        radius_thickness_ratio = \
            self.pipe_specification.pipe_avg_radius/self.pipe_specification.wall_thickness
        xi = crack_length / self.pipe_specification.wall_thickness
        q_value = self.calc_q(crack_depth/(crack_length/2))
        f_value = self.calc_f(q_value, radius_thickness_ratio, xi)
        longitudinal_stress = self.calc_stress_solution(crack_depth)
        return longitudinal_stress*np.sqrt((np.pi*crack_depth)/q_value)*f_value, f_value, q_value

    def calc_f(self, q_value, radius_thickness_ratio, xi):
        """Calculates current f value. """
        term1 = xi*(0.0103 + 0.00617*xi)
        term2 = 1 + 0.7*xi
        term3 = (radius_thickness_ratio - 5)**0.7
        return 1 + (0.02 + term1 + 0.0035*term2*term3)*q_value**2
