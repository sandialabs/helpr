# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

from helpr.utilities import unit_conversion
from .. import settings

"""Module to hold plot generation functionality. """


def get_time_str():
    return datetime.now().strftime('%y%m%d-%H%M%S%m')


def generate_pipe_life_assessment_plot(life_assessment,
                                       life_criteria,
                                       pipe_name="",
                                       save_fig=False):
    """Generates deterministic plot life assessment plot.

    Parameters
    -------------
    life_assessment : dict or DataFrame
        Single pipe life assessment results.
    life_criteria : dict or DataFrame
        Life criteria results. 
    pipe_name : str, optional
        Name of pipe to specify as title, defaults to no title.
    save_fig : bool, optional
        Flag to save plot to a png file.

    """
    _, axis = plt.subplots(figsize=(5, 5))
    life_assessment.plot(x='Total cycles', y='a/t', ax=axis)
    plt.gca().get_legend().remove()
    plt.plot(life_criteria['Cycles to a(crit)']['Total cycles'],
             life_criteria['Cycles to a(crit)']['a/t'],
             'k*', label='Cycles to a(crit)')
    plt.plot(life_criteria['Cycles to 25% a(crit)']['Total cycles'],
             life_criteria['Cycles to 25% a(crit)']['a/t'],
             'ro', label='Cycles at 25% a(crit)')
    plt.plot(life_criteria['Cycles to 1/2 Nc']['Total cycles'],
             life_criteria['Cycles to 1/2 Nc']['a/t'],
             'bs', label='Half of a(crit) Cycles')
    plt.ylabel('a/t')
    plt.xlabel('Total Cycles')
    plt.legend()
    plt.locator_params(axis='x', nbins=6)
    axis.set_ylim(0, 0.8)
    plt.grid(alpha=0.3)

    if pipe_name:
        title = f'{pipe_name:s}'
        plt.title(title)

    if save_fig:
        pipe_name = pipe_name.replace(' ', '_') if pipe_name else "pipe_"
        filename = pipe_name.replace(' ', '_') + f'_lifeassessment_{get_time_str()}.png'
        filepath = os.path.join(settings.OUTPUT_DIR, filename)
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        return filepath


def plot_pipe_life_ensemble(life_assessment,
                            criteria='Cycles to a(crit)',
                            save_fig=False):
    """Creates plot of ensemble pipe life assessment results.

    Parameters
    -------------
    life_assessment : CrackEvolutionAnalysis
        Ensemble life assessment results.
    life_criteria : dict
        Life criteria results. 
    save_fig : bool, optional
        Flag to save plot to a png file.

    """
    _, axis = plt.subplots(figsize=(4, 4))
    plt.plot([], [], 'k*', label=criteria)
    total_cycles = life_assessment.load_cycling['Total cycles']
    a_over_t = life_assessment.load_cycling['a/t']
    plt.plot(total_cycles, a_over_t, alpha=0.3)

    plt.plot(life_assessment.life_criteria[criteria][0],
             life_assessment.life_criteria[criteria][1],
             'k*')

    plt.xlabel('Total Cycles')
    plt.ylabel('a/t')
    plt.legend(loc=0)
    plt.xscale('log')
    axis.set_ylim(0, 0.8)
    plt.grid(alpha=0.3)

    if save_fig:
        filename = f'prob_crack_evolution_ensemble_{get_time_str()}.png'
        filepath = os.path.join(settings.OUTPUT_DIR, filename)
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        return filepath


def generate_crack_growth_rate_plot(life_assessment, save_fig=False):
    """Creates a crack growth rate plot.

    Parameters
    -------------
    life_assessment : dict or DataFrame
        Single life assessment results.
    save_fig : bool, optional
        Flag to save plot to a png file.
    """
    plt.subplots(figsize=(5, 5))
    da_over_dn = life_assessment['Delta a (m)']/life_assessment['Delta N']
    plt.plot(life_assessment['Delta K (Mpa m^1/2)'], da_over_dn, 'ko')
    plt.ylabel('da/dN (m/cycles)')
    plt.xlabel(r'$\Delta K$ (Mpa m$^{1/2}$)')
    plt.yscale('log')
    plt.xscale('log')
    plt.grid(alpha=0.3)

    if save_fig:
        filename = f"crack_growth_rate_{get_time_str()}.png"
        filepath = os.path.join(settings.OUTPUT_DIR, filename)
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        return filepath


