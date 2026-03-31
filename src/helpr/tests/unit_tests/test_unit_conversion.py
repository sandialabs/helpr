# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import pytest
from helpr.utilities import unit_conversion


def test_convert_in_to_m():
    """Test conversion from inches to meters."""
    assert unit_conversion.convert_in_to_m(0) == 0
    assert unit_conversion.convert_in_to_m(39.3701) == pytest.approx(1.0, rel=1e-4)


def test_convert_ksi_to_mpa():
    """Test conversion from ksi to MPa."""
    assert unit_conversion.convert_ksi_to_mpa(0) == 0
    assert unit_conversion.convert_ksi_to_mpa(1) == 6.89


def test_convert_psi_to_mpa():
    """Test conversion from psi to MPa."""
    assert unit_conversion.convert_psi_to_mpa(0) == 0
    assert unit_conversion.convert_psi_to_mpa(145.0) == pytest.approx(1.0, rel=1e-2)


@pytest.mark.parametrize("var,expected", [
    ("outer_diameter", " [m]"),
    ("wall_thickness", " [m]"),
    ("max_pressure", " [MPa]"),
    ("min_pressure", " [MPa]"),
    ("flaw_depth", " [% wall thickness]"),
    ("flaw_length", " [m]"),
    ("yield_strength", " [MPa]"),
    ("temperature", " [K]"),
    ("volume_fraction_h2", ""),
    ("fracture_resistance", r" [MPa m$^{1/2}$]"),
    ("weld_thickness", " [m]"),
    ("weld_yield_strength", " [MPa]"),
    ("weld_flaw_distance", " [m]"),
    ("residual_stress_intensity_factor", r" [MPa m$^{1/2}$]"),
])
def test_get_variable_units_plotting(var, expected):
    """
    Test getting variable units for plotting.

    Parameters
    ----------
    var : str
        Variable name.
    expected : str
        Expected unit string.
    """
    assert unit_conversion.get_variable_units(var, for_plotting=True) == expected


@pytest.mark.parametrize("var,expected", [
    ("outer_diameter", "(m)"),
    ("wall_thickness", "(m)"),
    ("max_pressure", "(MPa)"),
    ("min_pressure", "(MPa)"),
    ("flaw_depth", "(% wall thickness)"),
    ("flaw_length", "(m)"),
    ("yield_strength", "(MPa)"),
    ("temperature", "(K)"),
    ("volume_fraction_h2", ""),
    ("fracture_resistance", "(MPa m^1/2)"),
    ("weld_thickness", "(m)"),
    ("weld_yield_strength", "(MPa)"),
    ("weld_flaw_distance", "(m)"),
    ("residual_stress_intensity_factor", "(MPa m^1/2)"),
])
def test_get_variable_units_non_plotting(var, expected):
    """
    Test getting variable units for non-plotting.

    Parameters
    ----------
    var : str
        Variable name.
    expected : str
        Expected unit string.
    """
    assert unit_conversion.get_variable_units(var, for_plotting=False) == expected
