# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.
import os
from datetime import datetime
import pathlib as pl
import random as rd
import string as st
import numpy as np
import pandas as pd

from probabilistic.capabilities import sampling as Sampling
from probabilistic.capabilities.uncertainty_definitions import UncertaintyCharacterization
from probabilistic.capabilities.plotting import plot_sample_histogram

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
from helpr.utilities.unit_conversion import get_variable_units


class CrackEvolutionAnalysis:
    """Class to hold API capability for carrying out pipeline fracture and fatigue analyses.
    
    Attributes
    ----------
    crack_growth_model
    max_cycles
    cycle_step
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
                 delta_c_rule=None,
                 stress_intensity_method=None,
                 surface=None,
                 aleatory_samples=0,
                 epistemic_samples=0,
                 sample_type='deterministic',
                 random_seed=None,
                 max_cycles=None,
                 cycle_step=None):
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
        crack_growth_model : dict, optional
            Specific crack growth model. Defaults to None.
        stress_intensity_method : str, optional
            Stress intensity factor method. Defaults to None.
        surface : str, optional
            Surface on which the crack is growing. Defaults to None.
        aleatory_samples : int, optional
            Number of aleatory samples. Defaults to 0.
        epistemic_samples : int, optional
            Number of epistemic samples. Defaults to 0.
        sample_type : str, optional
            Defaults to 'deterministic'.
        random_seed : float, optional
            Random seed used to initialize probabilistic analysis elements. Defaults to None.
        max_cycles: float or None, optional
            Maximum number of cycles to run the life assessment for before
            stopping. If `None`, the assessment will run until instances
            reach a/t > 0.8. Note that an assessment may
            stop before reaching `max_cycles` if all instances reach
            a/t > 0.8 before that number of cycles. Default is `None`.
        cycle_step : float or None, optional
            Number of cycles to iterate by at each evaluation step. If
            `None`, the number of cycles will be dynamically adjusted each
            iteration based on the crack growth. Default is `None`.
        delta_c_rule : str, optional
            Defaults to 'proportional'

        """

        if crack_growth_model is None:
            crack_growth_model = {'model_name': 'code_case_2938'}

        if stress_intensity_method is None:
            stress_intensity_method = 'anderson'

        if surface is None:
            surface = 'inside'

        if delta_c_rule is None:
            delta_c_rule = 'proportional'

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
        self.stress_intensity_method = stress_intensity_method
        self.surface = surface
        self.delta_c_rule = delta_c_rule
        self.max_cycles = max_cycles
        self.cycle_step = cycle_step
        self.load_cycling = None
        self.nominal_load_cycling = None
        self.life_criteria = None
        self.nominal_life_criteria = None
        self.stress_state = None
        self.nominal_stress_state = None

        self.nominal_input_parameter_values = {}
        self.sampling_input_parameter_values = {}
        self.nominal_intermediate_variables = {}
        self.sampling_intermediate_variables = {}

        self.number_of_aleatory_samples = aleatory_samples
        self.number_of_epistemic_samples = epistemic_samples
        self.sample_type = sample_type
        self.uncertain_parameters = []
        self.study = None

        self.nominal_analysis_modules = None
        self.uncertain_analysis_modules = None

        self.check_parameter_names()
        self.random_seed = self.gen_random_seed(random_seed)
        self.set_random_state()
        self.setup_study()

        self.crack_growth_plot = None
        self.crack_growth_plot_data = None

        self.ex_rates_plot = None
        self.design_curve_dk = None
        self.design_curve_da_dn = None

    def check_parameter_names(self):
        """Function to ensure parameter object names match assigned parameter. """
        for parameter_name, parameter_object in self.input_parameters.items():
            if parameter_name != parameter_object.name:
                raise ValueError(f"Parameter assigned to {parameter_name} has incorrect name")

    def setup_study(self):
        """Setup crack evolution analysis modules."""
        self.setup_deterministic_study()

    def perform_study(self):
        """Starts crack evolution analysis study. """
        self.perform_deterministic_study()
        if self.sample_type != 'deterministic':
            self.setup_probabilistic_study()
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

    def setup_deterministic_study(self):
        """Setup modules for deterministic analysis."""
        self.study = self.specify_study(self.input_parameters,
                                        self.number_of_aleatory_samples,
                                        self.number_of_epistemic_samples,
                                        self.sample_type,
                                        self.random_state)
        self.nominal_input_parameter_values = self.study.create_variable_nominal_sheet()
        self.nominal_analysis_modules = \
            self.setup_crack_growth_analysis(self.nominal_input_parameter_values,
                                             sample_size=1)
        self.collect_intermediate_variables(self.nominal_analysis_modules,
                                            nominal=True)

    def setup_probabilistic_study(self):
        """Setup modules for probabilistic analysis."""
        self.sampling_input_parameter_values = self.study.create_variable_sample_sheet()
        self.uncertain_parameters = self.study.get_uncertain_parameter_names()
        self.uncertain_analysis_modules = \
            self.setup_crack_growth_analysis(self.sampling_input_parameter_values,
                                             sample_size=self.study.total_sample_size)
        self.collect_intermediate_variables(self.uncertain_analysis_modules,
                                            nominal=False)

    def perform_deterministic_study(self):
        """Performs a deterministic analysis.
        Calculates crack growth evolution and then failure assessment"""
        self.nominal_load_cycling, self.nominal_life_criteria, self.nominal_stress_state = \
            self.execute_crack_growth_analysis(self.nominal_analysis_modules)
        calculate_failure_assessment(self.nominal_input_parameter_values,
                                     self.nominal_load_cycling,
                                     self.nominal_stress_state,
                                     self.stress_intensity_method)
        settings.RUN_STATUS = Status.FINISHED

    def perform_probabilistic_study(self):
        """Performs a probabilistic analysis.
        Calculates crack growth evolution and then failure assessment"""
        self.load_cycling, self.life_criteria, self.stress_state = \
            self.execute_crack_growth_analysis(self.uncertain_analysis_modules)
        calculate_failure_assessment(self.sampling_input_parameter_values,
                                     self.load_cycling,
                                     self.stress_state,
                                     self.stress_intensity_method)
        if settings.is_stopping():
            settings.RUN_STATUS = Status.STOPPED
            return

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
                                surface=self.surface,
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
                                    stress_intensity_method=self.stress_intensity_method,
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
                                         crack_growth_model=analysis_modules['crack_growth_model'],
                                         delta_c_rule=self.delta_c_rule)
        load_cycling = pipe_evaluation.calc_life_assessment(
            max_cycles=self.max_cycles, cycle_step=self.cycle_step)
        life_criteria = calc_pipe_life_criteria(cycle_results=load_cycling,
                                                pipe=analysis_modules['pipe'],
                                                material=analysis_modules['material'])

        return load_cycling, life_criteria, analysis_modules['stress']

    def collect_intermediate_variables(self, analysis_modules, nominal=False):
        """Extracts intermediate variable values from analysis for pre and post processing steps"""
        if nominal:
            self.nominal_intermediate_variables['r_ratio'] =\
                  analysis_modules['environment'].calc_r_ratio()
            self.nominal_intermediate_variables['fugacity_ratio'] =\
                  analysis_modules['environment'].calc_fugacity_ratio()
            self.nominal_intermediate_variables['%SMYS'] = analysis_modules['stress'].percent_smys
            self.nominal_intermediate_variables['a (m)'] =\
                  analysis_modules['stress'].initial_crack_depth
            self.nominal_intermediate_variables['a/2c'] = analysis_modules['stress'].initial_a_over_c/2
            self.nominal_intermediate_variables['t/R'] = analysis_modules['pipe'].calc_t_over_r()
        else:
            self.sampling_intermediate_variables['r_ratio'] =\
                  analysis_modules['environment'].calc_r_ratio()
            self.sampling_intermediate_variables['fugacity_ratio'] =\
                  analysis_modules['environment'].calc_fugacity_ratio()
            self.sampling_intermediate_variables['%SMYS'] = analysis_modules['stress'].percent_smys
            self.sampling_intermediate_variables['a (m)'] =\
                  analysis_modules['stress'].initial_crack_depth
            self.sampling_intermediate_variables['a/2c'] = analysis_modules['stress'].initial_a_over_c/2
            self.sampling_intermediate_variables['t/R'] = analysis_modules['pipe'].calc_t_over_r()

    def print_nominal_intermediate_variables(self):
        """Prints nominal values of intermediate variables"""
        print('Nominal Intermediate Variable Values')
        print('------------------------------------')
        for key, value in self.nominal_intermediate_variables.items():
            print(f'{key} = {value}')

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

        plot_result = generate_pipe_life_assessment_plot(specific_load_cycling,
                                                         specific_life_criteria_result,
                                                         save_fig=save_figs)
        if plot_result is not None:
            # Note (Cianan): this is temp workaround to get data to frontend. TODO: standardize handling of plot data.
            self.crack_growth_plot = plot_result[0]
            self.crack_growth_plot_data = plot_result[1]

        self.ex_rates_plot = generate_crack_growth_rate_plot(specific_load_cycling,
                                                             save_fig=save_figs)

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
            return report_single_cycle_evolution(self.load_cycling, single_pipe_index)

        return report_single_cycle_evolution(self.nominal_load_cycling, 0)

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

        self.save_deterministic_results(folder_name)
        if self.sample_type != 'deterministic':
            self.save_parameter_characterizations(folder_name)
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
        CSV file has nominal input parameters specified first,
        then subset of cycle evolution results

        Parameters
        ----------
        folder_name : str
            Folder to store csv into
            
        """
        with open(folder_name + 'Nominal_Results.csv', mode='w', encoding='utf-8') as open_file:
            parameter_header = 'Parameter, Nominal Value, Units'
            open_file.write(parameter_header + '\n')
            for name, value in self.input_parameters.items():
                parameter_description = np.array([x.strip() for x in repr(value).split(',')])
                open_file.write(parameter_description[0] + ', '
                                + parameter_description[2] + ', '
                                + get_variable_units(name, for_plotting=False) + '\n')

            open_file.write('\n')

            for name, value in self.nominal_intermediate_variables.items():
                split_text = name.split('(')
                if len(split_text) == 2:
                    parameter_description = np.array([split_text[0].strip(),
                                                      '('+split_text[1].strip()])
                else:
                    parameter_description = np.array([split_text[0].strip(), '( )'])

                open_file.write(parameter_description[0] + ', '
                                + f'{value[0]:.5f}' + ', '
                                + parameter_description[1] + '\n')

            open_file.write('\n\n')

            csv_file_data = self.gather_single_crack_cycle_evolution()
            csv_file_data['2c/t'] = \
                csv_file_data['c (m)']*2/self.nominal_input_parameter_values['wall_thickness']
            desired_columns = ['Total cycles', 'a/t', '2c/t', 'Kmax (MPa m^1/2)',
                               'Delta K (MPa m^1/2)', 'Toughness ratio', 'Load ratio']
            analysis_results = csv_file_data[desired_columns].to_csv(path_or_buf=None, index=False)
            open_file.write(analysis_results)

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
        nominal_r_ratio = self.nominal_intermediate_variables['r_ratio']
        nominal_fugacity_ratio = self.nominal_intermediate_variables['fugacity_ratio']
        dk, da_dn = get_design_curve(specified_r=nominal_r_ratio,
                                     specified_fugacity=nominal_fugacity_ratio)

        filepath, plot_data = plot_det_design_curve(dk, da_dn, save_fig=True)
        return filepath, plot_data

    def assemble_failure_assessment_diagram(self, save_fig=False):
        """Creates failure assessment diagram. 
        
        Parameters
        ----------
        save_fig : bool, optional
            Flag for saving the diagram to a png file.
        
        """
        if self.sample_type == 'deterministic':
            plot, data = plot_failure_assessment_diagram(self.nominal_load_cycling,
                                                         save_fig=save_fig)

        else:
            plot, data = plot_failure_assessment_diagram(self.load_cycling,
                                                         self.nominal_load_cycling,
                                                         save_fig=save_fig)
        self.failure_assessment_plot = plot
        return plot, data

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

    def generate_input_parameter_plots(self, save_figs=False):
        """Creates plots of the samples of the input parameters."""
        plot_files = {}
        for parameter_name, parameter_value in self.input_parameters.items():
            plot_label = parameter_name.replace('_',' ').title() + ' ' + \
                get_variable_units(parameter_name, for_plotting=True)
            if isinstance(parameter_value, UncertaintyCharacterization):
                filepath = os.path.join(settings.OUTPUT_DIR, f"InputParameter_{parameter_name}.png") if save_figs else ""
                plot_sample_histogram(self.sampling_input_parameter_values[parameter_name],
                                      plot_label,
                                      density=False,
                                      save_fig=save_figs,
                                      filepath=filepath)
                plot_files[parameter_name] = filepath
            else:
                parameter_value.plot_distribution(alternative_name=plot_label)

        return plot_files
