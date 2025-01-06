# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import tempfile
import shutil
import os
from pathlib import Path

import matplotlib.pyplot as plt

import probabilistic.capabilities.uncertainty_definitions as Uncertainty

from helpr.utilities.plots import (generate_pipe_life_assessment_plot,
                                   plot_pipe_life_ensemble,
                                   generate_crack_growth_rate_plot,
                                   plot_cycle_life_cdfs,
                                   plot_cycle_life_cdf_ci,
                                   plot_cycle_life_pdfs,
                                   plot_cycle_life_criteria_scatter,
                                   plot_sensitivity_results,
                                   plot_failure_assessment_diagram)
from helpr.physics.api import CrackEvolutionAnalysis
from helpr.utilities.postprocessing import (report_single_pipe_life_criteria_results,
                                            report_single_cycle_evolution,
                                            calculate_failure_assessment)
from helpr import settings


class PlotsTestCaseBase(unittest.TestCase):
    """base class plotting unit test that check if file exists"""
    def assert_is_file(self, path):
        """function to check if a file exists"""
        if not Path(path).resolve().is_file():
            raise AssertionError(f'File does not exist: {str(path)}')

        assert True


class PlotsTestCase(PlotsTestCaseBase):
    """class for plotting functions"""
    def setUp(self):
        """function to specify common inputs to plot functions"""
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
        self.plotted_variable = 'Cycles to a(crit)'
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
        shutil.rmtree(self.fig_dir)

    def test_pipe_life_assessment_plot(self):
        """test for creation of lfe assessment plot for single instance"""
        fig_path, _ = generate_pipe_life_assessment_plot(
            self.single_load_cycling,
            self.single_life_criteria_result,
            'Test Pipe',
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'Test_Pipe_lifeassessment_.+.png')
        self.assert_is_file(fig_path)

    def test_life_assessment_ensemble_plot(self):
        """test for creation of life assessment plot for pipe ensemble"""
        fig_path, _ = plot_pipe_life_ensemble(self.example_results_anderson,
                                              self.plotted_variable,
                                              save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'prob_crack_evolution_ensemble_.+.png')
        self.assert_is_file(fig_path)

    def test_crack_growth_rate_plot(self):
        """test for creation of crack growth rate plot"""
        fig_path = generate_crack_growth_rate_plot(self.single_load_cycling,
                                                   save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'crack_growth_rate_.+.png')
        self.assert_is_file(fig_path)

    def test_cycle_life_cdfs(self):
        """test for creation of life criteria cdfs plot"""
        fig_path, _ = plot_cycle_life_cdfs(self.example_results_anderson,
                                              self.plotted_variable,
                                              save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'prob_critical_crack_cdf_.+.png')
        self.assert_is_file(fig_path)

    def test_cycle_life_cdf_ci(self):
        """test for creation of life criteria cdf confidence intervals plot"""
        plot_cycle_life_cdf_ci(self.example_results_anderson,
                               self.plotted_variable)
        plt.close()
        assert True

    def test_cycle_life_pdf(self):
        """test for creation of life criteria pdfs plot"""
        fig_path, _ = plot_cycle_life_pdfs(self.example_results_anderson,
                                           self.plotted_variable,
                                           save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'prob_critical_crack_pdf_.+.png')
        self.assert_is_file(fig_path)

    def test_cycle_life_criteria_scatter_plot_no_color_by_variable(self):
        """test for creation of life criteria scatter plot without changing
        colors by variable
        """
        fig_path, _ = plot_cycle_life_criteria_scatter(
            self.example_results_anderson,
            self.plotted_variable,
            color_by_variable=False,
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'prob_critical_crack_scatter_.+.png')
        self.assert_is_file(fig_path)
        
    def test_cycle_life_criteria_scatter_plot_color_by_variable(self):
        """test for creation of life criteria scatter plot with changing
        colors by variable
        """
        fig_paths = plot_cycle_life_criteria_scatter(
            self.example_results_anderson,
            self.plotted_variable,
            color_by_variable=True,
            save_fig=True)
        plt.close()
        fig_files = [os.path.basename(path) for path in fig_paths]
        self.assertEqual(len(fig_files), 2)
        [self.assertRegex(
            file, f'prob_critical_crack_scatter_colorbyvariable{i}_.+.png')
            for i, file in enumerate(fig_files)]
        [self.assert_is_file(file) for file in fig_paths]

    def test_sensitivity_results_plot(self):
        """test for creation of sensitivity plot"""
        fig_path, _ = plot_sensitivity_results(
            self.example_results_anderson,
            self.plotted_variable,
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'sensitivity_.+.png')
        self.assert_is_file(fig_path)

    def test_failure_assessment_diagram_anderson(self):
        """test for creation of failure assessment diagram using the Anderson
        stress intensity method."""
        calculate_failure_assessment(
            self.example_results_anderson.nominal_input_parameter_values,
            self.example_results_anderson.nominal_load_cycling,
            self.example_results_anderson.nominal_stress_state,
            self.example_results_anderson.stress_intensity_method)
        calculate_failure_assessment(
            self.example_results_anderson.sampling_input_parameter_values,
            self.example_results_anderson.load_cycling,
            self.example_results_anderson.stress_state,
            self.example_results_anderson.stress_intensity_method)
        fig_path, _ = plot_failure_assessment_diagram(
            self.example_results_anderson.load_cycling,
            self.example_results_anderson.nominal_load_cycling,
            save_fig=True)
        plt.close()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'failure_assmt_.+.png')
        self.assert_is_file(fig_path)

    def test_failure_assessment_diagram_api(self):
        """test for creation of failure assessment diagram using the API
        stress intensity method."""
        calculate_failure_assessment(
            self.example_results_api.nominal_input_parameter_values,
            self.example_results_api.nominal_load_cycling,
            self.example_results_api.nominal_stress_state,
            self.example_results_api.stress_intensity_method)
        calculate_failure_assessment(
            self.example_results_api.sampling_input_parameter_values,
            self.example_results_api.load_cycling,
            self.example_results_api.stress_state,
            self.example_results_api.stress_intensity_method)
        fig_path, _ = plot_failure_assessment_diagram(
            self.example_results_api.load_cycling,
            self.example_results_api.nominal_load_cycling,
            save_fig=True)
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'failure_assmt_.+.png')
        self.assert_is_file(fig_path)
        assert True

    def test_inspection_mitigation_plots(self):
        """test for creation of inspection mitigation plots"""
        probability_of_detection = 0.8  # 80%
        detection_resolution = 0.3  # able to detect cracks greater than 30% through
        inspection_interval = 4  # how many years between inspections
        inspection_frequency = 365*inspection_interval  # inspections in terms of cycles
        criteria='Cycles to a(crit)'

        _ = \
            self.example_results_anderson.apply_inspection_mitigation(probability_of_detection,
                                                             detection_resolution,
                                                             inspection_frequency,
                                                             criteria)
        plt.close()
        assert True

    def test_design_curve_plot(self):
        """test for creation of design curve plot"""
        self.example_results_anderson.postprocess_single_crack_results()
        fig_path, _ = self.example_results_anderson.get_design_curve_plot()
        fig_file = os.path.basename(fig_path)
        self.assertRegex(fig_file, 'design_curve_.+.png')
        self.assert_is_file(fig_path)