def ecdf(sample):
    """Calculates empirical distribution function for dataset. 

    Parameters
    ------------
    sample
        samples to be represented as an empirical cdf

    """
    quantiles = np.sort(sample)
    cumprob = np.linspace(0, 1, len(sample), endpoint=False)
    return cumprob, quantiles


def plot_cycle_life_cdfs(analysis_results,
                         criteria='Cycles to a(crit)',
                         save_fig=False):
    """Creates a plot with cdfs of analysis results.

    Parameters
    -------------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria: str
        Life criteria to plot, defaults to 'Cycles to a (crit)'.
    save_fig : bool, optional
        Flag to save plot to a png file.

    """
    cycle_life_data = analysis_results.life_criteria[criteria][0]
    number_of_aleatory_samples = analysis_results.number_of_aleatory_samples
    plt.figure(figsize=(4, 4))
    for i in range(max(analysis_results.number_of_epistemic_samples, 1)):
        sample_indices = slice(i*number_of_aleatory_samples, (i+1)*number_of_aleatory_samples)
        cycle_life_data_subset = cycle_life_data[sample_indices]
        y_ordinate, x_ordinate = ecdf(cycle_life_data_subset)
        plt.plot(x_ordinate, y_ordinate)

    plt.plot([analysis_results.nominal_life_criteria[criteria][0]]*2,
             [0, 1], 'r--', label='nominal')
    plt.legend(loc=0)
    plt.xlabel(criteria)
    plt.ylabel('Cumulative Probability')
    plt.xscale('log')
    plt.grid(color='gray', alpha=0.3)

    if save_fig:
        filename = f"prob_critical_crack_cdf_{get_time_str()}.png"
        filepath = os.path.join(settings.OUTPUT_DIR, filename)
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        return filepath


def plot_cycle_life_cdf_ci(analysis_results,
                           criteria='Cycles to a(crit)'):
    """Creates a plot of confidence intervals around cdfs of analysis results.

    Parameters
    -------------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria: str
        Life criteria to plot, defaults to 'Cycles to a (crit)'.

    """
    cdf_curves = np.empty(shape=(max(analysis_results.number_of_aleatory_samples, 1),
                                 max(analysis_results.number_of_epistemic_samples, 1)))
    cycle_life_data = analysis_results.life_criteria[criteria][0]
    number_of_aleatory_samples = analysis_results.number_of_aleatory_samples
    plt.figure(figsize=(4, 4))
    for i in range(max(analysis_results.number_of_epistemic_samples, 1)):
        sample_indices = slice(i*number_of_aleatory_samples, (i+1)*number_of_aleatory_samples)
        cycle_life_data_subset = cycle_life_data[sample_indices]
        y_ordinate, x_ordinate = ecdf(cycle_life_data_subset)
        cdf_curves[:, i] = x_ordinate

    plt.plot(cdf_curves.mean(axis=1), y_ordinate, 'k-')
    plt.fill_betweenx(y_ordinate,
                      np.quantile(cdf_curves, 0.95, axis=1),
                      np.quantile(cdf_curves, 0.05, axis=1),
                      alpha=0.5)
    plt.xlabel(criteria)
    plt.ylabel('Cumulative Probability')
    plt.xscale('log')
    plt.grid(color='gray', alpha=0.3)
    plt.legend(['mean', '5/95 percentiles'], loc=0)


def plot_cycle_life_pdfs(analysis_results,
                         criteria='Cycles to a(crit)',
                         save_fig=False):
    """Creates pdfs of life cycle analysis results.

    Parameters
    -------------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria: str
        Life criteria to plot, defaults to 'Cycles to a (crit)'.
    save_fig : bool, optional
        Flag to save plot to a png file.

    """
    cycle_life_data = analysis_results.life_criteria[criteria][0]
    number_of_aleatory_samples = analysis_results.number_of_aleatory_samples
    _, ax = plt.subplots(figsize=(4, 4))
    for i in range(max(analysis_results.number_of_epistemic_samples, 1)):
        sample_indices = slice(i*number_of_aleatory_samples, (i+1)*number_of_aleatory_samples)
        cycle_life_data_subset = cycle_life_data[sample_indices]

        if cycle_life_data_subset.max() > 1:
            non_unity_data = np.log10(cycle_life_data_subset[cycle_life_data_subset > 1])
            plt.hist(x=non_unity_data, bins='auto', histtype='step', density=False)

    plt.plot([np.log10(analysis_results.nominal_life_criteria[criteria][0])]*2,
             plt.gca().get_ylim(), 'r--', label='nominal')

    # ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.locator_params(axis='x', nbins=6)
    labels = [fr'10$^{{{item.get_text()}}}$' for item in ax.get_xticklabels()]
    ax.set_xticklabels(labels)
    plt.legend(loc=0)
    plt.xlabel(criteria)
    plt.ylabel('Frequency')
    plt.grid(color='gray', alpha=0.3)

    if save_fig:
        filename = f"prob_critical_crack_pdf_{get_time_str()}.png"
        filepath = os.path.join(settings.OUTPUT_DIR, filename)
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        return filepath


