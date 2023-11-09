# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
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
                                            

class PlotsTestCase(unittest.TestCase):
    """class for plotting functions"""
    def setUp(self):
        """function to specify common inputs to plot functions"""
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
        analysis = CrackEvolutionAnalysis(outer_diameter=outer_diameter,
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
                                          sample_type=sample_type)
        analysis.perform_study()
        self.example_results = analysis
        self.single_life_criteria_result = \
            report_single_pipe_life_criteria_results(self.example_results.life_criteria, 0)
        self.single_load_cycling = \
            report_single_cycle_evolution(self.example_results.load_cycling, 0)

    def test_pipe_life_assessment_plot(self):
        """test for creation of life assessment plot for single pipe"""
        generate_pipe_life_assessment_plot(self.single_load_cycling,
                                           self.single_life_criteria_result,
                                           'Test Pipe')
        plt.close()
        assert True

    def test_life_assessment_ensemble_plot(self):
        """test for creation of life assessment plot for pipe ensemble"""
        plot_pipe_life_ensemble(self.example_results,
                                self.plotted_variable)
        plt.close()
        assert True


    def test_crack_growth_rate_plot(self):
        """test for creation of crack growth rate plot"""
        generate_crack_growth_rate_plot(self.single_load_cycling)
        plt.close()
        assert True

    def test_cycle_life_cdfs(self):
        """test for creation of life criteria cdfs plot"""
        plot_cycle_life_cdfs(self.example_results,
                             self.plotted_variable)
        plt.close()
        assert True

    def test_cycle_life_cdf_ci(self):
        """test for creation of life criteria cdf confidence intervals plot"""
        plot_cycle_life_cdf_ci(self.example_results,
                               self.plotted_variable)
        plt.close()
        assert True

    def test_cycle_life_pdf(self):
        """test for creation of life criteria pdfs plot"""
        plot_cycle_life_pdfs(self.example_results,
                             self.plotted_variable)
        plt.close()
        assert True

    def test_cycle_life_critieria_scatter_plot(self):
        """test for creation of life criteria scatter plot"""
        plot_cycle_life_criteria_scatter(self.example_results,
                                         self.plotted_variable,
                                         False)
        plot_cycle_life_criteria_scatter(self.example_results,
                                         self.plotted_variable,
                                         True)
        plt.close()
        assert True

    def test_sensitivity_results_plot(self):
        """test for creation of sensitivity plot"""
        plot_sensitivity_results(self.example_results,
                                 self.plotted_variable)
        plt.close()
        assert True

    def test_failure_assessment_diagram(self):
        """test for creation of failure assessment diagram"""
        calculate_failure_assessment(self.example_results.nominal_input_parameter_values,
                                     self.example_results.nominal_load_cycling,
                                     self.example_results.nominal_stress_state)
        calculate_failure_assessment(self.example_results.sampling_input_parameter_values,
                                     self.example_results.load_cycling,
                                     self.example_results.stress_state)
        plot_failure_assessment_diagram(self.example_results.load_cycling,
                                        self.example_results.nominal_load_cycling)
        plt.close()
        assert True

    def test_inspection_mitigation_plots(self):
        """test for creation of inspection mitigation plots"""
        probability_of_detection = 0.8  # 80%
        detection_resolution = 0.3  # able to detect cracks greater than 30% through
        inspection_interval = 4  # how many years between inspections
        inspection_frequency = 365*inspection_interval  # inspections in terms of cycles
        criteria='Cycles to a(crit)'

        _ = \
            self.example_results.apply_inspection_mitigation(probability_of_detection,
                                                             detection_resolution,
                                                             inspection_frequency,
                                                             criteria)
        plt.close()
        assert True
