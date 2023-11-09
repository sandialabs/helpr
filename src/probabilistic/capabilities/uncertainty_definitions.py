# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import scipy.stats as sps
import numpy as np

from probabilistic.capabilities.plotting import (plot_distribution_pdf,
                                                 plot_deterministic_parameter_value)

""" Module for defining uncertainty definitions and capabilities """


def specify_distribution(parameter_specification):
    '''function to generate specified distribution type object
    Parameters
    ----------
    parameter_specification: dict
        dictionary containing specification of desired uncertainty distribution
    
    Returns
    -------
    dist: UncertaintyCharacterization
        specified distribution type object

    '''
    distribution_type = parameter_specification['distribution_type']
    parameter_name = parameter_specification['name']
    if distribution_type != 'deterministic':
        uncertainty_type = parameter_specification['uncertainty_type']
        nominal_value = parameter_specification['nominal_value']

    if distribution_type == 'deterministic':
        dist = DeterministicCharacterization(name=parameter_name,
                                             value=parameter_specification['value'])
    elif distribution_type == 'beta':
        dist = BetaDistribution(name=parameter_name,
                                uncertainty_type=uncertainty_type,
                                nominal_value=nominal_value,
                                a=parameter_specification['a'],
                                b=parameter_specification['b'])
    elif distribution_type == 'normal':
        dist = NormalDistribution(name=parameter_name,
                                  uncertainty_type=uncertainty_type,
                                  nominal_value=nominal_value,
                                  mean=parameter_specification['mean'],
                                  std_deviation=parameter_specification['std_deviation'],)
    elif distribution_type == 'log_normal':
        dist = LognormalDistribution(name=parameter_name,
                                     uncertainty_type=uncertainty_type,
                                     nominal_value=nominal_value,
                                     mu=parameter_specification['mu'],
                                     sigma=parameter_specification['sigma'])
    elif distribution_type == 'trunc_normal':
        dist = TruncatedNormalDistribution(name=parameter_name,
                                           uncertainty_type=uncertainty_type,
                                           nominal_value=nominal_value,
                                           mean=parameter_specification['mean'],
                                           std_deviation=parameter_specification['std_deviation'],
                                           lower_bound=parameter_specification['lower_bound'],
                                           upper_bound=parameter_specification['upper_bound'])
    elif distribution_type == 'uniform':
        dist = UniformDistribution(name=parameter_name,
                                   uncertainty_type=uncertainty_type,
                                   nominal_value=nominal_value,
                                   lower_bound=parameter_specification['lower_bound'],
                                   upper_bound=parameter_specification['upper_bound'])
    else:
        return ValueError(f'Distribution type {distribution_type} not supported, ' +
                        'supported: deterministic, beta, normal, log_normal, ' +
                        'trunc_normal, uniform')

    return dist

class DeterministicCharacterization:
    """
    Generic Deterministic Parameter Class

    Parameters
    -----------
    name: str
    value:float
    """
    def __init__(self,
                 name:str,
                 value:float):
        self.name = name
        self.value = value
        self.nominal = value

    def __str__(self):
        return f'{self.name} is a deterministic variable with value {self.value}'

    def __repr__(self):
        return f'{self.name}, deterministic, {self.value}'

    def generate_samples(self, sample_size):
        """
        Function to generate deterministic samples (same values)
        """
        return np.ones(sample_size)*self.value

    def plot_distribution(self):
        """
        Function to create plot of uncertainty distribution
        """
        plot_deterministic_parameter_value(self.value,
                                           self.name)


class UncertaintyCharacterization:
    """
    Generic Uncertainty Distribution Class

    Parameters
    ------------
    name:str
    uncertainty_type:str
    nominal_value:float
    distribution:str
    parameters:dict
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 distribution:str,
                 parameters:dict):
        self.name = name
        self.uncertainty_type = uncertainty_type
        self.nominal = nominal_value
        self.distribution = distribution(**parameters)
        self.parameters = parameters

    def __str__(self):
        return f'{self.name} is a probabilistic variable represented with a ' +\
               f'{self.distribution.dist.name} distribution and parameters {str(self.parameters)}'

    def __repr__(self):
        repr_part1 = f'{self.name}, {self.distribution.dist.name}, {self.nominal}, '
        repr_part2 = f'{", ".join(str(x) for x in list(self.parameters.values()))}, '
        repr_part3 = f'{self.uncertainty_type}'
        return repr_part1 + repr_part2 + repr_part3

    def generate_samples(self,
                         sample_size:int,
                         random_state=np.random.default_rng()):
        """
        Function to sample from uncertainty distributions

        Parameters
        ------------
            sample_size: int
                number of samples
            random_state: generator
                np default_rng instance or will be used to create randomState instance
        """
        return self.distribution.rvs(size=sample_size,
                                     random_state=random_state)

    def plot_distribution(self,
                          plot_limits=False):
        """
        Function to create plot of uncertainty distribution
        """
        plot_distribution_pdf(self.distribution,
                              self.name,
                              plot_limits)


class BetaDistribution(UncertaintyCharacterization):
    """
    Beta Distribution Uncertainty Class

    Parameters
    ----------
    name:str
    uncertainty_type:str
    nominal_value:float
    a:float
    b:float
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 a:float,
                 b:float):
        parameters = {'a': a,
                      'b': b}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.beta,
                         parameters=parameters)


class NormalDistribution(UncertaintyCharacterization):
    """
    Normal Distribution Uncertainty Class

    Parameters
    ----------
    name:str
    uncertainty_type:str
    nominal_value:float
    mean:float
    std_deviation:float
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 mean:float,
                 std_deviation:float):
        parameters = {'loc': mean,
                      'scale': std_deviation}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.norm,
                         parameters=parameters)


class LognormalDistribution(UncertaintyCharacterization):
    """
    Log-Normal Distribution Uncertainty Class

    Parameters
    -----------
    name:str
    uncertainty_type:str
    nominal_value:float
    mu:float
    sigma:float
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 mu:float,
                 sigma:float):
        parameters = {'scale': np.exp(mu),
                      's': sigma}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.lognorm,
                         parameters=parameters)


class TruncatedNormalDistribution(UncertaintyCharacterization):
    """
    Truncated Normal Distribution Uncertainty Class

    Parameters
    ------------
    name:str
    uncertainty_type:str
    nominal_value:float
    mean:float
    std_deviation:float
    lower_bound:float
    upper_bound:float
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 mean:float,
                 std_deviation:float,
                 lower_bound:float,
                 upper_bound:float):
        parameters = {'loc': mean,
                      'scale': std_deviation,
                      'a': (lower_bound - mean)/std_deviation,
                      'b': (upper_bound - mean)/std_deviation}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.truncnorm,
                         parameters=parameters)


class UniformDistribution(UncertaintyCharacterization):
    """
    Uniform Distribution Uncertainty Class

    Parameters
    ------------
    name:str
    uncertainty_type:str
    nominal_value:float
    lower_bound:float
    upper_bound:float
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 lower_bound:float,
                 upper_bound:float):
        if lower_bound > upper_bound:
            raise ValueError(f'parameter {name} lower bound {lower_bound}'
                             f' is greater the upper bound {upper_bound}')

        parameters = {'loc': lower_bound,
                      'scale': upper_bound - lower_bound}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.uniform,
                         parameters=parameters)
