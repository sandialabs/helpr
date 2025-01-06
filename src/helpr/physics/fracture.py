# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np
import xarray as xr
import os

path = os.path.dirname(os.path.realpath(__file__))

"""Module to hold fracture assessment diagram (FAD) functionality"""

class FailureAssessment:
    """Class for failure assessment calculations.
    
    Attributes
    ----------
    fracture_resistance
    yield_stress
    
    """
    def __init__(self,
                 fracture_resistance,
                 yield_stress):
        """Sets up failure assessment parameters.

        Parameters
        ------------
        fracture_resistance : float
            Fracture resistance of the pipe material.
        yield_stress : float
            Yield stress of the pipe material.

        """
        self.fracture_resistance = fracture_resistance
        self.yield_stress = yield_stress

    def assess_failure_state(self,
                             primary_stress_intensity_factor,
                             primary_reference_stress_solution,
                             crack_depth,
                             crack_length,
                             secondary_stress_intensity_factor=None,
                             zeta_file=os.path.join(path, '../data/Table_9.3.nc')):
        """function to calculate location of failure assessment diagram"""
        load_ratio = (primary_reference_stress_solution
                        / self.yield_stress)
        if secondary_stress_intensity_factor is None:
            toughness_ratio = (primary_stress_intensity_factor
                             / self.fracture_resistance)
        else:
            toughness_ratio = self.calc_toughness_ratio_api(
                load_ratio,
                primary_stress_intensity_factor,
                crack_depth,
                crack_length,
                secondary_stress_intensity_factor,
                zeta_file)

        return toughness_ratio, load_ratio

    def calc_toughness_ratio_api(self,
                                 load_ratio,
                                 primary_stress_intensity_factor,
                                 crack_depth,
                                 crack_length,
                                 secondary_stress_intensity_factor,
                                 zeta_file):
        """calculates the toughness ratio to use in a failure assessment
        diagram using the level 2 assessment from API 579-1.
        """
        def open_zeta_table(nc_file):
            """Opens a saved NetCDF file of influence coefficient values from
            API 579-1.
            """
            return xr.open_dataset(nc_file).to_array().squeeze()

        def calc_zeta(zeta_table, load_ratio, X):
            """Interpolates values for the influence coefficient based on
            Table 9.3 provided in API 579-1. Returns a float corresponding to
            the zeta parameter.
            """
            return zeta_table.interp(load_ratio=load_ratio, X=X).values.squeeze()

        def calc_phi_0(yield_stress, k_i_secondary_residual, a, c):
            a_eff = (a + (1/(6*np.pi)) # plane strain conditions
                * (k_i_secondary_residual / yield_stress)**2)
            phi_0_a = np.sqrt(a_eff / a)
            c_eff = (c + (1/(6*np.pi))
                * (k_i_secondary_residual / yield_stress)**2)
            phi_0_c = np.sqrt(c_eff / c)

            # TODO: is taking the more critical phi_0 correct?
            # API is unclear about which one to use.
            return np.max([phi_0_a, phi_0_c])

        ## Toughness ratio calculation
        k_i_prim = primary_stress_intensity_factor
        k_i_prim[k_i_prim < 0] = 0

        if secondary_stress_intensity_factor is None:
            k_i_sr = 0
        else:
            k_i_sr = secondary_stress_intensity_factor
            k_i_sr[k_i_sr < 0] = 0

        phi_0 = calc_phi_0(self.yield_stress,
                        k_i_sr,
                        crack_depth,
                        crack_length / 2)
        k_i_sr = phi_0 * k_i_sr

        x = k_i_sr * (load_ratio / k_i_prim)
        zeta_table = open_zeta_table(zeta_file)
        zeta = calc_zeta(zeta_table, load_ratio, x)
        phi = phi_0 * zeta
        toughness_ratio = ((k_i_prim + phi*k_i_sr)
                            / self.fracture_resistance)

        return toughness_ratio
