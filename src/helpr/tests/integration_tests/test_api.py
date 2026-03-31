# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import pathlib as pl
import warnings

from unittest.mock import patch
import matplotlib.pyplot as plt

import probabilistic.capabilities.uncertainty_definitions as Uncertainty
from helpr import settings
from helpr.settings import Status
from helpr.utilities.unit_conversion import convert_in_to_m, convert_ksi_to_mpa
from helpr.api import CrackEvolutionAnalysis


class APITestCase(unittest.TestCase):
    """
    Class for unit tests of api module.
    
    Attributes
    ----------
    outer_diameter : Uncertainty.DeterministicCharacterization
        Outer diameter of the pipe.
    wall_thickness : Uncertainty.DeterministicCharacterization
        Wall thickness of the pipe.
    flaw_depth : Uncertainty.DeterministicCharacterization
        Depth of the flaw.
    max_pressure : Uncertainty.DeterministicCharacterization
        Maximum pressure.
    min_pressure : Uncertainty.DeterministicCharacterization
        Minimum pressure.
    temperature : Uncertainty.DeterministicCharacterization
        Temperature.
    volume_fraction_h2 : Uncertainty.DeterministicCharacterization
        Volume fraction of hydrogen.
    yield_strength : Uncertainty.DeterministicCharacterization
        Yield strength of the material.
    fracture_resistance : Uncertainty.DeterministicCharacterization
        Fracture resistance of the material.
    flaw_length : Uncertainty.DeterministicCharacterization
        Length of the flaw.
    unc_flaw_depth : Uncertainty.NormalDistribution
        Uncertainty in the flaw depth.
    unc_temperature : Uncertainty.UniformDistribution
        Uncertainty in the temperature.
    unc_volume_fraction_h2 : Uncertainty.UniformDistribution
        Uncertainty in the volume fraction of hydrogen.
    folder_path_deterministic : str
        Path to the folder for deterministic results.
    folder_path_probabilistic : str
        Path to the folder for probabilistic results.
    deterministic_study : CrackEvolutionAnalysis
        Deterministic study object.
    deterministic_results : CrackEvolutionAnalysis
        Deterministic results object.
    probabilistic_results : CrackEvolutionAnalysis
        Probabilistic results object.
    weld_thickness : float
        Thickness of the weld.
    weld_yield_strength : float
        Yield strength of the weld.
    weld_flaw_distance : float
        Distance of the flaw from the weld.
    weld_flaw_direction : str
        Direction of the flaw with respect to the weld.
    weld_steel : str
        Type of steel used in the weld.
    weld_process : str
        Process used to create the weld.
    """

    def setUp(self):
        """Function to specify common inputs to api module."""
        self.outer_diameter = \
            Uncertainty.DeterministicCharacterization(name='outer_diameter',
                                                      value=convert_in_to_m(24))
        self.wall_thickness = \
            Uncertainty.DeterministicCharacterization(name='wall_thickness',
                                                      value=convert_in_to_m(1))
        self.flaw_depth = \
            Uncertainty.DeterministicCharacterization(name='flaw_depth',
                                                      value=5)
        self.max_pressure = \
            Uncertainty.DeterministicCharacterization(name='max_pressure',
                                                      value=convert_ksi_to_mpa(2.5))
        self.min_pressure = \
            Uncertainty.DeterministicCharacterization(name='min_pressure',
                                                      value=convert_ksi_to_mpa(.2748))
        self.temperature = \
            Uncertainty.DeterministicCharacterization(name='temperature',
                                                      value=293)
        self.volume_fraction_h2 = \
            Uncertainty.DeterministicCharacterization(name='volume_fraction_h2',
                                                      value=0.5)
        self.yield_strength = \
            Uncertainty.DeterministicCharacterization(name='yield_strength',
                                                      value=670)
        self.fracture_resistance = \
            Uncertainty.DeterministicCharacterization(name='fracture_resistance',
                                                      value=40)
        self.flaw_length = \
            Uncertainty.DeterministicCharacterization(name='flaw_length',
                                                      value=0.001)
        self.unc_flaw_depth = \
            Uncertainty.NormalDistribution(name='flaw_depth',
                                           uncertainty_type='aleatory',
                                           nominal_value=self.flaw_depth.value,
                                           mean=5,
                                           std_deviation=1)
        self.unc_temperature = \
            Uncertainty.UniformDistribution(name='temperature',
                                            uncertainty_type='epistemic',
                                            nominal_value=self.temperature.value,
                                            upper_bound=300,
                                            lower_bound=290)
        self.unc_volume_fraction_h2 = \
            Uncertainty.UniformDistribution(name='volume_fraction_h2',
                                            uncertainty_type='aleatory',
                                            nominal_value=self.volume_fraction_h2.value,
                                            upper_bound=1,
                                            lower_bound=0)
        self.folder_path_deterministic = 'temp_deterministic/'
        self.folder_path_probabilistic = 'temp_probabilistic/'
        self.deterministic_study = \
            CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                   wall_thickness=self.wall_thickness,
                                   flaw_depth=self.flaw_depth,
                                   max_pressure=self.max_pressure,
                                   min_pressure=self.min_pressure,
                                   temperature=self.temperature,
                                   volume_fraction_h2=self.volume_fraction_h2,
                                   yield_strength=self.yield_strength,
                                   fracture_resistance=self.fracture_resistance,
                                   flaw_length=self.flaw_length)
        self.deterministic_study.perform_study()
        self.deterministic_results = self.deterministic_study
        probabilistic_study = \
            CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                   wall_thickness=self.wall_thickness,
                                   flaw_depth=self.unc_flaw_depth,
                                   max_pressure=self.max_pressure,
                                   min_pressure=self.min_pressure,
                                   temperature=self.unc_temperature,
                                   volume_fraction_h2=self.unc_volume_fraction_h2,
                                   yield_strength=self.yield_strength,
                                   fracture_resistance=self.fracture_resistance,
                                   flaw_length=self.flaw_length,
                                   epistemic_samples=2,
                                   aleatory_samples=2,
                                   sample_type='random')
        probabilistic_study.perform_study()
        self.probabilistic_results = probabilistic_study

        self.weld_thickness = 0.01
        self.weld_yield_strength = 360
        self.weld_flaw_distance = 0.06
        self.weld_flaw_direction = 'perpendicular'
        self.weld_steel = 'ferritic'
        self.weld_process = 'SMAW'

    def tearDown(self):
        """Teardown function."""

    def rm_tree(self, path):
        """Function to remove results save folder after unit test."""
        path = pl.Path(path)
        for child in path.glob('*'):
            if child.is_file():
                child.unlink()
            else:
                self.rm_tree(child)
        path.rmdir()

    def test_api_scalar_inputs(self):
        """Unit test for passing scaling inputs (deterministic evaluation) to api."""
        analysis_results = self.deterministic_results
        self.assertEqual(len(analysis_results.nominal_life_criteria['Cycles to 1/2 Nc'][1]), 1)
        analysis_results.postprocess_single_crack_results()
        analysis_results.gather_single_crack_cycle_evolution()
        assert True

    def test_api_uncertain_inputs(self):
        """Unit test for passing uncertain inputs to api."""
        analysis_results = self.probabilistic_results
        self.assertEqual(len(analysis_results.life_criteria['Cycles to 1/2 Nc'][1]), 4)

        analysis_results.postprocess_single_crack_results(single_pipe_index=3)
        analysis_results.gather_single_crack_cycle_evolution(single_pipe_index=2)
        assert True

    def test_api_deterministic_w_residual_stress(self):
        """Unit test for deterministic study with an explicitly given
           residual stress included in the inputs."""
        k_res = Uncertainty.DeterministicCharacterization(
            name='residual_stress_intensity_factor', value=12.)

        deterministic_study = CrackEvolutionAnalysis(
            outer_diameter=self.outer_diameter,
            wall_thickness=self.wall_thickness,
            flaw_depth=self.flaw_depth,
            max_pressure=self.max_pressure,
            min_pressure=self.min_pressure,
            temperature=self.temperature,
            volume_fraction_h2=self.volume_fraction_h2,
            yield_strength=self.yield_strength,
            fracture_resistance=self.fracture_resistance,
            flaw_length=self.flaw_length,
            residual_stress_intensity_factor=k_res)
        deterministic_study.perform_study()
        deterministic_study.postprocess_single_crack_results()
        deterministic_study.gather_single_crack_cycle_evolution()
        assert True

    def test_api_probabilistic_w_residual_stress(self):
        """Unit test for deterministic study with an explicitly given
           residual stress included in the inputs."""
        k_res = Uncertainty.NormalDistribution(
            name='residual_stress_intensity_factor',
            uncertainty_type='epistemic',
            nominal_value=12.,
            mean=12.,
            std_deviation=2)
        probabilistic_study = \
            CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                   wall_thickness=self.wall_thickness,
                                   flaw_depth=self.unc_flaw_depth,
                                   max_pressure=self.max_pressure,
                                   min_pressure=self.min_pressure,
                                   temperature=self.unc_temperature,
                                   volume_fraction_h2=self.volume_fraction_h2,
                                   yield_strength=self.yield_strength,
                                   fracture_resistance=self.fracture_resistance,
                                   flaw_length=self.flaw_length,
                                   aleatory_samples=2,
                                   epistemic_samples=2,
                                   sample_type='random',
                                   residual_stress_intensity_factor=k_res)
        probabilistic_study.perform_study()
        probabilistic_study.postprocess_single_crack_results(single_pipe_index=3)
        probabilistic_study.gather_single_crack_cycle_evolution(single_pipe_index=2)
        assert True

    def test_api_deterministic_w_weld(self):
        """Unit test for deterministic study with weld parameters
           included in the inputs."""
        weld_thickness = Uncertainty.DeterministicCharacterization(
            name='weld_thickness', value=self.weld_thickness)
        weld_yield_strength = Uncertainty.DeterministicCharacterization(
            name='weld_yield_strength', value=self.weld_yield_strength)
        weld_flaw_distance = Uncertainty.DeterministicCharacterization(
            name='weld_flaw_distance', value=self.weld_flaw_distance)
        deterministic_study = CrackEvolutionAnalysis(
            outer_diameter=self.outer_diameter,
            wall_thickness=self.wall_thickness,
            flaw_depth=self.flaw_depth,
            max_pressure=self.max_pressure,
            min_pressure=self.min_pressure,
            temperature=self.temperature,
            volume_fraction_h2=self.volume_fraction_h2,
            yield_strength=self.yield_strength,
            fracture_resistance=self.fracture_resistance,
            flaw_length=self.flaw_length,
            weld_thickness=weld_thickness,
            weld_yield_strength=weld_yield_strength,
            weld_flaw_distance=weld_flaw_distance,
            weld_flaw_direction=self.weld_flaw_direction,
            weld_steel=self.weld_steel,
            weld_process=self.weld_process)
        deterministic_study.perform_study()
        deterministic_study.postprocess_single_crack_results()
        deterministic_study.gather_single_crack_cycle_evolution()
        assert True

    def test_api_probabilistic_w_weld(self):
        """Unit test for deterministic study with weld parameters
           included in the inputs."""
        weld_thickness = Uncertainty.NormalDistribution(
            name='weld_thickness',
            uncertainty_type='epistemic',
            nominal_value=self.weld_thickness,
            mean=self.weld_thickness,
            std_deviation=0.002)
        weld_yield_strength = Uncertainty.BetaDistribution(
            name='weld_yield_strength',
            uncertainty_type='aleatory',
            nominal_value=self.weld_yield_strength,
            a=2,
            b=0.5,
            loc=360,
            scale=1)
        weld_flaw_distance = Uncertainty.UniformDistribution(
            name='weld_flaw_distance',
            uncertainty_type='aleatory',
            nominal_value=self.weld_flaw_distance,
            lower_bound=0.05,
            upper_bound=0.25)
        probabilistic_study = CrackEvolutionAnalysis(
            outer_diameter=self.outer_diameter,
            wall_thickness=self.wall_thickness,
            flaw_depth=self.flaw_depth,
            max_pressure=self.max_pressure,
            min_pressure=self.min_pressure,
            temperature=self.temperature,
            volume_fraction_h2=self.volume_fraction_h2,
            yield_strength=self.yield_strength,
            fracture_resistance=self.fracture_resistance,
            flaw_length=self.flaw_length,
            weld_thickness=weld_thickness,
            weld_yield_strength=weld_yield_strength,
            weld_flaw_distance=weld_flaw_distance,
            weld_flaw_direction=self.weld_flaw_direction,
            weld_steel=self.weld_steel,
            weld_process=self.weld_process,
            epistemic_samples=2,
            aleatory_samples=3,
            sample_type='random',)
        probabilistic_study.perform_study()
        probabilistic_study.postprocess_single_crack_results(single_pipe_index=3)
        probabilistic_study.gather_single_crack_cycle_evolution(single_pipe_index=2)
        assert True

    def test_api_bounding_sensitivity_study(self):
        """Unit test for specifying a bound value sensitivity study in api."""
        analysis = CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                          wall_thickness=self.wall_thickness,
                                          flaw_depth=self.unc_flaw_depth,
                                          max_pressure=self.max_pressure,
                                          min_pressure=self.min_pressure,
                                          temperature=self.unc_temperature,
                                          volume_fraction_h2=self.volume_fraction_h2,
                                          yield_strength=self.yield_strength,
                                          fracture_resistance=self.fracture_resistance,
                                          flaw_length=self.flaw_length,
                                          sample_type='bounding')
        analysis.perform_study()
        self.assertEqual(len(analysis.life_criteria['Cycles to 1/2 Nc'][1]), 2*2)
        analysis.postprocess_single_crack_results(single_pipe_index=2)
        assert True

    def test_api_lhs_sensitivity_study(self):
        """Unit test for specifying a bound value sensitivity study in api."""
        aleatory_samples = 2
        epistemic_samples = 2
        analysis = CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                          wall_thickness=self.wall_thickness,
                                          flaw_depth=self.unc_flaw_depth,
                                          max_pressure=self.max_pressure,
                                          min_pressure=self.min_pressure,
                                          temperature=self.unc_temperature,
                                          volume_fraction_h2=self.volume_fraction_h2,
                                          yield_strength=self.yield_strength,
                                          fracture_resistance=self.fracture_resistance,
                                          flaw_length=self.flaw_length,
                                          aleatory_samples=aleatory_samples,
                                          epistemic_samples=epistemic_samples,
                                          sample_type='sensitivity')
        analysis.perform_study()
        self.assertEqual(len(analysis.life_criteria['Cycles to 1/2 Nc'][1]),
                         aleatory_samples + epistemic_samples)
        analysis.postprocess_single_crack_results(single_pipe_index=2)
        assert True

    def test_bad_study_type_specification(self):
        """
        Unit test for specifying a bound value sensitivity study in api.
        
        Raises
        ------
        ValueError
            If the study type is not supported.
        """
        with self.assertRaises(ValueError):
            analysis = CrackEvolutionAnalysis(
                outer_diameter=self.outer_diameter,
                wall_thickness=self.wall_thickness,
                flaw_depth=self.unc_flaw_depth,
                max_pressure=self.max_pressure,
                min_pressure=self.min_pressure,
                temperature=self.temperature,
                volume_fraction_h2=self.volume_fraction_h2,
                yield_strength=self.yield_strength,
                fracture_resistance=self.fracture_resistance,
                flaw_length=self.flaw_length,
                aleatory_samples=2,
                sample_type='mc')
            analysis.perform_study()

    def test_set_resid_stress_params_w_explicit_resid_stress(self):
        """Unit test to check that the residual stress defaults to
           the explicit input argument if both an explicit K and a weld
           are given."""
        exp_kres = 30
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.deterministic_study._set_resid_stress_params(
                weld_thickness=self.weld_thickness,
                weld_yield_strength=self.weld_yield_strength,
                weld_flaw_distance=self.weld_flaw_distance,
                weld_flaw_direction=self.weld_flaw_direction,
                weld_steel=self.weld_steel,
                weld_process=self.weld_process,
                residual_stress_intensity_factor=exp_kres)
            
            self.assertTrue(self.deterministic_study.include_resid_stress)
            self.assertEqual(
                self.deterministic_study.input_parameters['residual_stress_intensity_factor'],
                exp_kres)
            self.assertTrue(
                any("Weld input arguments will be ignored"
                    in str(warn.message) for warn in w))
    
    def test_set_resid_stress_params_no_resid_stress(self):
        """Unit test to check that no residual stress is calculated if
           all weld inputs are None and explicit value is not provided."""
        self.deterministic_study._set_resid_stress_params(
            weld_thickness=None,
            weld_yield_strength=None,
            weld_flaw_distance=None,
            weld_flaw_direction=None,
            weld_steel=None,
            weld_process=None,
            residual_stress_intensity_factor=None)
        
        self.assertFalse(self.deterministic_study.include_resid_stress)
    
    def test_set_resid_stress_params_no_explicit_resid_stress(self):
        """Unit test to check that weld inputs are passed in properly
           if an explicit residual K is not provided."""
        self.deterministic_study._set_resid_stress_params(
            weld_thickness=self.weld_thickness,
            weld_yield_strength=self.weld_yield_strength,
            weld_flaw_distance=self.weld_flaw_distance,
            weld_flaw_direction=self.weld_flaw_direction,
            weld_steel=self.weld_steel,
            weld_process=self.weld_process,
            residual_stress_intensity_factor=None)
        
        self.assertTrue(self.deterministic_study.include_resid_stress)
        self.assertEqual(
            self.deterministic_study.input_parameters['weld_thickness'],
            self.weld_thickness)
        self.assertEqual(
            self.deterministic_study.input_parameters['weld_yield_strength'],
            self.weld_yield_strength)
        self.assertEqual(
            self.deterministic_study.input_parameters['weld_flaw_distance'],
            self.weld_flaw_distance)
        self.assertEqual(
            self.deterministic_study.weld_flaw_direction,
            self.weld_flaw_direction)
        self.assertEqual(
            self.deterministic_study.weld_steel,
            self.weld_steel)
        self.assertEqual(
            self.deterministic_study.weld_process,
            self.weld_process)
    
    def test_missing_weld_params_raises_type_error(self):
        """
        Unit test to check that a TypeError is raised when missing weld parameters are not provided.

        Raises
        ------
        TypeError
            If the weld parameters are not provided.
        """
        with self.assertRaises(TypeError):
            self.deterministic_study._set_resid_stress_params(
                weld_thickness=self.weld_thickness,
                weld_yield_strength=None,
                weld_flaw_distance=None,
                weld_flaw_direction=None,
                weld_steel=None,
                weld_process=self.weld_process,
                residual_stress_intensity_factor=None)
    
    def test_default_values_for_missing_optional_params(self):
        """Unit test to check that default values are used for missing optional parameters."""
        self.deterministic_study._set_resid_stress_params(
            weld_thickness=self.weld_thickness,
            weld_yield_strength=None,
            weld_flaw_distance=None,
            weld_flaw_direction=self.weld_flaw_direction,
            weld_steel=self.weld_steel,
            weld_process=self.weld_process,
            residual_stress_intensity_factor=None)
        
        self.assertIsInstance(
            self.deterministic_study.input_parameters['weld_yield_strength'],
            Uncertainty.DeterministicCharacterization)
        self.assertEqual(
            self.deterministic_study.input_parameters['weld_flaw_distance'].value,
            0)

    def test_api_nominal_evaluations(self):
        """Unit test for ensuring nominal probabilistic results match deterministic results."""
        uncertain_analysis_results = self.probabilistic_results
        deterministic_analysis_results = self.deterministic_results

        # check that the crack evolutions match
        self.assertTrue(uncertain_analysis_results.nominal_load_cycling[0]['a/t'] == \
                        deterministic_analysis_results.nominal_load_cycling[0]['a/t'])

        # check that the post processed QoIs match
        self.assertEqual(uncertain_analysis_results.nominal_life_criteria,
                         deterministic_analysis_results.nominal_life_criteria)

        # check that the input parameters match
        self.assertEqual(uncertain_analysis_results.nominal_input_parameter_values,
                         deterministic_analysis_results.nominal_input_parameter_values)

        # check that the deterministic analysis did not populate the sampling input parameter dict
        assert not bool(deterministic_analysis_results.sampling_input_parameter_values)

        # check that uncertain variable list is properly populated
        self.assertEqual(len(deterministic_analysis_results.uncertain_parameters), 0)
        self.assertEqual(len(uncertain_analysis_results.uncertain_parameters), 3)

        # check that intermediate variables are calculated as expected
        rounded_value = \
            round(deterministic_analysis_results.nominal_intermediate_variables['r_ratio'], 2)
        self.assertEqual(rounded_value, 0.11)
        rounded_value = \
            round(deterministic_analysis_results.nominal_intermediate_variables['%SMYS'], 2)
        self.assertEqual(rounded_value, 30.85)


    def test_specifying_random_seed(self):
        """Unit test to check ability to specify random seed."""
        random_seed = 1234
        analysis_1 = \
            CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                   wall_thickness=self.wall_thickness,
                                   flaw_depth=self.unc_flaw_depth,
                                   max_pressure=self.max_pressure,
                                   min_pressure=self.min_pressure,
                                   temperature=self.unc_temperature,
                                   volume_fraction_h2=self.unc_volume_fraction_h2,
                                   yield_strength=self.yield_strength,
                                   fracture_resistance=self.fracture_resistance,
                                   flaw_length=self.flaw_length,
                                   epistemic_samples=2,
                                   aleatory_samples=2,
                                   sample_type='random',
                                   random_seed=random_seed)
        analysis_1.perform_study()
        analysis_2 = \
            CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                   wall_thickness=self.wall_thickness,
                                   flaw_depth=self.unc_flaw_depth,
                                   max_pressure=self.max_pressure,
                                   min_pressure=self.min_pressure,
                                   temperature=self.unc_temperature,
                                   volume_fraction_h2=self.unc_volume_fraction_h2,
                                   yield_strength=self.yield_strength,
                                   fracture_resistance=self.fracture_resistance,
                                   flaw_length=self.flaw_length,
                                   epistemic_samples=2,
                                   aleatory_samples=2,
                                   sample_type='random',
                                   random_seed=random_seed)
        analysis_2.perform_study()

        for key, life_criteria in analysis_1.life_criteria.items():
            self.assertIsNone(self.assertListEqual(life_criteria, analysis_2.life_criteria[key]))

    def test_reload_random_seed(self):
        """Unit test to check ability to use previous random seed."""
        analysis_results_1 = self.probabilistic_results
        saved_random_seed_1 = analysis_results_1.get_random_seed()
        analysis_2 = \
            CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                   wall_thickness=self.wall_thickness,
                                   flaw_depth=self.unc_flaw_depth,
                                   max_pressure=self.max_pressure,
                                   min_pressure=self.min_pressure,
                                   temperature=self.unc_temperature,
                                   volume_fraction_h2=self.unc_volume_fraction_h2,
                                   yield_strength=self.yield_strength,
                                   fracture_resistance=self.fracture_resistance,
                                   flaw_length=self.flaw_length,
                                   epistemic_samples=2,
                                   aleatory_samples=2,
                                   sample_type='random',
                                   random_seed=saved_random_seed_1)
        saved_random_seed_2 = analysis_2.get_random_seed()

        self.assertEqual(saved_random_seed_1, saved_random_seed_2)

        analysis_2.perform_study()
        for key, life_criteria in analysis_results_1.life_criteria.items():
            self.assertIsNone(self.assertListEqual(life_criteria, analysis_2.life_criteria[key]))

    def assert_is_file(self, path):
        """
        Function to assert if file exists.
        
        Raises
        ------
        AssertionError
            If the file does not exist.
        """
        if not pl.Path(path).resolve().is_file():
            raise AssertionError(f"File does not exist: {path}")

    def test_save_deterministic_results(self):
        """Unit test to check deterministic result saving capability."""
        analysis_results = self.deterministic_results
        analysis_results.save_results(self.folder_path_deterministic)
        self.assert_is_file(self.folder_path_deterministic+'Nominal_Results.csv')
        self.rm_tree(self.folder_path_deterministic)

        file_path = analysis_results.save_results()
        self.assert_is_file(file_path+'Nominal_Results.csv')
        self.rm_tree(file_path)

        pl.Path('tmp').mkdir(parents=True, exist_ok=True)
        file_path = analysis_results.save_results(output_dir='tmp')
        self.assert_is_file(file_path+'Nominal_Results.csv')
        self.rm_tree(file_path)

    def test_save_probabilistic_results(self):
        """Unit test to check probabilistic result saving capability."""
        analysis_results = self.probabilistic_results
        analysis_results.save_results(self.folder_path_probabilistic)
        self.assert_is_file(self.folder_path_probabilistic+'A.csv')
        self.rm_tree(self.folder_path_probabilistic)

    def test_inspection_mitigation_results(self):
        """Unit test for applying inspection mitigation function to crack evolution results."""
        analysis_results = self.probabilistic_results
        mitigated = analysis_results.apply_inspection_mitigation(probability_of_detection=0.3,
                                                                 detection_resolution=0.5,
                                                                 inspection_frequency=365*4,
                                                                 criteria='Cycles to a(crit)')
        # TODO: Add check of file path and figure existence
        assert True

    def test_create_failure_assessment_diagram(self):
        """Unit test for creating failure assessment diagram."""
        analysis_results = self.deterministic_results
        analysis_results.assemble_failure_assessment_diagram()

        analysis_results = self.probabilistic_results
        analysis_results.assemble_failure_assessment_diagram()

        assert True

    def test_create_probabilistic_plots(self):
        """
        Unit test for creating probabilistic plots.
        
        Raises
        ------
        ValueError
            If the analysis results are not probabilistic.
        """
        analysis_results = self.probabilistic_results
        analysis_results.generate_probabilistic_results_plots(['Cycles to 1/2 Nc'])
        analysis_results.generate_probabilistic_results_plots('Cycles to 1/2 Nc')

        analysis_results = self.deterministic_results
        with self.assertRaises(ValueError):
            analysis_results.generate_probabilistic_results_plots(['Cycles to 1/2 Nc'])

    def test_create_input_parameter_plots(self):
        """Unit test for creating input parameter plots."""
        self.probabilistic_results.generate_input_parameter_plots()
        plt.close('all')
        self.deterministic_results.generate_input_parameter_plots()
        plt.close('all')

        assert True

    def test_incorrect_parameter_name(self):
        """
        Unit test for warning of incorrect parameter name.
        
        Raises
        ------
        ValueError
            If the parameter name is incorrect.
        """
        flaw_length = \
            Uncertainty.DeterministicCharacterization(name='flaw_shape',
                                                      value=0.001)
        with self.assertRaises(ValueError):
            CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                   wall_thickness=self.wall_thickness,
                                   flaw_depth=self.flaw_depth,
                                   max_pressure=self.max_pressure,
                                   min_pressure=self.min_pressure,
                                   temperature=self.temperature,
                                   volume_fraction_h2=self.volume_fraction_h2,
                                   yield_strength=self.yield_strength,
                                   fracture_resistance=self.fracture_resistance,
                                   flaw_length=flaw_length)

    def test_generating_intermediate_variables(self):
        """Unit test for generating intermediate variables (derived from input variables)."""
        self.assertTrue(isinstance(self.deterministic_results.nominal_intermediate_variables['%SMYS'],
                                   float))
        self.assertFalse(isinstance(self.deterministic_results.sampling_intermediate_variables,
                                    float))
        self.assertTrue(isinstance(self.probabilistic_results.nominal_intermediate_variables['%SMYS'],
                                   float))
        self.assertEqual(len(self.probabilistic_results.sampling_intermediate_variables['%SMYS']), 4)

    def test_print_intermediate_variables(self):
        """Unit test for printing nominal intermediate variables."""
        self.deterministic_results.print_nominal_intermediate_variables()
        assert True

    def test_perform_probabilistic_study_stopping(self):
        """Unit test to simulate stopping condition in perform_probabilistic_study."""
        analysis = CrackEvolutionAnalysis(
            outer_diameter=self.outer_diameter,
            wall_thickness=self.wall_thickness,
            flaw_depth=self.unc_flaw_depth,
            max_pressure=self.max_pressure,
            min_pressure=self.min_pressure,
            temperature=self.unc_temperature,
            volume_fraction_h2=self.unc_volume_fraction_h2,
            yield_strength=self.yield_strength,
            fracture_resistance=self.fracture_resistance,
            flaw_length=self.flaw_length,
            epistemic_samples=2,
            aleatory_samples=2,
            sample_type='random'
        )
        with patch('helpr.settings.is_stopping', return_value=True):
            analysis.perform_study()
            self.assertEqual(settings.RUN_STATUS, Status.STOPPED)

    def test_postprocess_assigns_plot_when_plot_result_is_valid(self):
        """Unit test to confirm plot assignments when plot_result is not None."""
        dummy_plot = "dummy_plot_path.png"
        dummy_data = {"x": [0, 1], "y": [0.1, 0.2]}

        with patch('helpr.api.generate_pipe_life_assessment_plot',
                return_value=(dummy_plot, dummy_data)):
            analysis_results = self.deterministic_results
            analysis_results.postprocess_single_crack_results()

            self.assertEqual(analysis_results.crack_growth_plot, dummy_plot)
            self.assertEqual(analysis_results.crack_growth_plot_data, dummy_data)


    def test_random_loading_incorrect_time_stepping(self):
        """
        Unit test for erroring when cycle step = 1 isn't selected for study
        using random loading profiles.
        
        Raises
        ------
        ValueError
            If the cycle_step specification isn't correct.
        """
        max_pressure = \
            Uncertainty.TimeSeriesCharacterization(name='max_pressure',
                                                   value=[2, 2, 2])
        min_pressure = \
            Uncertainty.TimeSeriesCharacterization(name='min_pressure',
                                                   value=[1, 1, 1])

        with self.assertRaises(ValueError):
            CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                   wall_thickness=self.wall_thickness,
                                   flaw_depth=self.flaw_depth,
                                   max_pressure=max_pressure,
                                   min_pressure=min_pressure,
                                   temperature=self.temperature,
                                   volume_fraction_h2=self.volume_fraction_h2,
                                   yield_strength=self.yield_strength,
                                   fracture_resistance=self.fracture_resistance,
                                   flaw_length=self.flaw_length)

    def test_random_loading(self):
        """
        Unit test for using random load profiles
        
        Raises
        ------
        ValueError
            If the cycle_step specification isn't correct.
        """
        max_pressure = \
            Uncertainty.TimeSeriesCharacterization(name='max_pressure',
                                                   value=[17.2, 17.1, 17.3])
        min_pressure = \
            Uncertainty.TimeSeriesCharacterization(name='min_pressure',
                                                   value=[1.89, 1.9, 1.88])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            analysis = \
                CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                    wall_thickness=self.wall_thickness,
                                    flaw_depth=self.flaw_depth,
                                    max_pressure=max_pressure,
                                    min_pressure=min_pressure,
                                    temperature=self.temperature,
                                    volume_fraction_h2=self.volume_fraction_h2,
                                    yield_strength=self.yield_strength,
                                    fracture_resistance=self.fracture_resistance,
                                    flaw_length=self.flaw_length,
                                    cycle_step=1)
            analysis.perform_study()
            _, _ = analysis.assemble_failure_assessment_diagram()
            
            self.assertTrue(
                any('Extraction of FAD intersection QoI when using user specified random loading '
                    + 'profile may be incorrect due to its stochastic nature.'
                    in str(warn.message) for warn in w))

if __name__ == '__main__':
    unittest.main()
