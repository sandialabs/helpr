"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import numpy as np

from helprgui.hygu.models.fields_probabilistic import UncertainField
from helprgui.hygu.utils.distributions import Distributions
from probabilistic.capabilities.uncertainty_definitions import (UniformDistribution, NormalDistribution, LognormalDistribution,
                                                                DeterministicCharacterization,
                                                                TruncatedNormalDistribution, TruncatedLognormalDistribution)


class HelprUncertainField(UncertainField):
    _valid_distributions = ['det', 'tnor', 'tlog', 'uni']
    _distr_choices_display = ['Deterministic', 'Normal', 'Lognormal', 'Uniform']

    @property
    def distr_choices_display(self):
        return self._distr_choices_display

    def get_prepped_value(self):
        """Returns parameter value, in standard units, prepared for analysis as Characterization or Distribution.

        Returns
        -------
        DeterministicCharacterization or Type(UncertaintyCharacterization)
            Parameter parsed as characterization.

        Notes
        -----
        Must adjust std deviation (i.e. relative value) if using an absolutely-based unit like temperature.

        Raises
        ------
        ValueError
            If std or sigma is <= 0 for distributions that require positive values.
            This prevents division by zero errors in the backend.
        """
        if self._distr == 'det':
            result = DeterministicCharacterization(name=self.slug, value=self._value)
            return result

        uncertainty = 'epistemic' if self._uncertainty == 'epi' else 'aleatory'

        if self._distr == Distributions.uni:
            upper_val = np.inf if self._upper is None else self._upper
            result = UniformDistribution(name=self.slug,
                                         uncertainty_type=uncertainty,
                                         nominal_value=self._value,
                                         lower_bound=self._lower,
                                         upper_bound=upper_val)

        elif self._distr == Distributions.nor:
            std_dev = self._std
            # convert std dev to difference if in scale unit (e.g. temperature) and not using std units
            if self.is_scale_unit and self.unit != self.unit_type.std_unit:
                std_dev -= self.unit_type.scale_base

            if std_dev <= 0:
                raise ValueError(
                    f"Cannot create NormalDistribution for '{self.label}': "
                    f"std deviation must be positive (> 0), got {std_dev}"
                )

            result = NormalDistribution(name=self.slug,
                                        uncertainty_type=uncertainty,
                                        nominal_value=self._value,
                                        mean=self._mean,
                                        std_deviation=std_dev)

        elif self._distr == Distributions.tnor:
            std_dev = self._std
            # convert std dev to difference if in scale unit (e.g. temperature) and not using std units
            if self.is_scale_unit and self.unit != self.unit_type.std_unit:
                std_dev -= self.unit_type.scale_base

            if std_dev <= 0:
                raise ValueError(
                    f"Cannot create TruncatedNormalDistribution for '{self.label}': "
                    f"std deviation must be positive (> 0), got {std_dev}"
                )

            upper_val = np.inf if self._upper is None else self._upper

            result = TruncatedNormalDistribution(name=self.slug,
                                                 uncertainty_type=uncertainty,
                                                 nominal_value=self._value,
                                                 mean=self._mean,
                                                 std_deviation=std_dev,
                                                 lower_bound=self._lower,
                                                 upper_bound=upper_val)

        elif self._distr == Distributions.log:
            sigma = self._sigma
            # convert sigma to difference if not in std units
            if self.is_scale_unit and self.unit != self.unit_type.std_unit:
                sigma -= self.unit_type.scale_base

            if sigma <= 0:
                raise ValueError(
                    f"Cannot create LognormalDistribution for '{self.label}': "
                    f"sigma must be positive (> 0), got {sigma}"
                )

            result = LognormalDistribution(name=self.slug,
                                           uncertainty_type=uncertainty,
                                           nominal_value=self._value,
                                           mu=self._mu,
                                           sigma=sigma)

        elif self._distr == Distributions.tlog:
            sigma = self._sigma
            # convert sigma to difference if not in std units
            if self.is_scale_unit and self.unit != self.unit_type.std_unit:
                sigma -= self.unit_type.scale_base

            if sigma <= 0:
                raise ValueError(
                    f"Cannot create TruncatedLognormalDistribution for '{self.label}': "
                    f"sigma must be positive (> 0), got {sigma}"
                )

            upper_val = np.inf if self._upper is None else self._upper

            result = TruncatedLognormalDistribution(name=self.slug,
                                                    uncertainty_type=uncertainty,
                                                    nominal_value=self._value,
                                                    mu=self._mu,
                                                    sigma=sigma,
                                                    lower_bound=self._lower,
                                                    upper_bound=upper_val)

        else:
            raise ValueError(f"distribution key {self._distr} not recognized")

        return result

