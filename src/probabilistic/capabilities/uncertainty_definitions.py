# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import scipy.stats as sps
import numpy as np
import matplotlib.pyplot as plt

from probabilistic.capabilities.plotting import (plot_distribution_pdf,
                                                 plot_deterministic_parameter_value,
                                                 plot_time_series_parameter_value)

""" Module for defining uncertainty definitions and capabilities. """


def specify_distribution(parameter_specification):
    """
    Generate a distribution object based on a parameter specification.

    Parameters
    ----------
    parameter_specification : dict
        Dictionary containing the specification of the desired uncertainty distribution.
        Required keys vary depending on the `distribution_type` and may include:

            - 'distribution_type': str, type of distribution (e.g., 'normal', 'beta')
            - 'uncertainty_type': str, type of uncertainty
            - 'nominal_value': float
            - Other distribution-specific parameters (e.g., 'mean', 'std_deviation', 'a', 'b')

    Returns
    -------
    UncertaintyCharacterization or DeterministicCharacterization
        A distribution object based on the specification.

    Raises
    ------
    ValueError
        If an unsupported distribution type is specified.
    """
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
    elif distribution_type == 'trunc_lognormal':
        dist = TruncatedLognormalDistribution(name=parameter_name,
                                              uncertainty_type=uncertainty_type,
                                              nominal_value=nominal_value,
                                              mu=parameter_specification['mean'],
                                              sigma=parameter_specification['std_deviation'],
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
    Representation of a deterministic parameter.

    Attributes
    ----------
    name : str
        The name of the parameter.
    value : float
        The deterministic value of the parameter.
    nominal : float
        The same as `value`, used for compatibility with uncertain parameter interface.
    """

    def __init__(self,
                 name:str,
                 value:float):
        """
        Initialize a DeterministicCharacterization instance.

        Parameters
        ----------
        name : str
            The name of the parameter.
        value : float
            The deterministic value of the parameter.
        """
        self.name = name
        self.value = value
        self.nominal = value

    def __str__(self):
        """
        Return a human-readable string representation of the object.

        Returns
        -------
        str
            A string indicating the parameter name and its deterministic value.
        """
        return f'{self.name} is a deterministic variable with value {self.value}'

    def __repr__(self):
        """
        Return a detailed string representation for debugging.

        Returns
        -------
        str
            A concise summary of the deterministic parameter.
        """
        return f'{self.name}, deterministic, {self.value}'

    def generate_samples(self, sample_size):
        """
        Generate repeated deterministic samples.

        Parameters
        ----------
        sample_size : int
            Number of samples to generate.

        Returns
        -------
        np.ndarray
            Array filled with the same deterministic value.
        """
        return np.ones(sample_size)*self.value

    def plot_distribution(self, alternative_name=False):
        """
        Create plot of uncertainty distribution.

        Parameters
        ----------
        alternative_name : str or bool, optional
            Alternative label for the plot. If False (default), uses self.name.
        """
        name = alternative_name if alternative_name else self.name
        plot_deterministic_parameter_value(self.value,
                                           name)


class TimeSeriesCharacterization(DeterministicCharacterization):
    """
    Representation of a deterministic time-series parameter.

    Attributes
    ----------
    name : str
        The name of the parameter.
    value : np.ndarray
        The deterministic time series values.
    nominal : np.ndarray
        Same as `value`, used for compatibility.
    """

    def __init__(self,
                 name: str,
                 value: np.ndarray):
        """
        Initialize the TimeSeriesCharacterization object.

        Parameters
        ----------
        name : str
            The name of the time series parameter.
        value : np.array, list
            The time series values. Should be a 1D array or list.
        """
        # Ensure value is a numpy array
        if isinstance(value, list):
            value = np.array(value)
        elif not isinstance(value, np.ndarray):
            raise ValueError("Value must be a numpy array or a list.")

        super().__init__(name, value)  # Call the parent constructor

    def __str__(self):
        """
        Return a string representation of the object.

        Returns
        -------
        str
            String representation of the object.
        """
        return f'{self.name} is a TimeSeries variable with value {self.value}'

    def __repr__(self):
        """
        Return a detailed string representation of the object.

        Returns
        -------
        str
            Detailed string representation of the object.
        """
        return f'{self.name}, time series, {self.value}'

    def generate_samples(self, sample_size):
        """
        Generate copies of the time series.

        Parameters
        ----------
        sample_size : int
            The number of samples to generate.

        Returns
        -------
        np.array
            Array of time series values repeated to match the sample size.
        """
        return np.tile(self.value, (sample_size, 1))

    def plot_distribution(self, alternative_name=False):
        """
        Create plot of uncertainty distribution.

        Parameters
        ----------
        alternative_name : str, optional
            Alternative name to use for the plot. Defaults to False.
        """
        name = alternative_name if alternative_name else self.name
        plot_time_series_parameter_value(self.value,
                                         name)


class UncertaintyCharacterization:
    """
    Generic class for uncertain (probabilistic) parameters.

    Attributes
    ----------
    name : str
        Name of the parameter.
    uncertainty_type : str
        Type of uncertainty.
    nominal : float
        Nominal value.
    distribution : object
        The actual scipy.stats distribution object.
    parameters : dict
        Parameters used to initialize the distribution.
    """

    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 distribution:str,
                 parameters:dict):
        """
        Initialize an UncertaintyCharacterization instance.

        Parameters
        ----------
        name : str
            Name of the uncertain parameter.
        uncertainty_type : str
            Type of uncertainty (e.g., 'aleatory', 'epistemic').
        nominal_value : float
            The nominal (central or reference) value for the parameter.
        distribution : str
            A reference to a SciPy distribution constructor (e.g., `scipy.stats.norm`).
        parameters : dict
            Dictionary of parameters required to initialize the distribution.
        """
        self.name = name
        self.uncertainty_type = uncertainty_type
        self.nominal = nominal_value
        self.distribution = distribution(**parameters)
        self.parameters = parameters

    def __str__(self):
        """
        Return a human-readable string representation of the object.

        Returns
        -------
        str
            Description of the uncertain parameter and its distribution.
        """
        return f'{self.name} is a probabilistic variable represented with a ' +\
               f'{self.distribution.dist.name} distribution and parameters {str(self.parameters)}'

    def __repr__(self):
        """
        Return a concise representation of the object for debugging.

        Returns
        -------
        str
            Concise summary of the uncertain parameter, including distribution and values.
        """
        repr_part1 = f'{self.name}, {self.distribution.dist.name}, {self.nominal}, '
        repr_part2 = f'{self.uncertainty_type}, '
        repr_part3 = f'{", ".join(str(x) for x in list(self.parameters.values()))}'
        return repr_part1 + repr_part2 + repr_part3

    def generate_samples(self,
                         sample_size:int,
                         random_state=np.random.default_rng()):
        """
        Generate samples from the uncertainty distribution.

        Parameters
        ----------
        sample_size : int
            Number of samples to draw.
        random_state : Generator, optional
            NumPy random number generator. If not specified, uses default_rng().

        Returns
        -------
        np.ndarray
            Array of generated samples.
        """
        return self.distribution.rvs(size=sample_size,
                                     random_state=random_state)
    
    def ppf(self, locations):
        """
        Compute the Percent Point Function (inverse CDF) at given probabilities.

        Parameters
        ----------
        locations : array_like
            Probabilities at which to evaluate the inverse CDF.

        Returns
        -------
        np.ndarray
            Quantiles corresponding to the input probabilities.
        """
        return self.distribution.ppf(locations)

    def plot_distribution(self,
                          alternative_name=False,
                          plot_limits=False):
        """
        Plot the probability density function of the distribution.

        Parameters
        ----------
        alternative_name : str or bool, optional
            Alternative name to use in the plot label. Defaults to self.name.
        plot_limits : bool, optional
            Whether to include bounds/limits in the plot. Defaults to False.
        """
        name = alternative_name if alternative_name else self.name
        plot_distribution_pdf(self.distribution,
                              name,
                              plot_limits)


class BetaDistribution(UncertaintyCharacterization):
    """
    Beta distribution-based uncertainty characterization.

    Attributes
    ----------
    name : str
    uncertainty_type : str
    nominal_value : float
    distribution : scipy.stats._distn_infrastructure.rv_frozen
    a : float
    b : float
    loc : float
    scale : float
    """

    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 a:float,
                 b:float,
                 loc:float=None,
                 scale:float=None):
        """
        Initialize a BetaDistribution instance with the given parameters.

        Parameters
        ----------
        name : str
            Name of the uncertain parameter.
        uncertainty_type : str
            Type of uncertainty (e.g., 'aleatory', 'epistemic').
        nominal_value : float
            Nominal or reference value associated with the parameter.
        a : float
            Alpha shape parameter of the beta distribution.
        b : float
            Beta shape parameter of the beta distribution.
        loc : float, optional
            Location parameter of the beta distribution. Defaults to 0 if None.
        scale : float, optional
            Scale parameter of the beta distribution. Defaults to 1 if None.
        """
        parameters = {'a': a,
                      'b': b,
                      'loc': loc,
                      'scale': scale}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.beta,
                         parameters=parameters)


class NormalDistribution(UncertaintyCharacterization):
    """
    Normal distribution-based uncertainty characterization.

    Attributes
    ----------
    name : str
    uncertainty_type : str
    nominal : float
    distribution : scipy.stats._distn_infrastructure.rv_frozen
    'loc': float
    'scale': float
    """

    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 mean:float,
                 std_deviation:float):
        """
        Initialize a NormalDistribution instance.

        Parameters
        ----------
        name : str
            Name of the uncertain parameter.
        uncertainty_type : str
            Type of uncertainty (e.g., 'aleatory', 'epistemic').
        nominal_value : float
            Nominal or reference value of the parameter.
        mean : float
            Mean (`loc`) of the normal distribution.
        std_deviation : float
            Standard deviation (`scale`) of the normal distribution.

        Notes
        -----
        Internally, the normal distribution is represented using a frozen
        `scipy.stats.norm` object with the specified `loc` and `scale`.
        """
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

    Attributes
    -----------
    name : str
    uncertainty_type : str
    nominal_value : float
    distribution : scipy.stats._distn_infrastructure.rv_frozen
    's': float
    'scale': float
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 mu:float,
                 sigma:float):
        """
        Initialize a LognormalDistribution instance.

        Parameters
        ----------
        name : str
            Name of the uncertain parameter.
        uncertainty_type : str
            Type of uncertainty (e.g., 'aleatory', 'epistemic').
        nominal_value : float
            Nominal or reference value associated with the parameter.
        mu : float
            Mean of the underlying normal distribution.
        sigma : float
            Standard deviation of the underlying normal distribution. Used as the shape parameter `s`.

        Notes
        -----
        The log-normal distribution is parameterized such that:
            - `scale = exp(mu)`
            - `s = sigma`
        The resulting distribution is `scipy.stats.lognorm(s=s, scale=exp(mu))`.
        """
        parameters = {'scale': np.exp(mu),
                      's': sigma}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.lognorm,
                         parameters=parameters)


class TruncatedNormalDistribution(UncertaintyCharacterization):
    """
    Truncated normal distribution-based uncertainty characterization.

    Attributes
    ----------
    name : str
    uncertainty_type : str
    nominal_value : float
    distribution : scipy.stats._distn_infrastructure.rv_frozen
    'loc' : float
    'scale' : float
    'a' : float
    'b' : float
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 mean:float,
                 std_deviation:float,
                 lower_bound:float,
                 upper_bound:float):
        """
        Initialize a TruncatedNormalDistribution instance.

        Parameters
        ----------
        name : str
            Name of the uncertain parameter.
        uncertainty_type : str
            Type of uncertainty (e.g., 'aleatory', 'epistemic').
        nominal_value : float
            Nominal or reference value associated with the parameter.
        mean : float
            Mean (`loc`) of the original normal distribution.
        std_deviation : float
            Standard deviation (`scale`) of the original normal distribution.
        lower_bound : float
            Lower bound of the truncated distribution.
        upper_bound : float
            Upper bound of the truncated distribution.

        Notes
        -----
        The truncation is defined in standardized form using:
            - a = (lower_bound - mean) / std_deviation
            - b = (upper_bound - mean) / std_deviation
        The resulting distribution is equivalent to:
            `scipy.stats.truncnorm(a, b, loc=mean, scale=std_deviation)`
        """
        parameters = {'loc': mean,
                      'scale': std_deviation,
                      'a': (lower_bound - mean)/std_deviation,
                      'b': (upper_bound - mean)/std_deviation}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.truncnorm,
                         parameters=parameters)


