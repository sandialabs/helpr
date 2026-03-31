# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import math

from helpr.utilities.parameter import Parameter
from helpr.physics.environment import EnvironmentSpecification

class CrackGrowth:
    """
    Definition for crack growth physics model.

    Attributes
    ----------
    environment_specification
    model_arguments
    delta_k
    delta_a
    delta_n
    r_ratio
    """

    def __init__(self,
                 environment,
                 growth_model_specification):
        """
        Initialize crack growth model using a defined environment and specified model type.

        Parameters
        -----------
        environment : EnvironmentSpecification
            Specification of the gaseous environment within the pipeline.
        growth_model_specification : dict
            Specify whether ASME Code Case 2938 w/ fugacity correction (code_case_2938) 
            or a generic Paris Law (paris_law) will be used.
        """
        self.environment_specification = environment
        self.model_arguments = growth_model_specification
        self.delta_k = None
        self.delta_a = None
        self.delta_n = None
        self.r_ratio = None
        self.cycle_index = 0

    def calc_delta_n(self, delta_a, delta_k, r_ratio):
        """
        Calculates delta N (number of load cycles) based on selected crack growth model.

        Parameters
        ----------
        delta_a : float
            Change in crack size.
        delta_k : float
            Stress intensity factor range.
        r_ratio : float
            Load ratio (minimum load / maximum load), must be between 0 and 1.

        Returns
        -------
        float
            Calculated change in number of cycles (delta N).

        Raises
        ------
        ValueError
            If required model parameters are not specified or if model name is invalid.
        """
        self.delta_k = Parameter(name='delta_k',
                                 value=delta_k,
                                 lower_bound=0)
        self.delta_a = Parameter(name='delta_a',
                                 value=delta_a,
                                 lower_bound=0)
        self.r_ratio = Parameter(name='r_ratio',
                                 value=r_ratio,
                                 lower_bound=0,
                                 upper_bound=1)

        if (delta_k is None) or (delta_a is None):
            raise ValueError('delta_k or delta_a must be specified prior to calculating delta_n')

        if self.model_arguments['model_name'] == 'code_case_2938':
            return self.calc_dn_code_case_2938()

        if self.model_arguments['model_name'] == 'g_202006':
            return self.calc_dn_g202006()

        if self.model_arguments['model_name'] == 'paris_law':
            if ('c' in self.model_arguments) and ('m' in self.model_arguments):
                return self.calc_dn_paris_law(self.model_arguments['c'],
                                              self.model_arguments['m'])

            raise ValueError("""c and m must be specified in growth_model_specification
                             dictionary to use paris_law""")

        raise ValueError('crack growth model must be either code_case_2938 or paris_law')

    def calc_change_in_crack_size(self, delta_n, delta_k, r_ratio, cycle_index=0):
        """
        Calculates the change in crack size (delta A) based on cycles and selected model.

        Parameters
        ----------
        delta_n : float
            Number of load cycles.
        delta_k : float
            Stress intensity factor range.
        r_ratio : float
            Load ratio, between 0 and 1.
        cycle_index : int, optional
            Index of pressure cycle value, defaults to 0.

        Returns
        -------
        float
            Calculated change in crack size (delta A).

        Raises
        ------
        ValueError
            If required model parameters are not provided or model is invalid.
        """
        self.delta_k = Parameter(name='delta_k',
                                 value=delta_k,
                                 lower_bound=0)
        self.delta_n = Parameter(name='delta_n',
                                 value=delta_n,
                                 lower_bound=0)
        self.r_ratio = Parameter(name='r_ratio',
                                 value=r_ratio,
                                 lower_bound=0,
                                 upper_bound=1)
        self.cycle_index = cycle_index

        if (delta_k is None) or (delta_n is None):
            raise ValueError('delta_k or delta_n must be specified prior to calculating delta_n')

        if self.model_arguments['model_name'] == 'code_case_2938':
            return self.calc_da_code_case_2938()

        if self.model_arguments['model_name'] == 'g_202006':
            return self.calc_da_g202006()

        if self.model_arguments['model_name'] == 'paris_law':
            if ('c' in self.model_arguments) and ('m' in self.model_arguments):
                return self.calc_da_paris_law(self.model_arguments['c'],
                                              self.model_arguments['m'])

            raise ValueError("""c and m must be specified in growth_model_specification
                             dictionary to use paris_law""")
        print(self.model_arguments['model_name'])
        raise ValueError('crack growth model must be either code_case_2938 or paris_law')

    def calc_dn_g202006(self):
        """
        Calculate delta N using G 202006 model.

        Returns
        -------
        float
            Number of cycles (delta N).
        """
        # air curves not specified in report but assumed
        if self.environment_specification._get_partial_pressure(self.cycle_index) == 0:
            return self.calc_air_curve_dn()

        # delta K limit in units of MPa m^1/2
        # multiplying partial pressure x 10 to convert from MPa to bar.
        delta_k_limit = (3.6667E-6*
                         math.sqrt(self.environment_specification._get_partial_pressure(self.cycle_index)*10) )**(-0.25)
        if self.delta_k < delta_k_limit:
            # air_curve = self.calc_air_curve_dn()
            # return min(self.calc_g202006_dn_lower_k(), air_curve)
            return self.calc_g202006_dn_lower_k()

        return self.calc_g202006_dn_higher_k()

    def calc_da_g202006(self):
        """
        Calculate delta A using G 202006 model.

        Returns
        -------
        float
            Change in crack size (delta A).
        """
        # air curves not specified in report but assumed
        if self.environment_specification._get_partial_pressure(self.cycle_index) == 0:
            return self.calc_air_curve_da()

        # delta K limit in units of MPa m^1/2
        # multiplying partial pressure x 10 to convert from MPa to bar.
        delta_k_limit = (3.6667E-6*
                         math.sqrt(self.environment_specification._get_partial_pressure(self.cycle_index)*10) )**(-0.25)
        if self.delta_k < delta_k_limit:
            # air_curve = self.calc_air_curve_da()
            # return min(self.calc_g202006_da_lower_k(), air_curve)
            return self.calc_g202006_da_lower_k()

        return self.calc_g202006_da_higher_k()

    def calc_dn_code_case_2938(self):
        """
        Calculate delta N using Code Case 2938.

        Returns
        -------
        float
            Change in number of cycles.
        """
        dn_code_case_2938_lower_k = self.calc_code_case_2938_dn_lower_k()
        dn_code_case_2938_higher_k = self.calc_code_case_2938_dn_higher_k()
        dn_air_curve = self.calc_air_curve_dn()
        # Note while da/dn = f would use min(f), dn = da/f uses max(da/f)
        delta_n = max(dn_code_case_2938_lower_k, dn_code_case_2938_higher_k)
        delta_n = min(delta_n, dn_air_curve)
        return delta_n

    def calc_da_code_case_2938(self):
        """
        Calculate delta A using Code Case 2938.

        Returns
        -------
        float
            Change in crack size.
        """
        da_code_case_2938_lower_k = self.calc_code_case_2938_da_lower_k()
        da_code_case_2938_higher_k = self.calc_code_case_2938_da_higher_k()
        da_air_curve = self.calc_air_curve_da()
        # Note while da/dn = f would use min(f), da = dn*f uses min(dn*f)
        delta_a = min(da_code_case_2938_lower_k, da_code_case_2938_higher_k)
        delta_a = max(delta_a, da_air_curve)
        return delta_a

    def calc_air_curve_dn(self, c=6.89E-12, m=3):
        """
        Delta N from air curve using default Paris Law.

        Parameters
        ----------
        c : float, optional
            Paris Law constant.
        m : float, optional
            Paris Law exponent.

        Returns
        -------
        float
            Change in number of cycles.
        """
        return self.calc_dn_paris_law(c, m)

    def calc_code_case_2938_dn_lower_k(self,
                                       parameter=3.5E-14,
                                       m=6.5,
                                       multiplier=0.4286):
        """
        Calculates delta N using Code Case 2938 at lower K.

        Parameters
        ----------
        parameter : float
            Paris Law parameter.
        m : float
            Paris Law exponent.
        multiplier : float
            Multiplier for fugacity correction.

        Returns
        -------
        float
            Change in number of cycles.
        """
        c = self.calc_fugacity_correction(parameter, multiplier, case='low')
        return self.calc_dn_paris_law(c, m)

    def calc_code_case_2938_dn_higher_k(self,
                                        parameter=1.5E-11,
                                        m=3.66,
                                        multiplier=2):
        """
        Calculate delta N (number of cycles) for higher K values using Code Case 2938.

        This method applies a stress-driven model with fugacity correction for hydrogen environments,
        using the Paris Law.

        Parameters
        ----------
        parameter : float, optional
            Base Paris Law coefficient. Default is 1.5E-11.
        m : float, optional
            Paris Law exponent. Default is 3.66.
        multiplier : float, optional
            Multiplier for fugacity correction. Default is 2.

        Returns
        -------
        float
            Estimated number of load cycles (delta N) for higher K values.
        """
        c = self.calc_fugacity_correction(parameter, multiplier, case='high')
        return self.calc_dn_paris_law(c, m)

    def calc_air_curve_da(self, c=6.89E-12, m=3):
        """
        Calculate delta A (crack size increment) based on an air reference curve.

        Uses a default Paris Law with typical values for air.

        Parameters
        ----------
        c : float, optional
            Paris Law constant. Default is 6.89E-12.
        m : float, optional
            Paris Law exponent. Default is 3.

        Returns
        -------
        float
            Crack size increment (delta A).
        """
        return self.calc_da_paris_law(c, m)

    def calc_code_case_2938_da_lower_k(self,
                                       parameter=3.5E-14,
                                       m=6.5,
                                       multiplier=0.4286):
        """
        Calculate delta A (crack size increment) for lower K values using Code Case 2938.

        This method applies a hydrogen-driven model with fugacity correction,
        based on the Paris Law.

        Parameters
        ----------
        parameter : float, optional
            Base Paris Law coefficient. Default is 3.5E-14.
        m : float, optional
            Paris Law exponent. Default is 6.5.
        multiplier : float, optional
            Multiplier for fugacity correction. Default is 0.4286.

        Returns
        -------
        float
            Crack size increment (delta A).
        """
        c = self.calc_fugacity_correction(parameter, multiplier, case='low')
        return self.calc_da_paris_law(c, m)

    def calc_code_case_2938_da_higher_k(self,
                                        parameter=1.5E-11,
                                        m=3.66,
                                        multiplier=2):
        """
        Calculates delta a (change in crack size) for higher
        K values following code case 2938 (stress driven).

        Parameters
        ----------
        parameter : float, optional
            Base Paris Law constant for crack growth. Default is 1.5E-11.
        m : float, optional
            Paris Law exponent. Default is 3.66.
        multiplier : float, optional
            Multiplier applied to the fugacity correction term. Default is 2.

        Returns
        -------
        float
            Estimated crack size increment (Δa) in meters.
        """
        c = self.calc_fugacity_correction(parameter, multiplier, case='high')
        return self.calc_da_paris_law(c, m)

    def calc_g202006_dn_higher_k(self,
                                 parameter=1.2E-7,
                                 m=3,
                                 multiplier=3):
        """
        Calculates delta a (change in crack size) for high K values
        following DVGW Research Project G 202006 Final Report page 171.
        Dividing parameter by 1000 to convert from mm/cycle to m/cycle

        Parameters
        ----------
        parameter : float
            Paris Law parameter.
        m : float
            Paris Law exponent.
        multiplier : float
            Correction multiplier.

        Returns
        -------
        float
            Change in number of cycles.
        """
        c = self.calc_partial_pressure_correction(parameter/1000, multiplier, case='high')
        return self.calc_dn_paris_law(c, m)

    def calc_g202006_dn_lower_k(self,
                                 parameter=4.4E-13,
                                 m=7,
                                 multiplier=3):
        """
        Calculates delta a (change in crack size) for high K values
        following DVGW Research Project G 202006 Final Report page 171.
        Dividing parameter by 1000 to convert from mm/cycle to m/cycle

        Parameters
        ----------
        parameter : float
            Paris Law parameter.
        m : float
            Paris Law exponent.
        multiplier : float
            Correction multiplier.

        Returns
        -------
        float
            Change in number of cycles.
        """
        c = self.calc_partial_pressure_correction(parameter/1000, multiplier, case='low')
        return self.calc_dn_paris_law(c, m)

    def calc_g202006_da_higher_k(self,
                                 parameter=1.2E-7,
                                 m=3,
                                 multiplier=3):
        """
        Calculates delta a (change in crack size) for high K values
        following DVGW Research Project G 202006 Final Report page 171.
        Dividing parameter by 1000 to convert from mm/cycle to m/cycle

        Parameters
        ----------
        parameter : float
            Paris Law parameter.
        m : float
            Paris Law exponent.
        multiplier : float
            Correction multiplier.

        Returns
        -------
        float
            Change in crack size.
        """
        c = self.calc_partial_pressure_correction(parameter/1000, multiplier, case='high')
        return self.calc_da_paris_law(c, m)

    def calc_g202006_da_lower_k(self,
                                 parameter=4.4E-13,
                                 m=7,
                                 multiplier=3):
        """
        Calculates delta a (change in crack size) for high K values
        following DVGW Research Project G 202006 Final Report page 171.
        Dividing parameter by 1000 to convert from mm/cycle to m/cycle

        Parameters
        ----------
        parameter : float
            Paris Law parameter.
        m : float
            Paris Law exponent.
        multiplier : float
            Correction multiplier.

        Returns
        -------
        float
            Change in crack size.
        """ 
        c = self.calc_partial_pressure_correction(parameter/1000, multiplier, case='low')
        return self.calc_da_paris_law(c, m)

    def calc_partial_pressure_correction(self, p, multiplier, case):
        """
        Calculates hydrogen partial pressure correction for delta a.
        Multiplying partial pressure x10 to convert from MPa to bar.

        Parameters
        ----------
        p : float
            Paris Law base constant.
        multiplier : float
            Correction multiplier.
        case : str
            'low' or 'high', indicating the K-region.

        Returns
        -------
        float
            Corrected Paris Law coefficient.
        """
        if case == 'low':
            return p*(1 + multiplier*self.r_ratio) * \
                math.sqrt(self.environment_specification._get_partial_pressure(self.cycle_index)*10)

        if case == 'high':
            return p*(1 + multiplier*self.r_ratio)

        raise ValueError('code case must be specified as high or low')


    def calc_fugacity_correction(self, p, multiplier, case):
        """
        Calculate fugacity correction for Code Case 2938.

        Parameters
        ----------
        p : float
            Base Paris Law coefficient.
        multiplier : float
            Correction multiplier.
        case : str
            'low' or 'high'.

        Returns
        -------
        float
            Corrected Paris Law coefficient.
        """
        fugacity_ratio = self.environment_specification._get_fugacity_ratio(self.cycle_index)
        if case == 'low':
            return (fugacity_ratio * p * (
                    1 + multiplier*self.r_ratio) / (1 - self.r_ratio)
                    if self.r_ratio < 1
                    else 0)

        if case == 'high':
            return (p * (1 + multiplier*self.r_ratio) / (1 - self.r_ratio)
                    if (self.r_ratio < 1) & (fugacity_ratio > 0)
                    else 0)

        raise ValueError('code case must be specified as high or low')

    def calc_dn_paris_law(self, c, m):
        """
        Calculates delta N using Paris Law: delta_N = delta_a / (c * delta_K^m)

        Parameters
        ----------
        c : float
            Paris Law constant.
        m : float
            Paris Law exponent.

        Returns
        -------
        float
            Calculated change in number of cycles.
            Returns math.inf if any value is non-positive.
        """
        return (self.delta_a/(c*self.delta_k**m)
                if (self.delta_k > 0) & (self.delta_a > 0) & (c > 0)
                else math.inf)

    def calc_da_paris_law(self, c, m):
        """
        Calculates delta A using Paris Law: delta_A = delta_N * (c * delta_K^m)

        Parameters
        ----------
        c : float
            Paris Law constant.
        m : float
            Paris Law exponent.

        Returns
        -------
        float
            Change in crack size.
            Returns 0 if any value is non-positive.
        """
        return (self.delta_n*(c*self.delta_k**m)
                if (self.delta_k > 0) & (self.delta_n > 0) & (c > 0)
                else 0)


