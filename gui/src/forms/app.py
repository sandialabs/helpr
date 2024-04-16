"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import copy
import logging

from helprgui.models.models import ModelBase
from helprgui.forms import forms

from PySide6.QtCore import Slot, QObject
from PySide6.QtQml import QmlElement

import app_settings
from models.models import State, do_crack_evolution_analysis
from forms.results import CrackEvolutionResultsForm


QML_IMPORT_NAME = f"{ app_settings.APPNAME_LOWER}.classes"
QML_IMPORT_MAJOR_VERSION = 1

log = logging.getLogger(app_settings.APPNAME)


@QmlElement
class HelprAppForm(forms.AppForm):
    """Top-level manager of GUI form, analysis thread, and analysis requests.

    Notes
    -----
    Qt signals use camelCase for consistency with QML coding style.

    """

    def __init__(self):
        """Initializes backend store and thread controller. """
        super().__init__(model_class=State)

        self._about_str = ("Hydrogen Extremely Low Probability of Rupture (HELPR) is a modular probabilistic fracture mechanics "
                           "platform developed to assess structural integrity of natural gas infrastructure for transmission "
                           "and distribution of hydrogen natural gas blends."
                           "\n\nHELPR contains fatigue and fracture engineering "
                           "models allowing fast computations, while its probabilistic framework enables exploration and "
                           "characterization of the sensitivity of predicted outcomes to uncertainties of the pipeline "
                           "structure and operation.")

        self._copyright_str = ("Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS). "
                               "Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.\n\n"
                               "You should have received a copy of the BSD License along with HELPR.")

    @Slot()
    def request_analysis(self):
        """Handles analysis request by submitting valid data to thread and updating queue.

        Note: to accommodate additional forms, just pass an id that determines the form type and callbacks.

        """
        status = self.check_form_valid()
        if not status:
            return

        # must remove listeners on state, otherwise it will attempt (and fail) to deepcopy this object as well
        self._deactivate_validation()
        db_copy = copy.deepcopy(self.db)

        if db_copy.analysis_name.value in ["", None]:
            db_copy.analysis_name.value = f"Analysis {self.thread.get_curr_id() + 1} - {db_copy.study_type.get_value_display()}"

        analysis_id = self.thread.request_new_analysis(db_copy,
                                                       do_crack_evolution_analysis,
                                                       self.analysis_started_callback,
                                                       self.analysis_finished_callback)

        if analysis_id is not None:
            # Prep for results display with necessary data; won't have full access until analysis is complete.
            ac = CrackEvolutionResultsForm(analysis_id, db_copy)
            ac.request_overwrite_event += self.handle_child_requests_form_overwrite
            self.result_forms[analysis_id] = ac
            # add view to visible queue
            self.queue_controller.handle_new_analysis(ac)

        self._activate_validation()

    def analysis_finished_callback(self, state_obj: type(ModelBase), results: dict):
        """Updates state of returned analysis with finalized data and sends it to its AnalysisController for final processing.
        Called via thread after processing pool finishes executing analysis.

        Parameters
        ----------
        state_obj : State
            state model object containing parameter and result data for specified analysis.

        results : dict
            analysis results including data and plots.

        """
        result_form = self.result_forms[state_obj.analysis_id]

        status = results['status']
        if status == -1:
            self._log('Skipping hydration - analysis encountered error.')
            state_obj.has_error = True
            state_obj.error = results.pop('error', None)
            state_obj.error_message = results.pop('message', '')

        elif status == 2:
            # Analysis canceled by user
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

        del results
        result_form.update_from_state_object(state_obj)

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
