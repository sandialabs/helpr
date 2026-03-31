# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import os
import warnings as wr
import math

import xarray as xr


def open_nc_table(nc_file):
    """
    Opens a saved NetCDF file of lookup table values from
    API 579-1.

    Parameters
    ----------
    nc_file : str
        Name of the NetCDF file to load.

    Returns
    -------
    xarray.DataArray
        Loaded data array from the NetCDF file.
    """
    path = os.path.dirname(os.path.realpath(__file__))
    # go one dir higher if data dir not found (i.e. using GUI)
    data_dir = os.path.join(path, '../data')
    if not os.path.isdir(data_dir):
        data_dir = os.path.join(path, '../../data')
    nc_path = os.path.join(data_dir, nc_file)
    data = xr.load_dataset(nc_path, engine='netcdf4')
    arr = data.to_dataarray()
    res = arr.squeeze()
    return res


def calc_r_ratio(k_min, k_max, k_res=0):
    """
    Calculates the R ratio from applied stresses.
    
    Parameters
    ----------
    k_min : float
        Minimum stress intensity factor.
    k_max : float
        Maximum stress intensity factor.
    k_res : float, optional
        Residual stress intensity factor (default is 0).

    Returns
    -------
    float
        Calculated R ratio.
    """
    return (k_min + k_res) / (k_max + k_res)


class GenericStressState:
    """
    Parent Class for generic Stress State capabilities.
    
    Attributes
    ----------
    pipe_specification
    environment_specification
    material_specification
    defect_specification
    stress_intensity_method
    initial_crack_depth
    initial_crack_length
    initial_a_over_c
    percent_smys
    """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
                 stress_intensity_method=None,
                 preloaded_tables=None):
        """
        Initializes the stress state object.

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
        preloaded_tables : boolean or xarray table
            Provides preloaded API tables if already generated, defaults to None
        """
        self.pipe_specification = pipe
        self.environment_specification = environment
        self.material_specification = material
        self.defect_specification = defect
        self.stress_intensity_method = stress_intensity_method
        self.cycle_index = 0
        self.initial_crack_depth = self.calc_initial_crack_depth()
        self.initial_crack_length = self.defect_specification.flaw_length
        self.initial_a_over_c = self.initial_crack_depth / (self.initial_crack_length/2)
        self.check_initial_stress_criteria()

    def calc_stress_solution(self, crack_depth):
        """
        Calculates stress solution. 

        Parameters
        ----------
        crack_depth : float
            Crack depth in meters.

        Raises
        ------
        ValueError
            If the stress calculation is not specified for the generic stress class.
        """
        error_msg = 'Default stress calculation not specified for generic stress class'
        raise ValueError(error_msg)

    def calc_remaining_wall_thickness(self, crack_depth):
        """
        Calculates the remaining (non-cracked) pipe wall thickness. 
        
        Parameters
        ----------
        crack_depth : float
            Crack depth in meters.

        Returns
        -------
        float
            Remaining wall thickness in meters.
        """
        return self.pipe_specification.wall_thickness - crack_depth

    def calc_hoop_stress(self, remaining_thickness):
        """
        Calculates hoop stress. 

        Parameters
        ----------
        remaining_thickness : float
            Remaining wall thickness (m).

        Returns
        -------
        float
            Calculated hoop stress (MPa).
        """
        gas_pressure = self.environment_specification._get_max_pressure(self.cycle_index)
        # Using outer radius to be consistent with ASME B31.12
        return gas_pressure * self.pipe_specification.outer_diameter / (2 * remaining_thickness)

    def calc_longitudinal_stress(self, remaining_thickness):
        """
        Calculates longitudinal stress. 

        Parameters
        ----------
        remaining_thickness : float
            Remaining wall thickness (m).

        Returns
        -------
        float
            Calculated longitudinal stress (MPa).
        """
        hoop_stress = self.calc_hoop_stress(remaining_thickness)
        return hoop_stress/2

    def calc_allowable_stress(self):
        """
        Calculates the pipe's total allowable stress. 

        Returns
        -------
        float
            Total allowable stress (MPa).
        """
        yield_strength = self.material_specification.yield_strength
        location_factor = self.defect_specification.location_factor
        return yield_strength*location_factor

    def check_initial_stress_criteria(self):
        """
        Checks the initial stress state of the pipe. 

        Raises
        ------
        UserWarning
            If the stress state exceeds 72% SMYS.
        """
        allowable_stress = self.calc_allowable_stress()
        # initial stress criteria solution does not consider crack
        stress_solution = self.calc_stress_solution(crack_depth=0)
        self.percent_smys = stress_solution/allowable_stress*100
        if self.percent_smys > 72:
            wr.warn(f'Stress state {self.percent_smys:.2f} > 72% SMYS', UserWarning)

    def calc_initial_crack_depth(self):
        """
        Calculates initial crack depth. 

        Returns
        -------
        float
            Initial crack depth (m).
        """
        return (self.pipe_specification.wall_thickness
              * self.defect_specification.flaw_depth / 100)

    def calc_stress_intensity_factor(self, crack_depth, crack_length):
        """
        Calculates stress intensity factor (k). 

        Parameters
        ----------
        crack_depth : float
            Depth of the crack (m).
        crack_length : float
            Length of the crack (m).
        """

    def calc_f(self):
        """
        Calculates the current f values. 

        Returns
        -------
        float
            Current f value.
        """

    def calc_q(self, current_a_over_c):
        """
        Calculates Q variable from Equation (9B.95) in API 579-1.
        
        Parameters
        ----------
        current_a_over_c : float
            Crack depth to half-length ratio.

        Returns
        -------
        float
            Q correction factor.
        """
        if self.stress_intensity_method == 'api':
            q = (1 + 1.464 * current_a_over_c**1.65
                 if current_a_over_c <= 1.0
                 else 1 + 1.464 * (1/current_a_over_c)**1.65)
        else:
            q = 1 + 1.464 * current_a_over_c**1.65

        return q