def plot_cycle_life_criteria_scatter(analysis_results,
                                     criteria='Cycles to a(crit)',
                                     color_by_variable=False,
                                     save_fig=False):
    """
    Creates scatter plots of cycle life QOI results.
    If save_fig is True, will return filepath str (if not color_by_variable) 
    or list of filepaths if colored by variable.

    Parameters
    -------------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria: str, optional
        Life criteria to plot, defaults to 'Cycles to a (crit)'.
    color_by_variable : bool, optional
        Flag to change colors by variable.
    save_fig : bool, optional
        Flag to save plot to a png file.

    """
    cycle_life_cycles = analysis_results.life_criteria[criteria][0]
    cycle_life_values = analysis_results.life_criteria[criteria][1]
    number_of_aleatory_samples = analysis_results.number_of_aleatory_samples

    if color_by_variable:
        for uncertain_variable in analysis_results.uncertain_parameters:
            plt.figure(figsize=(4, 4))
            color = analysis_results.sampling_input_parameter_values[uncertain_variable]
            scatter_plot = plt.scatter(x=cycle_life_cycles,
                                       y=cycle_life_values,
                                       s=5, c=color, cmap='viridis')
            color_bar = plt.colorbar(scatter_plot)

            parameter_units = unit_conversion.get_variable_units(uncertain_variable)
            color_bar_label = \
                uncertain_variable.replace('_', ' ').replace('h2', r'$H_2$') + parameter_units

            color_bar.set_label(color_bar_label)
            nominal_cycle_life_cycles = analysis_results.nominal_life_criteria[criteria][0]
            nominal_cycle_life_values = analysis_results.nominal_life_criteria[criteria][1]
            plt.plot(nominal_cycle_life_cycles, nominal_cycle_life_values,
                     marker='*', linestyle='',
                     label='nominal', color='r', zorder=2)

            plt.legend(loc=0)
            plt.xlabel(criteria)
            plt.ylabel('a(crit)/t')
            plt.xscale('log')
            plt.grid(color='gray', alpha=0.3)

        if save_fig:
            figs = list(map(plt.figure, plt.get_fignums()))
            filepath1 = os.path.join(settings.OUTPUT_DIR, 
                                     f"prob_critical_crack_scatter_colorbyvariable1_{get_time_str()}.png")
            figs[2].savefig(filepath1, format='png', dpi=300, bbox_inches='tight')

            filepath2 = os.path.join(settings.OUTPUT_DIR,
                                     f"prob_critical_crack_scatter_colorbyvariable2_{get_time_str()}.png")
            figs[3].savefig(filepath2, format='png', dpi=300, bbox_inches='tight')

            filepath3 = os.path.join(settings.OUTPUT_DIR,
                                     f"prob_critical_crack_scatter_colorbyvariable3_{get_time_str()}.png")
            figs[5].savefig(filepath3, format='png', dpi=300, bbox_inches='tight')
            return [filepath1, filepath2, filepath3]

    else:
        plt.figure(figsize=(4, 4))
        for i in range(max(analysis_results.number_of_epistemic_samples, 1)):
            sample_indices = slice(i*number_of_aleatory_samples, (i+1)*number_of_aleatory_samples)
            cycle_life_cycles_subset = cycle_life_cycles[sample_indices]
            cycle_life_values_subset = cycle_life_values[sample_indices]
            plt.scatter(cycle_life_cycles_subset, cycle_life_values_subset, s=5)

        nominal_cycle_life_cycles = analysis_results.nominal_life_criteria[criteria][0]
        nominal_cycle_life_values = analysis_results.nominal_life_criteria[criteria][1]
        plt.plot(nominal_cycle_life_cycles,
                 nominal_cycle_life_values,
                 marker='*',
                 linestyle='',
                 label='nominal',
                 color='r',
                 zorder=2)

        plt.legend(loc=0)
        plt.xlabel(criteria)
        plt.ylabel('a(crit)/t')
        plt.xscale('log')
        plt.grid(color='gray', alpha=0.3)

        if save_fig:
            filename = f"prob_critical_crack_scatter_{get_time_str()}.png"
            filepath = os.path.join(settings.OUTPUT_DIR, filename)
            plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
            return filepath


