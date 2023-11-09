# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from itertools import cycle

'''Module for holding plotting functionality'''


def initiate_plot_settings():
    '''function to initiate plotting settings'''
    lines = ['-', '--', '-.', ':']
    colors = ['r', 'k', 'orange', 'purple', 'g']
    line_cycler = cycle(lines)
    color_cycler = cycle(colors)
    return line_cycler, color_cycler


def plot_distribution_pdf(distribution,
                          variable_name,
                          plot_limits=False):
    '''function to plot distribution pdf

    Parameters
    -----------
    distribution
    variable_name
    plot_limits: bool
        Defaults to False
    '''
    plt.figure(figsize=(4, 4))
    if not plot_limits:
        plot_spread = distribution.std()*3
        plot_limits = (distribution.mean() - plot_spread,
                       distribution.mean() + plot_spread)
    x_points = np.linspace(plot_limits[0], plot_limits[1], 100)
    y_points = distribution.pdf(x_points)

    plt.plot(x_points, y_points)
    plt.grid()
    plt.xlabel(variable_name)
    plt.ylabel('PDF')


def plot_deterministic_parameter_value(value,
                                       variable_name):
    '''function to plot deterministic value

    Parameters
    ----------
    value
    variable_name
    '''
    plt.figure(figsize=(4, 4))
    plt.plot(value, 0, 'ks')
    plt.grid()
    plt.xlabel(variable_name)
    plt.yticks([])
    plt.xticks([value])


def plot_sample_cdf(samples:np.array,
                    variable_name:str,
                    percentiles:list=False,
                    **kwargs):
    '''function to plot cdf of samples

    Parameters
    ----------
    samples: np.array
        data to be plotted
    variable_name: str
        name of data to be plotted
    percentiles: list
        percentiles to include on plot
    kwargs: dict
        additional histogram function inputs
    '''
    quantiles = np.sort(samples)[::-1]
    cumprob = np.linspace(0, 1, len(samples), endpoint=False)

    plt.figure(figsize=(4, 4))
    plt.plot(quantiles, cumprob, color='blue')
    plt.xlabel(variable_name)
    plt.ylabel('CDF')
    plt.grid(alpha=0.3, color='gray', linestyle='--')

    if percentiles:
        line_cycler, color_cycler = initiate_plot_settings()
        for ptile in percentiles:
            color=next(color_cycler)
            linestyle=next(line_cycler)
            plt.hlines(ptile,
                    xmin=samples.max(),
                    xmax=np.percentile(samples, q=100-ptile),
                    color=color,
                    linestyle=linestyle)
            plt.vlines(np.percentile(samples, q=100-ptile),
                    ymin=0,
                    ymax=100-ptile,
                    color=color,
                    linestyle=linestyle,
                    label=f'{ptile}th : {np.percentile(samples, q=100-ptile):.2f}')

        plt.legend(loc=0, title='percentile')

    plt.xlim(samples.min(), samples.max())
    plt.ylim(0, 1)


def plot_sample_histogram(samples:np.array,
                          variable_name:str,
                          percentiles:list=False,
                          **kwargs):
    '''function to plot histogram of samples

    Parameters
    ----------
    samples: np.array
        data to be plotted
    variable_name: str
        name of data to be plotted
    percentiles: list
        percentiles to include on plot
    kwargs: dict
        additional histogram function inputs
    '''
    if 'bins' not in kwargs:
        kwargs['bins'] = 'auto'

    plt.figure(figsize=(4, 4))
    plt.hist(samples, **kwargs)
    plt.xlabel(variable_name)
    plt.ylabel('PDF')
    plt.grid(alpha=0.3, color='gray', linestyle='--')

    if percentiles:
        axis = plt.subplot(111)
        line_cycler, color_cycler = initiate_plot_settings()
        for ptile in percentiles:
            axis.axvline(np.percentile(samples, q=100-ptile),
                    label=f'{ptile}th : {np.percentile(samples, q=100-ptile):.2f}',
                    color=next(color_cycler),
                    linestyle=next(line_cycler))

        plt.legend(loc=0, title='percentile')


def plot_scatter_matrix(data_dict, density=False):
    '''function to plot scatter matrix of samples from multiple parameters
    
    Parameters
    -----------
    data_dict: dict
    density: bool
        Defaults to False
    '''
    data_frame = pd.DataFrame(data_dict)
    axs = pd.plotting.scatter_matrix(data_frame, figsize=(9, 9))

    n_col = len(data_frame.columns)
    for x_var in range(n_col):
        for y_var in range(n_col):
            # to get the axis of subplots
            axis = axs[x_var, y_var]
            # to make x axis name vertical
            axis.xaxis.label.set_rotation(45)
            # to make y axis name horizontal
            axis.yaxis.label.set_rotation(45)
            # to make sure y axis names are outside the plot area
            axis.yaxis.labelpad = 50

            if x_var == y_var:
                axis.clear()
                axis.hist(data_frame.values[:, x_var],
                        bins='auto', density=density)
                axis.get_yaxis().set_visible(False)

    for i in range(np.shape(axs)[0]):
        for j in range(np.shape(axs)[1]):
            if i < j:
                axs[i,j].set_visible(False)
    plt.tight_layout()
