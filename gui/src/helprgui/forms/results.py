"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import json
import logging

import numpy as np
from PySide6.QtCore import Property
from PySide6.QtQml import QmlElement

from helprgui.hygu.forms.results import ResultsForm
from helprgui.hygu.forms.fields import ChoiceFormField, IntFormField, StringFormField, BoolFormField
from helprgui.hygu.forms.fields_probabilistic import UncertainFormField

from helprgui.models.models import State
from helprgui import app_settings

QML_IMPORT_NAME = f"{ app_settings.APPNAME_LOWER}.classes"
QML_IMPORT_MAJOR_VERSION = 1
log = logging.getLogger(app_settings.APPNAME)


@QmlElement
class CrackEvolutionResultsForm(ResultsForm):
    """Controller class which manages analysis data binding and views during and after execution of single analysis.

    Notes
    -----
    These controllers reside in main thread and can't access in-progress analyses in child processes.
    Completed analysis results are returned from thread loop.
    Note that event names correspond to usage location; e.g. camelCase events are used in QML.
    Many attributes are implemented as properties to allow access via QML. This includes the analysis parameter controllers.

    Attributes
    ----------
    plots
    study_type_disp
    study_type
    out_diam
    thickness
    p_max
    p_min
    crack_dep
    temp
    vol_h2
    yield_str
    frac_resist
    crack_len
    n_ale
    n_epi
    smys
    seed

    """

    # Parameter controllers used to process data in form and to display it in results pane for completed analyses.
    _out_diam: UncertainFormField = None
    _thickness: UncertainFormField = None
    _p_max: UncertainFormField = None
    _p_min: UncertainFormField = None
    _crack_dep: UncertainFormField = None
    _temp: UncertainFormField = None
    _vol_h2: UncertainFormField = None
    _yield_str: UncertainFormField = None
    _frac_resist: UncertainFormField = None
    _crack_len: UncertainFormField = None
    _n_ale: IntFormField = None
    _n_epi: IntFormField = None
    _seed: IntFormField = None
    _n_cycles: IntFormField = None
    _study_type: ChoiceFormField = None
    _stress_method: ChoiceFormField = None
    _surface: ChoiceFormField = None
    _crack_assump: ChoiceFormField = None

    _smys: UncertainFormField = None
    _r_ratio: UncertainFormField = None
    _a_m: UncertainFormField = None
    _a_c: UncertainFormField = None
    _t_r: UncertainFormField = None

    def __init__(self, analysis_id: int, prelim_state, *args, **kwargs):
        """Initializes controller with key data for analysis being submitted, including unique id.

        Parameters
        ----------
        analysis_id : int
            Increasing id indicating the analysis managed by this controller.

        """
        super().__init__(analysis_id=analysis_id, prelim_state=prelim_state)
        # self._study_type_str = study_type
        self._study_type_str = prelim_state.study_type.get_value_display()

    def update_from_state_object(self, state: State):
        """Updates parameters and state data from state object.

        Parameters
        ----------
        state : State
            State model containing parameter and result data for this completed analysis.

        Notes
        -----
        State object likely returned from analysis processing thread after analysis completed.

        """
        self._state = state

        self._analysis_name = StringFormField(param=self._state.analysis_name)
        self._study_type = ChoiceFormField(param=self._state.study_type)
        self._stress_method = ChoiceFormField(param=self._state.stress_method)
        self._surface = ChoiceFormField(param=self._state.surface)
        self._crack_assump = ChoiceFormField(param=self._state.crack_assump)

        self._out_diam = UncertainFormField(param=self._state.out_diam)
        self._thickness = UncertainFormField(param=self._state.thickness)
        self._crack_dep = UncertainFormField(param=self._state.crack_dep)
        self._p_max = UncertainFormField(param=self._state.p_max)
        self._p_min = UncertainFormField(param=self._state.p_min)
        self._temp = UncertainFormField(param=self._state.temp)
        self._vol_h2 = UncertainFormField(param=self._state.vol_h2)
        self._yield_str = UncertainFormField(param=self._state.yield_str)
        self._frac_resist = UncertainFormField(param=self._state.frac_resist)
        self._crack_len = UncertainFormField(param=self._state.crack_len)
        self._n_ale = IntFormField(param=self._state.n_ale)
        self._n_epi = IntFormField(param=self._state.n_epi)
        self._seed = IntFormField(param=self._state.seed)
        self._n_cycles = IntFormField(param=self._state.n_cycles)

        self._smys = UncertainFormField(param=self._state.smys)
        self._r_ratio = UncertainFormField(param=self._state.r_ratio)
        self._a_m = UncertainFormField(param=self._state.a_m)
        self._a_c = UncertainFormField(param=self._state.a_c)
        self._t_r = UncertainFormField(param=self._state.t_r)

        super().finish_state_update()

    @Property(list)
    def plots(self):
        """List of plots as prefixed filepaths for use in QML. """
        results = []
        if self.state is not None:
            results.append(f"file:{self.state.ensemble_plot}")
            results.append(f"file:{self.state.cycle_plot}")
            results.append(f"file:{self.state.cycle_cbv_plot}")
            results.append(f"file:{self.state.pdf_plot}")
            results.append(f"file:{self.state.cdf_plot}")
            results.append(f"file:{self.state.fad_plot}")
        return results

    # =====================
    # IN-PROGRESS TEMP DATA
    @Property(str, constant=True)
    def study_type_disp(self):
        """Prettified sample type descriptor; e.g. 'deterministic'. """
        return self._study_type_str

    # =====================
    # PARAMETERS
    study_type = Property(ChoiceFormField, fget=lambda self: self._study_type)
    stress_method = Property(ChoiceFormField, fget=lambda self: self._stress_method)
    surface = Property(ChoiceFormField, fget=lambda self: self._surface)
    crack_assump = Property(ChoiceFormField, fget=lambda self: self._crack_assump)

    thickness = Property(UncertainFormField, fget=lambda self: self._thickness)
    out_diam = Property(UncertainFormField, fget=lambda self: self._out_diam)
    crack_dep = Property(UncertainFormField, fget=lambda self: self._crack_dep)
    p_max = Property(UncertainFormField, fget=lambda self: self._p_max)
    p_min = Property(UncertainFormField, fget=lambda self: self._p_min)
    temp = Property(UncertainFormField, fget=lambda self: self._temp)
    vol_h2 = Property(UncertainFormField, fget=lambda self: self._vol_h2)
    yield_str = Property(UncertainFormField, fget=lambda self: self._yield_str)
    frac_resist = Property(UncertainFormField, fget=lambda self: self._frac_resist)
    crack_len = Property(UncertainFormField, fget=lambda self: self._crack_len)

    smys = Property(UncertainFormField, fget=lambda self: self._smys)
    r_ratio = Property(UncertainFormField, fget=lambda self: self._r_ratio)
    a_m = Property(UncertainFormField, fget=lambda self: self._a_m)
    a_c = Property(UncertainFormField, fget=lambda self: self._a_c)
    t_r = Property(UncertainFormField, fget=lambda self: self._t_r)

    n_ale = Property(IntFormField, fget=lambda self: self._n_ale)
    n_epi = Property(IntFormField, fget=lambda self: self._n_epi)
    seed = Property(IntFormField, fget=lambda self: self._seed)
    n_cycles = Property(IntFormField, fget=lambda self: self._n_cycles)

    # =====================
    # PLOTS
    @Property(bool, constant=True)
    def show_interactive_charts(self):
        """Whether to display static or interactive charts. """
        result = self.state.do_interactive_charts.value
        return result

    @Property(str, constant=True)
    def design_curve_plot(self):
        """String filepath of pipe lifetime plot. """
        result = self.state.design_curve_plot if self.state is not None and self.state.design_curve_plot else ""
        return result

    @Property(str, constant=True)
    def crack_growth_plot(self):
        """String filepath of crack growth plot. """
        result = self.state.crack_growth_plot if self.state is not None and self.state.crack_growth_plot else ""
        return result

    @Property(str, constant=True)
    def ensemble_plot(self):
        """String filepath of ensemble plot. """
        result = self.state.ensemble_plot if self.state is not None and self.state.ensemble_plot else ""
        return result

    @Property(str, constant=True)
    def cycle_plot(self):
        """String filepath of cycle plot. """
        result = self.state.cycle_plot if self.state is not None and self.state.cycle_plot else ""
        return result

    @Property(str, constant=True)
    def pdf_plot(self):
        """String filepath of PDF plot. """
        result = self.state.pdf_plot if self.state is not None and self.state.pdf_plot else ""
        return result

    @Property(str, constant=True)
    def cdf_plot(self):
        """String filepath of CDF plot. """
        result = self.state.cdf_plot if self.state is not None and self.state.cdf_plot else ""
        return result

    @Property(str, constant=True)
    def fad_plot(self):
        """String filepath of failure assessment plot. """
        result = self.state.fad_plot if self.state is not None and self.state.fad_plot else ""
        return result

    @Property(str, constant=True)
    def sen_plot(self):
        """String filepath of sensitivity plot. """
        result = self.state.sen_plot if self.state is not None and self.state.sen_plot else ""
        return result

    @Property(list, constant=True)
    def cycle_cbv_plots(self):
        """String filepath of cycle CBV plots. """
        results = []
        if self.state is not None and self.state.cycle_cbv_plots:
            for plot in self.state.cycle_cbv_plots:
                results.append(f"{plot}")
        return results

    def _get_slimmed_data_dict(self, xs, ys, max_num=100):
        """
        Gets zipped, sampled pairs of x,y data ready for GUI plotting.

        Returns
        -------
        [{x, y}]

        """
        if len(xs) > max_num:
            step = int(len(xs) / max_num)
            xs = xs[1::step]
            ys = ys[1::step]
        result = [{'x': x, 'y': y} for x, y in zip(xs, ys)]
        return result

    def _prep_arr_2d(self, arr, skip_x_0=False):
        """Converts list of points into {x, y} format ready for Chart.js.
        Optionally skip points where x is 0. This is primarily used for x-axis log plots and invalid data. """
        result = []
        for elem in arr:
            if np.any(np.isnan(elem)):
                continue

            if skip_x_0 and elem[0] == 0:
                continue

            result.append({'x': elem[0], 'y': elem[1]})
        return result

    def _prep_point(self, arr):
        if np.any(np.isnan(arr)):
            result = []
        else:
            result = [{'x': arr[0], 'y': arr[1]}]
        return result

    @Property(str, constant=True)
    def crack_growth_data(self):
        if self.state.crack_growth_plot is None or not self.state.do_crack_growth_plot.value:
            return ''

        data = self.state.crack_growth_data
        result = {
            'a_t': self._prep_arr_2d(data['a_t']),
            'acrit_pt': self._prep_point(data['acrit_pt']),
            '25acrit_pt': self._prep_point(data['25acrit_pt']),
            'half_pt': self._prep_point(data['half_pt']),
        }
        return json.dumps(result)

    @Property(str, constant=True)
    def design_curve_data(self):
        if self.state.design_curve_plot is None or not self.state.do_design_curve_plot.value:
            return ''

        data = self.state.design_curve_data
        result = {
            'ln1': self._prep_arr_2d(data['ln1']),
            'ln2': self._prep_arr_2d(data['ln2']),
        }
        return json.dumps(result)

    @Property(str, constant=True)
    def det_fad_data(self):
        if self.state.fad_plot is None or not self.state.do_fad_plot.value:
            return ''

        data = self.state.fad_data
        result = {
            'ln1': self._prep_arr_2d(data['ln1']),
            'pt1': self._prep_point(data['pt1']),
        }
        return json.dumps(result)

    @Property(str, constant=True)
    def ensemble_data(self):
        if self.state.ensemble_plot is None or not self.state.do_ensemble_plot.value:
            return ''
        data = self.state.ensemble_data
        result = {
            'lines': [self._prep_arr_2d(ln) for ln in data['lines']],
            'pts': self._prep_arr_2d(data['pts'], True),
        }
        return json.dumps(result)

    @Property(str, constant=True)
    def cycle_data(self):
        if self.state.cycle_plot is None or not self.state.do_cycle_plot.value:
            return ''
        data = self.state.cycle_data
        result = {
            'subsets': [self._prep_arr_2d(ln, True) for ln in data['subsets']],
            'nominal_pt': self._prep_point(data['nominal_pt']),
        }
        return json.dumps(result)

    @Property(str, constant=True)
    def prob_fad_data(self):
        if self.state.fad_plot is None or not self.state.do_fad_plot.value:
            return ''
        data = self.state.fad_data
        result = {
            'line': [self._prep_arr_2d(ln) for ln in data['lines']],
            'pts': [self._prep_arr_2d(data['pts'])],
            'nominal_pt': self._prep_point(data['nominal_pt']),
        }
        return json.dumps(result)

    @Property(str, constant=True)
    def pdf_data(self):
        if self.state.pdf_plot is None or not self.state.do_pdf_plot.value:
            return ''
        data = self.state.pdf_data
        result = {
            'lines': [self._prep_arr_2d(ln) for ln in data['bin_data']],
            'nominal': [self._prep_arr_2d(ln) for ln in data['nominal']],
        }
        return json.dumps(result)

    @Property(str, constant=True)
    def cdf_data(self):
        if self.state.cdf_plot is None or not self.state.do_cdf_plot.value:
            return ''
        data = self.state.cdf_data
        result = {
            'lines': [self._prep_arr_2d(ln, True) for ln in data['lines']],
            'nominal': [self._prep_arr_2d(data['nominal'])]
        }
        return json.dumps(result)

    @Property(str, constant=True)
    def sensitivity_data(self):
        if self.state.sen_plot is None or not self.state.do_sen_plot.value:
            return ''
        data = self.state.sen_data
        results = []
        for elem in data:
            dc = {
                'label': elem['label'],
                'data': self._prep_arr_2d(elem['data'])
            }
            results.append(dc)
        return json.dumps(results)
