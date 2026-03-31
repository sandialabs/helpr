"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import math

from helpr import settings
from helpr.physics.residual_stress import Weld


class LifeAssessment:
    """
    Class for running fatigue evolution analysis for a single sample.

    Attributes
    ----------
    pipe_specification
    stress_state
    crack_growth
    delta_c_rule
    other_stress_state
    cycle_dict
    cycle
    """

    def __init__(self,
                 pipe_specification,
                 stress_state,
                 crack_growth,
                 delta_c_rule,
                 other_stress_state=None):
        """
        Initialize the LifeAssessment object.

        Parameters
        ==========
        pipe_specification : Pipe
            Single sample Pipe object 
        stress_state : StressState
            Single sample StressState object
        crack_growth : CrackGrowth
            Single sample CrackGrowth object
        delta_c_rule : str
            Specify how the crack length growth (delta c) evolves.
            Valid options are:
                'proportional' : c evolves to stay proportional to crack depth (a)
                'fixed' : c remains unchanged throughout evolution
                'independent' : c evolves independently of crack depth.
                 Only valid for the api stress intensity method.
            Default option is 'proportional'
        other_stress_state : float or Weld or None, optional
            Single sample float or Weld object.
            If a float, it is assumed to be a stress intensity factor
            for an additional stress (e.g. a residual stress) to be
            considered in the life assessment.
            If a Weld object, the residual stress intensity factor is
            calculated based on the weld properties.
            Only needed if non-primary stresses are to be considered in
            the life assessment, otherwise set to None.
            Default is None.
        """

        self.pipe_specification = pipe_specification
        self.stress_state = stress_state
        self.crack_growth = crack_growth
        self.delta_c_rule = delta_c_rule
        self.cycle = {} # Single cycle results
        self.cycle_dict = {} # Overall results, combination of all cycles

        if delta_c_rule in ['proportional', 'fixed', 'independent']:
            self.delta_c_rule = delta_c_rule
        else:
            raise ValueError('Crack growth delta_c_rule is invalid. Select ' +
                             "'proportional', 'fixed', or 'independent'.")

        if ((isinstance(other_stress_state, (float, Weld))) or
            (other_stress_state is None)):
            self.other_stress_state = other_stress_state
        else:
            raise TypeError('other_stress_state must be of type ' +
                            'float, Weld, or None.')

    def create_clean_cycle(self):
        """Resets the cycle dictionary."""
        self.cycle = {}

    def create_cycle_dict(self):
        """Initialize dictionary to store full fatigue crack analysis as lists"""
        for key, cycle in self.cycle.items():
            self.cycle_dict[key] = [cycle]

    def calc_life_assessment(self, max_cycles, cycle_step):
        """
        Runs a fatigue crack life assessment analysis.

        Parameters
        ----------
        max_cycles : int or None
            Maximum number of cycles to run the life assessment for before
            stopping. If `None`, the assessment will run until instances
            reach a/t > 0.8. Note that an assessment may
            stop before reaching `max_cycles` if all instances reach
            a/t > 0.8 before that number of cycles. Default is `None`.
        cycle_step : float or None
            Number of cycles to iterate by at each evaluation step. If
            `None`, the number of cycles will be dynamically adjusted each
            iteration based on the crack growth. Default is `None`.

        Returns
        -------
        cycle_dict : dict
            Complete dict of results for all samples (lists).
        """
        self.initial_cycle()
        self.create_cycle_dict()
        self.step_through_cycles(max_cycles, cycle_step)
        return self.cycle_dict

    def initial_cycle(self):
        """Sets up initial cycle dictionary."""
        self.create_clean_cycle()
        self.cycle_dict['Total cycles'] = [0]
        self.cycle['a/t'] = \
            (self.stress_state.initial_crack_depth /
             self.pipe_specification.wall_thickness)
        self.cycle['a (m)'] = self.stress_state.initial_crack_depth
        self.cycle['Delta a (m)'] = 0
        self.cycle['Delta N'] = 0
        self.initialize_c()
        self.update_k_values_f_q()
        self.update_r_ratio()
        self.update_delta_k()
        self.cycle['Total cycles'] = 0

    def update_c_through_delta_k(self):
        """Updates cycle values for c, eta, k_max, k_res, f, q, and delta k."""
        self.update_c()
        self.update_k_values_f_q()
        self.update_r_ratio()
        self.update_delta_k()

    def step_through_cycles(self, max_cycles, cycle_step):
        """
        Loop through fatigue cycles until failure or max_cycles is reached.

        Parameters
        ----------
        max_cycles : int
            Maximum number of allowable load cycles.
        cycle_step : float or None
            Number of cycles per step, or None for adaptive stepping.
        """
        analysis_complete = False

        if cycle_step is None:
            deferential_type = lambda: self.compute_cycle_at()
        else:
            deferential_type = lambda: self.compute_cycle_n(cycle_step)

        while not analysis_complete:
            if settings.is_stopping():
                break

            self.create_clean_cycle()
            deferential_type()
            self.update_cycle_dict()
            analysis_complete = self.check_stopping_criteria(max_cycles)

    def compute_cycle_n(self, cycle_step):
        """Computes results for an explicit number of cycles."""
        self.cycle['Delta N'] = cycle_step
        delta_k = self.cycle_dict['Delta K (MPa m^1/2)'][-1]
        delta_n = self.cycle['Delta N']
        r_ratio = self.cycle_dict['R ratio'][-1]
        self.cycle['Delta a (m)'] = \
            self.crack_growth.calc_change_in_crack_size(delta_n=delta_n,
                                                        delta_k=delta_k,
                                                        r_ratio=r_ratio,
                                                        cycle_index=cycle_step)
        self.cycle['a (m)'] = self.cycle_dict['a (m)'][-1] + self.cycle['Delta a (m)']
        self.cycle['a/t'] = self.cycle['a (m)'] / self.pipe_specification.wall_thickness
        self.update_c_through_delta_k()
        self.update_total_cycles()

    def compute_cycle_at(self):
        """Computes results for single a/t cycle."""
        self.update_a_over_t()
        self.update_a()
        self.update_delta_a()
        self.update_c_through_delta_k()
        self.update_delta_n()
        self.update_total_cycles()

    def update_cycle_dict(self):
        """Inserts single cycle results into overall analysis results."""
        for key, cycle in self.cycle.items():
            self.cycle_dict[key].append(cycle)

    def check_stopping_criteria(self, max_cycles):
        """
        Determines whether to stop life assessment based on current
        crack conditions and the maximum number of cycles.
        
        Parameters
        ----------
        max_cycles : int
            Max number of cycles allowed.

        Returns
        -------
        bool
            True if assessment should stop, otherwise False.
        """
        condition_a_t = self.cycle_dict['a/t'][-1] > 0.8
        condition_total_cycles = self.cycle_dict['Total cycles'][-1] > max_cycles
        return condition_a_t or condition_total_cycles

    def update_a_over_t(self):
        """Calculates current a/t value."""
        cycle_step_size = self.selecting_a_over_t_step_size()
        self.cycle['a/t'] = self.cycle_dict['a/t'][-1] + cycle_step_size

    def update_a(self):
        """Calculates current crack depth (a) value."""
        self.cycle['a (m)'] = self.cycle['a/t']*self.pipe_specification.wall_thickness

    def update_delta_a(self):
        """Calculates current delta a value."""
        self.cycle['Delta a (m)'] = self.cycle['a (m)'] - self.cycle_dict['a (m)'][-1]

    def selecting_a_over_t_step_size(self):
        """
        Adaptively calculates a/t step size.

        Returns
        -------
        float
            Suggested increment in a/t.
        """
        # Check if there are enough data points to calculate the step size
        if len(self.cycle_dict['a/t']) > 3:
            current_step_size = \
                self.cycle_dict['a/t'][-1] - self.cycle_dict['a/t'][-2]
            change_in_a_over_t = \
                (self.cycle_dict['a/t'][-1]
                 - self.cycle_dict['a/t'][-2])/self.cycle_dict['a/t'][-1]

            return self.change_a_over_t_step_size(current_step_size, change_in_a_over_t)

        # Default step size calculation
        default_step_size = \
            (self.stress_state.initial_crack_depth /
             self.pipe_specification.wall_thickness*0.001)
        return default_step_size

    @staticmethod
    def change_a_over_t_step_size(current_step_size, change_in_a_over_t):
        """
        Calculates a/t step size.

        Parameters
        ----------
        current_step_size : float
            Current step size.
        change_in_a_over_t : float
            Change in a/t since the previous cycle.

        Returns
        -------
        float
            Adjusted step size for a/t.
        """
        # simple adaptive time stepping
        min_pct_change = 0.1  # 10%
        max_pct_change = 0.5  # 50%
        step_size_change = 0.005  # 0.5%

        # Determine the new step size based on the change in a/t
        if change_in_a_over_t < min_pct_change:
            return current_step_size * (1 + step_size_change)  # Increase step size
        elif change_in_a_over_t > max_pct_change:
            return current_step_size * (1 - step_size_change)  # Decrease step size

        return current_step_size  # No change

    def update_total_cycles(self):
        """Calculates current cycle count."""
        self.cycle['Total cycles'] = \
            self.cycle_dict['Total cycles'][-1] + self.cycle['Delta N']

    def update_delta_n(self):
        """Calculates current delta n value."""
        delta_k = self.cycle['Delta K (MPa m^1/2)']
        delta_a = self.cycle['Delta a (m)']
        r_ratio = self.cycle['R ratio']
        self.cycle['Delta N'] = self.crack_growth.calc_delta_n(delta_a=delta_a,
                                                               delta_k=delta_k,
                                                               r_ratio=r_ratio)

    def initialize_c(self):
        """Initializes value of c based on initial a/c ratio in stress state module"""
        self.cycle['c (m)'] = \
            self.cycle['a (m)']/self.stress_state.initial_a_over_c

    def update_c(self):
        """Calculates current crack width (c) value."""
        if self.delta_c_rule == 'proportional':
            self.cycle['c (m)'] = \
                self.cycle['a (m)']/self.stress_state.initial_a_over_c

        if self.delta_c_rule == 'fixed':
            self.cycle['c (m)'] = self.cycle_dict['c (m)'][-1]

        if self.delta_c_rule == 'independent':
            k_max_surf, k_min_surf, k_res_surf, _, _ = \
                self.calc_k_max_f_q(phi=0, previous_step_values=True)
            r_ratio_surf = (k_min_surf + k_res_surf)/(k_max_surf + k_res_surf)
            delta_k_surf = self.calc_delta_k(k_max=k_max_surf,
                                             r_ratio=r_ratio_surf,
                                             k_res=k_res_surf)
            delta_c = \
                self.crack_growth.calc_change_in_crack_size(
                    delta_n=self.cycle_dict['Delta N'][-1],
                    delta_k=delta_k_surf,
                    r_ratio=r_ratio_surf,
                    cycle_index=self.cycle_dict['Total cycles'][-1])
            self.cycle['c (m)'] = self.cycle_dict['c (m)'][-1] + delta_c

    def update_k_values_f_q(self):
        """Updates k_max, k_min, k_res, f, and q values at current cycle."""
        (self.cycle['Kmax (MPa m^1/2)'],
         self.cycle['Kmin (MPa m^1/2)'],
         self.cycle['Kres (MPa m^1/2)'],
         self.cycle['F'],
         self.cycle['Q']) = \
            self.calc_k_max_f_q()

    def calc_k_max_f_q(self, phi=math.pi/2, previous_step_values=False):
        """
        Calculates k_max, f, and q values.

        Parameters
        ----------
        phi : float, optional
            Angle for SIF calculation. Default is π/2.
        previous_step_values : bool, optional
            If True, use values from previous cycle.

        Returns
        -------
        tuple
            K_max, K_min, K_res, F, and Q values.
        """
        if previous_step_values:
            crack_depth = self.cycle_dict['a (m)'][-1]
            crack_length = self.cycle_dict['c (m)'][-1]*2
        else:
            crack_depth = self.cycle['a (m)']
            crack_length = self.cycle['c (m)']*2

        k_max, k_min, f, q = self.stress_state.calc_stress_intensity_factor(
            crack_depth=crack_depth,
            crack_length=crack_length,
            cycle_index=self.cycle_dict['Total cycles'][-1],
            phi=phi)

        if (self.other_stress_state is None): # or (phi != math.pi/2):
            k_res = 0

        else:
            if isinstance(self.other_stress_state, float):
                k_res = self.other_stress_state
            elif isinstance(self.other_stress_state, Weld):
                k_res = self.other_stress_state.calc_resid_stress_intensity_factor(
                    crack_depth)

        return k_max, k_min, k_res, f, q

    def update_r_ratio(self):
        """Updates r_ratio value at current cycle."""
        self.cycle['R ratio'] = \
            ( (self.cycle['Kmin (MPa m^1/2)'] + self.cycle['Kres (MPa m^1/2)']) /
              (self.cycle['Kmax (MPa m^1/2)'] + self.cycle['Kres (MPa m^1/2)']) )

    def update_delta_k(self):
        """Updates delta k value at current cycle."""
        self.cycle['Delta K (MPa m^1/2)'] = self.calc_delta_k(
            k_max=self.cycle['Kmax (MPa m^1/2)'],
            k_res=self.cycle['Kres (MPa m^1/2)'],
            r_ratio=self.cycle['R ratio'])

    def calc_delta_k(self, k_max, k_res, r_ratio):
        """
        Calculates delta k value.

        Parameters
        ----------
        k_max : float
            Maximum stress intensity factor.
        k_res : float
            Residual stress intensity factor.
        r_ratio : float
            R ratio = K_min / K_max (adjusted).

        Returns
        -------
        float
            ΔK value for the cycle.
        """
        return (k_max + k_res)*(1 - r_ratio)
