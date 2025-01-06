# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import unittest
import scipy.stats as sps
import numpy as np

from probabilistic.capabilities.plotting import plot_distribution_pdf, plot_sample_histogram, plot_scatter_matrix

class PlottingTestCase(unittest.TestCase):
    """ class for unit tests of plotting module """

    def setUp(self):
        """ function to specify common plotting inputs """
        self.distribution = sps.norm()
        self.x_axis_label = 'x label'
        self.x_limits = [-2, 2]

    def tearDown(self):
        """teardown function"""

    def test_pdf_plotting(self):
        '''unit test to check the pdf plotting function does not error
        with basic inputs'''
        plot_distribution_pdf(self.distribution,
                              self.x_axis_label,
                              self.x_limits)
        assert True

    def test_histogram_plotting(self):
        '''unit test to check the histogram plotting does not error
        with basic inputs'''
        plot_sample_histogram(self.distribution.rvs(50),
                              self.x_axis_label)
        plot_sample_histogram(self.distribution.rvs(50),
                              self.x_axis_label,
                              density=False)
        assert True

    def test_plot_scatter_matrix(self):
        '''unit test to check the scatter plot creation does not error'''
        sample_size = 20
        data_dict = {'parameter_1': np.random.random(sample_size).tolist(),
                     'parameter_2': np.random.random(sample_size).tolist()}
        plot_scatter_matrix(data_dict)
