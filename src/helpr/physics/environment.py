# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np
from scipy import constants as spc

from helpr.utilities.parameter import Parameter

"""Module to gather environmental specification for pipe"""


class EnvironmentSpecification:
    """Pipe interior environment specification.

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
    
    r_ratio : float
        Max pressure / min pressure.

    """
    def __init__(self,
                 max_pressure,
                 min_pressure,
                 sample_size=1,
                 temperature=293,
                 volume_fraction_h2=1,
                 reference_pressure=106):
        """
        Parameters
        -----------
        max_pressure : float
            Maximum pressure inside pipeline [MPa].
        min_pressure : float
            Minimum pressure inside pipeline [MPa].
        sample_size : int, optional
            Study sample size, defaults to 1.
        temperature : int, optional
            Temperature of gas inside pipeline [K], defaults to 293 K.
        volume_fraction_h2 : int, optional
            Volume fraction of H2 in gas [%], defaults to 1%.
        reference_pressure : int
            Reference pressure for calculating fugacity [MPa], defaults to 106 MPa.

        """
        self.max_pressure = Parameter('max_pressure',
                                      max_pressure,
                                      size=sample_size)
        self.min_pressure = Parameter('min_pressure',
                                      min_pressure,
                                      lower_bound=0,
                                      upper_bound=self.max_pressure,
                                      size=sample_size)
        self.temperature = Parameter('temperature',
                                     temperature,
                                     lower_bound=230,
                                     upper_bound=330,
                                     size=sample_size)
        self.volume_fraction_h2 = Parameter('volume_fraction_h2',
                                            volume_fraction_h2,
                                            lower_bound=0,
                                            upper_bound=1,
                                            size=sample_size)
        self.reference_pressure = Parameter('reference_pressure',
                                            reference_pressure,
                                            size=sample_size,
                                            lower_bound=0)
        self.calc_derived_quantities()

    def get_single_environment(self, sample_index):
        """Extracts a single environment instance from an ensemble.
        
        Parameters
        ----------
        sample_index : int
            Index of requested pipe instance.

        Returns
        -------
        EnvironmentSpecification
            Specification for the pipe instance.
        
        """
        single_max_pressure = self.max_pressure[sample_index] \
            if len(self.max_pressure) > sample_index else self.max_pressure
        single_min_pressure = self.min_pressure [sample_index] \
            if len(self.min_pressure) > sample_index else self.min_pressure
        single_temperature = self.temperature[sample_index] \
            if len(self.temperature) > sample_index else self.temperature
        single_volume_fraction_h2 = self.volume_fraction_h2[sample_index] \
            if len(self.volume_fraction_h2) > sample_index else self.volume_fraction_h2
        single_reference_pressure = self.reference_pressure[sample_index] \
            if len(self.reference_pressure) > sample_index else self.reference_pressure
        return EnvironmentSpecification(max_pressure=single_max_pressure,
                                        min_pressure=single_min_pressure,
                                        temperature=single_temperature,
                                        volume_fraction_h2=single_volume_fraction_h2,
                                        reference_pressure=single_reference_pressure,
                                        sample_size=1)

    def calc_derived_quantities(self):
        """Calculates other attributes based on input parameters. """
        self.fugacity = self.calc_fugacity(pressure=self.max_pressure,
                                           temperature=self.temperature,
                                           volume_fraction_h2=self.volume_fraction_h2)
        self.reference_fugacity = self.calc_fugacity(pressure=self.reference_pressure,
                                                     temperature=self.temperature,
                                                     volume_fraction_h2=1)
        self.fugacity_ratio = self.calc_fugacity_ratio()
        self.r_ratio = self.calc_r_ratio()

    def calc_fugacity(self, pressure, temperature, volume_fraction_h2):
        """Calculates fugacity. """
        reference_pressure = self.calc_fugacity_coefficient(pressure,
                                                            temperature)
        return pressure*volume_fraction_h2*np.exp(reference_pressure)

    @staticmethod
    def calc_fugacity_coefficient(pressure, temperature, co_volume=15.84):
        """Calculates fugacity using Abel-Noble EOS Reference Pressure.

        Parameters
        ----------
        pressure : float
            Pressure [MPa].
        temperature :float
            Temperature [K].
        co_volume : float, optional
            CO volume (b), defaults to 15.84 [cm^3/mol].

        Returns
        -------
        reference_pressure : float

        """
        gas_constant = spc.R  # J/mol K
        return co_volume*pressure/(gas_constant*temperature)

    def calc_fugacity_ratio(self):
        """Calculates fugacity ratio. """
        return (self.fugacity/self.reference_fugacity)**(1/2)

    def calc_r_ratio(self):
        """Calculates r ratio. """
        return self.min_pressure/self.max_pressure
