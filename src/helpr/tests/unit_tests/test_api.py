# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import pathlib as pl
import pandas as pd
import numpy as np

import probabilistic.capabilities.uncertainty_definitions as Uncertainty
from helpr.utilities.unit_conversion import convert_in_to_m, convert_ksi_to_mpa
from helpr.physics.api import CrackEvolutionAnalysis

class APITestCase(unittest.TestCase):
    """Class for unit tests of api module"""
    def setUp(self):
        """function to specify common inputs to api module"""
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
        self.folder_path = 'temp/'
        deterministic_study = \
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
        deterministic_study.perform_study()
        self.deterministic_results = deterministic_study
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

    def tearDown(self):
        """teardown function"""

    def rm_tree(self, path):
        """function to remove results save folder after unit test"""
        path = pl.Path(path)
        for child in path.glob('*'):
            if child.is_file():
                child.unlink()
            else:
                self.rm_tree(child)
        path.rmdir()

    def test_api_scalar_inputs(self):
        """unit test for passing scaling inputs (deterministic evaluation) to api"""
        analysis_results = self.deterministic_results
        self.assertEqual(len(analysis_results.nominal_life_criteria['Cycles to 1/2 Nc'][1]), 1)
        analysis_results.postprocess_single_crack_results()
        assert True

    def test_api_uncertain_inputs(self):
        """unit test for passing uncertain inputs to api"""
        analysis_results = self.probabilistic_results
        self.assertEqual(len(analysis_results.life_criteria['Cycles to 1/2 Nc'][1]), 4)

        analysis_results.postprocess_single_crack_results(single_pipe_index=3)
        analysis_results.gather_single_crack_cycle_evolution(single_pipe_index=2)
        assert True

    def test_api_bounding_sensitivity_study(self):
        """unit test for specifying a bound value sensitivity study in api"""
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
        """unit test for specifying a bound value sensitivity study in api"""
        aleatory_samples = 5
        epistemic_samples = 5
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
        """unit test for specifying a bound value sensitivity study in api"""
        with self.assertRaises(ValueError):
            analysis = CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                              wall_thickness=self.wall_thickness,
                                              flaw_depth=self.unc_flaw_depth,
                                              max_pressure=self.max_pressure,
                                              min_pressure=self.min_pressure,
                                              temperature=self.temperature,
                                              volume_fraction_h2=self.volume_fraction_h2,
                                              yield_strength=self.yield_strength,
                                              fracture_resistance=self.fracture_resistance,
                                              flaw_length=self.flaw_length,
                                              aleatory_samples=5,
                                              sample_type='mc')
            analysis.perform_study()

    def test_api_nominal_evaluations(self):
        """unit test for ensuring nominal probabilistic results match deterministic results"""
        uncertain_analysis_results = self.probabilistic_results
        deterministic_analysis_results = self.deterministic_results

        # check that the crack evolutions match
        assert pd.DataFrame.equals(uncertain_analysis_results.nominal_load_cycling['a/t'],
                                   deterministic_analysis_results.nominal_load_cycling['a/t'])

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

    def test_specifying_random_seed(self):
        """unit test to check ability to specify random seed"""
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
            self.assertIsNone(np.testing.assert_array_equal(life_criteria,
                                                            analysis_2.life_criteria[key]))

    def test_reload_random_seed(self):
        """unit test to check ability to use previous random seed"""
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
            self.assertIsNone(np.testing.assert_array_equal(life_criteria,
                                                            analysis_2.life_criteria[key]))

    def assert_is_file(self, path):
        """function to assert if file exists"""
        if not pl.Path(path).resolve().is_file():
            raise AssertionError(f"File does not exist: {path}")

    def test_save_deterministic_results(self):
        """unit test to check deterministic result saving capability"""
        analysis_results = self.deterministic_results
        analysis_results.save_results(self.folder_path)
        self.assert_is_file(self.folder_path+'A.csv')
        self.rm_tree(self.folder_path)

        file_path = analysis_results.save_results()
        self.assert_is_file(file_path+'A.csv')
        self.rm_tree(file_path)

    def test_save_probabilistic_results(self):
        """unit test to check probabilistic result saving capability"""
        analysis_results = self.probabilistic_results
        analysis_results.save_results(self.folder_path)
        self.assert_is_file(self.folder_path+'A.csv')
        self.rm_tree(self.folder_path)

    def test_inspection_mitigation_results(self):
        """unit test for applying inspection mitigation function to crack evolution results"""
        # TODO: should add test to ensure reproducibility of capability
        analysis_results = self.probabilistic_results
        mitigated = analysis_results.apply_inspection_mitigation(probability_of_detection=0.3,
                                                                 detection_resolution=0.5,
                                                                 inspection_frequency=365*4,
                                                                 criteria='Cycles to a(crit)')
        self.assertEqual(len(mitigated), 4)

    def test_create_failure_assessment_diagram(self):
        """unit test for creating failure assessment diagram"""
        analysis_results = self.deterministic_results
        analysis_results.assemble_failure_assessment_diagram()

        analysis_results = self.probabilistic_results
        analysis_results.assemble_failure_assessment_diagram()

        assert True

    def test_create_probabilistic_plots(self):
        """unit test for creating probabilistic plots"""
        analysis_results = self.probabilistic_results
        analysis_results.generate_probabilistic_results_plots('Cycles to 1/2 Nc')

        analysis_results = self.deterministic_results
        with self.assertRaises(ValueError):
            analysis_results.generate_probabilistic_results_plots('Cycles to 1/2 Nc')

    def test_incorrect_parameter_name(self):
        """unit test for warning of incorrect parameter name"""
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

if __name__ == '__main__':
    unittest.main()
