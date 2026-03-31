# Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

import os
from datetime import datetime
import matplotlib
matplotlib.rcParams['agg.path.chunksize'] = 10000
import matplotlib.pyplot as plt
import numpy as np

from helpr.utilities import unit_conversion
from .. import settings

"""Module to hold plot generation functionality. """


def get_time_str():
    """
    Get date and time in 'y m d - H M S' format.

    Returns
    -------
    str
        The current date and time formatted as 'y m d - H M S'.
    """
    return datetime.now().strftime('%y%m%d-%H%M%S%m')


def _get_plot_data(plot):
    """
    Retrieves line data from mpl plot. Note that this doesn't work with scatter.

    Parameters
    ----------
    plot : matplotlib.figure.Figure
        The matplotlib plot from which to retrieve line data.

    Returns
    -------
    list
        A list of numpy arrays containing the x and y data for each line in the plot.
    """
    plot_lines = plot.gca().get_lines()
    plot_data = [ln.get_xydata() for ln in plot_lines]
    return plot_data


def _save_fig(filename):
    filename = f'{filename}_{get_time_str()}.png'
    filepath = os.path.join(settings.OUTPUT_DIR, filename)
    plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
    # plt.close()
    return filepath

def _handle_criteria(criteria):
    # Set default criteria
    if criteria is None:
        return ['Cycles to a(crit)', 'Cycles to FAD line']

    # Convert single criteria to a list
    if isinstance(criteria, str):
        return [criteria]

    return criteria

def generate_pipe_life_assessment_plot(life_assessment,
                                       postprocessed_criteria,
                                       criteria=None,
                                       pipe_name="",
                                       save_fig=False):
    """
    Generates deterministic life assessment plot.

    Parameters
    -------------
    life_assessment : dict or DataFrame
        Single pipe life assessment results.
    postprocessed_criteria : dict or DataFrame
        Life criteria results.
    criteria : list, optional
        QoI to plot (postprocessed_criteria keys)
    pipe_name : str, optional
        Name of pipe to specify as title, defaults to no title.
    save_fig : bool, optional
        Flag to save plot to a png file.

    Returns
    -------
    tuple or None
        If `save_fig` is True, returns a tuple containing the file path of the saved figure
        and the plot data; otherwise, returns None.
    """
    criteria = _handle_criteria(criteria)
    colors = ['black', 'green', 'red', 'blue']
    markers = ['*', 's', 'o', '>']
    _, axis = plt.subplots(figsize=(5, 5))
    life_assessment.plot(x='Total cycles', y='a/t', ax=axis)
    plt.gca().get_legend().remove()
    for i, qoi in enumerate(criteria):
        plt.plot(postprocessed_criteria[qoi]['Total cycles'],
                 postprocessed_criteria[qoi]['a/t'],
                 color=colors[i], marker=markers[i], linestyle='', label=qoi)

    plt.ylabel('a/t')
    plt.xlabel('Total Cycles [#]')
    plt.legend()
    plt.locator_params(axis='x', nbins=6)
    axis.set_ylim(0, 0.8)
    plt.grid(alpha=0.3)

    if pipe_name:
        title = f'{pipe_name:s}'
        plt.title(title)

    if save_fig:
        plot_data = _get_plot_data(plt)
        pipe_name = pipe_name.replace(' ', '_') if pipe_name else "pipe_"
        filename = pipe_name.replace(' ', '_') + '_lifeassessment'
        filepath = _save_fig(filename)
        return filepath, plot_data


def plot_pipe_life_ensemble(life_assessment,
                            criteria=None,
                            save_fig=False):
    """
    Creates plot of ensemble pipe life assessment results.

    Parameters
    -------------
    life_assessment : CrackEvolutionAnalysis
        Ensemble life assessment results

    criteria : list
        QoI to plot (postprocessed_criteria keys)

    save_fig : bool, optional
        Flag to save plot to a png file.

    Returns
    -------
    tuple or None
        If `save_fig` is True, returns a tuple containing the file path of the saved figure
        and the plot data; otherwise, returns None.
    """

    criteria = _handle_criteria(criteria)

    colors = ['black', 'green', 'red', 'blue']
    markers = ['*', 's', 'o', '>']

    _, axis = plt.subplots(figsize=(4, 4))

    for load_cycle in life_assessment.load_cycling:
        total_cycles = load_cycle['Total cycles']
        a_over_t = load_cycle['a/t']
        plt.plot(total_cycles, a_over_t, alpha=0.3)

    for i, qoi in enumerate(criteria):
        plt.plot([], [], color=colors[i], marker=markers[i], linestyle='', label=qoi)

        plt.plot(life_assessment.life_criteria[qoi][0],
                 life_assessment.life_criteria[qoi][1],
                 color=colors[i], marker=markers[i], linestyle='')

    plt.xlabel('Total Cycles [#]')
    plt.ylabel('a/t')
    plt.legend(loc=0)
    plt.xscale('log')
    axis.set_ylim(0, 0.8)
    plt.grid(alpha=0.3)

    if save_fig:
        filename = 'prob_crack_evolution_ensemble'
        filepath = _save_fig(filename)
        plot_data = _get_plot_data(plt)
        return filepath, plot_data


