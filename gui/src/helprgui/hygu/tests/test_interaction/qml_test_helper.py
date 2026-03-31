"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

QML Test Helper - Provides Python backend for QML component tests.
Exposes test utilities and mock data to QML via Qt properties and slots.
"""
from typing import Optional

from PySide6.QtCore import QObject, Property, Signal, Slot

from ...forms.fields_probabilistic import UncertainFormField
from ...forms.fields import NumFormField, IntFormField, BoolFormField, ChoiceFormField, StringFormField, NumListFormField
from ...models.fields_probabilistic import UncertainField
from ...models.fields import NumField, IntField, BoolField, ChoiceField, StringField, NumListField
from ...utils.distributions import Distributions, Uncertainties, BaseChoiceList
from ...utils.units_of_measurement import Pressure, Temperature, SmallDistance, Fractional


class ValidationEvent:
    """Records a validation event for later inspection."""

    def __init__(self, param_name: str, status: int, message: str):
        self.param_name = param_name
        self.status = status
        self.message = message


class QmlTestHelper(QObject):
    """Test helper that provides UncertainFormField instances and validation tracking for QML tests.

    Usage in QML:
        tester.field - The UncertainFormField to test
        tester.set_subparam("lower", "20") - Set a sub-parameter value
        tester.get_validation_event_count() - Get number of validation events
        tester.clear_validation_events() - Clear recorded events
    """

    fieldChanged = Signal()
    validationEventReceived = Signal(str, int, str)  # param_name, status, message

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._validation_events: list[ValidationEvent] = []
        self._field: Optional[UncertainFormField] = None
        self._model: Optional[UncertainField] = None
        # Keep old fields alive to prevent "C++ object already deleted" errors
        # when QML still holds references during transitions
        self._old_fields: list[UncertainFormField] = []
        self._old_models: list[UncertainField] = []

        # NumFormField support
        self._num_field: Optional[NumFormField] = None
        self._num_model: Optional[NumField] = None
        self._old_num_fields: list[NumFormField] = []
        self._old_num_models: list[NumField] = []

    def _on_validation_changed(self, param_name: str, status: int, message: str):
        """Callback when validation state changes - records the event."""
        event = ValidationEvent(param_name, status, message)
        self._validation_events.append(event)
        self.validationEventReceived.emit(param_name, status, message)

    def _create_field(self,
                      label: str,
                      value: float,
                      distr: str = Distributions.det,
                      min_value: float = 0,
                      max_value: float = 100,
                      unit_type=None,
                      unit=None,
                      **kwargs
                      ) -> UncertainFormField:
        """Create a new UncertainFormField with the given parameters."""
        # Keep old field/model alive to prevent QML "C++ object deleted" errors
        if self._field is not None:
            self._old_fields.append(self._field)
        if self._model is not None:
            self._old_models.append(self._model)

        self._model = UncertainField(label=label,
                                     value=value,
                                     distr=distr,
                                     min_value=min_value,
                                     max_value=max_value,
                                     unit_type=unit_type,
                                     unit=unit,
                                     **kwargs)
        self._field = UncertainFormField(param=self._model)
        # Set parent to keep the Qt object alive
        self._field.setParent(self)

        # Connect validation signal to our tracker
        self._field.subparamValidationChanged.connect(self._on_validation_changed)

        self.fieldChanged.emit()
        return self._field

    @Property(QObject, notify=fieldChanged)
    def field(self) -> Optional[UncertainFormField]:
        """The UncertainFormField instance for QML binding."""
        return self._field

    # ==================== Factory Methods ====================

    @Slot(result=QObject)
    def create_deterministic_field(self) -> UncertainFormField:
        """Create a deterministic field for testing."""
        return self._create_field(label="Test Deterministic",
                                  value=50.0,
                                  distr=Distributions.det,
                                  min_value=0,
                                  max_value=100,
                                  unit_type=Pressure,
                                  unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_uniform_field(self) -> UncertainFormField:
        """Create a uniform distribution field for testing."""
        return self._create_field(label="Test Uniform",
                                  value=50.0,
                                  distr=Distributions.uni,
                                  lower=40.0,
                                  upper=60.0,
                                  min_value=0,
                                  max_value=100,
                                  unit_type=Pressure,
                                  unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_normal_field(self) -> UncertainFormField:
        """Create a normal distribution field for testing."""
        return self._create_field(label="Test Normal",
                                  value=50.0,
                                  distr=Distributions.nor,
                                  mean=50.0,
                                  std=10.0,
                                  min_value=0,
                                  max_value=100,
                                  unit_type=Pressure,
                                  unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_truncated_normal_field(self) -> UncertainFormField:
        """Create a truncated normal distribution field for testing."""
        return self._create_field(label="Test Truncated Normal",
                                  value=50.0,
                                  distr=Distributions.tnor,
                                  mean=50.0,
                                  std=10.0,
                                  lower=30.0,
                                  upper=70.0,
                                  min_value=0,
                                  max_value=100,
                                  unit_type=Pressure,
                                  unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_lognormal_field(self) -> UncertainFormField:
        """Create a lognormal distribution field for testing."""
        return self._create_field(label="Test Lognormal",
                                  value=50.0,
                                  distr=Distributions.log,
                                  mu=3.9,
                                  sigma=0.2,
                                  min_value=0,
                                  max_value=100,
                                  unit_type=Pressure,
                                  unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_truncated_lognormal_field(self) -> UncertainFormField:
        """Create a truncated lognormal distribution field for testing."""
        return self._create_field(label="Test Truncated Lognormal",
                                  value=50.0,
                                  distr=Distributions.tlog,
                                  mu=3.9,
                                  sigma=0.2,
                                  lower=30.0,
                                  upper=70.0,
                                  min_value=0,
                                  max_value=100,
                                  unit_type=Pressure,
                                  unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_beta_field(self) -> UncertainFormField:
        """Create a beta distribution field for testing."""
        return self._create_field(label="Test Beta",
                                  value=0.5,
                                  distr=Distributions.beta,
                                  alpha=2.0,
                                  beta=5.0,
                                  min_value=0,
                                  max_value=1)

    # ==================== Sub-parameter Manipulation ====================

    @Slot(str, str)
    def set_subparam(self, param_name: str, value: str):
        """Set a sub-parameter value by name. Used to trigger validation."""
        if self._field is None:
            return

        try:
            float_val = float(value)
        except ValueError:
            return

        # Map param names to field properties
        if param_name == "value" or param_name == "nominal":
            self._field.value = float_val
        elif param_name == "mean":
            self._field.mean = float_val
        elif param_name == "std":
            self._field.std = float_val
        elif param_name == "mu":
            self._field.mu = float_val
        elif param_name == "sigma":
            self._field.sigma = float_val
        elif param_name == "lower":
            self._field.lower = float_val
        elif param_name == "upper":
            self._field.upper = float_val
        elif param_name == "alpha":
            self._field.alpha = float_val
        elif param_name == "beta":
            self._field.beta = float_val

    @Slot(int)
    def set_distribution_by_index(self, index: int):
        """Change distribution type by combo box index."""
        if self._field is not None:
            self._field.set_input_type_from_index(index)

    @Slot(str)
    def set_distribution(self, distr: str):
        """Change distribution type by key (det, uni, nor, tnor, log, tlog, beta)."""
        if self._field is not None:
            self._field.input_type = distr

    @Slot(str)
    def set_uncertainty(self, uncertainty: str):
        """Set uncertainty type (ale or epi)."""
        if self._field is not None:
            self._field.uncertainty = uncertainty

    # ==================== Validation Event Access ====================

    @Slot(result=int)
    def get_validation_event_count(self) -> int:
        """Get number of recorded validation events."""
        return len(self._validation_events)

    @Slot(int, result=str)
    def get_validation_event_param(self, index: int) -> str:
        """Get parameter name for validation event at index."""
        if 0 <= index < len(self._validation_events):
            return self._validation_events[index].param_name
        return ""

    @Slot(int, result=int)
    def get_validation_event_status(self, index: int) -> int:
        """Get status for validation event at index (0=ERROR, 1=OK)."""
        if 0 <= index < len(self._validation_events):
            return self._validation_events[index].status
        return -1

    @Slot(int, result=str)
    def get_validation_event_message(self, index: int) -> str:
        """Get message for validation event at index."""
        if 0 <= index < len(self._validation_events):
            return self._validation_events[index].message
        return ""

    @Slot()
    def clear_validation_events(self):
        """Clear all recorded validation events."""
        self._validation_events.clear()

    # ==================== State Inspection ====================

    @Slot(result=str)
    def get_current_distribution(self) -> str:
        """Get current distribution type."""
        if self._field is not None:
            return self._field.input_type
        return ""

    @Slot(result=bool)
    def has_error(self) -> bool:
        """Check if any sub-parameter has an error."""
        # Check if any recent validation event was an error
        for event in self._validation_events:
            if event.status == 0:
                return True
        return False

    @Slot(str, result=bool)
    def is_field_visible(self, field_name: str) -> bool:
        """Check if a field should be visible for the current distribution.

        This mirrors the visibility logic in UncertainParamField.qml refresh().
        """
        if self._field is None:
            return False

        distr = self._field.input_type

        if field_name in ["nominal", "value"]:
            return True  # Always visible

        if field_name in ["mean", "std"]:
            return distr in [Distributions.nor, Distributions.tnor]

        if field_name in ["mu", "sigma"]:
            return distr in [Distributions.log, Distributions.tlog]

        if field_name in ["lower", "upper"]:
            return distr in [Distributions.tnor, Distributions.tlog, Distributions.uni]

        if field_name in ["alpha", "beta"]:
            return distr == Distributions.beta

        return False

    @Slot(result=str)
    def get_field_value(self) -> str:
        """Get the current nominal value as string."""
        if self._field is not None:
            return str(self._field.value)
        return ""

    @Slot(result=str)
    def get_input_type(self) -> str:
        """Get the current input/distribution type."""
        if self._field is not None:
            return self._field.input_type
        return ""

    # ==================== NumFormField Support ====================

    numFieldChanged = Signal()

    def _create_num_field(self, label: str,
                          value: float,
                          min_value: float = 0,
                          max_value: float = 100,
                          unit_type=None,
                          unit=None,
                          ) -> NumFormField:
        """Create a new NumFormField with the given parameters."""
        # Keep old field/model alive to prevent QML "C++ object deleted" errors
        if self._num_field is not None:
            self._old_num_fields.append(self._num_field)
        if self._num_model is not None:
            self._old_num_models.append(self._num_model)

        self._num_model = NumField(label=label,
                                   value=value,
                                   min_value=min_value,
                                   max_value=max_value,
                                   unit_type=unit_type,
                                   unit=unit)
        self._num_field = NumFormField(param=self._num_model)
        self._num_field.setParent(self)

        self.numFieldChanged.emit()
        return self._num_field

    @Property(QObject, notify=numFieldChanged)
    def num_field(self) -> Optional[NumFormField]:
        """The NumFormField instance for QML binding."""
        return self._num_field

    @Slot(result=QObject)
    def create_pressure_field(self) -> NumFormField:
        """Create a pressure field for testing."""
        return self._create_num_field(label="Test Pressure",
                                      value=50.0,
                                      min_value=0,
                                      max_value=100,
                                      unit_type=Pressure,
                                      unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_temperature_field(self) -> NumFormField:
        """Create a temperature field for testing."""
        return self._create_num_field(label="Test Temperature",
                                      value=300.0,
                                      min_value=200,
                                      max_value=500,
                                      unit_type=Temperature,
                                      unit=Temperature.k)

    @Slot(result=QObject)
    def create_distance_field(self) -> NumFormField:
        """Create a distance field for testing."""
        return self._create_num_field(label="Test Distance",
                                      value=0.005,
                                      min_value=0.001,
                                      max_value=0.1,
                                      unit_type=SmallDistance,
                                      unit=SmallDistance.m)

    @Slot(result=QObject)
    def create_fractional_field(self) -> NumFormField:
        """Create a fractional field for testing."""
        return self._create_num_field(label="Test Fractional",
                                      value=0.5,
                                      min_value=0,
                                      max_value=1,
                                      unit_type=Fractional,
                                      unit=Fractional.fr)

    @Slot(str)
    def set_num_value(self, value: str):
        """Set the numeric field value."""
        if self._num_field is None:
            return
        try:
            float_val = float(value)
            self._num_field.value = float_val
        except ValueError:
            pass

    @Slot(str)
    def set_num_unit(self, unit: str):
        """Set the numeric field unit."""
        if self._num_field is not None:
            self._num_field.unit = unit

    @Slot(result=str)
    def get_num_value(self) -> str:
        """Get the current numeric value as string."""
        if self._num_field is not None:
            return str(self._num_field.value)
        return ""

    @Slot(result=str)
    def get_num_unit(self) -> str:
        """Get the current unit."""
        if self._num_field is not None:
            return self._num_field.unit
        return ""

    @Slot(result=str)
    def get_num_unit_type(self) -> str:
        """Get the unit type label."""
        if self._num_field is not None:
            return self._num_field.unit_type
        return ""

    @Slot(result=float)
    def get_num_min_value(self) -> float:
        """Get the minimum allowed value."""
        if self._num_field is not None:
            return self._num_field.min_value
        return 0.0

    @Slot(result=float)
    def get_num_max_value(self) -> float:
        """Get the maximum allowed value."""
        if self._num_field is not None:
            return self._num_field.max_value
        return 0.0

    @Slot(result=int)
    def get_num_unit_index(self) -> int:
        """Get the current unit index."""
        if self._num_field is not None:
            return self._num_field.get_unit_index()
        return 0

    @Slot(result=str)
    def get_num_label(self) -> str:
        """Get the field label."""
        if self._num_field is not None:
            return self._num_field.label
        return ""

    @Slot(result=str)
    def get_num_value_tooltip(self) -> str:
        """Get the value tooltip."""
        if self._num_field is not None:
            return self._num_field.value_tooltip or ""
        return ""

    # ==================== IntFormField Support ====================

    intFieldChanged = Signal()

    def _create_int_field(self, label: str, value: int, min_value: int = 0, max_value: int = 100) -> IntFormField:
        """Create a new IntFormField with the given parameters."""
        if not hasattr(self, '_old_int_fields'):
            self._old_int_fields = []
            self._old_int_models = []

        if hasattr(self, '_int_field') and self._int_field is not None:
            self._old_int_fields.append(self._int_field)
        if hasattr(self, '_int_model') and self._int_model is not None:
            self._old_int_models.append(self._int_model)

        self._int_model = IntField(label=label,
                                   value=value,
                                   min_value=min_value,
                                   max_value=max_value,
                                   )
        self._int_field = IntFormField(param=self._int_model)
        self._int_field.setParent(self)

        self.intFieldChanged.emit()
        return self._int_field

    @Property(QObject, notify=intFieldChanged)
    def int_field(self) -> Optional[IntFormField]:
        """The IntFormField instance for QML binding."""
        return getattr(self, '_int_field', None)

    @Slot(result=QObject)
    def create_sample_count_field(self) -> IntFormField:
        """Create a sample count field for testing."""
        return self._create_int_field(label="Sample Count",
                                      value=50,
                                      min_value=1,
                                      max_value=10000)

    @Slot(result=QObject)
    def create_iteration_field(self) -> IntFormField:
        """Create an iteration count field for testing."""
        return self._create_int_field(label="Iterations",
                                      value=100,
                                      min_value=1,
                                      max_value=1000)

    @Slot(str)
    def set_int_value(self, value: str):
        """Set the int field value."""
        if not hasattr(self, '_int_field') or self._int_field is None:
            return
        try:
            int_val = int(value)
            self._int_field.value = int_val
        except ValueError:
            pass

    @Slot(result=str)
    def get_int_value(self) -> str:
        """Get the current int value as string."""
        if hasattr(self, '_int_field') and self._int_field is not None:
            val = self._int_field.value
            return str(val) if val is not None else ""
        return ""

    @Slot(result=int)
    def get_int_min_value(self) -> int:
        """Get the minimum allowed int value."""
        if hasattr(self, '_int_field') and self._int_field is not None:
            return self._int_field.min_value
        return 0

    @Slot(result=int)
    def get_int_max_value(self) -> int:
        """Get the maximum allowed int value."""
        if hasattr(self, '_int_field') and self._int_field is not None:
            return self._int_field.max_value
        return 0

    @Slot(result=str)
    def get_int_label(self) -> str:
        """Get the int field label."""
        if hasattr(self, '_int_field') and self._int_field is not None:
            return self._int_field.label
        return ""

    @Slot(result=bool)
    def get_int_is_null(self) -> bool:
        """Check if int field is null."""
        if hasattr(self, '_int_field') and self._int_field is not None:
            return self._int_field.is_null
        return False

    @Slot()
    def set_int_null(self):
        """Set the int field to null."""
        if hasattr(self, '_int_field') and self._int_field is not None:
            self._int_field.set_null()

    # ==================== BoolFormField Support ====================

    boolFieldChanged = Signal()

    def _create_bool_field(self, label: str, value: bool = False,) -> BoolFormField:
        """Create a new BoolFormField with the given parameters."""
        if not hasattr(self, '_old_bool_fields'):
            self._old_bool_fields = []
            self._old_bool_models = []

        if hasattr(self, '_bool_field') and self._bool_field is not None:
            self._old_bool_fields.append(self._bool_field)
        if hasattr(self, '_bool_model') and self._bool_model is not None:
            self._old_bool_models.append(self._bool_model)

        self._bool_model = BoolField(label=label,
                                      value=value)
        self._bool_field = BoolFormField(param=self._bool_model)
        self._bool_field.setParent(self)

        self.boolFieldChanged.emit()
        return self._bool_field

    @Property(QObject, notify=boolFieldChanged)
    def bool_field(self) -> Optional[BoolFormField]:
        """The BoolFormField instance for QML binding."""
        return getattr(self, '_bool_field', None)

    @Slot(result=QObject)
    def create_enabled_field(self) -> BoolFormField:
        """Create an enabled/disabled field for testing."""
        return self._create_bool_field(label="Enabled",
                                       value=True)

    @Slot(result=QObject)
    def create_debug_field(self) -> BoolFormField:
        """Create a debug mode field for testing."""
        return self._create_bool_field(label="Debug Mode",
                                       value=False)

    @Slot(bool)
    def set_bool_value(self, value: bool):
        """Set the bool field value."""
        if hasattr(self, '_bool_field') and self._bool_field is not None:
            self._bool_field.value = value

    @Slot(result=bool)
    def get_bool_value(self) -> bool:
        """Get the current bool value."""
        if hasattr(self, '_bool_field') and self._bool_field is not None:
            return self._bool_field.value
        return False

    @Slot(result=str)
    def get_bool_label(self) -> str:
        """Get the bool field label."""
        if hasattr(self, '_bool_field') and self._bool_field is not None:
            return self._bool_field.label
        return ""

    # ==================== ChoiceFormField Support ====================

    choiceFieldChanged = Signal()

    def _make_choice_list(self, choices: list) -> type:
        """Create a BaseChoiceList subclass from a list of (key, label) tuples."""
        keys = [c[0] for c in choices]
        labels = [c[1] for c in choices]

        # Dynamically create a BaseChoiceList subclass
        choice_class = type('DynamicChoiceList', (BaseChoiceList,), {
            'keys': keys,
            'labels': labels,
        })
        return choice_class

    def _create_choice_field(self, label: str, choices: list, value: str = None,) -> ChoiceFormField:
        """Create a new ChoiceFormField with the given parameters.

        Parameters
        ----------
        choices : list
            List of (key, label) tuples, e.g. [('det', 'Deterministic'), ('prb', 'Probabilistic')]
        """
        if not hasattr(self, '_old_choice_fields'):
            self._old_choice_fields = []
            self._old_choice_models = []

        if hasattr(self, '_choice_field') and self._choice_field is not None:
            self._old_choice_fields.append(self._choice_field)
        if hasattr(self, '_choice_model') and self._choice_model is not None:
            self._old_choice_models.append(self._choice_model)

        choice_list = self._make_choice_list(choices)

        self._choice_model = ChoiceField(label=label,
                                          choices=choice_list,
                                          value=value if value else choice_list.keys[0])
        self._choice_field = ChoiceFormField(param=self._choice_model)
        self._choice_field.setParent(self)

        self.choiceFieldChanged.emit()
        return self._choice_field

    @Property(QObject, notify=choiceFieldChanged)
    def choice_field(self) -> Optional[ChoiceFormField]:
        """The ChoiceFormField instance for QML binding."""
        return getattr(self, '_choice_field', None)

    @Slot(result=QObject)
    def create_study_type_field(self) -> ChoiceFormField:
        """Create a study type field for testing."""
        return self._create_choice_field(label="Study Type",
                                         choices=[('det', 'Deterministic'),
                                                  ('prb', 'Probabilistic'),
                                                  ('sam', 'Samples'),
                                                  ('bnd', 'Bounds')],
                                         value='det')

    @Slot(result=QObject)
    def create_method_field(self) -> ChoiceFormField:
        """Create a method field for testing."""
        return self._create_choice_field(label="Method",
                                         choices=[('fast', 'Fast'),
                                                  ('accurate', 'Accurate'),
                                                  ('balanced', 'Balanced')],
                                         value='balanced')

    @Slot(int)
    def set_choice_by_index(self, index: int):
        """Set choice by index."""
        if hasattr(self, '_choice_field') and self._choice_field is not None:
            self._choice_field.value = index

    @Slot(result=str)
    def get_choice_value(self) -> str:
        """Get the current choice value key."""
        if hasattr(self, '_choice_field') and self._choice_field is not None:
            return self._choice_field.value
        return ""

    @Slot(result=int)
    def get_choice_index(self) -> int:
        """Get the current choice index."""
        if hasattr(self, '_choice_field') and self._choice_field is not None:
            return self._choice_field.get_index()
        return 0

    @Slot(result=str)
    def get_choice_label(self) -> str:
        """Get the choice field label."""
        if hasattr(self, '_choice_field') and self._choice_field is not None:
            return self._choice_field.label
        return ""

    @Slot(result=str)
    def get_choice_value_display(self) -> str:
        """Get the display text for current selection."""
        if hasattr(self, '_choice_field') and self._choice_field is not None:
            return self._choice_field.value_display
        return ""

    @Slot(result=int)
    def get_choice_count(self) -> int:
        """Get the number of choices available."""
        if hasattr(self, '_choice_model') and self._choice_model is not None:
            return len(self._choice_model.choices)
        return 0

    # ==================== StringFormField Support ====================

    stringFieldChanged = Signal()

    def _create_string_field(self, label: str, value: str = "",) -> StringFormField:
        """Create a new StringFormField with the given parameters."""
        if not hasattr(self, '_old_string_fields'):
            self._old_string_fields = []
            self._old_string_models = []

        if hasattr(self, '_string_field') and self._string_field is not None:
            self._old_string_fields.append(self._string_field)
        if hasattr(self, '_string_model') and self._string_model is not None:
            self._old_string_models.append(self._string_model)

        self._string_model = StringField(label=label,
                                          value=value)
        self._string_field = StringFormField(param=self._string_model)
        self._string_field.setParent(self)

        self.stringFieldChanged.emit()
        return self._string_field

    @Property(QObject, notify=stringFieldChanged)
    def string_field(self) -> Optional[StringFormField]:
        """The StringFormField instance for QML binding."""
        return getattr(self, '_string_field', None)

    @Slot(result=QObject)
    def create_name_field(self) -> StringFormField:
        """Create a name field for testing."""
        return self._create_string_field(label="Analysis Name",
                                         value="Test Analysis")

    @Slot(result=QObject)
    def create_description_field(self) -> StringFormField:
        """Create a description field for testing."""
        return self._create_string_field(label="Description",
                                         value="")

    @Slot(result=QObject)
    def create_file_path_field(self) -> StringFormField:
        """Create a file path field for testing FileSelector."""
        return self._create_string_field(label="Input File",
                                         value="/path/to/data.csv")

    @Slot(result=QObject)
    def create_empty_file_path_field(self) -> StringFormField:
        """Create an empty file path field for testing FileSelector."""
        return self._create_string_field(label="Input File",
                                         value="")

    @Slot(result=QObject)
    def create_directory_path_field(self) -> StringFormField:
        """Create a directory path field for testing DirectorySelector."""
        return self._create_string_field(label="Output Directory",
                                         value="/path/to/output")

    @Slot(result=QObject)
    def create_empty_directory_path_field(self) -> StringFormField:
        """Create an empty directory path field for testing DirectorySelector."""
        return self._create_string_field(label="Output Directory",
                                         value="")

    @Slot(str)
    def set_string_value(self, value: str):
        """Set the string field value."""
        if hasattr(self, '_string_field') and self._string_field is not None:
            self._string_field.value = value

    @Slot(result=str)
    def get_string_value(self) -> str:
        """Get the current string value."""
        if hasattr(self, '_string_field') and self._string_field is not None:
            return self._string_field.value
        return ""

    @Slot(result=str)
    def get_string_label(self) -> str:
        """Get the string field label."""
        if hasattr(self, '_string_field') and self._string_field is not None:
            return self._string_field.label
        return ""

    # ==================== NumListFormField Support ====================

    numListFieldChanged = Signal()

    def _create_num_list_field(self,
                               label: str,
                               value: list,
                               min_value: float = 0,
                               max_value: float = 100,
                               unit_type=None,
                               unit=None) -> NumListFormField:
        """Create a new NumListFormField with the given parameters."""
        if not hasattr(self, '_old_num_list_fields'):
            self._old_num_list_fields = []
            self._old_num_list_models = []

        if hasattr(self, '_num_list_field') and self._num_list_field is not None:
            self._old_num_list_fields.append(self._num_list_field)
        if hasattr(self, '_num_list_model') and self._num_list_model is not None:
            self._old_num_list_models.append(self._num_list_model)

        self._num_list_model = NumListField(label=label,
                                            value=value,
                                            min_value=min_value,
                                            max_value=max_value,
                                            unit_type=unit_type,
                                            unit=unit)
        self._num_list_field = NumListFormField(param=self._num_list_model)
        self._num_list_field.setParent(self)

        self.numListFieldChanged.emit()
        return self._num_list_field

    @Property(QObject, notify=numListFieldChanged)
    def num_list_field(self) -> Optional[NumListFormField]:
        """The NumListFormField instance for QML binding."""
        return getattr(self, '_num_list_field', None)

    @Slot(result=QObject)
    def create_cycle_times_field(self) -> NumListFormField:
        """Create a cycle times field for testing."""
        return self._create_num_list_field(label="Cycle Times",
                                           value=[1.0, 2.0, 3.0, 4.0, 5.0],
                                           min_value=0,
                                           max_value=100,
                                           unit_type=Pressure,
                                           unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_temperature_list_field(self) -> NumListFormField:
        """Create a temperature list field for testing."""
        return self._create_num_list_field(label="Temperature Profile",
                                           value=[300.0, 350.0, 400.0],
                                           min_value=200,
                                           max_value=600,
                                           unit_type=Temperature,
                                           unit=Temperature.k)

    @Slot(result=QObject)
    def create_empty_list_field(self) -> NumListFormField:
        """Create an empty list field for testing."""
        return self._create_num_list_field(label="Empty List",
                                           value=[],
                                           min_value=0,
                                           max_value=1000,
                                           unit_type=Pressure,
                                           unit=Pressure.mpa)

    @Slot(str)
    def set_num_list_value(self, value: str):
        """Set the num list field value from space-separated string."""
        if hasattr(self, '_num_list_field') and self._num_list_field is not None:
            self._num_list_field.value = value

    @Slot(result=str)
    def get_num_list_value(self) -> str:
        """Get the current num list value as space-separated string."""
        if hasattr(self, '_num_list_field') and self._num_list_field is not None:
            return self._num_list_field.value
        return ""

    @Slot(result=int)
    def get_num_list_count(self) -> int:
        """Get the number of values in the list."""
        if hasattr(self, '_num_list_model') and self._num_list_model is not None:
            return len(self._num_list_model.value)
        return 0

    @Slot(result=str)
    def get_num_list_label(self) -> str:
        """Get the num list field label."""
        if hasattr(self, '_num_list_field') and self._num_list_field is not None:
            return self._num_list_field.label
        return ""

    @Slot(result=str)
    def get_num_list_unit_type(self) -> str:
        """Get the num list unit type."""
        if hasattr(self, '_num_list_field') and self._num_list_field is not None:
            return self._num_list_field.unit_type
        return ""

    @Slot(result=float)
    def get_num_list_min_value(self) -> float:
        """Get the minimum allowed value."""
        if hasattr(self, '_num_list_field') and self._num_list_field is not None:
            return self._num_list_field.min_value
        return 0.0

    @Slot(result=float)
    def get_num_list_max_value(self) -> float:
        """Get the maximum allowed value."""
        if hasattr(self, '_num_list_field') and self._num_list_field is not None:
            return self._num_list_field.max_value
        return 0.0

    @Slot(result=str)
    def get_num_list_value_tooltip(self) -> str:
        """Get the value tooltip."""
        if hasattr(self, '_num_list_model') and self._num_list_model is not None:
            return self._num_list_model.get_value_tooltip() or ""
        return ""

    # ==================== Nullable NumFormField Support (for FloatNullableParamField) ====================

    @Slot(result=QObject)
    def create_nullable_float_field(self) -> NumFormField:
        """Create a nullable float field for testing."""
        return self._create_num_field(label="Optional Value",
                                      value=25.0,
                                      min_value=0,
                                      max_value=100,
                                      unit_type=Pressure,
                                      unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_nullable_null_field(self) -> NumFormField:
        """Create a nullable float field starting as null."""
        field = self._create_num_field(label="Initially Null",
                                       value=0.0,
                                       min_value=0,
                                       max_value=100,
                                       unit_type=Pressure,
                                       unit=Pressure.mpa)
        # Set to null after creation
        self._num_field.set_null("value")
        return field

    @Slot(result=bool)
    def get_num_is_null(self) -> bool:
        """Check if num field is null."""
        if self._num_field is not None:
            return self._num_field.is_null
        return False

    @Slot()
    def set_num_null(self):
        """Set the num field to null."""
        if self._num_field is not None:
            self._num_field.set_null("value")

    # ==================== ReadonlyParameter Support (uses UncertainFormField) ====================

    @Slot(result=QObject)
    def create_readonly_result_field(self) -> UncertainFormField:
        """Create a readonly field for testing computed results."""
        return self._create_field(label="Computed Result",
                                  value=123.456,
                                  distr=Distributions.det,
                                  min_value=0,
                                  max_value=1000,
                                  unit_type=Pressure,
                                  unit=Pressure.mpa)

    @Slot(result=QObject)
    def create_readonly_infinity_field(self) -> UncertainFormField:
        """Create a readonly field with infinite value."""
        import math
        return self._create_field(label="Infinite Result",
                                  value=math.inf,
                                  distr=Distributions.det,
                                  min_value=0,
                                  max_value=math.inf,
                                  unit_type=Pressure,
                                  unit=Pressure.mpa)

    @Slot(result=str)
    def get_field_unit_display(self) -> str:
        """Get the unit display text for the field."""
        if self._field is not None:
            return self._field.get_unit_disp
        return ""