def get_design_curve(specified_r,
                     max_pressure=None,
                     min_pressure=None,
                     temperature=None,
                     volume_fraction_h2=None,
                     environment_obj=None,
                     crack_growth_model=None,
                     samples=99):
    """
    Generates design curves (ΔK vs. da/dN) for given material/environment.

    Parameters
    ----------
    specified_r : float
        Load ratio R.
    specified_fugacity : float, optional
        Fugacity ratio to override environment's default.
    max_pressure : float, optional
        Maximum pressure in MPa.
    min_pressure : float, optional
        Minimum pressure in MPa.
    temperature : float, optional
        Temperature in Kelvin.
    volume_fraction_h2 : float, optional
        Volume fraction of hydrogen in gas.
    environment_obj : EnvironmentSpecification, optional
        Predefined environment object. Used if pressure/temp/H2 are not given.
    crack_growth_model : dict, optional
        Crack growth model specification dictionary.
    samples : int, optional
        Number of samples in the curve.

    Returns
    -------
    delta_k : list of float
        ΔK values used for the curve.
    da_dn : list of float
        Corresponding da/dN values computed from the model.

    Raises
    ------
    ValueError
        If insufficient environment input is provided.
    """
    if crack_growth_model is None:
        crack_growth_model={'model_name': 'code_case_2938'}

    if (max_pressure is not None and
        min_pressure is not None and
        temperature is not None and
        volume_fraction_h2 is not None):

        environment = EnvironmentSpecification(max_pressure=max_pressure,
                                               min_pressure=min_pressure,
                                               temperature=temperature,
                                               volume_fraction_h2=volume_fraction_h2)
    elif environment_obj is not None:
        environment = environment_obj
    else:
        raise ValueError("Either temperature, volume_fraction, max_pressure, and min_presure " +
                         "must be specified or environment_obj must be provided.")

    crack_growth = CrackGrowth(environment=environment,
                               growth_model_specification=crack_growth_model)
    delta_a = [0.01] * samples
    delta_k = list(range(1, samples + 1))
    da_dn = [da/crack_growth.calc_delta_n(delta_a=da, delta_k=dk, r_ratio=specified_r)
                      for da, dk in zip(delta_a, delta_k)]
    return delta_k, da_dn
