# Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import numpy as np
from scipy.stats import qmc

from probabilistic.capabilities.uncertainty_definitions import (UncertaintyCharacterization,
                                                   DeterministicCharacterization)

""" module for sampling uncertainty definitions """


class UncertaintyStudy:
    """
    Generic Uncertainty Study Class

    Parameters
    ------------
    number_of_aleatory_samples:int
    number_of_epistemic_samples:int
    random_state
    """
    def __init__(self,
                 number_of_aleatory_samples:int,
                 number_of_epistemic_samples:int,
                 random_state):

        self.number_of_aleatory_samples = number_of_aleatory_samples
        self.number_of_epistemic_samples = number_of_epistemic_samples
        self.aleatory_variables = {}
        self.epistemic_variables = {}
        self.deterministic_variables = {}
        self.sample_sheet = {}
        self.nominal_sample_sheet = {}
        self.total_sample_size = None
        self.random_state = random_state

    def get_parameter_names(self):
        """function to both deterministic and probabilistic variable names"""
        return list(self.deterministic_variables.keys()) + list(self.aleatory_variables.keys()) +\
              list(self.epistemic_variables.keys())

    def get_uncertain_parameter_names(self):
        """function to determine total number of uncertain variables in study"""
        return list(self.aleatory_variables.keys()) + list(self.epistemic_variables.keys())

    def add_variables(self, input_parameters):
        """
        Function to add all uncertain variables to uncertainty study
        """
        distributions = []
        deterministic = []
        for parameter_name, parameter_value in input_parameters.items():
            if isinstance(parameter_value, UncertaintyCharacterization):
                distributions.append(parameter_value)
            elif isinstance(parameter_value, DeterministicCharacterization):
                deterministic.append(parameter_value)
            else:
                raise ValueError(f"input parameter {parameter_name} must be specified with an " +
                                 "uncertainty distribution or as deterministic")

        self.add_probabilistic_variables(distributions)
        self.add_deterministic_variables(deterministic)
        self.relevant_error_checks()

    def relevant_error_checks(self):
        """function to perform error checks on specified study details"""
        self.error_check_for_variable_unique_variable_names()
        self.error_check_for_distributions_if_sample_size()

    def add_probabilistic_variables(self, distribution_set):
        """function to add probabilistic variables to study"""
        for variable_distribution in distribution_set:
            if variable_distribution.uncertainty_type == 'aleatory':
                self.add_variable_name(variable_distribution,
                                       self.aleatory_variables)
            elif variable_distribution.uncertainty_type == 'epistemic':
                self.add_variable_name(variable_distribution,
                                       self.epistemic_variables)
            else:
                raise ValueError(f"{variable_distribution.name} not " +
                                 "specified as aleatory or epistemic")


    def add_deterministic_variables(self, deterministic_set):
        """function to add deterministic variables to study"""
        for variable in deterministic_set:
            self.add_variable_name(variable, self.deterministic_variables)

    def error_check_for_variable_unique_variable_names(self):
        """function to check that all variables have unique names"""
        shared_uncertainty_keys = \
            set(self.aleatory_variables).intersection(self.epistemic_variables)
        if shared_uncertainty_keys:
            raise ValueError(f"{shared_uncertainty_keys} uncertain variable specified " +
                             "for both uncertainty types")

        uncertainty_keys = set(self.aleatory_variables).union(set(self.epistemic_variables))
        shared_keys = set(self.deterministic_variables).intersection(uncertainty_keys)
        if shared_keys:
            raise ValueError(f"{shared_keys} variable specified " +
                             "for both uncertain and deterministic")

    def error_check_for_distributions_if_sample_size(self):
        """
        function to check that both an uncertainty distribution exists
        and sample size has been specified, not one or the other
        """
        has_aleatory_variables = bool(self.aleatory_variables)
        has_epistemic_variables = bool(self.epistemic_variables)
        has_aleatory_samples = self.number_of_aleatory_samples > 0
        has_epistemic_samples = self.number_of_epistemic_samples > 0

        # Throw error if variables are specified but no samples are
        if has_aleatory_samples and not has_aleatory_variables:
            raise ValueError("Specification of aleatory samples without aleatory distribution")
        if has_epistemic_samples and not has_epistemic_variables:
            raise ValueError("Specification of epistemic samples without " +
                             "epistemic distribution")

    def error_check_for_distributions_and_sample_size(self):
        """
        function to check that both an uncertainty distribution exists
        and sample size has been specified, not one or the other
        """
        has_aleatory_variables = bool(self.aleatory_variables)
        has_epistemic_variables = bool(self.epistemic_variables)
        has_aleatory_samples = self.number_of_aleatory_samples > 0
        has_epistemic_samples = self.number_of_epistemic_samples > 0

        # Throw error if variables or samples are specified without the other
        if  has_aleatory_variables ^ has_aleatory_samples:
            raise ValueError("Specification of aleatory samples or distribution " +
                             "without the other")
        if  has_epistemic_variables ^ has_epistemic_samples:
            raise ValueError("Specification of epistemic samples or distribution " +
                             "without the other")

    @staticmethod
    def add_variable_name(variable_distribution, location):
        """
        function to ensure two variables don't have the same name
        """
        if location.setdefault(variable_distribution.name,
                               variable_distribution) != variable_distribution:
            raise ValueError('Two variables with same name')

    def generate_lhs_samples(self,
                             number_of_variables:int,
                             number_of_samples:int,
                             optimization_method="random-cd"):
        """
        function to generate Latin hypercube samples (LHS) using 
        Scipy's Quasi-Monte Carlo submodule

        Parameters
        -----------
            number_of_variables: int
                 how many variables to generate samples for
            number_of_samples: int
                 how many LHS samples to generate             
    
        Returns
        --------
                lhs_samples (np.array(number_of_samples, number_of_variables))
                - LHS samples
        """
        if number_of_variables == 1:
            optimization_method = None

        lhs_sampler = qmc.LatinHypercube(d=number_of_variables,
                                         seed=self.random_state,
                                         optimization=optimization_method)
        lhs_samples = lhs_sampler.random(n=number_of_samples)
        return lhs_samples

    def add_aleatory_samples_to_sample_sheet(self, samples):
        """
        function to add aleatory variable samples to uncertainty study sample sheet
        """
        if self.number_of_epistemic_samples == 0:
            num_epistemic_samples = 1
        else:
            num_epistemic_samples = self.number_of_epistemic_samples

        for var_name, var_values in samples.items():
            self.sample_sheet[var_name] = np.array(var_values.tolist()*num_epistemic_samples)

    def add_epistemic_samples_to_sample_sheet(self, samples):
        """
        function to add epistemic variable samples to uncertainty study sample sheet
        """
        if self.number_of_aleatory_samples == 0:
            num_aleatory_samples = 1
        else:
            num_aleatory_samples = self.number_of_aleatory_samples

        for var_name, var_values in samples.items():
            self.sample_sheet[var_name] = np.array([[var_value]*num_aleatory_samples \
                                                    for var_value in var_values]).flatten()

    def add_deterministic_samples_to_sample_sheet(self, parameter, sample_size):
        """
        function to add deterministic samples to sample sheet
        """
        for var_name, var_values in parameter.items():
            self.sample_sheet[var_name] = var_values.generate_samples(sample_size)

    def calc_total_number_of_variables(self):
        """
        function to determine total number of uncertain variables in uncertainty study
        """
        aleatory_variables = self.calc_number_of_variables(self.aleatory_variables)
        epistemic_variables = self.calc_number_of_variables(self.epistemic_variables)
        return aleatory_variables + epistemic_variables

    @staticmethod
    def calc_number_of_variables(variable_dict):
        """
        function to calculate the number of variables in a dictionary
        """
        return len(variable_dict)

    @staticmethod
    def collect_variable_nominal_values(variable_dict):
        """
        function to collect nominal values of variables
        """
        samples = {}
        for variable_name, variable in variable_dict.items():
            samples[variable_name] = variable.nominal
        return samples

    def create_variable_nominal_sheet(self):
        """
        function to create sample sheet holding variables nominal values
        """
        aleatory_nominals = self.collect_variable_nominal_values(self.aleatory_variables)
        epistemic_nominals = self.collect_variable_nominal_values(self.epistemic_variables)
        deterministic_values = self.collect_variable_nominal_values(self.deterministic_variables)
        self.add_nominal_values_to_sample_sheet(aleatory_nominals)
        self.add_nominal_values_to_sample_sheet(epistemic_nominals)
        self.add_nominal_values_to_sample_sheet(deterministic_values)

        return self.nominal_sample_sheet

    def add_nominal_values_to_sample_sheet(self, nominal_values):
        """
        function for adding nominal values to sample sheet for generic sampling study
        """
        for var_name, var_value in nominal_values.items():
            self.nominal_sample_sheet[var_name] = var_value

    def get_total_double_loop_sample_size(self):
        """
        function to get sample size for double loop style uncertainty study
        """
        return max(self.number_of_aleatory_samples, 1)*max(self.number_of_epistemic_samples, 1)


