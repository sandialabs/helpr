"""
Copyright 2024 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import logging
from pathlib import Path

import numpy as np

from helprgui.models.fields import ChoiceField, BoolField, IntField, StringField, NumField
from helprgui.models.fields_probabilistic import UncertainField

import app_settings
from helprgui.models.models import ModelBase
from helprgui.utils import helpers
from helprgui.utils.helpers import hround, InputStatus, ValidationResponse
from helprgui.utils.units_of_measurement import Distance, SmallDistance, Pressure, Fracture, Temperature, Percent
from helprgui.utils.distributions import Distributions, StudyTypes, Uncertainties, CycleUnits

from helpr import settings as api_settings
from helpr.physics import api
from helpr.utilities import plots

log = logging.getLogger(app_settings.APPNAME)


def do_crack_evolution_analysis(analysis_id, params: dict, global_status_dict: dict):
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
    app_settings.SESSION_DIR = params['session_dir']

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
    als_name = helpers.convert_string_to_filename(params['analysis_name'])
    now_str = helpers.get_now_str()
    output_dirname = f'{now_str}_A{analysis_id:03d}_{als_name[0:10]}'
    output_dir = app_settings.SESSION_DIR.joinpath(output_dirname)
    Path.mkdir(output_dir, parents=True, exist_ok=True)

    # Update instance of api settings
    api_settings.OUTPUT_DIR = output_dir
    api_settings.USING_GUI = True
    # pass manually since dir name based on time and may not be present in settings or idempotent
    api_settings.SESSION_DIR = app_settings.SESSION_DIR
    api_settings.GUI_STATUS_DICT = global_status_dict
    api_settings.ANALYSIS_ID = analysis_id

    results = {'status': 1}
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

    except ValueError as err:
        proc_log.exception("ValueError occurred during analysis")
        results = {
            'status': -1,
            'analysis_id': analysis_id,
            'error': err,
            'message': str(err)
        }
    except Exception as err:
        proc_log.exception("Exception occurred during analysis")
        results = {
            'status': -1,
            'analysis_id': analysis_id,
            'error': err,
            'message': "Error during analysis - check log for details"
        }

    if results['status'] == -1:
        # analysis failed
        try:
            output_dir.rmdir()  # only removes empty dir
        except Exception:
            pass
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
        try:
            output_dir.rmdir()
        except Exception:
            pass
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


def _calc_intermediate_params(params, study_type):
    """ Update stored float intermediate parameter values based on sample type. """
    results = None
    try:
        als = api.CrackEvolutionAnalysis(outer_diameter=params['outer_diameter'],
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
                                         sample_type=study_type)
        if als.nominal_intermediate_variables.keys():
            api_dict = als.nominal_intermediate_variables
        else:
            api_dict = als.sampling_intermediate_variables

        results = {
            'r_ratio': api_dict['r_ratio'][0],
            'f_ratio': api_dict['fugacity_ratio'][0],
            'smys': api_dict['%SMYS'][0],
            'a_c': api_dict['a/2c'][0],
            't_r': api_dict['t/R'][0],
            'a_m': api_dict['a (m)'][0],
        }
    except Exception as err:
        pass

    return results


class State(ModelBase):
    """Representation of analysis parameter data.

    Attributes
    ----------
    out_diam : UncertainField
        Pipe outer diameter.
    thickness : UncertainField
        Pipe thickness.
    crack_dep : UncertainField
        Crack depth.
    crack_len : UncertainField
        Crack length.
    p_min : UncertainField
        Minimum pressure.
    p_max : UncertainField
        Maximum pressure.
    temp : UncertainField
        Temperature.
    vol_h2 : UncertainField
        H2 volume.
    yield_str : UncertainField
        Yield strength.
    frac_resist : UncertainField
        Fracture resistance.
    n_ale : IntField
        Number of aleatory samples.
    n_epi : IntField
        Number of epistemic samples.
    seed : IntField
        Random seed.
    study_type : ChoiceField
        Analysis sample type (deterministic, Probabilistic, sensitivity (bounds), or sensitivity (sample)).
    cycle_units : ChoiceField
        Active cycle time units.

    do_crack_growth_plot : BoolField
        Whether analysis shall create a crack growth plot.
    crack_growth_plot : str
        String filepath to crack growth plot (deterministic analysis only).
    do_fad_plot : BoolField
        Whether analysis shall create a failure assessment diagram
    fad_plot : str
        String filepath to failure assessment diagram (deterministic and Probabilistic analysis only).
    do_ex_rates_plot : BoolField
        Whether analysis shall create a design curve plot.
    ex_rates_plot : str
        String filepath to design curve plot (deterministic analysis only).
    do_ensemble_plot : BoolField
        Whether analysis shall create a pipe life ensemble (crack growth) plot.
    ensemble_plot : str
        String filepath to ensemble plot (Probabilistic analysis only).
    do_cycle_plot : BoolField
        Whether analysis shall create a cycle plot.
    cycle_plot : str
        String filepath to cycle plot (Probabilistic analysis only).
    do_pdf_plot : BoolField
        Whether analysis shall create a PDF plot.
    pdf_plot : str
        String filepath to PDF plot (Probabilistic analysis only).
    do_cdf_plot : BoolField
        Whether analysis shall create a CDF plot.
    cdf_plot : str
        String filepath to CDF plot (Probabilistic analysis only).
    do_sen_plot : BoolField
        Whether analysis shall create a sensitivity plot.
    sen_plot : str
        String filepath to sensitivity plot (bound and sensitivity analysis only).
    cycle_cbv_plots : List
        List of string filepaths to CBV cycle plots (Probabilistic analysis only).

    Notes
    -----
    Same state object can back multiple analysis form types.

    """
    out_diam: UncertainField
    thickness: UncertainField
    crack_dep: UncertainField
    crack_len: UncertainField
    p_min: UncertainField
    p_max: UncertainField
    temp: UncertainField
    vol_h2: UncertainField
    yield_str: UncertainField
    frac_resist: UncertainField
    n_ale: IntField
    n_epi: IntField
    seed: IntField
    study_type: ChoiceField
    cycle_units: ChoiceField

    do_crack_growth_plot: BoolField
    crack_growth_plot: str = ""
    do_fad_plot: BoolField
    fad_plot: str = ""
    do_ex_rates_plot: BoolField
    ex_rates_plot: str = ""

    do_ensemble_plot: BoolField
    ensemble_plot: str = ""
    do_cycle_plot: BoolField
    cycle_plot: str = ""
    do_pdf_plot: BoolField
    pdf_plot: str = ""
    do_cdf_plot: BoolField
    cdf_plot: str = ""
    cycle_cbv_plots: []

    do_sen_plot: BoolField
    sen_plot: str = ""

    # intermediate calculations
    _intermed_in_progress: bool = False

    def __init__(self):
        """Initializes parameter values and history tracking. """
        super().__init__()

        self.seed = IntField('Random seed', slug='seed', value=1234567)
        self.n_epi = IntField('Epistemic samples', value=0)
        self.cycle_units = ChoiceField('Cycle time units', choices=CycleUnits, value=CycleUnits.hr)

        self.do_crack_growth_plot = BoolField('Create crack growth plot', True)
        self.do_ex_rates_plot = BoolField('Create exercised rates plot', True)
        self.do_fad_plot = BoolField('Create failure assessment diagram', True)
        self.do_ensemble_plot = BoolField('Create ensemble plot', True)
        self.do_cycle_plot = BoolField('Create cycle plot', True)
        self.do_pdf_plot = BoolField('Create PDF plot', True)
        self.do_cdf_plot = BoolField('Create CDF plot', True)
        self.do_sen_plot = BoolField('Create sensitivity plot', True)

        # intermediate, read-only parameters.
        self.r_ratio = UncertainField('Stress ratio', value=1)
        self.f_ratio = UncertainField('Fugacity ratio', value=1)
        self.smys = UncertainField('% SMYS', value=1)
        self.a_m = UncertainField('Initial crack depth', value=1, unit=SmallDistance.inch)  # a(m), units should match those of wall thickness
        self.a_c = UncertainField('a/2c', value=1)
        self.t_r = UncertainField('t/R', value=1)

        pres_choices = [Pressure.mpa, Pressure.psi]

        defaults = 'det'
        if defaults == 'det':
            self.study_type = ChoiceField('Study type', choices=StudyTypes, value=StudyTypes.det)
            self.out_diam = UncertainField('Outer diameter', unit=SmallDistance.inch, value=36)
            self.thickness = UncertainField('Wall thickness', unit=SmallDistance.inch, value=0.406, max_value=3,
                                            tooltip='Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.p_max = UncertainField('Max pressure', unit=Pressure.psi, value=840)
            self.p_min = UncertainField('Min pressure', unit=Pressure.psi, value=638)
            self.temp = UncertainField('Temperature', unit=Temperature.k, value=293, min_value=230, max_value=330)
            self.vol_h2 = UncertainField('H2 volume fraction', slug='volume_fraction_h2', value=1, max_value=1,
                                         label_rtf="H<sub>2</sub> volume fraction")
            self.yield_str = UncertainField('Yield strength', unit=Pressure.psi, value=52_000, unit_choices=pres_choices)
            self.frac_resist = UncertainField('Fracture resistance', unit_type=Fracture, value=55)
            self.crack_dep = UncertainField('Crack depth', slug='flaw_depth', unit=Percent.p, value=25, min_value=0.1, max_value=80)
            self.crack_len = UncertainField('Crack length', slug='flaw_length', unit_type=SmallDistance, value=0.04)
            self.n_ale = IntField('Aleatory samples', value=0)
            self.n_ale.toggle_enabled(False)
            self.n_epi.toggle_enabled(False)

        elif defaults == 'prb':
            self.study_type = ChoiceField('Study type', choices=StudyTypes, value=StudyTypes.prb)
            self.out_diam = UncertainField('Outer diameter', unit=SmallDistance.inch, distr=Distributions.uni, value=22, a=21.9, b=22.1)
            self.thickness = UncertainField('Wall thickness', unit=SmallDistance.inch, distr=Distributions.uni, value=0.281,
                                            a=0.271, b=0.291, max_value=3,
                                            tooltip='Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.yield_str = UncertainField('Yield strength', unit=Pressure.psi, value=52_000, unit_choices=pres_choices)
            self.frac_resist = UncertainField('Fracture resistance', value=55, unit_type=Fracture)
            self.p_max = UncertainField('Max pressure', unit=Pressure.psi, distr=Distributions.nor, value=840, a=840, b=20)
            self.p_min = UncertainField('Min pressure', unit=Pressure.psi, distr=Distributions.nor, value=638, a=638, b=20)
            self.temp = UncertainField('Temperature', unit=Temperature.k, distr=Distributions.uni, value=293, a=285, b=300,
                                       min_value=230, max_value=330)
            self.vol_h2 = UncertainField('H2 volume fraction', slug='volume_fraction_h2', value=1, max_value=1,
                                         label_rtf="H<sub>2</sub> volume fraction")
            self.crack_dep = UncertainField('Crack depth', slug='flaw_depth', unit=Percent.p, distr=Distributions.uni,
                                            value=32, a=28, b=36, min_value=0.1, max_value=80)
            self.crack_len = UncertainField('Crack length', slug='flaw_length', unit_type=SmallDistance, distr=Distributions.uni,
                                            value=0.02, a=0.01, b=0.03)
            self.n_ale = IntField('Aleatory samples', value=50)

        elif defaults in ['sam', 'bnd']:
            self.out_diam = UncertainField('Outer diameter', unit=SmallDistance.inch, distr=Distributions.det, value=36)
            self.thickness = UncertainField('Wall thickness', unit=SmallDistance.inch, distr=Distributions.det, value=0.406, max_value=3,
                                            tooltip = 'Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.yield_str = UncertainField('Yield strength', unit=Pressure.psi, value=52_000, unit_choices=pres_choices)
            self.frac_resist = UncertainField('Fracture resistance', value=55, unit_type=Fracture)
            self.p_max = UncertainField('Max pressure', unit=Pressure.psi, distr=Distributions.nor, value=840, a=840, b=20)
            self.p_min = UncertainField('Min pressure', unit=Pressure.psi, distr=Distributions.nor, value=638, a=638, b=20)
            self.temp = UncertainField('Temperature', unit=Temperature.k, distr=Distributions.uni, value=293, a=285, b=300,
                                       min_value=230, max_value=330)
            self.vol_h2 = UncertainField('H2 volume fraction', slug='volume_fraction_h2', distr=Distributions.uni, value=0.1,
                                         a=0, b=0.2, max_value=1, label_rtf="H<sub>2</sub> volume fraction")
            self.crack_dep = UncertainField('Crack depth', slug='flaw_depth', unit=Percent.p, distr=Distributions.uni,
                                            value=25, a=20, b=30, min_value=0.1, max_value=80)
            self.crack_len = UncertainField('Crack length', slug='flaw_length', unit_type=SmallDistance, distr=Distributions.det, value=0.03)

            if defaults == 'sam':
                self.study_type = ChoiceField('Study type', choices=StudyTypes, value=StudyTypes.sam)
                self.n_ale = IntField('Aleatory samples', value=50)

            elif defaults == 'bnd':
                self.study_type = ChoiceField('Study type', choices=StudyTypes, value=StudyTypes.bnd)
                self.n_ale = IntField('Aleatory samples', value=0)

        # list parameters for easy iteration
        self.fields = [self.analysis_name,
                       self.out_diam, self.thickness, self.yield_str, self.frac_resist, self.p_max, self.p_min, self.temp,
                       self.vol_h2, self.crack_dep, self.crack_len,
                       self.n_ale, self.n_epi, self.seed,
                       self.do_crack_growth_plot, self.do_fad_plot, self.do_ex_rates_plot, self.do_ensemble_plot,
                       self.do_cycle_plot, self.do_pdf_plot, self.do_cdf_plot, self.do_sen_plot
                       ]

        self.cycle_units.changed += lambda x: self._handle_param_change()

        # reset sampling counts in addition to recording state
        self.study_type.changed += self._handle_study_type_changed

        super().post_init()

    # ==============================
    # ==== PARAMETER VALIDATION ====
    def check_valid(self) -> ValidationResponse:
        """Validates parameter values in form-wide manner. For example, validation of a parameter which depends on another parameter
        is done here.

        Notes
        -----
        Checks for errors first, then warnings, so most serious is shown first.

        Returns : ValidationResponse
        """
        study_type = self.study_type.value

        thickness = self.thickness.value_raw
        thick_max = self._thickness_max_val()
        if thickness > thick_max:
            return ValidationResponse(InputStatus.ERROR, 'Pipe thickness must be <= pipe radius and <= 3 in (76.2 mm)')

        if self.p_max.value_raw <= self.p_min.value_raw:
            return ValidationResponse(InputStatus.ERROR, 'Max pressure must be greater than minimum pressure')

        crack_len_min = 2 * (self.crack_dep.value_raw / 100.) * self.thickness.value_raw
        crack_len_min_disp = hround(self.crack_len.unit_type.convert(crack_len_min, new=self.crack_len.unit), p=3)
        if self.crack_len.value_raw <= crack_len_min:
            msg = f'Crack length must be greater than 2 x crack depth x pipe thickness ({crack_len_min_disp} {self.crack_len.unit})'
            return ValidationResponse(InputStatus.ERROR, msg)

        for field in self.fields:
            field_resp = field.check_valid()
            if field_resp.status != InputStatus.GOOD:
                return field_resp

        if study_type in ['prb', 'sam']:
            # ensure aleatory and epistemic counts and usage matches
            has_ale = False
            has_epi = False
            ale_samples = self.n_ale.value
            epi_samples = self.n_epi.value
            for field in self.fields:
                if type(field) == UncertainField:
                    if field.distr != 'det' and field.uncertainty == 'ale':
                        has_ale = True
                    elif field.distr != 'det' and field.uncertainty == 'epi':
                        has_epi = True

            if has_ale and ale_samples == 0:
                return ValidationResponse(InputStatus.ERROR, 'Aleatory samples do not match inputted parameters')

            if not has_ale and ale_samples > 0:
                return ValidationResponse(InputStatus.ERROR, 'Aleatory samples require corresponding parameter distribution')

            if has_epi and epi_samples == 0:
                return ValidationResponse(InputStatus.ERROR, 'Epistemic samples do not match inputted parameters')

            if not has_epi and epi_samples > 0:
                return ValidationResponse(InputStatus.ERROR, 'Epistemic samples require corresponding parameter distribution')

            if not has_ale and not has_epi:
                return ValidationResponse(InputStatus.WARN, 'Set at least one parameter to probabilistic for Probabilistic study')

            if (has_ale and ale_samples >= 100) or (has_epi and epi_samples >= 100):
                return ValidationResponse(InputStatus.WARN, 'large sample size may result in extended analysis time')

        elif study_type == 'det':
            for field in self.fields:
                if type(field) == UncertainField and field.distr != 'det':
                    name = field.label.lower()
                    return ValidationResponse(InputStatus.WARN, f"Probabilistic parameter value for {name} ignored in deterministic study")

        # Check warnings after errors

        if self.yield_str.value_raw >= 900:
            return ValidationResponse(InputStatus.WARN, 'high yield strength found - verify inputs before submitting')

        if self.frac_resist.value_raw >= 500:
            return ValidationResponse(InputStatus.WARN, 'high fracture resistance found - verify inputs before submitting')

        if self.p_max.value_raw >= 100:
            return ValidationResponse(InputStatus.WARN, 'high max pressure found - verify inputs before submitting')

        return ValidationResponse(InputStatus.GOOD, '')

    def _thickness_max_val(self) -> float:
        """Max pipe thickness is either 3in or half the diameter. """
        max1 = self.out_diam.value_raw / 2.
        max2 = self.out_diam.unit_type.convert(3, old=SmallDistance.inch, new=SmallDistance.m)
        result = max1 if max1 < max2 else max2
        return result

    def _handle_study_type_changed(self, study_type: ChoiceField):
        """Refresh form and available parameters when analysis sample type changes. """
        if self.study_type.value == 'det':
            for attr_name in self.__dict__:
                attr = getattr(self, attr_name)
                if type(attr) == UncertainField:
                    if attr.distr != 'det':
                        attr.distr = 'det'

            self.n_ale.toggle_enabled(False)
            self.n_ale.set_from_model(0)
            self.n_epi.toggle_enabled(False)
            self.n_epi.set_from_model(0)

        else:
            self.n_ale.toggle_enabled(True, silent=False)
            self.n_epi.toggle_enabled(True, silent=False)

        self._refresh_intermediate_params()
        self._record_state_change()

    def parse_study_type(self, val: str):
        """ Gets study type key for backend consumption. """
        if val == 'bnd':
            result = 'bounding'
        elif val == 'sam':
            result = 'sensitivity'
        elif val == 'prb':
            result = 'lhs'
        else:
            result = 'deterministic'
        return result

    def is_deterministic(self):
        return self.study_type.value == 'det'

    def _refresh_intermediate_params(self) -> None:
        """ Updates intermediate parameters via pool. """
        if self._intermed_in_progress:
            return
        self._intermed_in_progress = True

        try:
            params = self.get_prepped_param_dict()
        except ValueError as e:
            # param parsing may fail during changes so exit
            self._intermed_in_progress = False
            return

        study_type = self.parse_study_type(params['study_type'])

        results = _calc_intermediate_params(params, study_type)

        if results is None or 'r_ratio' not in results:
            self.r_ratio.value = np.inf
            self.f_ratio.value = np.inf
            self.smys.value = np.inf
            self.a_c.value = np.inf
            self.t_r.value = np.inf
            self.a_m.value = np.inf
        else:
            self.r_ratio.value = results['r_ratio']
            self.f_ratio.value = results['f_ratio']
            self.smys.value = results['smys']
            self.a_c.value = results['a_c']
            self.t_r.value = results['t_r']
            self.a_m.unit = self.thickness.unit
            self.a_m.set_value_raw(results['a_m'])  # incoming value always in meters
        self._intermed_in_progress = False

    def get_prepped_param_dict(self):
        """Returns dict of parameters prepared for analysis submission. """
        dct = super().get_prepped_param_dict()
        dct |= {
            'cycle_units': self.cycle_units.value,
            'study_type': self.study_type.value,
        }

        return dct

    def to_dict(self) -> dict:
        """Returns representation of this state as dict of parameter dicts. """
        result = super().to_dict()
        result |= {
            'study_type': self.study_type.to_dict(),
            'cycle_units': self.cycle_units.to_dict(),
        }
        return result

    def _from_dict(self, data: dict):
        """Overwrites state analysis parameter data from dict containing all parameters.

        Parameters
        ----------
        data : dict
            Analysis parameter data with keys matching internal snake_case naming.

        """
        # Verify all parameters present. Must account for new/revised params.
        if 'analysis_name' not in data:
            data['analysis_name'] = self.analysis_name.to_dict()

        super()._from_dict(data)

        self.study_type.from_dict(data['study_type'])
        self.cycle_units.from_dict(data['cycle_units'])

    def _handle_param_change(self):
        self._refresh_intermediate_params()
        super()._handle_param_change()

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