def generate_crack_growth_rate_plot(life_assessment, save_fig=False):
    """
    Creates a crack growth rate plot.

    Parameters
    -------------
    life_assessment : dict or DataFrame
        Single life assessment results.
    save_fig : bool, optional
        Flag to save plot to a png file.

    Returns
    -------
    str or None
        If `save_fig` is True, returns the file path of the saved figure; otherwise, returns None.
    """
    plt.subplots(figsize=(5, 5))

    # Convert to NumPy arrays for efficient computation
    da = np.array(life_assessment['Delta a (m)'])
    dn = np.array(life_assessment['Delta N'])

    # Use NumPy to compute da/dN, avoiding division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        da_over_dn = np.where(dn != 0, da / dn, 0)

    # Plotting
    plt.plot(life_assessment['Delta K (MPa m^1/2)'], da_over_dn, 'ko')
    plt.ylabel('da/dN [m/cycles]')
    plt.xlabel(r'$\Delta K$ [MPa m$^{1/2}$]')
    plt.yscale('log')
    plt.xscale('log')
    plt.grid(alpha=0.3)

    if save_fig:
        filename = 'crack_growth_rate'
        filepath = _save_fig(filename)
        return filepath


def ecdf(sample):
    """Calculates empirical cumulative distribution function (ECDF) for dataset. 

    Parameters
    ------------
    sample
        samples to be represented as an empirical cdf

    Returns
    -------
    tuple
        A tuple containing:
        - np.ndarray: The cumulative probabilities.
        - np.ndarray: The sorted quantiles of the sample.
    """
    quantiles = np.sort(sample)
    cumlative_probability = np.linspace(0, 1, len(sample), endpoint=False)
    return cumlative_probability, quantiles


def plot_cycle_life_cdfs(analysis_results,
                         criteria=None,
                         save_fig=False):
    """
    Creates a plot with cdfs of analysis results.

    Parameters
    -------------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria : list
        QoI to plot (postprocessed_criteria keys)
    save_fig : bool, optional
        Flag to save plot to a png file.

    Returns
    -------
    tuple or None
        If `save_fig` is True, returns a tuple containing the file path of the saved figure
        and the plot data; otherwise, returns None.
    """

    criteria = _handle_criteria(criteria)
    colors = ['black', 'green', 'red', 'blue']
    plt.figure(figsize=(4, 4))
    for j, qoi in enumerate(criteria):

        cycle_life_data = analysis_results.life_criteria[qoi][0]
        number_of_aleatory_samples = analysis_results.number_of_aleatory_samples

        # Preallocate arrays for x and y ordinates
        epistemic_samples = analysis_results.number_of_epistemic_samples
        y_ordinates = []
        x_ordinates = []

        for i in range(max(epistemic_samples, 1)):
            sample_indices = slice(i*number_of_aleatory_samples,
                                   (i+1)*number_of_aleatory_samples)
            cycle_life_data_subset = cycle_life_data[sample_indices]

            y_ordinate, x_ordinate = ecdf(cycle_life_data_subset)
            y_ordinates.append(y_ordinate)
            x_ordinates.append(x_ordinate)

        # Plot all CDFs in one go
        plt.plot([], [], color=colors[j], label=qoi)
        for x, y in zip(x_ordinates, y_ordinates):
            plt.plot(x, y, color=colors[j])

        # Plot nominal life criteria
        nominal_value = analysis_results.nominal_life_criteria[qoi][0]
        plt.plot([nominal_value] * 2, [0, 1],
                 linestyle='--', color=colors[j], label=qoi + ' Nominal')

        plt.legend(loc=0)
        plt.xlabel('Cycles to Criteria [#]')
        plt.ylabel('Cumulative Probability')
        plt.xscale('log')
        plt.grid(color='gray', alpha=0.3)

    if save_fig:
        filename = 'prob_critical_crack_cdf'
        filepath = _save_fig(filename)
        plot_data = _get_plot_data(plt)
        return filepath, plot_data


