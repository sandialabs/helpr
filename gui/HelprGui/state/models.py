"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import json
import logging
import pprint
from datetime import datetime
from pathlib import Path

from parameters.models import ChoiceParameter, BoolParameter, Parameter, BasicParameter

import gui_settings as settings
from utils.events import Event
from utils.helpers import hround
from utils.units_of_measurement import Distance, SmallDistance, Pressure, Fracture, Temperature, Percent
from utils.distributions import Distributions, StudyTypes, Uncertainties, CycleUnits

from helpr import settings as api_settings
from helpr.physics import api
from helpr.utilities import plots


log = logging.getLogger("HELPR")


def do_analysis(analysis_id, params: dict, global_status_dict: dict):
    """
    Executes new analysis with dict of parameter values prepped for API consumption and queries for relevant results once complete.
    Also updates sub-process copy of settings.

    Parameters
    ----------
    analysis_id : int
        Unique analysis id
    params : dict
        Map of prepped parameters ready for analysis {slug: Characterization}

    Notes
    -----
    Called within new process via cloned state object.
    Dict is used to avoid sub-processing issues with cloning state object.

    """
    # Update this process' version of GUI settings
    settings.SESSION_DIR = params['session_dir']

    # multiprocessing does not support logging to same file. Must implement queue handler if this functionality is desired.
    proc_log = logging.getLogger(__name__)
    proc_log.setLevel(logging.INFO)

    study_type = params['study_type']
    if study_type == 'bnd':
        api_study_type = 'bounding'
    elif study_type == 'sam':
        api_study_type = 'sensitivity'
    elif study_type == 'prb':
        api_study_type = 'lhs'
    else:
        api_study_type = 'deterministic'

    # create output dir for this analysis
    output_dirname = f'A{analysis_id:03d}_{study_type}'
    output_dir = settings.SESSION_DIR.joinpath(output_dirname)
    Path.mkdir(output_dir, parents=True, exist_ok=True)

    # Update instance of api settings
    api_settings.OUTPUT_DIR = output_dir
    api_settings.USING_GUI = True
    # pass manually instead of accessing from settings since dir name is based on time and may not be present in settings or idempotent
    api_settings.SESSION_DIR = settings.SESSION_DIR
    api_settings.GUI_STATUS_DICT = global_status_dict
    api_settings.ANALYSIS_ID = analysis_id

    try:
        # param dict keys are slugs and must match api kwarg naming
        analysis = api.CrackEvolutionAnalysis(outer_diameter=params['outer_diameter'],
                                              wall_thickness=params['wall_thickness'],
                                              flaw_depth=params['flaw_depth'],
                                              max_pressure=params['max_pressure'],
                                              min_pressure=params['min_pressure'],
                                              temperature=params['temperature'],
                                              volume_fraction_h2=params['volume_fraction_h2'],
                                              yield_strength=params['yield_strength'],
                                              fracture_resistance=params['fracture_resistance'],
                                              flaw_length=params['flaw_length'],

                                              aleatory_samples=params['aleatory_samples'],
                                              epistemic_samples=params['epistemic_samples'],
                                              random_seed=params['seed'],
                                              sample_type=api_study_type,
                                              )
        analysis.perform_study()

    except TypeError as err:
        proc_log.exception("TypeError occurred during analysis")
        results = {
            'status': -1,
            'analysis_id': analysis_id,
            'error': err,
            'message': "Incompatible input(s) for selected analysis type"
        }
        return results

    except ValueError as err:
        proc_log.exception("ValueError occurred during analysis")
        results = {
            'status': -1,
            'analysis_id': analysis_id,
            'error': err,
            'message': str(err)
        }
        return results
    except Exception as err:
        proc_log.exception("Exception occurred during analysis")
        results = {
            'status': -1,
            'analysis_id': analysis_id,
            'error': err,
            'message': "Error during analysis - check log for details"
        }
        return results

    # Process and store result data like plot filepaths
    crack_fpath = ""
    ex_rates_fpath = ""
    fad_fpath = ""
    ensemble_fpath = ""
    cycle_fpath = ""
    cycle_cbv_fpaths = []
    pdf_fpath = ""
    cdf_fpath = ""
    sen_fpath = ""

    # check if analysis was canceled
    if api_settings.RUN_STATUS == api_settings.Status.STOPPED:
        results = {
            'status': 2,
            'analysis_id': analysis_id,
            'message': "Analysis canceled successfully"
        }
        return results

    if study_type == 'det':
        analysis.postprocess_single_crack_results(save_figs=True)
        if params['create_crack_growth_plot']:
            crack_fpath = analysis.crack_growth_plot

        if params['create_exercised_rates_plot']:
            # ex_rates_fpath = analysis.ex_rates_plot
            ex_rates_fpath = analysis.get_design_curve_plot()

        if params['create_failure_assessment_diagram']:
            analysis.assemble_failure_assessment_diagram(save_fig=True)
            fad_fpath = analysis.failure_assessment_plot

    elif study_type == 'prb':
        analysis.postprocess_single_crack_results(single_pipe_index=2)
        # if params['create_crack_growth_plot']:
        #     crack_fpath = analysis.crack_growth_plot
        if params['create_failure_assessment_diagram']:
            analysis.assemble_failure_assessment_diagram(save_fig=True)
            fad_fpath = analysis.failure_assessment_plot

        plotted_variable = 'Cycles to a(crit)'
        if params['create_ensemble_plot']:
            ensemble_fpath = plots.plot_pipe_life_ensemble(analysis, criteria=plotted_variable, save_fig=True)
        if params['create_cycle_plot']:
            cycle_fpath = plots.plot_cycle_life_criteria_scatter(analysis, criteria=plotted_variable, save_fig=True)
            # cycle_cbv_fpaths = plots.plot_cycle_life_criteria_scatter(analysis, criteria=plotted_variable,
            #                                                           color_by_variable=True, save_fig=True)
        if params['create_pdf_plot']:
            pdf_fpath = plots.plot_cycle_life_pdfs(analysis, criteria=plotted_variable, save_fig=True)
        if params['create_cdf_plot']:
            cdf_fpath = plots.plot_cycle_life_cdfs(analysis, criteria=plotted_variable, save_fig=True)

    elif study_type == 'bnd':
        if params['create_sensitivity_plot']:
            sen_fpath = plots.plot_sensitivity_results(analysis, save_fig=True)

    elif study_type == 'sam':
        if params['create_sensitivity_plot']:
            sen_fpath = plots.plot_sensitivity_results(analysis, save_fig=True)

    analysis.save_results(output_dir=output_dir)

    results = {
        'status': 1,
        'analysis_id': analysis_id,
        'crack_growth_plot': crack_fpath,
        'ex_rates_plot': ex_rates_fpath,
        'ensemble_plot': ensemble_fpath,
        'cycle_plot': cycle_fpath,
        # 'cycle_cbv_plots': cycle_cbv_fpaths,
        'pdf_plot': pdf_fpath,
        'cdf_plot': cdf_fpath,
        'fad_plot': fad_fpath,
        'sen_plot': sen_fpath,
        'output_dir': output_dir,
    }

    # return instance of state from other process
    return results