class SensitivityStudy(UncertaintyStudy):
    """
    Generic Sensitivity Study Class

    Parameters
    ------------
    number_of_aleatory_samples:int
    number_of_epistemic_samples:int
    random_state
    """
    def relevant_error_checks(self):
        """function to perform error checks on specified study details"""
        self.error_check_for_variable_unique_variable_names()


class RandomStudy(UncertaintyStudy):
    """
    Random Sampling Uncertainty Study Class

    Parameters
    ------------
    number_of_aleatory_samples:int
    number_of_epistemic_samples:int
    random_state
    """
    def relevant_error_checks(self):
        """function to perform error checks on specified study details"""
        self.error_check_for_variable_unique_variable_names()
        self.error_check_for_distributions_and_sample_size()

    def collect_variables(self, variable_distribution_dict, number_of_samples):
        """
        function to collect variable samples for random sampling study
        """
        samples = {}
        for var_name, var_dist in variable_distribution_dict.items():
            samples[var_name] = var_dist.generate_samples(number_of_samples,
                                                          self.random_state)
        return samples

    def create_variable_sample_sheet(self):
        """
        function to create sample sheet and add samples for random sampling study
        """
        sample_func = self.collect_variables
        aleatory_samples = sample_func(self.aleatory_variables,
                                       self.number_of_aleatory_samples)
        epistemic_samples = sample_func(self.epistemic_variables,
                                        self.number_of_epistemic_samples)

        self.add_aleatory_samples_to_sample_sheet(aleatory_samples)
        self.add_epistemic_samples_to_sample_sheet(epistemic_samples)
        self.total_sample_size = max(self.number_of_aleatory_samples, 1)*\
            max(self.number_of_epistemic_samples, 1)
        self.add_deterministic_samples_to_sample_sheet(self.deterministic_variables,
                                                       self.total_sample_size)

        return self.sample_sheet


