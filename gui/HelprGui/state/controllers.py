"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import time
import logging
log = logging.getLogger("HELPR")

from PySide6.QtCore import (QObject, Slot, Signal, QUrl, Property)

import gui_settings
from state.models import State
from analyses.controllers import QueueController, AnalysisController
from analyses.threads import AnalysisThread

QML_IMPORT_NAME = "helpr.classes"
QML_IMPORT_MAJOR_VERSION = 1


class DataController(QObject):
    """Top-level manager of GUI form, analysis thread, and analysis requests.

    Attributes
    ----------
    save_file_exists
    about_str
    copyright_str
    version_str
    can_undo
    can_redo
    db : State
        Backing data store of all parameter values.
    q_app : QApplication or None
        Initialized Qt application
    queue_controller : QueueController
        Analysis queue manager
    analysis_controllers : dict
        List of analysis controllers corresponding to submitted or completed analysis; {analysis_id, controller}
    thread : AnalysisThread
        Long-running thread which handles analysis submissions and sub-process pool.
    analysisStarted : Signal
        Event emitted when a new analysis is submitted.
    historyChanged : Signal
        Event emitted when form history is modified.
    alertChanged : Signal
        Event emitted when alert state changes.
    newMessageEvent : Signal
        Event emitted when new messages is placed on UI message display queue.

    Notes
    -----
    Qt signals use camelCase for consistency with QML coding style.

    """
    db: State
    queue_controller: QueueController = None
    analysis_controllers: dict = {}
    thread: AnalysisThread

    analysisStarted = Signal(State)
    historyChanged = Signal()
    alertChanged = Signal(str, int)
    newMessageEvent = Signal(str)

    # parent QApplication
    q_app = None

    def __init__(self):
        """Initializes backend store and thread controller. """
        super().__init__(parent=None)
        self.db = State()
        self.db.history_changed += lambda x: self.historyChanged.emit()

        self.thread = AnalysisThread(self.db)
        self.thread.start()

        self._activate_validation()

    def set_app(self, app):
        """Sets Qt application once initialized. """
        self.q_app = app

    def set_controller(self, controller):
        """Sets queue controller. """
        self.queue_controller = controller

    def check_form_valid(self, *args, **kwargs) -> bool:
        """Checks whether form state is valid. Triggers form alert display and continuous validation when invalid.

        Notes
        -----
        May receive misc. inputs from other events.

        Returns
        -------
        bool
            True if form state is valid.

        """
        status_level, msg = self.db.check_valid()  # 3 is error, 2 is warning, 1 is info, 0 is no issues
        if status_level == 3:
            self._toggle_form_alert(msg, 3)
            return False

        elif status_level == 2:
            self._toggle_form_alert(msg, 2)
            return True

        elif status_level == 1:
            self._toggle_form_alert(msg, 1)
            return True

        elif status_level == 0:
            self._toggle_form_alert('', 0)
            return True

    @Slot()
    def request_analysis(self):
        """Handles analysis request by submitting valid data to thread and updating queue.

        """
        status = self.check_form_valid()
        if not status:
            return

        # must remove listeners on state, otherwise it will attempt (and fail) to deepcopy this object as well
        self._deactivate_validation()
        analysis_id = self.thread.request_new_analysis(self.analysis_started_callback, self.analysis_finished_callback)
        if analysis_id is not None:
            # does not have access to state analysis data used in analysis so manually pass in necessary temp data
            study_type_str = self.db.study_type.get_value_display()
            ac = AnalysisController(analysis_id, study_type=study_type_str)
            ac.request_overwrite_event += self.handle_child_requests_form_overwrite
            self.analysis_controllers[analysis_id] = ac
            # add view to visible queue
            self.queue_controller.handle_new_analysis(ac)
        self._activate_validation()

    @Slot(int)
    def cancel_analysis(self, ac_id):
        """Begins process of canceling in-progress analysis. Note that GUI updates immediately by removing queue item.
        """
        self._log(f"Cancel received {ac_id}")
        if ac_id in self.analysis_controllers:
            ac = self.analysis_controllers[ac_id]
            ac.do_cancel()
        self.thread.cancel_analysis(ac_id)

    def analysis_started_callback(self, analysis_id: int):
        """Updates analysis status. Called via thread once analysis is prepped for pool processing. """
        ac = self.analysis_controllers[analysis_id]
        ac.started = True

    def analysis_finished_callback(self, state_obj: State, results: dict):
        """Updates state of returned analysis with finalized data and sends it to its AnalysisController for final processing.
        Called via thread after processing pool finishes executing analysis.

        Parameters
        ----------
        state_obj : State
            state model object containing parameter and result data for specified analysis.

        results : dict
            analysis results including data and plots.

        """
        ac = self.analysis_controllers[state_obj.analysis_id]

        self._log('Hydrating state object with result data.')
        status = results['status']
        if status == -1:
            self._log('Skipping hydration - analysis encountered error.')
            state_obj.has_error = True
            state_obj.error = results.pop('error', None)
            state_obj.error_message = results.pop('message', '')

        elif status == 2:
            # Analysis canceled by user
            self._log('Skipping hydration - analysis canceled.')
            state_obj.has_error = False
            state_obj.was_canceled = True

        else:
            state_obj.has_error = False
            state_obj.set_output_dir(results['output_dir'])

            state_obj.crack_growth_plot = results.get('crack_growth_plot')
            state_obj.ensemble_plot = results.get('ensemble_plot')
            state_obj.ex_rates_plot = results.get('ex_rates_plot')
            state_obj.fad_plot = results.get('fad_plot')
            state_obj.cycle_plot = results.get('cycle_plot')
            state_obj.cycle_cbv_plots = results.get('cycle_cbv_plots')
            state_obj.pdf_plot = results.get('pdf_plot')
            state_obj.cdf_plot = results.get('cdf_plot')
            state_obj.sen_plot = results.get('sen_plot')
            self._log('Hydration complete.')

        del results
        ac.update_from_state_object(state_obj)

    def handle_child_requests_form_overwrite(self, data: dict):
        """ Overwrites main state with parameter data from dict. """
        self.db.load_data_from_dict(data)
        self.newMessageEvent.emit("Data loaded successfully")

    @Slot()
    def shutdown(self):
        """Shuts down analysis thread (with timer) and exits app. """
        self._log("Beginning shutdown")
        self.thread.shutdown()
        # Wait while thread ends processes and shuts down.
        timer = gui_settings.SHUTDOWN_TIMER
        while timer > 0:
            if self.thread.is_shutdown:
                break
            time.sleep(1.0)
            timer -= 1
            self._log(f"{timer}...")
        self._log("Pool shutdown complete. Quitting app. Goodbye!")

        if self.q_app is not None:
            self.q_app.quit()  # exit main loop; sys.exit called in main.py

    @Slot()
    def print_state(self):
        self.db.print_state()

    @Slot()
    def print_history(self):
        self.db.print_history()

    @Slot()
    def open_data_directory(self):
        """Opens session directory in native file browser. """
        import webbrowser
        if self.db.session_dir.is_dir():
            webbrowser.open("file:///" + self.db.session_dir.as_posix())

    def _toggle_form_alert(self, msg, level=1):
        """Displays and populates form-wide alert.

        Parameters
        ----------
        msg : str
        level : {0, 1, 2, 3}
            Tier of alert: 0 is no alert (hide), 1 is informational, 2 is warning, 3 is error.

        """
        self.alertChanged.emit(msg, level)

    def _activate_validation(self):
        self.db.history_changed += self.check_form_valid

    def _deactivate_validation(self):
        self.db.history_changed -= self.check_form_valid

    # /////////////////////
    # SAVE / LOAD FUNCTIONS
    @Property(bool)
    def save_file_exists(self):
        """True if a filepath for save-file currently exists. TODO: check if file exists? """
        result = self.db.save_filepath is not None
        return result

    @Slot()
    def save_file(self):
        """Saves current state to existing savefile. """
        if self.save_file_exists:
            self.db.save_to_file(filepath=None)
            self.newMessageEvent.emit("File saved")

    @Slot(QUrl)
    def save_file_as(self, filepath: QUrl):
        """Saves current state to new savefile. """
        self.db.save_to_file(filepath.toLocalFile())
        self.newMessageEvent.emit("File saved")

    @Slot(QUrl)
    def load_save_file(self, filepath: QUrl):
        """Loads state from existing JSON save file. """
        filepath = filepath.toLocalFile()
        self.db.load_data_from_file(filepath)
        self.newMessageEvent.emit("Data loaded successfully")

    @Slot()
    def load_new_form(self):
        """Clears form and loads deterministic demo as new data. """
        self.db.clear_save_file()
        self.db.load_demo_file_data('det')
        self.newMessageEvent.emit("Form reset to default values")

    @Slot()
    def load_det_demo(self):
        """Loads deterministic analysis data from repo file. """
        self.db.load_demo_file_data('det')
        self.newMessageEvent.emit("Demo loaded")

    @Slot()
    def load_prb_demo(self):
        """Loads Probabilistic analysis data from repo file. """
        self.db.load_demo_file_data('prb')
        self.newMessageEvent.emit("Probabilistic demo loaded")

    @Slot()
    def load_sam_demo(self):
        """Loads sen (sample) analysis data from repo file. """
        self.db.load_demo_file_data('sam')
        self.newMessageEvent.emit("Sensitivity (samples) demo loaded")

    @Slot()
    def load_bnd_demo(self):
        """Loads sen (bnd) analysis data from repo file. """
        self.db.load_demo_file_data('bnd')
        self.newMessageEvent.emit("Sensitivity (bounds) demo loaded")

    @Property(str, constant=True)
    def about_str(self):
        about = ("Hydrogen Extremely Low Probability of Rupture (HELPR) is a modular probabilistic fracture mechanics "
                 "platform developed to assess structural integrity of natural gas infrastructure for transmission "
                 "and distribution of hydrogen natural gas blends."
                 "\n\nHELPR contains fatigue and fracture engineering "
                 "models allowing fast computations, while its probabilistic framework enables exploration and "
                 "characterization of the sensitivity of predicted outcomes to uncertainties of the pipeline "
                 "structure and operation.")
        return about

    @Property(str, constant=True)
    def copyright_str(self):
        result = ("Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS). "
                  "Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.\n\n"
                  "You should have received a copy of the BSD License along with HELPR.")
        return result

    @Property(str, constant=True)
    def version_str(self):
        """Current version of HELPR. """
        result = f"V{gui_settings.VERSION}"
        return result

    @Property(bool, constant=True)
    def is_debug_mode(self):
        """Whether debug/development mode is active. """
        return gui_settings.DEBUG

    # ///////////////////
    # UNDO / REDO HISTORY
    @Property(bool)
    def can_undo(self):
        """True if history is available to undo. """
        return self.db.can_undo()

    @Property(bool)
    def can_redo(self):
        """True if forward history is available to redo. """
        return self.db.can_redo()

    @Slot()
    def undo(self):
        """ Triggers rollback of single event in state history. """
        self.db.undo_state_change()

    @Slot()
    def redo(self):
        """ Triggers forward step of single event in state history. """
        self.db.redo_state_change()

    def _log(self, msg: str):
        log.info(f"State - {msg}")



