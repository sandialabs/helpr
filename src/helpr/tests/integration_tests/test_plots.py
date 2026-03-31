# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np

import probabilistic.capabilities.uncertainty_definitions as Uncertainty

from helpr.utilities.plots import (generate_pipe_life_assessment_plot,
                                   plot_pipe_life_ensemble,
                                   generate_crack_growth_rate_plot,
                                   plot_cycle_life_cdfs,
                                   plot_cycle_life_cdf_ci,
                                   plot_cycle_life_pdfs,
                                   plot_cycle_life_criteria_scatter,
                                   plot_sensitivity_results,
                                   plot_failure_assessment_diagram,
                                   plot_random_loading_profiles)
from helpr.api import CrackEvolutionAnalysis
from helpr.physics.fracture import calculate_failure_assessment
from helpr.utilities.postprocessing import (report_single_pipe_life_criteria_results,
                                            report_single_cycle_evolution)
from helpr import settings

class PlotsTestCaseBase(unittest.TestCase):
    """Base class plotting unit test that check if file exists."""

    def assert_is_file(self, path):
        """
        Function to check if a file exists.
        
        Raises
        ------
        AssertionError
            If the file does not exist.
        """
        if not Path(path).resolve().is_file():
            raise AssertionError(f'File does not exist: {str(path)}')

        assert True


