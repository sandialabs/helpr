"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
from PySide6.QtCore import QObject, Slot, Signal, Property, QStringListModel
from PySide6.QtQml import QmlElement

from ..forms.fields import FormFieldBase
from ..models.fields_probabilistic import UncertainField
from ..utils.distributions import Uncertainties, DistributionParam as DP

QML_IMPORT_NAME = "hygu.classes"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class UncertainFormField(FormFieldBase):
    """Manages float parameter model object.

    Attributes
    ----------
    unit_choices
    min_value
    max_value
    unit_type
    get_unit_disp
    uncertainty_plot
    unit : str
        Key defining active unit of measurement; e.g. 'm'.
    unit_type : UnitType
        Class of units of measurement, e.g. Distance.
    value : float
        Parameter value in selected units; e.g. 315 K.
    use_nominal : bool
        Whether this parameter allows a nominal input
    use_uncertainty_type : bool
        Whether this parameter shows the uncertainty type input (aleatory, etc.)
    input_type : {'det', 'tnor', 'tlog', 'nor', 'log', 'uni', 'beta'}
        Key representation of input or distribution.
    uncertainty : {'ale', 'epi', None}
        Type of uncertainty, if any.
    mean : float
        Mean value for normal distributions.
    mu : float
        Mu parameter for lognormal distributions.
    std : float
        Standard deviation for normal distributions.
    sigma : float
        Sigma parameter for lognormal distributions.
    lower : float
        Lower bound for uniform and truncated distributions.
    upper : float or None
        Upper bound for uniform and truncated distributions.
    alpha : float
        alpha parameter for beta distribution.
    beta : float
        beta parameter for beta distribution.
    valueChanged : Signal
        Event emitted when parameter value changes via UI.
    meanChanged : Signal
        Event emitted when mean parameter changes.
    muChanged : Signal
        Event emitted when mu parameter changes.
    stdChanged : Signal
        Event emitted when standard deviation parameter changes.
    sigmaChanged : Signal
        Event emitted when sigma parameter changes.
    lowerChanged : Signal
        Event emitted when lower bound changes.
    upperChanged : Signal
        Event emitted when upper bound changes.
    alphaChanged : Signal
        Event emitted when alpha parameter changes.
    betaChanged : Signal
        Event emitted when beta parameter changes.
    labelChanged : Signal
        Event emitted when parameter label is changed.
    unitChanged : Signal
        Event emitted when parameter unit is changed.
    inputTypeChanged : Signal
        Event emitted when parameter input type is changed.
    uncertaintyChanged : Signal
        Event emitted when parameter uncertainty is changed.

    nominal_tooltip : str
        Tooltip for the nominal value input field.
    mean_tooltip : str
        Tooltip for the mean value input field.
    std_tooltip : str
        Tooltip for the standard deviation input field.
    mu_tooltip : str
        Tooltip for the mu value input field.
    sigma_tooltip : str
        Tooltip for the sigma input field.
    lower_tooltip : str
        Tooltip for the lower bound input field.
    upper_tooltip : str
        Tooltip for the upper bound input field.
    alpha_tooltip : str
        Tooltip for the alpha input field.
    beta_tooltip : str
        Tooltip for the beta input field.

    nominalTooltipChanged : Signal
        Event emitted when the nominal value tooltip changes.
    meanTooltipChanged : Signal
        Event emitted when the mean tooltip changes.
    stdTooltipChanged : Signal
        Event emitted when the standard deviation ('std') tooltip changes.
    muTooltipChanged : Signal
        Event emitted when the mu tooltip changes.
    sigmaTooltipChanged : Signal
        Event emitted when the sigma tooltip changes.
    lowerTooltipChanged : Signal
        Event emitted when the lower bound tooltip changes.
    upperTooltipChanged : Signal
        Event emitted when the upper bound tooltip changes.
    alphaTooltipChanged : Signal
        Event emitted when the alpha tooltip changes.
    betaTooltipChanged : Signal
        Event emitted when the beta tooltip changes.
    subparamValidationChanged : Signal
        Event emitted when a subparameter's validation state changes.

    """
    valueChanged = Signal(float)
    meanChanged = Signal(float)
    stdChanged = Signal(float)
    muChanged = Signal(float)
    sigmaChanged = Signal(float)
    lowerChanged = Signal(float)
    upperChanged = Signal(float)

    alphaChanged = Signal(float)
    betaChanged = Signal(float)

    unitChanged = Signal(str)
    inputTypeChanged = Signal(str)
    uncertaintyChanged = Signal(str)

    # Signals for tooltip updates
    nominalTooltipChanged = Signal(str)
    meanTooltipChanged = Signal(str)
    stdTooltipChanged = Signal(str)
    muTooltipChanged = Signal(str)
    sigmaTooltipChanged = Signal(str)
    lowerTooltipChanged = Signal(str)
    upperTooltipChanged = Signal(str)
    alphaTooltipChanged = Signal(str)
    betaTooltipChanged = Signal(str)

    # Signal for validation updates
    subparamValidationChanged = Signal(str, int, str)  # param_name, status, message

    _param: UncertainField
    _unit_choices: QStringListModel
    _distr_choices: QStringListModel

    def __init__(self, param=None):
        """Assigns model parameter to bind and preps unit choice list. """
        super().__init__(param=param)
        self._unit_choices = QStringListModel(self._param.unit_choices_display)
        self._distr_choices = QStringListModel(self._param.distr_choices_display)

        self._nominal_tooltip = ""
        self._mean_tooltip = ""
        self._std_tooltip = ""
        self._mu_tooltip = ""
        self._sigma_tooltip = ""
        self._lower_tooltip = ""
        self._upper_tooltip = ""
        self._alpha_tooltip = ""
        self._beta_tooltip = ""

        self._update_tooltips()

        # listen for db update to distribution
        self._param.distr_changed += lambda x: self._on_distribution_changed(x)
        self._param.uncertainty_changed += lambda x: self.uncertaintyChanged.emit(self._param.uncertainty)
        # self._param.subparam_validation_changed += lambda x, param_name, status, message: self.subparamValidationChanged.emit(param_name, status, message)
        self._param.subparam_validation_changed += self._on_subparam_validation_changed

    def _on_subparam_validation_changed(self, _, param_name, status, message):
        """Handle sub-parameter validation state change by updating tooltips and emitting signal."""
        self._update_tooltips()
        self.subparamValidationChanged.emit(param_name, status, message)

    def _update_tooltips(self):
        """Initialize tooltips for all sub-parameters."""
        self._nominal_tooltip = self._param.get_sub_tooltip(DP.NOMINAL)
        self._mean_tooltip = self._param.get_sub_tooltip(DP.MEAN)
        self._std_tooltip = self._param.get_sub_tooltip(DP.STD)

        self._mu_tooltip = self._param.get_sub_tooltip(DP.MU)
        self._sigma_tooltip = self._param.get_sub_tooltip(DP.SIGMA)

        self._lower_tooltip = self._param.get_sub_tooltip(DP.LOWER)
        self._upper_tooltip = self._param.get_sub_tooltip(DP.UPPER)

        self._alpha_tooltip = self._param.get_sub_tooltip(DP.ALPHA)
        self._beta_tooltip = self._param.get_sub_tooltip(DP.BETA)

        # Emit signals to notify QML of tooltip changes
        self.nominalTooltipChanged.emit(self._nominal_tooltip)

        self.meanTooltipChanged.emit(self._mean_tooltip)
        self.stdTooltipChanged.emit(self._std_tooltip)

        self.muTooltipChanged.emit(self._mu_tooltip)
        self.sigmaTooltipChanged.emit(self._sigma_tooltip)

        self.lowerTooltipChanged.emit(self._lower_tooltip)
        self.upperTooltipChanged.emit(self._upper_tooltip)

        self.alphaTooltipChanged.emit(self._alpha_tooltip)
        self.betaTooltipChanged.emit(self._beta_tooltip)

    def _on_distribution_changed(self, field):
        """Handle distribution type change by updating all tooltips and emitting signal."""
        self._update_tooltips()
        self.inputTypeChanged.emit(self._param.distr)

    def _update_tooltip(self, param_name):
        """Update tooltip for a specific parameter."""
        tooltip = self._param.get_sub_tooltip(param_name)

        if param_name == DP.NOMINAL:
            self._nominal_tooltip = tooltip
            self.nominalTooltipChanged.emit(tooltip)
        elif param_name == DP.MEAN:
            self._mean_tooltip = tooltip
            self.meanTooltipChanged.emit(tooltip)
        elif param_name == DP.STD:
            self._std_tooltip = tooltip
            self.stdTooltipChanged.emit(tooltip)
        elif param_name == DP.MU:
            self._mu_tooltip = tooltip
            self.muTooltipChanged.emit(tooltip)
        elif param_name == DP.SIGMA:
            self._sigma_tooltip = tooltip
            self.sigmaTooltipChanged.emit(tooltip)
        elif param_name == DP.LOWER:
            self._lower_tooltip = tooltip
            self.lowerTooltipChanged.emit(tooltip)
        elif param_name == DP.UPPER:
            self._upper_tooltip = tooltip
            self.upperTooltipChanged.emit(tooltip)
        elif param_name == DP.ALPHA:
            self._alpha_tooltip = tooltip
            self.alphaTooltipChanged.emit(tooltip)
        elif param_name == DP.BETA:
            self._beta_tooltip = tooltip
            self.betaTooltipChanged.emit(tooltip)

    @Property(bool, constant=True)
    def use_nominal(self):
        return self._param.use_nominal

    @Property(bool)
    def show_nominal(self):
        return self.is_param_visible(DP.NOMINAL)

    @Property(bool, constant=True)
    def use_uncertainty_type(self):
        return self._param.use_uncertainty_type

    @Property(bool)
    def show_uncertainty_type(self):
        return self.use_uncertainty_type and self._param.is_probabilistic

    @Property(QObject, constant=True)
    def unit_choices(self):
        """QObject representing list of unit choices available. """
        return self._unit_choices

    @Property(QObject, constant=True)
    def distr_choices(self):
        """QObject representing list of unit choices available. """
        return self._distr_choices

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
        result = self._param.unit_choices_display[self._param.get_unit_index()]
        if result == 'fraction':
            result = '\u2013'
        return result

    @Property(str)
    def uncertainty_disp(self):
        """Display-ready representation of uncertainty. """
        val = ""
        if self.uncertainty == Uncertainties.ale:
            val = "aleatory"
        elif self.uncertainty == Uncertainties.epi:
            val = "epistemic"
        return val

    @Property(str)
    def uncertainty_plot(self):
        """Filepath of uncertainty plot, if any. """
        return self._param.uncertainty_plot

    # ==========================
    # PROPERTY GETTERS & SETTERS

    @Slot(str)
    def set_null(self, field:str):
        """Explicit function sets value to null because QML doesn't support passing different dtype value (null)."""
        if field in ['value', DP.NOMINAL]:
            self.set_value(None)
        elif field == DP.MEAN:
            self.mean = None
        elif field == DP.STD:
            self.std = None
        elif field == DP.MU:
            self.mu = None
        elif field == DP.SIGMA:
            self.sigma = None
        elif field == DP.LOWER:
            self.lower = None
        elif field == DP.UPPER:
            self.upper = None
        elif field == DP.ALPHA:
            self.alpha = None
        elif field == DP.BETA:
            self.beta = None
        else:
            raise ValueError(f"Invalid field name: {field}")

    def get_value(self):
        val = self._param.value
        if type(val) is float:
            val = round(val, 8)
        return val

    def set_value(self, val: float or None):
        self._param.value = val
        self.valueChanged.emit(val)

    def get_input_type(self):
        return self._param.distr

    def set_input_type(self, val):
        self._param.distr = val
        # self._param.set_distr_from_index(val_index)
        # self._param.distr = int(val_index)
        self.inputTypeChanged.emit(self._param.distr)

    @Slot(int)
    def set_input_type_from_index(self, val_index):
        self._param.set_distr_from_index(val_index)
        self.inputTypeChanged.emit(self._param.distr)

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

    def get_mean(self):
        return self._param.mean

    def set_mean(self, val: float):
        self._param.mean = val
        self.meanChanged.emit(val)

    def get_mu(self):
        return self._param.mu

    def set_mu(self, val: float):
        self._param.mu = val
        self.muChanged.emit(val)

    def get_std(self):
        return self._param.std

    def set_std(self, val: float):
        self._param.std = val
        self.stdChanged.emit(val)

    def get_sigma(self):
        return self._param.sigma

    def set_sigma(self, val: float):
        self._param.sigma = val
        self.sigmaChanged.emit(val)

    def get_lower(self):
        return self._param.lower

    def set_lower(self, val: float):
        self._param.lower = val
        self.lowerChanged.emit(val)

    def get_alpha(self):
        return self._param.alpha

    def set_alpha(self, val: float):
        self._param.alpha = val
        self.alphaChanged.emit(val)

    def get_beta(self):
        return self._param.beta

    def set_beta(self, val: float):
        self._param.beta = val
        self.betaChanged.emit(val)

    @Property(float or None, notify=upperChanged)
    def upper(self):
        return self._param.upper

    @upper.setter
    def upper(self, val: float or str or None):
        self._param.upper = val
        self.upperChanged.emit(self._param.upper if self._param.upper is not None else 0.0)

    @Property(bool, constant=True)
    def upper_is_null(self):
        return self._param.upper is None

    unit = Property(str, get_unit, set_unit, notify=unitChanged)
    input_type = Property(str, get_input_type, set_input_type, notify=inputTypeChanged)
    uncertainty = Property(str, get_uncertainty, set_uncertainty, notify=uncertaintyChanged)
    value = Property(float, get_value, set_value, notify=valueChanged)
    mean = Property(float, get_mean, set_mean, notify=meanChanged)
    mu = Property(float, get_mu, set_mu, notify=muChanged)
    std = Property(float, get_std, set_std, notify=stdChanged)
    sigma = Property(float, get_sigma, set_sigma, notify=sigmaChanged)
    lower = Property(float, get_lower, set_lower, notify=lowerChanged)
    alpha = Property(float, get_alpha, set_alpha, notify=alphaChanged)
    beta = Property(float, get_beta, set_beta, notify=betaChanged)

    # =================
    # UTILITY FUNCTIONS
    @Slot(result=int)
    def get_unit_index(self):
        """Returns index of active unit. """
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

    @Slot()
    def update_all_validation_states(self):
        self._param.update_all_validation_states()

    @Slot(str, result=bool)
    def is_param_visible(self, param_name:str) -> bool:
        """Check if a sub-parameter should be visible.

        Parameters
        ----------
        param_name : str
            Name of the sub-parameter to check

        Returns
        -------
        bool
            True if the parameter should be visible, False otherwise
        """
        return self._param.is_param_visible(param_name)

    # Properties for tooltip access from QML

    @Property(str, notify=nominalTooltipChanged)
    def nominal_tooltip(self):
        """Tooltip for the nominal value input."""
        return self._nominal_tooltip

    @Property(str, notify=meanTooltipChanged)
    def mean_tooltip(self):
        """Tooltip for the mean value input."""
        return self._mean_tooltip

    @Property(str, notify=muTooltipChanged)
    def mu_tooltip(self):
        """Tooltip for the mu value input."""
        return self._mu_tooltip

    @Property(str, notify=stdTooltipChanged)
    def std_tooltip(self):
        """Tooltip for the standard deviation input."""
        return self._std_tooltip

    @Property(str, notify=sigmaTooltipChanged)
    def sigma_tooltip(self):
        """Tooltip for the sigma value input."""
        return self._sigma_tooltip

    @Property(str, notify=lowerTooltipChanged)
    def lower_tooltip(self):
        """Tooltip for the lower bound input."""
        return self._lower_tooltip

    @Property(str, notify=upperTooltipChanged)
    def upper_tooltip(self):
        """Tooltip for the upper bound input."""
        return self._upper_tooltip

    @Property(str, notify=alphaTooltipChanged)
    def alpha_tooltip(self):
        """Tooltip for the alpha input."""
        return self._alpha_tooltip

    @Property(str, notify=betaTooltipChanged)
    def beta_tooltip(self):
        """Tooltip for the beta input."""
        return self._beta_tooltip
