# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import pandas as pd
import numpy as np
from helpr import settings


class CycleEvolution:
    """Class for running fatigue evolution analysis.

    Attributes
    ----------
    pipe_specification
    stress_state
    defect_specification
    environment_specification
    material_specification
    number_of_pipe_instances
    crack_growth

    cycle_dict : dict
        Dictionary of pandas Series containing all cycle results.

    cycle : dict
        Dictionary containing data for the current cycle.

    """

    def __init__(self,
                 pipe,
                 stress_state,
                 defect,
                 environment,
                 material,
                 crack_growth_model,
                 delta_c_rule='proportional'):
        """Sets up evolution analysis model.

        Parameters
        -----------
        pipe : Pipe
            Pipe specification.
        stress_state : GenericStressState
            Stress state specification.
        defect : DefectSpecification
            Initial defect specification.
        environment : EnvironmentSpecification
            Pipe environment specification. 
        material : MaterialSpecification
            Pipe material specification.
        crack_growth_model : CrackGrowth
            Crack growth physics model. 
        delta_c_rule : str, optional
            Specify how the crack length growth (delta c) evolves.
            Valid options are:
                'proportional' : c evolves to stay proportional to crack depth (a)
                'fixed' : c remains unchanged throughout evolution
                'independent' : c evolves independently of crack depth.
                 Only valid for the api stress intensity method.
            Default option is 'proportional'

        """
        self.pipe_specification = pipe
        self.stress_state = stress_state
        self.defect_specification = defect
        self.environment_specification = environment
        self.material_specification = material
        self.number_of_pipe_instances = len(self.stress_state.initial_crack_depth)
        self.crack_growth = crack_growth_model
        if delta_c_rule in ['proportional', 'fixed', 'independent']:
            self.delta_c_rule = delta_c_rule
        else:
            raise ValueError('Crack growth delta_c_rule is invalid. Select ' +
                             "'proportional', 'fixed', or 'independent'.")

        self.cycle_dict = {}
        self.cycle = {}

    def create_clean_cycle(self):
        """Resets the cycle dictionary. """
        self.cycle = {}

    def calc_life_assessment(self, max_cycles=None, cycle_step=None):
        """Runs a fatigue crack life assessment analysis.

        Parameters
        ----------
        max_cycles : int or None, optional
            Maximum number of cycles to run the life assessment for before
            stopping. If `None`, the assessment will run until instances
            reach a/t > 0.8. Note that an assessment may
            stop before reaching `max_cycles` if all instances reach
            a/t > 0.8 before that number of cycles. Default is `None`.
        cycle_step : float or None, optional
            Number of cycles to iterate by at each evaluation step. If
            `None`, the number of cycles will be dynamically adjusted each
            iteration based on the crack growth. Default is `None`.

        Returns
        -------
        cycle_dict : dict
            Complete dict of results for all samples.

        """
        if max_cycles is None:
            max_cycles = np.inf
        self.initialize_cycle_dict()
        self.create_cycle_dict()
        self.step_through_cycles(max_cycles, cycle_step)
        return self.cycle_dict

    def initialize_cycle_dict(self):
        """Sets up initial cycle dictionary. """
        self.create_clean_cycle()
        self.cycle['a/t'] = \
            self.stress_state.initial_crack_depth/self.pipe_specification.wall_thickness
        self.cycle['a (m)'] = self.stress_state.initial_crack_depth
        self.cycle['Delta a (m)'] = np.zeros(self.number_of_pipe_instances)
        self.cycle['Delta N'] = np.zeros(self.number_of_pipe_instances)
        self.initialize_c()
        self.update_k_max_f_q()
        self.update_delta_k()
        self.cycle['Total cycles'] = np.zeros(self.number_of_pipe_instances)

    def update_c_through_delta_k(self):
        """Updates cycle values for c, eta, k_max, f, q, and delta k. """
        self.update_c()
        self.update_k_max_f_q()
        self.update_delta_k()

    def step_through_cycles(self, max_cycles, cycle_step):
        """Main loop for stepping through cycles in fatigue crack analysis"""
        analysis_complete = False
        while not analysis_complete:
            if settings.is_stopping():
                break

            self.create_clean_cycle()
            if cycle_step is None:
                self.compute_cycle_at()
            else:
                self.compute_cycle_n(cycle_step)

            self.update_cycle_dict()
            analysis_complete = self.check_stopping_criteria(max_cycles)                

    def compute_cycle_n(self, cycle_step):
        """Computes results for an explicit number of cycles. """
        self.cycle['Delta N'] = (
            np.ones(self.number_of_pipe_instances) * cycle_step)
        delta_k = self.cycle_dict['Delta K (MPa m^1/2)'].tail(1)
        delta_n = self.cycle['Delta N']
        self.cycle['Delta a (m)'] = \
            self.crack_growth.calc_change_in_crack_size(delta_n=delta_n,
                                                        delta_k=delta_k)
        self.cycle['a (m)'] = self.cycle_dict['a (m)'].values[-1] + self.cycle['Delta a (m)']
        self.cycle['a/t'] = self.cycle['a (m)'] / self.pipe_specification.wall_thickness
        self.update_c_through_delta_k()
        self.update_total_cycles()

    def compute_cycle_at(self):
        """Computes results for single a/t cycle. """
        self.update_a_over_t()
        self.update_a()
        self.update_delta_a()
        self.update_c_through_delta_k()
        self.update_delta_n()
        self.update_total_cycles()

    def update_cycle_dict(self):
        """Inserts single cycle results into overall analysis results. """
        for key, cycle in self.cycle.items():
            self.cycle_dict[key] = pd.concat([self.cycle_dict[key],
                                              pd.DataFrame(cycle).T],
                                             axis=0,
                                             ignore_index=True)

    def check_stopping_criteria(self, max_cycles):
        """Determines whether to stop life assessment based on current
        crack conditions and the maximum number of cycles.
        """
        if np.logical_or(
            self.cycle_dict['a/t'].values[-1] > 0.8,
            self.cycle_dict['Total cycles'].values[-1] > max_cycles).all():
            return True
        else:
            return False

    def create_cycle_dict(self):
        """Initialize dictionary to store full fatigue crack analysis"""
        self.cycle_dict = {}
        for key, cycle in self.cycle.items():
            self.cycle_dict[key] = pd.DataFrame(cycle).T

    def update_a_over_t(self):
        """Calculates current a/t value. """
        cycle_step_size = self.selecting_a_over_t_step_size()
        self.cycle['a/t'] = self.cycle_dict['a/t'].values[-1] + cycle_step_size

    def update_a(self):
        """Calculates current crack depth (a) value. """
        self.cycle['a (m)'] = self.cycle['a/t']*self.pipe_specification.wall_thickness

    def update_delta_a(self):
        """Calculates current delta a value. """
        self.cycle['Delta a (m)'] = self.cycle['a (m)'] - self.cycle_dict['a (m)'].values[-1]

    def selecting_a_over_t_step_size(self):
        """Adaptively calculates a/t step size. """
        if self.cycle_dict['a/t'].shape[0] > 3:
            current_step_size = \
                self.cycle_dict['a/t'].values[-1] - self.cycle_dict['a/t'].values[-2]
            change_in_a_over_t = \
                (self.cycle_dict['a/t'].values[-1]
                 - self.cycle_dict['a/t'].values[-2])/self.cycle_dict['a/t'].values[-1]
            return self.change_a_over_t_step_size(current_step_size, change_in_a_over_t)
        # TODO : What is a good default?
        default_step_size = \
            self.stress_state.initial_crack_depth/self.pipe_specification.wall_thickness*0.001
        return default_step_size
        # return 0.0005

    @staticmethod
    def change_a_over_t_step_size(current_step_size, change_in_a_over_t):
        """Calculates a/t step size. """
        # simple adaptive time stepping
        min_pct_change = 0.1  # 1%
        max_pct_change = 0.5  # 5%
        step_size_change = 0.005  # 20%
        # increase step size if change is less than minimum
        # decrease step size if change is greater than maximum
        condition_list = [change_in_a_over_t < min_pct_change, change_in_a_over_t > max_pct_change]
        outcome_list = [current_step_size*(1 + step_size_change),
                        current_step_size*(1 - step_size_change)]
        return np.select(condition_list, outcome_list, current_step_size)

    def update_total_cycles(self):
        """Calculates current cycle count. """
        self.cycle['Total cycles'] = \
            self.cycle_dict['Total cycles'].values[-1] + self.cycle['Delta N']

    def update_delta_n(self):
        """Calculates current delta n value. """
        delta_k = self.cycle['Delta K (MPa m^1/2)']
        delta_a = self.cycle['Delta a (m)']
        self.cycle['Delta N'] = self.crack_growth.calc_delta_n(delta_a=delta_a,
                                                               delta_k=delta_k)

    def initialize_c(self):
        """Initializes value of c based on initial a/c ratio in stress state module"""
        self.cycle['c (m)'] = \
            self.cycle['a (m)']/self.stress_state.initial_a_over_c

    def update_c(self):
        """Calculates current crack width (c) value. """
        if self.delta_c_rule == 'proportional':
            self.cycle['c (m)'] = \
                self.cycle['a (m)']/self.stress_state.initial_a_over_c

        if self.delta_c_rule == 'fixed':
            self.cycle['c (m)'] = self.cycle_dict['c (m)'].values[-1]

        if self.delta_c_rule == 'independent':
            k_max_surf, _, _ = self.calc_k_max_f_q(phi=0,
                                                   previous_step_values=True)
            delta_k_surf = self.calc_delta_k(k_max=k_max_surf)
            delta_c = \
                self.crack_growth.calc_change_in_crack_size(
                    delta_n=self.cycle_dict['Delta N'].values[-1],
                    delta_k=delta_k_surf)
            self.cycle['c (m)'] = self.cycle_dict['c (m)'].values[-1] + delta_c

    def update_k_max_f_q(self):
        """Updates k_max, f, and q values at current cycle. """
        self.cycle['Kmax (MPa m^1/2)'], self.cycle['F'], self.cycle['Q'] = \
            self.calc_k_max_f_q()

    def calc_k_max_f_q(self, phi=np.pi/2, previous_step_values=False):
        """Calculates k_max, f, and q values. """
        if previous_step_values:
            crack_depth = self.cycle_dict['a (m)'].values[-1]
            crack_length = self.cycle_dict['c (m)'].values[-1]*2
        else:
            crack_depth = self.cycle['a (m)']
            crack_length = self.cycle['c (m)']*2

        k_max, f, q = \
            self.stress_state.calc_stress_intensity_factor(crack_depth=crack_depth,
                                                           crack_length=crack_length,
                                                           phi=phi)
        return k_max, f, q

    def update_delta_k(self):
        """Updates delta k value at current cycle. """
        # TODO: Move R ratio to stress module to allow for additional factors impacting K
        self.cycle['Delta K (MPa m^1/2)'] = self.calc_delta_k(k_max=self.cycle['Kmax (MPa m^1/2)'])

    def calc_delta_k(self, k_max):
        """Calculates delta k value. """
        return k_max*(1 - self.environment_specification.r_ratio)
