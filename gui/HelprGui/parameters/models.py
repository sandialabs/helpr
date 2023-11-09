"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import numpy as np

from utils.distributions import Distributions, Uncertainties, BaseChoiceList
from utils.units_of_measurement import (UnitType, Unitless, get_unit_type_from_unit_key, get_unit_type, Percent)
from utils.events import Event

from probabilistic.capabilities.uncertainty_definitions import (UniformDistribution, NormalDistribution, LognormalDistribution,
                                                                DeterministicCharacterization, UncertaintyCharacterization)


def get_num_str(val) -> str:
    """Returns formatted string representation of converted value. """
    if val == -np.inf:
        result = '-infinity'
    elif val == np.inf:
        result = '+infinity'

    else:
        abs_val = abs(val)
        if abs_val > 1000:
            result = f"{val:.0e}"
        elif abs_val >= 1:
            result = f"{val:.1f}"
        elif abs_val >= 0.01:
            result = f"{val:.3f}"
        elif abs_val == 0:
            result = "0"
        else:
            result = f"{val:.3e}"
    return result


def get_slug(label: str, slug) -> str:
    """returns string in snake_case, derived from label if slug not already found. """
    result = slug.strip()
    if result in ['', None]:
        result = label.lower().strip().replace(" ", "_")
    return result


class ChoiceParameter:
    """Analysis parameter described by set of selectable options.

    Attributes
    ----------
    str_display
    label : str
    choices : BaseChoiceList

    changed : Event
        Event emitted when user changes value via GUI.
    changed_by_model : Event
        Event emitted when value is changed by state.

    """
    label: str
    choices: type(BaseChoiceList)
    _value: str  # 3-letter key identifying selected choice
    changed: Event
    changed_by_model: Event

    def __init__(self, label, choices, value=None):
        self.label = label
        self.choices = choices

        if value is not None:
            self._value = value.lower()
        else:
            self._value = self.choices[0]

        self.changed = Event()  # any change occurs; instance-only
        self.changed_by_model = Event()

    @property
    def str_display(self):
        """Returns string-representation of parameter, including label. """
        result = f"{self.label}: {self.get_value_display()}"
        return result

    def set_value_from_key(self, val: str):
        """ Sets active unit from key. e.g. 'MPa' updates unit type to 'mpa'. """
        if val not in self.choices:
            raise ValueError('Choice not found')
        self._value = val.lower()
        self.changed.notify(self)

    def set_value_from_index(self, i: int):
        """Sets value via index into choice list. """
        if i >= len(self.choices):
            raise ValueError("Index for selected value not found")
        self._value = self.choices[i]
        self.changed.notify(self)

    def get_value_index(self) -> int:
        """Returns index of selected value into choices options. """
        return self.choices.index(self._value)

    def get_value(self) -> str:
        """Returns shortened key-form of value; e.g. 'prb' """
        return self._value

    def get_value_display(self) -> str:
        """Returns display-ready form of value; e.g. Deterministic. """
        idx = self.get_value_index()
        result = self.choices.labels[idx]
        return result

    def get_choice_keys(self) -> [str]:
        """Returns key-only list of all choices. """
        results = self.choices.keys
        return results

    def get_choice_displays(self) -> [str]:
        """Returns display-ready list of all choices. """
        results = self.choices.labels
        return results

    def to_dict(self) -> dict:
        """Returns data representation of parameter as dict. """
        result = {
            'label': self.label,
            'value': self._value,
        }
        return result

    def from_dict(self, data: dict, notify_from_model=True):
        """Updates parameter properties from dict.

        Parameters
        ----------
        data : dict
            property value pairs as {'property': value}.
        notify_from_model : bool
            True if this function called by model.

        Notes
        -----
        Assumes all properties are present.

        """
        # Verify all data present
        expected_keys = self.to_dict().keys()
        for key in expected_keys:
            if key not in data:
                raise ValueError(f'Required key {key} not found in data {data}')

        self.label = data['label']
        self.set_value_from_key(data['value'])

        self.changed.notify(self)

        if notify_from_model:
            self.changed_by_model.notify(self)


