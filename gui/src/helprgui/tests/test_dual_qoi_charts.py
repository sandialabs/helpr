"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Tests for probabilistic interactive chart data pipeline (Issue H1).
Verifies that both QoIs are included in chart data for ensemble, CDF,
cycle scatter, PDF, and FAD charts.

Usage:
    pytest test_dual_qoi_charts.py -v
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from helprgui import app_settings
from helprgui.models import models


def _make_params(**overrides):
    """Build default probabilistic params dict with optional overrides."""
    params = {
        'session_dir': Path(tempfile.gettempdir()),
        'study_type': 'prb',
        'analysis_name': 'test',
        'create_sensitivity_plot': False,
        'create_crack_growth_plot': False,
        'create_fad_plot': False,
        'create_design_curve_plot': False,
        'create_ensemble_plot': False,
        'create_cycle_plot': False,
        'create_pdf_plot': False,
        'create_cdf_plot': False,
        'create_exercised_rates_plot': False,
        'create_failure_assessment_diagram': False,
        'random_loading_profile': None,
    }
    params.update(overrides)
    return params


def _make_analysis(n_ale=3, n_epi=2):
    """Build mock CrackEvolutionAnalysis with data for all chart types."""
    m = mock.MagicMock()
    m.generate_input_parameter_plots.return_value = {}
    m.number_of_aleatory_samples = n_ale
    m.number_of_epistemic_samples = n_epi
    total = n_ale * max(n_epi, 1)

    m.life_criteria = {
        'Cycles to a(crit)': [np.linspace(1000, 10000, total),
                              np.linspace(0.35, 0.55, total)],
        'Cycles to FAD line': [np.linspace(500, 8000, total),
                               np.linspace(0.3, 0.5, total),
                               np.linspace(0.5, 0.8, total),
                               np.linspace(0.4, 0.9, total)],
    }
    m.nominal_life_criteria = {
        'Cycles to a(crit)': [[5000], [0.5]],
        'Cycles to FAD line': [[3000], [0.4], [0.5], [0.6]],
    }
    m.load_cycling = [
        {'Total cycles': np.array([1, 10, 100, 1000]),
         'a/t': np.array([0.1, 0.2, 0.3, 0.5]),
         'Load ratio': np.array([0.1, 0.3, 0.5, 0.8]),
         'Toughness ratio': np.array([0.9, 0.7, 0.5, 0.3])},
        {'Total cycles': np.array([1, 10, 100, 500]),
         'a/t': np.array([0.1, 0.25, 0.35, 0.55]),
         'Load ratio': np.array([0.1, 0.4, 0.6, 0.9]),
         'Toughness ratio': np.array([0.85, 0.65, 0.45, 0.25])},
    ]
    m.nominal_load_cycling = [
        {'Load ratio': np.array([0.1, 0.3, 0.5, 0.7]),
         'Toughness ratio': np.array([0.95, 0.8, 0.6, 0.4])}
    ]
    return m


class EnsembleDataTestCase(unittest.TestCase):
    """Ensemble chart data: both QoI point sets + evolution lines."""

    def setUp(self):
        app_settings.init()

    def _run(self):
        analysis = _make_analysis()
        with mock.patch.object(models, '_do_api_crack_analysis',
                               return_value=analysis), \
             mock.patch.object(models.plots, 'plot_pipe_life_ensemble',
                               return_value=('/tmp/e.png', None)):
            return models.do_crack_evolution_analysis(
                1, _make_params(create_ensemble_plot=True), {})

    def test_ensemble_data_structure(self):
        data = self._run()['ensemble_data']
        self.assertIn('pts_acrit', data)
        self.assertIn('pts_fad', data)
        self.assertTrue(len(data['pts_acrit']) > 0)
        self.assertTrue(len(data['pts_fad']) > 0)
        self.assertEqual(len(data['lines']), 2)

    def test_ensemble_point_values(self):
        data = self._run()['ensemble_data']
        self.assertEqual(data['pts_acrit'].shape[1], 2)
        self.assertEqual(data['pts_fad'].shape[1], 2)
        # Points should match life_criteria sample count
        self.assertEqual(data['pts_acrit'].shape[0], 6)
        self.assertEqual(data['pts_fad'].shape[0], 6)


