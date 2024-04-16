"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""

import numpy as np

from helprgui.utils.distributions import Distributions, Uncertainties
from helprgui.utils.helpers import InputStatus, ValidationResponse, get_num_str
from helprgui.utils.events import Event
from helprgui.utils.units_of_measurement import Temperature
from helprgui.models.fields import NumField

from probabilistic.capabilities.uncertainty_definitions import (UniformDistribution, NormalDistribution, LognormalDistribution,
                                                                DeterministicCharacterization, UncertaintyCharacterization)


class UncertainField(NumField):
    """Analysis parameter described by float value, unit of measurement, and possibly distribution parameters.

    Attributes
    ----------
    distr
    uncertainty
    a
    b
    str_display

    distrChanged : Signal
        Event emitted when parameter input type/distribution is changed.
    uncertaintyChanged : Signal
        Event emitted when parameter uncertainty is changed.

    Notes
    -----
    All values, including `min_value`, `max_value`, and distribution params `a` and `b`, are stored in standard units; e.g., meters.

    """
    _uncertainty: str or None
    _dtype = float
    _value: float

    # Probabilistic properties
    _distr: str  # rename to rvc?
    _a: float or None  # mean or lower bound
    _b: float or None  # std deviation or upper bound

    distr_changed = Event()
    uncertainty_changed = Event()

    def __init__(self, label, value, slug='', unit_type=None, unit=None,
                 distr=Distributions.det, uncertainty=Uncertainties.ale, a=0, b=0,
                 min_value=0, max_value=np.inf, tooltip=None, label_rtf=None,
                 unit_choices=None):
        super().__init__(label=label, slug=slug, value=value, label_rtf=label_rtf, tooltip=tooltip,
                         min_value=min_value, max_value=max_value, unit_type=unit_type, unit=unit, unit_choices=unit_choices)
        self._distr = distr
        self._uncertainty = uncertainty

        self._a = self.unit_type.convert(a, old=self.unit)
        self._b = self.unit_type.convert(b, old=self.unit)

    @property
    def distr(self) -> str:
        return self._distr

    @distr.setter
    def distr(self, val: str):
        if val in Distributions:
            self._distr = val
            UncertainField.distr_changed.notify(self)
            self.changed.notify(self)
        else:
            raise ValueError(f"Distribution {val} not a valid option")

    @property
    def is_normal(self):
        """Whether parameter using a normal or lognormal distribution. """
        return self._distr in [Distributions.nor, Distributions.log]

    @property
    def is_scale_unit(self):
        """Whether parameter is using scale-based units such as temperature. """
        return self.unit_type in [Temperature]

    def set_values_ignore_lims(self, val: float, a: float, b: float):
        """ Sets values while ignoring min and max limits. e.g. When units changed. """
        new_value = self.unit_type.convert(val, old=self.unit)
        self._value = self._dtype(new_value)

        self._a = self._dtype(self.unit_type.convert(a, old=self.unit))
        self._b = self._dtype(self.unit_type.convert(b, old=self.unit))

        if self._track_changes:
            self.changed.notify(self)

    @property
    def a(self):
        """ Distribution parameter in active units; mean if normal or lognormal, lower bound if uniform. """
        result = self.unit_type.convert(self._a, new=self.unit, do_round=True)
        return result

    @a.setter
    def a(self, val: float):
        """ Sets distribution parameter value, converting from active unit. """
        nv = self.unit_type.convert(val, old=self.unit)
        if self._min_value <= nv <= self._max_value:
            self._a = self._dtype(nv)
            if self._track_changes:
                self.changed.notify(self)

    @property
    def a_str(self):
        """Distribution parameter a formatted for display. """
        return get_num_str(self.a)

    @property
    def b(self):
        """ Distribution parameter in active units; std deviation if normal or lognormal, upper bound if uniform. """
        result = self.unit_type.convert(self._b, new=self.unit, do_round=True)
        return result

    @b.setter
    def b(self, val: float):
        """ Sets distribution parameter value, converting from active unit. """
        nv = self.unit_type.convert(val, old=self.unit)
        # check bounds if uniform
        if self.is_normal or self._min_value <= nv <= self._max_value:
            self._b = self._dtype(nv)
            if self._track_changes:
                self.changed.notify(self)

    @property
    def b_str(self):
        """Distribution parameter b formatted for display. """
        return get_num_str(self.b)

    @property
    def uncertainty(self) -> str:
        return self._uncertainty

    @uncertainty.setter
    def uncertainty(self, val):
        """
        Sets uncertainty according to available choices

        Parameters
        ----------
        val : {'ale', 'epi', None}
            new uncertainty value

        """
        if val in Uncertainties:
            self._uncertainty = val
            UncertainField.uncertainty_changed.notify(self)
            self.changed.notify(self)
        else:
            raise ValueError(f"Uncertainty {val} not found")

    @property
    def str_display(self):
        """ Returns string-representation of parameter, including label.
        """
        result = ""
        if self.unit is None:
            unit_str = ""
        else:
            disp_unit_index = self.get_unit_index()
            unit_str = self._display_units[disp_unit_index]
        val = self.value_str

        if self._distr == 'det':
            result = f"{self.label}: {val} {unit_str}"
        elif self._distr == 'nor':
            result = f"{self.label}: Normal ({val} {unit_str}, {self.a} +/- {self.b})"
        elif self._distr == 'log':
            result = f"{self.label}: Lognormal ({val} {unit_str}, {self.a} +/- {self.b})"
        elif self._distr == 'uni':
            result = f"{self.label}: Uniform ({val} {unit_str}, {self.a} to {self.b})"
        return result

    def set_unit_from_display(self, val: str):
        """ Sets active unit from a selected display value, not key. e.g. 'MPa' updates unit type to 'mpa' """
        disp_units = self._display_units
        if len(disp_units) <= 1:
            return
        if val not in disp_units:
            raise ValueError('Display unit not found')

        old_param_val = self.value
        old_a = self.a
        old_b = self.b
        i = disp_units.index(val)
        self.unit = self._unit_choices[i]

        # displayed value now in new units so update raw values in batch to yield single change event
        tracking = self._track_changes
        self._track_changes = False
        self.set_values_ignore_lims(old_param_val, old_a, old_b)
        self._track_changes = tracking

        self.changed.notify(self)

    def get_distr_index(self) -> int:
        """Returns index of selected distribution. """
        result = Distributions.index(self._distr)
        return result

    def get_uncertainty_index(self) -> int:
        """Returns index of selected uncertainty option. """
        result = Uncertainties.index(self._uncertainty)
        return result

    def check_valid(self) -> ValidationResponse:
        resp = super().check_valid()
        if resp.status != InputStatus.GOOD:
            return resp

        msg = ""
        if self.distr in [Distributions.nor, Distributions.log]:
            if self.a < self.min_value:
                msg = f'{self.label} mean below minimum ({self.a_str} < {self.min_value_str})'
            elif self.a > self.max_value:
                msg = f'{self.label} mean above maximum ({self.a_str} > {self.max_value_str})'
        elif self.distr == Distributions.uni:
            if self.value < self.a:
                msg = f'{self.label} value below lower bound ({self.value_str} < {self.a_str})'
            elif self.value > self.b:
                msg = f'{self.label} value above upper bound ({self.value_str} > {self.b_str})'
            elif self.a > self.b:
                msg = f'{self.label} lower bound above upper bound ({self.a_str} > {self.b_str})'
            if self.b < self.min_value:
                msg = f'{self.label} upper bound below minimum ({self.b_str} < {self.min_value_str})'
            elif self.b > self.max_value:
                msg = f'{self.label} upper bound above maximum ({self.b_str} > {self.max_value_str})'
            elif self.a < self.min_value:
                msg = f'{self.label} lower bound below minimum ({self.a_str} < {self.min_value_str})'
            elif self.a > self.max_value:
                msg = f'{self.label} lower bound above maximum ({self.a_str} > {self.max_value_str})'

        status = InputStatus.ERROR if msg else InputStatus.GOOD
        return ValidationResponse(status, msg)

    def get_prepped_value(self):
        """Returns parameter value, in standard units, prepared for analysis as Characterization or Distribution.

        Returns
        -------
        DeterministicCharacterization or Type(UncertaintyCharacterization)
            Parameter parsed as characterization.

        Notes
        -----
        Must adjust std deviation (i.e. relative value) if using an absolutely-based unit like temperature.

        """
        if self._distr == 'det':
            result = DeterministicCharacterization(name=self.slug, value=self._value)
            return result

        uncertainty = 'epistemic' if self._uncertainty == 'epi' else 'aleatory'

        if self._distr == 'nor':
            # must convert std dev to difference if in scale unit (e.g. temperature) and not using std units
            if self.is_scale_unit and self.unit != self.unit_type.std_unit:
                std_dev = self._b - self.unit_type.scale_base
            else:
                std_dev = self._b

            result = NormalDistribution(name=self.slug,
                                        uncertainty_type=uncertainty,
                                        nominal_value=self._value,
                                        mean=self._a,
                                        std_deviation=std_dev)
        elif self._distr == 'uni':
            result = UniformDistribution(name=self.slug,
                                         uncertainty_type=uncertainty,
                                         nominal_value=self._value,
                                         lower_bound=self._a,
                                         upper_bound=self._b)
        elif self._distr == 'log':
            # must convert std dev to difference if not in std units
            if self.is_scale_unit and self.unit != self.unit_type.std_unit:
                sigma = self._b - self.unit_type.scale_base
            else:
                sigma = self._b

            result = LognormalDistribution(name=self.slug,
                                           uncertainty_type=uncertainty,
                                           nominal_value=self._value,
                                           mu=self._a,
                                           sigma=sigma)
        else:
            raise ValueError(f"distribution key {self._distr} not recognized")

        return result

    def to_dict(self) -> dict:
        """Returns data representation with values in standard (raw) format.

        Returns
        -------
        dict
            Parsed parameter data with values in standard units.

        """
        result = super().to_dict()
        extra = {
            'uncertainty': self._uncertainty,
            'distr': self._distr,
            'a': float(self._a),
            'b': float(self._b),
        }
        result |= extra
        return result

    def from_dict(self, data: dict, notify_from_model=True, silent=False):
        """
        Overwrites all parameter data from contents of incoming dict.

        Parameters
        ----------
        data : dict
            parameter data in standard units with keys matching field names.

        notify_from_model : bool, default=True
            flag indicating the call originated from backend model. Triggers corresponding event.

        Notes
        -----
        Assumes all required properties are present.
        Min and max values stored as strings to accommodate infinity.

        """
        super().from_dict(data=data, notify_from_model=notify_from_model, silent=True)

        # Verify all extra data present
        expected_keys = self.to_dict().keys()
        for key in expected_keys:
            if key not in data:
                raise ValueError(f'Required key {key} not found in data {data}')

        self.uncertainty = data['uncertainty']
        self.distr = data['distr']
        self._a = data['a']
        self._b = data['b']

        if not silent:
            self.changed.notify(self)

            if notify_from_model:
                self.changed_by_model.notify(self)
