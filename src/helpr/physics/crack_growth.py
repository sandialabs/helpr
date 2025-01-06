# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np

from helpr.utilities.parameter import Parameter
from helpr.physics.environment import EnvironmentSpecification

class CrackGrowth:
    """Definition for crack growth physics model.

    Attributes
    ----------
    environment_specification
    model_arguments
    sample_size
    delta_k
    delta_a
    delta_n
    
    """

    def __init__(self, environment, growth_model_specification, sample_size=1):
        """Initialize crack growth model using a defined environment and specified model type.

        Parameters
        -----------
        environment : EnvironmentSpecification
            Specification of the gaseous environment within the pipeline.
        growth_model_specification : dict
            Specify whether ASME Code Case 2938 w/ fugacity correction (code_case_2938) 
            or a generic Paris Law (paris_law) will be used.
        sample_size : int, optional
            Study sample size, defaults to 1.

        """
        self.environment_specification = environment
        self.model_arguments = growth_model_specification
        self.sample_size = sample_size
        self.delta_k = None
        self.delta_a = None
        self.delta_n = None

    def get_single_crack_growth_model(self, sample_index):
        """Creates a crack growth object for a single instance from ensemble. 
        
        Parameters
        ----------
        single_pipe_index : int
            Index of requested pipe instance.

        """
        single_environment_specification = \
            self.environment_specification.get_single_environment(sample_index)
        return CrackGrowth(environment=single_environment_specification,
                            growth_model_specification=self.model_arguments,
                            sample_size=1)

    def calc_delta_n(self, delta_a, delta_k):
        """"Calculates delta N (change in number of cycles). """
        self.delta_k = Parameter(name='delta_k',
                                 values=delta_k,
                                 lower_bound=0,
                                 size=self.sample_size)
        self.delta_a = Parameter(name='delta_a',
                                 values=delta_a,
                                 lower_bound=0,
                                 size=self.sample_size)

        if (delta_k is None) or (delta_a is None):
            raise ValueError('delta_k or delta_a must be specified prior to calculating delta_n')

        if self.model_arguments['model_name'] == 'code_case_2938':
            return self.calc_dn_code_case_2938()

        if self.model_arguments['model_name'] == 'paris_law':
            if ('c' in self.model_arguments) and ('m' in self.model_arguments):
                return self.calc_dn_paris_law(self.model_arguments['c'],
                                              self.model_arguments['m'])

            raise ValueError("""c and m must be specified in growth_model_specification
                             dictionary to use paris_law""")

        raise ValueError('crack growth model must be either code_case_2938 or paris_law')

    def calc_change_in_crack_size(self, delta_n, delta_k):
        """Calculates the change in crack size given delta_k.
        """
        self.delta_k = Parameter(name='delta_k',
                                 values=delta_k,
                                 lower_bound=0,
                                 size=self.sample_size)
        self.delta_n = Parameter(name='delta_n',
                                 values=delta_n,
                                 lower_bound=0,
                                 size=self.sample_size)


        if (delta_k is None) or (delta_n is None):
            raise ValueError('delta_k or delta_n must be specified prior to calculating delta_n')

        if self.model_arguments['model_name'] == 'code_case_2938':
            return self.calc_da_code_case_2938()

        if self.model_arguments['model_name'] == 'paris_law':
            if ('c' in self.model_arguments) and ('m' in self.model_arguments):
                return self.calc_da_paris_law(self.model_arguments['c'],
                                              self.model_arguments['m'])

            raise ValueError("""c and m must be specified in growth_model_specification
                             dictionary to use paris_law""")

        raise ValueError('crack growth model must be either code_case_2938 or paris_law')

    def calc_dn_code_case_2938(self):
        """Uses code case 2938 to calculate delta N. """
        dn_code_case_2938_lower_k = self.calc_code_case_2938_dn_lower_k()
        dn_code_case_2938_higher_k = self.calc_code_case_2938_dn_higher_k()
        dn_air_curve = self.calc_air_curve_dn()
        # Note while da/dn = f would use min(f), dn = da/f uses max(da/f)
        delta_n = np.maximum(dn_code_case_2938_lower_k,
                             dn_code_case_2938_higher_k)
        delta_n = np.minimum(delta_n,
                             dn_air_curve)
        return delta_n

    def calc_da_code_case_2938(self):
        """Uses code case 2938 to calculate delta A. """
        da_code_case_2938_lower_k = self.calc_code_case_2938_da_lower_k()
        da_code_case_2938_higher_k = self.calc_code_case_2938_da_higher_k()
        da_air_curve = self.calc_air_curve_da()
        # Note while da/dn = f would use min(f), da = dn*f uses min(dn*f)
        delta_a = np.minimum(da_code_case_2938_lower_k,
                             da_code_case_2938_higher_k)
        delta_a = np.maximum(delta_a,
                             da_air_curve)
        return delta_a

    def calc_air_curve_dn(self, c=6.89E-12, m=3):
        """Calculates delta n (change in # of cycles) from air curve. """
        return self.calc_dn_paris_law(c, m)

    def calc_code_case_2938_dn_lower_k(self,
                                       parameter=3.5E-14,
                                       m=6.5,
                                       multiplier=0.4286):
        """
        Calculates delta n (change in # of cycles) for lower k values
        following code case 2938 (hydrogen driven).
        """
        c = self.calc_fugacity_correction(parameter, multiplier, case='low')
        return self.calc_dn_paris_law(c, m)

    def calc_code_case_2938_dn_higher_k(self,
                                        parameter=1.5E-11,
                                        m=3.66,
                                        multiplier=2):
        """
        Calculates delta n (change in # of cycles) for higher
        k values following code case 2938 (stress driven).
        """
        c = self.calc_fugacity_correction(parameter, multiplier, case='high')
        return self.calc_dn_paris_law(c, m)

    def calc_air_curve_da(self, c=6.89E-12, m=3):
        """Calculates delta a (change in crack size) from air curve. """
        return self.calc_da_paris_law(c, m)

    def calc_code_case_2938_da_lower_k(self,
                                       parameter=3.5E-14,
                                       m=6.5,
                                       multiplier=0.4286):
        """
        Calculates delta a (change in crack size) for lower k values
        following code case 2938 (hydrogen driven). 
        """
        c = self.calc_fugacity_correction(parameter, multiplier, case='low')
        return self.calc_da_paris_law(c, m)

    def calc_code_case_2938_da_higher_k(self,
                                        parameter=1.5E-11,
                                        m=3.66,
                                        multiplier=2):
        """
        Calculates delta a (change in crack size) for higher
        k values following code case 2938 (stress driven).
        """
        c = self.calc_fugacity_correction(parameter, multiplier, case='high')
        return self.calc_da_paris_law(c, m)

    def calc_fugacity_correction(self, p, multiplier, case):
        """Calculates hydrogen fugacity correction for delta n (change in # of cycles). """
        r_ratio = self.environment_specification.r_ratio
        fugacity_ratio = self.environment_specification.fugacity_ratio
        if case == 'low':
            return np.where(r_ratio < 1,
                            fugacity_ratio*p*(1 + multiplier*r_ratio)/(1 - r_ratio),
                            0)

        if case == 'high':
            return np.where((r_ratio < 1) & (fugacity_ratio > 0), 
                            p*(1 + multiplier*r_ratio)/(1 - r_ratio),
                            0)

        raise ValueError('code case must be specified as high or low')

    def calc_dn_paris_law(self, c, m):
        """Calculates delta n (change in # of cycles) from general paris law form. """
        filtering_criteria = (self.delta_k > 0) & (self.delta_a > 0) # & (c > 0)
        dn = np.zeros_like(self.delta_a)
        delta_n = self.delta_a/(c*self.delta_k**m)
        dn[filtering_criteria] = delta_n[filtering_criteria]
        return dn

    def calc_da_paris_law(self, c, m):
        """Calculates delta a (change in crack size) from general paris law form. """
        filtering_criteria = (self.delta_k > 0) & (self.delta_n > 0) & (c > 0)
        da = np.zeros_like(self.delta_n)
        delta_a = self.delta_n*(c*self.delta_k**m)
        da[filtering_criteria] = delta_a[filtering_criteria]
        return da


def get_design_curve(specified_r,
                     specified_fugacity,
                     crack_growth_model=None,
                     samples=99):
    """Extracts ASME design curves from model. 
    
    Parameters
    ----------
    specified_r : float
        R value.
    specified_fugacity : float
        Fugacity coefficient. 
    crack_growth_model : CrackGrowth, optional
        Specified crack growth model, defaults to code case 2938.
    samples : int, optional
        Number of samples.

    Returns
    -------
    delta_k : list
        List of delta K values.
    da_dn : list
        List of delta A / delta N values. 

    """

    if crack_growth_model is None:
        crack_growth_model={'model_name': 'code_case_2938'}

    environment = EnvironmentSpecification(max_pressure=1,
                                            min_pressure=1,
                                            sample_size=samples)

    environment.r_ratio = specified_r
    environment.fugacity_ratio = specified_fugacity
    crack_growth = CrackGrowth(environment=environment,
                               growth_model_specification=crack_growth_model,
                               sample_size=samples)
    delta_a = 0.01*np.ones(samples)
    delta_k = np.arange(1, samples+1)
    return delta_k, delta_a/crack_growth.calc_delta_n(delta_a=delta_a,
                                                      delta_k=delta_k)
