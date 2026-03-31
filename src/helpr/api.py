# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import os
import math
import warnings

from datetime import datetime
from multiprocessing.pool import Pool

import pathlib as pl
import random as rd
import string as st
import multiprocessing as mp
import numpy as np
import numpy.random as npr

from probabilistic.capabilities import sampling as Sampling
from probabilistic.capabilities.uncertainty_definitions import (DeterministicCharacterization,
                                                                UncertaintyCharacterization,
                                                                TimeSeriesCharacterization)
from probabilistic.capabilities.plotting import plot_sample_histogram

from helpr import settings
from helpr.settings import Status
from helpr.physics.pipe import Pipe
from helpr.physics.crack_initiation import DefectSpecification
from helpr.physics.environment import EnvironmentSpecification, EnvironmentSpecificationRandomLoad
from helpr.physics.material import MaterialSpecification
from helpr.physics.stress_state import InternalAxialHoopStress
from helpr.physics.residual_stress import HeatInputFromProcess, CircumferentialWeld
from helpr.physics.crack_growth import CrackGrowth, get_design_curve
from helpr.physics.inspection_mitigation import InspectionMitigation
from helpr.physics.life_assessment import LifeAssessment
from helpr.physics.fracture import calculate_failure_assessment
from helpr.utilities.postprocessing import (calc_pipe_life_criteria,
                                            report_single_pipe_life_criteria_results,
                                            report_single_cycle_evolution)
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
from helpr.utilities.saving import (save_deterministic_results,
                                    save_probabilistic_results,
                                    save_parameter_characterizations,
                                    get_variable_units)


