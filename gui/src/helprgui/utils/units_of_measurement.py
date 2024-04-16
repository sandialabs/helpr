"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""


from helprgui.utils.helpers import hround


def c_to_k(val):
    """Converts Celsius temperate value to kelvin.

    """
    return val + 273.15


def k_to_c(val):
    """Converts kelvin temperature value to Celsius.

    """
    return val - 273.15


def f_to_k(val):
    """Converts Fahrenheit temperature value to kelvin.

    """
    result = (val - 32) * (5/9) + 273.15
    return result


def k_to_f(val):
    """Converts kelvin temperature value to Fahrenheit.

    """
    result = (val - 273.15) * (9/5) + 32
    return result


def get_unit_type(unit_type: str):
    """Returns UnitType class corresponding to string representation.

    Parameters
    ----------
    unit_type : str
        Unit type, e.g. 'unitless' or 'temperature'.

    Returns
    -------
    UnitType
        UnitType class corresponding to string key.

    """
    unit_type = unit_type.lower().strip()

    options = {
        'unitless': Unitless,
        'none': Unitless,

        'dist': Distance,
        'distance': Distance,

        'dist_sm': SmallDistance,
        'distance_sm': SmallDistance,
        'distance_small': SmallDistance,

        'pres': Pressure,
        'pressure': Pressure,

        'temp': Temperature,
        'temperature': Temperature,

        'fract': Fracture,
        'fracture': Fracture,

        'perc': Percent,
        'percent': Percent,

        'massflow': MassFlow,
        'angle': Angle,
    }
    result = options.get(unit_type, None)
    return result


def get_unit_type_from_unit_key(key: str):
    """
    Returns UnitType containing the given unit represented by string key. Returns Unitless if key not found.
    For example, 'm' returns Distance.

    Parameters
    ----------
    key : str
        string representation of unit, e.g. 'm' or 'psi'

    Returns
    -------
    UnitType
        UnitType containing the specified unit.

    """
    unit_types = [SmallDistance, Distance, Pressure, Temperature, Fracture, Percent, MassFlow, Angle]
    key = key.lower().strip()

    result = Unitless
    for g in unit_types:
        if key in g.units():
            result = g
            break
    return result


class UnitType:
    """
    Base class which describes a set of units of measurement, e.g. distance. These classes are primarily used for unit conversions.

    Attributes
    ----------
    label : str
        Short descriptor of the class of units of measurement; e.g. 'Distance'.
    unit_data : dict
        {string: float or function} Ordered pairs indicating the unit and conversion factor or function that converts from the standard unit
        to that unit; e.g. {'mm': 0.001}.
    display_units: list
        String descriptors of units which are ready for display. These can include HTML and must be ordered according to unit_data pairs.
    std_unit: str or None
        key of standard unit; e.g. 'm' for Distance and '%' for Percent.

    Notes
    -----
    Unit keys should be unique across UnitType, except for SmallDistance.

    """
    label: str
    unit_data: dict
    display_units: list
    std_unit: str or None  # must match value of std unit property, not it's name. e.g. '%' for percentage, not 'p'
    scale_base: float or None = None  # if scale unit (e.g. temperature), this is the base value in std units

    @classmethod
    def convert(cls, val, old=None, new=None, do_round=False):
        """
        Converts value from old to new units, with optional rounding.

        Notes
        -----
        It is usually better to store an un-rounded parameter value and only round for display.

        Parameters
        ----------
        val : float
            Value to convert.

        old : str or None
            Units of input value. If None, standard unit (e.g. meters) will be used.

        new : str or None
            Units of output. If None, standard unit (e.g. meters) will be used.

        do_round : bool, default=False
            Whether output should be rounded.

        Returns
        -------
        float
            Value converted from old units, into new units.

        """
        old_c = cls.unit_data[cls.std_unit] if old is None else cls.unit_data[old]
        new_c = cls.unit_data[cls.std_unit] if new is None else cls.unit_data[new]
        result = old_c * val / new_c
        if do_round:
            result = hround(result)
        return result

    @classmethod
    def units(cls) -> list:
        """Returns list of units available in UnitType class, as string keys.

        """
        return list(cls.unit_data.keys())


