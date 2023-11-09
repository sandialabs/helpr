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

def get_variable_units(variable_name:str)->str:
    """Specifies units used for analysis variables"""
    if variable_name == 'outer_diameter':
        return ' [m]'
    if variable_name == 'wall_thickness':
        return ' [m]'
    if variable_name == 'max_pressure':
        return ' [MPa]'
    if variable_name == 'min_pressure':
        return ' [MPa]'
    if variable_name == 'flaw_depth':
        return ' [% wall thickness]'
    if variable_name == 'flaw_length':
        return ' [m]'
    if variable_name == 'yield_strength':
        return ' [MPa]'
    if variable_name == 'temperature':
        return ' [K]'
    if variable_name == 'volume_fraction_h2':
        return ''
    if variable_name == 'fracture_resistance':
        return r' [MPa m$^{1/2}$]'