class BasicParameter:
    """Analysis parameter described by unit-less, deterministic integer; e.g. random seed.

    Attributes
    ----------
    min_value_str
    max_value_str
    value
    str_display
    label : str
        Descriptive label.
    slug : str
        Internal representation of parameter label. Must match backend API.
    min_value : int
        Minimum allowed value.
    max_value : int
        Maximum allowed value.
    enabled : bool
        Whether parameter can be modified and is in use.
    tooltip : str or None
        Descriptive representation of parameter for populating tooltip.
    changed : Event
        Event emitted when user changes value via GUI.
    changed_by_model : Event
        Event emitted when value is changed by state.

    """
    label: str
    slug: str  # internal reference, must match backend API
    _value: int
    min_value: int
    max_value: int
    enabled: bool = True
    tooltip: None or str

    def __init__(self, label, value, slug='', min_value=0, max_value=np.inf, tooltip=None):
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self._value = value
        self.slug = get_slug(label, slug)
        self.tooltip = tooltip

        self.changed = Event()  # any change occurs; instance-only
        self.changed_by_model = Event()  # param was changed by backend

    @property
    def min_value_str(self):
        """Minimum value formatted for display. """
        return get_num_str(self.min_value)

    @property
    def max_value_str(self):
        """Maximum value formatted for display. """
        return get_num_str(self.max_value)

    @property
    def value(self) -> int:
        """Parameter value. """
        return int(self._value)

    @value.setter
    def value(self, val: int):
        """Sets value bounded by minimum and maximum, and emits changed event. """
        if self.min_value <= val <= self.max_value:
            self._value = int(val)
            self.changed.notify(self)

    @property
    def str_display(self):
        """ Returns string-representation of parameter, including label. """
        result = f"{self.label}: {self.value:0d}"
        return result

    def toggle_enabled(self, val: bool, silent=True):
        """Sets enabled status and optionally emits model change event. """
        self.enabled = val
        if not silent:
            self.changed_by_model.notify(self)

    def set_from_model(self, val: int):
        """Sets value via backend model. """
        if self.min_value <= val <= self.max_value:
            self._value = int(val)
            self.changed_by_model.notify(self)

    def get_value_tooltip(self):
        """Returns tooltip for parameter. """
        if self.tooltip is None:
            if self.min_value == 0 and self.max_value == np.inf:
                result = "Enter a positive value"
            elif self.max_value == np.inf:
                result = f"Enter a value >= {self.min_value_str}"  # {self._param.unit}"
            else:
                result = f"Enter a value between {self.min_value_str} and {self.max_value_str}"
            return result
        else:
            return self.tooltip

    def get_prepped_value(self):
        """Returns value in standard units. """
        return int(self._value)

    def to_dict(self) -> dict:
        """Provide data representation in dict format. All values are stored in standard (raw) format. """
        result = {
            'label': self.label,
            'slug': self.slug,
            'value': self._value,
            'min_value': self.min_value_str,  # store as str to handle np.inf
            'max_value': self.max_value_str,
        }
        return result

    def from_dict(self, data: dict, notify_from_model=True):
        """Set all values from dict. Assume all properties are present. """
        # Verify all data present
        expected_keys = self.to_dict().keys()
        for key in expected_keys:
            if key not in data:
                raise ValueError(f'Required key {key} not found in data {data}')

        self.label = data['label']
        self.slug = data['slug']
        self.value = int(data['value'])

        # limit may be stored as string
        min_str = data.get('min_value', -np.inf)
        max_str = data.get('max_value', np.inf)
        self.min_value = -np.inf if type(min_str) is str and 'infinity' in min_str else float(min_str)
        self.max_value = np.inf if type(max_str) is str and 'infinity' in max_str else float(max_str)

        self.changed.notify(self)

        if notify_from_model:
            self.changed_by_model.notify(self)