class Unitless(UnitType):
    """Unit type representing lack of units.

    """
    label = 'unitless'
    unit_data = {}
    display_units = ['-']
    std_unit = None

    @classmethod
    def convert(cls, val, do_round=False, **kwargs):
        if do_round:
            val = hround(val)
        return val


class Percent(UnitType):
    """Unit type for percent-based values. Stored as percent, not decimal; i.e. 25% is stored as 25, not 0.25.

    """
    label = 'perc'
    unit_data = {'%': 1}
    display_units = ['%']
    p = '%'
    std_unit = '%'

    @classmethod
    def convert(cls, val, do_round=False, **kwargs):
        if do_round:
            val = hround(val)
        return val


class Distance(UnitType):
    """Default unit type indicating distance.

    """
    label = 'dist'
    unit_data = {'m': 1, 'mm': 0.001, 'km': 1000, 'in': 0.0254, 'ft': 0.3048, 'mi': 1609.34}
    display_units = ['m', 'mm', 'Km', 'in', 'ft', 'mi']
    m = 'm'
    mm = 'mm'
    km = 'km'
    inch = 'in'
    ft = 'ft'
    mi = 'mi'
    std_unit = 'm'


class SmallDistance(UnitType):
    """Specialized distance unit type which only includes units equal to or smaller than meters.
    This class is not assigned automatically and must be set by user.

    """
    label = 'dist_sm'
    unit_data = {'m': 1, 'mm': 0.001, 'in': 0.0254, 'ft': 0.3048}
    display_units = ['m', 'mm', 'in', 'ft']
    m = 'm'
    mm = 'mm'
    inch = 'in'
    ft = 'ft'
    std_unit = 'm'


class Pressure(UnitType):
    """Pressure unit type.

    """
    label = 'pres'
    unit_data = {'mpa': 1, 'psi': 0.00689476, 'bar': 0.1}
    display_units = ['MPa', 'psi', 'bar']
    mpa = 'mpa'
    psi = 'psi'
    bar = 'bar'
    std_unit = 'mpa'


class Temperature(UnitType):
    """Temperature unit type.

    """
    label = 'temp'
    unit_data = {'k': 1, 'c': c_to_k, 'f': f_to_k}  # converting FROM unit to std
    unit_data_out = {'k': 1, 'c': k_to_c, 'f': k_to_f}  # converting TO unit from std
    display_units = ['K', 'C', 'F']
    k = 'k'
    c = 'c'
    f = 'f'
    std_unit = 'k'
    scale_base = 273.15

    @classmethod
    def convert(cls, val, old=None, new=None, do_round=False):
        old_c = 1 if old is None else cls.unit_data[old]
        new_c = 1 if new is None else cls.unit_data_out[new]
        result = old_c(val) if callable(old_c) else old_c * val
        result = new_c(result) if callable(new_c) else new_c * result
        if do_round:
            result = hround(result)
        return result


class Fracture(UnitType):
    """Fracture unit type.

    """
    label = 'fract'
    unit_data = {'mpm': 1}
    display_units = ['MPa-m<sup>1/2</sup>']
    mpm = 'mpm'
    std_unit = 'mpm'


class MassFlow(UnitType):
    """Mass flow rate unit type.
    """
    label = 'massflow'
    unit_data = {'kgs': 1}
    display_units = ['kg/s']
    kgs = 'kgs'
    std_unit = 'kgs'


class Angle(UnitType):
    """Angle units
    """
    label = 'angle'
    unit_data = {'rad': 1, 'deg': 0.0174533}
    display_units = ['rad', 'deg']
    rad = 'rad'
    deg = 'deg'
    std_unit = 'rad'