class LHSStudy(UncertaintyStudy):
    """
    LHS Uncertainty Study Class

    Parameters
    ------------
    number_of_aleatory_samples:int
    number_of_epistemic_samples:int
    random_state
    """
    def relevant_error_checks(self):
        """function to perform error checks on specified study details"""
        self.error_check_for_variable_unique_variable_names()
        self.error_check_for_distributions_and_sample_size()

    def collect_variables(self, variable_distribution_dict, number_of_samples):
        """
        function to collect variable samples for LHS study
        """
        samples = {}
        number_of_variables = self.calc_total_number_of_variables()
        equal_probability_cdf_pts = self.generate_lhs_samples(number_of_variables,
                                                              number_of_samples)
        for i, (var_name, var_dist) in enumerate(variable_distribution_dict.items()):
            samples[var_name] = var_dist.ppf(equal_probability_cdf_pts[:, i])

        return samples

    def create_variable_sample_sheet(self):
        """
        function to create sample sheet for LHS study
        """
        sample_func = self.collect_variables
        aleatory_samples = sample_func(self.aleatory_variables,
                                       self.number_of_aleatory_samples)
        epistemic_samples = sample_func(self.epistemic_variables,
                                        self.number_of_epistemic_samples)

        self.add_aleatory_samples_to_sample_sheet(aleatory_samples)
        self.add_epistemic_samples_to_sample_sheet(epistemic_samples)
        self.total_sample_size = max(self.number_of_aleatory_samples, 1)*\
            max(self.number_of_epistemic_samples, 1)
        self.add_deterministic_samples_to_sample_sheet(self.deterministic_variables,
                                                       self.total_sample_size)

        return self.sample_sheet


