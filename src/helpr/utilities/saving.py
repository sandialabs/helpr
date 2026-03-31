# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import csv

import pandas as pd
import itertools as it
import numpy as np

from helpr.utilities.unit_conversion import get_variable_units


def save_life_criteria_data(life_criteria, folder_name, study_type='nominal'):
    """
    Save pipe life criteria results to a CSV file.

    Parameters
    ----------
    life_criteria : dict
        Dictionary of life criteria outputs from crack evolution analysis.
    folder_name : str
        Directory path where the CSV file will be saved.
    study_type : str, optional
        Type of analysis ('nominal' or 'probabilistic'), by default 'nominal'.
    """

    # Initialize a dictionary to hold the data
    life_criteria_data = {}

    for key, value in life_criteria.items():
        if key == 'a(crit)':
            if study_type == 'nominal':
                life_criteria_data[key] = value[0]
            else:
                life_criteria_data[key] = [val[0] for val in list(value)]
        else:
            life_criteria_data[key] = list(value[0])

    # Create DataFrame directly from the dictionary
    life_criteria_df = pd.DataFrame.from_dict(life_criteria_data)

    # Save to CSV
    life_criteria_df.to_csv(f'{folder_name}{study_type}_life_criteria.csv',
                             index=False)


def save_parameter_characterizations(results, folder_name):
    """
    Saves deterministic or probabilistic parameter characterizations 
    used in analysis to a csv file.

    Parameters
    ----------
    results : CrackEvolutionAnalysis
        Results of crack evolution analysis stored in associated object
    folder_name : str
        Folder to store csv into. 
    """
    with open(folder_name + 'input_parameters.csv', mode='w', encoding='utf-8') as open_file:
        header_part1 = 'Parameter, Deterministic/Distribution Type, Nominal Value, '
        header_part2 = 'Uncertainty Type, Distribution Parameter 1, Distribution Parameter 2, '
        header_part3 = 'Distribution Lower Bound, Distribution Upper Bound'
        open_file.write(header_part1 + header_part2 + header_part3 + '\n')
        for parameter in results.input_parameters.values():
            open_file.write(repr(parameter) + '\n')


def save_deterministic_results(results, folder_name):
    """
    Saves deterministic results to a csv file.
    CSV file has nominal input parameters specified first,
    then subset of cycle evolution results

    Parameters
    ----------
    results : CrackEvolutionAnalysis
        Results of crack evolution analysis stored in associated object
    folder_name : str
        Folder to store csv into
    """
    # Save nominal life criteria data
    save_life_criteria_data(results.nominal_life_criteria, folder_name, study_type='nominal')

    # Prepare the output file path
    output_file_path = folder_name + 'Nominal_Results.csv'

    # Prepare parameter data
    parameter_rows = []
    parameter_rows.append('Parameter, Nominal Value, Units')

    for name, value in results.input_parameters.items():
        parameter_description = repr(value).split(',')
        parameter_rows.append(f"{parameter_description[0].strip()}, "
                              f"{parameter_description[2].strip()}, "
                              f"{get_variable_units(name, for_plotting=False)}")

    parameter_rows.append('')  # Add a blank line

    # Prepare intermediate variable data
    for name, value in results.nominal_intermediate_variables.items():
        split_text = name.split('(')
        parameter_description = \
            [split_text[0].strip(), f"({split_text[1].strip()})"] \
                if len(split_text) == 2 else [split_text[0].strip(), '( )']
        parameter_rows.append(f"{parameter_description[0]}, {value:.5f}, {parameter_description[1]}")

    parameter_rows.append('')  # Add a blank line

    # Gather single crack cycle evolution data
    csv_file_data = results.gather_single_crack_cycle_evolution()
    csv_file_data['2c/t'] = \
        csv_file_data['c (m)'] * 2 / results.nominal_input_parameter_values['wall_thickness'][0]

    # Select desired columns
    desired_columns = ['Total cycles', 'a/t', '2c/t', 'Kmax (MPa m^1/2)',
                       'Delta K (MPa m^1/2)', 'Toughness ratio', 'Load ratio']

    # Convert to CSV format
    analysis_results = csv_file_data[desired_columns].to_csv(index=False, header=True)

    # Write all data to the file at once
    with open(output_file_path, mode='w', encoding='utf-8') as open_file:
        open_file.write('\n'.join(parameter_rows) + '\n\n')
        open_file.write(analysis_results)


def save_probabilistic_results(results, folder_name):
    """
    Saves probabilistic results to a csv file.

    Parameters
    ----------
    results : CrackEvolutionAnalysis
        Results of crack evolution analysis stored in associated object
    folder_name : str
        Folder to store csv into.   
    """
    # Save life criteria data
    save_life_criteria_data(results.life_criteria, folder_name, study_type='probabilistic')

    # Clean names
    cleaned_names = clean_results_names(results)

    # Iterate through keys and save data
    for key in results.load_cycling[0].keys():
        temp_data = [crack_instance[key] for crack_instance in results.load_cycling]

        # Use zip_longest to handle different sizes
        padded_data = list(it.zip_longest(*temp_data, fillvalue=''))

        # Use pandas to handle CSV writing more efficiently
        df = pd.DataFrame(padded_data)
        df.to_csv(f'{folder_name}{cleaned_names[key]}.csv', index=False, header=False, na_rep='')


def clean_results_names(results):
    """
    Cleans up variable names for saving to csv. 

    Parameters
    ----------
    results : CrackEvolutionAnalysis
        Results of crack evolution analysis stored in associated object

    Returns
    -------
    dict
        Dictionary mapping original result keys to cleaned names.
    """
    def process_name(name):
        """Helper function to process and clean a single name."""
        name_list = name.split()
        cleaned_name = ''.join(
            capitalize_rules(val.replace('/', 'Over'), name) if not check_for_units(val) else ''
            for val in name_list
        )
        return cleaned_name

    # Use dictionary comprehension for faster processing
    cleaned_names = {name: process_name(name) for name in results.nominal_load_cycling[0]}

    return cleaned_names


def check_for_units(value:str):
    """
    Checks for brackets in strings to indicate unit values.
    
    Parameters
    ----------
    value : str
        The string to check.

    Returns
    -------
    bool
        True if the string contains brackets indicating units, False otherwise.
    """
    return ('(' in value) or (')' in value)


def capitalize_rules(value:str, name:list):
    """
    Enforces capitalization rules for multi-word strings. 
    
    Parameters
    ----------
    value : str
        Individual word from a variable name.
    name : list
        The full name split into words.

    Returns
    -------
    str
        Capitalized or original string based on context.
    """
    if len(name.split()) > 1:
        return value.capitalize()

    return value