class CrackEvolutionAnalysis:
    """
    Class to hold API capability for carrying out pipeline fracture and fatigue analyses.
    
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
    weld_flaw_direction
    weld_steel
    weld_process

    nominal_load_cycling : dict
        Results from crack growth analysis for a deterministic (single) pipe instance.
    
    nominal_life_criteria : dict
        Life criteria results for a deterministic (single) pipe instance.

    load_cycling : dict
        Results from crack growth analysis for all samples in a probabilistic study.

    life_criteria : dict
        Life criteria results for all samples in a probabilistic study.

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
                 residual_stress_intensity_factor=None,
                 weld_thickness=None,
                 weld_yield_strength=None,
                 weld_flaw_distance=None,
                 weld_flaw_direction=None,
                 weld_steel=None,
                 weld_process=None,
                 aleatory_samples=0,
                 epistemic_samples=0,
                 sample_type='deterministic',
                 random_seed=None,
                 max_cycles=None,
                 cycle_step=None,
                 fad_type=None):
        """
        Initializes analysis object.

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
        residual_stress_intensity_factor : DeterministicCharacterization or UncertaintyCharacterization or None, optional
            Residual stress intensity factor, in MPa-m^(1/2).
            This will override all the weld properties specified below
            if provided.
            Default is None.
        weld_thickness : DeterministicCharacterization or UncertaintyCharacterization or None, optional
            Weld thickness, in meters.
            Must be defined if residual stresses are to be considered
            and `residual_stress_intensity_factor` is not provided.
            Ignored if `residual_stress_intensity_factor != None`.
            Default is None.
        weld_yield_strength: DeterministicCharacterization or UncertaintyCharacterization or None, optional
            Yield strength of the weld material, in MPa.
            Must be defined if residual stresses are to be considered
            and `residual_stress_intensity_factor` is not provided.
            Ignored if `residual_stress_intensity_factor != None`.
            If None and if other weld properties are defined,
            the yield strength is estimated using the yield strength of
            the base material using Equation 9D.1 from API 579-1.
            Default is None.
        weld_flaw_distance : DeterministicCharacterization or UncertaintyCharacterization or None, optional
            Distance from the weld that the flaw is located, in meters.
            Must be defined if residual stresses are to be considered
            and `residual_stress_intensity_factor` is not provided.
            Ignored if `residual_stress_intensity_factor != None`.
            If None and if other weld properties are defined,
            a distance of zero is used.
            Default is None.
        weld_flaw_direction : str, optional
            Direction of weld flaw relative to the weld seam.
            Must be defined if residual stresses are to be considered
            and `residual_stress_intensity_factor` is not provided.
            Ignored if `residual_stress_intensity_factor != None`.
            Default is None.
        weld_steel : str, optional
            Weld steel used.
            Must be defined if residual stresses are to be considered
            and `residual_stress_intensity_factor` is not provided.
            Ignored if `residual_stress_intensity_factor != None`.
            Default is None.
        weld_process : str, optional
            Weld process used.
            Must be defined if residual stresses are to be considered
            and `residual_stress_intensity_factor` is not provided.
            Ignored if `residual_stress_intensity_factor != None`.
            Default is None.
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
        fad_type : str, optional
            Indicates the type of FAD computations to use.
            Default to 'simple'
        """

        if isinstance(max_pressure, TimeSeriesCharacterization) and cycle_step != 1:
            raise ValueError(f'Random loading capability requires crack evolution with cycle_step=1')

        if crack_growth_model is None:
            crack_growth_model = {'model_name': 'code_case_2938'}

        if stress_intensity_method is None:
            stress_intensity_method = 'anderson'

        if surface is None:
            surface = 'inside'

        if delta_c_rule is None:
            delta_c_rule = 'proportional'

        if max_cycles is None:
            max_cycles = math.inf
        
        if fad_type is None:
            fad_type = 'simple'

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
        self._set_resid_stress_params(weld_thickness,
                                      weld_yield_strength,
                                      weld_flaw_distance,
                                      weld_flaw_direction,
                                      weld_steel,
                                      weld_process,
                                      residual_stress_intensity_factor)
        self.surface = surface
        self.delta_c_rule = delta_c_rule
        self.max_cycles = max_cycles
        self.fad_type = fad_type
        self.cycle_step = cycle_step
        self.load_cycling = None
        self.nominal_load_cycling = None
        self.life_criteria = None
        self.nominal_life_criteria = None

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

    def _set_resid_stress_params(self,
                                 weld_thickness,
                                 weld_yield_strength,
                                 weld_flaw_distance,
                                 weld_flaw_direction,
                                 weld_steel,
                                 weld_process,
                                 residual_stress_intensity_factor):
        """Check that the weld parameters associated with residual
         stress calculations are properly defined and create
         class variables for them.
         """
        # explicit residual_stress_intensity_factor overrides all the
        # weld inputs
        weld_args_undefined = [x is None for x in [
            weld_thickness, weld_flaw_direction, weld_steel, weld_process]]
        if residual_stress_intensity_factor:
            self.include_resid_stress = True
            self.input_parameters['residual_stress_intensity_factor'] = \
                residual_stress_intensity_factor
            if not any(weld_args_undefined):
                warnings.warn(
                    'Weld input arguments will be ignored an an ' +
                    'explicit residual stress intensity factor ' +
                    'has been provided.')
        else:
            if all(weld_args_undefined):
                self.include_resid_stress = False
            elif not any(weld_args_undefined):
                self.include_resid_stress = True
                if weld_yield_strength is None:
                    weld_yield_strength = DeterministicCharacterization(
                            name='weld_yield_strength', value=None)
                if weld_flaw_distance is None:
                    weld_flaw_distance = DeterministicCharacterization(
                    name='weld_flaw_distance', value=0)

                self.input_parameters['weld_thickness'] = \
                    weld_thickness
                self.input_parameters['weld_yield_strength'] = \
                    weld_yield_strength
                self.input_parameters['weld_flaw_distance'] = \
                    weld_flaw_distance
                self.weld_flaw_direction = weld_flaw_direction
                self.weld_steel = weld_steel
                self.weld_process = weld_process
            else:
                raise TypeError(
                    'Not all required weld parameters are fully defined. ' +
                    'To consider residual stresses in this assessment, ' +
                    "ensure 'weld_thickness', 'weld_steel', 'and " +
                    "'weld_process' are all defined.")

    def check_parameter_names(self):
        """
        Ensures parameter object names match assigned parameter.

        Raises
        ------
        ValueError
            If any parameter object name does not match its assigned parameter name.
        """
        for parameter_name, parameter_object in self.input_parameters.items():
            try:
                if parameter_name != parameter_object.name:
                    raise ValueError(f"Parameter assigned to {parameter_name} has incorrect name")
            except ValueError as e:
                raise ValueError(f"parameter {parameter_name} is incorrectly defined") from e

    def setup_study(self):
        """Setup crack evolution analysis modules."""
        self.setup_deterministic_study()
        if self.sample_type != 'deterministic':
            self.setup_probabilistic_study()

    def perform_study(self):
        """Starts crack evolution analysis study. """
        self.perform_deterministic_study()
        if self.sample_type != 'deterministic':
            self.perform_probabilistic_study()

    def gen_random_seed(self, random_seed):
        """
        Sets random seed for recreating.

        Parameters
        ----------
        random_seed : float
            The specified random seed or None.

        Returns
        -------
        int
            The generated random seed.
        """
        result = int(''.join(rd.choices(st.digits, k=10))) if random_seed is None else random_seed
        return result

    def get_random_seed(self):
        """
        Returns the random seed value.

        Returns
        -------
        float
            The random seed value.
        """
        return self.random_seed

    def set_random_state(self):
        """Sets up the random state. """
        self.random_state = npr.default_rng(seed=self.random_seed)

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
        self.nominal_load_cycling = \
            self.execute_crack_growth_analysis(self.nominal_analysis_modules, sample_size=1)
        calculate_failure_assessment(self.nominal_input_parameter_values,
                                     self.nominal_load_cycling,
                                     self.nominal_analysis_modules['stress'],
                                     self.fad_type)
        self.nominal_life_criteria = \
            calc_pipe_life_criteria(cycle_results=self.nominal_load_cycling,
                                    pipe=self.nominal_analysis_modules['pipe'],
                                    material=self.nominal_analysis_modules['material'])
        settings.RUN_STATUS = Status.FINISHED

    def perform_probabilistic_study(self):
        """Performs a probabilistic analysis.
        Calculates crack growth evolution and then failure assessment"""
        self.load_cycling = \
            self.execute_crack_growth_analysis(self.uncertain_analysis_modules,
                                               sample_size=self.study.total_sample_size)
        calculate_failure_assessment(self.sampling_input_parameter_values,
                                     self.load_cycling,
                                     self.uncertain_analysis_modules['stress'],
                                     self.fad_type)
        self.life_criteria = \
            calc_pipe_life_criteria(cycle_results=self.load_cycling,
                                    pipe=self.uncertain_analysis_modules['pipe'],
                                    material=self.uncertain_analysis_modules['material'])
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

        Parameters
        ----------
        input_parameters : dict
            Dictionary of input parameters for the study.
        aleatory_samples : int
            Number of aleatory samples.
        epistemic_samples : int
            Number of epistemic samples.
        sample_type : str
            Type of sampling ('deterministic', 'random', 'lhs', 'bounding', or 'sensitivity').
        random_state : np.random.Generator
            Random state for reproducibility.

        Returns
        -------
        Sampling.UncertaintyStudy or Sampling.RandomStudy or Sampling.LHSStudy or Sampling.BoundingStudy or Sampling.OneAtATimeSensitivityStudy
            The initialized study object based on the specified sample type.

        Raises
        ------
        ValueError
            If the sample_type is not one of the valid options.
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
        analysis_modules = {'pipe': [],
                            'defect': [],
                            'environment': [],
                            'material': [],
                            'stress': [],
                            'other_stress': [],
                            'crack_growth_model': []}

        for i in range(sample_size):
            analysis_modules['pipe'].append(Pipe(
                outer_diameter=parameter_value_dict['outer_diameter'][i],
                wall_thickness=parameter_value_dict['wall_thickness'][i]))
            analysis_modules['defect'].append(DefectSpecification(
                flaw_depth=parameter_value_dict['flaw_depth'][i],
                flaw_length=parameter_value_dict['flaw_length'][i],
                surface=self.surface))
            max_pressure_input = self.input_parameters['max_pressure']
            if isinstance(max_pressure_input, TimeSeriesCharacterization):
                analysis_modules['environment'].append(EnvironmentSpecificationRandomLoad(
                    max_pressure=parameter_value_dict['max_pressure'][i],
                    min_pressure=parameter_value_dict['min_pressure'][i],
                    temperature=parameter_value_dict['temperature'][i],
                    volume_fraction_h2=parameter_value_dict['volume_fraction_h2'][i]))
            else:
                analysis_modules['environment'].append(EnvironmentSpecification(
                    max_pressure=parameter_value_dict['max_pressure'][i],
                    min_pressure=parameter_value_dict['min_pressure'][i],
                    temperature=parameter_value_dict['temperature'][i],
                    volume_fraction_h2=parameter_value_dict['volume_fraction_h2'][i]))
            analysis_modules['material'].append(MaterialSpecification(
                yield_strength=parameter_value_dict['yield_strength'][i],
                fracture_resistance=parameter_value_dict['fracture_resistance'][i]))

            if self.stress_intensity_method == 'api':
                preloaded_api_g_tables, preloaded_api_a_tables =\
                      InternalAxialHoopStress.load_api_tables(surface=self.surface)
                preloaded_api_tables = (preloaded_api_g_tables, preloaded_api_a_tables)
            else:
                preloaded_api_tables = False

            analysis_modules['stress'].append(InternalAxialHoopStress(
                pipe=analysis_modules['pipe'][i],
                environment=analysis_modules['environment'][i],
                material=analysis_modules['material'][i],
                defect=analysis_modules['defect'][i],
                stress_intensity_method=self.stress_intensity_method,
                preloaded_tables=preloaded_api_tables))
            if self.include_resid_stress:
                if 'residual_stress_intensity_factor' in parameter_value_dict:
                    analysis_modules['other_stress'].append(
                        parameter_value_dict['residual_stress_intensity_factor'][i])
                else:
                    # MCD: heat_input could be moved to initialization, but
                    # keeping it here might make sense if we want to allow
                    # for HeatInputFromPower objects using uncertain inputs,
                    # so keeping it here for now TODO
                    heat_input = HeatInputFromProcess(
                        process=self.weld_process,
                        weld_steel=self.weld_steel)
                    analysis_modules['other_stress'].append(
                        CircumferentialWeld(
                            pipe=analysis_modules['pipe'][i],
                            environment=analysis_modules['environment'][i],
                            material=analysis_modules['material'][i],
                            defect=analysis_modules['defect'][i],
                            weld_thickness=parameter_value_dict['weld_thickness'][i],
                            flaw_direction=self.weld_flaw_direction,
                            flaw_distance=parameter_value_dict['weld_flaw_distance'][i],
                            heat_input=heat_input.calc_heat_input(),
                            weld_yield_strength=parameter_value_dict['weld_yield_strength'][i]))
            else:
                analysis_modules['other_stress'].append(None)
            analysis_modules['crack_growth_model'].append(CrackGrowth(
                environment=analysis_modules['environment'][i],
                growth_model_specification=self.crack_growth_model))

        return analysis_modules

    @staticmethod
    def calc_life_assessment_instance(stress_state,
                                      pipe,
                                      crack_growth,
                                      delta_c_rule,
                                      other_stress_state,
                                      max_cycles,
                                      cycle_step):
        """Calculate a life assessment for a single crack evolution instance
        
        Parameters
        ----------
        stress_state
        pipe
        weld
        crack_growth
        environment_specification
        delta_c_rule
        max_cycles
        cycle_step
        
        Returns
        -------
        all_cycles: dict
        
        """
        life_assessment = LifeAssessment(pipe_specification=pipe,
                                         stress_state=stress_state,
                                         crack_growth=crack_growth,
                                         delta_c_rule=delta_c_rule,
                                         other_stress_state=other_stress_state)

        return life_assessment.calc_life_assessment(max_cycles=max_cycles,
                                                    cycle_step=cycle_step)

    def execute_crack_growth_analysis(self, analysis_modules, sample_size):
        """Starts the process running crack growth analysis. """
        instance_data = []
        if sample_size > 1:
            for sample_index in range(sample_size):
                instance_data.append((analysis_modules['stress'][sample_index],
                                      analysis_modules['pipe'][sample_index],
                                      analysis_modules['crack_growth_model'][sample_index],
                                      self.delta_c_rule,
                                      analysis_modules['other_stress'][sample_index],
                                      self.max_cycles,
                                      self.cycle_step))

            # Initialize pool
            n_cpu = mp.cpu_count()
            with Pool(processes=n_cpu) as pool:
                load_cycling = pool.starmap(self.calc_life_assessment_instance, instance_data)

        else:
            load_cycling = [self.calc_life_assessment_instance(analysis_modules['stress'][0],
                                                       analysis_modules['pipe'][0],
                                                       analysis_modules['crack_growth_model'][0],
                                                       self.delta_c_rule,
                                                       analysis_modules['other_stress'][0],
                                                       self.max_cycles,
                                                       self.cycle_step)]

        return load_cycling

    def collect_intermediate_variables(self, analysis_modules, nominal=False):
        """
        Extracts intermediate variable values from analysis for pre and post processing steps

        Parameters
        ----------
        analysis_modules : dict
            Dictionary of analysis modules containing environmental and stress state information.
        nominal : bool, optional
            If True, collects nominal intermediate variables; otherwise, collects sampling intermediate variables.
        """
        if nominal:
            if self.include_resid_stress:
                if isinstance(analysis_modules['other_stress'][0],
                              float):
                    k_res = analysis_modules['other_stress'][0]
                else:
                    k_res = \
                        analysis_modules['other_stress'][0].calc_resid_stress_intensity_factor(
                            analysis_modules['stress'][0].initial_crack_depth)

                stress_mod = analysis_modules['stress'][0]
                k_max, k_min, _, _ = \
                    stress_mod.calc_stress_intensity_factor(
                        crack_depth=analysis_modules['stress'][0].initial_crack_depth,
                        crack_length=analysis_modules['stress'][0].initial_crack_length,
                        cycle_index=0,
                        phi=math.pi/2)
                self.nominal_intermediate_variables['r_ratio'] = (k_min + k_res)/(k_max + k_res)
            else:
                self.nominal_intermediate_variables['r_ratio'] = \
                    (analysis_modules['environment'][0]._get_min_pressure(index=0)/
                     analysis_modules['environment'][0]._get_max_pressure(index=0))
            self.nominal_intermediate_variables['fugacity_ratio'] =\
                  analysis_modules['environment'][0]._get_fugacity_ratio(index=0)
            self.nominal_intermediate_variables['%SMYS'] =\
                analysis_modules['stress'][0].percent_smys
            self.nominal_intermediate_variables['a (m)'] =\
                  analysis_modules['stress'][0].initial_crack_depth
            self.nominal_intermediate_variables['a/2c'] = \
                analysis_modules['stress'][0].initial_a_over_c/2
            self.nominal_intermediate_variables['t/R'] = analysis_modules['pipe'][0].calc_t_over_r()
        else:
            if self.include_resid_stress:
                if isinstance(analysis_modules['other_stress'][0],
                              float):
                    k_res = [
                        analysis_modules['other_stress'][i]
                        for i in range(self.study.total_sample_size)]
                else:
                    k_res = [
                        analysis_modules['other_stress'][i].calc_resid_stress_intensity_factor(
                            analysis_modules['stress'][i].initial_crack_depth)
                        for i in range(self.study.total_sample_size)]

                self.sampling_intermediate_variables['r_ratio'] = []
                for i in range(self.study.total_sample_size):
                    stress_mod = analysis_modules['stress'][i]
                    k_max, k_min, _, _ = \
                        stress_mod.calc_stress_intensity_factor(
                            crack_depth=analysis_modules['stress'][i].initial_crack_depth,
                            crack_length=analysis_modules['stress'][i].initial_crack_length,
                            phi=math.pi/2)
                    r = (k_min + k_res[i])/(k_max + k_res[i])
                    self.sampling_intermediate_variables['r_ratio'].append(r)

            else:
                self.sampling_intermediate_variables['r_ratio'] =\
                    [analysis_modules['environment'][i]._get_min_pressure(index=0)/
                        analysis_modules['environment'][i]._get_max_pressure(index=0)
                    for i in range(self.study.total_sample_size)]
            self.sampling_intermediate_variables['fugacity_ratio'] =\
                  [analysis_modules['environment'][i]._get_fugacity_ratio(index=0)
                   for i in range(self.study.total_sample_size)]
            self.sampling_intermediate_variables['%SMYS'] =\
                [analysis_modules['stress'][i].percent_smys
                 for i in range(self.study.total_sample_size)]
            self.sampling_intermediate_variables['a (m)'] =\
                  [analysis_modules['stress'][i].initial_crack_depth
                   for i in range(self.study.total_sample_size)]
            self.sampling_intermediate_variables['a/2c'] = \
                [analysis_modules['stress'][i].initial_a_over_c/2
                 for i in range(self.study.total_sample_size)]
            self.sampling_intermediate_variables['t/R'] =\
                [analysis_modules['pipe'][i].calc_t_over_r()
                 for i in range(self.study.total_sample_size)]

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
            # Note (Cianan): this is temp workaround to get data to frontend.
            # TODO: standardize handling of plot data.
            self.crack_growth_plot = plot_result[0]
            self.crack_growth_plot_data = plot_result[1]

        self.ex_rates_plot = generate_crack_growth_rate_plot(specific_load_cycling,
                                                             save_fig=save_figs)

    def gather_single_crack_cycle_evolution(self, single_pipe_index=None):
        """
        Gets results for a single pipe crack growth analysis from an ensemble analysis.

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
        """
        Saves crack evolution simulation results.
        
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

        save_deterministic_results(self, folder_name)
        if self.sample_type != 'deterministic':
            save_parameter_characterizations(self, folder_name)
            save_probabilistic_results(self, folder_name)

        return folder_name

    def apply_inspection_mitigation(self,
                                    probability_of_detection,
                                    detection_resolution,
                                    inspection_frequency,
                                    criteria,
                                    save_fig=False):
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
        save_fig : bool, optional
            Flag for saving the hist and cdf plots to png files.

        Returns
        -------
        filepath : list
            List of file paths to created hist and cdf figures
        plot_data : list
            List of lists of data contained in generated figures
        
        """
        monitoring_activity = InspectionMitigation(probability_of_detection,
                                                   detection_resolution,
                                                   inspection_frequency)
        cycles_till_mitigation = \
            monitoring_activity.inspect_then_mitigate(self.load_cycling,
                                                      self.life_criteria[criteria][1],
                                                      self.random_state)

        filepath_hist, plot_data_hist = \
            plot_mitigation_histograms(self.life_criteria[criteria][0],
                                       cycles_till_mitigation,
                                       save_fig=save_fig)
        filepath_cdf, plot_data_cdf = \
            plot_unscaled_mitigation_cdf(self.life_criteria[criteria][0],
                                         cycles_till_mitigation,
                                         save_fig=save_fig)
        filepaths = [filepath_hist, filepath_cdf]
        plot_data = [plot_data_hist, plot_data_cdf]

        return filepaths, plot_data

    def get_design_curve_plot(self):
        """Returns plot ready for GUI display. """
        r_ratio = self.nominal_load_cycling[0]['R ratio']
        environment_obj = self.nominal_analysis_modules['environment'][0]

        dk, da_dn = \
            get_design_curve(specified_r=r_ratio[0],
                             environment_obj=environment_obj,
                             crack_growth_model=self.crack_growth_model)
        filepath, plot_data = plot_det_design_curve(dk, da_dn, save_fig=True)


        max_pressure_input = self.input_parameters['max_pressure']
        random_loading_check = isinstance(max_pressure_input, TimeSeriesCharacterization)

        if len(set(r_ratio)) != 1 and not random_loading_check:
            for r_ratio_instance in np.unique(self.nominal_load_cycling[0]['R ratio']):
                dk, da_dn = \
                    get_design_curve(specified_r=r_ratio_instance,
                                     environment_obj=environment_obj,
                                     crack_growth_model=self.crack_growth_model)
                _, _ = plot_det_design_curve(dk, da_dn, save_fig=False)

        return filepath, plot_data

    def assemble_failure_assessment_diagram(self, save_fig=False):
        """
        Creates failure assessment diagram.

        Parameters
        ----------
        save_fig : bool, optional
            Flag for saving the diagram to a png file.

        Returns
        -------
        tuple
            A tuple containing:

            - plot : any
                The generated failure assessment plot.
            - data : any
                Data associated with the plot.
        """

        if isinstance(self.input_parameters['max_pressure'], TimeSeriesCharacterization):
            warnings.warn(
                    'Extraction of FAD intersection QoI when using user specified random loading '
                    + 'profile may be incorrect due to its stochastic nature.')

        if self.sample_type == 'deterministic':
            plot, data = plot_failure_assessment_diagram(life_assessment=self.nominal_load_cycling,
                                                         life_criteria=self.nominal_life_criteria,
                                                         fad_type=self.fad_type,
                                                         save_fig=save_fig)

        else:
            plot, data = \
                plot_failure_assessment_diagram(life_assessment=self.load_cycling,
                                                life_criteria=self.life_criteria,
                                                nominal=self.nominal_load_cycling,
                                                nominal_life_criteria=self.nominal_life_criteria,
                                                fad_type=self.fad_type,
                                                save_fig=save_fig)
        self.failure_assessment_plot = plot
        return plot, data

    def generate_probabilistic_results_plots(self, plotted_variable):
        """
        Creates ensemble of plots for probabilistic analysis results.
        
        Parameters
        ----------
        plotted_variable : list
            List of pipe life criteria to plot.

        Raises
        ------
        ValueError
            If the sample type is 'deterministic'.
        """
        if self.sample_type == 'deterministic':
            raise ValueError('Probabilistic plots can not be created for deterministic study')

            # Convert single criteria to a list
        if isinstance(plotted_variable, str):
            plotted_variable = [plotted_variable]

        plot_pipe_life_ensemble(self, criteria=plotted_variable)
        # for criteria in plotted_variable:
        plot_cycle_life_criteria_scatter(self, criteria=plotted_variable)
        plot_cycle_life_criteria_scatter(self, criteria=plotted_variable, color_by_variable=True)
        plot_cycle_life_pdfs(self, criteria=plotted_variable)
        plot_cycle_life_cdfs(self, criteria=plotted_variable)

    def generate_input_parameter_plots(self, save_figs=False):
        """
        Creates plots of the samples of the input parameters.

        Parameters
        ----------
        save_figs : bool, optional
            Flag for saving plots to PNG files. Defaults to False.

        Returns
        -------
        dict
            Dictionary of file paths for the generated plots.
        """
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