def plot_cycle_life_cdf_ci(analysis_results,
                           criteria=None):
    """
    Creates a plot of confidence intervals around cdfs of analysis results.
                           criteria=None):

    Parameters
    -------------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria : list
        QoI to plot (postprocessed_criteria keys)

    """

    criteria = _handle_criteria(criteria)
    colors = ['black', 'green', 'red', 'blue']
    number_of_aleatory_samples = max(analysis_results.number_of_aleatory_samples, 1)
    number_of_epistemic_samples = max(analysis_results.number_of_epistemic_samples, 1)

    plt.figure(figsize=(4, 4))
    plt.fill_betweenx([], [], [], alpha=0.5, color='gray', label='5/95 Percentiles')

    for j, qoi in enumerate(criteria):

        cycle_life_data = analysis_results.life_criteria[qoi][0]
        cdf_curves = np.empty(shape=(number_of_aleatory_samples, number_of_epistemic_samples))

        for i in range(number_of_epistemic_samples):
            sample_indices = slice(i * number_of_aleatory_samples,
                                (i + 1) * number_of_aleatory_samples)
            cycle_life_data_subset = cycle_life_data[sample_indices]

            # Compute ECDF
            y_ordinate, x_ordinate = ecdf(cycle_life_data_subset)
            cdf_curves[:, i] = x_ordinate

        # Plot mean CDF
        mean_cdf = cdf_curves.mean(axis=1)
        plt.plot(mean_cdf, y_ordinate, linestyle='-', color=colors[j], label=qoi)

        # Plot confidence intervals
        lower_bound = np.quantile(cdf_curves, 0.05, axis=1)
        upper_bound = np.quantile(cdf_curves, 0.95, axis=1)
        plt.fill_betweenx(y_ordinate, lower_bound, upper_bound, alpha=0.5, color=colors[j])

    plt.xlabel('Cycles to Criteria [#]')
    plt.ylabel('Cumulative Probability')
    plt.xscale('log')
    plt.grid(color='gray', alpha=0.3)
    plt.legend(loc=0)


def plot_cycle_life_pdfs(analysis_results,
                         criteria=None,
                         save_fig=False):
    """
    Creates pdfs of life cycle analysis results.

    Parameters
    -------------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria: str
        Life criteria to plot, defaults to 'Cycles to a (crit)'.
    save_fig : bool, optional
        Flag to save plot to a png file.

    Returns
    -------
    str or None
        If `save_fig` is True, returns the file path of the saved figure; otherwise, returns None.
    """

    file_paths = []
    plot_data = []
    criteria = _handle_criteria(criteria)

    for qoi in criteria:
        cycle_life_data = analysis_results.life_criteria[qoi][0]
        number_of_aleatory_samples = analysis_results.number_of_aleatory_samples
        _, ax = plt.subplots(figsize=(4, 4))

        freq_data = []
        epistemic_samples = max(analysis_results.number_of_epistemic_samples, 1)

        # Preallocate frequency data for efficiency
        non_unity_data_list = []

        for i in range(max(epistemic_samples, 1)):
            sample_indices = slice(i*number_of_aleatory_samples, (i+1)*number_of_aleatory_samples)
            cycle_life_data_subset = np.array(cycle_life_data[sample_indices])

            # Use a mask to filter out NaN values
            not_nan_mask = ~np.isnan(cycle_life_data_subset)
            valid_data = cycle_life_data_subset[not_nan_mask]

            if valid_data.size > 0 and valid_data.max() > 1:
                non_unity_data = np.log10(valid_data[valid_data > 1])
                plt.hist(non_unity_data, bins='auto', histtype='step', density=False)
                non_unity_data_list.append(non_unity_data)

        # Plot nominal life criteria
        nominal_value = analysis_results.nominal_life_criteria[qoi][0]
        plt.axvline(x=np.log10(nominal_value), color='r', linestyle='--', label='Nominal')

        # Customize x-axis ticks
        plt.locator_params(axis='x', nbins=6)
        ax.set_xticks(ax.get_xticks())
        labels = [fr'10$^{{{item.get_text()}}}$' for item in ax.get_xticklabels()]
        ax.set_xticklabels(labels)

        plt.legend(loc=0)
        plt.xlabel(qoi)
        plt.ylabel('Frequency')
        plt.grid(color='gray', alpha=0.3)

        if save_fig:
            filename = 'prob_critical_crack_pdf'
            filepath = _save_fig(filename)
            plotdata = {'Nominal': _get_plot_data(plt), 'freq_data': freq_data}
            file_paths.append(filepath)
            plot_data.append(plotdata)

    return file_paths, plot_data


