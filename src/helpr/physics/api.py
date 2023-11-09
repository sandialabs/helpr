# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from datetime import datetime
import pathlib as pl
import random as rd
import string as st
import numpy as np
import pandas as pd

from probabilistic.capabilities import sampling as Sampling

from helpr import settings
from helpr.settings import Status
from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.environment import EnvironmentSpecification
from helpr.physics.material import MaterialSpecification
from helpr.physics.stress_state import InternalAxialHoopStress
from helpr.physics.cycle_evolution import CycleEvolution
from helpr.physics.crack_growth import CrackGrowth, get_design_curve
from helpr.physics.inspection_mitigation import InspectionMitigation
from helpr.utilities.postprocessing import (calc_pipe_life_criteria,
                                            report_single_pipe_life_criteria_results,
                                            report_single_cycle_evolution,
                                            calculate_failure_assessment)
from helpr.utilities.plots import (generate_pipe_life_assessment_plot,
                                   plot_det_design_curve,
                                   generate_crack_growth_rate_plot,
                                   plot_failure_assessment_diagram,
                                   plot_pipe_life_ensemble,
                                   plot_cycle_life_criteria_scatter,
                                   plot_cycle_life_pdfs,
                                   plot_cycle_life_cdfs,
                                   plot_mitigation_histograms,
                                   plot_unscaled_mitigation_cdf)


