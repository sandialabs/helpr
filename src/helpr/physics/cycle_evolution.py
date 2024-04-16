# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor as Pool
import pandas as pd
import numpy as np
import scipy.optimize as opt
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
                 crack_growth_model):
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
        
        """
        self.pipe_specification = pipe
        self.stress_state = stress_state
        self.defect_specification = defect
        self.environment_specification = environment
        self.material_specification = material
        self.number_of_pipe_instances = len(self.stress_state.initial_crack_depth)
        self.crack_growth = crack_growth_model

        if len(self.stress_state.a_crit) > 1:
            self.setup_a_crit_solve(parallel=True)
        else:
            self.setup_a_crit_solve()

        self.cycle_dict = {}
        self.cycle = {}

    def setup_a_crit_solve(self, parallel=False):
        """Sets up solving function for 'a critical' value for each sample. """
        all_instances = []
        for sample_index in range(len(self.stress_state.a_crit)):
            single_instance = {}
            single_instance['pipe'] = self.pipe_specification.get_single_pipe(sample_index)
            single_instance['stress_state'] = \
                self.stress_state.get_single_stress_state(sample_index)
            single_instance['defect'] = self.defect_specification.get_single_defect(sample_index)
            single_instance['environment'] = \
                self.environment_specification.get_single_environment(sample_index)
            single_instance['material'] = \
                self.material_specification.get_single_material(sample_index)
            single_instance['crack_growth'] = \
                self.crack_growth.get_single_crack_growth_model(sample_index)
            all_instances.append(single_instance)

        if parallel:
            n_cpu = mp.cpu_count() - 1
            if n_cpu >= len(self.stress_state.a_crit):
                n_cpu = len(self.stress_state.a_crit)

            with Pool(n_cpu) as pool:
                results = pool.map(self.solve_for_a_crit, all_instances, chunksize=4)
                optimization_results = list(results)

            # Non-parallel form for debug
            # optimizationResults = []
            # for instance in all_instances:
            #     optimizationResults.append(self.solve_for_aCrit(instance))

        else:
            optimization_results = [self.solve_for_a_crit(all_instances[0])]

        holder_a_crit = []
        holder_fracture_resistance = []
        for sample_index in range(len(self.stress_state.a_crit)):
            holder_a_crit.append(optimization_results[sample_index].stress_state.a_crit[0])
            holder_fracture_resistance.append(optimization_results[sample_index].material_specification.fracture_resistance[0])

        self.stress_state.a_crit = np.array(holder_a_crit)
        self.material_specification.fracture_resistance = np.array(holder_fracture_resistance)

    @staticmethod
    def solve_for_a_crit(single_instance):
        """Creates an individual class object to solve 'a critical' for each instance. """
        return OptimizeACrit(pipe=single_instance['pipe'],
                             stress_state=single_instance['stress_state'],
                             defect=single_instance['defect'],
                             environment=single_instance['environment'],
                             material=single_instance['material'],
                             crack_growth_model=single_instance['crack_growth'])

    def create_clean_cycle(self):
        """Resets the cycle dictionary. """
        self.cycle = {}

    def calc_life_assessment(self, step_cycles:(bool or int)=False):
        """Runs a fatigue crack life assessment analysis.

        Parameters
        ----------
        step_cycles : bool or int, optional
            Flag for evolving analysis by cycle or by a/t value, defaults to False (a/t).
            Passing an int will run the analysis the specified number of cycles.

        Returns
        -------
        cycle_dict : dict
            Complete dict of results for all samples.

        """
        self.initialize_cycle_dict()
        self.create_cycle_dict()
        self.step_through_cycles(step_cycles)
        return self.cycle_dict

    def initialize_cycle_dict(self, optimize=False):
        """Sets up initial cycle dictionary. """
        self.create_clean_cycle()
        self.cycle['a/t'] = \
            self.stress_state.initial_crack_depth/self.pipe_specification.wall_thickness
        self.cycle['a (m)'] = self.stress_state.initial_crack_depth
        self.cycle['Delta a (m)'] = np.zeros(self.number_of_pipe_instances)
        self.update_c_through_delta_k(optimize=optimize)
        self.cycle['Delta N'] = np.zeros(self.number_of_pipe_instances)
        self.cycle['Total cycles'] = np.zeros(self.number_of_pipe_instances)

    def update_c_through_delta_k(self, optimize=False):
        """Updates cycle values for c, eta, k_max, f, q, and delta k. """
        self.update_c(optimize)
        self.update_k_max_f_q(optimize)
        self.update_delta_k()

    def step_through_cycles(self, step_cycles:(bool or int)=False):
        """Main loop for stepping through cycles in fatigue crack analysis"""
        if type(step_cycles) == int:
            for _ in range(step_cycles):
                if settings.is_stopping():
                    break
                self.create_clean_cycle()
                self.compute_cycle_n()
                self.update_cycle_dict()
        else:
            while not (self.cycle_dict['a/t'].values[-1] > 1).all():
                if settings.is_stopping():
                    break
                self.create_clean_cycle()
                self.compute_cycle_at()
                self.update_cycle_dict()

    def compute_cycle_n(self):
        """Computes results for a single (n) cycle. """
        self.cycle['Delta N'] = np.ones(self.number_of_pipe_instances)
        delta_k = self.cycle_dict['Delta K (MPa m^1/2)'].tail(1)
        delta_n = self.cycle['Delta N']
        self.crack_growth.update_delta_k_delta_n(delta_k=delta_k, delta_n=delta_n)
        self.cycle['Delta a (m)'] = self.crack_growth.calc_delta_a()
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
        self.crack_growth.update_delta_k_delta_a(delta_k=delta_k, delta_a=delta_a)
        self.cycle['Delta N'] = self.crack_growth.calc_delta_n()

    def update_c(self, optimize=False):
        """Calculates current crack width (c) value. """
        if optimize:
            self.cycle['c (m)'] = \
                self.stress_state.a_crit/self.stress_state.defect_specification.a_over_c
        else:
            self.cycle['c (m)'] = \
                self.cycle['a (m)']/self.stress_state.defect_specification.a_over_c
        
    def update_k_max_f_q(self, optimize=False):
        """Calculates current k_max, f, and q values. """
        k_max, f, q = \
            self.stress_state.calc_stress_intensity_factor(crack_depth=self.cycle['a (m)'],
                                                           crack_length=2*self.cycle['c (m)'],
                                                           optimize=optimize)
        self.cycle['Kmax (MPa m^1/2)'] = k_max
        self.cycle['F'] = f
        self.cycle['Q'] = q

    def update_delta_k(self):
        """Calculates current delta k value. """
        self.cycle['Delta K (MPa m^1/2)'] = self.calc_delta_k()

    def calc_delta_k(self):
        """Calculates current delta k value. """
        # TODO: Move R ratio to stress module to allow for additional factors impacting K
        k_max = self.cycle['Kmax (MPa m^1/2)']
        r_ratio = self.environment_specification.r_ratio
        return k_max*(1 - r_ratio)


class OptimizeACrit(CycleEvolution):
    """ACrit optimization solver using a single cycle instance.

    Attributes
    ----------
    pipe
    stress_state
    defect
    environment
    material
    crack_growth_model

    """
    def setup_a_crit_solve(self, parallel=False):
        """Initializes solver for a critical value. """
        if parallel:
            a_crit_opt_error = ValueError("""Multiple aCrit values passed to Optimize_ACrit
                                           object when only one should be""")
            raise a_crit_opt_error
        self.minimize_for_a_crit()

    def minimize_for_a_crit(self):
        """Performs optimization for crit value. """
        opt.minimize(fun=self.determine_a_crit,
                     x0=self.stress_state.a_crit,
                     method='Nelder-Mead',
                     tol=1E-6,
                     options={'disp': False})

    def determine_a_crit(self, a_crit):
        """Acts as objective function for optimization of a crit. """
        # lower bound bounding due to minimize function not taking bound currently
        a_crit = max(a_crit, 0)
        self.stress_state.a_crit = a_crit
        self.initialize_cycle_dict(optimize=True)
        self.create_cycle_dict()
        return abs(self.material_specification.fracture_resistance - self.cycle['Kmax (MPa m^1/2)'])
