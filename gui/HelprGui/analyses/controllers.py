"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
from datetime import datetime
import webbrowser
import logging

from PySide6.QtCore import (QObject, Slot, Signal, Property, QAbstractListModel, QModelIndex, Qt)
from PySide6.QtGui import QClipboard, QImage
from PySide6.QtQml import QmlElement

from utils.events import Event
from state.models import State
from parameters.controllers import ParameterController, ChoiceParameterController, BasicParameterController


log = logging.getLogger("HELPR")

QML_IMPORT_NAME = "helpr.classes"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class AnalysisController(QObject):
    """Controller class which manages analysis data binding and views during and after execution of single analysis.

    Notes
    -----
    These controllers reside in main thread and can't access in-progress analyses in child processes.
    Completed analysis results are returned from thread loop.
    Note that event names correspond to usage location; e.g. camelCase events are used in QML.
    Many attributes are implemented as properties to allow access via QML. This includes the analysis parameter controllers.

    Attributes
    ----------
    started
    finished
    has_error
    error_message
    has_warning
    warning_message
    state
    name
    analysis_id
    plots
    study_type_disp
    started_at_str
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
    seed
    study_type

    startedChanged : Signal
        Event indicating analysis has started processing on backend.

    finishedChanged : Signal
        Event indicating analysis has finished.

    request_overwrite_event : Event
        Event indicating form data is overwritten by another set of data (e.g. user loading data from result pane.)

    """
    startedChanged: Signal = Signal(bool)
    finishedChanged: Signal = Signal(bool)

    request_overwrite_event: Event

    # instance of state that undergoes analysis.
    _analysis_id: int
    _state: State or None = None
    _started: bool = False
    _finished: bool = False
    _canceled: bool = False

    # temp data used while analysis in-progress
    _study_type_str: str = ''
    _started_at: datetime

    # Parameter controllers used to process data in form and to display it in results pane for completed analyses.
    _out_diam: ParameterController
    _thickness: ParameterController
    _p_max: ParameterController
    _p_min: ParameterController
    _crack_dep: ParameterController
    _temp: ParameterController
    _vol_h2: ParameterController
    _yield_str: ParameterController
    _frac_resist: ParameterController
    _crack_len: ParameterController
    _n_ale: BasicParameterController
    _n_epi: BasicParameterController
    _seed: BasicParameterController
    _study_type: ChoiceParameterController

    def __init__(self, analysis_id: int, study_type: str):
        """Initializes controller with key data for analysis being submitted, including unique id.

        Parameters
        ----------
        analysis_id : int
            Increasing id indicating the analysis managed by this controller.
        study_type : str
            Analysis sample type; e.g. 'bnd', 'det'.

        """
        super().__init__(parent=None)
        self._analysis = None
        self._analysis_id = analysis_id
        self._study_type_str = study_type
        self._started_at = datetime.now()

        self.request_overwrite_event = Event()

    def update_from_state_object(self, state: State):
        """Updates parameters and state data from state object.

        Parameters
        ----------
        state : State
            State model containing parameter and result data for this completed analysis.

        Notes
        -----
        State object likely returned from analysis processing thread after analysis completed.
        Emits finishedChanged event.

        """
        self._finished = True
        self._state = state
        self._study_type = ChoiceParameterController(param=self._state.study_type)

        self._out_diam = ParameterController(param=self._state.out_diam)
        self._thickness = ParameterController(param=self._state.thickness)
        self._crack_dep = ParameterController(param=self._state.crack_dep)
        self._p_max = ParameterController(param=self._state.p_max)
        self._p_min = ParameterController(param=self._state.p_min)
        self._temp = ParameterController(param=self._state.temp)
        self._vol_h2 = ParameterController(param=self._state.vol_h2)
        self._yield_str = ParameterController(param=self._state.yield_str)
        self._frac_resist = ParameterController(param=self._state.frac_resist)
        self._crack_len = ParameterController(param=self._state.crack_len)

        self._n_ale = BasicParameterController(param=self._state.n_ale)
        self._n_epi = BasicParameterController(param=self._state.n_epi)
        self._seed = BasicParameterController(param=self._state.seed)

        self.finishedChanged.emit(True)

    @Property(bool, notify=startedChanged)
    def started(self):
        """Flag indicating analysis has begun processing. """
        return self._started

    @started.setter
    def started(self, val: bool):
        self._started = val
        self.startedChanged.emit(val)

    @Property(bool, notify=finishedChanged)
    def finished(self):
        """Flag indicating analysis has finished. """
        return self._finished

    @Property(bool)
    def canceled(self):
        """Flag indicating analysis was canceled by user. """
        # return self._state and self._state.was_canceled
        return self._canceled

    def do_cancel(self):
        self._canceled = True
        self._finished = True

    @Property(bool, constant=True)
    def has_error(self):
        """Flag indicating analysis encountered an error. """
        return self._state and self._state.has_error

    @Property(str, constant=True)
    def error_message(self):
        """Message describes error encountered during analysis. """
        if self._state is None:
            return ""
        else:
            return self._state.error_message

    @Property(bool, constant=True)
    def has_warning(self):
        """Flag indicating analysis encountered a warning. """
        return self._state.has_warning

    @Property(str, constant=True)
    def warning_message(self):
        """Message describes warning encountered during analysis. """
        return self._state.warning_message

    @Property(State)
    def state(self):
        """State object containing analysis parameters used during analysis processing. """
        return self._state

    @Property(str, constant=True)
    def name(self):
        """Simple name of analysis. """
        return f"{self.analysis_id}"

    @Property(int, constant=True)
    def analysis_id(self):
        """Unique int id corresponding to analysis. """
        return self._analysis_id

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

    # =============
    # Result interaction
    @Slot()
    def overwrite_form_data(self):
        """Replaces current parameter in form state with data from this analysis. """
        new_data = self.state.to_dict()
        self.request_overwrite_event.notify(new_data)

    @Slot()
    def export_pdf(self):
        pass

    @Slot()
    def open_output_directory(self):
        """Opens data output directory in OS window. """
        output_dir = self.state.get_output_dir()
        if output_dir is not None:
            webbrowser.open("file:///" + output_dir.as_posix())

    @Slot(str)
    def copy_image_to_clipboard(self, img_str):
        """Copies image filepath string to user's OS clipboard. """
        clip = QClipboard()
        img = QImage(img_str)
        clip.setImage(img, QClipboard.Mode.Clipboard)

    # =====================
    # IN-PROGRESS TEMP DATA
    @Property(str, constant=True)
    def study_type_disp(self):
        """Prettified sample type descriptor; e.g. 'deterministic'. """
        return self._study_type_str

    @Property(str, constant=True)
    def started_at_str(self):
        """String describing time at which analysis begin, (H:M:S). """
        return self._started_at.strftime('%H:%M:%S')

    # =====================
    # PARAMETERS
    @Property(ChoiceParameterController)
    def study_type(self):
        """Parameter representation of sample type input. """
        return self._study_type

    @Property(ParameterController)
    def thickness(self):
        """Parameter representation of thickness input. """
        return self._thickness

    @Property(ParameterController)
    def out_diam(self):
        """Parameter representation of outer diameter input. """
        return self._out_diam

    @Property(ParameterController)
    def crack_dep(self):
        """Parameter representation of crack depth input. """
        return self._crack_dep

    @Property(ParameterController)
    def p_max(self):
        """Parameter representation of maximum pressure input. """
        return self._p_max

    @Property(ParameterController)
    def p_min(self):
        """Parameter representation of minimum pressure input. """
        return self._p_min

    @Property(ParameterController)
    def temp(self):
        """Parameter representation of temperature input. """
        return self._temp

    @Property(ParameterController)
    def vol_h2(self):
        """Parameter representation of H2 volume input. """
        return self._vol_h2

    @Property(ParameterController)
    def yield_str(self):
        """Parameter representation of yield strength input. """
        return self._yield_str

    @Property(ParameterController)
    def frac_resist(self):
        """Parameter representation of fracture resistance input. """
        return self._frac_resist

    @Property(ParameterController)
    def crack_len(self):
        """Parameter representation of crack length input. """
        return self._crack_len

    @Property(BasicParameterController)
    def n_ale(self):
        """Parameter representation of aleatory sample count input. """
        return self._n_ale

    @Property(BasicParameterController)
    def n_epi(self):
        """Parameter representation of epistemic sample count input. """
        return self._n_epi

    @Property(BasicParameterController)
    def seed(self):
        """Parameter representation of random seed input. """
        return self._seed

    # =====================
    # PLOTS
    @Property(str, constant=True)
    def ex_rates_plot(self):
        """String filepath of pipe lifetime plot. """
        result = ""
        if self.state is not None and self.state.ex_rates_plot:
            result = self.state.ex_rates_plot
        return result

    @Property(str, constant=True)
    def crack_growth_plot(self):
        """String filepath of crack growth plot. """
        result = ""
        if self.state is not None and self.state.crack_growth_plot:
            result = self.state.crack_growth_plot
        return result

    @Property(str, constant=True)
    def ensemble_plot(self):
        """String filepath of ensemble plot. """
        result = ""
        if self.state is not None and self.state.ensemble_plot:
            result = self.state.ensemble_plot
        return result

    @Property(str, constant=True)
    def cycle_plot(self):
        """String filepath of cycle plot. """
        result = ""
        if self.state is not None and self.state.cycle_plot:
            result = self.state.cycle_plot
        return result

    @Property(list, constant=True)
    def cycle_cbv_plots(self):
        """String filepath of cycle CBV plots. """
        results = []
        if self.state is not None and self.state.cycle_cbv_plots:
            for plot in self.state.cycle_cbv_plots:
                results.append(f"{plot}")
        return results

    @Property(str, constant=True)
    def pdf_plot(self):
        """String filepath of PDF plot. """
        result = ""
        if self.state is not None and self.state.pdf_plot:
            result = self.state.pdf_plot
        return result

    @Property(str, constant=True)
    def cdf_plot(self):
        """String filepath of CDF plot. """
        result = ""
        if self.state is not None and self.state.cdf_plot:
            result = self.state.cdf_plot
        return result

    @Property(str, constant=True)
    def fad_plot(self):
        """String filepath of failure assessment plot. """
        result = ""
        if self.state is not None and self.state.fad_plot:
            result = self.state.fad_plot
        return result

    @Property(str, constant=True)
    def sen_plot(self):
        """String filepath of sensitivity plot. """
        result = ""
        if self.state is not None and self.state.sen_plot:
            result = self.state.sen_plot
        return result