class InternalAxialHoopStress(GenericStressState):
    """
    Stress State Class for Internal Axial Hoop Stress Cases. 
    
    Attributes
    ----------
    api_infinite_crack_G_table
    api_finite_crack_A_table
    """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
                 stress_intensity_method,
                 preloaded_tables=None):
        """
        Initialize an InternalAxialHoopStress object for evaluating internal axial hoop stress 
        using either API 579-1 or Anderson methodologies.

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
        preloaded_tables : tuple of xarray.DataArray, optional
            A tuple (G_table, A_table) of preloaded API 579-1 lookup tables. If not provided,
            tables are automatically loaded based on flaw surface.

        Raises
        ------
        ValueError
            If the stress intensity method is not valid.
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
            if preloaded_tables:
                self.api_infinite_crack_G_table = preloaded_tables[0]
                self.api_finite_crack_A_table = preloaded_tables[1]
            else:
                self.api_infinite_crack_G_table, self.api_finite_crack_A_table = \
                    self.load_api_tables(defect.surface)

        elif stress_intensity_method == 'anderson':
            self.check_anderson_solution_assumptions()

    def calc_stress_solution(self, crack_depth):
        """
        Calculates stress solution.

        Parameters
        ----------
        crack_depth : float
            Crack depth (m).
        
        Returns
        -------
        float
            Calculated stress solution (MPa).
        """
        remaining_thickness = self.calc_remaining_wall_thickness(crack_depth)
        return self.calc_hoop_stress(remaining_thickness)

    def interp_table_parameters(self, table, **table_args):
        """
        Interpolates values for the influence coefficients based on
        provided in API 579-1. The `table_args` provided should match the
        dimensions in the provided table.
        
        Parameters
        ----------
        table : xarray.DataArray
            API 579-1 lookup table.
        **table_args : dict
            Parameters used to interpolate the table.

        Returns
        -------
        float
            Interpolated value.

        Raises
        ------
        ValueError
            If input parameter dimensions are inconsistent.
        """
        return table.interp(**table_args, kwargs={'fill_value': 'extrapolate'})

    def calc_ref_stress_api(self, crack_depth):
        """
        Calculates reference stress using API 579-1 Annex 9C.5.10.

        Parameters
        ----------
        crack_depth : float
            Crack depth (m).

        Returns
        -------
        float
            Reference stress (MPa).

        Notes
        -----
        Falls back to standard stress solution if crack length or depth is zero.
        """
        p = self.environment_specification._get_max_pressure(self.cycle_index)
        a = crack_depth
        c = self.defect_specification.flaw_length / 2
        t = self.pipe_specification.wall_thickness
        r = self.pipe_specification.inner_diameter / 2

        if (a <= 0) or (c <= 0):
            print('Crack length or depth of zero found. ' +
                  'Reverting to standard stress solution calculation.')
            return self.calc_stress_solution(a)

        a_over_t = a / t
        p_m = p * r / t
        if self.defect_specification.surface == 'outside':
            p_b = -p / 2
        else:
            p_b = p / 2

        alpha = a_over_t / (1 + (t / c))
        g = 1 - 20 * (a / (2*c))**0.75 * alpha**3
        lmbda_a = 1.818 * c / math.sqrt(r * a)
        avg_area = a_over_t * (math.pi/4)

        m_t = math.sqrt(
            (1.02 + 0.4411*lmbda_a**2 + 0.006124*lmbda_a**4)
            / (1.0 + 0.02642*lmbda_a**2 + 1.533e-6*lmbda_a**4) )
        m_s = 1 / (1 - avg_area + avg_area*(1 / m_t))

        return (g * p_b
            + math.sqrt((g * p_b)**2 + 9 * (m_s * p_m * (1 - alpha)**2)**2)) \
            / (3 * (1 - alpha)**2)

    def calc_stress_intensity_factor(self,
                                     crack_depth,
                                     crack_length,
                                     cycle_index=0,
                                     phi=math.pi/2):
        """
        Calculates the stress intensity factor. For finite length
        flaws, either the Anderson analytical method
        (:python:`method='anderson'`) or the API 579-1 method
        (:python:`method='api'`) can be used.

        Parameters
        ----------
        crack_depth : float
            Crack depth (m).
        crack_length : float
            Crack length (m).
        cycle_index : int
            Index of loading profile, defaults to 0 for cases with fixed loading
        phi : float, optional
            Angle to crack tip in radians. Default is pi/2.

        Returns
        -------
        tuple
            - float: Maximum K (MPa * sqrt(m)).
            - float: Minimum K (MPa * sqrt(m)).
            - float: f-value.
            - float: q-value.

        Raises
        ------
        ValueError
            If Anderson method is used for a non-interior crack.
        """
        self.cycle_index = cycle_index

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

        k_max = min(finite_length_internal_flaw,
                    infinite_length_internal_flaw)
        k_min = k_max * (self.environment_specification._get_min_pressure(self.cycle_index)
                       / self.environment_specification._get_max_pressure(self.cycle_index))

        return (k_max,
                k_min,
                f_value,
                q_value)

    def check_anderson_solution_assumptions(self):
        """
        Checks validity of Anderson solution assumptions based on geometric limits.

        Raises
        ------
        UserWarning
            If geometry violates Anderson criteria for R_i/t or a/t.
        """
        inner_radius = self.pipe_specification.inner_diameter/2
        wall_thickness = self.pipe_specification.wall_thickness
        initial_crack_depth = self.initial_crack_depth

        r_i_over_t = inner_radius/wall_thickness

        if r_i_over_t < 5:
            wr.warn('Inner Radius / wall thickness below bounds ' +
                    f'5 <= R_i/t <= 20, R_i/t = {r_i_over_t}, violating ' +
                    'Anderson solution limits.', UserWarning)

        if r_i_over_t > 20:
            wr.warn('Inner Radius / wall thickness exceeds bounds ' +
                    f'5 <= R_i/t <= 20, R_i/t = {r_i_over_t}, violating ' +
                    'Anderson solution limits.', UserWarning)


        a_over_t = initial_crack_depth/wall_thickness
        if a_over_t > 0.8:
            wr.warn('Crack depth / wall thickness exceeds ' +
                   f'a/t = 0.8 (value = {a_over_t}), violating ' +
                    'Anderson solution limits.', UserWarning)

    def calc_k_solution_long_part_through_internal_flaw(self,
                                                        crack_depth,
                                                        crack_length):
        """
        Calculates K for long part-through internal flaws.

        Parameters
        ----------
        crack_depth : float
            Crack depth (m).
        crack_length : float
            Crack length (m).

        Returns
        -------
        tuple
            - float: K solution.
            - float: f-value.
            - float: q-value.
        """

        def calc_a(ratio_inner_radius_wall_thickness):
            """
            Computes the correction factor 'a' used in the stress intensity factor (K) solution 
            for long part-through internal flaws, based on the ratio of inner radius to wall thickness.

            Parameters
            ----------
            ratio_inner_radius_wall_thickness : float
                Ratio of pipe inner radius to wall thickness (R_i / t).

            Returns
            -------
            float
                Correction factor 'a' used in the K calculation.
            """
            length_criteria = (ratio_inner_radius_wall_thickness >= 5) &\
                  (ratio_inner_radius_wall_thickness <= 10)
            return (calc_a_small_radius_thickness_ratio(ratio_inner_radius_wall_thickness)
                    if length_criteria
                    else calc_a_large_radius_thickness_ratio(ratio_inner_radius_wall_thickness))

        def calc_a_small_radius_thickness_ratio(ratio_inner_radius_thickness):
            """
            Calculates a solutions for small radius to thickness ratios
            for long part k solutions.
            
             Parameters
            ----------
            ratio_inner_radius_thickness : float
                The ratio of inner radius to thickness.

            Returns
            -------
            float
                The calculated 'a' value for small radius to thickness ratios.
            """
            return (0.125*ratio_inner_radius_thickness - 0.25)**0.25

        def calc_a_large_radius_thickness_ratio(ratio_inner_radius_thickness):
            """
            Calculates a solutions for larger radius to thickness ratios
            for long part k solutions.
            
            Parameters
            ----------
            ratio_inner_radius_thickness : float
                The ratio of inner radius to thickness.

            Returns
            -------
            float
                The calculated 'a' value for larger radius to thickness ratios.
            """
            return (0.2*ratio_inner_radius_thickness - 1)**0.25

        def calc_f(a_value, a_over_t):
            """
            Calculates f solutions for long part k solutions. 

            Parameters
            ----------
            a_value : float
                The calculated 'a' value.
            a_over_t : float
                The ratio of crack depth to wall thickness.

            Returns
            -------
            float
                The calculated 'f' value for long part k solutions.
            """
            return 1.1 + a_value*(4.951*a_over_t**2 + 1.092*a_over_t**4)

        gas_pressure = self.environment_specification._get_max_pressure(self.cycle_index)
        inner_radius = self.pipe_specification.inner_diameter/2
        outer_radius = self.pipe_specification.outer_diameter/2
        wall_thickness = self.pipe_specification.wall_thickness
        a_value = calc_a(inner_radius/wall_thickness)
        f_value = calc_f(a_value, crack_depth/wall_thickness)
        q_value = self.calc_q(crack_depth/(crack_length/2))
        term1 = (2 * gas_pressure * outer_radius**2
              / (outer_radius**2 - inner_radius**2))
        return (term1*math.sqrt(math.pi*crack_depth)*f_value,
                f_value,
                q_value)

    def calc_k_solution_finite_length_part_through_internal_flaw(
            self,
            crack_depth,
            crack_length):
        """
        Calculates stress intensity factor for finite length
        part-through internal flaws.
        
        Parameters
        ----------
        crack_depth : float
            The depth of the crack (m).
        crack_length : float
            The length of the crack (m).

        Returns
        -------
        tuple
            A tuple containing:
            - float: The scaled pressure multiplied by the square root of (π * crack_depth / q_value) and f_value.
            - float: The f-value associated with the calculation.
            - float: The q-value associated with the calculation.
        """

        def calc_xi(crack_length, pipe_wall_thickness):
            """
            Calculates the xi parameter based on crack length and pipe wall thickness.

            Parameters
            ----------
            crack_length : float
                The length of the crack (m).
            pipe_wall_thickness : float
                The thickness of the pipe wall (m).

            Returns
            -------
            float
                The calculated xi value, which is the ratio of crack length to pipe wall thickness.
            """
            return crack_length / pipe_wall_thickness

        def calc_f(radius_thickness_ratio, xi):
            """
            Calculates current f value for finite length
            part-through internal flaws.
            
            Parameters
            ----------
            radius_thickness_ratio : float
                The ratio of the pipe's average radius to its wall thickness.
            xi : float
                The xi parameter, which is the ratio of crack length to pipe wall thickness.

            Returns
            -------
            float
                The calculated f value for finite length part-through internal flaws.
            """
            term1 = 1.12 + 0.053*xi + 0.0055*xi**2
            term2 = 1 + 0.02*xi + 0.0191*xi**2
            term3 = (20 - radius_thickness_ratio)**2/1400
            return term1 + term2*term3

        gas_pressure = self.environment_specification._get_max_pressure(self.cycle_index)
        radius_thickness_ratio = (self.pipe_specification.pipe_avg_radius
                                / self.pipe_specification.wall_thickness)

        xi = calc_xi(crack_length, self.pipe_specification.wall_thickness)
        scaled_pressure = gas_pressure*radius_thickness_ratio
        f_value = calc_f(radius_thickness_ratio, xi)
        q_value = self.calc_q(crack_depth/(crack_length/2))
        return (scaled_pressure*math.sqrt((math.pi*crack_depth)/q_value)*f_value,
                f_value,
                q_value)

    def check_api_solution_assumptions(self):
        """
        Checks that the inputs do not violate the
        API 579-1 dimensional limits
        
        Raises
        ------
        UserWarning
            If the crack depth to wall thickness ratio exceeds 0.8.
        """
        a_over_t = (self.initial_crack_depth
                  / self.pipe_specification.wall_thickness)
        if a_over_t > 0.8:
            wr.warn('Crack depth / wall thickness exceeds ' +
                   f'a/t = 0.8 (value = {a_over_t}), violating ' +
                    'API 579-1 limits.', UserWarning)

    @staticmethod
    def load_api_tables(surface):
        """
        Loads the data from the necessary lookup tables from API 579-1.
        
        Parameters
        ----------
        surface : str
            Crack surface location. Must be either 'inside' or 'outside'.

        Returns
        -------
        tuple of xarray.DataArray
            - api_infinite_crack_G_table : xarray.DataArray
                G table data for infinite surface cracks, filtered by surface.
            - api_finite_crack_A_table : xarray.DataArray
                A table data for finite surface cracks corresponding to the specified surface.

        Raises
        ------
        ValueError
            If `surface` is not 'inside' or 'outside'.
        """
        if surface == 'inside':
            filename = 'Table_9B12.nc'
        elif surface == 'outside':
            filename = 'Table_9B13.nc'
        else:
            raise ValueError('surface must be specified as inside or ' +
                             f'outside, currently {surface}')
        api_finite_crack_A_table = open_nc_table(filename)

        G_table = open_nc_table('Table_9B10.nc')
        api_infinite_crack_G_table = G_table.sel(surface=surface)

        return api_infinite_crack_G_table, api_finite_crack_A_table

    def calc_G_parameters_finite_length(self, A, Q, phi):
        """
        Calculates influence coefficients for a finite length
        surface cracks based on equations in
        API 579-1 Section 9B.5.10.
        
        Parameters
        ----------
        A : object
            The A table object used for calculations.
        Q : float
            The Q parameter used in calculations.
        phi : float
            The angle to the crack tip (rad).

        Returns
        -------
        tuple
            A tuple containing:
            - float: G0 coefficient.
            - float: G1 coefficient.
            - float: G2 coefficient.
            - float: G3 coefficient.
            - float: G4 coefficient.
        """

        def A_val(A_num, G_num):
            """
            Retrieves a scalar value from the A lookup table given specific A and G coordinates.

            Parameters
            ----------
            A_num : float or int
                The A-coordinate used to index the lookup table.
            G_num : float or int
                The G-coordinate used to index the lookup table.

            Returns
            -------
            float
                The value at the specified (A, G) location in the A table.

            Notes
            -----
            Assumes that the variable `A` is an xarray.DataArray with dimensions including 'A' and 'G'.
            """
            return float(A.sel(A=A_num, G=G_num).values)

        beta = 2*phi / math.pi

        G0 = (A_val(0,0) + A_val(1,0)*beta + A_val(2,0)*beta**2
            + A_val(3,0)*beta**3 + A_val(4,0)*beta**4 + A_val(5,0)*beta**5
            + A_val(6,0)*beta**6)
        G1 = (A_val(0,1) + A_val(1,1)*beta + A_val(2,1)*beta**2
            + A_val(3,1)*beta**3 + A_val(4,1)*beta**4 + A_val(5,1)*beta**5
            + A_val(6,1)*beta**6)

        if phi == math.pi/2:
            sqrt_2Q = math.sqrt(2*Q)
            M1 = 2 * math.pi / sqrt_2Q * (3*G1 - G0) - 24/5
            M2 = 3
            M3 = 6 * math.pi / sqrt_2Q * (G0 - 2*G1) + 8/5
            G2 = ((sqrt_2Q / math.pi)
                    * (16/15 + 1/3*M1 + 16/105*M2 + 1/12*M3))
            G3 =((sqrt_2Q / math.pi)
                * (32/35 + 1/4*M1 + 32/315*M2 + 1/20*M3))
            G4 = ((sqrt_2Q / math.pi)
                    * (256/315 + 1/5*M1 + 256/3465*M2 + 1/30*M3))
        elif phi == 0:
            sqrt_Q = math.sqrt(Q)
            pi_over_sqrt_Q = math.pi / sqrt_Q
            sqrt_Q_over_pi = sqrt_Q / math.pi
            N1 = 3*pi_over_sqrt_Q * (2*G0 - 5*G1) - 8
            N2 = 15*pi_over_sqrt_Q * (3*G1 - G0) + 15
            N3 = 3*pi_over_sqrt_Q * (3*G0 - 10*G1) - 8
            G2 = sqrt_Q_over_pi * (4/5 + 2/3*N1 + 4/7*N2 + 1/2*N3)
            G3 = sqrt_Q_over_pi * (4/7 + 1/2*N1 + 4/9*N2 + 2/5*N3)
            G4 = sqrt_Q_over_pi * (4/9 + 2/5*N1 + 4/11*N2 + 1/3*N3) 
        else:
            sqrt_Q = math.sqrt(Q)
            z = math.sin(phi)
            delta = math.sqrt(1 + z)
            omega = math.sqrt(1 - z)
            eta = math.sqrt(1/z - 1)
            M1 = ((-1050*math.pi*G1 + 105*math.pi*G0*(3+7*z)
                - 4*sqrt_Q*(35 - 70*z+35*z**2 + 189*delta*z**0.5
                                + 61*delta*z**1.5))
                / (sqrt_Q*(168 + 152*z) * z**0.5*delta))
            M2 = 1/3 * (M1 - 3)
            M3 = (2 * (-105*math.pi*G1 + 45*math.pi*G0*z + sqrt_Q
                * (28 + 24*z - 52*z**2 + 44*delta*z**1.5))
                / (sqrt_Q * (-21 + 2*z + 19*z**2) * eta))
            G2_1 = (108 + 180*z + 576*z**2 - 864*z**3
                + (1056+128*M1)*delta*z**2.5)
            G2_2 = M3 * (45*eta + 54*eta*z + 72*eta*z**2
                    - 315*omega*z**2.5 + 144*eta*z**3)
            G2 = sqrt_Q / (945*math.pi) * (G2_1 + G2_2)
            G3_1 = (880 + 1232*z + 2112*z**2 + 7040*z**3
                - 11264*z**4 + (13056+1280*M1)*delta*z**3.5)
            G3_2 = M3 * (385*eta + 440*eta*z + 528*eta*z**2
                    + 704*eta*z**3 - 3465*omega*z**3.5 + 1408*eta*z**4)
            G3 = sqrt_Q / (13860*math.pi) * (G3_1 + G3_2)
            G4_1 = (1820 + 2340*z + 3328*z**2 + 5824*z**3 + 19968*z**4
                - 33280*z**5 + (37376+3072*M1)*delta*z**4.5)
            G4_2 = M3 * (819*eta + 909*eta*z + 1040*eta*z**2
                    + 1248*eta*z**3 + 1664*eta*z**4
                    - 9009*omega*z**4.5 + 3328*eta*z**5)
            G4 = sqrt_Q / (45045*math.pi) * (G4_1 + G4_2)

        return G0, G1, G2, G3, G4

    def calc_k_solution_finite_length_part_through_flaw_api(self,
                                                            crack_depth,
                                                            crack_length,
                                                            phi=math.pi/2):
        """
        Calculates stress intensity factor for longitudinal
        direction surface cracks with semi-elliptical shape,
        internal pressure (KCSCLE1), given in Equation (9B.186) in API 579-1
        Section 9B.5.10.

        Dimensional limits:
        1. 0.0 <= a/t <= 0.8
        2. 0.03125 <= a/c <= 2.0
        3. phi <= pi/2; for pi/2 < phi <= pi, K_I(phi) = K_I(pi - phi)
        4. 0.0 <= t/inner_radius <= 1.0
        
        Parameters
        ----------
        crack_depth : float
            The depth of the crack (m).
        crack_length : float
            The length of the crack (m).
        phi : float, optional
            The angle to the crack tip (rad). Default is π/2.

        Returns
        -------
        tuple
            A tuple containing:
            - float: The calculated stress intensity factor.
            - list: A list of f-values (not used for API method).
            - float: The calculated q-value.
        """
        gas_pressure = self.environment_specification._get_max_pressure(self.cycle_index)
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
            aoc=float(crack_depth/(crack_length/2)),
            aot=float(crack_depth/self.pipe_specification.wall_thickness))

        q_value = self.calc_q(crack_depth/(crack_length/2))
        G0, G1, G2, G3, G4 = self.calc_G_parameters_finite_length(
            As, q_value, phi)

        term3 = math.sqrt(math.pi*crack_depth/q_value)

        if surface == 'inside':
            term1 = (gas_pressure*outer_radius**2
                   / (outer_radius**2 - inner_radius**2))
            term2 = (2*G0 - 2*G1*aoR
                + 3*G2*aoR**2 - 4*G3*aoR**3
                + 5*G4*aoR**4)
        else:  # surface == 'outside'
            term1 = (gas_pressure*inner_radius**2
                   / (outer_radius**2 - inner_radius**2))
            term2 = (2*G0 + 2*G1*aoR
                + 3*G2*aoR**2 + 4*G3*aoR**3
                + 5*G4*aoR**4)

        stress_intensity = term1 * term2 * term3
        f_value = math.nan
        return stress_intensity, f_value, q_value

    def calc_k_solution_long_part_through_flaw_api(self,
                                                   crack_depth,
                                                   crack_length):
        """
        Calculates stress intensity factor for longitudinal
        direction surface cracks with infinite length,
        internal pressure (KCSCLL1), given in Equation (9B.176) in API 579-1
        Section 9B.5.4.
        
        Dimensional limits:
        1. 0.0 <= a/t <= 0.8
        2. 0.0 <= t/inner_radius <= 1.0
    
        Parameters
        ----------
        crack_depth : float
            Crack depth, a (m).
        crack_length : float
            Crack length, 2c (m). Only used for q-value.

        Returns
        -------
        tuple
            - float: Calculated stress intensity factor (MPa*sqrt(m)).
            - float: f-value (unused, returns NaN).
            - float: q-value used in the calculation.
        """
        gas_pressure = self.environment_specification._get_max_pressure(self.cycle_index)
        outer_radius = self.pipe_specification.outer_diameter/2
        inner_radius = self.pipe_specification.inner_diameter/2
        # note this uses inner radius for R/t instead of average radius
        radius_thickness_ratio = (inner_radius
                                / self.pipe_specification.wall_thickness)
        surface = self.defect_specification.surface
        Gs = self.interp_table_parameters(
            self.api_infinite_crack_G_table,
            toR=1/radius_thickness_ratio,
            aot=float(crack_depth/self.pipe_specification.wall_thickness))
        G0, G1, G2, G3, G4 = Gs.values.squeeze()
        term3 = math.sqrt(math.pi * crack_depth)
        if surface == 'inside':
            crack_depth_over_inner_radius = crack_depth/inner_radius
            term1 = (gas_pressure*outer_radius**2
                   / (outer_radius**2 - inner_radius**2))
            term2 = ((2*G0 - 2*G1*crack_depth_over_inner_radius
                + 3*G2*crack_depth_over_inner_radius**2
                - 4*G3*crack_depth_over_inner_radius**3
                + 5*G4*crack_depth_over_inner_radius**4))
        else:  # surface == 'outside'
            crack_depth_over_outer_radius = crack_depth/outer_radius
            term1 = (gas_pressure*inner_radius**2
                   / (outer_radius**2 - inner_radius**2))
            term2 = ((2*G0 + 2*G1*crack_depth_over_outer_radius
                + 3*G2*crack_depth_over_outer_radius**2
                + 4*G3*crack_depth_over_outer_radius**3
                + 5*G4*crack_depth_over_outer_radius**4))

        stress_intensity = term1 * term2 * term3
        q_value = self.calc_q(crack_depth/(crack_length/2))
        f_value = math.nan
        return stress_intensity, f_value, q_value


class InternalCircumferentialLongitudinalStress(GenericStressState):
    """Stress State Class for Internal Circumferential Longitudinal Stress Cases."""

    def calc_stress_solution(self, crack_depth):
        """
        Calculates stress solution.

        Parameters
        ----------
        crack_depth : float
            Crack depth (m).
            
        Returns
        -------
        float
            The calculated longitudinal stress based on the remaining wall thickness.
        """
        remaining_thickness = self.calc_remaining_wall_thickness(crack_depth)
        return self.calc_longitudinal_stress(remaining_thickness)

    def calc_stress_intensity_factor(self,
                                     crack_depth,
                                     crack_length,
                                     cycle_index=0):
        """
        Calculates stress intensity factor.
        
        Parameters
        ----------
        crack_depth : float
            Current crack depth, a (m)

        crack_length : float
            Current crack length, 2c (m)

        cycle_index : int
            Index of loading profile, default to 0 for fix loading cases

        Returns
        -------
        tuple of float
            A 4-element tuple containing:

            - k_max : float
                Maximum stress intensity factor (MPa√m).
            - k_min : float
                Minimum stress intensity factor (MPa√m), adjusted by pressure ratio.
            - f_value : float
                The correction factor for the geometry and crack configuration.
            - q_value : float
                The q-factor accounting for the elliptical shape of the crack.

        Notes
        -----
        The SIF is calculated using a modified form of the classical elliptical 
        surface crack solution under internal pressure.
        """

        self.cycle_index = cycle_index

        radius_thickness_ratio = \
            self.pipe_specification.pipe_avg_radius/self.pipe_specification.wall_thickness
        xi = crack_length / self.pipe_specification.wall_thickness
        q_value = self.calc_q(crack_depth/(crack_length/2))
        f_value = self.calc_f(q_value, radius_thickness_ratio, xi)
        longitudinal_stress = self.calc_stress_solution(crack_depth)
        k_max = longitudinal_stress*math.sqrt((math.pi*crack_depth)/q_value)*f_value
        k_min = k_max*self.environment_specification._get_min_pressure(self.cycle_index)/\
            self.environment_specification._get_max_pressure(self.cycle_index)
        return k_max, k_min, f_value, q_value

    def calc_f(self, q_value, radius_thickness_ratio, xi):
        """
        Calculates current f value. 

        Parameters
        ----------
        q_value : float
            The calculated q-value.
        radius_thickness_ratio : float
            The ratio of the pipe's average radius to its wall thickness.
        xi : float
            The ratio of crack length to wall thickness.

        Returns
        -------
        float
            The calculated geometry correction factor 'f'.

        Notes
        -----
        This empirical equation captures the interaction between geometry, 
        crack length, and wall thickness, used to scale the longitudinal stress
        to estimate the stress intensity.
        """
        term1 = xi*(0.0103 + 0.00617*xi)
        term2 = 1 + 0.7*xi
        term3 = (radius_thickness_ratio - 5)**0.7
        return 1 + (0.02 + term1 + 0.0035*term2*term3)*q_value**2
