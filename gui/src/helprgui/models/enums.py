from helprgui.hygu.utils.distributions import BaseChoiceList


class StudyTypes(BaseChoiceList):
    """Study type options for submitted analysis. """
    keys = ['det', 'prb', 'bnd', 'sam']
    labels = ['Deterministic', 'Probabilistic', 'Sensitivity (Bounds)', 'Sensitivity (Samples)']
    det = 'det'
    prb = 'prb'
    bnd = 'bnd'
    sam = 'sam'


class StressMethod(BaseChoiceList):
    keys = ['anderson', 'api']
    labels = ['Anderson', 'API 579-1']
    anderson = 'anderson'
    api = 'api'


class SurfaceType(BaseChoiceList):
    keys = ['inside', 'outside']
    labels = ['Inside', 'Outside']
    inside = 'inside'
    outside = 'outside'


class CrackAssumption(BaseChoiceList):
    keys = ['prop', 'fix', 'ind']
    labels = ['Constant a/c ratio', 'Fixed c value', 'Independent a & c']
    prop = 'prop'
    fix = 'fix'
    ind = 'ind'


class CycleUnits(BaseChoiceList):
    """Cycle options representing units of time. """
    keys = ['hr', 'day']
    labels = ['Hour', 'Day']
    hr = 'hr'
    day = 'day'
