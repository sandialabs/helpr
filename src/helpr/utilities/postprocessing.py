# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np
import pandas as pd
import warnings as wr

from helpr.physics.fracture import FailureAssessment

"""Module of general crack evolution post processing functions. """


def report_single_cycle_evolution(all_results, pipe_index):
    """Creates a DataFrame object for plotting a single crack cycle evolution.
    
    Parameters
    -----------
    all_results : dict
        All load cycling results.
    pipe_index : int
        Index of single pipe instance.

    Returns
    -------
    single_cycle_evolution : pd.DataFrame
        DataFrame for plotting of single instance.

    """
    single_cycle_evolution = pd.DataFrame()
    for column in all_results.keys():
        if all_results[column].shape[1] > 1:
            single_cycle_evolution[column] = all_results[column][pipe_index]
        else:
            single_cycle_evolution[column] = all_results[column][0]
    return single_cycle_evolution


def parallel_interpolation_single_pt(interpolation_points, x_vals, y_vals,
                                     left=None, right=None):
    """Interpolates single points in parallel.
    
    Parameters
    ----------
    interpolation_points : list
        List of a critical values.
    x_vals : pandas.Series
        Series of x values for interpolated data.
    y_vals : pandas.Series
        Series of y values for interpolated data.
    left: float or None, optional
        Value to return for when `interpolation_points < x_vals[0]`.
        If `None`, defaults to `y_vals[0]`. Default is `None`.
    right: float or None, optional
        Value to return for when `interpolation_points > x_vals[-1]`.
        If `None`, defaults to `y_vals[-1]`. Default is `None`.

    Returns
    -------
    interpolation_results : numpy.ndarray

    """
    interpolation_results = []
    for x_val, y_val in zip(x_vals.items(), y_vals.items()):
        interpolation_results.append(np.interp(interpolation_points,
                                               x_val[1], y_val[1],
                                               left=left, right=right))

    return np.array(interpolation_results).flatten()


def parallel_interpolation_list_pts(interpolation_points, x_vals, y_vals,
                                    left=None, right=None):
    """Interpolates a list of points in parallel.
    
    Parameters
    ----------
    interpolation_points : list
        List of a critical values.
    x_vals : pandas.Series
        Series of x values for interpolated data.
    y_vals : pandas.Series
        Series of y values for interpolated data.
    left: float or None, optional
        Value to return for when `interpolation_points < x_vals[0]`.
        If `None`, defaults to `y_vals[0]`. Default is `None`.
    right: float or None, optional
        Value to return for when `interpolation_points > x_vals[-1]`.
        If `None`, defaults to `y_vals[-1]`. Default is `None`.
        
    Returns
    -------
    interpolation_results : numpy.ndarray

    """
    interpolation_results = []
    if np.size(left) == 1:
        left = [left] * len(interpolation_points)

    if np.size(right) == 1:
        right = [right] * len(interpolation_points)

    for interp_pt, x_val, y_val, l, r in zip(
        interpolation_points, x_vals.items(), y_vals.items(), left, right):
        interpolation_results.append(np.interp(interp_pt, x_val[1], y_val[1], left=l, right=r))

    return np.array(interpolation_results).flatten()


def report_single_pipe_life_criteria_results(life_results, pipe_index):
    """Reports pipe life criteria results for single instance.
    
    Parameters
    -----------
    life_results : dict
        Complete load cycling results.
    pipe_index : int
        Index of single pipe instance.

    Returns
    -------
    pipe_life : pandas.DataFrame
        Collected life criteria results.

    """
    life_criteria = [(life_results['Cycles to a(crit)'][0][pipe_index],
                      life_results['Cycles to 25% a(crit)'][0][pipe_index],
                      life_results['Cycles to 1/2 Nc'][0][pipe_index]),
                     (life_results['Cycles to a(crit)'][1][pipe_index],
                      life_results['Cycles to 25% a(crit)'][1][pipe_index],
                      life_results['Cycles to 1/2 Nc'][1][pipe_index])]
    columns = ['Cycles to a(crit)', 'Cycles to 25% a(crit)', 'Cycles to 1/2 Nc']
    index = ['Total cycles', 'a/t']
    pipe_life = pd.DataFrame(life_criteria, columns=columns, index=index)
    print(pipe_life)
    return pipe_life


