"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
from PySide6.QtCore import QObject, Slot, Signal, Property, QStringListModel
from PySide6.QtQml import QmlElement

from parameters.models import Parameter, ChoiceParameter, BasicParameter, BoolParameter
from utils.distributions import Uncertainties

QML_IMPORT_NAME = "helpr.classes"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ChoiceParameterController(QObject):
    """Manages parameter model comprising a list of choices typically displayed with a selector combo-box.

    Attributes
    ----------
    choices
    label
    value
    value_display
    str_display
    valueChanged : Signal
        Event emitted when parameter value changes via UI.
    modelChanged : Signal
        Event emitted when state model changes value.

    """
    valueChanged = Signal(str)
    modelChanged = Signal()
    _param: ChoiceParameter
    _choices: QStringListModel

    def __init__(self, param=None):
        """Initializes controller with parameter model.

        Parameters
        ----------
        param : ChoiceParameter
            Parameter model object with which to bind.

        """
        super().__init__(parent=None)
        self._param = param
        self._choices = QStringListModel(self._param.get_choice_displays())
        self._param.changed_by_model += lambda x: self.modelChanged.emit()

    @Property(QObject, constant=True)
    def choices(self):
        """List of parameter choices as QStringListModel. """
        return self._choices

    @Property(str, constant=True)
    def label(self):
        """Parameter label. """
        return self._param.label

    @Property(str, notify=valueChanged)
    def value(self):
        """Shortened key representation of stored value. """
        return self._param.get_value()

    @value.setter
    def value(self, index: int):
        """Sets value from selected index into list of choices.

        Parameters
        ----------
        index : int
            Index into list of parameter choices.

        """
        self._param.set_value_from_index(int(index))
        self.valueChanged.emit(self._param.get_value())

    @Property(str)
    def value_display(self):
        """Display-ready value; e.g. 'deterministic'. """
        return self._param.get_value_display()

    @Property(str)
    def str_display(self):
        """String representation of Parameter including label and value. """
        return self._param.str_display

    @Slot(result=int)
    def get_index(self):
        """Returns index of currently-selected value out of available choices. """
        result = self._param.get_value_index()
        return result


@QmlElement
class BasicParameterController(QObject):
    """Manages simple parameter model object.

    Attributes
    ----------
    label
    min_value
    max_value
    str_display
    value_tooltip
    enabled
    value : int
        Stored parameter value which is deterministic and unit-less.
    valueChanged : Signal
        Event emitted when parameter value changes via UI.
    labelChanged : Signal
        Event emitted when parameter label is changed.
    modelChanged : Signal
        Event emitted when state model changes value.

    """
    valueChanged = Signal(int)
    labelChanged = Signal(str)
    modelChanged = Signal()
    _param: BasicParameter

    def __init__(self, param=None):
        """Assigns parameter model. """
        super().__init__(parent=None)
        self._param = param
        self._param.changed_by_model += lambda x: self.modelChanged.emit()

    @Property(str, notify=labelChanged)
    def label(self):
        """Parameter label. """
        return self._param.label

    @Property(str, constant=True)
    def min_value(self):
        """Minimum value allowed, as string. """
        return str(self._param.min_value_str)

    @Property(str, constant=True)
    def max_value(self):
        """Maximum value allowed, as string. """
        return str(self._param.max_value_str)

    def get_value(self):
        val = int(self._param.value)
        return val

    def set_value(self, val: int):
        self._param.value = val
        self.valueChanged.emit(val)

    @Property(str)
    def str_display(self):
        """String representation of Parameter including label and value. """
        return self._param.str_display

    @Property(str, constant=True)
    def value_tooltip(self):
        """Tooltip description of parameter. """
        return self._param.get_value_tooltip()

    @Property(bool, constant=True)
    def enabled(self):
        """Whether parameter is currently enabled and ready for changes. """
        return bool(self._param.enabled)

    value = Property(int, get_value, set_value, notify=valueChanged)


@QmlElement
class BoolParameterController(QObject):
    """Manages boolean parameter model.

    Attributes
    ----------
    label
    str_display
    enabled
    value : bool
        Parameter bool value.
    valueChanged : Signal
        Event emitted when parameter value changes via UI.
    modelChanged : Signal
        Event emitted when state model changes value.

    """
    valueChanged = Signal(bool)
    modelChanged = Signal()
    _param: BoolParameter

    def __init__(self, param=None):
        """Assigns parameter model. """
        super().__init__(parent=None)
        self._param = param
        self._param.changed_by_model += lambda x: self.modelChanged.emit()

    @Property(str, constant=True)
    def label(self):
        """Parameter label. """
        return self._param.label

    def get_value(self):
        val = bool(self._param.value)
        return val

    def set_value(self, val: bool):
        self._param.value = val
        self.valueChanged.emit(val)

    @Property(str)
    def str_display(self):
        """String representation of Parameter including label and value. """
        return self._param.str_display

    @Property(bool, constant=True)
    def enabled(self):
        """Whether parameter is currently enabled and ready for changes. """
        return bool(self._param.enabled)

    value = Property(bool, get_value, set_value, notify=valueChanged)


