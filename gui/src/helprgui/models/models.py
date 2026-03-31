"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import logging
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.constants as scp

from probabilistic.capabilities.uncertainty_definitions import TimeSeriesCharacterization, DeterministicCharacterization
from helprgui.hygu.models.fields import ChoiceField, BoolField, IntField, StringField, NumField

from helprgui import app_settings
from helprgui.hygu.models.models import ModelBase
from helprgui.hygu.utils import helpers
from helprgui.hygu.utils.distributions import Distributions
from helprgui.hygu.utils.helpers import hround, InputStatus, ValidationResponse
from helprgui.hygu.utils.units_of_measurement import (SmallDistance, Pressure, Fracture, Temperature, BasicPercent, LongTime)

from helpr import settings as api_settings
from helpr import api
from helpr.utilities import plots
from .enums import StudyTypes, CycleUnits, StressMethod, SurfaceType, CrackAssumption, EvolutionMethod, \
    LoadingProfileUnits
from .fields import HelprUncertainField

log = logging.getLogger(app_settings.APPNAME)


def parse_study_type(val: str):
    """ Gets API sample type key from GUI study type. """
    if val == 'bnd':
        result = 'bounding'
    elif val == 'sam':
        result = 'sensitivity'
    elif val == 'prb':
        result = 'lhs'
    else:
        result = 'deterministic'
    return result