class BoolParameter:
    """Analysis parameter described by boolean value; e.g. a flag.

    Attributes
    ----------
    value
    str_display
    label : str
        Descriptive label.
    slug : str
        Internal representation of parameter label. Must match backend API.
    enabled : bool
        Whether parameter can be modified and is in use.
    changed : Event
        Event emitted when user changes value via GUI.
    changed_by_model : Event
        Event emitted when value is changed by state.
    """
    label: str
    slug: str  # internal reference, must match backend API
    _value: bool = True
    enabled: bool = True

    def __init__(self, label, value, slug=''):
        self.label = label
        self._value = value
        self.slug = get_slug(label, slug)

        self.changed = Event()
        self.changed_by_model = Event()

    @property
    def value(self) -> bool:
        """Returns boolean value. """
        return bool(self._value)

    @value.setter
    def value(self, val: int):
        """ Sets boolean value. """
        self._value = bool(val)
        self.changed.notify(self)

    @property
    def str_display(self):
        """Returns string-representation of parameter, including label. """
        result = f"{self.label}: {self.value}"
        return result

    def toggle_enabled(self, val: bool, silent=True):
        """Sets enabled status and optionally emits model change event. """
        self.enabled = val
        if not silent:
            self.changed_by_model.notify(self)

    def set_from_model(self, val: bool):
        """Sets value via backend state. """
        self._value = val
        self.changed_by_model.notify(self)

    def get_prepped_value(self):
        """Returns value ready for analysis. """
        return self._value

    def to_dict(self) -> dict:
        """Provide data representation in dict format. All values are stored in standard (raw) format. """
        result = {
            'label': self.label,
            'slug': self.slug,
            'value': self._value,
        }
        return result

    def from_dict(self, data: dict, notify_from_model=True):
        """Set all values from dict. Assume all properties are present. """
        # Verify all data present
        expected_keys = self.to_dict().keys()
        for key in expected_keys:
            if key not in data:
                raise ValueError(f'Required key {key} not found in data {data}')

        self.label = data['label']
        self.slug = data['slug']
        self.value = bool(data['value'])

        self.changed.notify(self)

        if notify_from_model:
            self.changed_by_model.notify(self)


