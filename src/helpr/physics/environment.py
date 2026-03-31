# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import math
import numpy as np
from scipy import constants as spc

from helpr.utilities.parameter import Parameter

"""Module to gather environmental specification for pipe"""


class EnvironmentSpecification:
    """
    Pipe interior environment specification.

    Attributes
    ----------
    max_pressure
    min_pressure
    temperature
    volume_fraction_h2
    reference_pressure
    fugacity : float
        Fugacity coefficient of blended gas.
    reference_fugacity : float
        Fugacity coefficient of pure H2.
    fugacity_ratio : 
        (fugacity / reference fugacity) ** 1/2. 
    partial_pressure : float
        Partial pressure of hydrogen gas [MPa].
    """
    def __init__(self,
                 max_pressure,
                 min_pressure,
                 temperature,
                 volume_fraction_h2,
                 reference_pressure=106.0):
        """
        Parameters
        -----------
        max_pressure : float
            Maximum pressure inside pipeline [MPa].
        min_pressure : float
            Minimum pressure inside pipeline [MPa].
        temperature : float, optional
            Temperature of gas inside pipeline [K].
        volume_fraction_h2 : float, optional
            Volume fraction of H2 in gas [%].
        reference_pressure : float
            Reference pressure for calculating fugacity [MPa], defaults to 106 MPa.
        """
        self.max_pressure = Parameter('max_pressure',
                                      value=max_pressure)
        self.min_pressure = Parameter('min_pressure',
                                      value=min_pressure,
                                      lower_bound=0,
                                      upper_bound=self.max_pressure)
        self.temperature = Parameter('temperature',
                                     value=temperature,
                                     lower_bound=230,
                                     upper_bound=330)
        self.volume_fraction_h2 = Parameter('volume_fraction_h2',
                                            value=volume_fraction_h2,
                                            lower_bound=0,
                                            upper_bound=1)
        self.reference_pressure = Parameter('reference_pressure',
                                            value=reference_pressure,
                                            lower_bound=0)
        self.calc_derived_quantities()

    def _get_max_pressure(self, index):
        return self.max_pressure

    def _get_min_pressure(self, index):
        return self.min_pressure

    def _get_partial_pressure(self, index):
        return self.partial_pressure

    def _get_fugacity_ratio(self, index):
        return self.fugacity_ratio

    def calc_derived_quantities(self):
        """Calculates other attributes based on input parameters."""
        self.fugacity = self.calc_fugacity(pressure=self.max_pressure,
                                           temperature=self.temperature,
                                           volume_fraction_h2=self.volume_fraction_h2)
        self.reference_fugacity = self.calc_fugacity(pressure=self.reference_pressure,
                                                     temperature=self.temperature,
                                                     volume_fraction_h2=1.0)
        self.fugacity_ratio = self.calc_fugacity_ratio()
        self.partial_pressure = self.max_pressure*self.volume_fraction_h2

    def calc_fugacity(self, pressure, temperature, volume_fraction_h2):
        """
        Calculates fugacity.

        Parameters
        ----------
        pressure : Parameter
            Pressure inside the pipeline [MPa].
        temperature : Parameter
            Temperature of gas inside the pipeline [K].
        volume_fraction_h2 : Parameter
            Volume fraction of H2 in gas [%].

        Returns
        -------
        float
            Computed fugacity of hydrogen [MPa].
        """
        reference_pressure = self.calc_fugacity_coefficient(pressure,
                                                            temperature)
        if isinstance(reference_pressure, float):
            return pressure*volume_fraction_h2*math.exp(reference_pressure)
        else:
            return pressure*volume_fraction_h2*np.exp(reference_pressure)

    @staticmethod
    def calc_fugacity_coefficient(pressure, temperature, co_volume=15.84):
        """
        Calculates fugacity using Abel-Noble EOS Reference Pressure.

        Parameters
        ----------
        pressure : float
            Pressure [MPa].
        temperature : float
            Temperature [K].
        co_volume : float, optional
            CO volume (b). Default is 15.84 [cm^3/mol].

        Returns
        -------
        float
            Calculated fugacity coefficient.
        """
        gas_constant = spc.R  # J/mol K
        return co_volume*pressure/(gas_constant*temperature)

    def calc_fugacity_ratio(self):
        """
        Calculates fugacity ratio.

        Returns
        -------
        float
            Calculated fugacity ratio.
        """
        return (self.fugacity/self.reference_fugacity)**(1/2)


class EnvironmentSpecificationRandomLoad(EnvironmentSpecification):
    """Pipe interior environment specification for case with random loading.

    Attributes
    ----------
    max_pressure : list, np.array
    min_pressure : list, np.array
    temperature : float
    volume_fraction_h2 : float
    reference_pressure : float, list, np.array

    fugacity : float
        Fugacity coefficient of blended gas.

    reference_fugacity : float
        Fugacity coefficient of pure H2.

    fugacity_ratio : 
        (fugacity / reference fugacity) ** 1/2.

    partial_presure :
        max pressure * H2 volume fraction

    """
    def __init__(self,
                 max_pressure,
                 min_pressure,
                 temperature,
                 volume_fraction_h2,
                 reference_pressure=106.0):
        """
        Parameters
        -----------
        max_pressure : list, np.array
            Temporal loading profile of maximum pressure inside pipeline [MPa].
        min_pressure : list, np.array
            Temporal loading profile of minimum pressure inside pipeline [MPa].
        temperature : float, optional
            Temperature of gas inside pipeline [K], defaults to 293.15 K.
        volume_fraction_h2 : float, optional
            Volume fraction of H2 in gas [%], defaults to 1%.
        reference_pressure : float
            Reference pressure for calculating fugacity [MPa], defaults to 106 MPa.

        """
        self.max_pressure = np.asarray(max_pressure)
        self.min_pressure = np.asarray(min_pressure)
        self.temperature = Parameter('temperature',
                                     value=temperature,
                                     lower_bound=230,
                                     upper_bound=330)
        self.volume_fraction_h2 = Parameter('volume_fraction_h2',
                                            value=volume_fraction_h2,
                                            lower_bound=0,
                                            upper_bound=1)
        self.reference_pressure = Parameter('reference_pressure',
                                            value=reference_pressure,
                                            lower_bound=0)
        self.calc_derived_quantities()

    def _get_max_pressure(self, index):
        return self.max_pressure[index % len(self.max_pressure)]

    def _get_min_pressure(self, index):
        return self.min_pressure[index % len(self.max_pressure)]

    def _get_partial_pressure(self, index):
        return self.partial_pressure[index % len(self.max_pressure)]

    def _get_fugacity_ratio(self, index):
        return self.fugacity_ratio[index % len(self.max_pressure)]