class State(object):
    """Representation of analysis parameter data.

    Attributes
    ----------
    out_diam : Parameter
        Pipe outer diameter.
    thickness : Parameter
        Pipe thickness.
    crack_dep : Parameter
        Crack depth.
    crack_len : Parameter
        Crack length.
    p_min : Parameter
        Minimum pressure.
    p_max : Parameter
        Maximum pressure.
    temp : Parameter
        Temperature.
    vol_h2 : Parameter
        H2 volume.
    yield_str : Parameter
        Yield strength.
    frac_resist : Parameter
        Fracture resistance.
    n_ale : BasicParameter
        Number of aleatory samples.
    n_epi : BasicParameter
        Number of epistemic samples.
    seed : BasicParameter
        Random seed.
    study_type : ChoiceParameter
        Analysis sample type (deterministic, Probabilistic, sensitivity (bounds), or sensitivity (sample)).
    cycle_units : ChoiceParameter
        Active cycle time units.
    session_dir : Path
        Filepath to directory containing files for this application session.
    save_filepath : Path or None
        Last-used filepath to save file for easy re-saving

    analysis_id : int or None
        Unique identifier for analysis associated with this state, if it represents a completed analysis.
    started_at : datetime or None
        Time at which analysis began.
    finished_at : datetime or None
        Time at which analysis finished.
    is_finished : bool
        True if associated analysis finished.
    has_error : bool
        True if analysis encountered error.
    error_message : str
        Error message describing error encountered during analysis.
    error : Exception
        Error describing error encountered during analysis.
    has_warning : bool
        True if analysis encountered warning.
    warning_message : str
        Warning message describing error encountered during analysis.

    do_crack_growth_plot : BoolParameter
        Whether analysis shall create a crack growth plot.
    crack_growth_plot : str
        String filepath to crack growth plot (deterministic analysis only).
    do_fad_plot : BoolParameter
        Whether analysis shall create a failure assessment diagram
    fad_plot : str
        String filepath to failure assessment diagram (deterministic and Probabilistic analysis only).
    do_ex_rates_plot : BoolParameter
        Whether analysis shall create a design curve plot.
    ex_rates_plot : str
        String filepath to design curve plot (deterministic analysis only).
    do_ensemble_plot : BoolParameter
        Whether analysis shall create a pipe life ensemble (crack growth) plot.
    ensemble_plot : str
        String filepath to ensemble plot (Probabilistic analysis only).
    do_cycle_plot : BoolParameter
        Whether analysis shall create a cycle plot.
    cycle_plot : str
        String filepath to cycle plot (Probabilistic analysis only).
    do_pdf_plot : BoolParameter
        Whether analysis shall create a PDF plot.
    pdf_plot : str
        String filepath to PDF plot (Probabilistic analysis only).
    do_cdf_plot : BoolParameter
        Whether analysis shall create a CDF plot.
    cdf_plot : str
        String filepath to CDF plot (Probabilistic analysis only).
    do_sen_plot : BoolParameter
        Whether analysis shall create a sensitivity plot.
    sen_plot : str
        String filepath to sensitivity plot (bound and sensitivity analysis only).
    cycle_cbv_plots : List
        List of string filepaths to CBV cycle plots (Probabilistic analysis only).
    history_changed : Event
        Emitted when state history is modified.

    Notes
    -----
    A single "master" State instance is created and bound to the form UI.
    This state data is then cloned for each analysis to preserve the submitted state, resulting in child states for each completed analysis.

    """
    out_diam: Parameter
    thickness: Parameter
    crack_dep: Parameter
    crack_len: Parameter
    p_min: Parameter
    p_max: Parameter
    temp: Parameter
    vol_h2: Parameter
    yield_str: Parameter
    frac_resist: Parameter
    n_ale: BasicParameter
    n_epi: BasicParameter
    seed: BasicParameter
    study_type: ChoiceParameter
    cycle_units: ChoiceParameter

    session_dir: Path
    _output_dir: Path or None
    _cwd_dir: Path
    _demo_dir: Path
    _float_params: list
    _bool_params: list
    _basic_params: list

    save_filepath: Path or None  # track last-used save-file to enable easy resaving

    # Properties used during analysis, not by main state object.
    analysis_id: int or None = None
    started_at: datetime or None = None
    finished_at: datetime or None = None
    is_finished: bool = False

    has_error: bool = False
    error_message: str = ""
    error: Exception = None
    has_warning: bool = False
    warning_message: str = ""

    was_canceled: bool = False

    do_crack_growth_plot: BoolParameter
    crack_growth_plot: str = ""
    do_fad_plot: BoolParameter
    fad_plot: str = ""
    do_ex_rates_plot: BoolParameter
    ex_rates_plot: str = ""

    do_ensemble_plot: BoolParameter
    ensemble_plot: str = ""
    do_cycle_plot: BoolParameter
    cycle_plot: str = ""
    do_pdf_plot: BoolParameter
    pdf_plot: str = ""
    do_cdf_plot: BoolParameter
    cdf_plot: str = ""
    cycle_cbv_plots: []

    do_sen_plot: BoolParameter
    sen_plot: str = ""

    # Track changes to data over time. Each entry is dict (or JSON?) describing data state before change.
    _history: list
    _redo_history: list
    _record_changes = True
    history_changed: Event

    def __init__(self):
        """Initializes parameter values and history tracking. """
        super().__init__()
        self._log('Initializing data-store')
        self.history_changed = Event()  # any change occurs; instance-only

        self.session_dir = settings.SESSION_DIR
        self._cwd_dir = settings.CWD_DIR
        self._demo_dir = self._cwd_dir.joinpath('assets').joinpath('demo')
        self._output_dir = None
        self._history = []
        self._redo_history = []
        self.clear_save_file()

        self.seed = BasicParameter('Random seed', slug='seed', value=1234567)
        self.n_epi = BasicParameter('Epistemic samples', value=0)
        self.cycle_units = ChoiceParameter('Cycle time units', choices=CycleUnits, value=CycleUnits.hr)

        self.do_crack_growth_plot = BoolParameter('Create crack growth plot', True)
        self.do_ex_rates_plot = BoolParameter('Create exercised rates plot', True)
        self.do_fad_plot = BoolParameter('Create failure assessment diagram', True)
        self.do_ensemble_plot = BoolParameter('Create ensemble plot', True)
        self.do_cycle_plot = BoolParameter('Create cycle plot', True)
        self.do_pdf_plot = BoolParameter('Create PDF plot', True)
        self.do_cdf_plot = BoolParameter('Create CDF plot', True)
        self.do_sen_plot = BoolParameter('Create sensitivity plot', True)

        defaults = 'det'
        if defaults == 'det':
            self.study_type = ChoiceParameter('Study type', choices=StudyTypes, value=StudyTypes.det)
            self.out_diam = Parameter('Outer diameter', unit=Distance.inch, value=36)
            self.thickness = Parameter('Wall thickness', unit=Distance.inch, value=0.406, max_value=3,
                                       tooltip='Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.p_max = Parameter('Max pressure', unit=Pressure.psi, value=850)
            self.p_min = Parameter('Min pressure', unit=Pressure.psi, value=638)
            self.temp = Parameter('Temperature', unit=Temperature.k, value=293, min_value=230, max_value=330)
            self.vol_h2 = Parameter('H2 volume fraction', slug='volume_fraction_h2', value=1, max_value=1, label_rtf="H<sub>2</sub> volume fraction")
            self.yield_str = Parameter('Yield strength', unit=Pressure.psi, value=52_000)
            self.frac_resist = Parameter('Fracture resistance', unit_type=Fracture, value=55)
            self.crack_dep = Parameter('Crack depth', slug='flaw_depth', unit=Percent.p, value=25, min_value=0.1, max_value=80)
            self.crack_len = Parameter('Crack length', slug='flaw_length', unit_type=SmallDistance, value=0.04)
            self.n_ale = BasicParameter('Aleatory samples', value=0)
            self.n_ale.toggle_enabled(False)
            self.n_epi.toggle_enabled(False)

        elif defaults == 'prb':
            # matches demo_prob_v2 notebook
            self.study_type = ChoiceParameter('Study type', choices=StudyTypes, value=StudyTypes.prb)
            self.out_diam = Parameter('Outer diameter', unit=Distance.inch, distr=Distributions.uni, value=22, a=21.9, b=22.1)
            self.thickness = Parameter('Wall thickness', unit=Distance.inch, distr=Distributions.uni, value=0.281,
                                       a=0.271, b=0.291, max_value=3,
                                       tooltip='Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.yield_str = Parameter('Yield strength', unit=Pressure.psi, value=52_000)
            self.frac_resist = Parameter('Fracture resistance', value=55, unit_type=Fracture)
            self.p_max = Parameter('Max pressure', unit=Pressure.psi, distr=Distributions.nor, value=850, a=850, b=20)
            self.p_min = Parameter('Min pressure', unit=Pressure.psi, distr=Distributions.nor, value=638, a=638, b=20)
            self.temp = Parameter('Temperature', unit=Temperature.k, distr=Distributions.uni, value=293, a=285, b=300,
                                  min_value=230, max_value=330)
            self.vol_h2 = Parameter('H2 volume fraction', slug='volume_fraction_h2', value=1, max_value=1,
                                    label_rtf="H<sub>2</sub> volume fraction")
            self.crack_dep = Parameter('Crack depth', slug='flaw_depth', unit=Percent.p, distr=Distributions.uni, value=32, a=28, b=36, min_value=0.1, max_value=80)
            self.crack_len = Parameter('Crack length', slug='flaw_length', unit_type=SmallDistance, distr=Distributions.uni, value=0.02, a=0.01, b=0.03)
            self.n_ale = BasicParameter('Aleatory samples', value=50)

        elif defaults in ['sam', 'bnd']:
            self.out_diam = Parameter('Outer diameter', unit=Distance.inch, distr=Distributions.det, value=36)
            self.thickness = Parameter('Wall thickness', unit=Distance.inch, distr=Distributions.det, value=0.406, max_value=3,
                                       tooltip = 'Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.yield_str = Parameter('Yield strength', unit=Pressure.psi, value=52_000)
            self.frac_resist = Parameter('Fracture resistance', value=55, unit_type=Fracture)
            self.p_max = Parameter('Max pressure', unit=Pressure.psi, distr=Distributions.nor, value=850, a=850, b=20)
            self.p_min = Parameter('Min pressure', unit=Pressure.psi, distr=Distributions.nor, value=638, a=638, b=20)
            self.temp = Parameter('Temperature', unit=Temperature.k, distr=Distributions.uni, value=293, a=285, b=300,
                                  min_value=230, max_value=330)
            self.vol_h2 = Parameter('H2 volume fraction', slug='volume_fraction_h2', distr=Distributions.uni, value=0.1,
                                    a=0, b=0.2, max_value=1, label_rtf="H<sub>2</sub> volume fraction")
            self.crack_dep = Parameter('Crack depth', slug='flaw_depth', unit=Percent.p, distr=Distributions.uni, value=25, a=20, b=30, min_value=0.1, max_value=80)
            self.crack_len = Parameter('Crack length', slug='flaw_length', unit_type=SmallDistance, distr=Distributions.det, value=0.03)

            if defaults == 'sam':
                self.study_type = ChoiceParameter('Study type', choices=StudyTypes, value=StudyTypes.sam)
                self.n_ale = BasicParameter('Aleatory samples', value=50)

            elif defaults == 'bnd':
                self.study_type = ChoiceParameter('Study type', choices=StudyTypes, value=StudyTypes.bnd)
                self.n_ale = BasicParameter('Aleatory samples', value=0)

        # list parameters for easy iteration
        self._float_params = [self.out_diam, self.thickness, self.yield_str, self.frac_resist, self.p_max, self.p_min, self.temp,
                              self.vol_h2, self.crack_dep, self.crack_len]
        self._basic_params = [self.n_ale, self.n_epi, self.seed]
        self._bool_params = [self.do_crack_growth_plot, self.do_fad_plot, self.do_ex_rates_plot, self.do_ensemble_plot,
                             self.do_cycle_plot, self.do_pdf_plot, self.do_cdf_plot, self.do_sen_plot]

        for param in self._float_params:
            param.changed += lambda x: self._record_state_change()
        for param in self._basic_params:
            param.changed += lambda x: self._record_state_change()
        for param in self._bool_params:
            param.changed += lambda x: self._record_state_change()

        self.cycle_units.changed += lambda x: self._record_state_change()

        # reset sampling counts in addition to recording state
        self.study_type.changed += self._handle_study_type_changed

        # record initial state as first entry
        self._record_state_change()

    # ==============================
    # ==== PARAMETER VALIDATION ====
    def check_valid(self) -> (int, str):
        """Validates parameter values in form-wide manner. For example, validation of a parameter which depends on another parameter
        is done here.

        Notes
        -----
        Checks for errors first, then warnings, so most serious is shown first.

        Returns
        -------
        {0, 1, 2, 3}
            Tier of alert: 0 is no alert (hide), 1 is informational, 2 is warning, 3 is error.
        str
            Descriptive message if form has warning or error.

        """
        study_type = self.study_type.get_value()

        thickness = self.thickness.value_raw
        thick_max = self._thickness_max_val()
        if thickness > thick_max:
            return 3, 'Pipe thickness must be <= pipe radius and <= 3 in (76.2 mm)'

        if self.p_max.value_raw <= self.p_min.value_raw:
            return 3, 'Max pressure must be greater than minimum pressure'

        crack_len_min = 2 * (self.crack_dep.value_raw / 100.) * self.thickness.value_raw
        crack_len_min_disp = hround(self.crack_len.unit_type.convert(crack_len_min, new=self.crack_len.unit), p=3)
        if self.crack_len.value_raw <= crack_len_min:
            return 3, f'Crack length must be greater than 2 x crack depth x pipe thickness ({crack_len_min_disp} {self.crack_len.unit})'

        if study_type in ['prb', 'sam']:
            # ensure aleatory and epistemic counts and usage matches
            has_ale = False
            has_epi = False
            ale_samples = self.n_ale.value
            epi_samples = self.n_epi.value
            for par in self._float_params:
                if par.distr != 'det' and par.uncertainty == 'ale':
                    has_ale = True
                elif par.distr != 'det' and par.uncertainty == 'epi':
                    has_epi = True

            if has_ale and ale_samples == 0:
                return 3, 'Aleatory samples do not match inputted parameters'

            if not has_ale and ale_samples > 0:
                return 3, 'Aleatory samples require corresponding parameter distribution'

            if has_epi and epi_samples == 0:
                return 3, 'Epistemic samples do not match inputted parameters'

            if not has_epi and epi_samples > 0:
                return 3, 'Epistemic samples require corresponding parameter distribution'

            if not has_ale and not has_epi:
                return 2, 'Set at least one parameter to probabilistic for Probabilistic study'

            if (has_ale and ale_samples >= 100) or (has_epi and epi_samples >= 100):
                return 2, 'large sample size may result in extended analysis time'

        elif study_type == 'det':
            for par in self._float_params:
                if par.distr != 'det':
                    name = par.label.lower()
                    return 2, f"Probabilistic parameter value for {name} ignored in deterministic study"

        # Check warnings after errors

        if self.yield_str.value_raw >= 900:
            return 2, 'high yield strength found - verify inputs before submitting'

        if self.frac_resist.value_raw >= 500:
            return 2, 'high fracture resistance found - verify inputs before submitting'

        if self.p_max.value_raw >= 100:
            return 2, 'high max pressure found - verify inputs before submitting'

        return 0, ''

    def _thickness_max_val(self) -> float:
        """Max pipe thickness is either 3in or half the diameter. """
        max1 = self.out_diam.value_raw / 2.
        max2 = self.out_diam.unit_type.convert(3, old=Distance.inch, new=Distance.m)
        result = max1 if max1 < max2 else max2
        return result

    def _handle_study_type_changed(self, study_type: ChoiceParameter):
        """Refresh form and available parameters when analysis sample type changes. """
        if self.study_type.get_value() == 'det':
            for attr_name in self.__dict__:
                attr = getattr(self, attr_name)
                if type(attr) == Parameter:
                    if attr.distr != 'det':
                        attr.distr = 'det'

            self.n_ale.toggle_enabled(False)
            self.n_ale.set_from_model(0)
            self.n_epi.toggle_enabled(False)
            self.n_epi.set_from_model(0)

        else:
            self.n_ale.toggle_enabled(True, silent=False)
            self.n_epi.toggle_enabled(True, silent=False)

        self._record_state_change()

    def set_id(self, val):
        """Updates analysis ID to match submitted analysis. """
        self.analysis_id = val

    def set_output_dir(self, val):
        """Assigns filepath object to directory containing analysis file outputs. """
        self._output_dir = val

    def get_output_dir(self):
        """Filepath to directory containing files for analysis output. Child directory of `session_dir`. """
        if self._output_dir is not None and type(self._output_dir) != str and self._output_dir.is_dir():
            return self._output_dir
        else:
            return None

    # ===========================================
    # ========= DATA CONVERSION & PARSING =======
    def load_data_from_file(self, filepath):
        """Loads state parameter data from specified filepath to JSON file.

        Parameters
        ----------
        filepath : Path or str
            Path to file containing complete parameter JSON data to load.

        Notes
        -----
        .HPR filetype is alias for JSON filetype.

        """
        if type(filepath) == str:
            filepath = Path(filepath)

        recording = self._record_changes
        self._record_changes = False  # Only do 1 record at end

        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)
                self._from_dict(state_dict)
            self._record_changes = True
            self._record_state_change()
        else:
            self._log(f"Can't load data - file not found {filepath.as_posix()}")
        self._record_changes = recording

    def load_data_from_dict(self, data: dict):
        """Overwrites state parameter data from complete dict as a single history state change.

        Parameters
        ----------
        data : dict
            Dictionary containing data for all parameters, including value, selected unit, etc.

        """
        recording = self._record_changes
        self._record_changes = False  # Only do 1 record at end
        self._from_dict(data)
        # update history
        self._record_changes = True
        self._record_state_change()
        # restore tracking state
        self._record_changes = recording

    def save_to_file(self, filepath=None):
        """Saves current state to file. Overwrites current save-file path if different.

        Parameters
        ----------
        filepath : str or None
            Full filepath of possibly non-existent .hpr (JSON) file in which to output data.

        """
        if filepath is None or filepath == self.save_filepath:
            filepath = self.save_filepath

        else:  # new filepath, i.e. "Save As"
            filepath = Path(filepath)
            self.save_filepath = filepath

        data = self.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def clear_save_file(self):
        """Empties current save filepath. """
        self.save_filepath = None

    def get_prepped_param_dict(self):
        """Returns dict of parameters prepared for analysis submission. """
        data = {
            'cycle_units': self.cycle_units.get_value(),
            'study_type': self.study_type.get_value(),
            'session_dir': self.session_dir,  # sub-process must not try to
            'output_dir': None,
        }

        for param in self._basic_params:
            data[param.slug] = param.get_prepped_value()
        for param in self._float_params:
            data[param.slug] = param.get_prepped_value()
        for param in self._bool_params:
            data[param.slug] = param.get_prepped_value()

        return data

    def to_dict(self) -> dict:
        """Returns representation of this state as dict of parameter dicts. """
        result = {
            'study_type': self.study_type.to_dict(),
            'cycle_units': self.cycle_units.to_dict(),
        }

        for param in self._basic_params:
            result[param.slug] = param.to_dict()
        for param in self._float_params:
            result[param.slug] = param.to_dict()
        for param in self._bool_params:
            result[param.slug] = param.to_dict()

        return result

    def _from_dict(self, data: dict):
        """Overwrites state analysis parameter data from dict containing all parameters.

        Parameters
        ----------
        data : dict
            Analysis parameter data with keys matching internal snake_case naming.

        """
        # Verify all parameters present
        expected_keys = self.to_dict().keys()
        for key in expected_keys:
            if key not in data:
                raise ValueError(f'Required key {key} not found in state data {data}')

        for param in self._basic_params:
            param.from_dict(data[param.slug])

        for param in self._float_params:
            param.from_dict(data[param.slug])

        for param in self._bool_params:
            param.from_dict(data[param.slug])

        self.study_type.from_dict(data['study_type'])
        self.cycle_units.from_dict(data['cycle_units'])

    # ======================================
    # ========= HISTORY RECORDING ==========
    def _record_state_change(self):
        """Records full state to history as dict of params (also dicts) """
        if not self._record_changes:
            return

        current = self.to_dict()
        # ensure state has actually changed
        if self._history:
            prev = self._history[-1]
            if current == prev:
                return

        self._redo_history = []
        self._history.append(current)
        self.history_changed.notify(self)

    def undo_state_change(self):
        """Restores previous state from history and stores the change to redo_history list. """
        recording = self._record_changes
        self._record_changes = False

        if self.can_undo():
            current = self._history.pop(-1)
            self._redo_history.append(current)
            new_current = self._history[-1]
            self._from_dict(new_current)

        self._record_changes = recording
        self.history_changed.notify(self)

    def redo_state_change(self):
        """Undoes previous undo call. """
        recording = self._record_changes
        self._record_changes = False

        if self.can_redo():
            dct = self._redo_history.pop(-1)
            self._history.append(dct)
            self._from_dict(dct)

        self._record_changes = recording
        self.history_changed.notify(self)

    def can_undo(self) -> bool:
        """Flag indicating whether there is history to return to. """
        return len(self._history) > 1

    def can_redo(self) -> bool:
        """Flag indicating whether there is forward history available for restoration. """
        return bool(self._redo_history)

    # ======================
    # ==== LOGGING & DEV ===
    def _log(self, msg):
        log.info(f'State - {msg}')

    def print_state(self):
        pass
        # logging.warning(PPRINT.pprint(self.to_dict()))

    def print_history(self):
        pass
        # for i, item in enumerate(self._history):
        #     print(f"HISTORY {i}")
        #     PPRINT.pprint(item)

    def load_demo_file_data(self, label='det'):
        """Loads sample data from specified demo file. """
        if label == 'prb':
            demo_file = self._demo_dir.joinpath('prb_demo.hpr')
        elif label == 'bnd':
            demo_file = self._demo_dir.joinpath('bnd_demo.hpr')
        elif label == 'sam':
            demo_file = self._demo_dir.joinpath('sam_demo.hpr')
        else:
            demo_file = self._demo_dir.joinpath('det_demo.hpr')
        self.load_data_from_file(demo_file)