def plot_cycle_life_criteria_scatter(analysis_results,
                                     criteria=None,
                                     color_by_variable=False,
                                     save_fig=False):
    """
    Creates scatter plots of cycle life QOI results.

    If ``save_fig`` is ``True``, the function returns the file-path string
    (when ``color_by_variable`` is ``False``) or a list of file-paths
    (when ``color_by_variable`` is ``True``).

    Parameters
    -----------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.

    criteria : list
        QoI to plot (``postprocessed_criteria``).

    color_by_variable : bool, optional
        When ``True`` each variable gets its own colour.

    save_fig : bool, optional
        When ``True`` the plot is saved to a PNG file.

    Returns
    -------
    str or list of str
        * If ``save_fig`` is ``True`` and ``color_by_variable`` is ``False``,
          the file path of the saved figure.
        * If ``color_by_variable`` is ``True``, a list of file paths - one for
          each variable.
    """
    # ------------------------------------------------------------------
    # 1️⃣  Normalise the criteria argument
    # ------------------------------------------------------------------
    criteria = _handle_criteria(criteria)

    file_paths = []  # will hold the returned path(s)
    plot_data = []   # will hold data used in plot

    # ------------------------------------------------------------------
    # 2️⃣  Loop over each QoI (criterion)
    # ------------------------------------------------------------------
    for j, qoi in enumerate(criteria):
        # ---- data needed for the scatter plot ---------------------------------
        cycle_life_cycles = analysis_results.life_criteria[qoi][0]
        cycle_life_values = analysis_results.life_criteria[qoi][1]
        number_of_aleatory_samples = analysis_results.number_of_aleatory_samples
        nominal_cycle_life_cycles = analysis_results.nominal_life_criteria[qoi][0]
        nominal_cycle_life_values = analysis_results.nominal_life_criteria[qoi][1]

        # --------------------------------------------------------------------
        # 3️⃣  Colour‑by‑variable case
        # --------------------------------------------------------------------
        if color_by_variable:
            # One figure per uncertain variable
            for i, uncertain_variable in enumerate(analysis_results.uncertain_parameters):
                # ---- 3.1️⃣  Create a fresh figure --------------------------------
                fig = plt.figure(figsize=(4, 4))

                # ---- 3.2️⃣  Plot the scatter ------------------------------------
                color = analysis_results.sampling_input_parameter_values[uncertain_variable]
                scatter_plot = plt.scatter(x=cycle_life_cycles,
                                           y=cycle_life_values,
                                           s=5, c=color, cmap='viridis')
                color_bar = plt.colorbar(scatter_plot)

                # ---- 3.3️⃣  Label the colour bar --------------------------------
                parameter_units = unit_conversion.get_variable_units(uncertain_variable)
                color_bar_label = \
                    uncertain_variable.replace('_', ' ').replace('h2', r'$H_2$') + parameter_units

                color_bar.set_label(color_bar_label)

                # ---- 3.4️⃣  Plot the nominal point -------------------------------
                plt.plot(nominal_cycle_life_cycles, nominal_cycle_life_values,
                        marker='*', linestyle='',
                        label='Nominal', color='r', zorder=2)

                # ---- 3.5️⃣  Axes, legend & grid ---------------------------------
                plt.legend(loc=0)
                plt.xlabel(qoi)

                if qoi == 'Cycles to a(crit)':
                    plt.ylabel('a(crit)/t')

                if qoi == 'Cycles to FAD line':
                    plt.ylabel('a/t at FAD Intersection')

                plt.xscale('log')
                plt.grid(color='gray', alpha=0.3)

                # ----------------------------------------------------------------
                # 3️⃣️⃣  Save the figure (inside the loop) if requested
                # ----------------------------------------------------------------
                if save_fig:
                    filename = (
                        f'prob_critical_crack_scatter_'
                        f'colorbyvariable_{i}_qoi_{j}')
                    # _save_fig uses the *current* figure (plt.gcf()), which is `fig`
                    filepath = _save_fig(filename)
                    file_paths.append(filepath)
                    plot_data.append([])

        else:
            plt.figure(figsize=(4, 4))
            subsets = []
            for i in range(max(analysis_results.number_of_epistemic_samples, 1)):
                sample_indices = slice(
                    i*number_of_aleatory_samples,
                    (i+1)*number_of_aleatory_samples)
                cycle_life_cycles_subset = cycle_life_cycles[sample_indices]
                cycle_life_values_subset = cycle_life_values[sample_indices]

                plt.scatter(cycle_life_cycles_subset, cycle_life_values_subset, s=5)
                subsets.append((cycle_life_cycles_subset, cycle_life_values_subset))

            plt.plot(nominal_cycle_life_cycles,
                    nominal_cycle_life_values,
                    marker='*',
                    linestyle='',
                    label='Nominal',
                    color='r',
                    zorder=2)

            plt.legend(loc=0)
            plt.xlabel(qoi)

            if qoi == 'Cycles to a(crit)':
                plt.ylabel('a(crit)/t')

            if qoi == 'Cycles to FAD line':
                plt.ylabel('a/t at FAD Intersection')

            plt.xscale('log')
            plt.grid(color='gray', alpha=0.3)

            if save_fig:
                filename = f'prob_critical_crack_scatter_qoi_{j}'
                filepath = _save_fig(filename)
                file_paths.append(filepath)
                plotdata = {
                    'nominal_pt': (nominal_cycle_life_cycles[0],
                                   nominal_cycle_life_values[0]),
                    'subsets': subsets
                }
                plot_data.append(plotdata)

    return file_paths, plot_data