class PlotsTestCase(PlotsTestCaseBase):
    """
    Class for plotting functions.
    
    Attributes
    ----------
    fig_dir : str
        The directory where figures will be saved.
    plotted_variable : str
        The variable that will be plotted.
    example_results_anderson : CrackEvolutionAnalysis
        The results of a crack evolution analysis using the Anderson stress intensity method.
    example_results_api : CrackEvolutionAnalysis
        The results of a crack evolution analysis using the API stress intensity method.
    single_life_criteria_result : dict
        The life criteria for a single pipe.
    single_load_cycling : dict
        The load cycling data for a single pipe.
    """

    def setUp(self):
        """Function to specify common inputs to plot functions."""
        self.fig_dir = tempfile.mkdtemp()
        settings.OUTPUT_DIR = self.fig_dir
        outer_diameter = \
            Uncertainty.DeterministicCharacterization(name='outer_diameter',
                                                      value=0.9144)
        wall_thickness = \
            Uncertainty.DeterministicCharacterization(name='wall_thickness',
                                                      value=0.0102)
        yield_strength = \
            Uncertainty.DeterministicCharacterization(name='yield_strength',
                                                      value=358)
        fracture_resistance = \
            Uncertainty.NormalDistribution(name='fracture_resistance',
                                           uncertainty_type='epistemic',
                                           nominal_value=55,
                                           mean=55,
                                           std_deviation=2)
        max_pressure = \
            Uncertainty.NormalDistribution(name='max_pressure',
                                           uncertainty_type='aleatory',
                                           nominal_value=5.857,
                                           mean=5.857,
                                           std_deviation=.07)
        min_pressure = \
            Uncertainty.DeterministicCharacterization(name='min_pressure',
                                                      value=4.4)
        temperature = \
            Uncertainty.DeterministicCharacterization(name='temperature',
                                                      value=293)
        volume_fraction_h2 = \
            Uncertainty.DeterministicCharacterization(name='volume_fraction_h2',
                                                      value=1)
        flaw_depth = \
            Uncertainty.DeterministicCharacterization(name='flaw_depth',
                                                      value=25)
        flaw_length = \
            Uncertainty.DeterministicCharacterization(name='flaw_length',
                                                      value=0.04)
        self.plotted_variable = ['Cycles to a(crit)', 'Cycles to FAD line']
        self.fad_type = 'simple'
        sample_type = 'lhs'
        sample_size = 5
        analysis_anderson = CrackEvolutionAnalysis(outer_diameter=outer_diameter,
                                          wall_thickness=wall_thickness,
                                          flaw_depth=flaw_depth,
                                          max_pressure=max_pressure,
                                          min_pressure=min_pressure,
                                          temperature=temperature,
                                          volume_fraction_h2=volume_fraction_h2,
                                          yield_strength=yield_strength,
                                          fracture_resistance=fracture_resistance,
                                          flaw_length=flaw_length,
                                          aleatory_samples=sample_size,
                                          epistemic_samples=sample_size,
                                          sample_type=sample_type,
                                          stress_intensity_method='anderson')
        analysis_anderson.perform_study()
        self.example_results_anderson = analysis_anderson
        analysis_api = CrackEvolutionAnalysis(outer_diameter=outer_diameter,
                                          wall_thickness=wall_thickness,
                                          flaw_depth=flaw_depth,
                                          max_pressure=max_pressure,
                                          min_pressure=min_pressure,
                                          temperature=temperature,
                                          volume_fraction_h2=volume_fraction_h2,
                                          yield_strength=yield_strength,
                                          fracture_resistance=fracture_resistance,
                                          flaw_length=flaw_length,
                                          aleatory_samples=sample_size,
                                          epistemic_samples=sample_size,
                                          sample_type=sample_type,
                                          stress_intensity_method='api')
        analysis_api.perform_study()
        self.example_results_api = analysis_api
        self.single_life_criteria_result = \
            report_single_pipe_life_criteria_results(self.example_results_anderson.life_criteria, 0)
        self.single_load_cycling = \
            report_single_cycle_evolution(self.example_results_anderson.load_cycling, 0)

    def tearDown(self):
        """Function to clean up after each test."""
        shutil.rmtree(self.fig_dir)

    def test_pipe_life_assessment_plot(self):
        """Test for creation of life assessment plot for single instance."""
        fig_path, _ = generate_pipe_life_assessment_plot(
            life_assessment=self.single_load_cycling,
            postprocessed_criteria=self.single_life_criteria_result,
            criteria=['Cycles to a(crit)'],
            pipe_name='Test Pipe',
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'Test_Pipe_lifeassessment_.+.png')
        self.assert_is_file(fig_path)

    def test_life_assessment_ensemble_plot(self):
        """Test for creation of life assessment plot for pipe ensemble."""
        fig_path, _ = plot_pipe_life_ensemble(self.example_results_anderson,
                                              self.plotted_variable,
                                              save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'prob_crack_evolution_ensemble_.+.png')
        self.assert_is_file(fig_path)

    def test_crack_growth_rate_plot(self):
        """Test for creation of crack growth rate plot."""
        fig_path = generate_crack_growth_rate_plot(self.single_load_cycling,
                                                   save_fig=True)
        plt.close()
        self.assertIsNotNone(fig_path)  # ensure the path is returned
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'crack_growth_rate_.+.png')
        self.assert_is_file(fig_path)


    def test_cycle_life_cdfs(self):
        """Test for creation of life criteria cdfs plot."""
        fig_path, _ = plot_cycle_life_cdfs(self.example_results_anderson,
                                              self.plotted_variable,
                                              save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'prob_critical_crack_cdf_.+.png')
        self.assert_is_file(fig_path)

    def test_cycle_life_cdf_ci(self):
        """Test for creation of life criteria cdf confidence intervals plot."""
        plot_cycle_life_cdf_ci(self.example_results_anderson,
                               self.plotted_variable)
        plt.close()
        assert True

    def test_cycle_life_pdf(self):
        """Test for creation of life criteria pdfs plot."""
        fig_path, _ = plot_cycle_life_pdfs(self.example_results_anderson,
                                           self.plotted_variable,
                                           save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path[0])
        self.assertRegex(fig_file, 'prob_critical_crack_pdf_.+.png')
        self.assert_is_file(fig_path[0])

    def test_cycle_life_criteria_scatter_plot_no_color_by_variable(self):
        """Test for creation of life criteria scatter plot without changing
           colors by variable."""
        fig_path, _ = plot_cycle_life_criteria_scatter(
            self.example_results_anderson,
            self.plotted_variable,
            color_by_variable=False,
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path[0])
        self.assertRegex(fig_file, 'prob_critical_crack_scatter_qoi_0_.+.png')
        self.assert_is_file(fig_path[0])

    def test_cycle_life_criteria_scatter_plot_color_by_variable(self):
        """Test for creation of life criteria scatter plot with changing
           colors by variable."""
        fig_paths, _ = plot_cycle_life_criteria_scatter(
            self.example_results_anderson,
            self.plotted_variable,
            color_by_variable=True,
            save_fig=True)
        plt.close('all')
        fig_files = [os.path.basename(path) for path in fig_paths]
        # updated to 4 from 2 as 2 QoIs are now included
        self.assertEqual(len(fig_files), 4)
        # [self.assertRegex(
        #     file, f'prob_critical_crack_scatter_colorbyvariable_{i}_qoi_0'+'.png')
        #     for i, file in enumerate(fig_files)]
        # [self.assert_is_file(file) for file in fig_paths]

    def test_sensitivity_results_plot(self):
        """Test for creation of sensitivity plot."""
        fig_path, _ = plot_sensitivity_results(
            self.example_results_anderson,
            self.plotted_variable,
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path[0])
        self.assertRegex(fig_file, 'sensitivity_.+.png')
        self.assert_is_file(fig_path[0])

        result = plot_sensitivity_results(
            self.example_results_anderson,
            self.plotted_variable,
            save_fig=False)
        self.assertEqual(result, (None, None))

    def test_failure_assessment_diagram_anderson(self):
        """Test for creation of failure assessment diagram using the Anderson
           stress intensity method."""
        calculate_failure_assessment(
            self.example_results_anderson.nominal_input_parameter_values,
            self.example_results_anderson.nominal_load_cycling,
            self.example_results_anderson.nominal_analysis_modules['stress'],
            self.fad_type)
        calculate_failure_assessment(
            self.example_results_anderson.sampling_input_parameter_values,
            self.example_results_anderson.load_cycling,
            self.example_results_anderson.uncertain_analysis_modules['stress'],
            self.fad_type)
        fig_path, _ = plot_failure_assessment_diagram(
            self.example_results_anderson.load_cycling,
            self.example_results_anderson.life_criteria,
            self.fad_type,
            self.example_results_anderson.nominal_load_cycling,
            self.example_results_anderson.nominal_life_criteria,
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'failure_assmt_.+.png')
        self.assert_is_file(fig_path)

    def test_failure_assessment_diagram_api(self):
        """Test for creation of failure assessment diagram using the API
           stress intensity method."""
        calculate_failure_assessment(
            self.example_results_api.nominal_input_parameter_values,
            self.example_results_api.nominal_load_cycling,
            self.example_results_api.nominal_analysis_modules['stress'],
            self.fad_type)
        calculate_failure_assessment(
            self.example_results_api.sampling_input_parameter_values,
            self.example_results_api.load_cycling,
            self.example_results_api.uncertain_analysis_modules['stress'],
            self.fad_type)
        fig_path, _ = plot_failure_assessment_diagram(
            self.example_results_api.load_cycling,
            self.example_results_api.life_criteria,
            'API 579-1 Level 2',
            self.example_results_api.nominal_load_cycling,
            self.example_results_api.nominal_life_criteria,
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'failure_assmt_.+.png')
        self.assert_is_file(fig_path)

    def test_inspection_mitigation_plots(self):
        """Test for creation of inspection mitigation plots."""
        probability_of_detection = 0.8  # 80%
        detection_resolution = 0.3  # able to detect cracks greater than 30% through
        inspection_interval = 4  # how many years between inspections
        inspection_frequency = 365*inspection_interval  # inspections in terms of cycles
        criteria='Cycles to a(crit)'

        fig_paths, _ = \
            self.example_results_anderson.apply_inspection_mitigation(probability_of_detection,
                                                             detection_resolution,
                                                             inspection_frequency,
                                                             criteria,
                                                             save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_paths[0])
        self.assertRegex(fig_file, 'inspection_mitigation_hist_.+.png')
        self.assert_is_file(fig_paths[0])

        fig_file = os.path.basename(fig_paths[1])
        self.assertRegex(fig_file, 'inspection_mitigation_cdf_.+.png')
        self.assert_is_file(fig_paths[1])
        assert True

    def test_design_curve_plot(self):
        """Test for creation of design curve plot."""
        self.example_results_anderson.postprocess_single_crack_results()
        fig_path, _ = self.example_results_anderson.get_design_curve_plot()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'design_curve_.+.png')
        self.assert_is_file(fig_path)
        plt.close()


    def test_plot_random_loading_profiles_save_fig_true(self):
        minimum_pressure = [1, 2, 3]
        maximum_pressure = [4, 5, 6]
        pressure_units = 'MPa'
        cycle_description = 'Cycle [#]'
        save_fig = True

        with patch('helpr.utilities.plots._save_fig') as mock_save_fig, patch('helpr.utilities.plots._get_plot_data') as mock_get_plot_data:
            mock_save_fig.return_value = 'file_path'
            mock_get_plot_data.return_value = [np.array([1, 2, 3])]

            result = plot_random_loading_profiles(minimum_pressure,
                                                  maximum_pressure,
                                                  pressure_units,
                                                  cycle_description,
                                                  save_fig)
            self.assertEqual(result[0], 'file_path')
            self.assertTrue(np.array_equal(result[1][0], np.array([1, 2, 3])))
            # self.assertEqual(result, ('file_path', [np.array([1, 2, 3])]))

    def test_plot_random_loading_profiles_save_fig_false(self):
        minimum_pressure = [1, 2, 3]
        maximum_pressure = [4, 5, 6]
        pressure_units = 'MPa'
        cycle_description = 'Cycle [#]'
        save_fig = False

        result = plot_random_loading_profiles(minimum_pressure,
                                              maximum_pressure,
                                              pressure_units,
                                              cycle_description,
                                              save_fig)
        self.assertEqual(result, (None, None))

    def test_plot_random_loading_profiles_invalid_input(self):
        minimum_pressure = 'invalid'
        maximum_pressure = [4, 5, 6]
        pressure_units = 'MPa'
        cycle_description = 'Cycle [#]'
        save_fig = True

        with self.assertRaises(TypeError):
            plot_random_loading_profiles(minimum_pressure,
                                         maximum_pressure,
                                         pressure_units,
                                         cycle_description,
                                         save_fig)

    def test_plot_random_loading_profiles_unequal_input(self):
        minimum_pressure = [1, 2, 3]
        maximum_pressure = [4, 5]
        pressure_units = 'MPa'
        cycle_description = 'Cycle [#]'
        save_fig = True

        with self.assertRaises(ValueError):
            plot_random_loading_profiles(minimum_pressure,
                                         maximum_pressure,
                                         pressure_units,
                                         cycle_description,
                                         save_fig)

    def test_plot_random_loading_profiles_zero_division(self):
        minimum_pressure = [1, 2, 3]
        maximum_pressure = [4, 0, 6]
        pressure_units = 'MPa'
        cycle_description = 'Cycle [#]'
        save_fig = True

        with self.assertRaises(ZeroDivisionError):
            plot_random_loading_profiles(minimum_pressure,
                                         maximum_pressure,
                                         pressure_units,
                                         cycle_description,
                                         save_fig)


if __name__ == '__main__':
    unittest.main()
