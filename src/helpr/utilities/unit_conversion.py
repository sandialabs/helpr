# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

"""Common unit conversion functions. """


def convert_in_to_m(inch_value:float)->float:
    """
    Converts inches to meters. 

    Parameters
    ----------
    inch_value : float
        The value in inches to be converted.

    Returns
    -------
    float
        The converted value in meters.
    """
    return inch_value*25.4/1000

def convert_ksi_to_mpa(ksi_value:float)->float:
    """
    Converts KSI to MPa. 

    Parameters
    ----------
    ksi_value : float
        The value in KSI to be converted.

    Returns
    -------
    float
        The converted value in MPa.
    """
    return ksi_value*6.89

def convert_psi_to_mpa(psi_value:float)->float:
    """
    Converts PSI to MPa.

    Parameters
    ----------
    psi_value : float
        The value in PSI to be converted.

    Returns
    -------
    float
        The converted value in MPa.
    """
    return psi_value*6.89/1_000

def get_variable_units(variable_name:str, for_plotting:bool=True)->str:
    """
    Specifies units used for analysis variables

    Parameters
    ----------
    variable_name : str
        The name of the variable for which to retrieve the units.
    for_plotting : bool, optional
        A flag indicating whether the units are for plotting (default is True).

    Returns
    -------
    str
        A string representing the units of the specified variable.
    """
    if for_plotting:
        left_bracket = ' ['
        right_bracket = ']'
    else:
        left_bracket = '('
        right_bracket = ')'

    if variable_name == 'outer_diameter':
        return left_bracket + 'm' + right_bracket

    if variable_name == 'wall_thickness':
        return left_bracket + 'm' + right_bracket

    if variable_name == 'max_pressure':
        return left_bracket + 'MPa' + right_bracket

    if variable_name == 'min_pressure':
        return left_bracket + 'MPa' + right_bracket

    if variable_name == 'flaw_depth':
        return left_bracket + '% wall thickness' + right_bracket

    if variable_name == 'flaw_length':
        return left_bracket + 'm' + right_bracket

    if variable_name == 'yield_strength':
        return left_bracket + 'MPa' + right_bracket

    if variable_name == 'temperature':
        return left_bracket + 'K' + right_bracket

    if variable_name == 'volume_fraction_h2':
        return ''

    if variable_name == 'fracture_resistance':
        if for_plotting:
            return r' [MPa m$^{1/2}$]'

        return '(MPa m^1/2)'

    if variable_name == 'weld_thickness':
        return left_bracket + 'm' + right_bracket

    if variable_name == 'weld_yield_strength':
        return left_bracket + 'MPa' + right_bracket

    if variable_name == 'weld_flaw_distance':
        return left_bracket + 'm' + right_bracket

    if variable_name == 'residual_stress_intensity_factor':
        if for_plotting:
            return r' [MPa m$^{1/2}$]'

        return '(MPa m^1/2)'
       