def plot_sensitivity_results(analysis_results, criteria='Cycles to a(crit)', save_fig=False):
    """Creates a plot of sensitivity results.

    Parameters
    -----------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria: str, optional
        Life criteria to plot, defaults to 'Cycles to a (crit)'.
    save_fig : bool, optional
        Flag to save plot to a png file.

    """
    cycle_life_data = analysis_results.life_criteria[criteria][0]
    plt.figure(figsize=(4, 4))
    for uncertain_variable in analysis_results.uncertain_parameters:
        samples = analysis_results.sampling_input_parameter_values[uncertain_variable]
        nominal_sample = analysis_results.nominal_input_parameter_values[uncertain_variable]
        nominal_result = analysis_results.nominal_life_criteria[criteria][0]
        parameter_specific_samples = samples[samples != nominal_sample]
        corresponding_outputs = cycle_life_data[samples != nominal_sample]
        parameter_specific_samples = np.append(parameter_specific_samples,
                                               nominal_sample)
        parameter_specific_samples = np.sort(parameter_specific_samples)
        index = np.where(parameter_specific_samples == nominal_sample)[0][0]
        corresponding_outputs = np.insert(corresponding_outputs, index, nominal_result)

        plt.plot(corresponding_outputs,
                 parameter_specific_samples/nominal_sample*100,
                 label=uncertain_variable)

    legend = plt.legend(loc='upper left', bbox_to_anchor=(1.04, 1))
    for legend_entry in legend.get_texts():
        legend_entry.set_text(legend_entry.get_text().replace('_', ' ').replace('h2', r'H$_2$'))
    plt.ylabel('% of Nominal Value')
    plt.xlabel(criteria)
    plt.xscale('log')
    plt.grid(color='gray', alpha=0.3)

    if save_fig:
        filename = f"sensitivity_{get_time_str()}.png"
        filepath = os.path.join(settings.OUTPUT_DIR, filename)
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        return filepath


def plot_det_design_curve(dk, da_dn, save_fig=False):
    """Creates a plot of design curve values exercised in an analysis.

    Parameters
    ------------
    dk : pandas.DataFrame
        Change in stress intensity factor.
    da_dn : pandas.DataFrame
        Change of crack size over change in cycles (da/dn).
    save_fig : bool, optional
        Flag to save plot to a png file.
    
    """
    plt.plot(dk, da_dn, 'r--', zorder=2)
    plt.legend(['Exercised Rates', 'Design Curve'], loc=0)
    if save_fig:
        filename = f"design_curve_{get_time_str()}.png"
        filepath = os.path.join(settings.OUTPUT_DIR, filename)
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        return filepath


def plot_failure_assessment_diagram(life_assessment,
                                    nominal=False,
                                    save_fig=False):
    """
    Creates a failure assessment diagram (FAD).


    Parameters
    ------------
    life_assessment : dict
        Single or Ensemble life assessment results.
    nominal : bool, optional
        Flag for nominal or probabilistic results.
    save_fig : bool, optional
        Flag to save plot to a png file.

    """
    plt.figure(figsize=(4, 4))
    load_ordinate_space = np.linspace(0, 2.2)
    diagram_bound_line = failure_assessment_diagram_equation(load_ordinate_space)
    plt.plot(load_ordinate_space, diagram_bound_line, 'k-')

    if nominal:
        data_filter = filter_failure_assessment_data(nominal)
        plt.plot(nominal['Load ratio'][data_filter].head(1),
                 nominal['Toughness ratio'][data_filter].head(1),
                 'r.', label='nominal', zorder=2)
        plt.legend()

    data_filter = filter_failure_assessment_data(life_assessment)
    plt.plot(life_assessment['Load ratio'][data_filter].head(1),
             life_assessment['Toughness ratio'][data_filter].head(1),
             'b.', zorder=1)

    plt.xlabel(r'L$_r$ (load ratio)')
    plt.ylabel(r'K$_r$ (toughness ratio)')
    plt.grid(color='gray', alpha=0.3, linestyle='--')

    if save_fig:
        filename = f"failure_assmt_{get_time_str()}.png"
        filepath = os.path.join(settings.OUTPUT_DIR, filename)
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        return filepath