class CdfDataTestCase(unittest.TestCase):
    """CDF chart data: per-QoI CDF lines + nominal vertical lines."""

    def setUp(self):
        app_settings.init()

    def _run(self, n_ale=3, n_epi=2):
        analysis = _make_analysis(n_ale=n_ale, n_epi=n_epi)
        with mock.patch.object(models, '_do_api_crack_analysis',
                               return_value=analysis), \
             mock.patch.object(models.plots, 'plot_cycle_life_cdfs',
                               return_value=('/tmp/cdf.png', None)):
            return models.do_crack_evolution_analysis(
                1, _make_params(create_cdf_plot=True), {})

    def test_cdf_data_structure(self):
        data = self._run()['cdf_data']
        self.assertTrue(len(data['acrit_lines']) > 0)
        self.assertTrue(len(data['fad_lines']) > 0)
        # Nominal lines: vertical from (val, 0) to (val, 1)
        self.assertEqual(data['acrit_nominal'].shape, (2, 2))
        self.assertEqual(data['fad_nominal'].shape, (2, 2))
        self.assertEqual(data['acrit_nominal'][0, 0], 5000)
        self.assertEqual(data['fad_nominal'][0, 0], 3000)

    def test_cdf_line_count_matches_epistemic(self):
        data = self._run(n_ale=5, n_epi=3)['cdf_data']
        self.assertEqual(len(data['acrit_lines']), 3)
        self.assertEqual(len(data['fad_lines']), 3)

    def test_cdf_lines_have_sorted_x(self):
        data = self._run(n_ale=5, n_epi=1)['cdf_data']
        for key in ('acrit_lines', 'fad_lines'):
            for line in data[key]:
                x = line[:, 0]
                self.assertTrue(np.all(x[:-1] <= x[1:]),
                                f"{key} x values should be sorted")


class CycleScatterDataTestCase(unittest.TestCase):
    """Cycle scatter chart: per-QoI subsets + nominal points."""

    def setUp(self):
        app_settings.init()

    def _run(self, n_ale=3, n_epi=2):
        analysis = _make_analysis(n_ale=n_ale, n_epi=n_epi)
        with mock.patch.object(models, '_do_api_crack_analysis',
                               return_value=analysis), \
             mock.patch.object(models.plots, 'plot_cycle_life_criteria_scatter',
                               return_value=(['/tmp/c0.png', '/tmp/c1.png'],
                                             [None, None])):
            return models.do_crack_evolution_analysis(
                1, _make_params(create_cycle_plot=True), {})

    def test_cycle_data_structure(self):
        data = self._run()['cycle_data']
        self.assertIn('subsets_acrit', data)
        self.assertIn('subsets_fad', data)
        for subset in data['subsets_acrit']:
            self.assertEqual(subset.shape[1], 2)
        self.assertAlmostEqual(data['nominal_pt_acrit'][0], 5000)
        self.assertAlmostEqual(data['nominal_pt_fad'][0], 3000)

    def test_cycle_subset_count_matches_epistemic(self):
        data = self._run(n_ale=4, n_epi=3)['cycle_data']
        self.assertEqual(len(data['subsets_acrit']), 3)
        self.assertEqual(len(data['subsets_fad']), 3)


class PdfDataTestCase(unittest.TestCase):
    """PDF chart: per-QoI histograms + log10 nominals."""

    def setUp(self):
        app_settings.init()

    def test_pdf_data_structure(self):
        analysis = _make_analysis(n_ale=10, n_epi=1)
        with mock.patch.object(models, '_do_api_crack_analysis',
                               return_value=analysis), \
             mock.patch.object(models.plots, 'plot_cycle_life_pdfs',
                               return_value=(['/tmp/pdf.png'], [None])):
            results = models.do_crack_evolution_analysis(
                1, _make_params(create_pdf_plot=True), {})

        data = results['pdf_data']
        self.assertTrue(len(data['acrit_bins']) > 0)
        self.assertTrue(len(data['fad_bins']) > 0)
        self.assertAlmostEqual(data['acrit_nominal'],
                               np.log10(5000), places=5)
        self.assertAlmostEqual(data['fad_nominal'],
                               np.log10(3000), places=5)