class TruncatedLognormalDistribution(UncertaintyCharacterization):
    """
    Truncated Lognormal Distribution Uncertainty Class

    Attributes
    ----------
    name : str
    uncertainty_type : str
    nominal_value : float
    distribution : scipy.stats._distn_infrastructure.rv_frozen
    'loc' : float
    'scale' : float
    'a' : float
    'b' : float
    lower_bound : float
    upper_bound : float
    """
    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 mu:float,
                 sigma:float,
                 lower_bound:float,
                 upper_bound:float):
        """
        Initialize a TruncatedLognormalDistribution instance.

        Parameters
        ----------
        name : str
            Name of the uncertain parameter.
        uncertainty_type : str
            Type of uncertainty (e.g., 'aleatory', 'epistemic').
        nominal_value : float
            Nominal or reference value associated with the parameter.
        mu : float
            Mean of the underlying normal distribution (in log space).
        sigma : float
            Standard deviation of the underlying normal distribution (in log space).
        lower_bound : float
            Lower bound of the truncated lognormal distribution (in real space).
        upper_bound : float
            Upper bound of the truncated lognormal distribution (in real space).
        """
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        parameters = {'loc': mu,
                      'scale': sigma,
                      'a': (np.log(lower_bound) - mu)/sigma,
                      'b': (np.log(upper_bound) - mu)/sigma}
        super().__init__(name=name,
                         uncertainty_type=uncertainty_type,
                         nominal_value=nominal_value,
                         distribution=sps.truncnorm,
                         parameters=parameters)

    def ppf(self, locations):
        """
        Compute the percentile point function (inverse CDF) values in real space.

        Parameters
        ----------
        locations : array_like
            Probabilities at which to evaluate the inverse CDF.

        Returns
        -------
        np.ndarray
            Quantile values in real (lognormal) space.
        """
        return np.exp(self.distribution.ppf(locations))

    def generate_samples(self,
                         sample_size:int,
                         random_state=np.random.default_rng()):
        """
        Generate samples from a truncated lognormal distribution.

        Parameters
        ----------
        sample_size : int
            Number of samples to generate.
        random_state : Generator, optional
            NumPy random number generator instance. If not provided, uses default_rng().

        Returns
        -------
        np.ndarray
            Samples drawn from the truncated lognormal distribution.
        """
        normal_samples =  self.distribution.rvs(size=sample_size,
                                                random_state=random_state)
        return np.exp(normal_samples)

    def plot_distribution(self,
                          alternative_name=False,
                          plot_limits=False):
        """
        Plot the probability density function (PDF) of the truncated lognormal distribution.

        Parameters
        ----------
        alternative_name : str or bool, optional
            Alternative label for the plot. If False (default), uses the parameter name.
        plot_limits : tuple of float or bool, optional
            Tuple (min, max) specifying x-axis limits for the plot. If False, defaults
            to 90%–110% of the lower and upper bounds.
        """
        name = alternative_name if alternative_name else self.name

        plt.figure(figsize=(4, 4))
        if not plot_limits:
            plot_limits = (self.lower_bound*.9, self.upper_bound*1.1)

        x_points = np.linspace(plot_limits[0], plot_limits[1], 100)
        y_points = self.distribution.pdf(np.log(x_points))/(x_points)

        plt.plot(x_points, y_points)
        plt.grid()
        plt.xlabel(name)
        plt.ylabel('PDF')


class UniformDistribution(UncertaintyCharacterization):
    """
    Uniform Distribution Uncertainty Class

    Attributes
    ----------
    name : str
    uncertainty_type : str
    nominal_value : float
    distribution : scipy.stats._distn_infrastructure.rv_frozen
    'loc' : float
    'scale' : float
    """

    def __init__(self,
                 name:str,
                 uncertainty_type:str,
                 nominal_value:float,
                 lower_bound:float,
                 upper_bound:float):
        """
        Initialize a UniformDistribution instance.

        Parameters
        ----------
        name : str
            Name of the uncertain parameter.
        uncertainty_type : str
            Type of uncertainty (e.g., 'aleatory', 'epistemic').
        nominal_value : float
            Nominal or reference value associated with the parameter.
        lower_bound : float
            Lower bound of the uniform distribution.
        upper_bound : float
            Upper bound of the uniform distribution.

        Raises
        ------
        ValueError
            If the lower bound is greater than the upper bound.
        """
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
