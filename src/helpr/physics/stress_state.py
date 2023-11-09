# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np

from helpr.utilities.parameter import Parameter, divide_by_dataframe, subtract_dataframe

"""Module defining stress state information. """


class GenericStressState:
    """Parent Class for generic Stress State capabilities.
    
    Attributes
    ----------
    pipe_specification
    environment_specification
    material_specification
    defect_specification
    a_crit

    """

    def __init__(self,
                 pipe,
                 environment,
                 material,
                 defect,
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
        sample_size : int
            Analysis sample size, defaults to 1

        """
        self.pipe_specification = pipe
        self.environment_specification = environment
        self.material_specification = material
        self.defect_specification = defect
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
        return divide_by_dataframe(gas_pressure*self.pipe_specification.pipe_avg_radius,
                                   remaining_thickness)

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
        if (stress_solution > allowable_stress).any():
            exceeding_indices = stress_solution > allowable_stress
            print(f'stress solutions {stress_solution[exceeding_indices]} > ' +
                  f'allowable stresses {allowable_stress[exceeding_indices]}')
            raise ValueError('Instance of stress solution exceeded allowable stress')

    def calc_initial_crack_depth(self):
        """Calculates initial crack depth. """
        return self.pipe_specification.wall_thickness*self.defect_specification.flaw_depth/100

    def determine_a(self, a_value, optimize=False):
        """Determines either the critical or current value of a. """
        if optimize:
            return self.a_crit

        return a_value

    def calc_stress_intensity_factor(self, crack_depth, eta, optimize=False):
        """Calculates stress intensity factor (k). """

    def calc_f(self, radius_thickness_ratio, eta):
        """Calculates the current q values. """

    def calc_q(self):
        """Calculates the current q values. """
        # TODO: Q may evolve in the future, currently static
        return 1 + 1.464*self.defect_specification.a_over_c**1.65


class InternalAxialHoopStress(GenericStressState):
    """Stress State Class for Internal Axial Hoop Stress Cases. """

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
                                     eta,
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
        finite_length_internal_flaw, f_value, q_value = \
            self.calc_k_solution_finite_length_part_through_internal_flaw(crack_depth,
                                                                          eta,
                                                                          optimize)
        infinite_length_internal_flaw, _, _ = \
            self.calc_k_solution_long_part_through_internal_flaw(crack_depth,
                                                                 optimize)
        return np.minimum(finite_length_internal_flaw,
                          infinite_length_internal_flaw), f_value, q_value

    def calc_k_solution_long_part_through_internal_flaw(self,
                                                        crack_depth,
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
        first_term = 2*gas_pressure*outer_radius**2/(outer_radius**2 - inner_radius**2)
        return first_term*np.sqrt(np.pi*crack_depth)*parameter_f, parameter_f, self.calc_q()

    def calc_k_solution_finite_length_part_through_internal_flaw(self,
                                                                 crack_depth,
                                                                 eta,
                                                                 optimize=False):
        """Calculates stress intensity factor for finite length part-through internal flaws. """

        def calc_f(radius_thickness_ratio, eta):
            """
            Calculates current f value
            for finite length part-through internal flaws.
            """
            term1 = 1.12 + 0.053*eta + 0.0055*eta**2
            term2 = 1 + 0.02*eta + 0.0191*eta**2
            term3 = (20 - radius_thickness_ratio)**2/1400
            return term1 + term2*term3

        crack_depth = self.determine_a(crack_depth, optimize=optimize)
        gas_pressure = self.environment_specification.max_pressure
        radius_thickness_ratio = \
            self.pipe_specification.pipe_avg_radius/self.pipe_specification.wall_thickness
        scaled_pressure = gas_pressure*radius_thickness_ratio
        f_value = calc_f(radius_thickness_ratio, eta)
        q_value = self.calc_q()
        return scaled_pressure*np.sqrt((np.pi*crack_depth)/q_value)*f_value, f_value, q_value


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
                                     eta,
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
        f_value = self.calc_f(radius_thickness_ratio, eta)
        q_value = self.calc_q()
        longitudinal_stress = self.calc_stress_solution(crack_depth)
        return longitudinal_stress*np.sqrt((np.pi*crack_depth)/q_value)*f_value, f_value, q_value

    def calc_f(self, radius_thickness_ratio, eta):
        """Calculates current f value. """
        q_value = self.calc_q()
        term1 = eta*(0.0103 + 0.00617*eta)
        term2 = 1 + 0.7*eta
        term3 = (radius_thickness_ratio - 5)**0.7
        return 1 + (0.02 + term1 + 0.0035*term2*term3)*q_value**2
