# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

"""Common unit conversion functions. """


def convert_in_to_m(inch_value:float)->float:
    """Converts inches to meters. """
    return inch_value*25.4/1000

def convert_ksi_to_mpa(ksi_value:float)->float:
    """Converts KSI to MPa. """
    return ksi_value*6.89

def convert_psi_to_mpa(psi_value:float)->float:
    """Converts PSI to MPa. """
    return psi_value*6.89/1_000

def get_variable_units(variable_name:str, for_plotting:bool=True)->str:
    """Specifies units used for analysis variables"""
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
        else:
            return '(MPa m^1/2)'