def plot_sensitivity_results(analysis_results,
                             criteria=None,
                             save_fig=False,
                             filename='sensitivity'):
    """
    Creates a plot of sensitivity results.

    Parameters
    -----------
    analysis_results : CrackEvolutionAnalysis
        Ensemble life assessment results.
    criteria: str, optional
        Life criteria to plot, defaults to 'Cycles to a (crit)'.
    save_fig : bool, optional
        Flag to save plot to a png file.
    filename : str, optional
        Base filename for saved plot. Defaults to 'sensitivity'.

    Returns
    -------
    str or None
        If `save_fig` is True, returns the file path of the saved figure; otherwise, returns None.
    """

    criteria = _handle_criteria(criteria)
    file_paths = []
    plot_data = []

    # loop over QoIs
    for qoi in criteria:
        plt.figure(figsize=(4, 4))
        plt.plot([], [], 'ks', markerfacecolor='none', label='Nominal')
        cycle_life_data = np.array(analysis_results.life_criteria[qoi][0])
        nominal_result = np.array(analysis_results.nominal_life_criteria[qoi][0])

        # loop over uncertaint parameters
        for uncertain_variable in analysis_results.uncertain_parameters:
            # Convert the list of samples to a NumPy array
            samples = np.array(analysis_results.sampling_input_parameter_values[uncertain_variable])
            nominal_sample = \
                np.array(analysis_results.nominal_input_parameter_values[uncertain_variable])

            # Use NumPy to create a boolean mask for non-nominal samples
            non_nominal_mask = samples != nominal_sample

            # Filter samples and corresponding outputs using the mask
            parameter_specific_samples = samples[non_nominal_mask]
            corresponding_outputs = cycle_life_data[non_nominal_mask]

            # Locate normalization min and max based on uncertainty samples
            x_min = min(parameter_specific_samples)
            x_max = max(parameter_specific_samples)

            # Append nominal sample and sort
            parameter_specific_samples = np.sort(np.append(parameter_specific_samples, nominal_sample))

            # Find index of nominal sample
            index = np.searchsorted(parameter_specific_samples, nominal_sample)
            corresponding_outputs = np.insert(corresponding_outputs, index, nominal_result)

            # Calculate y values
            # ys = parameter_specific_samples / nominal_sample * 100
            ys = (parameter_specific_samples - x_min) / (x_max - x_min)
            plt.plot(corresponding_outputs, ys, marker='.', label=uncertain_variable)
            plt.plot(nominal_result, (nominal_sample - x_min)/(x_max - x_min), 'ks', zorder=3, markerfacecolor='none')

            # Prepare plot data
            plot_data.append({
                'label': uncertain_variable.replace('_', ' ').replace('h2', 'hydrogen'),
                'data': np.array([corresponding_outputs, ys]).T
            })

        # Update legend text
        legend = plt.legend(loc='upper left', bbox_to_anchor=(1.04, 1))
        for legend_entry in legend.get_texts():
            legend_entry.set_text(legend_entry.get_text().replace('_', ' ').replace('h2', r'H$_2$'))

        plt.ylabel('Min-Max Scaled to Parameter Values')
        plt.xlabel(qoi)
        plt.xscale('log')
        plt.grid(color='gray', alpha=0.3)

        if save_fig:
            filepath = _save_fig(filename)
            file_paths.append(filepath)

    if save_fig:
        return file_paths, plot_data

    return None, None


