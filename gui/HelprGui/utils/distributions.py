

class MetaChoiceList(type):
    """Metaclass defining enum-like list of choices described by short strings.

    """
    keys: list

    def __contains__(cls, item):
        item = item.lower().strip()
        return item in cls.keys

    def __len__(cls):
        return len(cls.keys)

    def __index__(cls, i: int):
        return cls.keys[i]

    def __getitem__(cls, item):
        return cls.keys[item]


class BaseChoiceList(metaclass=MetaChoiceList):
    """Represents a list of paired keys and labels. """
    keys: list
    labels: list

    @classmethod
    def index(cls, item: str):
        item = item.lower().strip()
        return cls.keys.index(item)


class Distributions(BaseChoiceList):
    """Distribution options for input parameter sampling. """
    keys = ['det', 'nor', 'log', 'uni']
    labels = ['Deterministic', 'Normal', 'Lognormal', 'Uniform']
    det = 'det'
    nor = 'nor'
    log = 'log'
    uni = 'uni'


class Uncertainties(BaseChoiceList):
    """Uncertainty options for input parameter sampling. """
    keys = ['ale', 'epi', None]
    labels = ['Aleatory', 'Epistemic', 'None']
    ale = 'ale'
    epi = 'epi'


class StudyTypes(BaseChoiceList):
    """Study type options for submitted analysis. """
    keys = ['det', 'prb', 'bnd', 'sam']
    labels = ['Deterministic', 'Probabilistic', 'Sensitivity (Bounds)', 'Sensitivity (Samples)']
    det = 'det'
    prb = 'prb'
    bnd = 'bnd'
    sam = 'sam'


class CycleUnits(BaseChoiceList):
    """Cycle options representing units of time. """
    keys = ['hr', 'day']
    labels = ['Hour', 'Day']
    hr = 'hr'
    day = 'day'
