"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import logging

from PySide6.QtCore import Property
from PySide6.QtQml import QmlElement

from helprgui.forms.results import ResultsForm
from helprgui.forms.fields import ChoiceFormField, IntFormField, StringFormField
from helprgui.forms.fields_probabilistic import UncertainFormField

from models.models import State
import app_settings

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
    _smys: UncertainFormField = None
    _seed: IntFormField = None
    _study_type: ChoiceFormField = None

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
        self._smys = UncertainFormField(param=self._state.smys)
        self._seed = IntFormField(param=self._state.seed)

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

    n_ale = Property(IntFormField, fget=lambda self: self._n_ale)
    n_epi = Property(IntFormField, fget=lambda self: self._n_epi)
    seed = Property(IntFormField, fget=lambda self: self._seed)

    # =====================
    # PLOTS
    @Property(str, constant=True)
    def ex_rates_plot(self):
        """String filepath of pipe lifetime plot. """
        result = self.state.ex_rates_plot if self.state is not None and self.state.ex_rates_plot else ""
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


# class QueueController(QAbstractListModel):
#     """Manages display of analysis queue.
#
#     Attributes
#     ----------
#     item_role : int
#         Qt property for item management.
#
#     Notes
#     -----
#     QML reserves the terms 'data' and 'model' so don't use those here.
#
#     """
#     item_role = Qt.UserRole + 2
#     _controllers: [AnalysisController]
#     _removedItems = {}  # {id, ac}
#
#     _roles = {item_role: b"item"}
#
#     def __init__(self):
#         """Initialize with empty controller list. """
#         super().__init__(parent=None)
#         self._controllers = []
#
#     def rowCount(self, parent=None, *args, **kwargs):
#         """Returns count of controllers. """
#         return len(self._controllers)
#
#     def data(self, index, role=Qt.DisplayRole):
#         """Returns controller based on index.
#
#         Parameters
#         ----------
#         index : int
#             Array index of selected item.
#         role : int
#             Qt internal role
#
#         Returns
#         -------
#         AnalysisController
#             Controller matching given index.
#
#         """
#         try:
#             item = self._controllers[index.row()]
#         except IndexError:
#             return Qt.QVariant()
#
#         if role == self.item_role:
#             return item
#
#     def roleNames(self):
#         return self._roles
#
#     @Slot(AnalysisController)
#     def add_item(self, ac):
#         """Adds AnalysisController to queue. """
#         self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
#         self._controllers.append(ac)
#         self.endInsertRows()
#
#     @Slot(int)
#     def remove_item(self, idx):
#         """Removes AnalysisController from queue and saves it for potential restoration. """
#         self.beginRemoveRows(QModelIndex(), idx, idx)
#         # save in case of restore
#         removed = self._controllers.pop(idx)
#         self._removedItems[removed.analysis_id] = removed
#         self.endRemoveRows()
#
#     @Slot(int)
#     def restore_item(self, a_id):
#         """Restores AnalysisController to queue. """
#         ac = self._removedItems.get(a_id, None)
#         if ac is not None:
#             self.add_item(ac)
#
#     def handle_new_analysis(self, ac: AnalysisController):
#         """Tracks given AnalysisController via queue. """
#         self.add_item(ac)