def filter_failure_assessment_data(data):
    """Filters out data for failure assessment diagram. """
    data_filter = (data['Load ratio'] < 2.2) & \
                  (data['Load ratio'] > 0) & \
                  (data['Toughness ratio'] < 1)
    return data_filter


def failure_assessment_diagram_equation(load_ratio):
    """Calculates line from FAD equation. """
    return (1 - 0.14*load_ratio**2)*(0.3 + 0.7*np.exp(-0.65*load_ratio**6))


def plot_unscaled_mitigation_cdf(analysis_results,
                                 mitigated,
                                 inspection_interval):
    """Creates a plot of unscaled cdfs showing impact of inspection/mitigation.

    Parameters
    ----------
    analysis_results : dict
        Life criteria data from fatigue analysis.
    mitigated : list
        Indication of which cracks were mitigated through inspection.
    inspection_interval : float
        Frequency of inspections.

    """
    cycle_life_data = analysis_results[0]/365
    inspection_interval = inspection_interval/365

    mitigated_life_data = cycle_life_data[mitigated]
    not_mitigated_life_data = cycle_life_data[np.invert(mitigated)]

    plt.figure(figsize=(4, 4))
    ax = plt.subplot()
    plt.plot(np.sort(cycle_life_data),
            np.arange(len(cycle_life_data)), label='w/o mitigation')
    plt.plot(np.sort(mitigated_life_data),
            np.arange(len(mitigated_life_data)), label='mitigated')
    plt.plot(np.sort(not_mitigated_life_data),
            np.arange(len(not_mitigated_life_data)), label='non mitigated')
    ax.axvline(x=inspection_interval,
            color='green',
            linestyle=':',
            label=f'{inspection_interval} year inspection freq.')

    plt.legend(loc='upper right', bbox_to_anchor=(1.7, 1.0))
    plt.xlabel('Years')
    plt.ylabel('Cumulative Failed Cracks')
    plt.xscale('log')
    plt.grid(color='gray', alpha=0.3)


def plot_log_hist(data, label, logbins=None):
    """Create a log10-scale histogram of the given data. 

    Parameters
    ----------
    data : np.ndarray
        Data to bin and plot.
    label : str
        Legend label for data.
    logbins : np.ndarray, optional
        Option to pass in log spaced bins if already computed.

    Returns
    -------
    logbins : np.array
        Bin locations in log10 spacing.
    """
    if logbins is None:
        num_bins = int(np.sqrt(data.size))
        _, bins = np.histogram(data, bins=num_bins)
        logbins = np.logspace(np.log10(bins[0]), np.log10(bins[-1]), len(bins))

    plt.hist(x=data,
            bins=logbins,
            histtype='step',
            density=False,
            label=label)
    return logbins


def plot_mitigation_histograms(analysis_results,
                               mitigated,
                               inspection_interval):
    """Create histogram plots showing cracks failing over time and the impact of inspection.

    Parameters
    ----------
    analysis_results : dict
        Life criteria data from fatigue analysis.
    mitigated : list
        Indication of which cracks were mitigated through inspection.
    inspection_interval : float
        Frequency of inspections.

    """
    cycle_life_data = analysis_results[0]/365
    inspection_interval = inspection_interval/365

    mitigated_life_data = cycle_life_data[mitigated]
    # not_mitigated_life_data = cycle_life_data[np.invert(mitigated)]

    plt.figure(figsize=(4, 4))
    ax = plt.subplot()

    logbins = plot_log_hist(cycle_life_data, 'w/o mitigation')
    # plot_log_hist(not_mitigated_life_data, 'non-mitigated', logbins)
    plot_log_hist(mitigated_life_data, 'mitigated', logbins)
    ax.axvline(x=inspection_interval,
               color='green',
               linestyle=':',
               label=f'{inspection_interval} year inspection freq.')

    plt.legend(loc='upper right', bbox_to_anchor=(1.7, 1))
    plt.xlabel('Years')
    plt.ylabel('PDF - Critical Cracks')
    plt.xscale('log')
    plt.grid(color='gray', alpha=0.3)