def plot_det_design_curve(dk, da_dn, save_fig=False):
    """
    Creates a plot of design curve values exercised in an analysis.

    Parameters
    ------------
    dk : pandas.DataFrame
        Change in stress intensity factor.
    da_dn : pandas.DataFrame
        Change of crack size over change in cycles (da/dn).
    save_fig : bool, optional
        Flag to save plot to a png file.
    
    Returns
    -------
    str or None
        If `save_fig` is True, returns the file path of the saved figure; otherwise, returns None, None.
    """
    plt.plot(dk, da_dn, 'r--', zorder=2)
    plt.legend(['Exercised Rates', 'Design Curve'], loc=0)

    if save_fig:
        filename = 'design_curve'
        filepath = _save_fig(filename)
        plot_data = _get_plot_data(plt)
        return filepath, plot_data

    return None, None


def plot_failure_assessment_diagram(life_assessment,
                                    life_criteria,
                                    fad_type,
                                    nominal=False,
                                    nominal_life_criteria=False,
                                    save_fig=False):
    """
    Creates a failure assessment diagram (FAD).

    Parameters
    ------------
    life_assessment : dict
        Single or Ensemble life assessment results.
    life_criteria : dict
        Single or Ensemble of postprocessed life criteria results.
    fad_type : str
        Type of FAD calculations presented.
    nominal : dict or bool, optional
        Nominal results and flag for nominal or probabilistic results.
    nominal_life_criteria : dict or bool, optional
        Nominal postprocessed life criteria results.
    save_fig : bool, optional
        Flag to save plot to a png file.

    Returns
    -------
    str or None
        If `save_fig` is True, returns the file path of the saved figure; otherwise, returns None.
    """
    plt.figure(figsize=(4, 4))
    load_ordinate_space = np.linspace(0, 2.2)
    diagram_bound_line = failure_assessment_diagram_equation(load_ordinate_space)
    plt.plot(load_ordinate_space, diagram_bound_line, 'k-', label='FAD Equation')

    plt.ylim(0, 1.01)
    plt.xlim(0, 1.5)

    if nominal:
        plt.plot(nominal[0]['Load ratio'],
                 nominal[0]['Toughness ratio'],
                 'r:', label='Nominal', zorder=2)
        plt.plot(nominal_life_criteria['Cycles to FAD line'][2],
                 nominal_life_criteria['Cycles to FAD line'][3],
                 'gs')

        # Check where the data goes off the chart
        exceeding_plot = np.array(nominal[0]['Toughness ratio']) > 1
        first_above_upper = np.argmax(exceeding_plot)

        # Add markers at the points where data goes off the chart
        if exceeding_plot.any():
            plt.plot(nominal[0]['Load ratio'][first_above_upper], 1,
                     marker='^', markersize=8,
                     markerfacecolor='none', markeredgecolor='black', clip_on=False)

    load_ratio = []
    toughness_ratio = []
    plt.plot([], [], color='purple', linestyle='--', marker='', label='Crack Evolution')
    plt.plot([], [],
             marker='^', markersize=8, linestyle='none',
             markerfacecolor='none', markeredgecolor='black',
             clip_on=False, label='Beyond Plot')
    plt.plot([], [], 'gs', label='FAD Intersection')
    for sample in life_assessment:
        load_ratio = np.array(sample['Load ratio'])
        toughness_ratio = np.array(sample['Toughness ratio'])
        plt.plot(load_ratio, toughness_ratio, color='purple', linestyle='--', marker='', zorder=1)

        # Check where the data goes off the chart
        exceeding_plot = toughness_ratio > 1
        first_above_upper = np.argmax(exceeding_plot > 1)

        # Add markers at the points where data goes off the chart
        if exceeding_plot.any():
            plt.plot(load_ratio[first_above_upper], 1,
                    marker='^', markersize=8, linestyle='none',
                    markerfacecolor='none', markeredgecolor='black',
                    clip_on=False)

    plt.plot(life_criteria['Cycles to FAD line'][2],
             life_criteria['Cycles to FAD line'][3],
             'gs')
    plt.xlabel(r'L$_r$ (load ratio)')
    plt.ylabel(r'K$_r$ (toughness ratio)')
    plt.grid(color='gray', alpha=0.3, linestyle='--')
    plt.legend(loc=0, title=f'{fad_type}\n FAD calculation')

    if save_fig:
        filename = 'failure_assmt'
        filepath = _save_fig(filename)
        plot_data = _get_plot_data(plt)
        return filepath, plot_data
    else:
        return None, None


