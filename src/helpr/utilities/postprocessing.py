# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import warnings as wr
import numpy as np
import pandas as pd

from helpr.utilities.plots import failure_assessment_diagram_equation

def report_single_cycle_evolution(all_results, pipe_index):
    """
    Creates a DataFrame object for plotting a single crack cycle evolution.
    
    Parameters
    -----------
    all_results : list of dicts
        All load cycling results.
    pipe_index : int
        Index of single pipe instance.

    Returns
    -------
    single_cycle_evolution : pd.DataFrame
        DataFrame for plotting of single instance.
    """
    single_cycle_evolution = pd.DataFrame()

    # added for cases where life assessments completed outside of API interface
    if isinstance(all_results, dict):
        all_results = [all_results]

    for column in all_results[pipe_index].keys():
        single_cycle_evolution[column] = all_results[pipe_index][column]

    return single_cycle_evolution


def report_single_pipe_life_criteria_results(life_results, pipe_index):
    """
    Reports pipe life criteria results for single instance.
    
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
                      life_results['Cycles to 1/2 Nc'][0][pipe_index],
                      life_results['Cycles to FAD line'][0][pipe_index]),
                     (life_results['Cycles to a(crit)'][1][pipe_index],
                      life_results['Cycles to 25% a(crit)'][1][pipe_index],
                      life_results['Cycles to 1/2 Nc'][1][pipe_index],
                      life_results['Cycles to FAD line'][1][pipe_index])]
    columns = ['Cycles to a(crit)',
               'Cycles to 25% a(crit)',
               'Cycles to 1/2 Nc',
               'Cycles to FAD line']
    index = ['Total cycles', 'a/t']
    pipe_life = pd.DataFrame(life_criteria, columns=columns, index=index)
    print(pipe_life)
    return pipe_life


def find_intersection(load_ratio_data, toughness_ratio_data, cycles, a_over_t):
    """
    Finds the intersection point where the toughness ratio exceeds the FAD values.

    Parameters:
    - load_ratio_data: Array of load ratios.
    - toughness_ratio_data: Array of toughness ratios.
    - cycles: Array of total cycles corresponding to load ratios.
    - a_over_t: Array of a/t values corresponding to load ratios.

    Returns:
    - A dictionary containing the intersection details or a message if no intersection is found.
    """
    # calculate FAD values for the given load ratios
    fad_values = failure_assessment_diagram_equation(load_ratio_data)

    # determine the boolean array where toughness exceeds FAD values
    bool_array = toughness_ratio_data > fad_values
    first_true_index = np.argmax(bool_array)

    # check if any toughness ratio value exceeds the FAD line
    fad_intersection = np.any(bool_array)

    # check if all toughness ratio values exceeds the FAD line
    fad_exceedence = np.all(bool_array)

    # return dict indicating initial specifications exceeded FAD line
    if fad_exceedence:
        return {
            'load_intersection': np.nan,
            'toughness_intersection': np.nan,
            'cycles_fad_criteria': 1,
            'a_over_t_fad_criteria': a_over_t[0]
        }

    if fad_intersection:
        # interpolate to the # of cycles to reach the FAD line intersection
        cycles_fad_criteria = np.interp(fad_values[first_true_index],
                                [toughness_ratio_data[first_true_index-1],
                                 toughness_ratio_data[first_true_index]],
                                [cycles[first_true_index-1],
                                 cycles[first_true_index]])
        # interpolate to the a/t value at the FAD line intersection
        a_over_t_fad_criteria = np.interp(fad_values[first_true_index],
                                [toughness_ratio_data[first_true_index-1],
                                 toughness_ratio_data[first_true_index]],
                                [a_over_t[first_true_index-1],
                                 a_over_t[first_true_index]])
        # interpolate to the load ratio value at the FAD line intersection
        load_intersection = np.interp(fad_values[first_true_index],
                                [toughness_ratio_data[first_true_index-1],
                                 toughness_ratio_data[first_true_index]],
                                [load_ratio_data[first_true_index-1],
                                 load_ratio_data[first_true_index]])
        # use toughness value on FAD line used as interpolation reference for other QoIs
        toughness_intersection = fad_values[first_true_index]

        # return dict of FAD line intersection QoIs
        return {
            'load_intersection': load_intersection,
            'toughness_intersection': toughness_intersection,
            'cycles_fad_criteria': cycles_fad_criteria,
            'a_over_t_fad_criteria': a_over_t_fad_criteria
        }

    # return dict indicating the crack never exceeded the FAD line
    return {'message': "No intersection found; all toughness ratios are below the FAD values.",
            'load_intersection': np.nan,
            'toughness_intersection': np.nan,
            'cycles_fad_criteria': np.nan,
            'a_over_t_fad_criteria': np.nan
            }


def determine_qoi_values(crack_instance,
                         fracture_resistance,
                         wall_thickness):
    """
    Helper function to determine quality of interest values.
    
    Parameters
    ----------
    crack_instance : dict
        Dictionary with crack growth data containing keys like 'Kmax', 'Kres', 'a (m)', and 'Total cycles'.
    fracture_resistance : float
        Critical fracture resistance (MPa√m).
    wall_thickness : float
        Wall thickness of the pipe (m).

    Returns
    -------
    life_criteria : dict
        Dictionary containing:
        - a(crit): critical crack depth
        - Cycles to a(crit): total cycles and a/t value
        - Cycles to 25% a(crit): total cycles and a/t value
        - Cycles to 1/2 Nc: total cycles and a/t value
    warning_1 : bool
        True if a_crit was not reached and max a/t < 0.8.
    warning_2 : bool
        True if Kmax + Kres < fracture resistance but max a/t >= 0.8.
    """
    # boolean warning trackers
    warning_1 = False
    warning_2 = False

    # determine a_crit based on Kmax == fracture resistance
    a_crit = np.interp(fracture_resistance,
                        crack_instance['Kmax (MPa m^1/2)']+ \
                            np.array(crack_instance['Kres (MPa m^1/2)']),
                        crack_instance['a (m)'],
                        right=np.nan)

    # set upper limit of a_crit to 0.8 x wall thickness
    a_crit = min(a_crit, 0.8 * wall_thickness)

    # boolean for if Kmax ever exceeded fracture resistance
    a_crit_not_reached = (max(np.array(crack_instance['Kmax (MPa m^1/2)']) +\
                              np.array(crack_instance['Kres (MPa m^1/2)'])) <
                              fracture_resistance)

    # boolean for it crack depth ever exceeded 0.8 x wall thickness
    a_over_t_greater_than_point8 = (max(crack_instance['a (m)']) >
                                    0.8*wall_thickness)

    # warn if a_crit not reached and a never exceeded 0.8 x wall thickness
    if a_crit_not_reached &  ~a_over_t_greater_than_point8:
        warning_1 = True

    # if Kmax never reaches fracture resistance and a/t>0.8 set a_crit to 0.8 x wall thickness
    # warn if a_crit not reached and a exceeded 0.8 x wall thickness
    if a_over_t_greater_than_point8 & a_crit_not_reached:
        a_crit = 0.8 * wall_thickness
        warning_2 = True

    # number of cycles to reach a_crit
    cycles_to_a_crit = np.interp(a_crit,
                                    crack_instance['a (m)'],
                                    crack_instance['Total cycles'],
                                    left=1, right=np.nan)
    a_over_t_a_crit_cycles = a_crit/wall_thickness

    # number of cycles to reach 1/4 a_crit
    cycles_to_25_pct_a_crit= np.interp(0.25*a_crit,
                                        crack_instance['a (m)'],
                                        crack_instance['Total cycles'],
                                        left=1)
    a_over_t_25_pct_a_crit = 0.25*a_crit/wall_thickness

    # number of cycle to 1/2 a_crit cycles
    cycles_to_half_a_crit_cycles = cycles_to_a_crit/2
    a_over_t_half_a_crit_cycles = np.interp(cycles_to_half_a_crit_cycles,
                                            crack_instance['Total cycles'],
                                            crack_instance['a/t'])

    # cycles until intersection with FAD curve
    fad_intersection_details = \
        find_intersection(load_ratio_data=np.array(crack_instance['Load ratio']),
                          toughness_ratio_data=np.array(crack_instance['Toughness ratio']),
                          cycles=np.array(crack_instance['Total cycles']),
                          a_over_t=np.array(crack_instance['a/t']))

    life_criteria = {'a(crit)': [a_crit],
                        'Cycles to a(crit)': [cycles_to_a_crit, a_over_t_a_crit_cycles],
                        'Cycles to 25% a(crit)': [cycles_to_25_pct_a_crit, a_over_t_25_pct_a_crit],
                        'Cycles to 1/2 Nc': [cycles_to_half_a_crit_cycles,
                                             a_over_t_half_a_crit_cycles],
                        'Cycles to FAD line': [fad_intersection_details['cycles_fad_criteria'],
                                               fad_intersection_details['a_over_t_fad_criteria'],
                                               fad_intersection_details['load_intersection'],
                                               fad_intersection_details['toughness_intersection']]}
    return life_criteria, warning_1, warning_2


def calc_pipe_life_criteria(cycle_results, pipe, material):
    """
    Calculates overall pipe life criteria.
    
    Parameters
    -----------
    cycle_results : list of dicts
        Complete load cycling results.
    pipe : Pipe
        Pipe specification    
    material : object or list of objects
        Object or list of objects with attribute `fracture_resistance`.

    Returns
    -------
    dict
        Aggregated life criteria results:
        - 'a(crit)' : list of critical crack depths
        - 'Cycles to a(crit)' : [list of cycles, list of a/t values]
        - 'Cycles to 25% a(crit)' : [list of cycles, list of a/t values]
        - 'Cycles to 1/2 Nc' : [list of cycles, list of a/t values]

    Raises
    ------
    UserWarning
        If critical conditions are not met and default values are used.
    """
    warning_1_global = False
    warning_2_global = False
    life_criteria_global = {'a(crit)': [],
                            'Cycles to a(crit)': [[], []],
                            'Cycles to 25% a(crit)': [[], []],
                            'Cycles to 1/2 Nc': [[], []],
                            'Cycles to FAD line': [[], [], [], []]}

    # added for cases where life assessments completed outside of API interface
    # Ensure cycle_results is a list
    if isinstance(cycle_results, dict):
        cycle_results = [cycle_results]

    # # Determine fracture resistance and wall thickness for each crack instance
    # def get_material_properties(i):
    #     '''function to get fracture resistance and wall thickness for crack instance
    #     depending on how data is organized'''
    #     if len(cycle_results) > 1:
    #         return material[i].fracture_resistance, pipe[i].wall_thickness
    #     elif isinstance(material, (list, np.ndarray)):
    #         return material[0].fracture_resistance, pipe[0].wall_thickness
    #     else:
    #         return material.fracture_resistance, pipe.wall_thickness

    # # Prepare arguments for parallel processing
    # args = [(crack_instance, *get_material_properties(i))
    #         for i, crack_instance in enumerate(cycle_results)]

    # # Parallel processing of crack instances using multiprocessing
    # chunk_size = max(1, len(args) // mp.cpu_count())
    # with mp.Pool(processes=mp.cpu_count()) as pool:
    #     results = pool.starmap(determine_qoi_values, args, chunksize=chunk_size)


    # TODO: Make into parallel call
    for i, crack_instance in enumerate(cycle_results):
        if len(cycle_results) > 1:
            fracture_resistance = material[i].fracture_resistance
            wall_thickness = pipe[i].wall_thickness
        elif isinstance(material, (list, np.ndarray)):
            fracture_resistance = material[0].fracture_resistance
            wall_thickness = pipe[0].wall_thickness
        else:
            fracture_resistance = material.fracture_resistance
            wall_thickness = pipe.wall_thickness

        life_criteria_inst, warning_1_inst, warning_2_inst = \
            determine_qoi_values(crack_instance,
                                 fracture_resistance,
                                 wall_thickness)
        warning_1_global += warning_1_inst
        warning_2_global += warning_2_inst

    # # Collect results
    # for life_criteria_inst, warning_1_inst, warning_2_inst in results:
    #     warning_1_global |= warning_1_inst
    #     warning_2_global |= warning_2_inst

        life_criteria_global['a(crit)'] += \
            [life_criteria_inst['a(crit)']]
        life_criteria_global['Cycles to a(crit)'][0] += \
            [life_criteria_inst['Cycles to a(crit)'][0]]
        life_criteria_global['Cycles to a(crit)'][1] += \
            [life_criteria_inst['Cycles to a(crit)'][1]]
        life_criteria_global['Cycles to 25% a(crit)'][0] += \
            [life_criteria_inst['Cycles to 25% a(crit)'][0]]
        life_criteria_global['Cycles to 25% a(crit)'][1] += \
            [life_criteria_inst['Cycles to 25% a(crit)'][1]]
        life_criteria_global['Cycles to 1/2 Nc'][0] += \
            [life_criteria_inst['Cycles to 1/2 Nc'][0]]
        life_criteria_global['Cycles to 1/2 Nc'][1] += \
            [life_criteria_inst['Cycles to 1/2 Nc'][1]]
        
        life_criteria_global['Cycles to FAD line'][0] += \
            [life_criteria_inst['Cycles to FAD line'][0]]
        life_criteria_global['Cycles to FAD line'][1] += \
            [life_criteria_inst['Cycles to FAD line'][1]]
        life_criteria_global['Cycles to FAD line'][2] += \
            [life_criteria_inst['Cycles to FAD line'][2]]
        life_criteria_global['Cycles to FAD line'][3] += \
            [life_criteria_inst['Cycles to FAD line'][3]]

    if warning_1_global:
        wr.warn('Cycles to a_crit not reached for at least one crack, ' +
                    'setting a_crit = Nan for such cracks', UserWarning)

    if warning_2_global:
        wr.warn('Kmax + Kres did not reach fracture resistance for at least one crack, ' +
                    'setting a_crit/t = 0.8 for such cracks', UserWarning)

    return life_criteria_global