class QueueController(QAbstractListModel):
    """Manages display of analysis queue.

    Attributes
    ----------
    item_role : int
        Qt property for item management.

    Notes
    -----
    QML reserves the terms 'data' and 'model' so don't use those here.

    """
    item_role = Qt.UserRole + 2
    _controllers: [AnalysisController]
    _removedItems = {}  # {id, ac}

    _roles = {item_role: b"item"}

    def __init__(self):
        """Initialize with empty controller list. """
        super().__init__(parent=None)
        self._controllers = []

    def rowCount(self, parent=None, *args, **kwargs):
        """Returns count of controllers. """
        return len(self._controllers)

    def data(self, index, role=Qt.DisplayRole):
        """Returns controller based on index.

        Parameters
        ----------
        index : int
            Array index of selected item.
        role : int
            Qt internal role

        Returns
        -------
        AnalysisController
            Controller matching given index.

        """
        try:
            item = self._controllers[index.row()]
        except IndexError:
            return Qt.QVariant()

        if role == self.item_role:
            return item

    def roleNames(self):
        return self._roles

    @Slot(AnalysisController)
    def add_item(self, ac):
        """Adds AnalysisController to queue. """
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._controllers.append(ac)
        self.endInsertRows()

    @Slot(int)
    def remove_item(self, idx):
        """Removes AnalysisController from queue and saves it for potential restoration. """
        self.beginRemoveRows(QModelIndex(), idx, idx)
        # save in case of restore
        removed = self._controllers.pop(idx)
        self._removedItems[removed.analysis_id] = removed
        self.endRemoveRows()

    @Slot(int)
    def restore_item(self, a_id):
        """Restores AnalysisController to queue. """
        ac = self._removedItems.get(a_id, None)
        if ac is not None:
            self.add_item(ac)

    def handle_new_analysis(self, ac: AnalysisController):
        """Tracks given AnalysisController via queue. """
        self.add_item(ac)