def failure_assessment_diagram_equation(load_ratio):
    """
    Calculates line from FAD equation.
    Eq. 9.22 on page 9-61 of API 579-1/ASME FFS-1, June, 2016 Fitness-For-Service

    Parameters
    ----------
    load_ratio : np.ndarray
        The load ratio values for which to calculate the FAD line.

    Returns
    -------
    np.ndarray
        The calculated toughness ratio values corresponding to the input load ratios.
    """
    toughness_ratio = (1 - 0.14*load_ratio**2)*(0.3 + 0.7*np.exp(-0.65*load_ratio**6))
    return toughness_ratio

def failure_assessment_diagram_equation_v2(load_ratio):
    """
    Calculates line from FAD equation.
    Eq. supposed to be in API 579 2021 Fitness-For-Service


    Parameters
    ----------
    load_ratio : np.ndarray
        The load ratio values for which to calculate the FAD line.

    Returns
    -------
    np.ndarray
        The calculated toughness ratio values corresponding to the input load ratios.
    """
    toughness_ratio = (1 + load_ratio**2/2)**(-1/2) * (0.3 + 0.7 * np.exp(-0.6 * load_ratio**6))
    return toughness_ratio

def plot_unscaled_mitigation_cdf(cycles_to_critical_crack,
                                 cycles_till_mitigation,
                                 save_fig=False):
    """
    Creates a plot of unscaled cdfs showing impact of inspection/mitigation.

    Parameters
    ----------
    cycles_to_critical_crack : list
        Cycle count at which crack reaches critical size

    cycles_till_mitigation : list
        Cycle count at which a crack was identified through inspection and mitigated

    save_fig : bool, optional
        If True, saves the plot as a PNG file and returns the file path and plot data
        Default is False.

    Returns
    -------
    tuple or None
        If `save_fig` is True, returns a tuple:

            - str: file path to saved image
            - list of np.ndarray: line data from the plotted CDFs

        If `save_fig` is False, returns (None, None)
    """
    cycle_life_data = cycles_to_critical_crack
    mitigated_life_data = cycles_till_mitigation
    not_mitigated_life_data = [x if np.isnan(y)
                               else np.nan
                               for x, y in zip(cycles_to_critical_crack, mitigated_life_data)]

    plt.figure(figsize=(4, 4))
    plt.plot(np.sort(cycle_life_data),
            np.arange(len(cycle_life_data)), label='Critical \n w/o Inspection')
    plt.plot(np.sort(mitigated_life_data),
            np.arange(len(mitigated_life_data)), label='Mitigated \n w/ Inspection')
    plt.plot(np.sort(not_mitigated_life_data),
            np.arange(len(not_mitigated_life_data)), label='Critical Not Detected \n w/ Inspection')

    plt.legend(loc='upper right', bbox_to_anchor=(1.7, 1.0))
    plt.xlabel('Time [cycles]')
    plt.ylabel('Cumulative Cracks')
    plt.xscale('log')
    plt.grid(color='gray', alpha=0.3)

    if save_fig:
        filename = 'inspection_mitigation_cdf'
        filepath = _save_fig(filename)
        plot_data = _get_plot_data(plt)
        return filepath, plot_data
    else:
        return None, None

def plot_log_hist(data, label, logbins=None):
    """
    Create a log10-scale histogram of the given data.

    Parameters
    ----------
    data : list
        Data to bin and plot.
    label : str
        Legend label for data.
    logbins : np.ndarray, optional
        Option to pass in log spaced bins if already computed.
        Default is None.

    Returns
    -------
    logbins : np.array
        Bin locations in log10 spacing.
    """
    if logbins is None:
        num_bins = int(np.sqrt(len(data)))
        _, bins = np.histogram(data, bins=num_bins)
        logbins = np.logspace(np.log10(bins[0]), np.log10(bins[-1]), len(bins))

    plt.hist(x=data,
            bins=logbins,
            histtype='step',
            density=False,
            label=label)
    return logbins