class CrackEvolutionAnalysis:
    """Class to hold API capability for carrying out pipeline fracture and fatigue analyses.
    
    Attributes
    ----------
    crack_growth_model
    step_cycles
    nominal_input_parameter_values
    sampling_input_parameter_values
    number_of_aleatory_samples
    number_of_epistemic_samples
    sample_type
    uncertain_parameters
    random_seed

    nominal_load_cycling : dict
        Results from crack growth analysis for a deterministic (single) pipe instance.
    
    nominal_life_criteria : dict
        Life criteria results for a deterministic (single) pipe instance.

    nominal_stress_state : GenericStressState
        Deterministic stress state specification.

    load_cycling : dict
        Results from crack growth analysis for all samples in a probabilistic study.

    life_criteria : dict
        Life criteria results for all samples in a probabilistic study.

    stress_state : GenericStressState
        Probabilistic stress state specification.

    ex_rates_plot : str or None
        Filepath to generated rate plot.

    crack_growth_plot : str or None
        Filepath to generated crack growth plot.

    failure_assessment_plot : str or None
        Filepath to generated failure assessment plot.

    """

    def __init__(self,
                 outer_diameter,
                 wall_thickness,
                 flaw_depth,
                 max_pressure,
                 min_pressure,
                 temperature,
                 volume_fraction_h2,
                 yield_strength,
                 fracture_resistance,
                 flaw_length,
                 crack_growth_model=None,
                 aleatory_samples=0,
                 epistemic_samples=0,
                 sample_type='deterministic',
                 random_seed=None,
                 step_cycles=False):
        """Initializes analysis object.

        Parameters
        -----------
        outer_diameter : DeterministicCharacterization or UncertaintyCharacterization
            Pipe outer diameter specification.
        wall_thickness : DeterministicCharacterization or UncertaintyCharacterization
            Pipe wall thickness specification.
        flaw_depth : DeterministicCharacterization or UncertaintyCharacterization
            Initial flaw depth specification.
        max_pressure : DeterministicCharacterization or UncertaintyCharacterization
            Maximum pipe pressure specification.
        min_pressure : DeterministicCharacterization or UncertaintyCharacterization
            Minimum pipe pressure specification.
        temperature : DeterministicCharacterization or UncertaintyCharacterization
            Pipe temperature specification.
        volume_fraction_h2 : DeterministicCharacterization or UncertaintyCharacterization
            H2 volume fraction specification.
        yield_strength : DeterministicCharacterization or UncertaintyCharacterization
            Pipe yield strength specification.
        fracture_resistance : DeterministicCharacterization or UncertaintyCharacterization
            Pipe fracture resistance specification.
        flaw_length : DeterministicCharacterization or UncertaintyCharacterization
            Initial flaw length specification.
        crack_growth_model : CrackGrowth, optional
            Specific crack growth model. Defaults to None.
        aleatory_samples : int, optional
            Number of aleatory samples. Defaults to 0.
        epistemic_samples : int, optional
            Number of epistemic samples. Defaults to 0.
        sample_type : str, optional
            Defaults to 'deterministic'.
        random_seed : float, optional
            Random seed used to initialize probabilistic analysis elements. Defaults to None.
        step_cycles : int or bool, optional
            Number of cycles of evolve crack(s). 
            Defaults to (bool) False indicating crack evaluation by a/t values.

        """

        if crack_growth_model is None:
            crack_growth_model = {'model_name': 'code_case_2938'}

        self.input_parameters = {'outer_diameter': outer_diameter,
                                 'wall_thickness': wall_thickness,
                                 'flaw_depth': flaw_depth,
                                 'max_pressure': max_pressure,
                                 'min_pressure': min_pressure,
                                 'temperature': temperature,
                                 'volume_fraction_h2': volume_fraction_h2,
                                 'yield_strength': yield_strength,
                                 'fracture_resistance': fracture_resistance,
                                 'flaw_length': flaw_length}

        self.crack_growth_model = crack_growth_model
        self.step_cycles = step_cycles
        self.load_cycling = None
        self.nominal_load_cycling = None
        self.life_criteria = None
        self.nominal_life_criteria = None
        self.stress_state = None
        self.nominal_stress_state = None

        self.nominal_input_parameter_values = {}
        self.sampling_input_parameter_values = {}

        self.number_of_aleatory_samples = aleatory_samples
        self.number_of_epistemic_samples = epistemic_samples
        self.sample_type = sample_type
        self.uncertain_parameters = []

        self.check_parameter_names()
        self.random_seed = self.gen_random_seed(random_seed)
        self.set_random_state()

        self.ex_rates_plot = None
        self.crack_growth_plot = None
        self.failure_assessment_plot = None

    def check_parameter_names(self):
        """Function to ensure parameter object names match assigned parameter. """
        for parameter_name, parameter_object in self.input_parameters.items():
            if parameter_name != parameter_object.name:
                raise ValueError(f"Parameter assigned to {parameter_name} has incorrect name")

    def perform_study(self):
        """Starts crack evolution analysis study. """
        if self.sample_type == 'deterministic':
            self.perform_deterministic_study()

        else:
            self.perform_probabilistic_study()

    def gen_random_seed(self, random_seed):
        """Sets random seed for recreating. """
        result = int(''.join(rd.choices(st.digits, k=10))) if random_seed is None else random_seed
        return result

    def get_random_seed(self):
        """Returns the random seed value. """
        return self.random_seed

    def set_random_state(self):
        """Sets up the random state. """
        self.random_state = np.random.default_rng(seed=self.random_seed)

    def perform_deterministic_study(self):
        """Performs a deterministic analysis. """
        study = self.specify_study(self.input_parameters,
                                   self.number_of_aleatory_samples,
                                   self.number_of_epistemic_samples,
                                   self.sample_type,
                                   self.random_state)
        self.nominal_input_parameter_values = study.create_variable_nominal_sheet()
        nominal_analysis_modules = \
            self.setup_crack_growth_analysis(self.nominal_input_parameter_values, sample_size=1)
        self.nominal_load_cycling, self.nominal_life_criteria, self.nominal_stress_state = \
            self.execute_crack_growth_analysis(nominal_analysis_modules)
        settings.RUN_STATUS = Status.FINISHED

    def perform_probabilistic_study(self):
        """Performs a probabilistic analysis. """
        uncertainty_study = self.specify_study(self.input_parameters,
                                               self.number_of_aleatory_samples,
                                               self.number_of_epistemic_samples,
                                               self.sample_type,
                                               self.random_state)

        self.sampling_input_parameter_values = uncertainty_study.create_variable_sample_sheet()
        self.uncertain_parameters = uncertainty_study.get_uncertain_parameter_names()
        uncertain_analysis_modules = \
            self.setup_crack_growth_analysis(self.sampling_input_parameter_values,
                                             sample_size=uncertainty_study.total_sample_size)
        self.load_cycling, self.life_criteria, self.stress_state = \
            self.execute_crack_growth_analysis(uncertain_analysis_modules)
        if settings.is_stopping():
            settings.RUN_STATUS = Status.STOPPED
            return

        self.nominal_input_parameter_values = uncertainty_study.create_variable_nominal_sheet()
        nominal_analysis_modules = \
            self.setup_crack_growth_analysis(self.nominal_input_parameter_values, sample_size=1)
        self.nominal_load_cycling, self.nominal_life_criteria, self.nominal_stress_state = \
            self.execute_crack_growth_analysis(nominal_analysis_modules)
        settings.RUN_STATUS = Status.FINISHED

    @staticmethod
    def specify_study(input_parameters,
                      aleatory_samples,
                      epistemic_samples,
                      sample_type,
                      random_state):
        """
        Builds up study framework in terms of study type, 
        sample size distribution type, and uncertainty classification.
        """
        if sample_type == 'deterministic':
            study = Sampling.UncertaintyStudy(number_of_aleatory_samples=aleatory_samples,
                                              number_of_epistemic_samples=epistemic_samples,
                                              random_state=random_state)
        elif sample_type == 'random':
            study = Sampling.RandomStudy(number_of_aleatory_samples=aleatory_samples,
                                         number_of_epistemic_samples=epistemic_samples,
                                         random_state=random_state)
        elif sample_type == 'lhs':
            study = Sampling.LHSStudy(number_of_aleatory_samples=aleatory_samples,
                                      number_of_epistemic_samples=epistemic_samples,
                                      random_state=random_state)
        elif sample_type == 'bounding':
            study = \
                Sampling.BoundingStudy(number_of_aleatory_samples=aleatory_samples,
                                       number_of_epistemic_samples=epistemic_samples,
                                       random_state=random_state)
        elif sample_type == 'sensitivity':
            study = \
                Sampling.OneAtATimeSensitivityStudy(number_of_aleatory_samples=aleatory_samples,
                                                    number_of_epistemic_samples=epistemic_samples,
                                                    random_state=random_state)
        else:
            raise ValueError("sample_type must be deterministic, random, "
                             + "lhs, bounding, or sensitivity")

        study.add_variables(input_parameters)

        return study

    def setup_crack_growth_analysis(self, parameter_value_dict, sample_size):
        """Creates the underlying modules for the crack growth analysis. """
        analysis_modules = {}
        analysis_modules['pipe'] = Pipe(outer_diameter=parameter_value_dict['outer_diameter'],
                                        wall_thickness=parameter_value_dict['wall_thickness'],
                                        sample_size=sample_size)
        analysis_modules['defect'] = \
            DefectSpecification(flaw_depth=parameter_value_dict['flaw_depth'],
                                flaw_length=parameter_value_dict['flaw_length'],
                                sample_size=sample_size)
        analysis_modules['environment'] = \
            EnvironmentSpecification(max_pressure=parameter_value_dict['max_pressure'],
                                     min_pressure=parameter_value_dict['min_pressure'],
                                     temperature=parameter_value_dict['temperature'],
                                     volume_fraction_h2=parameter_value_dict['volume_fraction_h2'],
                                     sample_size=sample_size)
        analysis_modules['material'] = \
            MaterialSpecification(yield_strength=parameter_value_dict['yield_strength'],
                                  fracture_resistance=parameter_value_dict['fracture_resistance'],
                                  sample_size=sample_size)
        analysis_modules['stress'] = \
            InternalAxialHoopStress(pipe=analysis_modules['pipe'],
                                    environment=analysis_modules['environment'],
                                    material=analysis_modules['material'],
                                    defect=analysis_modules['defect'],
                                    sample_size=sample_size)
        analysis_modules['crack_growth_model'] = \
            CrackGrowth(analysis_modules['environment'],
                        growth_model_specification=self.crack_growth_model,
                        sample_size=sample_size)
        return analysis_modules

    def execute_crack_growth_analysis(self, analysis_modules):
        """Starts the process running crack growth analysis. """
        pipe_evaluation = CycleEvolution(pipe=analysis_modules['pipe'],
                                         stress_state=analysis_modules['stress'],
                                         defect=analysis_modules['defect'],
                                         environment=analysis_modules['environment'],
                                         material=analysis_modules['material'],
                                         crack_growth_model=analysis_modules['crack_growth_model'])
        load_cycling = pipe_evaluation.calc_life_assessment(step_cycles=self.step_cycles)
        life_criteria = calc_pipe_life_criteria(cycle_results=load_cycling,
                                                pipe=analysis_modules['pipe'],
                                                stress_state=analysis_modules['stress'])

        return load_cycling, life_criteria, analysis_modules['stress']

    def postprocess_single_crack_results(self, single_pipe_index=None, save_figs=False):
        """
        Postprocesses a single pipe's results from an ensemble analysis.
        If no pipe index is specified, nominal results are shown.

        Parameters
        ----------
        single_pipe_index : int, optional
            Index of requested pipe. Defaults to None.
        save_figs : bool, optional
            Flag that enables saving plots to png files. Defaults to False.

        """
        if single_pipe_index is not None:
            specific_life_criteria_result = \
                report_single_pipe_life_criteria_results(self.life_criteria, single_pipe_index)
            specific_load_cycling = report_single_cycle_evolution(self.load_cycling,
                                                                  single_pipe_index)
        else:
            specific_life_criteria_result = \
                report_single_pipe_life_criteria_results(self.nominal_life_criteria, pipe_index=0)
            specific_load_cycling = report_single_cycle_evolution(self.nominal_load_cycling,
                                                                  pipe_index=0)

        self.crack_growth_plot = generate_pipe_life_assessment_plot(specific_load_cycling,
                                                                    specific_life_criteria_result,
                                                                    save_fig=save_figs)
        self.ex_rates_plot = generate_crack_growth_rate_plot(specific_load_cycling, save_fig=save_figs)

    def gather_single_crack_cycle_evolution(self, single_pipe_index=None):
        """Gets results for a single pipe crack growth analysis from an ensemble analysis.

        Parameters
        ----------
        single_pipe_index : int, optional
            Index of requested pipe. Defaults to None.

        Returns
        -------
        pandas.DataFrame
            DataFrame of single pipe analysis results.

        """
        if single_pipe_index is not None:
            single_cycle_evolution = {}
            for column_name, column_value in self.load_cycling.items():
                single_cycle_evolution[column_name] = column_value[single_pipe_index]
        else:
            single_cycle_evolution = self.nominal_load_cycling

        return pd.DataFrame(single_cycle_evolution)

    def save_results(self, folder_name=None, output_dir=None):
        """Saves crack evolution simulation results.
        
        Parameters
        ----------
        folder_name : str, optional
            Folder name to store results into. 
            Defaults to 'Results/'.  
        output_dir : str, optional
            Directory path for creating the results folder.
            Defaults to current working directory. 

        """

        if output_dir is None:
            if folder_name is None:
                now = datetime.now()
                folder_name = now.strftime('Results/date_%d_%m_%Y_time_%H_%M/')

            folder_path = pl.Path(folder_name)
            folder_path.mkdir(parents=True, exist_ok=True)
        else:
            folder_name = str(output_dir) + '/'

        self.save_parameter_characterizations(folder_name)

        if self.sample_type == 'deterministic':
            self.save_deterministic_results(folder_name)
        else:
            self.save_probabilistic_results(folder_name)

        return folder_name

    def save_parameter_characterizations(self, folder_name):
        """
        Saves deterministic or probabilistic parameter characterizations 
        used in analysis to a csv file.

        Parameters
        ----------
        folder_name : str
            Folder to store csv into. 

        """
        with open(folder_name + 'input_parameters.csv', mode='w', encoding='utf-8') as open_file:
            header_part1 = 'Parameter, Deterministic/Distribution Type, Nominal Value, '
            header_part2 = 'Uncertainty Type, Distribution Parameter 1, Distribution Parameter 2, '
            header_part3 = 'Distribution Lower Bound, Distribution Upper Bound'
            open_file.write(header_part1 + header_part2 + header_part3 + '\n')
            for parameter in self.input_parameters.values():
                open_file.write(repr(parameter) + '\n')

    def save_deterministic_results(self, folder_name):
        """Saves deterministic results to a csv file.

        Parameters
        ----------
        folder_name : str
            Folder to store csv into. 
            
        """
        life_criteria_data = pd.DataFrame()
        for key, value in self.nominal_life_criteria.items():
            life_criteria_data[key] = list(value[0])

        life_criteria_data.to_csv(f'{folder_name}life_criteria.csv',
                                  index_label=False,
                                  index=False)

        cleaned_name = self.clean_results_names()
        for key, values in self.nominal_load_cycling.items():
            values.T.to_csv(f'{folder_name}{cleaned_name[key]}.csv',
                            index_label=False, index=False, header=False)

    def save_probabilistic_results(self, folder_name):
        """Saves probabilistic results to a csv file.

        Parameters
        ----------
        folder_name : str
            Folder to store csv into. 
            
        """
        life_criteria_data = pd.DataFrame()
        for key, value in self.life_criteria.items():
            life_criteria_data[key] = list(value[0])

        life_criteria_data.to_csv(f'{folder_name}life_criteria.csv',
                                  index_label=False,
                                  index=False)

        cleaned_name = self.clean_results_names()
        for key, values in self.load_cycling.items():
            values.T.to_csv(f'{folder_name}{cleaned_name[key]}.csv',
                            index_label=False, index=False, header=False)

    def clean_results_names(self):
        """Cleans up variable names for saving to csv. """
        cleaned_name = {}
        for name in self.nominal_load_cycling:
            name_list = name.split()
            cleaned_name[name] = ''
            for val in name_list:
                val = val.replace('/', 'Over')
                if self.check_for_units(val):
                    pass
                else:
                    cleaned_name[name] += self.capitalize_rules(val, name)

        return cleaned_name

    @staticmethod
    def check_for_units(value:str):
        """Checks for brackets in strings to indicate unit values. """
        return ('(' in value) or (')' in value)

    @staticmethod
    def capitalize_rules(value:str, name:list):
        """Enforces capitalization rules for multi-word strings. """
        if len(name.split()) > 1:
            return value.capitalize()

        return value

    def apply_inspection_mitigation(self,
                                    probability_of_detection,
                                    detection_resolution,
                                    inspection_frequency,
                                    criteria):
        """Run inspection and mitigation analysis on crack evolution results.
        
        Parameters
        ----------
        probability_of_detection : float
            Probability of a crack being detected at each inspection.
        detection_resolution : float
            Crack depth that is detectable by inspection. 
            For example, a value of 0.3 indicates any crack larger than 30% of wall thickness is
            detectable.
        inspection_frequency : int
            Number of cycles between each inspection.
            For example, a 4-year inspection interval would have a frequency of 4 * 365 cycles.
        criteria : str
            Failure criteria to select from life criteria results.

        Returns
        -------
        mitigated : list
            List of bool values for each sample indicating whether or not the failure was mitigated.
        
        """
        monitoring_activity = InspectionMitigation(probability_of_detection,
                                                   detection_resolution,
                                                   inspection_frequency)
        mitigated, _ = \
            monitoring_activity.inspect_then_mitigate(self.load_cycling,
                                                      self.life_criteria[criteria][1],
                                                      self.random_state)
        plot_mitigation_histograms(self.life_criteria[criteria],
                                   mitigated,
                                   inspection_frequency)
        plot_unscaled_mitigation_cdf(self.life_criteria[criteria],
                                     mitigated,
                                     inspection_frequency)
        return mitigated

    def get_design_curve_plot(self):
        """Returns plot ready for GUI display. """
        dk, da_dn = get_design_curve(specified_r=0.75, specified_fugacity=0.16973535)
        filepath = plot_det_design_curve(dk, da_dn, save_fig=True)
        return filepath

    def assemble_failure_assessment_diagram(self, save_fig=False):
        """Creates failure assessment diagram. 
        
        Parameters
        ----------
        save_fig : bool, optional
            Flag for saving the diagram to a png file.
        
        """
        calculate_failure_assessment(self.nominal_input_parameter_values,
                                     self.nominal_load_cycling,
                                     self.nominal_stress_state)

        if self.sample_type == 'deterministic':
            self.failure_assessment_plot = \
                plot_failure_assessment_diagram(self.nominal_load_cycling,
                                                save_fig=save_fig)
        else:
            calculate_failure_assessment(self.sampling_input_parameter_values,
                                         self.load_cycling,
                                         self.stress_state)
            self.failure_assessment_plot = \
                plot_failure_assessment_diagram(self.load_cycling,
                                                self.nominal_load_cycling,
                                                save_fig=save_fig)


    def generate_probabilistic_results_plots(self, plotted_variable):
        """Creates ensemble of plots for probabilistic analysis results. 
        
        Parameters
        ----------
        plotted_variable : str
            Pipe life criteria to plot. 

        """
        if self.sample_type == 'deterministic':
            raise ValueError('Probabilistic plots can not be created for deterministic study')
        plot_pipe_life_ensemble(self, criteria=plotted_variable)
        plot_cycle_life_criteria_scatter(self, criteria=plotted_variable)
        plot_cycle_life_criteria_scatter(self, criteria=plotted_variable, color_by_variable=True)
        plot_cycle_life_pdfs(self, criteria=plotted_variable)
        plot_cycle_life_cdfs(self, criteria=plotted_variable)