@QmlElement
class ParameterController(QObject):
    """Manages float parameter model object.

    Attributes
    ----------
    unit_choices
    label
    label_rtf
    min_value
    max_value
    unit_type
    get_unit_disp
    value_tooltip
    str_display
    unit : str
        Key defining active unit of measurement; e.g. 'm'.
    unit_type : UnitType
        Class of units of measurement, e.g. Distance.
    value : float
        Parameter value in selected units; e.g. 315 K.
    input_type : {'det', 'nor', 'log', 'uni'}
        Key representation of input or distribution.
    uncertainty : {'ale', 'epi', None}
        Type of uncertainty, if any.
    a : float
        Non-deterministic distribution parameter (minimum bound or mean).
    b : float
        Non-deterministic distribution parameter (maximum bound or standard deviation).
    value : int
        Stored parameter value which is deterministic and unit-less.
    valueChanged : Signal
        Event emitted when parameter value changes via UI.
    aChanged : Signal
        Event emitted when parameter `a` changes.
    bChanged : Signal
        Event emitted when parameter `b` changes.
    labelChanged : Signal
        Event emitted when parameter label is changed.
    unitChanged : Signal
        Event emitted when parameter unit is changed.
    inputTypeChanged : Signal
        Event emitted when parameter input type is changed.
    uncertaintyChanged : Signal
        Event emitted when parameter uncertainty is changed.
    modelChanged : Signal
        Event emitted when state model changes value.

    """
    valueChanged = Signal(float)
    aChanged = Signal(float)
    bChanged = Signal(float)
    labelChanged = Signal(str)
    unitChanged = Signal(str)
    inputTypeChanged = Signal(str)
    uncertaintyChanged = Signal(str)

    modelChanged = Signal()
    _param: Parameter
    _unit_choices: QStringListModel

    def __init__(self, param=None):
        """Assigns model parameter to bind and preps unit choice list. """
        super().__init__(parent=None)
        self._param = param
        self._unit_choices = QStringListModel(self._param.unit_choices_display)

        # listen for db update to distribution
        self._param.distr_changed += lambda x: self.inputTypeChanged.emit(self._param.distr)
        self._param.uncertainty_changed += lambda x: self.uncertaintyChanged.emit(self._param.uncertainty)
        self._param.changed_by_model += lambda x: self.modelChanged.emit()

    @Property(QObject, constant=True)
    def unit_choices(self):
        """QObject representing list of unit choices available. """
        return self._unit_choices

    @Property(str, notify=labelChanged)
    def label(self):
        """Parameter label. """
        return self._param.label

    @Property(str, constant=True)
    def label_rtf(self):
        """Parameter label in rich-text formatting; e.g. Volume H<sub>2</sub>. """
        return self._param.label_rtf

    @Property(float, constant=True)
    def min_value(self):
        """Minimum value allowed as string, in selected units."""
        result = float(self._param.min_value)
        return result

    @Property(float, constant=True)
    def max_value(self):
        """Maximum value allowed as string, in selected units."""
        result = float(self._param.max_value)
        return result

    @Property(str)
    def unit_type(self):
        """UnitType as string, e.g. 'Temperature'. """
        return self._param.unit_type

    @Property(str)
    def get_unit_disp(self):
        """Display-ready representation of active unit. """
        return self._param.unit_choices_display[self._param.get_unit_index()]

    @Property(str)
    def uncertainty_disp(self):
        """Display-ready representation of uncertainty. """
        val = ""
        if self.uncertainty == Uncertainties.ale:
            val = "aleatory"
        elif self.uncertainty == Uncertainties.epi:
            val = "epistemic"
        return val

    # ==========================
    # PROPERTY GETTERS & SETTERS

    def get_value(self):
        val = self._param.value
        if type(val) is float:
            val = round(val, 8)
        return val

    def set_value(self, val: float):
        self._param.value = val
        self.valueChanged.emit(val)

    def get_input_type(self):
        return self._param.distr

    def set_input_type(self, val):
        self._param.distr = str(val)
        self.inputTypeChanged.emit(val)

    def get_uncertainty(self):
        return self._param.uncertainty

    def set_uncertainty(self, val):
        self._param.uncertainty = str(val)
        self.uncertaintyChanged.emit(val)

    def get_unit(self):
        return self._param.unit

    def set_unit(self, val: str):
        self._param.set_unit_from_display(val)
        self.unitChanged.emit(val)

    def get_a(self):
        return self._param.a

    def set_a(self, val: float):
        self._param.a = val

    def get_b(self):
        return self._param.b

    def set_b(self, val: float):
        self._param.b = val

    unit = Property(str, get_unit, set_unit, notify=unitChanged)
    input_type = Property(str, get_input_type, set_input_type, notify=inputTypeChanged)
    uncertainty = Property(str, get_uncertainty, set_uncertainty, notify=uncertaintyChanged)
    value = Property(float, get_value, set_value, notify=valueChanged)
    a = Property(float, get_a, set_a, notify=aChanged)
    b = Property(float, get_b, set_b, notify=bChanged)

    # =================
    # UTILITY FUNCTIONS
    @Slot(result=int)
    def get_unit_index(self):
        """Returns index of active unit. """
        # print(f"PC | {self.label} get_unit_index of {self.get_unit()} in {self._param.unit_choices_display}")
        result = self._param.get_unit_index()
        return result

    @Slot(result=int)
    def get_input_type_index(self):
        """Returns index of selected input type. """
        result = self._param.get_distr_index()
        return result

    @Slot(result=int)
    def get_uncertainty_index(self):
        """Returns index of selected uncertainty type. """
        result = self._param.get_uncertainty_index()
        return result

    @Property(str, constant=True)
    def value_tooltip(self):
        """Tooltip representation of parameter. """
        return self._param.get_value_tooltip()

    @Property(str)
    def str_display(self):
        """Representation of parameter including label and value. """
        return self._param.str_display