class FadDataTestCase(unittest.TestCase):
    """FAD chart: boundary line, trajectories, intersection points, nominal."""

    def setUp(self):
        app_settings.init()

    def _run(self):
        analysis = _make_analysis()
        analysis.assemble_failure_assessment_diagram = mock.MagicMock(
            return_value=('/tmp/fad.png', None))
        with mock.patch.object(models, '_do_api_crack_analysis',
                               return_value=analysis):
            return models.do_crack_evolution_analysis(
                1, _make_params(create_failure_assessment_diagram=True), {})

    def test_fad_data_structure(self):
        data = self._run()['fad_data']
        # 1 boundary line (50 pts) + 2 sample trajectories
        self.assertEqual(data['lines'][0].shape[0], 50)
        self.assertEqual(len(data['lines']), 3)
        # Intersection points
        self.assertEqual(data['pts'].shape[1], 2)
        # Nominal point
        self.assertAlmostEqual(data['nominal_pt'][0], 0.5)
        self.assertAlmostEqual(data['nominal_pt'][1], 0.6)

    def test_fad_data_has_nominal_line(self):
        data = self._run()['fad_data']
        nom = data['nominal_line']
        self.assertEqual(nom.shape, (4, 2))
        np.testing.assert_array_almost_equal(
            nom[:, 0], [0.1, 0.3, 0.5, 0.7])


class EnsembleResultsFormTestCase(unittest.TestCase):
    """ResultsForm JSON serialization for ensemble chart."""

    def setUp(self):
        app_settings.init()
        self.state = models.State()
        from helprgui.forms.results import CrackEvolutionResultsForm
        self.form = CrackEvolutionResultsForm(analysis_id=1,
                                              prelim_state=self.state)
        self.form._state = self.state

    def test_empty_when_no_data(self):
        self.assertEqual(self.form.ensemble_data, '')

    def test_json_format(self):
        self.state.do_ensemble_plot.value = True
        self.state.ensemble_plot = "/tmp/e.png"
        self.state.ensemble_data = {
            'lines': [np.array([[1, 0.1], [10, 0.2]])],
            'pts_acrit': np.array([[1000, 0.5], [500, 0.55]]),
            'pts_fad': np.array([[800, 0.45], [400, 0.5]]),
        }
        parsed = json.loads(self.form.ensemble_data)
        self.assertIn('pts_acrit', parsed)
        self.assertIn('pts_fad', parsed)
        self.assertIn('x', parsed['pts_acrit'][0])
        self.assertIn('x', parsed['pts_fad'][0])


class CdfResultsFormTestCase(unittest.TestCase):
    """ResultsForm JSON serialization for CDF chart."""

    def setUp(self):
        app_settings.init()
        self.state = models.State()
        from helprgui.forms.results import CrackEvolutionResultsForm
        self.form = CrackEvolutionResultsForm(analysis_id=1,
                                              prelim_state=self.state)
        self.form._state = self.state

    def test_empty_when_no_data(self):
        self.assertEqual(self.form.cdf_data, '')

    def test_json_format(self):
        self.state.do_cdf_plot.value = True
        self.state.cdf_plot = "/tmp/cdf.png"
        self.state.cdf_data = {
            'acrit_lines': [np.array([[100, 0.0], [500, 0.5], [1000, 1.0]])],
            'acrit_nominal': np.array([[5000, 0], [5000, 1]]),
            'fad_lines': [np.array([[80, 0.0], [400, 0.5], [800, 1.0]])],
            'fad_nominal': np.array([[3000, 0], [3000, 1]]),
        }
        parsed = json.loads(self.form.cdf_data)
        for key in ('acrit_lines', 'acrit_nominal', 'fad_lines', 'fad_nominal'):
            self.assertIn(key, parsed)
        self.assertIn('x', parsed['acrit_lines'][0][0])
        self.assertIn('x', parsed['fad_lines'][0][0])


if __name__ == '__main__':
    unittest.main()
