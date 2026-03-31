"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import sys

import numpy as np

from ..utils.distributions import Distributions, Uncertainties, DistributionParam as DP
from ..utils.helpers import InputStatus, ValidationResponse, get_num_str, MathSymbol
from ..utils.events import Event
from ..utils.units_of_measurement import Temperature
from ..models.fields import NumField



class UncertainField(NumField):
    """
    Analysis parameter described by float value, unit of measurement, and possibly distribution parameters.
    Sub-parameters are used as follows:
        Normal: mean, standard deviation
        Lognormal: mu, sigma
        Truncated normal: mean, standard deviation, lower bound, upper bound
        Truncated lognormal: mu, sigma, lower bound, upper bound
        Uniform: lower bound, upper bound

    Erroneous sub-parameter values are handled in one of two ways:
        If they are completely invalid, like a negative standard deviation or a value outside the min/max range, they're ignored.
        If they're valid but incompatible with other sub-parameters, like a lower bound above an upper bound, then the incoming
        value is accepted but the parameter enters an error state (fails validation). This should be shown to the user.

    Attributes
    ----------
    distr
    uncertainty : str or None
    use_nominal : bool
        Whether a nominal value shall be displayed and used
    use_uncertainty_type : bool
        Whether the uncertainty type (aleatory, epistemic) shall be displayed and used
    mean : float
        Mean for normal distributions.
    std : float
        Standard deviation for normal distributions.
    mu : float
        Mu parameter for lognormal distributions.
    sigma : float
        Sigma parameter for lognormal distributions.
    lower: float
        Lower bound for uniform, truncated normal, and truncated lognormal distributions.
    upper: float or None
        Optional upper bound for uniform, truncated normal, and truncated lognormal distributions.
    alpha : float
        Parameter for beta distribution.
    beta : float
        Parameter for beta distribution.
    str_display
    uncertainty_plot : str
        Plot of parameter uncertainty distribution, if applicable, from analysis post-processing.

    distrChanged : Event
        Event emitted when parameter input type/distribution is changed.
    uncertaintyChanged : Event
        Event emitted when parameter uncertainty is changed.
    subparam_validation_changed : Event
        Event emitted when a sub-parameter's validation state changes.

    Notes
    -----
    All values, including `min_value`, `max_value`, and distribution params `a` and `b`, are stored in standard units; e.g., meters.

    """
    _uncertainty: str or None
    _dtype = float
    _value: float

    # Probabilistic parameters stored as raw values (standard units) internally
    _distr: str
    _alpha: float
    _beta: float
    _mean: float
    _mu: float
    _std: float
    _sigma: float
    _lower: float
    _upper: float or None
    # Store read-only default values for later use (e.g., loading from file and none given)
    _defaults: dict

    # Restrict available distribution types by specifying allowed keys
    _valid_distributions = Distributions.keys

    use_nominal: bool = True
    use_uncertainty_type: bool = True
    a: float
    b: float
    mean: float
    mu: float
    std: float
    sigma: float
    lower: float
    upper: float or None

    uncertainty_plot: str = ""  # only set in app.py during analysis post-processing

    # Keep these instance-only to avoid cross-instance event pollution
    subparam_validation_changed: Event
    distr_changed: Event
    uncertainty_changed: Event

    def __init__(self, label, value, slug='', unit_type=None, unit=None,
                 distr=Distributions.det, uncertainty=Uncertainties.ale,
                 mean=0, std=1,
                 mu=0, sigma=1,
                 lower=-np.inf, upper=None,
                 alpha=0.1, beta=0.1,
                 min_value=0, max_value=np.inf,
                 use_nominal=True,
                 use_uncertainty_type=True,
                 tooltip=None, label_rtf=None,
                 tooltip_nominal="Nominal value of the parameter",
                 tooltip_mean="Mean value of the distribution",
                 tooltip_std="Standard deviation of the distribution",
                 tooltip_mu=f"{MathSymbol.MU} of the distribution",
                 tooltip_sigma=f"{MathSymbol.SIGMA} of the distribution",
                 tooltip_lower="Lower bound of the distribution",
                 tooltip_upper="Upper bound of the distribution",
                 tooltip_alpha="Alpha of the distribution",
                 tooltip_beta="Beta of the distribution",
                 unit_choices=None):

        if max_value is None:
            max_value = np.inf
        if min_value is None:
            min_value = -np.inf

        super().__init__(label=label, slug=slug, value=value, label_rtf=label_rtf, tooltip=tooltip,
                         min_value=min_value, max_value=max_value,
                         unit_type=unit_type, unit=unit, unit_choices=unit_choices)
        self._distr = distr
        self._uncertainty = uncertainty

        self.use_nominal = use_nominal
        self.use_uncertainty_type = use_uncertainty_type
        self._mean = 0
        self._mu = 0
        self._std = 1  # must be > 0
        self._sigma = 1  # must be > 0
        self._lower = 0
        self._upper = 0
        self._alpha = 0
        self._beta = 0
        
        self._mean = self.unit_type.convert(mean, old=self.unit)
        self._lower = self.unit_type.convert(lower, old=self.unit)
        self._upper = None if upper is None else self.unit_type.convert(upper, old=self.unit)
        # Alpha and beta are dimensionless shape parameters - no unit conversion
        self._alpha = float(alpha)
        self._beta = float(beta)

        # mu and sigma are converted differently because they're based on ln(X)
        self._mu = self.unit_type.convert_mu(mu, old=self.unit)
        self._sigma = sigma

        # std is a difference value, so use convert_difference (no offset for temperature)
        self._std = self.unit_type.convert_difference(std, old=self.unit)

        # Instance-only events to avoid cross-instance pollution when form fields subscribe
        self.subparam_validation_changed = Event()
        self.distr_changed = Event()
        self.uncertainty_changed = Event()

        # Store sub-parameter tooltips
        self._sub_tooltips = {
            DP.NOMINAL: tooltip_nominal,
            DP.MEAN: tooltip_mean,
            DP.STD: tooltip_std,
            DP.MU: tooltip_mu,
            DP.SIGMA: tooltip_sigma,
            DP.LOWER: tooltip_lower,
            DP.UPPER: tooltip_upper,
            DP.ALPHA: tooltip_alpha,
            DP.BETA: tooltip_beta
        }
        
        # store validation state for each sub-parameter
        self._validation_states = {
            DP.NOMINAL: ValidationResponse(InputStatus.GOOD, ""),
            DP.MEAN: ValidationResponse(InputStatus.GOOD, ""),
            DP.STD: ValidationResponse(InputStatus.GOOD, ""),
            DP.MU: ValidationResponse(InputStatus.GOOD, ""),
            DP.SIGMA: ValidationResponse(InputStatus.GOOD, ""),
            DP.LOWER: ValidationResponse(InputStatus.GOOD, ""),
            DP.UPPER: ValidationResponse(InputStatus.GOOD, ""),
            DP.ALPHA: ValidationResponse(InputStatus.GOOD, ""),
            DP.BETA: ValidationResponse(InputStatus.GOOD, "")
        }

        # Set read-only values for reference
        self._defaults = {
            DP.NOMINAL: self._value,
            DP.MEAN: self._mean,
            DP.STD: self._std,
            DP.MU: self._mu,
            DP.SIGMA: self._sigma,
            DP.LOWER: self._lower,
            DP.UPPER: self._upper,
            DP.ALPHA: self._alpha,
            DP.BETA: self._beta
        }
        
        self.update_all_validation_states()

    @property
    def distr(self) -> str:
        return self._distr

    @property
    def is_probabilistic(self) -> bool:
        return self._distr != Distributions.det

    def set_distr_from_index(self, index):
        if index < len(self._valid_distributions):
            new_distr = self._valid_distributions[index]
            self.distr = new_distr
        else:
            raise ValueError(f"Index {index} out of range for valid distributions: {self._valid_distributions}")

    @distr.setter
    def distr(self, val: str):
        """Override to update validation states on distribution change"""
        if val in Distributions and val in self._valid_distributions:
            self._distr = val
            
            # Clear all validation states for fresh start with new distribution
            for param in self._validation_states:
                self._validation_states[param] = ValidationResponse(InputStatus.GOOD, "")
            
            self.update_all_validation_states()
            
            # Emit signals
            self.distr_changed.notify(self)
            self.changed.notify(self)
        else:
            raise ValueError(f"Distribution {val} not a valid option")

    @property
    def is_normal(self):
        """Whether parameter using a normal or lognormal distribution. """
        return self._distr in [Distributions.nor, Distributions.log, Distributions.tnor, Distributions.tlog]

    @property
    def is_scale_unit(self):
        """Whether parameter is using scale-based units such as temperature. """
        return self.unit_type in [Temperature]

    def set_values_ignore_lims(self, val: float, **kwargs):
        """ Sets values while ignoring min and max limits. e.g. When units changed. 
        
        Parameters
        ----------
        val : float
            Nominal value
        **kwargs
            Distribution-specific parameters with str keys: mean, mu, std, sigma, lower, upper
        """
        new_value = self.unit_type.convert(val, old=self.unit)
        self._value = self._dtype(new_value)

        if self._distr in [Distributions.nor, Distributions.tnor]:
            if DP.MEAN in kwargs:
                self._mean = self._dtype(self.unit_type.convert(kwargs[DP.MEAN], old=self.unit))
            if DP.STD in kwargs:
                # std is a difference value, use convert_difference (no offset for temperature)
                self._std = self._dtype(self.unit_type.convert_difference(kwargs[DP.STD], old=self.unit))

        elif self._distr in [Distributions.log, Distributions.tlog]:
            if DP.MU in kwargs:
                self._mu = self._dtype(self.unit_type.convert(kwargs[DP.MU], old=self.unit))
            if DP.SIGMA in kwargs:
                self._sigma = self._dtype(self.unit_type.convert(kwargs[DP.SIGMA], old=self.unit))

        elif self._distr == Distributions.beta:
            # Alpha and beta are dimensionless shape parameters - no unit conversion
            if DP.ALPHA in kwargs:
                self._alpha = self._dtype(kwargs[DP.ALPHA])
            if DP.BETA in kwargs:
                self._beta = self._dtype(kwargs[DP.BETA])
        
        # Handle bounds for all distributions that use them
        if self._distr in [Distributions.uni, Distributions.tnor, Distributions.tlog]:
            if DP.LOWER in kwargs:
                self._lower = self._dtype(self.unit_type.convert(kwargs[DP.LOWER], old=self.unit))
            if DP.UPPER in kwargs:
                upper_val = kwargs.get(DP.UPPER)
                self._upper = None if upper_val is None else self._dtype(self.unit_type.convert(upper_val, old=self.unit))

        if self._track_changes:
            self.changed.notify(self)


    # ====== DESCRIPTIVE PROPERTIES ======
    @property
    def mean(self) -> float:
        """Mean value for normal distributions, in selected units."""
        return self.unit_type.convert(self._mean, new=self.unit)

    @mean.setter
    def mean(self, val: float):
        """Sets mean value for normal distributions."""
        nv = self.unit_type.convert(val, old=self.unit)
        if self._min_value <= nv <= self._max_value:
            self._mean = self._dtype(nv)
            self.update_all_validation_states()
            if self._track_changes:
                self.changed.notify(self)

    @property
    def mean_str(self) -> str:
        """Mean value formatted for display, in selected units."""
        return get_num_str(self.mean)
    
    @property
    def std(self):
        """Standard deviation for normal distributions, in selected units."""
        # std is a difference value, use convert_difference (no offset for temperature)
        return self.unit_type.convert_difference(self._std, new=self.unit)

    @std.setter
    def std(self, val: float):
        """Sets standard deviation for normal distributions in selected units (must be > 0)."""
        # std is a difference value, use convert_difference (no offset for temperature)
        nv = self.unit_type.convert_difference(val, old=self.unit)
        self._std = self._dtype(nv)
        self.update_all_validation_states()
        if self._track_changes:
            self.changed.notify(self)

    @property
    def std_str(self):
        """Standard deviation formatted for display, in selected units."""
        return get_num_str(self.std)

    @property
    def mu(self) -> float:
        """Mu parameter for lognormal distributions, in selected units."""
        return self.unit_type.convert_mu(self._mu, new=self.unit)

    @mu.setter
    def mu(self, val: float):
        """Sets mu parameter for lognormal distributions.

        Mu is the mean of the underlying normal distribution in log-space (mean of ln(X)).
        It can be any real number since exp(mu) transforms it to the actual distribution.
        No bounds checking is applied - mu is not constrained by min_value/max_value.
        """
        nv = self.unit_type.convert_mu(val, old=self.unit)
        self._mu = self._dtype(nv)
        self.update_all_validation_states()
        if self._track_changes:
            self.changed.notify(self)

    @property
    def mu_str(self) -> str:
        """Mu value formatted for display, in selected units."""
        return get_num_str(self.mu)

    @property
    def sigma(self):
        """
        Sigma parameter for lognormal distributions in selected units.
        Note sigma remains constant because it's based on natural log of the random value.
        """
        # return self.unit_type.convert(self._sigma, new=self.unit)
        return self._sigma

    @sigma.setter
    def sigma(self, val: float):
        """Sets sigma parameter for lognormal distributions (must be > 0)."""
        self._sigma = self._dtype(val)
        self.update_all_validation_states()
        if self._track_changes:
            self.changed.notify(self)

    @property
    def sigma_str(self):
        """Sigma value formatted for display, in selected units."""
        return get_num_str(self.sigma)
    
    @property
    def lower(self):
        """Lower bound for uniform and truncated distributions, in selected units."""
        return self.unit_type.convert(self._lower, new=self.unit)

    @lower.setter
    def lower(self, val: float):
        """Sets lower bound for uniform and truncated distributions, in selected units."""
        nv = self.unit_type.convert(val, old=self.unit)
        if self._min_value <= nv <= self._max_value:
            self._lower = self._dtype(nv)
            self.update_all_validation_states()
            if self._track_changes:
                self.changed.notify(self)

    @property
    def lower_str(self):
        """Lower bound formatted for display, in selected units."""
        return get_num_str(self.lower)
    
    @property
    def upper(self):
        """Upper bound for uniform and truncated distributions, in selected units."""
        return None if self._upper is None else self.unit_type.convert(self._upper, new=self.unit)

    @upper.setter
    def upper(self, val: float or None):
        """Sets upper bound for uniform and truncated distributions, in selected units."""
        if val is None:
            self._upper = None
        else:
            nv = self.unit_type.convert(val, old=self.unit)
            if self._min_value <= nv <= self._max_value:
                self._upper = self._dtype(nv)
        self.update_all_validation_states()
        if self._track_changes:
            self.changed.notify(self)

    @property
    def upper_str(self):
        """Upper bound formatted for display, in selected units."""
        return get_num_str(self.upper)

    @property
    def alpha(self) -> float:
        """Alpha shape parameter for beta distributions (dimensionless, must be > 0)."""
        return self._alpha

    @alpha.setter
    def alpha(self, val: float):
        """Sets alpha shape parameter for beta distributions (must be positive)."""
        if val <= 0:
            return  # Reject non-positive values
        self._alpha = self._dtype(val)
        self.update_all_validation_states()
        if self._track_changes:
            self.changed.notify(self)

    @property
    def alpha_str(self) -> str:
        """Alpha value formatted for display."""
        return get_num_str(self.alpha)

    @property
    def beta(self) -> float:
        """Beta shape parameter for beta distributions (dimensionless, must be > 0)."""
        return self._beta

    @beta.setter
    def beta(self, val: float):
        """Sets beta shape parameter for beta distributions (must be positive)."""
        if val <= 0:
            return  # Reject non-positive values
        self._beta = self._dtype(val)
        self.update_all_validation_states()
        if self._track_changes:
            self.changed.notify(self)

    @property
    def beta_str(self) -> str:
        """Beta value formatted for display."""
        return get_num_str(self.beta)


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
            self.uncertainty_changed.notify(self)
            self.changed.notify(self)
        else:
            raise ValueError(f"Uncertainty {val} not found")

    @property
    def str_display(self):
        """ Returns string-representation of parameter, including label.

        Notes
        -----
        May throw UnicodeEncodeError on windows when attempting to print to console in development. (Windows console can't handle unicode chars.)
        Use str_display_dev instead.
        """
        result = ""
        if self.unit is None:
            unit_str = ""
        else:
            disp_unit_index = self.get_unit_index()
            unit_str = self._display_units[disp_unit_index]
        val = self.value_str

        if self._distr == Distributions.det:
            result = f"{self.label}: {val} {unit_str}"

        elif self._distr == Distributions.nor:
            result = f"{self.label}: Normal ({val} {unit_str}, Mean {self.mean}, Std {self.std})"

        elif self._distr == Distributions.log:
            result = f"{self.label}: Lognormal ({val} {unit_str}, {MathSymbol.MU} {self.mu}, {MathSymbol.SIGMA} {self.sigma})"

        elif self._distr in Distributions.tnor:
            ustr = "inf" if self.upper is None else str(self.upper)
            result = f"{self.label}: Truncated Normal ({val} {unit_str}, Mean {self.mean}, Std {self.std}, bounds [{self.lower}, {ustr}])"

        elif self._distr in Distributions.tlog:
            ustr = "inf" if self.upper is None else str(self.upper)
            result = (f"{self.label}: Truncated Lognormal ({val} {unit_str}, {MathSymbol.MU} {self.mu}, {MathSymbol.SIGMA} {self.sigma}, "
                      f"bounds [{self.lower}, {ustr}])")

        elif self._distr == Distributions.uni:
            ustr = "inf" if self.upper is None else str(self.upper)
            result = f"{self.label}: Uniform ({val} {unit_str}, {self.lower} to {ustr})"

        elif self._distr == Distributions.beta:
            result = f"{self.label}: Beta ({val} {unit_str}, {MathSymbol.ALPHA} {self.alpha}, {MathSymbol.BETA} {self.beta})"

        return result

    @property
    def str_display_dev(self):
        """ Returns string-representation of parameter, including label, without unicode.
        """
        result = ""
        if self.unit is None:
            unit_str = ""
        else:
            disp_unit_index = self.get_unit_index()
            unit_str = self._display_units[disp_unit_index]
        val = self.value_str

        if self._distr == Distributions.det:
            result = f"{self.label}: {val} {unit_str}"

        elif self._distr == Distributions.nor:
            result = f"{self.label}: Normal ({val} {unit_str}, mean {self.mean}, std {self.std})"

        elif self._distr == Distributions.log:
            result = f"{self.label}: Lognormal ({val} {unit_str}, mu {self.mu}, sigma {self.sigma})"

        elif self._distr in Distributions.tnor:
            ustr = "inf" if self.upper is None else str(self.upper)
            result = (f"{self.label}: Truncated Normal ({val} {unit_str}, mean {self.mean}, std {self.std}, "
                      f"bounds [{self.lower}, {ustr}])")

        elif self._distr in Distributions.tlog:
            ustr = "inf" if self.upper is None else str(self.upper)
            result = (f"{self.label}: Truncated Lognormal ({val} {unit_str}, mu {self.mu}, sigma {self.sigma}, "
                      f"bounds [{self.lower}, {ustr}])")

        elif self._distr == Distributions.uni:
            ustr = "inf" if self.upper is None else str(self.upper)
            result = f"{self.label}: Uniform ({val} {unit_str}, {self.lower} to {ustr})"

        elif self._distr == Distributions.beta:
            result = f"{self.label}: Beta ({val} {unit_str}, alpha {self.alpha}, beta {self.beta})"

        return result


    def set_unit_from_display(self, val: str):
        """ Sets active unit from a selected display value, not key. e.g. 'MPa' updates unit type to 'mpa' """
        disp_units = self._display_units
        if len(disp_units) <= 1:
            return
        if val not in disp_units:
            raise ValueError('Display unit not found')

        # Store old values based on distribution type
        old_param_val = self.value
        old_values = {}
        
        if self._distr in [Distributions.nor, Distributions.tnor]:
            old_values[DP.MEAN] = self.mean
            old_values[DP.STD] = self.std
        elif self._distr in [Distributions.log, Distributions.tlog]:
            old_values[DP.MU] = self.mu
            old_values[DP.SIGMA] = self.sigma
        elif self._distr in [Distributions.beta]:
            old_values[DP.ALPHA] = self.alpha
            old_values[DP.BETA] = self.beta
        
        if self._distr in [Distributions.uni, Distributions.tnor, Distributions.tlog]:
            old_values[DP.LOWER] = self.lower
            old_values[DP.UPPER] = self.upper

        i = disp_units.index(val)
        self.unit = self._unit_choices[i]

        # displayed value now in new units so update raw values in batch to yield single change event
        tracking = self._track_changes
        self._track_changes = False
        self.set_values_ignore_lims(old_param_val, **old_values)
        self._track_changes = tracking
        self.changed.notify(self)
        
        self.update_all_validation_states()

    def get_distr_index(self) -> int:
        """Returns index of selected distribution. """
        result = self._valid_distributions.index(self._distr)
        return result

    def get_uncertainty_index(self) -> int:
        """Returns index of selected uncertainty option. """
        result = Uncertainties.index(self._uncertainty)
        return result
        
    def update_all_validation_states(self):
        """Update validation state for all sub-parameters"""
        self._update_validation_state(DP.NOMINAL, self._value)
        self._update_validation_state(DP.MEAN, self._mean)
        self._update_validation_state(DP.STD, self._std)
        self._update_validation_state(DP.LOWER, self._lower)
        self._update_validation_state(DP.UPPER, self._upper)
        self._update_validation_state(DP.MU, self._mu)
        self._update_validation_state(DP.SIGMA, self._sigma)
        self._update_validation_state(DP.ALPHA, self._alpha)
        self._update_validation_state(DP.BETA, self._beta)

    def _update_validation_state(self, param_name, value):
        """Update validation state for a specific parameter"""
        result = ValidationResponse(InputStatus.GOOD, "")
        if self.is_param_visible(param_name):
            result = self.validate_subparam_incoming_value(param_name, value)

        # Validate and store result
        self._validation_states[param_name] = result

        # Emit signal with updated validation state
        self._emit_validation_state(param_name, result)

    def _emit_validation_state(self, param_name:str, response:ValidationResponse):
        """Emit validation state signal for UI display"""
        status = response.status
        message = response.message
        
        # Emit signal with the consistent parameter name string
        self.subparam_validation_changed.notify(self, param_name, status, message)

    def get_validation_state(self, param_name: str = None) -> ValidationResponse:
        """Get validation state for a parameter or overall state
        
        Parameters
        ----------
        param_name : str, optional
            Distribution parameter to get validation for. If None, returns worst validation state.
            
        Returns
        -------
        ValidationResponse
            Validation response for the parameter or worst response
        """
        if param_name is not None:
            self.update_all_validation_states()
            return self._validation_states.get(param_name, ValidationResponse(InputStatus.GOOD, ""))
                   
        # Return worst validation state if no specific parameter requested
        for param in [DP.NOMINAL, DP.MEAN, DP.STD, DP.MU, DP.SIGMA, DP.LOWER, DP.UPPER, DP.ALPHA, DP.BETA]:
            state = self._validation_states.get(param)
            if state and state.status == InputStatus.ERROR:
                return state
                
        # All valid
        return ValidationResponse(InputStatus.GOOD, "")

    # Override the NumField value property to add validation
    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, val):
        # Call original implementation to set the value, and validate
        super(UncertainField, self.__class__).value.fset(self, val)
        self.update_all_validation_states()

    def is_param_visible(self, param_name:str) -> bool:
        """Determine if a sub-parameter should be visible.

        Parameters
        ----------
        param_name : str
            String name of the sub-parameter; e.g. 'mean' for the mean of a distribution.

        Returns
        -------
        bool
            True if sub-parameter should be visible, False otherwise
        """
        result = False

        if self.use_nominal and param_name == DP.NOMINAL:
            return True

        if self.distr  == Distributions.nor:
            result = param_name in [DP.MEAN, DP.STD]

        elif self.distr == Distributions.tnor:
            result = param_name in [DP.MEAN, DP.STD, DP.LOWER, DP.UPPER]

        elif self.distr == Distributions.log:
            result = param_name in [DP.MU, DP.SIGMA]

        elif self.distr == Distributions.tlog:
            result = param_name in [DP.MU, DP.SIGMA, DP.LOWER, DP.UPPER]

        elif self.distr == Distributions.uni:
            result = param_name in [DP.LOWER, DP.UPPER]

        elif self.distr == Distributions.beta:
            result = param_name in [DP.ALPHA, DP.BETA]

        return result


    def get_sub_tooltip(self, param_name:str, include_validation=True):
        """Get tooltip for a specific sub-parameter with validation context.
        Recall that:
            Normal: mean, standard deviation
            Lognormal: mu, sigma
            Truncated normal: mean, standard deviation, lower bound, upper bound
            Truncated lognormal: mu, sigma, lower bound, upper bound
            Uniform: lower bound, upper bound

        Parameters
        ----------
        param_name : str
            Name of sub-parameter
        include_validation : bool, optional
            Whether to include validation-related context, by default True

        Returns
        -------
        str
            Tooltip text with validation context if requested
        """
        base_tooltip = self._sub_tooltips.get(param_name, "")

        # Add unit information where appropriate
        if hasattr(self, 'unit') and self.unit:
            unit_disp = self.unit_choices_display[self.get_unit_index()]
            if unit_disp != 'fraction':
                unit_str = f" ({unit_disp})"
                if base_tooltip and not base_tooltip.endswith(unit_str):
                    base_tooltip += unit_str

        if not include_validation:
            return base_tooltip

        # Add validation context based on parameter and distribution
        context = ""

        # --- Distribution-specific validation. This could be simplified but leaving it explicit for clarity. ---
        if self.distr == Distributions.nor:
            if param_name == DP.NOMINAL and self.use_nominal or param_name == DP.MEAN:
                if self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"
                if self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"

            elif param_name == DP.STD:
                context += "\nMust be positive (> 0)"

        elif self.distr == Distributions.log:
            if param_name == DP.NOMINAL and self.use_nominal:
                if self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"
                if self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"
            # MU is in log-space and can be any real number - no bounds constraints

            elif param_name == DP.SIGMA:
                context += "\nMust be positive (> 0)"

        elif self.distr == Distributions.tnor:
            if param_name == DP.NOMINAL and self.use_nominal or param_name == DP.MEAN:
                if self._lower not in [None, -np.inf]:
                    context += f"\nMust be ≥ lower bound {self.lower_str}"
                elif self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"
                if self._upper not in [None, np.inf]:
                    context += f"\nMust be ≤ upper bound {self.upper_str}"
                elif self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"

            elif param_name == DP.STD:
                context += "\nMust be positive (> 0)"

        elif self.distr == Distributions.tlog:
            if param_name == DP.NOMINAL and self.use_nominal:
                if self._lower not in [None, -np.inf]:
                    context += f"\nMust be ≥ lower bound {self.lower_str}"
                elif self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"
                if self._upper not in [None, np.inf]:
                    context += f"\nMust be ≤ upper bound {self.upper_str}"
                elif self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"
            # MU is in log-space and can be any real number - no bounds constraints

            elif param_name == DP.SIGMA:
                context += "\nMust be positive (> 0)"

        elif self.distr == Distributions.uni:
            # Uniform distribution uses nominal, lower, upper
            if param_name == DP.NOMINAL and self.use_nominal:
                if self._lower not in [None, -np.inf]:
                    context += f"\nMust be ≥ lower bound {self.lower_str}"
                elif self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"
                if self._upper not in [None, np.inf]:
                    context += f"\nMust be ≤ upper bound {self.upper_str}"
                elif self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"

        elif self.distr == Distributions.beta:
            # Beta distribution uses nominal, alpha, beta
            if param_name == DP.NOMINAL and self.use_nominal:
                if self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"
                if self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"
            elif param_name in [DP.ALPHA, DP.BETA]:
                # Alpha/beta are dimensionless shape parameters, must be strictly positive
                context += f"\nMust be positive (> 0)"

        if self.distr in [Distributions.tnor, Distributions.tlog, Distributions.uni]:
            if param_name == DP.LOWER:
                # assume nominal value will be set after this so don't need to validate it against nominal
                if self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"

                if self._upper not in [None, np.inf]:
                    context += f"\nMust be ≤ upper bound {self.upper_str}"
                elif self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"

            elif param_name == DP.UPPER:
                if self._lower not in [None, -np.inf]:
                    context += f"\nMust be ≥ lower bound {self.lower_str}"
                elif self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"

                if self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"

        else:
            # Deterministic
            if param_name == DP.NOMINAL:
                if self._min_value != -np.inf:
                    context += f"\nMust be ≥ {self.min_value_str}"
                if self._max_value != np.inf:
                    context += f"\nMust be ≤ {self.max_value_str}"

        full_tooltip = base_tooltip + context
        return full_tooltip

    def validate_subparam_incoming_value(self, param_name:str, value) -> ValidationResponse:
        """Validate a potential raw value for a sub-parameter.

        Parameters
        ----------
        param_name : str
            name of sub-parameter for which value is applicable.
        value : float or str or None
            Value to validate; assumed to be in standard units.

        Returns
        -------
        ValidationResponse
            Validation result with status and message
        """
        # Convert input to float for validation
        try:
            if value in [None, ""]:
                val = None
                val_str = "infinity"
            else:
                val = float(value)
                val_converted = self.unit_type.convert(val, old=self.unit)
                val_str = get_num_str(val_converted)
        except (ValueError, TypeError):
            return ValidationResponse(InputStatus.ERROR, "Sub-parameter value must be a valid number or None")

        # --- Distribution-specific validation ---
        # Keeping this verbose to make it easier to add new distributions in the future
        msg = ""
        if self.distr == Distributions.nor:
            if param_name == DP.NOMINAL and self.use_nominal:
                if val < self.min_value:
                    msg = f'Nominal value below minimum ({val_str} < {self.min_value_str})'
                elif val > self.max_value:
                    msg = f'Nominal value above maximum ({val_str} > {self.max_value_str})'

            elif param_name == DP.MEAN:
                if val < self.min_value:
                    msg = f'Mean below minimum ({val_str} < {self.min_value_str})'
                elif val > self.max_value:
                    msg = f'Mean above maximum ({val_str} > {self.max_value_str})'

            elif param_name == DP.STD:
                if val <= 0:
                    msg = f'Standard deviation must be positive (> 0)'

        elif self.distr == Distributions.log:
            if param_name == DP.NOMINAL and self.use_nominal:
                if val < self.min_value:
                    msg = f'Nominal value below minimum ({val_str} < {self.min_value_str})'
                elif val > self.max_value:
                    msg = f'Nominal value above maximum ({val_str} > {self.max_value_str})'

            elif param_name == DP.MU:
                # Mu is the mean of the underlying normal distribution in log-space (mean of ln(X)).
                # It should not be compared to min/max bounds, which apply to the parameter value X.
                # Mu can be any real number since exp(mu) transforms it to the actual distribution.
                pass

            elif param_name == DP.SIGMA:
                # Sigma must be strictly positive for lognormal distributions
                if val <= 0:
                    msg = f'{MathSymbol.SIGMA} must be positive (> 0)'

        elif self.distr == Distributions.tnor:
            if param_name == DP.NOMINAL and self.use_nominal:
                if self._lower is not None and val < self._lower:
                    msg = f'Nominal value below lower bound ({val_str} < {self.lower_str})'
                elif val < self._min_value:
                    msg = f'Nominal value below minimum ({val_str} < {self.min_value_str})'
                if self._upper is not None and val > self._upper:
                    msg = f'Nominal value above upper bound ({val_str} > {self.upper_str})'
                elif val > self._max_value:
                    msg = f'Nominal value above maximum ({val_str} > {self.max_value_str})'

            if param_name == DP.MEAN:
                if self._lower is not None and val < self._lower:
                    msg = f'Mean below lower bound ({val_str} < {self.lower_str})'
                elif val < self._min_value:
                    msg = f'Mean below minimum ({val_str} < {self.min_value_str})'
                if self._upper is not None and val > self._upper:
                    msg = f'Mean above upper bound ({val_str} > {self.upper_str})'
                elif val > self._max_value:
                    msg = f'Mean above maximum ({val_str} > {self.max_value_str})'

            elif param_name == DP.STD:
                if val <= 0:
                    msg = f'Standard deviation must be positive (> 0)'

        elif self.distr == Distributions.tlog:
            if param_name == DP.NOMINAL and self.use_nominal:
                if self._lower is not None and val < self._lower:
                    msg = f'Nominal value below lower bound ({val_str} < {self.lower_str})'
                elif val < self._min_value:
                    msg = f'Nominal value below minimum ({val_str} < {self.min_value_str})'
                if self._upper is not None and val > self._upper:
                    msg = f'Nominal value above upper bound ({val_str} > {self.upper_str})'
                elif val > self._max_value:
                    msg = f'Nominal value above maximum ({val_str} > {self.max_value_str})'

            elif param_name == DP.MU:
                pass

            elif param_name == DP.SIGMA:
                # Sigma must be strictly positive for truncated lognormal distributions
                if val <= 0:
                    msg = f'{MathSymbol.SIGMA} must be positive (> 0)'

        elif self.distr == Distributions.uni:
            # Uniform distribution uses nominal, lower, upper
            if param_name == DP.NOMINAL and self.use_nominal:
                if self._lower is not None and val < self._lower:
                    msg = f'Nominal value below lower bound ({val_str} < {self.lower_str})'
                elif val < self._min_value:
                    msg = f'Nominal value below minimum ({val_str} < {self.min_value_str})'
                if self._upper is not None and val > self._upper:
                    msg = f'Nominal value above upper bound ({val_str} > {self.upper_str})'
                elif val > self._max_value:
                    msg = f'Nominal value above maximum ({val_str} > {self.max_value_str})'

        elif self.distr == Distributions.beta:
            if param_name == DP.NOMINAL and self.use_nominal:
                if val < self.min_value:
                    msg = f'Nominal value below minimum ({val_str} < {self.min_value_str})'
                elif val > self.max_value:
                    msg = f'Nominal value above maximum ({val_str} > {self.max_value_str})'
            elif param_name == DP.ALPHA:
                # Alpha is a dimensionless shape parameter, must be strictly positive
                if val <= 0:
                    msg = f'Alpha must be positive (> 0)'
            elif param_name == DP.BETA:
                if val <= 0:
                    msg = f'Beta must be positive (> 0)'

        if self.distr in [Distributions.tnor, Distributions.tlog, Distributions.uni]:
            if param_name == DP.LOWER:
                if val < self._min_value:
                    msg = f'Lower bound is below minimum ({val_str} < {self.min_value_str})'
                if self._upper is not None and val > self._upper:
                    msg = f'Lower bound is above upper bound ({val_str} > {self.upper_str})'
                elif val > self._max_value:
                    msg = f'Lower bound is above maximum ({val_str} > {self.max_value_str})'

            elif param_name == DP.UPPER:
                # check against max value
                if val is None:
                    if self._max_value != np.inf:
                        msg = f'Upper bound must be below maximum ({self.max_value_str})'
                    else:
                        # upper bound is blank (infinity) and max value is infinity
                        pass
                elif val > self._max_value:
                    msg = f'Upper bound is above maximum ({val_str} > {self.max_value_str})'

                # check against lower bound
                if val is None:
                    pass
                elif self._lower is not None and val < self._lower:
                    msg = f'Upper bound is below lower bound ({val_str} < {self.lower_str})'
                elif val < self._min_value:
                    msg = f'Upper bound is below minimum ({val_str} < {self.min_value_str})'

        else:
            # Deterministic
            if param_name == DP.NOMINAL and self.use_nominal:
                if val is None:
                    msg = f'Value cannot be blank - enter a valid number'
                elif val < self._min_value:
                    msg = f'Value below minimum ({val_str} < {self.min_value_str})'
                elif val > self._max_value:
                    msg = f'Value above maximum ({val_str} > {self.max_value_str})'

        status = InputStatus.ERROR if msg else InputStatus.GOOD
        return ValidationResponse(status, msg)

    def check_valid(self) -> ValidationResponse:
        resp = super().check_valid()
        if resp.status != InputStatus.GOOD:
            return resp

        responses = []
        if self.use_nominal:
            responses.append(self.validate_subparam_incoming_value(DP.NOMINAL, self._value))

        if self.distr == Distributions.nor:
            responses.append(self.validate_subparam_incoming_value(DP.MEAN, self._mean))
            responses.append(self.validate_subparam_incoming_value(DP.STD, self._std))

        elif self.distr == Distributions.log:
            responses.append(self.validate_subparam_incoming_value(DP.MU, self._mu))
            responses.append(self.validate_subparam_incoming_value(DP.SIGMA, self._sigma))

        elif self.distr == Distributions.tnor:
            responses.append(self.validate_subparam_incoming_value(DP.MEAN, self._mean))
            responses.append(self.validate_subparam_incoming_value(DP.STD, self._std))
            responses.append(self.validate_subparam_incoming_value(DP.LOWER, self._lower))
            responses.append(self.validate_subparam_incoming_value(DP.UPPER, self._upper))

        elif self.distr == Distributions.tlog:
            responses.append(self.validate_subparam_incoming_value(DP.MU, self._mu))
            responses.append(self.validate_subparam_incoming_value(DP.SIGMA, self._sigma))
            responses.append(self.validate_subparam_incoming_value(DP.LOWER, self._lower))
            responses.append(self.validate_subparam_incoming_value(DP.UPPER, self._upper))

        elif self.distr == Distributions.uni:
            responses.append(self.validate_subparam_incoming_value(DP.LOWER, self._lower))
            responses.append(self.validate_subparam_incoming_value(DP.UPPER, self._upper))

        elif self.distr == Distributions.beta:
            responses.append(self.validate_subparam_incoming_value(DP.ALPHA, self._alpha))
            responses.append(self.validate_subparam_incoming_value(DP.BETA, self._beta))

        else:
            pass

        for resp in responses:
            if resp.status != InputStatus.GOOD:
                return resp
        else:
            return ValidationResponse(InputStatus.GOOD, "")

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
        }
        
        # Add descriptive parameter names based on distribution type
        if self._distr in [Distributions.nor, Distributions.tnor]:
            extra[DP.MEAN] = float(self._mean)
            extra[DP.STD] = float(self._std)

        elif self._distr in [Distributions.log, Distributions.tlog]:
            extra[DP.MU] = float(self._mu)
            extra[DP.SIGMA] = float(self._sigma)

        elif self._distr == Distributions.beta:
            extra[DP.ALPHA] = float(self._alpha)
            extra[DP.BETA] = float(self._beta)

        if self._distr in [Distributions.tnor, Distributions.tlog, Distributions.uni]:
            extra[DP.LOWER] = float(self._lower)
            extra[DP.UPPER] = 'inf' if self._upper is None else float(self._upper)
            
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

        self.uncertainty = data['uncertainty']
        self.distr = data['distr']
        default = self._defaults
        
        # Load parameters based on distribution type
        if self.distr in [Distributions.nor, Distributions.tnor]:
            self._mean = data.get(DP.MEAN, default[DP.MEAN])
            self._std = data.get(DP.STD, default[DP.STD])
            # Initialize other params to defaults
            self._mu = default[DP.MU]
            self._sigma = default[DP.SIGMA]

        elif self.distr in [Distributions.log, Distributions.tlog]:
            self._mu = data.get(DP.MU, default[DP.MU])
            self._sigma = data.get(DP.SIGMA, default[DP.SIGMA])
            self._mean = default[DP.MEAN]
            self._std = default[DP.STD]

        elif self.distr == Distributions.uni:
            self._mean = default[DP.MEAN]
            self._std = default[DP.STD]
            self._mu = default[DP.MU]
            self._sigma = default[DP.SIGMA]

        elif self.distr == Distributions.beta:
            self._alpha = data.get(DP.ALPHA, default[DP.ALPHA])
            self._beta = data.get(DP.BETA, default[DP.BETA])

        else:
            # Deterministic - leave all to defaults
            self._mean = default[DP.MEAN]
            self._std = default[DP.STD]
            self._mu = default[DP.MU]
            self._sigma = default[DP.SIGMA]
            self._lower = default[DP.LOWER]
            self._upper = default[DP.UPPER]

        if self.distr in [Distributions.tnor, Distributions.tlog, Distributions.uni]:
            self._lower = data.get(DP.LOWER, default[DP.LOWER])
            u_val = data.get(DP.UPPER, default[DP.UPPER])
            self._upper = None if u_val == 'inf' else u_val
        else:
            self._lower = default[DP.LOWER]
            self._upper = default[DP.UPPER]

        if not silent:
            self.changed.notify(self)

            if notify_from_model:
                self.changed_by_model.notify(self)