def _do_api_crack_analysis(params, sample_type):
    """ Requests crack evolution analysis from HELPR API. """
    api_settings.USING_GUI = True

    try:
        with warnings.catch_warnings(record=True) as warnings_list:
            warnings.simplefilter("always")  # catch all
            result = api.CrackEvolutionAnalysis(outer_diameter=params['outer_diameter'],
                                                wall_thickness=params['wall_thickness'],
                                                flaw_depth=params['flaw_depth'],
                                                max_pressure=params['max_pressure'],
                                                min_pressure=params['min_pressure'],
                                                temperature=params['temperature'],
                                                volume_fraction_h2=params['volume_fraction_h2'],
                                                yield_strength=params['yield_strength'],
                                                fracture_resistance=params['fracture_resistance'],
                                                flaw_length=params['flaw_length'],
                                                stress_intensity_method=params['stress_method'],
                                                surface=params['surface'],
                                                residual_stress_intensity_factor=params['residual_stress_intensity_factor'],
                                                delta_c_rule=params['crack_assump'],

                                                aleatory_samples=params['aleatory_samples'],
                                                epistemic_samples=params['epistemic_samples'],
                                                random_seed=params['seed'],
                                                max_cycles=params['n_cycles'],
                                                cycle_step=params['cycle_step_size'],
                                                sample_type=sample_type)
            for warning in warnings_list:
                # Ignore backend warning spam
                if "Inner Radius / wall thickness exceeds bounds" in str(warning.message):
                    continue
                log.warning(f"Warning during analysis: {str(warning.message)}")
            return result
    except Exception as err:
        log.warning(f"Crack evolution analysis failed with error: {str(err)}")
        raise



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
    Parameter list must match expected call from thread; changing it requires changing all threaded analysis calls!

    """
    # Update this process' version of GUI settings
    app_settings.SESSION_DIR = params['session_dir']

    # multiprocessing does not support logging to same file. Must implement queue handler if this functionality is desired.
    proc_log = logging.getLogger(__name__)
    proc_log.setLevel(logging.INFO)

    study_type = params['study_type']
    api_sample_type = parse_study_type(study_type)

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

    try:
        return _do_crack_evolution_analysis(analysis_id, params, study_type, api_sample_type,
                                            output_dir, proc_log)
    finally:
        import matplotlib.pyplot as plt
        plt.close('all')


def _do_crack_evolution_analysis(analysis_id, params, study_type, api_sample_type,
                                 output_dir, proc_log):
    """Inner analysis logic for do_crack_evolution_analysis. """
    results = {'status': 1}
    try:
        # param dict keys are slugs and must match api kwarg naming
        analysis = _do_api_crack_analysis(params, api_sample_type)
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
    input_param_plots = {}
    crack_filepath = ""
    crack_growth_data = {}

    design_curve_filepath = ""
    design_curve_data = {}

    fad_filepath = ""
    fad_data = {}

    ensemble_filepath = ""
    ensemble_data = {}

    cycle_filepath = ""
    cycle_data = {}

    pdf_filepath = ""
    pdf_data = {}

    cdf_filepath = ""
    cdf_data = {}

    sen_filepath = ""
    sen_data = {}
    sen_filepath_fad = ""
    sen_data_fad = {}

    loading_profile_path = ""

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

    # Note (Cianan): HELPR plot data was revamped in summer '25 by SNL so interactive plots might be stale
    if study_type == 'det':
        analysis.postprocess_single_crack_results(save_figs=True)

        if params['create_crack_growth_plot']:
            crack_filepath = analysis.crack_growth_plot
            plot_data = analysis.crack_growth_plot_data
            a_t = np.around(plot_data[0], 3)
            crack_growth_data = {
                'a_t': helpers.slim_arr(a_t),  # row-point format [(x,y), ...]
                'acrit_pt': np.around(plot_data[1][0], 2),
                '25acrit_pt': np.around(plot_data[2][0], 2),
                # 'half_pt': np.around(plot_data[2][0], 2),
            }

        if params['create_exercised_rates_plot']:
            design_curve_filepath, plot_data = analysis.get_design_curve_plot()
            design_curve_data = {
                'ln1': helpers.slim_arr(plot_data[1]),
                'ln2': helpers.slim_arr(plot_data[0]),
            }

        if params['create_failure_assessment_diagram']:
            fad_filepath, plot_data = analysis.assemble_failure_assessment_diagram(save_fig=True)
            # plot_data[0] = FAD equation line, [4] = crack evolution trajectory, [-1] = FAD intersection pt
            evolution = plot_data[4]
            # Beyond-plot point: first point where Kr (y) exceeds 1.0
            beyond_pt = np.array([np.nan, np.nan])
            exceeding = evolution[:, 1] > 1.0
            if np.any(exceeding):
                idx = np.argmax(exceeding)
                beyond_pt = np.array([float(evolution[idx, 0]), 1.0])

            fad_data = {
                'ln1': helpers.slim_arr(plot_data[0], x_decimals=4, y_decimals=4),
                'evolution': helpers.slim_arr(evolution, x_decimals=4, y_decimals=4),
                'pt1': np.around(plot_data[-1][0], 4),
                'beyond_pt': np.around(beyond_pt, 4),
            }

    elif study_type == 'prb':
        try:
            analysis.postprocess_single_crack_results()
        except IndexError as err:
            msg = "Exception occurred during analysis postprocessing"
            proc_log.exception(msg)
            results = {'status': -1, 'analysis_id': analysis_id, 'error': err, 'message': msg}
            return results

        input_param_plots = analysis.generate_input_parameter_plots(save_figs=True)
        plotted_variables = ['Cycles to a(crit)', 'Cycles to FAD line']

        if params['create_ensemble_plot']:
            ensemble_filepath, _ = plots.plot_pipe_life_ensemble(analysis, criteria=plotted_variables, save_fig=True)
            ensemble_data = {'lines': [], 'pts_acrit': [], 'pts_fad': []}

            for load_cycle in analysis.load_cycling:
                elem = np.array([load_cycle['Total cycles'], load_cycle['a/t']]).T
                if elem.shape[0] == 0:
                    continue
                ln = helpers.slim_arr(elem, max_len=30, x_decimals=0, y_decimals=3)
                ensemble_data['lines'].append(ln)

            # Build point data per QoI directly from analysis results
            for qoi in plotted_variables:
                pts = np.array([np.around(analysis.life_criteria[qoi][0], 0),
                                np.around(analysis.life_criteria[qoi][1], 3)]).T
                if qoi == 'Cycles to a(crit)':
                    ensemble_data['pts_acrit'] = pts
                else:
                    ensemble_data['pts_fad'] = pts

        if params['create_cycle_plot']:
            cycle_filepaths, _ = plots.plot_cycle_life_criteria_scatter(analysis, criteria=plotted_variables, save_fig=True)
            cycle_filepath = cycle_filepaths[0]
            n_ale = analysis.number_of_aleatory_samples
            n_epi = analysis.number_of_epistemic_samples
            cycle_data = {'subsets_acrit': [], 'nominal_pt_acrit': [],
                          'subsets_fad': [], 'nominal_pt_fad': []}
            for qoi in plotted_variables:
                cycles = analysis.life_criteria[qoi][0]
                values = analysis.life_criteria[qoi][1]
                nom_cycles = float(analysis.nominal_life_criteria[qoi][0][0])
                nom_values = float(analysis.nominal_life_criteria[qoi][1][0])
                qoi_subsets = []
                for i in range(max(n_epi, 1)):
                    idx = slice(i * n_ale, (i + 1) * n_ale)
                    qoi_subsets.append(np.array([cycles[idx], values[idx]]).T)
                if qoi == 'Cycles to a(crit)':
                    cycle_data['subsets_acrit'] = qoi_subsets
                    cycle_data['nominal_pt_acrit'] = np.array([nom_cycles, nom_values])
                else:
                    cycle_data['subsets_fad'] = qoi_subsets
                    cycle_data['nominal_pt_fad'] = np.array([nom_cycles, nom_values])

        if params['create_failure_assessment_diagram']:
            fad_filepath, _ = analysis.assemble_failure_assessment_diagram(save_fig=True)
            fad_data = {'lines': [], 'pts': [], 'nominal_pt': [0, 0],
                        'nominal_line': []}

            # FAD equation boundary line
            load_space = np.linspace(0, 2.2)
            toughness_line = plots.failure_assessment_diagram_equation(load_space)
            fad_data['lines'].append(np.array([load_space, toughness_line]).T)

            # Sample crack evolution trajectories
            for sample in analysis.load_cycling:
                lr = np.array(sample['Load ratio'])
                tr = np.array(sample['Toughness ratio'])
                fad_data['lines'].append(helpers.slim_arr(np.array([lr, tr]).T))

            # FAD intersection points for all samples
            fad_pts_lr = analysis.life_criteria['Cycles to FAD line'][2]
            fad_pts_tr = analysis.life_criteria['Cycles to FAD line'][3]
            fad_data['pts'] = np.array([fad_pts_lr, fad_pts_tr]).T

            # Nominal trajectory line
            if hasattr(analysis, 'nominal_load_cycling') and analysis.nominal_load_cycling:
                nom_sample = analysis.nominal_load_cycling[0]
                nom_lr_line = np.array(nom_sample['Load ratio'])
                nom_tr_line = np.array(nom_sample['Toughness ratio'])
                fad_data['nominal_line'] = np.array([nom_lr_line, nom_tr_line]).T

            # Nominal FAD intersection point
            nom_lr = analysis.nominal_life_criteria['Cycles to FAD line'][2]
            nom_tr = analysis.nominal_life_criteria['Cycles to FAD line'][3]
            if len(nom_lr) > 0 and len(nom_tr) > 0:
                fad_data['nominal_pt'] = np.array([float(nom_lr[0]), float(nom_tr[0])])

        if params['create_pdf_plot']:
            pdf_filepaths, _ = plots.plot_cycle_life_pdfs(analysis, criteria=plotted_variables, save_fig=True)
            pdf_filepath = pdf_filepaths[0]
            n_ale = analysis.number_of_aleatory_samples
            n_epi = analysis.number_of_epistemic_samples
            pdf_data = {'acrit_bins': [], 'acrit_nominal': 0,
                        'fad_bins': [], 'fad_nominal': 0}
            for qoi in plotted_variables:
                cycle_life_data = analysis.life_criteria[qoi][0]
                nominal_val = float(analysis.nominal_life_criteria[qoi][0][0])
                qoi_bins = []
                for i in range(max(n_epi, 1)):
                    idx = slice(i * n_ale, (i + 1) * n_ale)
                    subset = np.array(cycle_life_data[idx])
                    valid = subset[~np.isnan(subset)]
                    if valid.size > 0 and valid.max() > 1:
                        log_data = np.log10(valid[valid > 1])
                        freqs, bins = np.histogram(log_data, bins='auto')
                        freqs = freqs.tolist()
                        bins = bins.tolist()
                        pts = [(bins[0], 0)]
                        for j in range(len(freqs)):
                            pts.append((bins[j], freqs[j]))
                            pts.append((bins[j+1], freqs[j]))
                        pts.append((bins[-1], 0))
                        qoi_bins.append(pts)

                if qoi == 'Cycles to a(crit)':
                    pdf_data['acrit_bins'] = qoi_bins
                    pdf_data['acrit_nominal'] = np.log10(nominal_val) if nominal_val > 0 else 0
                else:
                    pdf_data['fad_bins'] = qoi_bins
                    pdf_data['fad_nominal'] = np.log10(nominal_val) if nominal_val > 0 else 0

        if params['create_cdf_plot']:
            cdf_filepath, _ = plots.plot_cycle_life_cdfs(analysis, criteria=plotted_variables, save_fig=True)
            n_ale = analysis.number_of_aleatory_samples
            n_epi = analysis.number_of_epistemic_samples
            cdf_data = {'acrit_lines': [], 'acrit_nominal': [],
                        'fad_lines': [], 'fad_nominal': []}
            for qoi in plotted_variables:
                cycle_life_data = analysis.life_criteria[qoi][0]
                qoi_lines = []
                for i in range(max(n_epi, 1)):
                    sample_indices = slice(i * n_ale, (i + 1) * n_ale)
                    subset = cycle_life_data[sample_indices]
                    y_ord, x_ord = plots.ecdf(subset)
                    qoi_lines.append(np.array([x_ord, y_ord]).T)

                nominal_val = float(analysis.nominal_life_criteria[qoi][0][0])
                nominal_line = np.array([[nominal_val, 0], [nominal_val, 1]])

                if qoi == 'Cycles to a(crit)':
                    cdf_data['acrit_lines'] = qoi_lines
                    cdf_data['acrit_nominal'] = nominal_line
                else:
                    cdf_data['fad_lines'] = qoi_lines
                    cdf_data['fad_nominal'] = nominal_line

    elif study_type in ['bnd', 'sam']:
        input_param_plots = analysis.generate_input_parameter_plots(save_figs=True)
        if params['create_sensitivity_plot']:
            # Generate sensitivity plot for 'Cycles to a(crit)'
            sen_filepaths, sen_data_list = plots.plot_sensitivity_results(analysis,
                                                                          criteria='Cycles to a(crit)',
                                                                          save_fig=True,
                                                                          filename='sensitivity_acrit')
            sen_filepath = sen_filepaths[0]
            sen_data = sen_data_list

            # Generate sensitivity plot for 'Cycles to FAD line'
            sen_filepaths_fad, sen_data_list_fad = plots.plot_sensitivity_results(analysis,
                                                                                  criteria='Cycles to FAD line',
                                                                                  save_fig=True,
                                                                                  filename='sensitivity_fad')
            sen_filepath_fad = sen_filepaths_fad[0]
            sen_data_fad = sen_data_list_fad

    # Create random loading profile plot. For testing, use 50,000 cycles and 5 aleatory samples.
    if params['random_loading_profile']:
        p_min_arr = params['min_pressure'].value
        p_min_arr = p_min_arr.tolist() if isinstance(p_min_arr, np.ndarray) else p_min_arr
        p_max_arr = params['max_pressure'].value
        p_max_arr = p_max_arr.tolist() if isinstance(p_max_arr, np.ndarray) else p_max_arr
        loading_profile_path, plot_data = plots.plot_random_loading_profiles(minimum_pressure=p_min_arr,
                                                                             maximum_pressure=p_max_arr,
                                                                             save_fig=True)
    else:
        loading_profile_path = ""

    analysis.save_results(output_dir=output_dir)

    results = {
        'status': 1,
        'crack_analysis': analysis,
        'analysis_id': analysis_id,
        'input_param_plots': input_param_plots,
        'crack_growth_plot': crack_filepath,
        'crack_growth_data': crack_growth_data,

        'design_curve_plot': design_curve_filepath,
        'design_curve_data': design_curve_data,

        'ensemble_plot': ensemble_filepath,
        'ensemble_data': ensemble_data,
        'cycle_plot': cycle_filepath,
        'cycle_data': cycle_data,

        'pdf_plot': pdf_filepath,
        'pdf_data': pdf_data,

        'cdf_plot': cdf_filepath,
        'cdf_data': cdf_data,

        'fad_plot': fad_filepath,
        'fad_data': fad_data,

        'sen_plot': sen_filepath,
        'sen_data': sen_data,
        'sen_plot_fad': sen_filepath_fad,
        'sen_data_fad': sen_data_fad,

        'loading_profile_plot': loading_profile_path,

        'output_dir': output_dir,
    }

    # return instance of state from other process
    return results


def _calc_intermediate_params(params, sample_type):
    """ Update stored float intermediate parameter values based on sample type. """
    api_settings.USING_GUI = True

    results = None
    try:
        analysis = _do_api_crack_analysis(params, sample_type)

        if analysis.nominal_intermediate_variables.keys():
            api_dict = analysis.nominal_intermediate_variables
        else:
            api_dict = analysis.sampling_intermediate_variables

        results = {
            'r_ratio': api_dict['r_ratio'],
            'f_ratio': api_dict['fugacity_ratio'],
            'smys': api_dict['%SMYS'],
            'a_c': api_dict['a/2c'],
            't_r': api_dict['t/R'],
            'a_m': api_dict['a (m)'],
        }
    except Exception as err:
        log.warning("Intermediate parameter calculation failed")

    return results


def do_inspection_mitigation_analysis(analysis_id, params: dict, global_status_dict: dict):
    """ Conduct API inspection mitigation analysis via threading.
    Note that this is executed on a stored datastore object from a completed analysis, and not the "live" one attached to the main form.
    """
    try:
        return _do_inspection_mitigation_analysis(analysis_id, params, global_status_dict)
    finally:
        import matplotlib.pyplot as plt
        plt.close('all')


def _do_inspection_mitigation_analysis(analysis_id, params: dict, global_status_dict: dict):
    """Inner analysis logic for do_inspection_mitigation_analysis. """
    sample_type = parse_study_type(params['study_type'])
    results = {'status': 0, 'message': "", 'histogram_plot': '', 'cdf_plot': '', 'mitigated': []}

    analysis_dir = params.get('analysis_dir', None)
    if analysis_dir is None:
        results['status'] = -1
        results['message'] = "Analysis output directory not found"
        return results

    try:
        analysis = params['crack_analysis']

        probability_of_detection = params['probability_of_detection']
        detection_resolution = params['detection_resolution']
        inspection_interval = params['inspection_interval']
        criteria='Cycles to a(crit)'
        filepaths, plot_data = analysis.apply_inspection_mitigation(probability_of_detection=probability_of_detection,
                                                                    detection_resolution=detection_resolution,
                                                                    inspection_frequency=inspection_interval,
                                                                    criteria=criteria,
                                                                    save_fig=True)
        histogram_filepath, cdf_filepath = filepaths
        data_hist, data_cdf = plot_data

        # percent_mitigated = sum(mitigated_list) / params['aleatory_samples'] * 100
        results['histogram_plot'] = histogram_filepath
        results['cdf_plot'] = cdf_filepath
        # results['percent_mitigated'] = percent_mitigated
        results['status'] = 1

        # Include input values in results for display
        results['probability_of_detection'] = probability_of_detection
        results['detection_resolution'] = detection_resolution
        results['inspection_interval'] = inspection_interval

    except Exception as err:
        log.exception(err)
        results['status'] = -1
        results['message'] = "Inspection mitigation analysis failed"

    return results


class State(ModelBase):
    """Representation of analysis parameter data.

    Note
    ----
    When default parameter values are changed, regenerate demo files by running:
        python gui/scripts/generate_demos.py

    Attributes
    ----------
    out_diam : HelprUncertainField
        Pipe outer diameter.
    thickness : HelprUncertainField
        Pipe thickness.
    crack_dep : HelprUncertainField
        Crack depth.
    crack_len : HelprUncertainField
        Crack length.
    p_min : HelprUncertainField
        Minimum pressure.
    p_max : HelprUncertainField
        Maximum pressure.
    temp : HelprUncertainField
        Temperature.
    vol_h2 : HelprUncertainField
        H2 volume.
    yield_str : HelprUncertainField
        Yield strength.
    stress_intensity : HelprUncertainField
        Residual stress intensity factor [MPa-m^(1/2)].
    frac_resist : HelprUncertainField
        Fracture resistance [MPa-m^(1/2)].
    n_ale : IntField
        Number of aleatory samples.
    n_epi : IntField
        Number of epistemic samples.
    seed : IntField
        Random seed.
    n_cycles : IntField
        Number of cycles.
    study_type : ChoiceField
        Analysis sample type (deterministic, Probabilistic, sensitivity (bounds), or sensitivity (sample)).
    cycle_units : ChoiceField
        Active cycle time units.
    random_loading_profile : StringField
        File path to CSV file of random loading profile data.
    profile_units : ChoiceField
        Pressure units of random loading profile data.
    evolution_method : ChoiceField
        How to evolve analysis: a/t or cycles
    cycle_step_size : IntField
        Step size of cycles if evolving by cycles. Note that random loading profile overrides this to value of 1.

    probability_of_detection : NumField
        Probability of a crack being detected at each inspection.
    detection_resolution : NumField
        Crack depth that is detectable by inspection. For example, a value of 0.3 indicates any crack larger than 30% of wall thickness is
            detectable.
    inspection_interval : NumField
        Time between inspections, in cycles (days).

    input_param_plots : dict
        Filepaths of plots of uncertain input parameters.

    do_interactive_charts : BoolField
        Whether results will show interactive charts or static plots.
    crack_analysis : CrackEvolutionAnalysis
        Analysis result object to be reused in post-process analyses.
    do_crack_growth_plot : BoolField
        Whether analysis shall create a crack growth plot.
    crack_growth_plot : str
        String filepath to crack growth plot (deterministic analysis only).
    do_fad_plot : BoolField
        Whether analysis shall create a failure assessment diagram
    fad_plot : str
        String filepath to failure assessment diagram (deterministic and Probabilistic analysis only).
    do_design_curve_plot : BoolField
        Whether analysis shall create a design curve plot.
    design_curve_plot : str
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
    loading_profile_plot : str
        String filepath to random loading profile plot, if profile provided.
    cycle_cbv_plots : List
        List of string filepaths to CBV cycle plots (Probabilistic analysis only).

    Notes
    -----
    Same state object can back multiple analysis form types.

    """
    out_diam: HelprUncertainField
    thickness: HelprUncertainField
    crack_dep: HelprUncertainField
    crack_len: HelprUncertainField
    p_min: HelprUncertainField
    p_max: HelprUncertainField
    temp: HelprUncertainField
    vol_h2: HelprUncertainField
    yield_str: HelprUncertainField
    frac_resist: HelprUncertainField
    n_ale: IntField
    n_epi: IntField
    seed: IntField
    n_cycles: IntField
    study_type: ChoiceField
    stress_method: ChoiceField
    surface: ChoiceField
    stress_intensity: HelprUncertainField
    crack_assump: ChoiceField
    cycle_units: ChoiceField
    random_loading_profile: StringField
    profile_units: ChoiceField
    evolution_method: ChoiceField
    cycle_step_size: IntField

    # Inspection mitigation analysis inputs
    probability_of_detection: NumField
    detection_resolution: NumField
    inspection_interval: NumField

    input_param_plots: dict

    do_interactive_charts: BoolField
    use_deterministic_intermediates: BoolField

    crack_analysis: api.CrackEvolutionAnalysis = None
    do_crack_growth_plot: BoolField
    crack_growth_plot: str = ""
    crack_growth_data: dict

    do_fad_plot: BoolField
    fad_plot: str = ""
    fad_data: dict

    do_design_curve_plot: BoolField
    design_curve_plot: str = ""
    design_curve_data: dict

    do_ensemble_plot: BoolField
    ensemble_plot: str = ""
    ensemble_data: dict

    do_cycle_plot: BoolField
    cycle_plot: str = ""
    cycle_data: dict

    do_pdf_plot: BoolField
    pdf_plot: str = ""
    pdf_data: dict

    do_cdf_plot: BoolField
    cdf_plot: str = ""
    cdf_data: dict

    cycle_cbv_plots: []

    do_sen_plot: BoolField
    sen_plot: str = ""
    sen_data: dict
    sen_plot_fad: str = ""
    sen_data_fad: dict

    loading_profile_plot: str = ""

    # intermediate calculations
    _intermed_in_progress: bool = False

    def __init__(self, defaults: str = None):
        """Initializes parameter values and history tracking.

        Parameters
        ----------
        defaults : str, optional
            Study type to use for default parameter values. One of 'det', 'prb', 'sam', 'bnd'.
            If None, defaults to 'prb' (probabilistic).
        """
        super().__init__()

        # For debounced intermediate parameter calls - only do one refresh after a delay to avoid spammed calls
        # self._intermed_refresh_delay = 1.0
        # self._intermed_refresh_timer = None

        self.seed = IntField('Random seed', slug='seed', value=1234567)
        self.n_epi = IntField('Epistemic samples', value=0, min_value=0)
        self.n_cycles = IntField('Maximum number of cycles', slug='n_cycles', value=None, min_value=1)
        self.cycle_units = ChoiceField('Cycle time units', choices=CycleUnits, value=CycleUnits.hr)

        self.do_interactive_charts = BoolField('Display interactive plots', False)
        self.use_deterministic_intermediates = BoolField('Use deterministic intermediate calculations', True)

        self.do_crack_growth_plot = BoolField('Create crack growth plot', True)
        self.do_design_curve_plot = BoolField('Create exercised rates plot', True)
        self.do_fad_plot = BoolField('Create failure assessment diagram', True)
        self.do_ensemble_plot = BoolField('Create ensemble plot', True)
        self.do_cycle_plot = BoolField('Create cycle plot', True)
        self.do_pdf_plot = BoolField('Create PDF plot', True)
        self.do_cdf_plot = BoolField('Create CDF plot', True)
        self.do_sen_plot = BoolField('Create sensitivity plot', True)

        self.stress_method = ChoiceField('Stress intensity factor model', slug='stress_method',
                                         choices=StressMethod, value=StressMethod.anderson)
        self.surface = ChoiceField('Surface', choices=SurfaceType, value=SurfaceType.inside)

        self.stress_intensity = HelprUncertainField('Residual stress intensity factor',
                                               slug="residual_stress_intensity_factor",  # must match API
                                               unit_type=Fracture,
                                               value=0,
                                               lower=0,
                                               min_value=0)

        self.crack_assump = ChoiceField('Crack length assumption', slug='crack_assump',
                                        choices=CrackAssumption, value=CrackAssumption.prop)

        self.random_loading_profile = StringField('Random loading profile', value='')
        self.profile_units = ChoiceField('Loading profile units', slug='profile_units',
                                         choices=LoadingProfileUnits, value=LoadingProfileUnits.psi)

        self.evolution_method = ChoiceField('Evolution method', choices=EvolutionMethod, value=EvolutionMethod.a_t)
        self.cycle_step_size = IntField('Cycle step size', value=1, min_value=1, max_value=1000000)

        # intermediate, read-only parameters.
        self.r_ratio = HelprUncertainField('Stress ratio', value=1)
        self.f_ratio = HelprUncertainField('Fugacity ratio', value=1)
        self.smys = HelprUncertainField('% SMYS', value=1)
        self.a_m = HelprUncertainField('Initial crack depth', value=1, unit=SmallDistance.inch)  # a(m), units should match those of wall thickness
        self.a_c = HelprUncertainField('a/2c', value=1)
        self.t_r = HelprUncertainField('t/R', value=1)

        # Inspection mitigation analysis params (post-result analysis)
        self.probability_of_detection = NumField('Probability of detection', value=0.8, min_value=0, max_value=1)
        self.detection_resolution = NumField('Detection resolution', value=0.3, min_value=0, max_value=0.8)
        self.inspection_interval = IntField('Inspection interval', value=365, min_value=1, max_value=1000000, unit=LongTime.day)

        pres_choices = [Pressure.mpa, Pressure.psi]

        # Switch between these sets of inputs to quickly reproduce demo cases
        if defaults is None:
            defaults = StudyTypes.prb

        if defaults == StudyTypes.det:
            self.study_type = ChoiceField('Study type', choices=StudyTypes, value=StudyTypes.det)
            self.out_diam = HelprUncertainField('Outer diameter', unit=SmallDistance.inch, value=36)
            self.thickness = HelprUncertainField('Wall thickness', unit=SmallDistance.inch, value=0.406, max_value=3,
                                            tooltip='Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.p_max = HelprUncertainField('Max pressure', unit=Pressure.psi, value=840)
            self.p_min = HelprUncertainField('Min pressure', unit=Pressure.psi, value=638)
            self.temp = HelprUncertainField('Temperature', unit=Temperature.k, value=293, min_value=230, max_value=330)
            self.vol_h2 = HelprUncertainField('H2 volume fraction', slug='volume_fraction_h2',
                                         value=1, min_value=0, max_value=1, lower=0, upper=1,
                                         label_rtf="H<sub>2</sub> volume fraction")
            self.yield_str = HelprUncertainField('Yield strength', unit=Pressure.psi, value=52_000, unit_choices=pres_choices)
            self.frac_resist = HelprUncertainField('Fracture resistance', unit_type=Fracture, value=55)
            self.crack_dep = HelprUncertainField('Crack depth', slug='flaw_depth', unit=BasicPercent.p,
                                            value=25, min_value=0.1, max_value=80)
            self.crack_len = HelprUncertainField('Crack length', slug='flaw_length', unit_type=SmallDistance,
                                                 unit=SmallDistance.inch,
                                                 min_value=1e-6, lower=1e-6, std=1e-6, mean=1e-6,
                                                 value=1.575)
            self.n_ale = IntField('Aleatory samples', value=0, min_value=0)

        elif defaults == StudyTypes.prb:
            self.do_interactive_charts.value = False
            self.study_type = ChoiceField('Study type', choices=StudyTypes, value=StudyTypes.prb)
            self.out_diam = HelprUncertainField('Outer diameter', unit=SmallDistance.inch,
                                           distr=Distributions.uni,
                                           value=22, lower=21.9, upper=22.1)
            self.thickness = HelprUncertainField('Wall thickness', unit=SmallDistance.inch,
                                            distr=Distributions.uni,
                                            value=0.281,
                                            lower=0.271, upper=0.291, max_value=3,
                                            tooltip='Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.yield_str = HelprUncertainField('Yield strength', unit=Pressure.psi, value=52_000, unit_choices=pres_choices)
            self.frac_resist = HelprUncertainField('Fracture resistance', value=55, unit_type=Fracture)
            self.p_max = HelprUncertainField('Max pressure', unit=Pressure.psi,
                                        distr=Distributions.tnor,
                                        value=840, mean=850, std=20, lower=850-3*20, upper=850+3*20)
            self.p_min = HelprUncertainField('Min pressure', unit=Pressure.psi,
                                        distr=Distributions.tnor,
                                        value=638, mean=638, std=20, lower=638-3*20, upper=638+3*20)
            self.temp = HelprUncertainField('Temperature', unit=Temperature.k,
                                       distr=Distributions.uni,
                                       value=293, lower=285, upper=300, min_value=230, max_value=330)
            self.vol_h2 = HelprUncertainField('H2 volume fraction', slug='volume_fraction_h2',
                                         value=1, min_value=0, max_value=1, lower=0, upper=1,
                                         label_rtf="H<sub>2</sub> volume fraction")
            self.crack_dep = HelprUncertainField('Crack depth', slug='flaw_depth',
                                            distr=Distributions.tlog, unit=BasicPercent.p,
                                            value=25, mu=3.2, sigma=0.17, lower=0.001, upper=80,
                                            min_value=0.0001, max_value=80)
            self.crack_len = HelprUncertainField('Crack length', slug='flaw_length', unit_type=SmallDistance,
                                                 distr=Distributions.det, unit=SmallDistance.inch,
                                                 min_value=1e-6, lower=1e-6, std=1e-6, mean=1e-6,
                                                 value=1.575)
            self.n_ale = IntField('Aleatory samples', value=50)

        elif defaults in [StudyTypes.sam, StudyTypes.bnd]:
            self.out_diam = HelprUncertainField('Outer diameter', unit=SmallDistance.inch, distr=Distributions.det, value=36)
            self.thickness = HelprUncertainField('Wall thickness', unit=SmallDistance.inch, distr=Distributions.det, value=0.406, max_value=3,
                                            tooltip='Enter a positive value <= half the pipe diameter. Cannot exceed 3 in (76.2 mm).')
            self.yield_str = HelprUncertainField('Yield strength', unit=Pressure.psi, value=52_000, unit_choices=pres_choices)
            self.frac_resist = HelprUncertainField('Fracture resistance', value=55, unit_type=Fracture)
            self.p_max = HelprUncertainField('Max pressure', unit=Pressure.psi,
                                        distr=Distributions.tnor,
                                        value=840, mean=850, std=20, lower=850-3*20, upper=850+3*20)
            self.p_min = HelprUncertainField('Min pressure', unit=Pressure.psi,
                                        distr=Distributions.tnor,
                                        value=638, mean=638, std=20, lower=638-3*20, upper=638+3*20)
            self.temp = HelprUncertainField('Temperature', unit=Temperature.k, distr=Distributions.uni,
                                       value=293, lower=285, upper=300, min_value=230, max_value=330)
            self.vol_h2 = HelprUncertainField('H2 volume fraction', slug='volume_fraction_h2',
                                         distr=Distributions.uni,
                                         value=0.1, lower=0, upper=0.2, # lower=0, upper=1,
                                         min_value=0, max_value=1, label_rtf="H<sub>2</sub> volume fraction")
            self.crack_dep = HelprUncertainField('Crack depth', slug='flaw_depth', distr=Distributions.uni,
                                            unit=BasicPercent.p,
                                            value=25, lower=20, upper=30, min_value=0.1, max_value=80)
            self.crack_len = HelprUncertainField('Crack length', slug='flaw_length', unit_type=SmallDistance,
                                                 min_value=1e-6, lower=1e-6, std=1e-6, mean=1e-6,
                                                 distr=Distributions.det, unit=SmallDistance.inch, value=1.575)

            if defaults == StudyTypes.sam:
                self.study_type = ChoiceField('Study type', choices=StudyTypes, value=StudyTypes.sam)
                self.n_ale = IntField('Aleatory samples', value=50)

            elif defaults == StudyTypes.bnd:
                self.study_type = ChoiceField('Study type', choices=StudyTypes, value=StudyTypes.bnd)
                self.n_ale = IntField('Aleatory samples', value=0)

        # list parameters for easy iteration
        self.fields = [self.analysis_name,
                       # self.study_type,
                       self.stress_method,
                       self.surface,
                       self.stress_intensity,
                       self.crack_assump,
                       self.out_diam, self.thickness, self.yield_str,
                       self.frac_resist, self.p_max, self.p_min, self.temp,
                       self.vol_h2, self.crack_dep, self.crack_len,
                       self.n_ale, self.n_epi, self.seed, self.n_cycles,
                       self.do_interactive_charts,
                       self.random_loading_profile, self.profile_units, self.evolution_method, self.cycle_step_size,
                       self.do_crack_growth_plot, self.do_fad_plot, self.do_design_curve_plot, self.do_ensemble_plot,
                       self.do_cycle_plot, self.do_pdf_plot, self.do_cdf_plot, self.do_sen_plot,

                       self.probability_of_detection, self.detection_resolution, self.inspection_interval,
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
        base_resp = super().check_valid()
        if base_resp.status != InputStatus.GOOD:
            return base_resp

        study_type = self.study_type.value

        if self.crack_assump.value == CrackAssumption.ind and self.stress_method.value == StressMethod.anderson:
            return ValidationResponse(InputStatus.ERROR,
                                      'Crack length assumption ("Independent...") requires API 579-1 stress intensity method')

        if self.stress_method.value == StressMethod.anderson and self.surface.value != SurfaceType.inside:
            return ValidationResponse(InputStatus.ERROR, 'Anderson stress method requires Inside surface type')

        thickness = self.thickness.value_raw
        thick_max = self._thickness_max_val()
        if thickness > thick_max:
            return ValidationResponse(InputStatus.ERROR, 'Pipe thickness must be <= pipe radius and <= 3 in (76.2 mm)')

        if self.p_max.value_raw <= self.p_min.value_raw:
            return ValidationResponse(InputStatus.ERROR, 'Max pressure must be greater than minimum pressure')

        # check compatible pressure bounds
        if (self.p_min.distr in [Distributions.uni, Distributions.tlog, Distributions.tnor] and
            self.p_max.distr in [Distributions.uni, Distributions.tlog, Distributions.tnor]):
            p_min_upper = self.p_min._upper
            p_min_upper_disp = self.p_min.upper_str

            p_max_lower = self.p_max._lower
            p_max_lower_disp = self.p_max.lower_str
            if p_min_upper is None or p_min_upper > p_max_lower:
                return ValidationResponse(InputStatus.ERROR,
                                          f'Max pressure lower bound ({p_max_lower_disp} {self.p_max.unit}) must be > '
                                          f'min pressure upper bound ({p_min_upper_disp} {self.p_min.unit})')

        crack_len_min = 2 * (self.crack_dep.value_raw / 100.) * self.thickness.value_raw
        crack_len_min_disp = hround(self.crack_len.unit_type.convert(crack_len_min, new=self.crack_len.unit), p=3)
        if self.crack_len.value_raw <= crack_len_min:
            msg = f'Crack length must be greater than 2 x crack depth x pipe thickness ({crack_len_min_disp} {self.crack_len.unit})'
            return ValidationResponse(InputStatus.ERROR, msg)

        if study_type in ['prb', 'sam']:
            # ensure aleatory and epistemic counts and usage matches
            has_prb = False
            has_ale = False
            has_epi = False
            ale_samples = self.n_ale.value
            epi_samples = self.n_epi.value
            for field in self.fields:
                if type(field) == HelprUncertainField:
                    if field.distr != Distributions.det:  # ensure probabilistic analysis has at least 1 relevant parameter
                        has_prb = True

                    if field.distr != 'det' and field.uncertainty == 'ale':
                        has_ale = True
                    elif field.distr != 'det' and field.uncertainty == 'epi':
                        has_epi = True

            if not has_prb:
                return ValidationResponse(InputStatus.ERROR, 'Probabilistic analysis requires 1+ probabilistic parameter')

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
                if type(field) == HelprUncertainField and field.distr != 'det':
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
                if type(attr) == HelprUncertainField:
                    if attr.distr != 'det':
                        attr.distr = 'det'

            self.n_ale.toggle_enabled(False)
            self.n_ale.set_from_model(0)
            self.n_epi.toggle_enabled(False)
            self.n_epi.set_from_model(0)

        else:
            self.n_ale.toggle_enabled(True, silent=False)
            self.n_epi.toggle_enabled(True, silent=False)

        if self.study_type.value == 'prb':
            self.do_interactive_charts.set_from_model(False)
        else:
            self.do_interactive_charts.set_from_model(False)  # temporary until plots updated

        self._refresh_intermediate_params()
        self._record_state_change()

    def is_deterministic(self):
        return self.study_type.value == 'det'

    def _refresh_intermediate_params(self) -> None:
        """Refresh intermediate parameters based on current state. Resets timer so multiple calls are ignored."""
        # if self._intermed_refresh_timer:
        #     self._intermed_refresh_timer.cancel()

        # Create new timer that will execute after the delay
        # self._intermed_refresh_timer = Timer(self._intermed_refresh_delay, self._do_intermediate_refresh)
        # self._intermed_refresh_timer.start()
        self._do_intermediate_refresh()

    def _do_intermediate_refresh(self) -> None:
        """ Updates intermediate parameters via pool. """
        if self._intermed_in_progress:
            return

        self._intermed_in_progress = True

        try:
            force_det = self.use_deterministic_intermediates.value
            params = self.get_prepped_param_dict(force_deterministic=force_det)
            study_type = 'deterministic' if force_det else parse_study_type(params['study_type'])

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

        except ValueError as e:
            # param parsing may fail during changes so exit
            self._intermed_in_progress = False
            return
        except ZeroDivisionError as e:
            # param parsing may fail during file load so exit
            self._intermed_in_progress = False
            return
        finally:
            self._intermed_in_progress = False

    def get_prepped_param_dict(self, force_deterministic: bool = False):
        """Returns dict of parameters prepared for analysis submission.

        Parameters
        ----------
        force_deterministic : bool
            If True, forces all HelprUncertainField values to use
            DeterministicCharacterization regardless of study_type.

        When study_type is 'det' (deterministic) or force_deterministic is True,
        all HelprUncertainField values are forced to DeterministicCharacterization,
        ignoring any distribution settings. This ensures that distribution parameters
        like std and sigma are not considered for deterministic analyses.
        """
        dct = super().get_prepped_param_dict()
        dct |= {
            'cycle_units': self.cycle_units.value,
            'study_type': self.study_type.value,
        }

        # For deterministic studies, force all uncertain fields to use nominal values only
        if self.study_type.value == 'det' or force_deterministic:
            for field in self.fields:
                if isinstance(field, HelprUncertainField):
                    # Override with deterministic characterization using nominal value
                    dct[field.slug] = DeterministicCharacterization(
                        name=field.slug,
                        value=field._value
                    )

            # When forcing deterministic, also override study type and sample counts
            # to avoid API validation errors about aleatory samples without distributions
            if force_deterministic:
                dct['study_type'] = 'det'
                dct['aleatory_samples'] = 0
                dct['epistemic_samples'] = 0
        delta_opts = {CrackAssumption.prop: 'proportional',
                      CrackAssumption.fix: 'fixed',
                      CrackAssumption.ind: 'independent'}
        dct['crack_assump'] = delta_opts[dct['crack_assump']]

        cycle_step_size = dct['cycle_step_size'] if dct['evolution_method'] == EvolutionMethod.cycles else None
        dct['cycle_step_size'] = cycle_step_size

        # Backend expects days but raw value is in seconds, so convert
        interval_sec = self.inspection_interval.value_raw
        dct['inspection_interval'] = self.inspection_interval.unit_type.convert(interval_sec, new=LongTime.day)

        # Override pressure inputs if random profile data was provided
        profile_filepath = self.random_loading_profile.value
        if profile_filepath not in ["", None] and os.access(profile_filepath, os.R_OK):
            try:
                pressure_data = pd.read_csv(profile_filepath, index_col=0, dtype=np.float64)
                pressure_data['r_ratio'] = pressure_data['Min'] / pressure_data['Max']
                p_mins = pressure_data['Min'].values.copy()
                p_maxs = pressure_data['Max'].values.copy()

                p_units = self.profile_units.value
                if p_units == LoadingProfileUnits.psi:
                    p_mins *= scp.psi / scp.mega
                    p_maxs *= scp.psi / scp.mega
                elif p_units == LoadingProfileUnits.bar:
                    p_mins *= scp.bar / scp.mega
                    p_maxs *= scp.bar / scp.mega

                dct['min_pressure'] = TimeSeriesCharacterization(name='min_pressure', value=p_mins)
                dct['max_pressure'] = TimeSeriesCharacterization(name='max_pressure', value=p_maxs)
                dct['cycle_step_size'] = 1
            except Exception as e:
                print(str(e))
                raise e

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
        if not self._record_changes:
            return
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

    def set_random_loading_profile(self, filepath: str):
        """ Updates the random loading profile with a CSV filepath output if the new filepath is accessible.
        Also overrides cycle_step_size to 1.
        """
        if os.access(filepath, os.R_OK):
            self.random_loading_profile.set_from_model(filepath)
            self.evolution_method.set_from_model(EvolutionMethod.cycles)
            self.cycle_step_size.set_from_model(1)
            self._record_state_change()
            return True
        else:
            self.random_loading_profile.set_alert("Selected file was not accessible", stat=InputStatus.WARN)
            return False

    def clear_random_loading_profile(self):
        """ Clears the random loading profile. """
        self.random_loading_profile.set_from_model('')
        self._record_state_change()