class Parameter:
    """Analysis parameter described by float value, unit of measurement, and possibly distribution parameters.

    Attributes
    ----------
    unit_choices_display
    value
    min_value
    max_value
    min_value_str
    max_value_str
    distr
    uncertainty
    a
    b
    str_display

    label : str
        Descriptive label.
    label_rtf : str
        Parameter label in rich-text formatting; e.g. Volume H<sub>2</sub>.
    slug : str
        Internal representation of parameter label. Must match backend API.
    tooltip : str or None
        Descriptive representation of parameter for populating tooltip.
    min_value : int
        Minimum allowed value.
    max_value : int
        Maximum allowed value.
    unit_type : UnitType
        Class of units of measurement, e.g. Distance.
    unit : str or None
        Key defining active unit of measurement; e.g. 'm'. Value of None indicates parameter is unit-less.

    changed : Event
        Event emitted when user changes value via GUI.
    changed_by_model : Event
        Event emitted when value is changed by state.
    distrChanged : Signal
        Event emitted when parameter input type/distribution is changed.
    uncertaintyChanged : Signal
        Event emitted when parameter uncertainty is changed.
    Notes
    -----
    All values, including `min_value`, `max_value`, and distribution params `a` and `b`, are stored in standard units; e.g., meters.

    """
    label: str
    label_rtf: str = ""
    slug: str
    tooltip: None or str
    unit_type: type(UnitType)
    unit: str or None

    _uncertainty: str or None
    _value: float
    _min_value: float
    _max_value: float

    # Probabilistic properties
    _distr: str  # rename to rvc?
    _a: float or None  # mean or lower bound
    _b: float or None  # std deviation or upper bound

    changed: Event
    changed_by_model: Event
    distr_changed = Event()
    uncertainty_changed = Event()

    _track_changes = True

    def __init__(self, label, value, slug='', unit_type=None, unit=None,
                 distr=Distributions.det, uncertainty=Uncertainties.ale, a=0, b=0,
                 min_value=0, max_value=np.inf, tooltip=None, label_rtf=None):
        self.label = label
        self.label_rtf = label_rtf if label_rtf is not None else label
        self._distr = distr
        self._uncertainty = uncertainty

        self.slug = get_slug(label, slug)
        self.tooltip = tooltip

        # unit type is given or determined from unit (e.g. 'm' unit yields Distance)
        if unit_type is not None:
            self.unit_type = unit_type
        elif unit_type is None and unit is None:
            self.unit_type = Unitless
        elif unit_type is None:
            self.unit_type = get_unit_type_from_unit_key(unit)

        if unit is None:
            unit = self.unit_type.std_unit
        self.unit = unit

        self._value = self.unit_type.convert(value, old=self.unit)
        self._min_value = self.unit_type.convert(min_value, old=self.unit)
        self._max_value = self.unit_type.convert(max_value, old=self.unit)
        self._a = self.unit_type.convert(a, old=self.unit)
        self._b = self.unit_type.convert(b, old=self.unit)

        self.changed = Event()  # any change occurs; instance-only
        self.changed_by_model = Event()  # param was changed by backend

    # ====================
    # ==== PROPERTIES ====
    @property
    def value(self):
        """ Returns value in selected units. If probabilistic, returns value as distribution. """
        result = self.unit_type.convert(self._value, new=self.unit, do_round=True)
        return result

    @value.setter
    def value(self, val: float):
        """ Sets stored standard value according to active unit. """
        new_value = self.unit_type.convert(val, old=self.unit)
        if self._min_value <= new_value <= self._max_value:
            self._value = new_value
            if self._track_changes:
                self.changed.notify(self)

    @property
    def value_raw(self):
        return self._value

    @property
    def min_value(self):
        if self._min_value == -np.inf:
            result = -np.inf
        else:
            result = self.unit_type.convert(self._min_value, new=self.unit, do_round=True)
        return result

    @property
    def max_value(self):
        if self._max_value == np.inf:
            result = np.inf
        else:
            result = self.unit_type.convert(self._max_value, new=self.unit, do_round=True)
        return result

    @property
    def min_value_str(self):
        return get_num_str(self.min_value)

    @property
    def max_value_str(self):
        return get_num_str(self.max_value)

    @property
    def unit_choices_display(self):
        return self.unit_type.display_units

    @property
    def distr(self) -> str:
        return self._distr

    @distr.setter
    def distr(self, val: str):
        if val in Distributions:
            self._distr = val
            Parameter.distr_changed.notify(self)
            self.changed.notify(self)
        else:
            raise ValueError(f"Distribution {val} not a valid option")

    @property
    def a(self):
        """ Returns distribution param in active units. """
        result = self.unit_type.convert(self._a, new=self.unit, do_round=True)
        return result

    @a.setter
    def a(self, val: float):
        """ Sets distribution parameter value, converting from active unit. """
        self._a = self.unit_type.convert(val, old=self.unit)
        if self._track_changes:
            self.changed.notify(self)

    @property
    def b(self):
        """ Returns distribution param in active units. """
        result = self.unit_type.convert(self._b, new=self.unit, do_round=True)
        return result

    @b.setter
    def b(self, val: float):
        """ Sets distribution parameter value, converting from active unit. """
        self._b = self.unit_type.convert(val, old=self.unit)
        if self._track_changes:
            self.changed.notify(self)

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
            Parameter.uncertainty_changed.notify(self)
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
            unit_str = self.unit_type.display_units[disp_unit_index]
        val = self._value_str()

        if self._distr == 'det':
            result = f"{self.label}: {val} {unit_str}"
        elif self._distr == 'nor':
            result = f"{self.label}: Normal ({val} {unit_str}, {self.a} +/- {self.b})"
        elif self._distr == 'log':
            result = f"{self.label}: Lognormal ({val} {unit_str}, {self.a} +/- {self.b})"
        elif self._distr == 'uni':
            result = f"{self.label}: Uniform ({val} {unit_str}, {self.a} to {self.b})"
        return result

    # =======================
    # ==== ADD'L SETTERS ====
    def set_value_raw(self, val):
        """ Sets value assuming standard units. """
        if self._min_value <= val <= self._max_value:
            self._value = val
            if self._track_changes:
                self.changed.notify(self)

    def set_unit_from_display(self, val: str):
        """ Sets active unit from a selected display value, not key. e.g. 'MPa' updates unit type to 'mpa' """
        disp_units = self.unit_type.display_units
        if len(disp_units) <= 1:
            return
        if val not in disp_units:
            raise ValueError('Display unit not found')

        old_param_val = self.value
        old_a = self.a
        old_b = self.b
        i = disp_units.index(val)
        self.unit = self.unit_type.units()[i]

        # displayed value now in new units so update raw values in batch to yield single change event
        track_val = self._track_changes
        self._track_changes = False
        self.value = old_param_val
        self.a = old_a
        self.b = old_b
        self._track_changes = track_val

        self.changed.notify(self)

    # ===========================
    # ==== UTILITY FUNCTIONS ====
    def get_unit_index(self):
        """ Returns int index of selected unit within its unit choices. e.g. bar in [MPa, bar, psi] would return 1. """
        if self.unit is None or self.unit_type in [Unitless, Percent]:
            return 0

        if self.unit not in self.unit_type.units():
            raise ValueError(f"Unit {self.unit} not found in unit choices")
        result = self.unit_type.units().index(self.unit)
        return result

    def _value_str(self):
        """ Returns formatted string representation of converted value. """
        return get_num_str(self.value)

    def get_distr_index(self) -> int:
        """Returns index of selected distribution. """
        result = Distributions.index(self._distr)
        return result

    def get_uncertainty_index(self) -> int:
        """Returns index of selected uncertainty option. """
        result = Uncertainties.index(self._uncertainty)
        return result

    def get_value_tooltip(self):
        """Returns tooltip for parameter. """
        if self.tooltip is None:
            if self.min_value == 0 and self.max_value == np.inf:
                result = "Enter a positive value"
            elif self.max_value == np.inf:
                result = f"Enter a value >= {self.min_value_str}"  # {self._param.unit}"
            else:
                result = f"Enter a value between {self.min_value_str} and {self.max_value_str}"
            return result
        else:
            return self.tooltip

    def get_prepped_value(self):
        """Returns parameter value, in standard units, prepared for analysis as Characterization or Distribution.

        Returns
        -------
        DeterministicCharacterization or Type(UncertaintyCharacterization)
            Parameter parsed as characterization.

        """
        if self._distr == 'det':
            result = DeterministicCharacterization(name=self.slug, value=self._value)
            return result

        uncertainty = 'epistemic' if self._uncertainty == 'epi' else 'aleatory'

        if self._distr == 'nor':
            result = NormalDistribution(name=self.slug,
                                        uncertainty_type=uncertainty,
                                        nominal_value=self._value,
                                        mean=self._a,
                                        std_deviation=self._b)
        elif self._distr == 'uni':
            result = UniformDistribution(name=self.slug,
                                         uncertainty_type=uncertainty,
                                         nominal_value=self._value,
                                         lower_bound=self._a,
                                         upper_bound=self._b)
        elif self._distr == 'log':
            result = LognormalDistribution(name=self.slug,
                                           uncertainty_type=uncertainty,
                                           nominal_value=self._value,
                                           mu=self._a,
                                           sigma=self._b)
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
        result = {
            'label': self.label,
            'slug': self.slug,
            'unit_type': self.unit_type.label,
            'unit': self.unit,
            'uncertainty': self._uncertainty,
            'value': float(self._value),
            'min_value': self.min_value_str,
            'max_value': self.max_value_str,
            'distr': self._distr,
            'a': float(self._a),
            'b': float(self._b),
        }
        return result

    def from_dict(self, data: dict, notify_from_model=True):
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
        # Verify all data present
        expected_keys = self.to_dict().keys()
        for key in expected_keys:
            if key not in data:
                raise ValueError(f'Required key {key} not found in data {data}')

        unit_type_key = data['unit_type']
        unit_type = get_unit_type(unit_type_key)

        self.label = data['label']
        self.slug = data['slug']
        self.unit_type = unit_type
        self.uncertainty = data['uncertainty']
        self.distr = data['distr']
        self.unit = data['unit']
        self._a = data['a']
        self._b = data['b']
        self.set_value_raw(float(data['value']))

        # parse value bounds which may be stored as string or float
        min_val = data.get('min_value', -np.inf)
        max_val = data.get('max_value', np.inf)
        self._min_value = -np.inf if type(min_val) is str and 'infinity' in min_val else float(min_val)
        self._max_value = np.inf if type(max_val) is str and 'infinity' in max_val else float(max_val)

        self.changed.notify(self)

        if notify_from_model:
            self.changed_by_model.notify(self)
