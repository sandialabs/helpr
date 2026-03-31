# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np


class Parameter(float):
    """
    Class to enable checking and enforcing parameter bounds.
    
    Attributes
    ----------
    name
    value
    lower_bound
    upper_bound
    error_function
    """

    def __new__(cls,
                name,
                value,
                lower_bound=0,
                upper_bound=np.inf,
                error_function=ValueError):
        """
        Creates a new Parameter instance with bound-checking.

        Parameters
        ----------
        name : str
            Name of the parameter.
        values : list
            Parameter values.
        lower_bound: int
            Lower bound for values, defaults to 0.
        upper_bound
            Upper bound for values, defaults to np.inf.
        error_function: func
            Function used to return bounds check message, defaults to ValueError.
        
        Returns
        -------
        Parameter
            A new instance of the Parameter class.

        Raises
        ------
        error_function
            If `value` is outside the range [`lower_bound`, `upper_bound`].
        ValueError
            If `value` is a list or array with more than one element.
        """
        value = cls.check_size(value, name)
        cls.parameter_bounds_check(name, value, lower_bound, upper_bound, error_function)
        return value

    @staticmethod
    def check_size(obj, name):
        """
        Ensures object is a float, or extracts float from single element array or list.
        
        Parameters
        ----------
        obj : float, list, or np.ndarray
            Input object to check.
        name : str
            Name of the parameter (for error reporting).

        Returns
        -------
        float
            The extracted or cast float value.

        Raises
        ------
        ValueError
            If the input is a list/array with more than one element.
        """
        if isinstance(obj, (list, np.ndarray)):
            if len(obj) > 1:
                raise ValueError(f'{name} must be a float, not an array or list of length > 1')

            return float(obj[0])

        return float(obj)

    @staticmethod
    def parameter_bounds_check(name, value, lower_bound, upper_bound, error_function):
        """
        Checks that parameter values are within specified bounds.
        
        Parameters
        ----------
        name : str
            Name of the parameter.
        value : float
            Value to check.
        lower_bound : float
            Minimum acceptable value.
        upper_bound : float
            Maximum acceptable value.
        error_function : callable
            Function to raise in case of bound violation.

        Raises
        ------
        error_function
            If the value is not within the bounds.
        """
        if (lower_bound <= value) & (value <= upper_bound):
            pass
        else:
            raise error_function(f"""{name} value not all within expected bounds.
                                 Parameter value: {value} ,
                                 Specified bounds: {lower_bound}, {upper_bound}.""")


def get_length(data):
    """
    Returns the 'length' of the input data.

    Parameters
    ----------
    data : float, int, list, or np.ndarray
        Input data to evaluate.

    Returns
    -------
    int
        Length of the input if it's a list or array; 1 if it's a float or int.

    Raises
    ------
    ValueError
        If the input is of an unsupported type.
    """
    if isinstance(data, (list, np.ndarray)):
        return len(data)

    if isinstance(data, (float, int)):
        return 1

    # may want to make this error message report the current datatype
    raise ValueError(f'{data} must be list, array, or float')
