# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import multiprocessing as mp
import functools
from joblib import Parallel, delayed
from typing import Callable

"""Script to holder parallelization functions"""


def parallel_function_evaluations(input_function:Callable,
                                  input_dictionary_list:list,
                                  number_of_cpu:int=None,
                                  additional_inputs=None) -> list:
    """
    Function to evaluate a function with a dictionary input in a parallel fashion
    
    Parameters
    ----------
    input_function : Callable
        The function to evaluate in parallel. It must accept keyword arguments from
        each dictionary in `input_dictionary_list`, as well as any additional inputs.
    input_dictionary_list : list of dict
        A list where each item is a dictionary of keyword arguments to be passed to
        `input_function`.
    number_of_cpu : int, optional
        Number of CPU cores to use for parallelization. If None, uses all available cores.
    additional_inputs : dict, optional
        Additional keyword arguments to pass to `input_function` via `functools.partial`.

    Returns
    -------
    list
        A list of results returned by applying `input_function` to each dictionary
        in `input_dictionary_list`.
    """
    if number_of_cpu == None:
        number_of_cpu = mp.cpu_count()
    
    if additional_inputs == None:
        additional_inputs = {}
    
    f_partial = functools.partial(input_function, **additional_inputs)

    return Parallel(n_jobs=number_of_cpu)(
        delayed(f_partial)(input_dictionary) for input_dictionary in input_dictionary_list)