def calc_pipe_life_criteria(cycle_results, pipe, material):
    """Calculates overall pipe life criteria.
    
    Parameters
    -----------
    cycle_results : dict
        Complete load cycling results.
    pipe_index : int
        Index of single pipe instance.    
    stress_state : GenericStressState
        Stress state specification.

    Returns
    -------
    life_criteria : dict
        Collected life criteria results.

    """
    if len(material.fracture_resistance) == 1:
        interp_function = parallel_interpolation_single_pt
    else:
        interp_function = parallel_interpolation_list_pts

    a_crit_not_reached = cycle_results['Kmax (MPa m^1/2)'].max() < material.fracture_resistance
    a_over_t_greater_than_point8 = cycle_results['a (m)'].max() > 0.8*pipe.wall_thickness

    a_crit = interp_function(interpolation_points=material.fracture_resistance,
                             x_vals=cycle_results['Kmax (MPa m^1/2)'],
                             y_vals=cycle_results['a (m)'],
                             right=np.nan)

    if np.logical_and(a_crit_not_reached,  ~a_over_t_greater_than_point8).any():
        wr.warn('Cycles to a_crit not reached for at least one crack, ' +
                    'setting a_crit = Nan for such cracks', UserWarning)

    if np.logical_and(a_crit_not_reached, a_over_t_greater_than_point8).any():
        wr.warn('Kmax did not reach fracture resistance for at least one crack, ' +
                    'setting a_crit/t = 0.8 for such cracks', UserWarning)
        a_crit = np.where(a_over_t_greater_than_point8 & a_crit_not_reached,
                          0.8*pipe.wall_thickness,
                          a_crit)

    # TODO: remove this once cracks are evolved individually
    a_crit = np.where(a_crit > 0.8*pipe.wall_thickness,
                      0.8*pipe.wall_thickness,
                      a_crit)

    cycles_to_a_crit = interp_function(interpolation_points=a_crit,
                                        x_vals=cycle_results['a (m)'],
                                        y_vals=cycle_results['Total cycles'],
                                        left=1, right=np.nan)
    cycles_to_25_pct_a_crit = interp_function(interpolation_points=0.25*a_crit,
                                             x_vals=cycle_results['a (m)'],
                                             y_vals=cycle_results['Total cycles'],
                                             left=1)
    cycles_to_half_a_crit_cycles = cycles_to_a_crit/2
    a_over_t_criterion_0 = calc_a_over_t_criterion_0(pipe, a_crit)
    a_over_t_criterion_1 = calc_a_over_t_criterion_1(pipe, a_crit)
    a_over_t_criterion_2 = calc_a_over_t_criterion_2(cycle_results, cycles_to_half_a_crit_cycles)
    life_criteria = {'a(crit)': [a_crit],
                     'Cycles to a(crit)': [cycles_to_a_crit, a_over_t_criterion_0],
                     'Cycles to 25% a(crit)': [cycles_to_25_pct_a_crit, a_over_t_criterion_1],
                     'Cycles to 1/2 Nc': [cycles_to_half_a_crit_cycles, a_over_t_criterion_2]}
    return life_criteria


def calc_a_over_t_criterion_0(pipe_specification, a_crit):
    """Calculates 'a critical' life criteria. """
    return a_crit/pipe_specification.wall_thickness


def calc_a_over_t_criterion_1(pipe_specification, a_crit):
    """Calculates '25% a critical' life criteria. """
    return 0.25*a_crit/pipe_specification.wall_thickness


def calc_a_over_t_criterion_2(cycle_sheet, cycles_to_half_a_crit_cycles):
    """Calculates 'half a critical cycles' life criteria. """
    return parallel_interpolation_list_pts(interpolation_points=cycles_to_half_a_crit_cycles,
                                           x_vals=cycle_sheet['Total cycles'],
                                           y_vals=cycle_sheet['a/t'])


def calculate_failure_assessment(parameters,
                                 fatigue_results,
                                 stress_state,
                                 stress_method):
    """Calculates failure assessment values for load cycling results.
    
    Parameters
    ------------
    parameters : dict
        Analysis input parameters.
    fatigue_results : dict
        Analysis load cycling results.
    stress_state : GenericStressState
        Stress state specification.

    """
    failure_assessment = \
        FailureAssessment(fracture_resistance=parameters['fracture_resistance'],
                          yield_stress=parameters['yield_strength'])
    stress_intensity_factor = fatigue_results['Kmax (MPa m^1/2)']
    crack_depth = fatigue_results['a (m)'].copy()
    # TODO: should this selection be independent of K solution method?
    if stress_method == 'anderson':
        # To not include crack in considerations
        crack_depth[:] = 0
        ref_stress_solution = stress_state.calc_stress_solution(crack_depth)
    elif stress_method == 'api':
        ref_stress_solution = stress_state.calc_ref_stress_api(crack_depth)
    else:
        raise ValueError(f"Stress method specified as {stress_method}"
                         + " but needs to be anderson or api")

    toughness_ratio, load_ratio = \
        failure_assessment.assess_failure_state(stress_intensity_factor,
                                                ref_stress_solution,
                                                fatigue_results['a (m)'],
                                                fatigue_results['c (m)']*2)
    fatigue_results['Toughness ratio'] = toughness_ratio
    fatigue_results['Load ratio'] = load_ratio
