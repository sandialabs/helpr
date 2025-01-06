# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np


class Parameter(np.ndarray):
    """Class to enable checking and enforcing parameter bounds. """
    def __new__(cls,
                name,
                values,
                lower_bound=0,
                upper_bound=np.inf,
                size=False,
                dtype=float,
                error_function=ValueError):
        """
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
        size: bool or int
            Number of values, defaults to False to skip error checking.
        dtype : type
            Data type, defaults to float.
        error_function: func
            Function used to return bounds check message, defaults to ValueError.
        """
        array = cls.ensure_array(values, size, dtype)
        cls.parameter_bounds_check(name, array, lower_bound, upper_bound, error_function)
        return array

    @staticmethod
    def ensure_array(obj, size, dtype):
        """Checks that object is an array and converts it otherwise. """
        if isinstance(obj, np.ndarray):
            return obj if not size else Parameter.check_size(obj, size, dtype)

        if not size:
            return np.array([obj], dtype=dtype).flatten()

        return Parameter.check_size(np.array([obj]).flatten(), size, dtype)

    @staticmethod
    def check_size(obj, size, dtype):
        """Ensures object is of desired size. """
        if len(obj) == 1:
            return np.array([obj[0]]*size, dtype=dtype)

        if len(obj) == size:
            return obj

        raise ValueError(f'size of array obj {obj} not equal to expected size {size}')

    @staticmethod
    def parameter_bounds_check(name, parameter_values, lower_bound, upper_bound, error_function):
        """Checks that parameter values are within specified bounds. """
        if ((lower_bound <= parameter_values) & (parameter_values <= upper_bound)).all():
            pass
        else:
            raise error_function(f"""{name} values not all within expected bounds.
                                 Minimum and maximum parameter values:
                                 {parameter_values.min()} {parameter_values.max()}
                                 Specified bounds: {lower_bound}, {upper_bound}.""")


def divide_by_dataframe(numerator, denominator):
    """Calculate division of a numpy array by a pandas DataFrame. """
    if numerator.size > 1:
        return numerator/denominator
    return numerator[0]/denominator


def subtract_dataframe(minuend, subtrahend):
    """Calculate subtraction of a numpy array by a pandas DataFrame. """
    if minuend.size > 1:
        return minuend - subtrahend
    return minuend[0] - subtrahend