class OneAtATimeSensitivityStudy(SensitivityStudy):
    """
    Single Variable Sampling-Based Sensitivity Study

    Parameters
    ------------
    number_of_aleatory_samples:int
    number_of_epistemic_samples:int
    random_state
    """
    def relevant_error_checks(self):
        """function to perform error checks on specified study details"""
        self.error_check_for_variable_unique_variable_names()
        self.error_check_for_distributions_and_sample_size()

    def collect_variables(self, variable_distribution_dict, number_of_samples):
        """
        function to collect samples for uncertain variables for sampling based sensitivity study
        """
        samples = {}
        cdf_pts = self.generate_cdf_samples(number_of_samples)
        for var_name, var_dist in variable_distribution_dict.items():
            samples[var_name] = var_dist.ppf(cdf_pts)

        return samples

    def generate_cdf_samples(self, number_of_samples):
        """function to specify percentiles sampled from cdf"""
        cdf_samples = self.generate_lhs_samples(1, number_of_samples, optimization_method=None)
        return cdf_samples.reshape(-1)

    def add_sensitivity_samples_to_sample_sheet(self,
                                                aleatory_samples,
                                                epistemic_samples):
        """
        function to add sensitivity study samples to sample sheet for sampling based
        sensitivity study
        """
        aleatory_samples_size = self.number_of_aleatory_samples
        epistemic_sample_size = self.number_of_epistemic_samples
        number_of_aleatory_entries = \
            self.calc_number_of_variables(self.aleatory_variables)*aleatory_samples_size
        number_of_epistemic_entries = \
            self.calc_number_of_variables(self.epistemic_variables)*epistemic_sample_size
        column_length = number_of_aleatory_entries + number_of_epistemic_entries

        i = 0
        for var_name, var_values in aleatory_samples.items():
            nominal = self.aleatory_variables[var_name].nominal
            self.sample_sheet[var_name] = np.ones(shape=column_length)*nominal
            relevant_samples = slice(i*aleatory_samples_size,
                                     i*aleatory_samples_size+aleatory_samples_size)
            self.sample_sheet[var_name][relevant_samples] = np.sort(var_values)
            i += 1

        i = 0
        for var_name, var_values in epistemic_samples.items():
            nominal = self.epistemic_variables[var_name].nominal
            self.sample_sheet[var_name] = np.ones(shape=column_length)*nominal
            offset = number_of_aleatory_entries
            current_slice = slice(offset + i*epistemic_sample_size, offset + \
                                  i*epistemic_sample_size+epistemic_sample_size)
            self.sample_sheet[var_name][current_slice] = np.sort(var_values)
            i += 1

        return self.sample_sheet

    def create_variable_sample_sheet(self):
        """
        function to create sample sheet for sampling based sensitivity study
        """
        sample_func = self.collect_variables
        aleatory_samples = sample_func(self.aleatory_variables,
                                       self.number_of_aleatory_samples)
        epistemic_samples = sample_func(self.epistemic_variables,
                                        self.number_of_epistemic_samples)

        self.add_sensitivity_samples_to_sample_sheet(aleatory_samples, epistemic_samples)
        self.determine_total_sample_size()
        self.add_deterministic_samples_to_sample_sheet(self.deterministic_variables,
                                                       self.total_sample_size)
        return self.sample_sheet

    def determine_total_sample_size(self):
        """function to determine the total sample size of the study"""
        number_of_aleatory_variables = self.calc_number_of_variables(self.aleatory_variables)
        number_of_epistemic_variables = self.calc_number_of_variables(self.epistemic_variables)
        self.total_sample_size = \
            self.number_of_aleatory_samples*number_of_aleatory_variables +\
            self.number_of_epistemic_samples*number_of_epistemic_variables


class BoundingStudy(OneAtATimeSensitivityStudy):
    """
    Bounding Sensitivity Study Class

    Parameters
    ------------
    number_of_aleatory_samples:int
    number_of_epistemic_samples:int
    random_state
    """
    def relevant_error_checks(self):
        """function to perform error checks on specified study details"""
        self.error_check_for_variable_unique_variable_names()

    def generate_cdf_samples(self, _):
        """function to specify percentiles sampled from cdf"""
        return np.array([0.01, 0.99])

    def add_sensitivity_samples_to_sample_sheet(self,
                                                aleatory_samples,
                                                epistemic_samples):
        """
        function to add samples from bounding sensitivity study to sample sheet
        """
        column_length = self.calc_total_number_of_variables()*2

        idx = 0
        for var_name, var_values in aleatory_samples.items():
            nominal = self.aleatory_variables[var_name].nominal
            self.sample_sheet[var_name] = np.ones(shape=column_length) * nominal
            self.sample_sheet[var_name][idx*2:idx*2+2] = var_values
            idx += 1

        for var_name, var_values in epistemic_samples.items():
            nominal = self.epistemic_variables[var_name].nominal
            self.sample_sheet[var_name] = np.ones(shape=column_length) * nominal
            self.sample_sheet[var_name][idx*2:idx*2+2] = var_values
            idx += 1

        return self.sample_sheet

    def determine_total_sample_size(self):
        self.total_sample_size = self.calc_total_number_of_variables()*2
