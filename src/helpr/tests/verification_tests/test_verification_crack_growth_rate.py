# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import probabilistic.capabilities.uncertainty_definitions as Uncertainty

from helpr.utilities.unit_conversion import convert_in_to_m, convert_ksi_to_mpa
from helpr.api import CrackEvolutionAnalysis


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = THIS_DIR + '/verification_data/'
figure_path = THIS_DIR + '/test_figures/'
os.makedirs(figure_path, exist_ok=True)


class VerificationCrackGrowth(unittest.TestCase):
    """
    Class for verification tests of crack growth rate calculations.
    
    Attributes
    ----------
    mean_error_metric : float
        Mean error metric for verification tests (%)
    max_error_metric : float
        Maximum error metric for verification tests (%)
    outer_diameter : Uncertainty.DeterministicCharacterization
        Outer diameter of the pipe (m)
    wall_thickness : Uncertainty.DeterministicCharacterization
        Thickness of the pipe wall (m)
    flaw_depth : Uncertainty.DeterministicCharacterization
        Depth of the flaw (%)
    max_pressure : Uncertainty.DeterministicCharacterization
        Maximum pressure (MPa)
    temperature : Uncertainty.DeterministicCharacterization
        Temperature (K)
    yield_strength : Uncertainty.DeterministicCharacterization
        Yield strength (ksi)
    fracture_resistance : Uncertainty.DeterministicCharacterization
        Fracture resistance
    flaw_length : Uncertainty.DeterministicCharacterization
        Length of the flaw (m)
    """

    def setUp(self):
        """Set up common inputs for verification tests."""
        self.mean_error_metric = 10  # %
        self.max_error_metric = 30  # %
        self.outer_diameter = \
            Uncertainty.DeterministicCharacterization(name='outer_diameter',
                                                      value=convert_in_to_m(12.76))
        self.wall_thickness = \
            Uncertainty.DeterministicCharacterization(name='wall_thickness',
                                                      value=convert_in_to_m(0.5))
        self.flaw_depth = \
            Uncertainty.DeterministicCharacterization(name='flaw_depth',
                                                      value=25)
        self.max_pressure = \
            Uncertainty.DeterministicCharacterization(name='max_pressure',
                                                      value=convert_ksi_to_mpa(2.900))
        self.temperature = \
            Uncertainty.DeterministicCharacterization(name='temperature',
                                                      value=293)
        self.yield_strength = \
            Uncertainty.DeterministicCharacterization(name='yield_strength',
                                                      value=359)
        self.fracture_resistance = \
            Uncertainty.DeterministicCharacterization(name='fracture_resistance',
                                                      value=40)
        self.flaw_length = \
            Uncertainty.DeterministicCharacterization(name='flaw_length',
                                                      value=0.04)

    def tearDown(self):
        """Teardown function."""

    def calculate_crack_evolution_error(self, truth, simulation_data):
        """
        Function for calculating % rel. err. between predictions and data.
        
        Parameters
        ----------
        truth : pandas.DataFrame
            Truth data.
        simulation_data : list of pandas.DataFrame
            Simulation data.

        Returns
        -------
        error : float
            % relative error.
        """
        interpolated_points = np.interp(truth['N'], simulation_data[0]['Total cycles'],
                                        simulation_data[0]['a/t'])
        return (truth['a/t'] - interpolated_points)/truth['a/t']*100

    def calculate_error_metrics(self, truth, simulation_data):
        """
        Function for calculating error metrics.
        
        Parameters
        ----------
        truth : pandas.DataFrame
            Truth data.
        simulation_data : list of pandas.DataFrame
            Simulation data.

        Returns
        -------
        max_error : float
            Maximum error.
        mean_error : float
            Mean error.
        """
        percent_error = self.calculate_crack_evolution_error(truth, simulation_data)
        return abs(percent_error).max(), abs(percent_error).mean()

    def verification_raw_comparison_plot(self, verification_data, simulation_data, condition):
        """
        Function for creating verification comparison plots.
        
        Parameters
        ----------
        verification_data : pandas.DataFrame
            Verification data.
        simulation_data : list of pandas.DataFrame
            Simulation data.
        condition : str
            Condition for plot title.
        """
        plt.figure()
        plt.plot(verification_data['N'], verification_data['a/t'], 'k--', label='verification')
        plt.plot(simulation_data[0]['Total cycles'], simulation_data[0]['a/t'],
                 'r-', label='prediction')
        plt.xlabel('# of cycles')
        plt.ylabel('fractional crack length (a/t)')
        plt.legend(loc=0)
        plt.title('Fatigue Crack Growth of Semi-Elliptical Flaw (constant a/2c)')
        plt.grid(color='gray', alpha=0.3, linestyle='--')
        plt.text(0.5, 0.5, condition)
        plt.savefig(figure_path+condition.replace('%', '').replace('=', ' ').replace(' ', '_') + '.png',
                    format='png', dpi=200)
        plt.close()

    def test_dataset_1(self):
        """"Verification test using dataset 1."""
        min_pressure = \
            Uncertainty.DeterministicCharacterization(name='min_pressure',
                                                      value=self.max_pressure.value*.5)
        volume_fraction_h2 = \
            Uncertainty.DeterministicCharacterization(name='volume_fraction_h2',
                                                      value=1)
        analysis = CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                          wall_thickness=self.wall_thickness,
                                          flaw_depth=self.flaw_depth,
                                          max_pressure=self.max_pressure,
                                          min_pressure=min_pressure,
                                          temperature=self.temperature,
                                          volume_fraction_h2=volume_fraction_h2,
                                          yield_strength=self.yield_strength,
                                          fracture_resistance=self.fracture_resistance,
                                          flaw_length=self.flaw_length)
        analysis.perform_study()
        simulation_data1 = analysis.nominal_load_cycling

        file = 'data_set_1.txt'
        verification_data1 = pd.read_csv(data_path+file, header=2, sep=r'\s+')
        max_error, mean_error = self.calculate_error_metrics(verification_data1,
                                                             simulation_data1)
        self.assertTrue(max_error < self.max_error_metric)
        self.assertTrue(mean_error < self.mean_error_metric)

        self.verification_raw_comparison_plot(verification_data1, simulation_data1,
                                              '100% H2, 200 bar, R=0.5')

    def test_dataset_2(self):
        """Verification test using dataset 2."""
        min_pressure = \
            Uncertainty.DeterministicCharacterization(name='min_pressure',
                                                      value=self.max_pressure.value*.7)
        volume_fraction_h2 = \
            Uncertainty.DeterministicCharacterization(name='volume_fraction_h2',
                                                      value=1)
        analysis = CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                          wall_thickness=self.wall_thickness,
                                          flaw_depth=self.flaw_depth,
                                          max_pressure=self.max_pressure,
                                          min_pressure=min_pressure,
                                          temperature=self.temperature,
                                          volume_fraction_h2=volume_fraction_h2,
                                          yield_strength=self.yield_strength,
                                          fracture_resistance=self.fracture_resistance,
                                          flaw_length=self.flaw_length)
        analysis.perform_study()
        simulation_data2 = analysis.nominal_load_cycling

        file = 'data_set_2.txt'
        verification_data2 = pd.read_csv(data_path+file, header=2, sep=r'\s+')
        max_error, mean_error = self.calculate_error_metrics(verification_data2,
                                                             simulation_data2)
        self.assertTrue(max_error < self.max_error_metric)
        self.assertTrue(mean_error < self.mean_error_metric)

        self.verification_raw_comparison_plot(verification_data2, simulation_data2,
                                              '100% H2, 200 bar, R=0.7')

    def test_dataset_3(self):
        """Verification test using dataset 3."""
        min_pressure = \
            Uncertainty.DeterministicCharacterization(name='min_pressure',
                                                      value=self.max_pressure.value*.5)
        volume_fraction_h2 = \
            Uncertainty.DeterministicCharacterization(name='volume_fraction_h2',
                                                      value=0.2)
        analysis = CrackEvolutionAnalysis(outer_diameter=self.outer_diameter,
                                          wall_thickness=self.wall_thickness,
                                          flaw_depth=self.flaw_depth,
                                          max_pressure=self.max_pressure,
                                          min_pressure=min_pressure,
                                          temperature=self.temperature,
                                          volume_fraction_h2=volume_fraction_h2,
                                          yield_strength=self.yield_strength,
                                          fracture_resistance=self.fracture_resistance,
                                          flaw_length=self.flaw_length)
        analysis.perform_study()
        simulation_data3 = analysis.nominal_load_cycling

        file = 'data_set_3.txt'
        verification_data3 = pd.read_csv(data_path+file, header=2, sep=r'\s+')
        max_error, mean_error = self.calculate_error_metrics(verification_data3, simulation_data3)
        self.assertTrue(max_error < self.max_error_metric)
        self.assertTrue(mean_error < self.mean_error_metric)

        self.verification_raw_comparison_plot(verification_data3, simulation_data3,
                                              '20% H2, 200 bar, R=0.5')

if __name__ == '__main__':
    unittest.main()