def plot_mitigation_histograms(cycles_to_critical_crack,
                               cycles_till_mitigation,
                               save_fig=False):
    """
    Create histogram plots showing cracks failing over time and the impact of inspection.

    Parameters
    ----------
    cycles_to_critical_crack : list
        Cycle count at which crack reaches critical size.

    cycles_till_mitigation : list
        Cycle count at which a crack was identified through inspection and mitigated

    save_fig : bool, optional
        If True, the figure is saved as a PNG and file path is returned. Default is False.

    Returns
    -------
    tuple or None
        If `save_fig` is True, returns a tuple:

            - str: file path to the saved image
            - list of np.ndarray: histogram line data for plotting

        If `save_fig` is False, returns (None, None).
    """
    cycle_life_data = cycles_to_critical_crack
    mitigated_life_data = cycles_till_mitigation
    not_mitigated_life_data = [x if np.isnan(y)
                               else np.nan
                               for x, y in zip(cycle_life_data, mitigated_life_data)]

    plt.figure(figsize=(4, 4))
    logbins = plot_log_hist(cycle_life_data, 'Critical \n w/o Inspection')
    plot_log_hist(mitigated_life_data, 'Mitigated \n w/ Inspection', logbins)
    plot_log_hist(not_mitigated_life_data, 'Critical Not Detected \n w/ Inspection', logbins)

    plt.legend(loc='upper right', bbox_to_anchor=(1.7, 1))
    plt.xlabel('Time [cycles]')
    plt.ylabel('PDF - Cracks')
    plt.xscale('log')
    plt.grid(color='gray', alpha=0.3)

    if save_fig:
        filename = 'inspection_mitigation_hist'
        filepath = _save_fig(filename)
        plot_data = _get_plot_data(plt)
        return filepath, plot_data
    else:
        return None, None


def plot_random_loading_profiles(minimum_pressure,
                                 maximum_pressure,
                                 pressure_units='MPa',
                                 cycle_description='Cycle [#]',
                                 save_fig=False):
    """
    Create plots showing random pressure loading and load ratio (R) in terms of cycles.

    Parameters
    ----------
    minimum_pressure : list
        Minimum pressure values for each cycle in pressure loading profile

    maximum_pressure : list
        Maxium pressure values for each cycle in pressure loading profile

    pressure_units : str
        Units of pressure values being plotted

    cycle_description : str
        Label for x-axis describing units of pressure loading profile indices

    save_fig : bool, optional
        If True, the figure is saved as a PNG and file path is returned.
        Default is False.

    Returns
    -------
    tuple or None
        If `save_fig` is True, returns a tuple:

            - str: file path to the saved image
            - list of np.ndarray: line data for plotting

        If `save_fig` is False, returns (None, None).
    """

    # Check if minimum_pressure and maximum_pressure are lists
    if not isinstance(minimum_pressure, list) or not isinstance(maximum_pressure, list):
        raise TypeError("Minimum and maximum pressure must be lists")

    # Check if minimum_pressure and maximum_pressure have the same length
    if len(minimum_pressure) != len(maximum_pressure):
        raise ValueError("Minimum and maximum pressure must have the same length")

    # Check for zero division
    if any(max_p == 0 for max_p in maximum_pressure):
        raise ZeroDivisionError("Cannot divide by zero")

    fig, axs = plt.subplots(2, 1, figsize=(5, 6), sharex=True)
    axs[0].plot(maximum_pressure, label='Maximum')
    axs[0].plot(minimum_pressure, label='Minimum')
    axs[0].set_ylabel(f'Pressure [{pressure_units}]')
    axs[0].legend(loc=0)
    axs[0].grid(color='gray', linestyle='--', alpha=0.3)

    axs[1].plot(np.array(minimum_pressure)/np.array(maximum_pressure))
    axs[1].set_xlabel(cycle_description)
    axs[1].set_ylabel('Load Ratio (R)')
    axs[1].grid(color='gray', linestyle='--', alpha=0.3)

    if save_fig:
        filename = 'random_loading_profile'
        filepath = _save_fig(filename)
        plot_data = _get_plot_data(plt)
        return filepath, plot_data
    else:
        return None, None
